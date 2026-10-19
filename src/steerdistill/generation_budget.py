"""Budget generated tokens against the server's exact rendered chat prompt."""
from functools import lru_cache
import json
import os
import urllib.request


class ContextWindowExceeded(ValueError):
    """A normal rollout length boundary, distinct from transport failures."""

    def __init__(self, window, prompt_tokens):
        self.window = window
        self.prompt_tokens = prompt_tokens
        super().__init__(f"Prompt has {prompt_tokens} tokens; context window is {window}")

    def as_error(self):
        return {"message": str(self), "type": "invalid_request_error",
                "code": "context_length_exceeded", "context_window": self.window,
                "prompt_tokens": self.prompt_tokens}


def read_json(url, payload=None, api_key="EMPTY"):
    request = urllib.request.Request(url,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


@lru_cache(maxsize=32)
def context_window(root, model, api_key):
    models = read_json(root + "/v1/models", api_key=api_key)["data"]
    for row in models:
        if row["id"] == model:
            return int(row["max_model_len"])
    raise ValueError(f"Requested model is not served: {model}")


def available_tokens(window, prompt_tokens, requested):
    remaining = window - prompt_tokens
    if remaining <= 0:
        raise ContextWindowExceeded(window, prompt_tokens)
    return min(remaining, requested)


def apply_budget(api_url, payload, api_key="EMPTY"):
    root = api_url.rstrip("/").removesuffix("/v1")
    window = min(context_window(root, payload["model"], api_key),
                 int(os.getenv("MODEL_MAX_LENGTH", "32768")))
    tokenize = {key: payload[key] for key in (
        "model", "messages", "tools", "chat_template", "chat_template_kwargs",
        "add_generation_prompt", "continue_final_message", "add_special_tokens",
    ) if key in payload}
    count = int(read_json(root + "/tokenize", tokenize, api_key)["count"])
    key = "max_completion_tokens" if "max_completion_tokens" in payload else "max_tokens"
    requested = int(payload.get(key) or os.getenv("MAX_TOKENS", "32768"))
    payload[key] = available_tokens(window, count, requested)
    if "min_tokens" in payload:
        payload["min_tokens"] = min(int(payload["min_tokens"]), payload[key])
    return payload
