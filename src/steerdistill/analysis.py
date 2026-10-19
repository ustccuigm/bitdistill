#!/usr/bin/env python3
"""Create or revise skill from verifier-grounded counterfactual trajectories."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from steerdistill.common import (
    assistant_turns,
    canonical_decision,
    causal_action_delta,
    first_divergence,
    iter_jsonl,
    read_json,
    stable_id,
    verification_evidence,
)
from steerdistill.store import SkillStore
from steerdistill.generation_budget import apply_budget


ANALYSIS_SCHEMA = "causal-steer-v2"
STEER_FIELDS = {
    "precondition", "decision_rule", "expected_transition", "recovery_check"
}
STEER_RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "decision": {"type": "string", "enum": ["create", "revise"]},
        "summary": {"type": "string"},
        "failure_mechanism": {"type": "string"},
        "failure_type": {"type": "string"},
        "relation_to_prior": {"type": "string", "enum": ["new", "recurrence", "revision"]},
        "causal_assistant_turn": {"type": "integer", "minimum": 0},
        "steer": {"type": "object", "additionalProperties": False,
                  "properties": {key: {"type": "string"} for key in sorted(STEER_FIELDS)},
                  "required": sorted(STEER_FIELDS)},
    },
    "required": ["decision", "summary", "failure_mechanism", "failure_type",
                 "relation_to_prior", "causal_assistant_turn", "steer"],
}

SYSTEM_PROMPT = """You are the causal Steer analyzer in a self-evolving agent system.
You receive one failed W4 environment trajectory and one independently verified successful
counterfactual trajectory for the same task. The declared first divergence is the exact
intervention candidate and its turn index is immutable: causal_assistant_turn MUST equal
declared_first_divergence.assistant_turn. When same_recovery_lineage is true, analyze
the divergence selected by realignment, even if it revisits an earlier repaired turn.
Explain the failed transition using the current trajectory and fixed reference. When it is
false, the evidence comes from an independent rollout: its turn indices MUST NOT be ordered
against anchors from an older rollout. Legitimate alternative actions are not failures. The
supplied evidence-derived action_delta and failure_type are immutable and MUST be returned
exactly.

Write one concise procedural Steer for this causal turn. It must contain a state precondition,
decision rule, expected environment transition, and concrete recovery check. Do not copy the
full answer or the exact expected tool call. Previously verified Steers are context only. If a
previous Steer exists in the same repair trajectory, rewrite one integrated Steer that preserves
valid earlier guidance and incorporates the current correction. Do not emit numbered Steers or
concatenate separate rules. If action_delta.signature is new, create a genuinely new mechanism and rule; never repeat an old
mechanism. If the same signature recurs, set relation_to_prior=recurrence and refine the
existing rule rather than pretending it is a new mechanism. If the current unverified Steer
failed validation, set relation_to_prior=revision and revise only that active Steer.

Return exactly one JSON object with keys:
decision (create|revise), summary, failure_mechanism,
failure_type, relation_to_prior (new|recurrence|revision),
causal_assistant_turn (zero based integer), and steer. ``steer`` MUST be a JSON object with
exactly these semantic fields: precondition, decision_rule, expected_transition,
recovery_check.
"""


def endpoint(url: str) -> str:
    value = url.rstrip("/")
    return value if value.endswith("/chat/completions") else value + "/chat/completions"


def extract_object(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Analyzer returned an empty response")
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Analyzer did not return a JSON object")
        value = json.loads(text[start:end + 1])
    # Accept the legacy key while old local analyzer templates drain, but all
    # newly persisted and user-visible objects are Steers.
    if isinstance(value, dict) and "steer" not in value and "skill" in value:
        value["steer"] = value["skill"]
    required = {
        "decision", "summary", "failure_mechanism", "failure_type",
        "relation_to_prior", "causal_assistant_turn", "steer",
    }
    if not isinstance(value, dict):
        raise ValueError("Analyzer response must be a JSON object")
    if required - value.keys():
        raise ValueError(f"Analyzer response missing {sorted(required - value.keys())}")
    if value["decision"] not in {"create", "revise"}:
        raise ValueError(f"Invalid analyzer decision: {value['decision']}")
    if value["relation_to_prior"] not in {"new", "recurrence", "revision"}:
        raise ValueError(
            f"Invalid relation_to_prior: {value['relation_to_prior']}"
        )
    return value


def normalize_steer(value) -> tuple[dict, str]:
    """Canonicalize structured Steer output without executing model text."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError) as error:
                raise ValueError("steer must be a structured object") from error
    if not isinstance(value, dict):
        raise ValueError("steer must be a JSON object")
    missing = STEER_FIELDS - set(value)
    if missing:
        raise ValueError(f"steer missing fields: {sorted(missing)}")
    normalized = {key: str(value[key]).strip() for key in sorted(STEER_FIELDS)}
    if any(not item for item in normalized.values()):
        raise ValueError("steer fields must be non-empty")
    return normalized, json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def _semantic_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _tool_label(value: str | None) -> str:
    text = str(value or "required tool")
    return text.removeprefix("mcp_tool_mcp_server_")


