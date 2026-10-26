#!/usr/bin/env python3
"""Shared trajectory, verification, and prompt utilities."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{number}: expected object")
                yield value


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def task_key(scenario: str, task_id: int | str) -> str:
    return f"{scenario}:{task_id}"


def is_success(run_dir: Path) -> bool:
    path = run_dir / "verify.code.json"
    if not path.is_file():
        return False
    value = read_json(path)
    return (
        value.get("reward_type") == "complete"
        and (value.get("verify_result") or {}).get("execution_status") == "success"
    )


def verification_evidence(run_dir: Path) -> dict:
    path = run_dir / "verify.code.json"
    return read_json(path) if path.is_file() else {"missing": True}


def failure_signature(run: dict) -> str:
    """Verifier-grounded identity used to detect a repeated failed recovery."""
    trajectory = run["trajectory"]
    decisions = [canonical_decision(turn) for turn in assistant_turns(trajectory)]
    verifier = verification_evidence(Path(run["run_dir"]))
    result = verifier.get("verify_result") or {}
    payload = {
        "task": task_key(trajectory.get("scenario", "unknown"), trajectory.get("task_id", -1)),
        "tail_decisions": decisions[-2:],
        "reward_type": verifier.get("reward_type"),
        "execution_status": result.get("execution_status"),
        "error": result.get("error") or result.get("message") or verifier.get("error"),
    }
    return stable_id("failure", json.dumps(payload, ensure_ascii=False, sort_keys=True))


def collect_runs(root: Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for path in sorted(root.glob("**/trajectory.json")):
        trajectory = read_json(path)
        if "messages" not in trajectory or "scenario" not in trajectory or "task_id" not in trajectory:
            continue  # Snapshot prefix files are not independently verified episodes.
        key = task_key(trajectory.get("scenario", "unknown"), trajectory.get("task_id", -1))
        result.setdefault(key, []).append(
            {
                "run_dir": str(path.parent),
                "trajectory_path": str(path),
                "trajectory": trajectory,
                "success": is_success(path.parent),
            }
        )
    return result


def api_messages(messages: list[dict]) -> list[dict]:
    result = []
    for message in messages:
        role = message.get("role")
        if role in {"system", "user", "assistant"}:
            content = message.get("content")
            row = {"role": role, "content": "" if content is None else str(content)}
            if role == "assistant" and message.get("tool_calls") is not None:
                row["tool_calls"] = message.get("tool_calls")
            result.append(row)
        elif role == "tool":
            result.append(
                {
                    "role": "tool",
                    "tool_call_id": message.get("tool_call_id", "call_unknown"),
                    "content": "" if message.get("content") is None else str(message.get("content", "")),
                }
            )
    return result


def inject_skill(messages: list[dict], skill: str) -> list[dict]:
    marker = (
        "Verified causal Steer from earlier environment interaction. Use it as "
        "procedural steering; independently decide the current action:\n" + skill.strip()
    )
    copied = [dict(message) for message in messages]
    if copied and copied[0].get("role") == "system":
        copied[0]["content"] = str(copied[0].get("content", "")) + "\n\n" + marker
    else:
        copied.insert(0, {"role": "system", "content": marker})
    return copied


def _structured_content(content: str):
    """Parse one or more structured tool-call wrappers from assistant text."""
    for tag, name in (("action", "environment_action"), ("search", "search")):
        match = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", content, re.S)
        if match:
            command = match.group(1).strip()
            if tag == "action" and command:
                verb = re.split(r"[\s\[]", command, maxsplit=1)[0].lower()
                name = f"environment.{verb}"
            return {"name": name, "arguments": {"text": command}}
    candidates = [content]
    tagged = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", content, re.S)
    if tagged:
        parsed = []
        for candidate in tagged:
            try:
                parsed.append(json.loads(candidate.strip()))
            except (json.JSONDecodeError, TypeError):
                parsed = []
                break
        if parsed:
            return parsed if len(parsed) > 1 else parsed[0]
    candidates.extend(tagged)
    candidates.extend(re.findall(r"```(?:json)?\s*(.*?)\s*```", content, re.S))
    for candidate in candidates:
        candidate = candidate.strip()
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _canonical_value(value):
    """Normalize JSON values while preserving task arguments such as ``id``."""
    if isinstance(value, dict):
        return {
            str(key): _canonical_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_arguments(value):
    """Parse JSON encoded arguments, without rewriting ordinary string values."""
    if isinstance(value, str):
        stripped = value.strip()
        try:
            return _canonical_value(json.loads(stripped))
        except (json.JSONDecodeError, TypeError):
            return value
    return _canonical_value(value)


def _canonical_tool_call(call) -> dict:
    """Convert native and MCP wrapper calls to one action representation."""
    if not isinstance(call, dict):
        return {"name": str(call), "arguments": None}
    function = call.get("function")
    if isinstance(function, dict):
        name = function.get("name")
        arguments = function.get("arguments")
    else:
        name = call.get("name") or call.get("tool_name")
        arguments = call.get("arguments")
        if name == "call_tool" and isinstance(arguments, dict):
            name = arguments.get("tool_name")
            arguments = arguments.get("arguments")
    result = {"name": "" if name is None else str(name)}
    if arguments is not None:
        normalized_arguments = _canonical_arguments(arguments)
        # OpenAI-compatible clients may serialize a no-argument tool call as
        # either null/omitted or {}. They are the same action for matching a
        # restored trajectory to its recorded causal prefix.
        if normalized_arguments != {}:
            result["arguments"] = normalized_arguments
    return result


def _canonical_tool_calls(tool_calls) -> list:
    if isinstance(tool_calls, dict):
        tool_calls = [tool_calls]
    return [_canonical_tool_call(call) for call in tool_calls]


def _canonical_tool_sequence(tool_calls):
    calls = _canonical_tool_calls(tool_calls)
    return calls[0] if len(calls) == 1 else calls


def canonical_decision(message: dict) -> str:
    """Canonicalize actions while ignoring transport metadata only."""
    tool_calls = message.get("tool_calls")
    if tool_calls:
        return json.dumps(_canonical_tool_sequence(tool_calls), ensure_ascii=False,
                          sort_keys=True, separators=(",", ":"))
    raw_content = message.get("content")
    content = "" if raw_content is None else str(raw_content)
    structured = _structured_content(content)
    if structured is not None:
        if isinstance(structured, list):
            structured = _canonical_tool_sequence(structured)
        elif isinstance(structured, dict) and (
            "function" in structured or structured.get("name") or structured.get("tool_name")
        ):
            structured = _canonical_tool_call(structured)
        else:
            structured = _canonical_value(structured)
        return json.dumps(structured, ensure_ascii=False,
                          sort_keys=True, separators=(",", ":"))
    normalized = re.sub(r"\s+", " ", content).strip()
    answer = re.search(r"<answer>\s*(.*?)\s*</answer>", content, re.S)
    if answer:
        normalized = re.sub(r"\s+", " ", answer.group(1)).strip()
    return normalized


def decision_descriptor(decision: str | None) -> dict:
    """Return the action-bearing parts of one canonical assistant decision.

    The tool-use environment traces contain both OpenAI ``tool_calls`` and the MCP
    ``call_tool`` wrapper.  A deterministic descriptor gives the causal
    analyzer an action delta that cannot be overwritten by free-form text.
    """
    if decision is None:
        return {"kind": "missing", "tool": None, "arguments": None}
    try:
        value = json.loads(decision)
    except (json.JSONDecodeError, TypeError):
        return {"kind": "final_response", "tool": None, "arguments": None}
    if isinstance(value, list) and value:
        value = value[0]
    if not isinstance(value, dict):
        return {"kind": "final_response", "tool": None, "arguments": None}
    function = value.get("function") if isinstance(value.get("function"), dict) else None
    if function is not None:
        tool = function.get("name")
        arguments = function.get("arguments")
    else:
        outer_arguments = value.get("arguments")
        if value.get("name") == "call_tool" and isinstance(outer_arguments, dict):
            tool = outer_arguments.get("tool_name")
            arguments = outer_arguments.get("arguments")
        else:
            tool = value.get("tool_name") or value.get("command") or value.get("name")
            arguments = outer_arguments
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            pass
    if not tool:
        return {"kind": "final_response", "tool": None, "arguments": None}
    return {"kind": "tool_action", "tool": str(tool), "arguments": arguments}


def causal_action_delta(
    failed_decision: str | None,
    expected_decision: str | None,
    mismatch_kind: str | None = None,
) -> dict:
    """Build the immutable mechanism identity for one causal repair.

    It distinguishes an argument correction, a wrong tool, and premature
    termination.  The resulting signature is evidence-derived rather than
    chosen by the language-model analyzer.
    """
    failed = decision_descriptor(failed_decision)
    expected = decision_descriptor(expected_decision)
    changed_arguments = []
    if mismatch_kind == "transition_mismatch" and failed_decision == expected_decision:
        failure_type = "environment_transition_mismatch"
        identity = [failure_type, expected.get("tool"), expected.get("arguments")]
    elif failed["kind"] == expected["kind"] == "tool_action" and failed["tool"] == expected["tool"]:
        failed_args = failed["arguments"] if isinstance(failed["arguments"], dict) else {}
        expected_args = expected["arguments"] if isinstance(expected["arguments"], dict) else {}
        changed_arguments = sorted(
            key for key in set(failed_args) | set(expected_args)
            if failed_args.get(key) != expected_args.get(key)
        )
        failure_type = "argument_grounding"
        identity = [failure_type, expected["tool"], *changed_arguments]
    elif failed["kind"] != "tool_action" and expected["kind"] == "tool_action":
        failure_type = "premature_termination"
        identity = [failure_type, expected["tool"]]
    elif failed["kind"] == "tool_action" and expected["kind"] == "tool_action":
        failure_type = "wrong_tool"
        identity = [failure_type, failed["tool"], expected["tool"]]
    elif expected["kind"] != "tool_action":
        failure_type = "failure_to_terminate"
        identity = [failure_type, failed.get("tool")]
    else:
        failure_type = "decision_mismatch"
        identity = [failure_type, failed.get("kind"), expected.get("kind")]
    signature = stable_id("causal", json.dumps(identity, ensure_ascii=False, sort_keys=True))
    return {
        "signature": signature,
        "failure_type": failure_type,
        "changed_arguments": changed_arguments,
        "failed": failed,
        "expected": expected,
    }


def _action_bearing(message: dict) -> bool:
    """Return whether an assistant turn changes or queries environment state."""
    if message.get("tool_calls"):
        return True
    value = _structured_content(str(message.get("content", "")))
    return isinstance(value, dict) and bool(
        value.get("name") or value.get("tool_name") or value.get("command")
    )


def observations_after_assistant_turn(trajectory: dict, target: int) -> list[str]:
    """Canonical observations produced by one assistant decision.

    tool-use environment records tool results as messages between adjacent assistant turns.  IDs
    assigned by the OpenAI transport are intentionally ignored; the verifier
    relevant payload is the role and normalized content.
    """
    messages = trajectory.get("messages", [])
    seen = -1
    collecting = False
    result = []
    for message in messages:
        if message.get("role") == "assistant":
            seen += 1
            if collecting:
                break
            collecting = seen == target
            continue
        if collecting and message.get("role") in {"tool", "user"}:
            raw_content = str(message.get("content", "")).strip()
            try:
                parsed_content = json.loads(raw_content)
                content = json.dumps(
                    parsed_content,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            except json.JSONDecodeError:
                content = re.sub(r"\s+", " ", raw_content).strip()
            result.append(f"{message.get('role')}:{content}")
    return result


def transition_signature(trajectory: dict, target: int) -> tuple[str, tuple[str, ...]]:
    turns = assistant_turns(trajectory)
    decision = canonical_decision(turns[target]) if target < len(turns) else "<missing>"
    return decision, tuple(observations_after_assistant_turn(trajectory, target))


def local_transition_match(
    candidate: dict,
    reference: dict,
    target: int,
    expected_decision: str | None = None,
    reference_target: int | None = None,
) -> tuple[bool, str]:
    """Verify one repaired causal transition without requiring episode success.

    Current tool trajectories use immutable database snapshots and read
    evidence. Action identity is not required when effects match. Legacy traces
    without snapshots retain their original strict action/observation check.
    """
    candidate_turns = assistant_turns(candidate)
    reference_target = target if reference_target is None else reference_target
    reference_turns = assistant_turns(reference)
    if target >= len(candidate_turns) or reference_target >= len(reference_turns):
        return False, "turn_missing"
    if candidate.get("snapshot_root") or reference.get("snapshot_root"):
        if (expected_decision is not None
                and canonical_decision(reference_turns[reference_target]) != expected_decision):
            return False, "reference_expected_mismatch"
        if not _action_bearing(candidate_turns[target]):
            return False, "candidate_not_action"
        if not candidate.get("snapshot_root") or not reference.get("snapshot_root"):
            raise ValueError("Both trajectories require state snapshots")
        from steerdistill.transition_verifier import compare_transition
        return compare_transition(candidate["snapshot_root"], reference["snapshot_root"],
                                  target, reference_target, candidate["messages"], reference["messages"])
    candidate_turn = candidate_turns[target]
    reference_turn = reference_turns[reference_target]
    if not _action_bearing(reference_turn):
        return False, "reference_not_action"
    reference_decision = canonical_decision(reference_turn)
    candidate_decision = canonical_decision(candidate_turn)
    if expected_decision is not None and reference_decision != expected_decision:
        return False, "reference_expected_mismatch"
    target_decision = expected_decision or reference_decision
    if candidate_decision != target_decision:
        return False, "decision_mismatch"
    observations = observations_after_assistant_turn(candidate, target)
    if not observations:
        return False, "observation_missing"
    reference_observations = observations_after_assistant_turn(reference, reference_target)
    if not reference_observations:
        return False, "reference_observation_missing"
    if observations != reference_observations:
        return False, "observation_mismatch"
    lowered = " ".join(observations).lower()
    error_markers = (
        "error:", "internal server error", "status code: 4", "status code: 5",
        "traceback",
    )
    if any(marker in lowered for marker in error_markers):
        return False, "environment_error"
    return True, "verified_action_transition"


def causal_transition_match(
    candidate: dict,
    reference: dict,
    target: int,
    expected_decision: str | None,
    *,
    candidate_success: bool,
    reference_target: int | None = None,
) -> tuple[bool, str]:
    """Validate either an environment action or a terminal decision.

    Tool actions use the environment transition checker. A terminal
    answer has no following environment observation, so its causal evidence is
    instead: both policies terminate at the target turn and the real task
    verifier marks the candidate complete.  Exact prose equality is neither
    necessary nor desirable for terminal answers.
    """
    expected = decision_descriptor(expected_decision)
    if expected["kind"] != "final_response":
        return local_transition_match(
            candidate, reference, target, expected_decision=expected_decision,
            reference_target=reference_target,
        )
    candidate_turns = assistant_turns(candidate)
    reference_turns = assistant_turns(reference)
    reference_target = target if reference_target is None else reference_target
    if target >= len(candidate_turns) or reference_target >= len(reference_turns):
        return False, "turn_missing"
    if decision_descriptor(canonical_decision(reference_turns[reference_target]))["kind"] != "final_response":
        return False, "reference_expected_mismatch"
    if decision_descriptor(canonical_decision(candidate_turns[target]))["kind"] != "final_response":
        return False, "decision_mismatch"
    if not candidate_success:
        return False, "terminal_verifier_failed"
    return True, "verified_terminal_success"


def assistant_turns(trajectory: dict) -> list[dict]:
    return [m for m in trajectory.get("messages", []) if m.get("role") == "assistant"]


def first_divergence(failure: dict, success: dict) -> dict:
    """Select the first action whose environment transition differs."""
    if not failure.get("snapshot_root") or not success.get("snapshot_root"):
        raise ValueError("State-only localization requires snapshots for both trajectories")
    failed = assistant_turns(failure)
    corrected = assistant_turns(success)
    i = j = 0
    mismatch_kind = "none"
    from steerdistill.transition_verifier import compare_alignment_state, unchanged_state

    def matches(left, right):
        return compare_alignment_state(
            failure["snapshot_root"], success["snapshot_root"], left, right,
            candidate_terminal=left == len(failed) - 1 and not _action_bearing(failed[left]),
            reference_terminal=right == len(corrected) - 1 and not _action_bearing(corrected[right]),
        )

    while i < len(failed) and j < len(corrected):
        if matches(i, j):
            i += 1
            j += 1
            continue
        # Skip explanatory turns only when snapshots prove they preserve state.
        if not _action_bearing(failed[i]) and i + 1 < len(failed) and unchanged_state(failure["snapshot_root"], i):
            i += 1
            continue
        if not _action_bearing(corrected[j]) and j + 1 < len(corrected) and unchanged_state(success["snapshot_root"], j):
            j += 1
            continue
        aligned = False
        for side in ("candidate", "reference"):
            trajectory, turns, start = (failure, failed, i) if side == "candidate" else (success, corrected, j)
            for offset in range(1, len(turns) - start):
                if not unchanged_state(trajectory["snapshot_root"], start + offset - 1):
                    break
                left, right = (i + offset, j) if side == "candidate" else (i, j + offset)
                if matches(left, right):
                    i, j = left + 1, right + 1
                    aligned = True
                    break
            if aligned:
                break
        if aligned:
            continue
        mismatch_kind = "transition_mismatch"
        break
    index = i
    if mismatch_kind == "none" and (i != len(failed) or j != len(corrected)):
        mismatch_kind = "length_mismatch"
    return {
        "assistant_turn": index,
        "failed_assistant_turn": index,
        "corrected_assistant_turn": j,
        "failed_decision": canonical_decision(failed[index]) if index < len(failed) else None,
        "corrected_decision": canonical_decision(corrected[j]) if j < len(corrected) else None,
        "common_assistant_turns": min(i, j),
        "failed_turn_count": len(failed),
        "corrected_turn_count": len(corrected),
        "mismatch_kind": mismatch_kind,
        "failed_transition": {
            "decision": transition_signature(failure, index)[0] if index < len(failed) else None,
            "observations": list(transition_signature(failure, index)[1]) if index < len(failed) else [],
        },
        "corrected_transition": {
            "decision": transition_signature(success, j)[0] if j < len(corrected) else None,
            "observations": list(transition_signature(success, j)[1]) if j < len(corrected) else [],
        },
    }


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def prompt_fingerprint(messages: list[dict]) -> str:
    """Identify a semantic action prefix, independent of API transport fields."""
    normalized = []
    for message in messages:
        row = {
            "role": message.get("role"),
            "content": str(message.get("content", "")),
        }
        if message.get("tool_calls") is not None:
            row["tool_call_decision"] = canonical_decision(message)
        normalized.append(row)
    return stable_id("prefix", json.dumps(normalized, ensure_ascii=False, sort_keys=True))


def prefix_before_assistant_turn(trajectory: dict, target: int) -> list[dict]:
    prefix, seen = [], 0
    for message in trajectory.get("messages", []):
        if message.get("role") == "assistant":
            if seen == target:
                break
            seen += 1
        prefix.append(message)
    return api_messages(prefix)


def sampling_by_assistant_turn(trajectory: dict) -> dict[int, dict]:
    result = {}
    for entry in trajectory.get("trajectory", []):
        if entry.get("role") == "assistant":
            iteration = int(entry.get("iteration", len(result) + 1))
            result[iteration - 1] = entry.get("sampling") or {}
    return result
