import json
from pathlib import Path
import sys
import concurrent.futures
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
import threading
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_budget import ContextWindowExceeded, apply_budget, available_tokens
from verified_teacher import response_bridge
from verified_teacher.response_bridge import preserve_reasoning


class GenerationBudgetTest(unittest.TestCase):
    def test_steering_context_exhaustion_has_same_length_contract(self):
        from skill_proxy import handler_for
        matched = {"skill": "steering instruction", "causal_divergence": {"assistant_turn": 0}}
        state = SimpleNamespace(upstream="http://127.0.0.1:1",
            route=lambda messages: (matched, "skill_inject", None), log=lambda row: None)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("generation_budget.context_window", return_value=32768), \
                 patch("generation_budget.read_json", return_value={"count": 33370}):
                request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                    data=json.dumps({"model": "test", "messages": [{"role": "user", "content": "task"}]}).encode(),
                    headers={"Content-Type": "application/json"})
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code, 400)
                self.assertEqual(json.load(caught.exception)["error"]["code"], "context_length_exceeded")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_exhausted_prompt_is_typed_without_mutating_history(self):
        body = {"model": "test", "messages": [{"role": "user", "content": "task"}],
                "max_tokens": 32768}
        original = json.loads(json.dumps(body))
        with patch("generation_budget.context_window", return_value=32768), \
             patch("generation_budget.read_json", return_value={"count": 33370}):
            with self.assertRaises(ContextWindowExceeded) as caught:
                apply_budget("http://localhost:1234/v1", body)
        self.assertEqual(caught.exception.as_error()["code"], "context_length_exceeded")
        self.assertEqual(caught.exception.prompt_tokens, 33370)
        self.assertEqual(body, original)

    def test_bridge_returns_nonretryable_length_error_without_generation(self):
        with patch("generation_budget.context_window", return_value=32768), \
             patch("generation_budget.read_json", return_value={"count": 33370}), \
             response_bridge.bridge_endpoint("http://127.0.0.1:1") as endpoint:
            request = urllib.request.Request(endpoint + "/chat/completions",
                data=json.dumps({"model": "test", "messages": [{"role": "user", "content": "task"}]}).encode(),
                headers={"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code, 400)
            error = json.load(caught.exception)["error"]
            self.assertEqual(error["code"], "context_length_exceeded")
            self.assertEqual(error["prompt_tokens"], 33370)

    def test_long_prompt_uses_remaining_window(self):
        self.assertEqual(available_tokens(32768, 30000, 32768), 2768)
        self.assertEqual(available_tokens(32768, 1000, 32768), 31768)
        self.assertEqual(available_tokens(32768, 1000, 128), 128)
        with self.assertRaises(ValueError):
            available_tokens(32768, 32768, 32768)

    def test_budget_counts_tools_and_steered_context(self):
        body = {"model": "model", "messages": [{"role": "system", "content": "steer"}],
                "tools": [{"type": "function"}], "max_completion_tokens": 32768,
                "chat_template_kwargs": {"enable_thinking": True}}
        with patch("generation_budget.context_window", return_value=32768), \
             patch("generation_budget.read_json", return_value={"count": 31000}) as count:
            apply_budget("http://localhost:1234/v1", body)
        self.assertEqual(body["max_completion_tokens"], 1768)
        self.assertEqual(count.call_args.args[1]["tools"], body["tools"])
        self.assertEqual(count.call_args.args[1]["messages"], body["messages"])

    def test_reasoning_and_native_calls_preserve_exact_logprobs(self):
        response = {"choices": [{"message": {"role": "assistant", "content": None,
                    "reasoning": "Check the price first", "tool_calls": [{"id": "call_1"}]},
                    "logprobs": {"content": [{"token": "token_id:42", "logprob": -0.3}]}}]}
        expected = json.loads(json.dumps(response["choices"][0]["logprobs"]))
        preserve_reasoning(response)
        preserve_reasoning(response)
        message = response["choices"][0]["message"]
        self.assertEqual(message["content"], "<think>Check the price first</think>")
        self.assertEqual(message["tool_calls"], [{"id": "call_1"}])
        self.assertEqual(response["choices"][0]["logprobs"], expected)

    def test_text_tool_action_survives_native_parser(self):
        raw = 'inspect</think>\n<tool_call>{"name":"list_tools","arguments":{}}</tool_call><|im_end|>'
        tokenizer = SimpleNamespace(eos_token="<|im_end|>", decode=lambda ids, **kw: raw)
        response = {"choices": [{"message": {"reasoning": "inspect", "content": ""},
                                 "logprobs": {"content": [{"token": "token_id:42", "logprob": -0.3}]}}]}
        preserve_reasoning(response, tokenizer)
        content = response["choices"][0]["message"]["content"]
        self.assertTrue(content.startswith("<think>inspect</think>"))
        self.assertIn('"name":"list_tools"', content)
        self.assertNotIn("<|im_end|>", content)

    def test_tokenizer_load_is_singleton_under_bridge_concurrency(self):
        calls = []

        class FakeTokenizer:
            pass

        class FakeAutoTokenizer:
            @staticmethod
            def from_pretrained(path):
                calls.append(path)
                time.sleep(0.01)
                return FakeTokenizer()

        fake_transformers = SimpleNamespace(AutoTokenizer=FakeAutoTokenizer)
        with patch.dict(sys.modules, {"transformers": fake_transformers}), \
             patch.dict(response_bridge._TOKENIZER_CACHE, {}, clear=True):
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
                loaded = list(pool.map(response_bridge.load_tokenizer, ["tokenizer"] * 16))
        self.assertEqual(calls, ["tokenizer"])
        self.assertEqual(len({id(tokenizer) for tokenizer in loaded}), 1)


if __name__ == "__main__":
    unittest.main()
