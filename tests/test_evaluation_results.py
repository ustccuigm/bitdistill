import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from evaluate_bfcl import register_model, serializable_messages, validate_results


class EvaluationResultTest(unittest.TestCase):
    def test_native_context_limit_retains_real_evaluation_prefix(self):
        import evaluate_sdar
        from generation_budget import ContextWindowExceeded
        env = SimpleNamespace(done=False, success=False, score=0., turn=1,
                              prompt=lambda: "long history", close=lambda: None)
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(benchmark="webshop", output=Path(directory), url="local", model="test", seed=42)
            with patch.object(evaluate_sdar, "Environment", return_value=env), \
                 patch.object(evaluate_sdar, "generate", side_effect=ContextWindowExceeded(32768, 33000)):
                self.assertEqual(evaluate_sdar.evaluate_task((args, {"task_id": 0})), ("webshop", False, 0.))
            saved = json.loads((Path(directory) / "tasks/0.json").read_text())
            self.assertEqual(saved["trajectory"], [])
            self.assertEqual(saved["termination"]["reason"], "context_length")

    def test_bfcl_escaped_registry_key_keeps_the_served_model_identity(self):
        from types import SimpleNamespace
        for name in ("Qwen3-8B", "qwen3_5_4b", "google/gemma-4-12B-it"):
            registry = {}
            config = SimpleNamespace(model_name=name)
            register_model(registry, name, config)
            restored = name.replace("/", "_").replace("_", "/")
            self.assertIs(registry[restored], config)
            self.assertEqual(registry[restored].model_name, name)

    def test_sdk_messages_keep_tool_calls_and_reasoning(self):
        from pydantic import BaseModel

        class Message(BaseModel):
            role: str
            content: str | None = None
            reasoning: str
            tool_calls: list[dict]

        message = Message(role="assistant", reasoning="Inspect state first.",
            tool_calls=[{"id": "call1", "type": "function", "function": {"name": "ls", "arguments": "{}"}}])
        raw = [{"role": "user", "content": "List files."}, message]
        normalized = json.loads(json.dumps(serializable_messages(raw)))
        self.assertEqual(normalized[1]["tool_calls"], message.tool_calls)
        self.assertEqual(normalized[1]["reasoning"], message.reasoning)
        self.assertIs(raw[1], message)

    def test_upstream_inference_error_is_not_a_completed_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "multi_turn_base_result.json"
            path.write_text(json.dumps({"id": "task0", "result": "Error during inference: failure", "traceback": "trace"}) + "\n")
            with self.assertRaisesRegex(RuntimeError, "inference failed"):
                validate_results(root, {"task0"})
            path.write_text(json.dumps({"id": "task0", "result": []}) + "\n")
            validate_results(root, {"task0"})
            with self.assertRaisesRegex(RuntimeError, "every selected"):
                validate_results(root, {"task0", "task1"})
            path.write_text(path.read_text() * 2)
            with self.assertRaisesRegex(RuntimeError, "Duplicate"):
                validate_results(root, {"task0"})


if __name__ == "__main__":
    unittest.main()