def recovery_lineage(run_dir: str | Path | None) -> str:
    """Return the repair transaction containing a run, if it has one.

    Turn indices are comparable only inside this transaction.  Two independent
    discovery rollouts for the same task may reach their first causal failure at
    unrelated turn indices, even when they occur in adjacent optimization steps.
    """
    parts = Path(str(run_dir or "")).parts
    for index, part in enumerate(parts[:-1]):
        if part == "repairs" and index + 1 < len(parts):
            return str(Path(*parts[: index + 2]))
    return ""


def accepted_memory(previous: dict | None) -> dict | None:
    """Failed proposals are feedback, never trajectory-local accepted memory."""
    steps = [step for step in (previous or {}).get("steer_steps", [])
             if step.get("status") in {"locally_verified", "verified"}]
    if not steps:
        return None
    prompt = steps[-1]["integrated_steer"]
    return dict(previous, steer_steps=steps, skill=prompt, steer=prompt,
                status=steps[-1]["status"])


def same_recovery_lineage(previous: dict | None, failed_run_dir: str | Path) -> bool:
    previous_lineage = str((previous or {}).get("repair_lineage") or "")
    if not previous_lineage:
        previous_lineage = recovery_lineage((previous or {}).get("failed_run_dir"))
    current_lineage = recovery_lineage(failed_run_dir)
    return bool(previous_lineage and current_lineage == previous_lineage)


def required_relation(
    previous: dict | None,
    action_delta: dict,
    *,
    same_lineage: bool = True,
) -> str:
    steps = list((previous or {}).get("steer_steps") or [])
    matching = [
        step for step in steps
        if step.get("causal_signature") == action_delta["signature"]
    ]
    if matching:
        if any(
            step.get("status") in {"locally_verified", "verified", "teacher_rescue"}
            for step in matching
        ):
            return "recurrence"
        return "revision"
    return "new"


def merge_steer_step(previous_steps: list[dict], current_step: dict, relation: str) -> list[dict]:
    """Append a new mechanism or replace the matching recurring mechanism.

    A recurrence is evidence for refining an existing rule, not for appending a
    duplicate copy of that rule.  This also keeps cumulative Steer prompts from
    growing with the same failure mechanism across optimization steps.
    """
    # Per-turn intervention evidence must survive recurrence at a later turn.
    # Keep the old suffix until validation accepts its replacement.
    if current_step.get("assistant_turn") is not None:
        steps = [dict(step) for step in previous_steps]
        current_step["index"] = max((step.get("index", 0) for step in steps), default=0) + 1
        return steps + [current_step]
    # Older checkpoints may contain duplicate copies created by the former
    # append-on-recurrence behavior.  Collapse them before adding new evidence:
    # keep the newest rule text but preserve the first rule's stable identity.
    steps = []
    signature_positions = {}
    for source in previous_steps:
        step = dict(source)
        signature = step.get("causal_signature")
        if signature and signature in signature_positions:
            position = signature_positions[signature]
            stable = steps[position]
            step["index"] = stable.get("index", position + 1)
            step["step_id"] = stable.get("step_id", step.get("step_id"))
            steps[position] = step
        else:
            if signature:
                signature_positions[signature] = len(steps)
            steps.append(step)
    replace_at = None
    if relation in {"recurrence", "revision"}:
        signature = current_step.get("causal_signature")
        for index in range(len(steps) - 1, -1, -1):
            if steps[index].get("causal_signature") == signature:
                replace_at = index
                break
        if replace_at is None and relation == "revision":
            for index in range(len(steps) - 1, -1, -1):
                if steps[index].get("status") not in {
                    "locally_verified", "verified", "teacher_rescue"
                }:
                    replace_at = index
                    break
    if replace_at is None:
        current_step["index"] = len(steps) + 1
        steps.append(current_step)
    else:
        current_step["index"] = steps[replace_at].get("index", replace_at + 1)
        current_step["step_id"] = steps[replace_at].get(
            "step_id", current_step["step_id"]
        )
        steps[replace_at] = current_step
    for index, step in enumerate(steps, 1):
        step["index"] = index
    return steps


