import io
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from types import SimpleNamespace

from steerdistill.analysis import (AnalysisRejected, STEER_FIELDS, call_analyzer,
                                   trajectory_view, _compact_retry_feedback, _local_verifier_feedback)
from steerdistill.benchmarks.online_rollout import generate
from steerdistill.generation_evidence import (MissingReasoning, enable_thinking,
                                              require_reasoning, verifier_summary)


class GenerationEvidenceTest(unittest.TestCase):
    def analysis(self):
        return dict(decision="create", summary="Check the account", failure_mechanism="Wrong account",
                    failure_type="wrong_argument", relation_to_prior="new", causal_assistant_turn=0,
                    steer={key: "Check the account" for key in STEER_FIELDS})

    def test_explicit_thinking_preserves_template_options_and_rejects_disabled(self):
        payload = {"chat_template_kwargs": {"custom_option": 1}}
        enable_thinking(payload)
        self.assertEqual(payload["chat_template_kwargs"], {"custom_option": 1, "enable_thinking": True})
        self.assertTrue(payload["include_reasoning"])
        with self.assertRaisesRegex(ValueError, "enable_thinking"):
            enable_thinking({"chat_template_kwargs": {"enable_thinking": False}})

    def test_empty_thought_is_not_replaced_by_action_or_metadata(self):
        for msg in ({"content": "<think> </think>do action"},
                    {"reasoning": "", "content": "do action"}, {"content": None, "tool_calls": [{}]}):
            with self.assertRaises(MissingReasoning):
                require_reasoning(msg)
        self.assertEqual(require_reasoning({"content": "<think>Inspect state.</think>act"}), "Inspect state.")
        self.assertEqual(require_reasoning({"reasoning_content": " Inspect state. "}), "Inspect state.")

    def test_teacher_saves_exact_exchange_and_retains_reasoning(self):
        message = {"content": json.dumps(self.analysis()), "reasoning": "The requested account differs."}
        raw = {"choices": [{"message": message, "finish_reason": "stop"}]}
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)
            with patch("steerdistill.analysis.apply_budget", side_effect=lambda u,b,k:b), \
                 patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(raw).encode())):
                result = call_analyzer("http://local/v1", "secret", "teacher", "{}", dest)
            self.assertEqual(result["teacher_reasoning"], message["reasoning"])
            self.assertEqual(json.loads((dest / "attempt-0/response.json").read_text()), raw)
            request = json.loads((dest / "attempt-0/request.json").read_text())
            self.assertTrue(request["chat_template_kwargs"]["enable_thinking"])
            self.assertNotIn("secret", json.dumps(request))

    def test_teacher_rejects_empty_thinking_and_truncated_json_but_keeps_raw(self):
        for reasoning, finish in (("", "stop"), ("Inspect state", "length")):
            with self.subTest(reasoning=reasoning, finish=finish), tempfile.TemporaryDirectory() as folder:
                raw = {"choices": [{"message": {"content": json.dumps(self.analysis()), "reasoning": reasoning}, "finish_reason": finish}]}
                with patch("steerdistill.analysis.apply_budget", side_effect=lambda u,b,k:b), \
                     patch("urllib.request.urlopen", side_effect=lambda *a,**k:io.BytesIO(json.dumps(raw).encode())):
                    with self.assertRaises(AnalysisRejected):
                        call_analyzer("http://local/v1", "EMPTY", "teacher", "{}", Path(folder))
                self.assertEqual(len(list(Path(folder).glob("*/response.json"))), 5)

    def test_student_empty_thinking_is_rejected_before_execution_and_saved(self):
        raw = {"choices": [{"message": {"content": "<action>look</action>", "reasoning": ""}, "finish_reason": "stop"}]}
        with tempfile.TemporaryDirectory() as folder:
            with patch("steerdistill.benchmarks.online_rollout.apply_budget", side_effect=lambda u,b:b), \
                 patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(raw).encode())):
                with self.assertRaises(MissingReasoning):
                    generate("http://local/v1", "student", [], 42, Path(folder))
            self.assertEqual(json.loads((Path(folder) / "response.json").read_text()), raw)

    def test_verifier_answers_cannot_reach_teacher(self):
        result = verifier_summary({"reward_type": "incomplete", "expected_answer": "SECRET",
                 "verify_result": {"execution_status": "failed", "error": "SECRET", "details": {"answer": "SECRET"}}})
        self.assertEqual(result, {"reward_type": "incomplete", "verify_result": {"execution_status": "failed"}})
        self.assertEqual(verifier_summary({"reward_type": "SECRET", "passed": "SECRET"}), {})

    def test_trajectory_view_excludes_next_decision_and_grader_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "trajectory.json").write_text(json.dumps({"scenario": "s", "task_id": 1, "messages": [
                {"role": "user", "content": "task"}, {"role": "assistant", "content": "current action"},
                {"role": "tool", "content": "current result"}, {"role": "assistant", "content": "FUTURE_ANSWER"}]}))
            (path / "verify.code.json").write_text(json.dumps({"verify_result": {"ground_truth": "GRADER_ANSWER"}}))
            view = json.dumps(trajectory_view(str(path / "trajectory.json"), 0))
            self.assertIn("current result", view)
            self.assertNotIn("FUTURE_ANSWER", view)
            self.assertNotIn("GRADER_ANSWER", view)

    def test_retry_feedback_stops_at_failed_local_turn(self):
        value = [{"assistant_turn": 0, "local_feedback": [{"accepted": False, "reason": "GRADER_ANSWER"}],
                  "candidate_trajectories": [{"messages": [{"role": "assistant", "content": "failed action"},
                                                            {"role": "assistant", "content": "FUTURE_ANSWER"}]}]}]
        result = json.dumps(_compact_retry_feedback(value))
        self.assertIn("failed action", result)
        self.assertNotIn("FUTURE_ANSWER", result)
        self.assertNotIn("GRADER_ANSWER", result)
        del value[0]["assistant_turn"]
        self.assertNotIn("failed action", json.dumps(_compact_retry_feedback(value)))

    def test_native_feedback_excludes_reference_answers_and_grader_details(self):
        feedback = [{"response": "failed local action", "expected": {"action": "ANSWER_SENTINEL"},
                     "transition": {"ground_truth": "ANSWER_SENTINEL"}, "reason": "postcondition_state_mismatch"}]
        result = json.dumps(_local_verifier_feedback(feedback))
        self.assertIn("failed local action", result)
        self.assertNotIn("ANSWER_SENTINEL", result)

    def test_materialization_and_prefix_preserve_split_thought_once(self):
        from steerdistill.materialize import assistant_completion
        from steerdistill.common import api_messages
        for key in ("reasoning", "reasoning_content"):
            msg = {"role": "assistant", "content": "act", key: "ACTUAL_THOUGHT"}
            completion = assistant_completion(msg)
            prefix = api_messages([msg])
            self.assertEqual(completion, "<think>ACTUAL_THOUGHT</think>act")
            self.assertEqual(api_messages(prefix), prefix)
            self.assertEqual(assistant_completion(prefix[0]), completion)
        self.assertEqual(assistant_completion({"content": "ACTUAL_THOUGHT</think>act"}),
                         "<think>ACTUAL_THOUGHT</think>act")

    def test_native_tools_keep_thought_through_training_loader(self):
        try:
            from steerdistill.training.data_loading import _extract_prompt_completion
        except ImportError:
            self.skipTest("Training dependencies unavailable")
        from steerdistill.materialize import rows_from_run
        for key in ("reasoning", "reasoning_content"):
            call = [{"id": "1", "type": "function", "function": {"name": "inspect", "arguments": "{}"}}]
            run = {"run_dir": "test", "success": True, "trajectory": {"scenario": "s", "task_id": 1,
                   "messages": [{"role": "user", "content": "task"},
                                {"role": "assistant", "content": None, key: "ACTUAL_THOUGHT", "tool_calls": call}]}}
            row = rows_from_run(run, "ordinary_opd")[0]
            loaded = _extract_prompt_completion(row, None)
            self.assertEqual(loaded["completion"], "<think>ACTUAL_THOUGHT</think>")
            self.assertEqual(loaded["completion_tool_calls"], call)

    def test_training_bridge_rejects_empty_tool_reasoning_and_keeps_response(self):
        from steerdistill.teacher.response_bridge import bridge_endpoint
        requests = []
        class Upstream(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                raw = {"choices": [{"message": {"role": "assistant", "content": None, "reasoning": "",
                    "tool_calls": [{"function": {"name": "act", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]}
                data = json.dumps(raw).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        try:
            with tempfile.TemporaryDirectory() as folder, \
                 patch("steerdistill.teacher.response_bridge.apply_budget", side_effect=lambda u,b:b), \
                 bridge_endpoint(f"http://127.0.0.1:{server.server_port}", evidence_dir=folder, training=True) as endpoint:
                request = urllib.request.Request(endpoint + "/chat/completions", data=json.dumps({"model": "test", "messages": [], "tools": [{}]}).encode())
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code, 502)
                self.assertTrue(requests[0]["chat_template_kwargs"]["enable_thinking"])
                self.assertEqual(len(list(Path(folder).glob("*/response.json"))), 1)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_unverified_old_cache_and_changed_evidence_are_rejected(self):
        from steerdistill.generation_evidence import write_run_receipt, validate_run_receipt
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("trajectory.json", "verify.code.json"):
                (root / name).write_text("{}")
            with self.assertRaisesRegex(ValueError, "lacks generation evidence"):
                validate_run_receipt(root)
            (root / "generations/first").mkdir(parents=True)
            (root / "generations/first/response.json").write_text("{}")
            write_run_receipt(root); validate_run_receipt(root)
            (root / "trajectory.json").write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, "changed"):
                validate_run_receipt(root)

    def test_native_resume_rejects_missing_generation_even_with_valid_training_shard(self):
        from steerdistill.generation_evidence import generation_files
        from steerdistill.benchmarks.online_rollout import run_task
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            run = root / "tasks/1/0"
            exchange = run / "plain/generations/turn0000"
            exchange.mkdir(parents=True)
            (exchange / "request.json").write_text('{}')
            (exchange / "response.json").write_text('{}')
            shard = run / "training_rows.jsonl";shard.write_text('{}\n')
            receipt = {"generation_evidence_version": 1, "generation_files": generation_files(run),
                       "rows_sha256": hashlib.sha256(shard.read_bytes()).hexdigest()}
            (run / "completed.json").write_text(json.dumps(receipt))
            (exchange / "response.json").unlink()
            with self.assertRaisesRegex(ValueError, "generation"):
                run_task((SimpleNamespace(attempts=1, output=root), {"task": {"task_id": 1}}))


if __name__ == "__main__":
    unittest.main()
