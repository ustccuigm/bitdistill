import copy
import json
from pathlib import Path
import pickle
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import steerdistill
from steerdistill.benchmarks import online_rollout
from scripts.data.audit_training_data import main as audit


class DeterministicEnvironment:
    def __init__(self, benchmark, task):
        self.benchmark, self.task = benchmark, task
        self.description = "Reach the destination."
        self.state = 0
        self.done = self.success = False

    def prompt(self):
        return f"state{self.state}"

    def snapshot(self):
        return {"state": self.state, "done": self.done, "success": self.success,
                "semantic_hash": f"s{self.state}"}

    def save_snapshot(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        state = self.snapshot()
        path.write_bytes(pickle.dumps(state))
        return state

    def restore(self, state):
        for key in ("state", "done", "success"):
            setattr(self, key, state[key])

    def step(self, response):
        if "correct" in response:
            self.state += 1
            self.done = self.success = self.state == 2
        else:
            self.state = -1
            self.done = True
        return {"state_hash": f"s{self.state}", "success": self.success,
                "done": self.done, "observation": self.prompt(), "valid": True,
                "score": float(self.success)}

    def close(self):
        pass


class NativeRevisionTest(unittest.TestCase):
    def test_materialization_does_not_invent_eos_after_length_termination(self):
        for generation, expected in (({"finish_reason": "length"}, False),
                                     ({"finish_reason": "stop"}, True), (None, True)):
            trajectory = {"scenario": "webshop", "task_id": 1, "messages": [
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "retained response", "generation": generation}]}
            rows = steerdistill.benchmarks.online_rollout.rows_from_run(
                {"trajectory": trajectory, "success": False, "run_dir": "test"}, "ordinary_opd", None)
            self.assertEqual(rows[0]["add_eos"], expected)
            self.assertEqual(rows[0]["completion"], "retained response")

    def test_realignment_revisits_turn_without_overwriting_evidence(self):
        analysis = {"steer": {"precondition": "unfinished", "decision_rule": "correct",
                              "expected_transition": "advance", "recovery_check": "progress"},
                    "failure_mechanism": "wrong action", "relation_to_prior": "new"}

        unsteered = []

        def generate(url, model, messages, seed):
            good = url == "teacher" or any(m["role"] == "system" for m in messages)
            if not good:
                unsteered.append(messages)
                good = len(unsteered) >= 3
            return "correct" if good else "wrong", {}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=1,
                                   retries=2, output=root, store=root / "store.jsonl",
                                   student_url="student", teacher_url="teacher", model="test")
            with patch.object(online_rollout, "Environment", DeterministicEnvironment), \
                 patch.object(online_rollout, "generate", side_effect=generate), \
                 patch.object(online_rollout, "grounded_analysis", return_value=analysis), \
                 patch.object(online_rollout, "divergence", side_effect=[(0, 0), (0, 0)]):
                steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 7}}))
            receipt = json.loads((root / "tasks/7/0/completed.json").read_text())
            self.assertEqual(receipt["attempted"], 2)
            self.assertEqual(receipt["accepted_interventions"], 1)
            self.assertIsNone(receipt["fallback"])
            self.assertEqual(len(list(root.rglob("steering.json"))), 2)
            self.assertIn("revision0002", receipt["retained_run"])

    def test_analysis_rejection_retains_trajectory_but_service_errors_propagate(self):
        from steerdistill.analysis import AnalysisRejected
        for error in (AnalysisRejected(["ungrounded"], {"steer": "rejected"}),
                      RuntimeError("service unavailable")):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=1,
                                       retries=2, output=root, store=root / "store.jsonl",
                                       student_url="student", teacher_url="teacher", model="test")
                with patch.object(online_rollout, "Environment", DeterministicEnvironment), \
                     patch.object(online_rollout, "generate", side_effect=lambda url, *a: (
                         "correct" if url == "teacher" else "wrong", {})), \
                     patch.object(online_rollout, "grounded_analysis", side_effect=error):
                    if not isinstance(error, AnalysisRejected):
                        with self.assertRaisesRegex(RuntimeError, "service unavailable"):
                            steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 7}}))
                        continue
                    steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 7}}))
                receipt = json.loads((root / "tasks/7/0/completed.json").read_text())
                self.assertEqual(receipt["fallback"], "steering_exhausted")
                self.assertEqual(receipt["attempted"], 2)
                self.assertEqual(receipt["accepted_interventions"], 0)
                self.assertEqual(receipt["plain_run"], receipt["retained_run"])
                self.assertEqual(len(list(root.rglob("steering.json"))), 2)

    def test_context_limit_preserves_completed_turns_without_empty_response(self):
        from steerdistill.generation_budget import ContextWindowExceeded
        with tempfile.TemporaryDirectory() as folder:
            env = DeterministicEnvironment("alfworld", {"task_id": 1})
            with patch.object(online_rollout, "generate", side_effect=[
                ("correct", {}), ContextWindowExceeded(32768, 32770)]):
                run = steerdistill.benchmarks.online_rollout.rollout(env, Path(folder), "student", "test", 1)
            self.assertEqual(run["trajectory"]["termination_reason"], "context_length")
            self.assertEqual(len(run["trajectory"]["transitions"]), 1)
            self.assertEqual(len(run["snapshots"]), 1)
            self.assertEqual([m["content"] for m in run["trajectory"]["messages"]
                              if m["role"] == "assistant"], ["correct"])

    def test_generation_limit_does_not_request_another_response(self):
        with tempfile.TemporaryDirectory() as folder:
            env = DeterministicEnvironment("alfworld", {"task_id": 1})
            with patch.object(online_rollout, "generate", return_value=("correct", {"finish_reason": "length"})) as generate:
                run = steerdistill.benchmarks.online_rollout.rollout(env, Path(folder), "student", "test", 1)
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(run["trajectory"]["termination_reason"], "generation_length")
            self.assertEqual(env.state, 1)

    def test_accepted_action_is_executed_once_and_terminal_feedback_is_retained(self):
        class CountedEnvironment(DeterministicEnvironment):
            executed = []

            def step(self, response):
                self.executed.append((self.state, response))
                result = super().step(response)
                result["observation"] += f" execution{len(self.executed)}"
                return result

        analysis = {"steer": {"precondition": "unfinished", "decision_rule": "correct",
                              "expected_transition": "advance", "recovery_check": "progress"},
                    "failure_mechanism": "wrong action", "relation_to_prior": "new"}

        def generate(url, model, messages, seed):
            good = url == "teacher" or any(m["role"] == "system" for m in messages)
            return "correct" if good else "wrong", {}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=1,
                                   retries=2, output=root, store=root / "store.jsonl",
                                   student_url="student", teacher_url="teacher", model="test")
            with patch.object(online_rollout, "Environment", CountedEnvironment), \
                 patch.object(online_rollout, "generate", side_effect=generate), \
                 patch.object(online_rollout, "grounded_analysis", return_value=analysis):
                steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 1}}))
            # One failed rollout, two teacher actions, two repairs, one failed continuation.
            self.assertEqual(len(CountedEnvironment.executed), 6)
            receipt = json.loads((root / "tasks/1/0/completed.json").read_text())
            trajectory = json.loads((Path(receipt["retained_run"]) / "trajectory.json").read_text())
            self.assertEqual(trajectory["transitions"][-1]["observation"], "state2 execution6")
            self.assertEqual(len(trajectory["transitions"]), 2)

    def test_no_alignable_divergence_retains_failed_episode(self):
        class SameStateEnvironment(DeterministicEnvironment):
            def step(self, response):
                self.done = True
                self.success = response == "correct"
                return {"state_hash": "s0", "success": self.success, "done": True,
                        "valid": True, "observation": "same observation"}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=1,
                                   retries=2, output=root, store=root / "store.jsonl",
                                   student_url="student", teacher_url="teacher", model="test")
            with patch.object(online_rollout, "Environment", SameStateEnvironment), \
                 patch.object(online_rollout, "generate", side_effect=lambda url, *a: (
                     "correct" if url == "teacher" else "wrong", {})):
                steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 2}}))
            receipt = json.loads((root / "tasks/2/0/completed.json").read_text())
            self.assertEqual(receipt["fallback"], "no_alignable_divergence")
            self.assertEqual(receipt["retained_run"], receipt["plain_run"])
            shard = root / "tasks/2/0/training_rows.jsonl"
            with patch.object(sys, "argv", ["audit", "--data", str(shard), "--store", str(args.store)]):
                audit()

    def test_suffix_records_removed_only_after_acceptance(self):
        from steerdistill.analysis import merge_steer_step
        from scripts.validate.validate_skills import transition_with_steps
        from unittest.mock import Mock
        previous = [{"assistant_turn": turn, "index": turn + 1, "step_id": str(turn),
                     "status": "verified", "causal_signature": "same"} for turn in (0, 2, 4)]
        current = {"assistant_turn": 2, "step_id": "replacement", "status": "proposed",
                   "causal_signature": "same"}
        proposed = merge_steer_step(previous, current, "recurrence")
        self.assertEqual(len(proposed), 4)
        store = Mock()
        skill = {"skill_id": "test", "skill": "guidance"}
        transition_with_steps(store, skill, "unresolved", proposed)
        self.assertEqual(len(store.transition.call_args.kwargs["steer_steps"]), 4)
        transition_with_steps(store, skill, "locally_verified", proposed)
        kept = store.transition.call_args.kwargs["steer_steps"]
        self.assertEqual([step["step_id"] for step in kept], ["0", "replacement"])

    def test_failed_proposal_does_not_replace_accepted_memory(self):
        from steerdistill.analysis import accepted_memory
        accepted = {"status": "locally_verified", "integrated_steer": "accepted guidance"}
        failed = {"status": "unresolved", "integrated_steer": "failed guidance"}
        self.assertIsNone(accepted_memory({"steer_steps": [failed]}))
        result = accepted_memory({"skill": "failed guidance", "steer_steps": [accepted, failed]})
        self.assertEqual(result["skill"], "accepted guidance")
        self.assertEqual(result["steer_steps"], [accepted])

    def test_exhausted_steering_keeps_retained_trajectory_without_takeover(self):
        analysis = {"decision": "create", "summary": "Choose the valid step",
                    "failure_type": "decision_mismatch", "failure_mechanism": "Wrong action",
                    "relation_to_prior": "new", "causal_assistant_turn": 0,
                    "steer": {"precondition": "Unfinished", "decision_rule": "Choose correct",
                              "expected_transition": "Advance", "recovery_check": "Progress"}}
        for keep_first in (False, True):
            with self.subTest(keep_first=keep_first), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=2,
                                       retries=2, output=root, store=root / "store.jsonl",
                                       student_url="student", teacher_url="teacher", model="test")
                teacher_calls = []

                def generate(url, model, messages, seed):
                    if url == "teacher":
                        teacher_calls.append(messages)
                    steered = any(m["role"] == "system" for m in messages)
                    first = messages[-1]["content"] == "state0"
                    correct = url == "teacher" or (keep_first and steered and first)
                    return "<action>correct</action>" if correct else "<action>wrong</action>", {}

                with patch.object(online_rollout, "Environment", DeterministicEnvironment), \
                     patch.object(online_rollout, "generate", side_effect=generate), \
                     patch.object(online_rollout, "grounded_analysis", return_value=analysis):
                    steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 5}}))
                self.assertEqual(len(teacher_calls), 2)  # Only the fixed reference episode.
                directory = root / "tasks/5/0"
                self.assertFalse((directory / "takeover").exists())
                shard = directory / "training_rows.jsonl"
                rows = [json.loads(line) for line in shard.read_text().splitlines()]
                expected = ["skill_recovery", "ordinary_opd"] if keep_first else ["ordinary_opd"]
                self.assertEqual([row["distill_mode"] for row in rows], expected)
                self.assertTrue(all(not row["verifier"]["success"] for row in rows))
                with patch.object(sys, "argv", ["audit", "--data", str(shard), "--store", str(args.store)]):
                    audit()

    def test_streaming_exhaustion_never_requests_teacher_action(self):
        from steerdistill.stream_repair import RepairConsumer
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            (work / "initial.pairs.jsonl").write_text(json.dumps({
                "corrected_trajectory_path": str(work / "reference"),
                "divergence": {"assistant_turn": 0}}) + "\n")
            consumer = object.__new__(RepairConsumer)
            consumer.args = SimpleNamespace(validation_attempts=2)
            with patch.object(consumer, "latest_status", return_value="unresolved"), \
                 patch.object(consumer, "latest_record", return_value={"skill": "Try correct"}), \
                 patch.object(consumer, "analyze"), \
                 patch.object(consumer, "validate_attempt") as attempt:
                self.assertEqual(consumer.validate(work / "prompt", work, "task", 0),
                                 "retained_after_exhausted_retries")
                self.assertEqual(attempt.call_count, 2)
                self.assertTrue(all(call.args[-1] == "steer" for call in attempt.call_args_list))

    def test_multiple_local_repairs_preserve_prefix_and_actual_context(self):
        analysis = {"decision": "create", "summary": "Use the next valid step.",
                    "failure_type": "decision_mismatch", "failure_mechanism": "Wrong action",
                    "relation_to_prior": "new", "causal_assistant_turn": 0,
                    "steer": {"precondition": "An unfinished task", "decision_rule": "Choose a valid next step",
                              "expected_transition": "Advance", "recovery_check": "Observe progress"}}

        def generate(url, model, messages, seed):
            steered = any(m["role"] == "system" for m in messages)
            action = "correct" if url == "teacher" or steered else "wrong"
            return f"<think>Choose a step.</think><action>{action}</action>", {"seed": seed}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=2,
                                   retries=2, output=root, store=root / "store.jsonl",
                                   student_url="student", teacher_url="teacher", model="test")
            with patch.object(online_rollout, "Environment", DeterministicEnvironment), \
                 patch.object(online_rollout, "generate", side_effect=generate), \
                 patch.object(online_rollout, "grounded_analysis", return_value=analysis):
                counts = steerdistill.benchmarks.online_rollout.run_task((args, {"split": "train", "task": {"task_id": 3}}))
            self.assertEqual(counts["attempted"], 2)
            shard = root / "tasks/3/0/training_rows.jsonl"
            rows = [json.loads(line) for line in shard.read_text().splitlines()]
            self.assertEqual([r["distill_mode"] for r in rows], ["skill_recovery", "skill_recovery"])
            self.assertEqual([r["prompt"] for r in rows], [[{"role": "user", "content": "state0"}],
                                                          [{"role": "user", "content": "state1"}]])
            self.assertNotEqual(rows[0]["state_snapshot"]["snapshot_id"], rows[1]["state_snapshot"]["snapshot_id"])
            with patch.object(sys, "argv", ["audit", "--data", str(shard), "--store", str(args.store)]):
                audit()
            with patch.object(online_rollout, "Environment", side_effect=AssertionError("resume must not rerun")):
                self.assertEqual(steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 3}})), counts)

    def test_no_reference_requires_real_failed_reference_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(benchmark="alfworld", step=1, attempts=1, reference_attempts=2,
                                   retries=2, output=root, store=root / "store.jsonl",
                                   student_url="student", teacher_url="teacher", model="test")
            with patch.object(online_rollout, "Environment", DeterministicEnvironment), \
                 patch.object(online_rollout, "generate", return_value=("<action>wrong</action>", {})):
                counts = steerdistill.benchmarks.online_rollout.run_task((args, {"task": {"task_id": 4}}))
            self.assertEqual(counts["reference_found"], 0)
            shard = root / "tasks/4/0/training_rows.jsonl"
            with patch.object(sys, "argv", ["audit", "--data", str(shard), "--store", str(args.store)]):
                audit()
            receipt_path = root / "tasks/4/0/completed.json"
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(len(receipt["reference_runs"]), 2)
            Path(receipt["reference_runs"][0], "verify.code.json").unlink()
            from scripts.data.audit_training_data import audit_ordinary_fallback
            audit_ordinary_fallback.cache_clear()
            with patch.object(sys, "argv", ["audit", "--data", str(shard), "--store", str(args.store)]):
                with self.assertRaisesRegex(ValueError, "evidence"):
                    audit()


if __name__ == "__main__":
    unittest.main()
