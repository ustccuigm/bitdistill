"""Explicit thinking requests and lossless generation evidence for training."""
import json
import hashlib
from pathlib import Path
import re


class MissingReasoning(ValueError):
    """An action or Teacher analysis cannot be certified without its reasoning."""


def enable_thinking(payload):
    options = dict(payload.get("chat_template_kwargs") or {})
    if options.get("enable_thinking") is False:
        raise ValueError("Training requires enable_thinking=True")
    options["enable_thinking"] = True
    payload["chat_template_kwargs"] = options
    payload["include_reasoning"] = True
    return payload


def reasoning_text(message):
    for key in ("reasoning_content", "reasoning"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    content = message.get("content") or ""
    if not isinstance(content, str):
        return ""
    if "<think>" not in content and "</think>" in content:
        # Some templates prefill the opening delimiter in the prompt.
        return content.split("</think>", 1)[0].strip()
    return "\n".join(re.findall(r"<think>(.*?)</think>", content, re.S)).strip()


def require_reasoning(message):
    text = reasoning_text(message)
    if not text:
        raise MissingReasoning("Generated response has no nonempty reasoning; retain raw evidence and reject it")
    return text


def content_with_reasoning(message):
    """Normalize split reasoning once for saved training text, without inventing it."""
    content = message.get("content") or ""
    content = content if isinstance(content, str) else str(content)
    thought = reasoning_text(message)
    if thought and "<think>" not in content:
        if "</think>" in content and content.split("</think>", 1)[0].strip() == thought:
            return "<think>" + content
        return f"<think>{thought}</think>{content}"
    return content


def save_exchange(directory, request, response=None):
    """Save payloads without HTTP authorization headers, including rejected outputs."""
    if directory is None:
        return
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
    if response is not None:
        (directory / "response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n")
        choice = response.get("choices", [{}])[0]
        message = choice.get("message") or {}
        (directory / "reasoning.txt").write_text(reasoning_text(message))


def verifier_summary(value):
    """Only verdicts enter Teacher prompts; free-form grader output stays on disk."""
    allowed = {"reward_type": {"complete", "incomplete", "others"},
               "execution_status": {"success", "failed", "error"},
               "result": {"complete", "incomplete", "others"}}
    summary = {}
    for key, choices in allowed.items():
        item = value.get(key)
        if isinstance(item, str) and item in choices:
            summary[key] = item
    for key in ("success", "passed", "valid", "missing"):
        if type(value.get(key)) is bool:
            summary[key] = value[key]
    if isinstance(value.get("verify_result"), dict):
        summary["verify_result"] = verifier_summary(value["verify_result"])
    return summary


def write_run_receipt(run_dir):
    run_dir = Path(run_dir)
    files = [run_dir / "trajectory.json", run_dir / "verify.code.json"]
    files.extend(sorted((run_dir / "generations").glob("*/response.json")))
    if len(files) < 3:
        raise ValueError("Training run has no saved generation responses")
    receipt = {"version": 1, "files": {
        str(path.relative_to(run_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}
    (run_dir / "generation_evidence.json").write_text(json.dumps(receipt, indent=2) + "\n")


def validate_run_receipt(run_dir):
    run_dir = Path(run_dir)
    path = run_dir / "generation_evidence.json"
    if not path.is_file():
        raise ValueError("Existing training run lacks generation evidence; use a fresh output directory")
    receipt = json.loads(path.read_text())
    files = receipt.get("files", {})
    if receipt.get("version") != 1 or not {"trajectory.json", "verify.code.json"} <= files.keys():
        raise ValueError("Invalid training generation receipt")
    if not any(name.startswith("generations/") and name.endswith("/response.json") for name in files):
        raise ValueError("Training generation receipt has no responses")
    for name, expected in files.items():
        path = (run_dir / name).resolve()
        if not path.is_relative_to(run_dir.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Training generation evidence changed")


def generation_files(directory):
    directory = Path(directory)
    paths = sorted(path for path in directory.rglob("*.json") if path.name in {"request.json", "response.json"})
    if not paths:
        raise ValueError("Rollout has no saved generation exchanges")
    if not any(path.name == "response.json" for path in paths):
        raise ValueError("Rollout has no saved generation responses")
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def validate_generation_files(directory, expected):
    if not isinstance(expected, dict) or not expected or generation_files(directory) != expected:
        raise ValueError("Rollout generation evidence is missing or changed")
