"""Contract tests for isolation and real assistant targets in the shared route."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
from data_loading import _extract_prompt_completion, DataCollatorForSupervisedDataset
from test_pipeline import TinyTokenizer


class BenchmarkRouteTest(unittest.TestCase):
    def test_export_preserves_multimodal_processor_metadata(self):
        import tempfile
        from convert_hf_to_awq_runtime import copy_processor_metadata
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root / "source", root / "output"
            source.mkdir()
            output.mkdir()
            expected = {"image_processor_type": "Qwen3VLImageProcessor", "size": {"longest_edge": 4194304}}
            (source / "preprocessor_config.json").write_text(json.dumps(expected))
            (source / "video_preprocessor_config.json").write_text(json.dumps({"fps": 2}))
            copy_processor_metadata(source, output)
            self.assertEqual(json.loads((output / "preprocessor_config.json").read_text()), expected)
            self.assertEqual(json.loads((output / "video_preprocessor_config.json").read_text()), {"fps": 2})

    def test_calibration_rejects_test_data_and_raw_catalogs(self):
        spec = importlib.util.spec_from_file_location("prepare_data", ROOT / "benchmarks/prepare_data.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(ValueError, "split"):
            module.calibration_record({"prompt": "question", "extra_info": {"split": "test"}})
        with self.assertRaisesRegex(ValueError, "raw benchmark"):
            module.calibration_record({"record": {"asin": "product"}})
        with self.assertRaisesRegex(ValueError, "Serialized"):
            module.calibration_record({"prompt": json.dumps({"record": {"asin": "product"}})})
        row = module.calibration_record({"prompt": [{"role": "user", "content": "question"}],
                                         "split": "train", "reward_model": {"answer": "hidden"}})
        self.assertNotIn("reward_model", row)
        self.assertNotIn("completion", row)

    def test_external_adapter_requires_verifier_and_exact_restore(self):
        spec = importlib.util.spec_from_file_location("adapter_contract", ROOT / "benchmarks/validate_adapter_output.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = {"benchmark": "webshop", "task_key": "task:1", "completion": "click", "source_run": "/run",
               "verifier": {"success": True}, "state_snapshot": {
                   "snapshot_id": "s1", "prefix_hash": "p", "before_state_hash": "b", "after_state_hash": "a"},
               "restore_verified": True}
        module.validate(row, 1, "webshop")
        for key in ("verifier", "state_snapshot", "restore_verified"):
            invalid = dict(row)
            invalid.pop(key)
            with self.assertRaises(ValueError):
                module.validate(invalid, 1, "webshop")

    def test_revised_turns_bind_individual_verified_steps(self):
        from materialize_training_data import rows_from_run
        run = {"trajectory": {"scenario": "s", "task_id": 1, "messages": [
            {"role": "user", "content": "task"}, {"role": "assistant", "content": "first"},
            {"role": "tool", "content": "observation"}, {"role": "assistant", "content": "second"},
        ]}, "success": True, "run_dir": "/run"}
        skill = {"skill_id": "skill", "version": 1}
        steps = {0: {"step_id": "first-step", "index": 1, "status": "locally_verified"},
                 1: {"step_id": "second-step", "index": 2, "status": "verified"}}
        rows = rows_from_run(run, "revised", skill, {0: "rule1", 1: "rule2"},
                             {0: "skill_recovery", 1: "skill_recovery"}, steps)
        self.assertEqual([r["steer_step_id"] for r in rows], ["first-step", "second-step"])
        self.assertTrue(all(r["local_transition_verified"] for r in rows))

    def test_clipping_preserves_per_group_bounds(self):
        import torch
        from quantization.clip_state import clipped_weight
        weight = torch.tensor([[-4., 4., -8., 8.]])
        maximum = torch.tensor([[[2.], [3.]]])
        minimum = torch.tensor([[[-1.], [-2.]]])
        self.assertTrue(torch.equal(clipped_weight(weight, (maximum, minimum)),
                                    torch.tensor([[-1., 2., -2., 3.]])))

    def test_all_fifteen_routes_are_isolated_and_tool_checkpoints_shared(self):
        paths = {}
        script = '''set -a
source "$1/config.example.env"
printf '%s\n' "$MODEL_SOURCE_PATH" "$RUN_ROOT" "$CLIP_PATH" "$STEER_SKILL_STORE" "$INITIAL_RUNTIME_W4"
'''
        for model in ("qwen3_8b", "qwen3_5_4b", "gemma4_12b"):
            for benchmark in ("bfcl_v4", "tau2_bench", "webshop", "alfworld", "search_qa"):
                env = {"PATH": os.environ["PATH"], "STEER_ASSET_ROOT": "/assets",
                       "ENV_ROOT": "/environment", "MODEL_FAMILY": model, "BENCHMARK": benchmark}
                values = subprocess.check_output(["bash", "-c", script, "bash", str(ROOT)],
                                                 env=env, text=True).splitlines()
                paths[model, benchmark] = values
                self.assertIn(f"/{model}/{benchmark}", values[1])
                training_benchmark = "bfcl_v4" if benchmark == "tau2_bench" else benchmark
                for value in values[2:]:
                    self.assertIn(f"/{model}/{training_benchmark}", value)
        self.assertEqual(len({v[1] for v in paths.values()}), 15)
        for column in range(2, 5):
            self.assertEqual(len({v[column] for v in paths.values()}), 12)
        for model in ("qwen3_8b", "qwen3_5_4b", "gemma4_12b"):
            self.assertEqual(paths[model, "bfcl_v4"][0], paths[model, "tau2_bench"][0])
            self.assertEqual(paths[model, "bfcl_v4"][2:], paths[model, "tau2_bench"][2:])
            self.assertEqual(len({paths[model, b][0] for b in ("bfcl_v4", "webshop", "alfworld", "search_qa")}), 4)

    def test_newline_placeholder_cannot_train(self):
        collator = DataCollatorForSupervisedDataset(TinyTokenizer())
        with self.assertRaisesRegex(ValueError, "whitespace completion"):
            collator([{"prompt": "question", "completion": "\n", "skill_prompt": "question", "distill_mode": "ordinary_opd"}])

    def test_messages_preserve_native_tool_calls(self):
        call = {"type": "function", "function": {"name": "lookup", "arguments": "{}"}}
        row = _extract_prompt_completion({"messages": [
            {"role": "user", "content": "query"},
            {"role": "assistant", "content": None, "tool_calls": [call]},
        ]}, TinyTokenizer())
        self.assertEqual(row["completion"], "")
        self.assertEqual(row["completion_tool_calls"], [call])
        self.assertIsInstance(row["prompt"], list)

    def test_fsdp_selection_uses_checkpoint_architecture(self):
        spec = importlib.util.spec_from_file_location("select_fsdp", ROOT / "common/select_fsdp.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.select({"model_type": "qwen3_5"}), "fsdp2_8gpu_qwen3_5.yaml")
        self.assertEqual(module.select({"model_type": "qwen3"}), "fsdp2_8gpu.yaml")
        self.assertEqual(module.select({"model_type": "gemma4_unified_text"}), "fsdp2_8gpu_gemma4.yaml")
        with self.assertRaises(ValueError):
            module.select({"model_type": "unknown"})

    def test_eval_requires_a_trained_runtime_and_never_starts_training(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, STEER_ASSET_ROOT=directory, BENCHMARK="bfcl_v4",
                       MODEL_FAMILY="qwen3_8b", MODEL_SERVING_NAME="student", RUN_ROOT=directory)
            result = subprocess.run(["bash", str(ROOT / "benchmarks/evaluate.sh"), "1"],
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing trained runtime", result.stderr)
            self.assertFalse((Path(directory) / "steps").exists())


if __name__ == "__main__":
    unittest.main()