def grounded_failure_mechanism(action_delta: dict) -> str:
    """Name the causal mechanism from observed actions, not model prose."""
    failure_type = action_delta["failure_type"]
    failed = action_delta["failed"]
    expected = action_delta["expected"]
    expected_tool = _tool_label(expected.get("tool"))
    if failure_type == "argument_grounding":
        fields = ", ".join(action_delta.get("changed_arguments") or ["arguments"])
        return (
            f"Incorrect task/environment grounding of {fields} for {expected_tool} "
            "changed the local environment transition."
        )
    if failure_type == "premature_termination":
        return (
            f"The policy terminated before calling {expected_tool}, so it did not "
            "obtain or execute the next state-advancing transition."
        )
    if failure_type == "wrong_tool":
        return (
            f"The policy called {_tool_label(failed.get('tool'))} where the verified "
            f"state required {expected_tool}."
        )
    if failure_type == "failure_to_terminate":
        return "The policy continued acting after the verified trajectory should terminate."
    return "The selected decision did not match the verified state transition."


def grounded_decision_rule(action_delta: dict) -> str:
    failure_type = action_delta["failure_type"]
    expected_tool = _tool_label(action_delta["expected"].get("tool"))
    if failure_type == "argument_grounding":
        fields = ", ".join(action_delta.get("changed_arguments") or ["arguments"])
        return (
            f"Before calling {expected_tool}, derive {fields} from the current task and "
            "latest verified observation; do not infer them from an unrelated turn."
        )
    if failure_type == "premature_termination":
        return (
            f"Do not terminate at this state; call {expected_tool} with arguments grounded "
            "in the latest verified observation, then inspect its result."
        )
    if failure_type == "wrong_tool":
        return (
            f"Use {expected_tool} for the next state transition instead of "
            f"{_tool_label(action_delta['failed'].get('tool'))}."
        )
    if failure_type == "failure_to_terminate":
        return "Terminate once the verifier-relevant task state has been completed."
    return "Choose the action that realizes the verified next-state transition."


def bind_teacher_analysis(
    analysis: dict,
    *,
    focus: int,
    action_delta: dict,
    previous: dict | None,
    same_lineage: bool = True,
) -> dict:
    """Bind Teacher language to immutable action-derived causal evidence."""
    result = dict(analysis)
    result["teacher_reported_causal_turn"] = analysis.get("causal_assistant_turn")
    result["teacher_reported_failure_type"] = analysis.get("failure_type")
    result["teacher_reported_relation"] = analysis.get("relation_to_prior")
    result["teacher_failure_explanation"] = str(analysis.get("failure_mechanism", ""))
    result["causal_assistant_turn"] = focus
    result["failure_type"] = action_delta["failure_type"]
    result["relation_to_prior"] = required_relation(
        previous, action_delta, same_lineage=same_lineage
    )
    steer_fields, _ = normalize_steer(analysis["steer"])
    result["steer_fields"] = steer_fields
    result["steer"] = json.dumps(steer_fields, ensure_ascii=False, sort_keys=True)
    result["decision"] = "create" if result["relation_to_prior"] == "new" else "revise"
    return result


