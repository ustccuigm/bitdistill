#!/usr/bin/env python3
"""Inject task-matched skill before forwarding to the W4 runtime."""

from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from steerdistill.common import canonical_decision, inject_skill, prompt_fingerprint, read_json
from steerdistill.store import SkillStore
from steerdistill.generation_budget import ContextWindowExceeded, apply_budget


class ProxyState:
    def __init__(
        self,
        upstream: str,
        store: Path,
        role_log: Path,
        statuses: set[str],
        mode: str = "steer",
        step: int | None = None,
    ):
        self.upstream = upstream.rstrip("/")
        self.mode = mode
        latest = SkillStore(store).latest_by_task(step)
        self.skills = [
            dict(row) for row in latest.values()
            if row["status"] in statuses and row.get("task_text") and row.get("skill")
            and (step is None or int(row.get("step", -1)) == step)
        ]
        usable = []
        for row in self.skills:
            trajectory_path = Path(str(row.get("failed_run_dir", ""))) / "trajectory.json"
            if not trajectory_path.is_file():
                continue
            trajectory = read_json(trajectory_path)
            # ``messages`` is the API history and intentionally omits the
            # behavior-policy sampling record.  Deterministic anchor replay
            # must use the full recorded trajectory entries so the replayed
            # W4 tokens retain their exact sampled logprobs.
            row["_anchor_turns"] = [
                message for message in trajectory.get("trajectory", [])
                if message.get("role") == "assistant"
            ]
            trigger = int(row["causal_divergence"]["assistant_turn"])
            if len(row["_anchor_turns"]) <= trigger:
                continue
            if self.mode == "teacher_rescue":
                corrected_path = Path(str(row.get("corrected_run_dir", ""))) / "trajectory.json"
                if not corrected_path.is_file():
                    continue
                corrected = read_json(corrected_path)
                row["_corrected_turns"] = [
                    message for message in corrected.get("trajectory", [])
                    if message.get("role") == "assistant"
                ]
                if len(row["_corrected_turns"]) <= trigger:
                    continue
            usable.append(row)
        self.skills = usable
        self.role_log = role_log
        self.role_log.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def match_task(self, messages: list[dict]) -> dict | None:
        text = "\n".join(str(message.get("content", "")) for message in messages)
        matches = [row for row in self.skills if row["task_text"] in text]
        return max(matches, key=lambda row: len(row["task_text"]), default=None)

    def route(self, messages: list[dict]) -> tuple[dict | None, str, dict | None]:
        row = self.match_task(messages)
        if row is None:
            return None, "plain", None
        assistant_turn = sum(message.get("role") == "assistant" for message in messages)
        prefix_decisions = [
            canonical_decision(message)
            for message in messages if message.get("role") == "assistant"
        ]
        expected = list(row.get("causal_prefix_decisions") or [])
        trigger = int(row["causal_divergence"]["assistant_turn"])
        # The paper's intervention starts from a restored state.  A request
        # that has not been restored must fail closed; replaying the prefix
        # through a live environment is not the same causal condition.
        if assistant_turn < trigger:
            return row, "restore_required", None
        if assistant_turn == trigger and prefix_decisions == expected:
            if self.mode == "teacher_rescue":
                return row, "teacher_rescue_replay", dict(row["_corrected_turns"][trigger])
            return row, "skill_inject", None
        return row, "plain", None

    def log(self, row: dict) -> None:
        with self.lock, self.role_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def handler_for(state: ProxyState):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.rstrip("/") == "/health":
                self._send(200, b'{"status":"ok"}')
                return
            self._forward(None)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                self._send(400, b'{"error":"invalid json"}')
                return
            matched = None
            mode = "plain"
            anchor_message = None
            fingerprint = None
            original_messages = body.get("messages") or []
            if self.path.endswith("/chat/completions"):
                if body.get("stream"):
                    self._send(400, b'{"error":"skill proxy requires stream=false"}')
                    return
                fingerprint = prompt_fingerprint(original_messages)
                matched, mode, anchor_message = state.route(original_messages)
                if mode == "restore_required":
                    self._send(
                        409,
                        json.dumps({
                            "error": "exact state restore was required before intervention",
                            "task_key": matched.get("task_key") if matched else None,
                            "request_id": None,
                        }).encode(),
                    )
                    return
                if mode == "skill_inject":
                    body["messages"] = inject_skill(
                        body["messages"], matched["skill"]
                    )
            observed_prefix = None
            expected_prefix = None
            trigger = None
            if matched is not None:
                observed_prefix = [
                    canonical_decision(message)
                    for message in original_messages
                    if message.get("role") == "assistant"
                ]
                expected_prefix = list(matched.get("causal_prefix_decisions") or [])
                trigger = int(matched["causal_divergence"]["assistant_turn"])
            request_id = uuid.uuid4().hex
            state.log(
                {
                    "request_id": request_id,
                    "task_key": matched.get("task_key") if matched else None,
                    "skill_id": matched.get("skill_id") if matched else None,
                    "skill_version": matched.get("version") if matched else None,
                    "prefix_fingerprint": fingerprint,
                    "assistant_turn": sum(
                        message.get("role") == "assistant"
                        for message in body.get("messages", [])
                    ),
                    "injected": mode == "skill_inject",
                    "anchor_replayed": False,
                    "teacher_rescued": mode == "teacher_rescue_replay",
                    "route": mode,
                    "trigger_assistant_turn": trigger,
                    "expected_prefix_decisions": expected_prefix,
                    "observed_prefix_decisions": observed_prefix,
                }
            )
            if anchor_message is not None:
                message = {
                    "role": "assistant",
                    "content": anchor_message.get("content"),
                }
                if anchor_message.get("tool_calls") is not None:
                    message["tool_calls"] = anchor_message["tool_calls"]
                # Anchor replay is still part of the W4 behavior trajectory.
                # Preserve the exact sampled-token logprobs captured by the
                # original rollout so tool-use environment can materialize a valid on-policy
                # reverse-KL row.  Returning ``logprobs=None`` makes the tool-use environment
                # client reject the response before the Steer turn is reached.
                sampling = anchor_message.get("sampling") or {}
                token_ids = sampling.get("token_ids") or []
                token_logprobs = sampling.get("logprobs") or []
                if not token_ids or len(token_ids) != len(token_logprobs):
                    self._send(
                        500,
                        json.dumps({
                            "error": "anchor replay lacks sampled-token logprobs",
                            "request_id": request_id,
                        }).encode(),
                    )
                    return
                replay_logprobs = {
                    "content": [
                        {
                            "token": f"token_id:{token_id}",
                            "logprob": float(logprob),
                            "bytes": None,
                            "top_logprobs": [],
                        }
                        for token_id, logprob in zip(token_ids, token_logprobs)
                    ],
                    "refusal": None,
                }
                payload = {
                    "id": "chatcmpl-anchor-" + request_id,
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": body.get("model", "Qwen3-8B"),
                    "choices": [{
                        "index": 0, "message": message,
                        "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
                        "logprobs": replay_logprobs,
                    }],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": len(token_ids),
                        "total_tokens": len(token_ids),
                    },
                }
                self._send(200, json.dumps(payload, ensure_ascii=False).encode())
                return
            if self.path.endswith("/chat/completions"):
                try:
                    apply_budget(state.upstream, body)
                except ContextWindowExceeded as error:
                    self._send(400, json.dumps({"error": error.as_error()}).encode())
                    return
                except (OSError, ValueError, KeyError) as error:
                    self._send(502, json.dumps({"error": str(error)}).encode())
                    return
            self._forward(json.dumps(body).encode())

        def _forward(self, body: bytes | None):
            url = state.upstream + self.path
            headers = {"Content-Type": "application/json"}
            if self.headers.get("Authorization"):
                headers["Authorization"] = self.headers["Authorization"]
            request = urllib.request.Request(url, data=body, headers=headers, method=self.command)
            try:
                with urllib.request.urlopen(request, timeout=3600) as response:
                    payload = response.read()
                    self._send(
                        response.status,
                        payload,
                        response.headers.get("Content-Type", "application/json"),
                    )
            except urllib.error.HTTPError as error:
                self._send(error.code, error.read())
            except Exception as error:
                self._send(502, json.dumps({"error": str(error)}).encode())

        def log_message(self, format, *args):
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--role-log", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--statuses", nargs="+", default=["proposed", "verified", "regressed"])
    parser.add_argument("--mode", choices=["steer", "teacher_rescue"], default="steer")
    parser.add_argument("--step", type=int)
    args = parser.parse_args()
    state = ProxyState(
        args.upstream, args.store, args.role_log, set(args.statuses), args.mode, args.step
    )
    # A repair may legitimately have no usable skill yet: the analyzer can
    # produce evidence for a task whose first validation has not succeeded.
    # Keep the proxy alive as a pass-through endpoint so validation can record
    # that outcome and continue to the next trajectory.
    print(f"SKILL_PROXY_SIGNAL skills={len(state.skills)} port={args.port} mode=pass_through" if not state.skills
          else f"SKILL_PROXY_SIGNAL skills={len(state.skills)} port={args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), handler_for(state)).serve_forever()


if __name__ == "__main__":
    main()
