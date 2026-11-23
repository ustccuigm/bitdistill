"""Generate native text actions using the tokenizer of the served checkpoint."""
import json
import re
import urllib.request

from steerdistill.generation_budget import available_tokens, read_json


def sample_action(url, model, prompt, seed, temperature):
    root = url.rstrip("/").removesuffix("/v1")
    rendered = read_json(root + "/tokenize", {
        "model": model, "messages": prompt, "add_generation_prompt": True,
        "chat_template_kwargs": {"enable_thinking": True},
    })
    tokens = rendered["tokens"]
    limit = available_tokens(min(rendered["max_model_len"], 16384), len(tokens), 8192)
    payload = {"model": model, "prompt": tokens, "max_tokens": limit, "seed": seed,
               "temperature": temperature, "top_p": 1.0, "top_k": -1, "skip_special_tokens": False}
    request = urllib.request.Request(root + "/v1/completions", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=1800) as response:
        data = json.load(response)
    choice = data["choices"][0]
    return choice["text"], {"finish_reason": choice["finish_reason"], "usage": data["usage"], "seed": seed}


def environment_action(benchmark, response):
    reasoning, closed, body = response.rpartition("</think>")
    if not closed or (benchmark == "webshop" and "<think>" not in reasoning):
        return "Invalid action"
    if len(re.findall(r"<action>\s*.+?\s*</action>", body, re.I | re.S)) != 1:
        return "Invalid action"
    bridge = re.sub(r"</?action>", "", reasoning, flags=re.I) + closed + body
    if benchmark == "webshop":
        from agent_system.environments.env_package.webshop.projection import webshop_projection
        actions, valid = webshop_projection([bridge])
        if not valid[0] or not re.fullmatch(r"(search|click)\[.+\]", actions[0], re.S):
            return "Invalid action"
    return bridge