def analysis_violations(
    analysis: dict,
    *,
    focus: int,
    action_delta: dict,
    previous: dict | None,
    same_lineage: bool = True,
) -> list[str]:
    """Reject ungrounded, duplicated, or turn-misaligned Analyzer output."""
    violations = []
    if int(analysis["causal_assistant_turn"]) != focus:
        violations.append(
            f"causal_assistant_turn must be {focus}, not "
            f"{analysis['causal_assistant_turn']}"
        )
    if str(analysis["failure_type"]) != action_delta["failure_type"]:
        violations.append(
            f"failure_type must be {action_delta['failure_type']}, not "
            f"{analysis['failure_type']}"
        )
    previous_steps = list((previous or {}).get("steer_steps") or [])
    expected_relation = required_relation(
        previous, action_delta, same_lineage=same_lineage
    )
    if analysis["relation_to_prior"] != expected_relation:
        violations.append(
            f"relation_to_prior must be {expected_relation}, not "
            f"{analysis['relation_to_prior']}"
        )
    try:
        _, steer_text = normalize_steer(analysis["steer"])
    except ValueError as error:
        violations.append(str(error))
        steer_text = ""
    if expected_relation == "new":
        mechanism_key = _semantic_key(analysis["failure_mechanism"])
        steer_key = _semantic_key(steer_text)
        for step in previous_steps:
            if mechanism_key and mechanism_key == _semantic_key(step.get("failure_mechanism", "")):
                violations.append("new causal signature repeated a previous failure_mechanism")
                break
            if steer_key and steer_key == _semantic_key(step.get("steer", "")):
                violations.append("new causal signature repeated a previous Steer")
                break
    return violations


class AnalysisRejected(RuntimeError):
    """Teacher proposals exhausted causal validation, not a service failure."""

    def __init__(self, violations, analysis):
        self.violations = list(violations)
        self.analysis = analysis
        super().__init__("Analyzer failed causal-grounding checks: " + "; ".join(violations))


def grounded_analysis(
    api_url: str,
    api_key: str,
    model: str,
    evidence: dict,
    previous: dict | None,
    same_lineage: bool = True,
) -> dict:
    """Require the Teacher explanation to remain bound to causal evidence."""
    feedback = []
    for _ in range(3):
        payload = dict(evidence)
        if feedback:
            payload["rejected_previous_analysis"] = {
                "violations": feedback,
                "instruction": "Regenerate from the current residual action delta only.",
            }
        payload["retry_feedback"] = _compact_retry_feedback(
            payload.get("retry_feedback", [])
        )
        analysis = call_analyzer(
            api_url, api_key, model, json.dumps(payload, ensure_ascii=False)
        )
        analysis = bind_teacher_analysis(
            analysis,
            focus=int(evidence["declared_first_divergence"]["assistant_turn"]),
            action_delta=evidence["action_delta"],
            previous=previous,
            same_lineage=same_lineage,
        )
        feedback = analysis_violations(
            analysis,
            focus=int(evidence["declared_first_divergence"]["assistant_turn"]),
            action_delta=evidence["action_delta"],
            previous=previous,
            same_lineage=same_lineage,
        )
        if not feedback:
            return analysis
    raise AnalysisRejected(feedback, analysis)


