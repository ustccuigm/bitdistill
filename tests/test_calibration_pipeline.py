"""Calibration must preserve agent context and reject stale cache reuse."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from steerdistill.quantization.clip_provenance import check_manifest, sha256
from steerdistill.benchmarks import prepare_data as calibration


class CalibrationPipelineTest(unittest.TestCase):
    def test_training_signal_requires_finite_nonzero_gradients_and_complete_steps(self):
        from scripts.validate.check_training_signal import check
        state = {"global_step": 2, "log_history": [
            {"step": 1, "loss": 0.3, "grad_norm": 0.1},
            {"step": 2, "loss": 0.2, "grad_norm": 0.08},
        ]}
        self.assertEqual(check(state, 2)["status"], "passed")
        with self.assertRaisesRegex(ValueError, "complete"):
            check(state, 3)
        for gradient in (0., float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                check({"global_step": 1, "log_history": [{"loss": 0.2, "grad_norm": gradient}]}, 1)

    def test_cleanup_preserves_native_actions_and_tool_schema(self):
        call = {"type": "function", "function": {"name": "lookup", "arguments": "{}"}}
        tools = [{"type": "function", "function": {"name": "lookup"}}]
        row = calibration.calibration_record({
            "prompt": [{"role": "user", "content": "look up the price"}],
            "completion": "", "completion_tool_calls": [call], "tools": tools,
        })
        self.assertEqual(row["messages"][-1]["tool_calls"], [call])
        self.assertEqual(row["tools"], tools)
        clean = calibration.calibration_record({"messages": [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "\n"},
        ]})
        self.assertEqual(len(clean["messages"]), 1)
        self.assertNotIn("completion", clean)

    def test_dedup_reports_actual_input_and_output_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "raw.jsonl", Path(directory) / "clean.jsonl"
            source.write_text(json.dumps({"prompt": "question", "completion": "\n"}) + "\n"
                              + json.dumps({"prompt": "question"}) + "\n")
            report = calibration.prepare(source, output)
            self.assertEqual(report["kept_records"], 1)
            self.assertEqual(report["duplicate_records"], 1)
            self.assertEqual(report["source_sha256"], sha256(source))
            self.assertEqual(report["output_sha256"], sha256(output))
            self.assertEqual(json.loads(output.read_text()), {"prompt": "question"})

    def test_bad_data_does_not_replace_previous_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "raw.jsonl", Path(directory) / "clean.jsonl"
            source.write_text(json.dumps({"prompt": "test question", "split": "test"}) + "\n")
            output.write_text("previous output")
            with self.assertRaisesRegex(ValueError, "split"):
                calibration.prepare(source, output)
            self.assertEqual(output.read_text(), "previous output")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                calibration.prepare(source, source)

    def test_cache_rejects_changed_inputs_and_changed_content(self):
        with tempfile.TemporaryDirectory() as directory:
            clip = Path(directory) / "clip.pt"
            clip.write_bytes(b"test cache")
            inputs = {"model": "weights-A", "data_sha256": "data-A"}
            recorded = {"inputs": inputs, "clip_sha256": sha256(clip)}
            check_manifest(recorded, inputs, clip)
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                check_manifest(recorded, {**inputs, "model": "weights-B"}, clip)
            clip.write_bytes(b"changed cache")
            with self.assertRaisesRegex(ValueError, "checksum"):
                check_manifest(recorded, inputs, clip)

    def test_empty_clip_cannot_pass_validation(self):
        import torch
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.pt"
            torch.save({"clip": []}, path)
            result = subprocess.run([sys.executable, "-m", "steerdistill.teacher.validate_clip",
                                     str(path)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonempty", result.stderr)


if __name__ == "__main__":
    unittest.main()
