"""Online batch coverage, global KL normalization, and checkpoint continuity."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from steerdistill.training.online_step import OnlineGlobalBatches, OnlineCollator, trajectory_groups
from steerdistill.training.data_loading import DataCollatorForSupervisedDataset, IndexedJsonlDataset
from steerdistill.training.mytrainer import SkillKDTrainer
from test_pipeline import TinyLM, TinyTokenizer
from steerdistill.online import epoch_batches, main
from scripts.validate.check_training_signal import check
from scripts.data.audit_training_data import audit_tool_fallback
from steerdistill.stream_repair import RepairConsumer, restored_state


def records():
    return [{"task_key": f"task-{task}", "source_run": f"run-{task}",
             "assistant_turn": turn,
             "prompt": "prefix", "skill_prompt": "steer", "completion": "abc"[:turn % 3 + 1],
             "add_eos": False, "distill_mode": (
                 "ordinary_opd", "skill_recovery", "teacher_rescue", "steer_forward")[turn % 4]}
            for task in range(16) for turn in range(task % 5 + 1)]


class OnlineStepTest(unittest.TestCase):
    def test_system_error_requires_explicit_recovery_and_replays_only_that_event(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "state.jsonl"
            state.write_text("\n".join(json.dumps(row) for row in (
                {"event_id": "accepted", "task_key": "a", "repair_status": "not_required", "repair_complete": False},
                {"event_id": "done", "task_key": "b", "repair_status": "verified", "repair_complete": True},
                {"event_id": "retry", "task_key": "c", "repair_status": "system_error", "repair_complete": False},
            )) + "\n")
            with self.assertRaisesRegex(RuntimeError, "system error"):
                restored_state(state, False)
            processed, repaired = restored_state(state, True)
            self.assertEqual(processed, {"accepted", "done"})
            self.assertEqual(repaired, {"b"})

    def test_repair_view_preserves_exact_snapshot_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            snapshot = source / "snapshots/turn_0001/manifest.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text('{"state": "original"}')
            (source / "trajectory.json").write_text('{}')
            event = dict(scenario="s", task_id=1, attempt=0, run_dir=str(source))
            consumer = object.__new__(RepairConsumer)
            for _ in range(2):
                consumer.event_plain_root(event, root / "repair")
            view = root / "repair/runs/s/task_1/attempt_0/snapshots/turn_0001/manifest.json"
            self.assertEqual(view.resolve(), snapshot.resolve())
            self.assertEqual(view.read_bytes(), snapshot.read_bytes())

    def test_tool_fallback_requires_completed_repair_and_matching_event(self):
        trajectory = {"scenario": "s", "task_id": 1}
        state = {"task_key": "s:1", "repair_complete": True, "event_id": "event",
                 "counterfactual_attempts": 4, "repair_status": "no_verified_counterfactual"}
        event = {"run_dir": "/runs/s/task_1/attempt_0", "status": "rejected"}
        source = event["run_dir"]
        with patch("scripts.data.audit_training_data.read_json", side_effect=lambda path:
                   trajectory if path.name == "trajectory.json" else event), \
                patch("scripts.data.audit_training_data.iter_jsonl", return_value=[state]), \
                patch("scripts.data.audit_training_data.collect_runs", return_value={"s:1": [{"success": False}] * 4}):
            self.assertTrue(audit_tool_fallback("/steps/step000001/stream.state.jsonl", source))
            state["repair_status"] = "system_error"
            self.assertFalse(audit_tool_fallback("/steps/step000001/stream.state.jsonl", source))
            state["repair_status"] = "no_verified_counterfactual"
            event["run_dir"] = "/different/run"
            self.assertFalse(audit_tool_fallback("/steps/step000001/stream.state.jsonl", source))

    def test_sixteen_trajectories_are_not_sixteen_turns(self):
        rows = records()
        self.assertEqual(len(trajectory_groups(rows)), 16)
        dataset = OnlineGlobalBatches(rows, 16, 1, 8)
        collator = OnlineCollator(DataCollatorForSupervisedDataset(TinyTokenizer()), 4)
        ids = []
        for rank in range(8):
            batch = collator([dataset[rank]])
            ids.extend(batch["online_ids"])
            for group in batch["online_microgroups"]:
                self.assertTrue(all(len(micro["labels"]) <= 4 for micro in group))
        self.assertEqual(sorted(ids), list(range(len(rows))))
        with self.assertRaisesRegex(ValueError, "more than once"):
            trajectory_groups(rows + [rows[0]])
        with self.assertRaisesRegex(ValueError, "exceeds"):
            OnlineGlobalBatches(rows, 8, 1, 8)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            indexed = IndexedJsonlDataset(path, TinyTokenizer())
            self.assertEqual(trajectory_groups(indexed), trajectory_groups(rows))

    def test_accumulated_rank_gradients_equal_full_token_objective(self):
        rows = records()
        collator = DataCollatorForSupervisedDataset(TinyTokenizer())
        trainer = object.__new__(SkillKDTrainer)
        trainer.teacher_model = TinyLM(2).eval().requires_grad_(False)
        trainer.skill_reference_model = TinyLM(3).eval().requires_grad_(False)
        student = TinyLM(1)
        batch = collator(rows)
        tokens = batch["labels"][:, 1:].ne(-100).sum()
        SkillKDTrainer.compute_loss(trainer, student, dict(batch)).backward()
        expected = [parameter.grad.clone() for parameter in student.parameters()]
        dataset = OnlineGlobalBatches(rows, 16, 1, 8)
        accumulated = [torch.zeros_like(value) for value in expected]
        online_collator = OnlineCollator(collator, 4)
        for rank in range(8):
            local = TinyLM(1)
            online = online_collator([dataset[rank]])
            with patch("steerdistill.training.online_step.distributed", return_value=True), \
                    patch("torch.distributed.get_world_size", return_value=8):
                for group in online["online_microgroups"]:
                    for micro in group:
                        SkillKDTrainer.compute_loss(trainer, local, dict(micro), num_items_in_batch=tokens).backward()
                SkillKDTrainer.compute_loss(trainer, local, dict(online["online_dummy"]),
                                            num_items_in_batch=tokens).backward()
            for total, parameter in zip(accumulated, local.parameters()):
                total.add_(parameter.grad / 8)
        for actual, reference in zip(accumulated, expected):
            torch.testing.assert_close(actual, reference, atol=2e-6, rtol=2e-5)

    def test_signal_checks_only_new_update(self):
        state = {"global_step": 2, "log_history": [
            {"step": 1, "loss": 0.2, "grad_norm": 0.8},
            {"step": 2, "loss": 0.1, "grad_norm": 0.4}]}
        self.assertEqual(check(state, 2, 1)["loss_records"], 1)
        state["log_history"][1]["grad_norm"] = 0
        with self.assertRaisesRegex(ValueError, "zero"):
            check(state, 2, 1)

    def test_shuffle_keeps_every_task_including_final_batch(self):
        batches = list(epoch_batches(list(range(35)), 16, 2, 42, 0))
        self.assertEqual(len(batches), 6)
        for offset in (0, 3):
            indices = sum((batches[i][2] for i in range(offset, offset + 3)), [])
            self.assertEqual(sorted(indices), list(range(35)))
            self.assertEqual(len(batches[offset + 2][2]), 3)
        self.assertNotEqual(batches[0][2], batches[3][2])

    def test_partial_batch_preserves_rows_and_pads_empty_ranks(self):
        for task_count in (3, 8):
            rows = [row for row in records() if int(row["task_key"].split("-")[1]) < task_count]
            dataset = OnlineGlobalBatches(rows, 16, 1, 8)
            collator = OnlineCollator(DataCollatorForSupervisedDataset(TinyTokenizer()), 4)
            ids = []
            for rank in range(8):
                batch = collator([dataset[rank]])
                self.assertEqual(len(batch["online_microgroups"]), 2)
                self.assertEqual(batch["online_trajectories"], task_count)
                self.assertFalse(batch["online_dummy"]["online_row_mask"].any())
                ids.extend(batch["online_ids"])
            self.assertEqual(sorted(ids), list(range(len(rows))))

    def test_partial_batch_gradient_matches_full_token_objective(self):
        for task_count in (3, 8):
            rows = [row for row in records() if int(row["task_key"].split("-")[1]) < task_count]
            with self.subTest(tasks=task_count), patch(__name__ + ".records", return_value=rows):
                self.test_accumulated_rank_gradients_equal_full_token_objective()

    def test_scheduler_samples_from_new_student_and_resumes_without_retraining(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            prompts = base / "prompts.jsonl"
            prompts.write_text("".join(json.dumps({"task": i}) + "\n" for i in range(32)))
            clip = base / "clip.pt"
            clip.write_bytes(b"clip")
            run = base / "online"
            env = {"STEER_ONLINE_ROOT": str(run), "BENCHMARK_ENGINE": "tool_env",
                   "PROMPT_MANIFEST": str(prompts), "BENCHMARK": "bfcl_v4", "MODEL_FAMILY": "qwen3_8b",
                   "TEACHER_MODEL": "teacher", "INITIAL_W4_MASTER": "initial-master",
                   "INITIAL_RUNTIME_W4": "initial-runtime", "CLIP_PATH": str(clip),
                   "OPD_EPOCHS": "1", "OPD_MAX_STEPS": "2"}
            sampled = []
            def execute(command, environment, log):
                step = int(command[-2])
                sampled.append((environment["OPD_STUDENT_RUNTIME"], environment["OPD_PREVIOUS_OPTIMIZER_STEP"]))
                directory = run / "steps" / f"step{step:06d}" / "train"
                directory.mkdir()
                (directory / "training_signal.json").write_text(json.dumps(
                    {"global_step": step, "previous_step": step - 1, "status": "passed"}))
            with patch.dict(os.environ, env, clear=True), patch("sys.argv", ["steerdistill.online.py", "--gpu-ids", "0,1,2,3,4,5,6,7"]), \
                    patch("steerdistill.online.model_digest", side_effect=lambda path: str(path)), \
                    patch("steerdistill.online.run_command", side_effect=execute):
                main()
                self.assertEqual(sampled[0], ("initial-runtime", "0"))
                self.assertEqual(sampled[1], (str(run / "checkpoints/student-step000001-awq-runtime"), "1"))
                main()
                self.assertEqual(len(sampled), 2)
                config_path = run / "run_config.json"
                legacy = json.loads(config_path.read_text())
                for key in ("bits", "activation_bits", "group_size"):
                    legacy.pop(key)
                config_path.write_text(json.dumps(legacy))
                main()
                self.assertEqual(len(sampled), 2)
                with patch.dict(os.environ, {"BITS": "2"}):
                    with self.assertRaisesRegex(ValueError, "inputs changed"):
                        main()
                self.assertTrue((run / "steps/step000002/complete.json").is_file())
                with patch.dict(os.environ, {"MAX_TOKENS": "1024"}):
                    with self.assertRaisesRegex(ValueError, "inputs changed"):
                        main()


if __name__ == "__main__":
    unittest.main()