def call_analyzer(api_url: str, api_key: str, model: str, payload: str) -> dict:
    payload_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload},
            ],
            "temperature": 0.0,
            "max_tokens": int(os.getenv("MAX_TOKENS", "32768")),
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "causal_steer", "strict": True, "schema": STEER_RESPONSE_SCHEMA}},
        }
    last_error = None
    rejected = []
    invalid_content = False
    for attempt in range(5):
        body = json.dumps(apply_budget(api_url, payload_body, api_key)).encode()
        request = urllib.request.Request(
            endpoint(api_url), data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                result = json.loads(response.read())
            content = result["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as error:
            last_error = error
            invalid_content = False
            if attempt < 4:
                time.sleep(2 ** attempt)
            continue
        try:
            analysis = extract_object(content)
            normalize_steer(analysis["steer"])
            return analysis
        except ValueError as error:
            last_error = error
            invalid_content = True
            rejected.append({"content": content, "error": str(error)})
            payload_body["messages"] = payload_body["messages"][:2] + [{
                "role": "user", "content": "Your previous response failed schema validation: "
                + str(error) + ". Return the complete required JSON object from the original evidence."}]
    if invalid_content:
        raise AnalysisRejected([str(last_error)], {"rejected_responses": rejected})
    raise RuntimeError(f"Analyzer failed after retries: {last_error}")


def _bounded_content(value, limit=1800):
    text = str(value)
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n...[observation middle omitted]...\n" + text[-half:]


def _compact_retry_feedback(feedback):
    """Keep retry evidence causal without embedding complete trajectories."""
    compact = []
    for item in feedback or []:
        row = {
            "attempt": item.get("attempt"),
            "steering_prompt": _bounded_content(item.get("steering_prompt", ""), 1200),
            "local_feedback": item.get("local_feedback", []),
            "candidate_trajectories": [],
        }
        for candidate in item.get("candidate_trajectories", []):
            if not isinstance(candidate, dict):
                continue
            assistants = [m for m in candidate.get("messages", [])
                          if m.get("role") == "assistant"]
            row["candidate_trajectories"].append({
                "scenario": candidate.get("scenario"),
                "task_id": candidate.get("task_id"),
                "termination_reason": candidate.get("termination_reason"),
                "truncated": candidate.get("truncated"),
                "assistant_turns": [
                    {"content": _bounded_content(m.get("content", ""), 700),
                     "tool_calls": m.get("tool_calls", [])}
                    for m in assistants[-3:]
                ],
            })
        compact.append(row)
    return compact


def trajectory_view(path: str, focus_assistant_turn: int) -> dict:
    value = read_json(Path(path))
    messages = value.get("messages", [])
    assistant_seen = -1
    focus_message = 0
    for index, message in enumerate(messages):
        if message.get("role") == "assistant":
            assistant_seen += 1
            if assistant_seen == focus_assistant_turn:
                focus_message = index
                break
    # Keep analyzer input well below the 32768-token runtime window. The full
    # immutable trajectories remain on disk for audit and training.
    selected = set(range(min(2, len(messages))))
    selected.update(range(max(0, focus_message - 2), min(len(messages), focus_message + 3)))
    compact = []
    previous = -2
    for index in sorted(selected):
        if index != previous + 1:
            compact.append({"role": "system", "content": "[unrelated trajectory span omitted]"})
        message = dict(messages[index])
        message["content"] = _bounded_content(message.get("content", ""))
        compact.append(message)
        previous = index
    return {
        "scenario": value.get("scenario"),
        "task_id": value.get("task_id"),
        "messages": compact,
        "verifier": verification_evidence(Path(path).parent),
    }


def assert_pair_binding(pair: dict) -> tuple[dict, dict]:
    """Fail closed if serialized divergence fields do not match source traces."""
    focus = int(pair["divergence"]["assistant_turn"])
    corrected_focus = int(
        pair["divergence"].get("corrected_assistant_turn", focus)
    )
    failed = read_json(Path(pair["failed_trajectory_path"]))
    corrected = read_json(Path(pair["corrected_trajectory_path"]))
    failed_turns = assistant_turns(failed)
    corrected_turns = assistant_turns(corrected)
    if focus >= len(failed_turns) or corrected_focus >= len(corrected_turns):
        raise ValueError(f"causal turn {focus} is absent from one source trajectory")
    actual_failed = canonical_decision(failed_turns[focus])
    actual_expected = canonical_decision(corrected_turns[corrected_focus])
    if actual_failed != pair["divergence"].get("failed_decision"):
        raise ValueError("serialized failed_decision is not the action at causal turn")
    if actual_expected != pair["divergence"].get("corrected_decision"):
        raise ValueError("serialized corrected_decision is not the action at causal turn")
    actual = first_divergence(failed, corrected)
    if actual["assistant_turn"] != focus:
        raise ValueError("declared causal turn is not the first behavioral divergence")
    if actual.get("corrected_assistant_turn") != corrected_focus:
        raise ValueError("declared reference turn is not aligned with the first divergence")
    if actual_failed == actual_expected and actual.get("mismatch_kind") != "transition_mismatch":
        raise ValueError("declared causal turn has no action or transition divergence")
    return failed, corrected


def render_integrated_steer(steer: str) -> str:
    """Wrap the Teacher's single rewritten Steer for model injection."""
    return (
        "Verified causal steering instruction. Apply only the rules whose "
        "preconditions hold.\n\n" + str(steer).strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--api-key", default="EMPTY")
    parser.add_argument("--model", required=True)
    parser.add_argument("--analyzer-policy", required=True)
    args = parser.parse_args()
    store = SkillStore(args.store)
    latest = store.latest_by_task()
    processed_evidence = {
        row.get("evidence_id") for row in store.events() if row.get("evidence_id")
    }
    created = revised = retained = retired = 0
    for pair in iter_jsonl(args.pairs) or []:
        evidence_id = stable_id(
            "evidence",
            f"{ANALYSIS_SCHEMA}|{pair['step']}|{pair['failed_run_dir']}|"
            f"{pair['corrected_run_dir']}",
        )
        if pair.get("retry_feedback"):
            evidence_id = stable_id(evidence_id, json.dumps(pair["retry_feedback"], sort_keys=True))
        if evidence_id in processed_evidence:
            print(
                f"SKILL_ANALYSIS_SIGNAL task={pair['task_key']} "
                f"evidence={evidence_id} status=cached",
                flush=True,
            )
            continue
        stored_previous = latest.get(pair["task_key"])
        current_lineage = recovery_lineage(pair["failed_run_dir"])
        # The append-only store is an audit log, not a cross-trajectory memory.
        # A previous Steer is available only inside the same repair transaction.
        previous = (
            stored_previous
            if (
                (stored_previous or {}).get("analysis_schema") == ANALYSIS_SCHEMA
                and int((stored_previous or {}).get("step", -1)) == int(pair["step"])
                and current_lineage
                and str((stored_previous or {}).get("repair_lineage") or "") == current_lineage
            )
            else None
        )
        focus = int(pair["divergence"]["assistant_turn"])
        previous = accepted_memory(previous)
        try:
            failed_trajectory, _ = assert_pair_binding(pair)
        except ValueError as error:
            # Counterfactual generation can terminate before the declared
            # action. Such a pair has no causal evidence and must not abort
            # the whole online batch; retain it in the audit directory and
            # let the repair controller fall through to the next option.
            print(
                f"SKILL_ANALYSIS_SIGNAL task={pair.get('task_key')} "
                f"status=invalid_counterfactual reason={error}", flush=True
            )
            continue
        action_delta = causal_action_delta(
            pair["divergence"].get("failed_decision"),
            pair["divergence"].get("corrected_decision"),
            pair["divergence"].get("mismatch_kind"),
        )
        same_lineage = same_recovery_lineage(previous, pair["failed_run_dir"])
        evidence = {
            "task_key": pair["task_key"],
            "task_text": pair.get("task_text", ""),
            "declared_first_divergence": pair["divergence"],
            "action_delta": action_delta,
            "failed": trajectory_view(pair["failed_trajectory_path"], focus),
            "verified_counterfactual": trajectory_view(
                pair["corrected_trajectory_path"], int(
                    pair["divergence"].get("corrected_assistant_turn", focus)
                )
            ),
            "counterfactual_source": pair["source_kind"],
            "same_recovery_lineage": same_lineage,
            "retry_feedback": pair.get("retry_feedback", []),
            "previous_steer": (
                {
                    "integrated_prompt": previous["skill"],
                    "version": previous["version"],
                    "status": previous["status"],
                    "verified_mechanisms": [
                        {
                            "index": step.get("index"),
                            "causal_signature": step.get("causal_signature"),
                            "failure_type": step.get("failure_type"),
                            "failure_mechanism": step.get("failure_mechanism"),
                            "steer": step.get("steer"),
                        }
                        for step in previous.get("steer_steps", [])
                    ],
                }
                if previous else None
            ),
        }
        analysis = grounded_analysis(
            args.api_url, args.api_key, args.model, evidence, previous,
            same_lineage=same_lineage,
        )
        decision = analysis["decision"]
        skill_id = (
            previous["skill_id"] if previous
            else stable_id("skill", f"{ANALYSIS_SCHEMA}|{pair['task_key']}")
        )
        version = int((stored_previous or {}).get("version", 0)) + 1
        failure_divergences = dict((previous or {}).get("failure_divergences") or {})
        failure_divergences[pair["failed_run_dir"]] = pair["divergence"]
        status = "proposed"
        # The action and intervention index are one atomic evidence unit.  An
        # Analyzer may reject its causality, but it may never move the index
        # while retaining another turn's expected action.
        causal_turn = focus
        causal_divergence = dict(pair["divergence"])
        causal_divergence["assistant_turn"] = causal_turn
        causal_prefix_decisions = [
            canonical_decision(turn)
            for turn in assistant_turns(failed_trajectory)[:causal_turn]
        ]
        previous_steps = [dict(step) for step in (previous or {}).get("steer_steps", [])]
        current_step = {
            "index": len(previous_steps) + 1,
            "step_id": stable_id("steer_step", evidence_id),
            "status": "proposed",
            "assistant_turn": causal_turn,
            "reference_assistant_turn": int(
                pair["divergence"].get("corrected_assistant_turn", causal_turn)
            ),
            "summary": str(analysis["summary"]),
            "failure_mechanism": str(analysis["failure_mechanism"]),
            "teacher_failure_explanation": analysis["teacher_failure_explanation"],
            "teacher_reported_failure_type": analysis["teacher_reported_failure_type"],
            "teacher_reported_causal_turn": analysis["teacher_reported_causal_turn"],
            "teacher_reported_relation": analysis["teacher_reported_relation"],
            "failure_type": action_delta["failure_type"],
            "causal_signature": action_delta["signature"],
            "action_delta": action_delta,
            "relation_to_prior": analysis["relation_to_prior"],
            "steer": analysis["steer"],
            "steer_fields": analysis["steer_fields"],
            "failed_decision": pair["divergence"].get("failed_decision"),
            "expected_decision": pair["divergence"].get("corrected_decision"),
            "failed_run_dir": pair["failed_run_dir"],
            "corrected_run_dir": pair["corrected_run_dir"],
            "source_kind": pair["source_kind"],
            "source_policy": pair["source_policy"],
        }
        # A genuinely new action signature appends a new mechanism.  A
        # recurrence/revision replaces its matching mechanism instead of
        # duplicating it in the Teacher-integrated Steer prompt.
        previous_steps = merge_steer_step(
            previous_steps, current_step, analysis["relation_to_prior"]
        )
        integrated_steer = render_integrated_steer(analysis["steer"])
        current_step["integrated_steer"] = integrated_steer
        record = {
            "skill_id": skill_id,
            "evidence_id": evidence_id,
            "version": version,
            "parent_version": int(previous["version"]) if previous else None,
            "step": pair["step"],
            "task_key": pair["task_key"],
            "task_text": pair.get("task_text", ""),
            "status": status,
            "analysis_schema": ANALYSIS_SCHEMA,
            "repair_lineage": current_lineage,
            "decision": decision,
            "summary": str(analysis["summary"]),
            "failure_mechanism": str(analysis["failure_mechanism"]),
            "failure_type": action_delta["failure_type"],
            "causal_signature": action_delta["signature"],
            # Legacy keys remain serialized for trainer/store compatibility.
            "skill": integrated_steer,
            "steer": integrated_steer,
            "steer_steps": previous_steps,
            "active_step_index": current_step["index"],
            "divergence": pair["divergence"],
            "causal_divergence": causal_divergence,
            "causal_prefix_decisions": causal_prefix_decisions,
            "failure_divergences": failure_divergences,
            # Preserve verifier-grounded failure identity across revisions.
            # Otherwise every proposed version forgets the prior failure and
            # repeated-signature teacher rescue can never fire.
            "failure_signatures": list((previous or {}).get("failure_signatures") or []),
            "source_kind": pair["source_kind"],
            "source_policy": pair["source_policy"],
            "plain_policy": pair["plain_policy"],
            "analyzer_policy": args.analyzer_policy,
            "failed_run_dir": pair["failed_run_dir"],
            "original_run_dir": (previous or {}).get("original_run_dir", pair["failed_run_dir"]),
            "retained_run_dir": (previous or {}).get("retained_run_dir"),
            "retained_interventions": list((previous or {}).get("retained_interventions", [])),
            "corrected_run_dir": pair["corrected_run_dir"],
            "verification_runs": list((previous or {}).get("verification_runs") or []),
            "status_history": [{"status": status, "step": pair["step"]}],
        }
        store.append(record)
        processed_evidence.add(evidence_id)
        latest[pair["task_key"]] = record
        if decision == "create": created += 1
        elif decision == "revise": revised += 1
        elif decision == "retain": retained += 1
        else: retired += 1
        print(
            f"SKILL_ANALYSIS_SIGNAL task={pair['task_key']} id={skill_id} "
            f"version={version} decision={decision}", flush=True
        )
    store.compact()
    print(
        f"SKILL_ANALYSIS_SUMMARY created={created} revised={revised} "
        f"retained={retained} retired={retired}"
    )


if __name__ == "__main__":
    main()
