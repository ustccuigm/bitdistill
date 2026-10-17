"""Exercise the external adapter's actual loop without model or MCP processes.

Set STEER_TOOL_ENV_AGENT_SOURCE to the patched external agent module.
"""
import ast
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import urlparse


class RequestError(Exception):
    def __init__(self, body):
        self.body = body


@unittest.skipUnless(os.getenv("STEER_TOOL_ENV_AGENT_SOURCE"), "external adapter source not configured")
class ToolContextTerminationTest(unittest.TestCase):
    def run_loop(self, responses, gate=None):
        source = Path(os.environ["STEER_TOOL_ENV_AGENT_SOURCE"])
        tree = ast.parse(source.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                        and node.name == "run_agent")
        executor = SimpleNamespace(list_tools=AsyncMock(return_value=[]))
        generate = AsyncMock(side_effect=responses)
        scope = {"Config": object, "os": os, "datetime": datetime, "urlparse": urlparse,
                 "json": json, "logger": Mock(), "AsyncOpenAI": Mock(),
                 "MCPToolExecutor": Mock(return_value=executor), "generate_response": generate,
                 "BadRequestError": RequestError, "get_system_prompt": lambda: "system",
                 "format_tools_for_response": lambda tools: "catalog",
                 "resolve_llm_config": lambda **kwargs: ("http://localhost/v1", "EMPTY", "test"),
                 "tools_json_save": lambda value, path: Path(path).write_text(json.dumps(value)),
                 "_write_state_snapshot": Mock()}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), scope)
        with tempfile.TemporaryDirectory() as folder:
            config = SimpleNamespace(scenario="test", task_id=0, task="task", api_url="local",
                model="test", output_dir=folder, restore_snapshot=None, mcp_url="fake",
                snapshot_dir=folder if gate else None, max_iterations=30, verbose=False, temperature=0.7,
                behavior_logprobs=True)
            if gate:
                with patch.dict(os.environ, STEER_LOCAL_GATE="test", STEER_LOCAL_GATE_MODULE="test"), \
                     patch("runpy.run_path", return_value={"check_boundary": gate}):
                    asyncio.run(scope["run_agent"](config))
            else:
                asyncio.run(scope["run_agent"](config))
            result = json.loads(Path(folder, "trajectory.json").read_text())
        return result, generate.await_count

    def test_local_rejection_stops_before_next_model_request(self):
        action = ("inspect", [{"id": "1", "name": "list_tools", "arguments": {}}], {"finish_reason": "stop"})
        gate = Mock(return_value=False)
        result, calls = self.run_loop([action, ("must not run", [], {})], gate=gate)
        self.assertEqual(calls, 1)
        self.assertEqual(result["termination_reason"], "local_transition_rejected")
        gate.assert_called_once()

    def test_local_acceptance_precedes_continuation(self):
        action = ("inspect", [{"id": "1", "name": "list_tools", "arguments": {}}], {"finish_reason": "stop"})
        gate = Mock(return_value=True)
        result, calls = self.run_loop([action, ("done", [], {"finish_reason": "stop"})], gate=gate)
        self.assertEqual(calls, 2)
        self.assertEqual(result["termination_reason"], "completed")
        gate.assert_called_once()

    def test_overlong_tool_observation_preserves_real_prefix(self):
        response = ("inspect", [{"id": "call_1", "name": "list_tools", "arguments": {}}],
                    {"finish_reason": "stop", "token_ids": [42], "logprobs": [-0.3]})
        error = RequestError({"code": "context_length_exceeded", "prompt_tokens": 33370,
                              "context_window": 32768})
        result, calls = self.run_loop([response, error])
        self.assertEqual(calls, 2)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["termination_reason"], "context_length")
        self.assertEqual(result["total_iterations"], 1)
        self.assertEqual(len(result["trajectory"]), 1)
        self.assertEqual(result["messages"][-1]["content"], "catalog")
        self.assertEqual(result["trajectory"][0]["sampling"]["token_ids"], [42])

    def test_length_limited_response_is_not_marked_final(self):
        result, calls = self.run_loop([("unfinished reasoning", [], {"finish_reason": "length"})])
        self.assertEqual(calls, 1)
        self.assertEqual(result["termination_reason"], "generation_length")
        self.assertFalse(result["trajectory"][0]["is_final"])

    def test_length_limited_tool_response_stops_after_actual_tool(self):
        response = ("inspect", [{"id": "call_1", "name": "list_tools", "arguments": {}}],
                    {"finish_reason": "length"})
        result, calls = self.run_loop([response])
        self.assertEqual(calls, 1)
        self.assertEqual(result["messages"][-1]["role"], "tool")
        self.assertTrue(result["truncated"])

    def test_unrelated_request_error_still_fails(self):
        with self.assertRaises(RequestError):
            self.run_loop([RequestError({"code": "invalid_model"})])

    def test_normal_completion_is_unchanged(self):
        result, calls = self.run_loop([("done", [], {"finish_reason": "stop"})])
        self.assertEqual(calls, 1)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["termination_reason"], "completed")


if __name__ == "__main__":
    unittest.main()
