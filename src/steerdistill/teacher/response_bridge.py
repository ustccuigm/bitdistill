"""Preserve reasoning when an environment consumes assistant content only."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request
from steerdistill.generation_budget import ContextWindowExceeded, apply_budget


_TOKENIZER_LOCK = threading.Lock()
_TOKENIZER_CACHE = {}


def load_tokenizer(path):
    """Load each tokenizer once before bridge request threads can use it."""
    key = str(path)
    with _TOKENIZER_LOCK:
        tokenizer = _TOKENIZER_CACHE.get(key)
        if tokenizer is None:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(key)
            _TOKENIZER_CACHE[key] = tokenizer
        return tokenizer


def preserve_reasoning(response, tokenizer=None):
    for choice in response.get("choices", []):
        message = choice.get("message", {})
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        content = message.get("content") or ""
        if tokenizer is not None:
            entries = (choice.get("logprobs") or {}).get("content") or []
            if not entries or any(not entry["token"].startswith("token_id:") for entry in entries):
                raise ValueError("Text tool response lacks exact sampled token IDs")
            content = tokenizer.decode([int(entry["token"].split(":", 1)[1]) for entry in entries],
                                       skip_special_tokens=False)
            eos = tokenizer.eos_token
            if eos and content.endswith(eos):
                content = content[:-len(eos)]
            if reasoning and "<think>" not in content:
                content = "<think>" + content
            message["content"] = content
            message["tool_calls"] = None
            continue
        if reasoning and "<think>" not in content:
            message["content"] = f"<think>{reasoning}</think>{content}"
    return response


@contextmanager
def bridge_endpoint(upstream, seed_namespace="", tokenizer_path=None):
    upstream = upstream.rstrip("/").removesuffix("/v1")
    # The environment fans out requests immediately. Loading Transformers lazily
    # in those handlers races its module-level import on this Python runtime.
    text_tokenizer = load_tokenizer(tokenizer_path) if tokenizer_path else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def forward(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0"))) or None
            try:
                if body and self.path.rstrip("/").endswith("/chat/completions"):
                    chat = json.loads(body)
                    # Text-based tool environments parse their own action
                    # markup. A native parser must not consume that markup.
                    if not chat.get("tools"):
                        chat["tool_choice"] = "none"
                        if text_tokenizer is not None:
                            chat["logprobs"] = True
                            chat["return_tokens_as_token_ids"] = True
                    if seed_namespace:
                        seed = json.dumps([seed_namespace, chat.get("seed")]).encode()
                        chat["seed"] = int.from_bytes(hashlib.sha256(seed).digest()[:4], "big")
                    body = json.dumps(apply_budget(upstream, chat)).encode()
                request = urllib.request.Request(upstream + self.path, data=body,
                    headers={"Content-Type": "application/json", "Authorization": "Bearer EMPTY"},
                    method=self.command)
                with urllib.request.urlopen(request, timeout=1800) as result:
                    payload, status = result.read(), result.status
                    content_type = result.headers.get("Content-Type", "application/json")
                if self.path.rstrip("/").endswith("/chat/completions"):
                    payload = json.dumps(preserve_reasoning(json.loads(payload), text_tokenizer)).encode()
            except ContextWindowExceeded as error:
                payload = json.dumps({"error": error.as_error()}).encode()
                status, content_type = 400, "application/json"
            except urllib.error.HTTPError as error:
                payload, status, content_type = error.read(), error.code, "application/json"
            except (OSError, ValueError) as error:
                payload = json.dumps({"error": {"message": str(error)}}).encode()
                status, content_type = 502, "application/json"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_POST = do_GET = forward

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
