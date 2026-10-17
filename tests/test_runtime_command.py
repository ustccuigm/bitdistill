"""Check architecture-specific inference flags without starting a server."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from runtime import Runtime


class RuntimeCommandTest(unittest.TestCase):
    def test_text_models_and_tool_parsers(self):
        for model_type, parser in (("qwen3", "hermes"), ("qwen3_5", "qwen3_xml"),
                                   ("gemma4_unified_text", "gemma4")):
            with self.subTest(model_type=model_type), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "config.json").write_text(json.dumps({"model_type": model_type}))
                process = MagicMock()
                process.poll.return_value = 1
                with patch.dict(os.environ, INFERENCE_ENV_ROOT=directory,
                                TMPDIR=directory + "/" + "long-run-name" * 20), \
                     patch("runtime.subprocess.Popen", return_value=process) as start:
                    runtime = Runtime(root, "student", "0", 0, root / "server.log", tool_calls=True)
                    with self.assertRaisesRegex(RuntimeError, "Inference server exited"):
                        runtime.__enter__()
                command = start.call_args.args[0]
                self.assertEqual(command[command.index("--tool-call-parser") + 1], parser)
                self.assertEqual(command[command.index("--reasoning-parser") + 1],
                                 "gemma4" if model_type == "gemma4_unified_text" else "qwen3")
                self.assertEqual("--language-model-only" in command, model_type == "qwen3_5")
                self.assertEqual("--enforce-eager" in command, model_type == "gemma4_unified_text")
                self.assertTrue(runtime.handle.closed)
                rpc = start.call_args.kwargs["env"]["VLLM_RPC_BASE_PATH"]
                self.assertLess(len(os.fsencode(rpc)) + 37, 108)


if __name__ == "__main__":
    unittest.main()
