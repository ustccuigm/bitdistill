#!/usr/bin/env python3
"""Fail closed on provenance and completion identity before Skill OPD."""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import re
from pathlib import Path

from steerdistill.common import (
    api_messages,
    canonical_decision,
    decision_descriptor,
    iter_jsonl,
    is_success,
    read_json,
    sampling_by_assistant_turn,
    collect_runs,
    task_key,
)
from steerdistill.store import SkillStore


ANALYSIS_SCHEMA = "causal-steer-v2"


@lru_cache(maxsize=32)
def audit_ordinary_fallback(receipt_path: str, source_run: str, tool_repair_state: str = "") -> bool:
    if not receipt_path:
        return is_success(Path(source_run)) or (
            bool(tool_repair_state) and audit_tool_fallback(tool_repair_state, source_run))
    path = Path(receipt_path)
    receipt = read_json(path)
    if receipt.get("retained_run") != source_run or receipt.get("plain_run") != source_run:
        return False
    shard = path.parent / "training_rows.jsonl"
    if hashlib.sha256(shard.read_bytes()).hexdigest() != receipt.get("rows_sha256"):
        return False
    if receipt.get("accepted_interventions") != 0:
        return False
    fallback = receipt.get("fallback")
    if fallback == "already_successful":
        return is_success(Path(source_run))
    references = [Path(run) for run in receipt.get("reference_runs", [])]
    if any(not (run / "verify.code.json").is_file() for run in references):
        return False
    if fallback == "no_successful_reference":
        return (len(references) == receipt.get("reference_attempts") and len(references) > 0
                and not any(is_success(run) for run in references))
    if fallback == "steering_exhausted":
        trials = list((path.parent / "repairs").rglob("steering.json"))
        return (any(is_success(run) for run in references)
                and receipt.get("steering_retries", 0) > 0
                and len(trials) == receipt["steering_retries"]
                and all(read_json(trial).get("accepted") is False for trial in trials))
    if fallback == "no_alignable_divergence":
        from steerdistill.benchmarks.online_rollout import divergence
        failed = read_json(Path(source_run) / "trajectory.json")
        successful = [run for run in references if is_success(run)]
        return (bool(successful) and receipt.get("attempted") == 0
                and divergence(failed, read_json(successful[-1] / "trajectory.json")) is None)
    return False


def audit_tool_fallback(state_path: str, source_run: str) -> bool:
    root = Path(state_path).parent
    trajectory = read_json(Path(source_run) / "trajectory.json")
    key = task_key(trajectory["scenario"], trajectory["task_id"])
    states = [row for row in iter_jsonl(Path(state_path)) if row.get("task_key") == key
              and row.get("repair_complete")]
    if len(states) != 1:
        return False
    state = states[0]
    event = read_json(root / "events" / f"{state['event_id']}.json")
    if Path(event["run_dir"]).resolve() != Path(source_run).resolve() or event.get("status") != "rejected":
        return False
    work = root / "repairs" / state["event_id"]
    references = collect_runs(work / "teacher/runs").get(key, [])
    expected = state.get("counterfactual_attempts", 0)
    if expected < 1 or len(references) != expected:
        return False
    if state.get("repair_status") == "no_verified_counterfactual":
        # A reference episode may finish successfully while failing to provide
        # a verified local transition. It is still not an accepted correction
        # target, so the original ordinary trajectory remains the only loss.
        return len(references) == expected and expected > 0
    if state.get("repair_status") == "retained_after_exhausted_retries":
        budget = state.get("validation_attempts", 0)
        candidates = list((work / "skill_aware").glob("revision001-attempt*"))
        runs = [collect_runs(candidate).get(key, []) for candidate in candidates]
        return (budget > 0 and len(candidates) == budget and all(runs)
                and any(row["success"] for row in references)
                and not any(row["success"] for group in runs for row in group))
    return False


def verified_prefix_matches(step: dict, trajectory: dict, turn: int) -> bool:
    """A later retained suffix may carry an earlier verified intervention."""
    directory = step.get("verification_run_dir")
    if not directory:
        return False
    verified = read_json(Path(directory) / "trajectory.json")
    def prefix(value):
        count = 0
        for index, message in enumerate(value.get("messages", [])):
            if message.get("role") == "assistant":
                if count == turn:
                    return api_messages(value["messages"][:index]), canonical_decision(message)
                count += 1
        return None
    left, right = prefix(verified), prefix(trajectory)
    return left is not None and left == right


def semantic_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def audit_distinct_mechanisms(skill: dict) -> None:
    by_signature = {}
    by_mechanism = {}
    for step in skill.get("steer_steps", []):
        if step.get("status") not in {"locally_verified", "verified"}:
            continue
        signature = step.get("causal_signature")
        mechanism = semantic_key(step.get("failure_mechanism", ""))
        if not signature or not mechanism:
            raise ValueError("verified Steer lacks causal signature or mechanism")
        previous_mechanism = by_signature.setdefault(signature, mechanism)
        if previous_mechanism != mechanism and step.get("relation_to_prior") != "recurrence":
            raise ValueError("same causal signature changed mechanism without recurrence")
        previous_signature = by_mechanism.setdefault(mechanism, signature)
        if previous_signature != signature:
            raise ValueError("distinct causal signatures reuse one failure mechanism")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    args = parser.parse_args()
    latest = SkillStore(args.store).latest_by_id()
    rows = iter_jsonl(args.data)
    counts = {"ordinary_opd": 0, "skill_recovery": 0, "teacher_rescue": 0}
    exact_tokens, record_count, plain_fallback_valid = 0, 0, True
    read_cached = lru_cache(maxsize=16)(read_json)
    for index, row in enumerate(rows):
        record_count += 1
        if not str(row.get("completion") or "").strip() and not (
            row.get("completion_tool_calls") or row.get("completion_token_ids")
        ):
            raise ValueError(f"row {index}: empty/whitespace completion is not a trajectory")
        mode = row.get("distill_mode")
        if mode not in counts:
            raise ValueError(f"row {index}: invalid distill_mode={mode!r}")
        counts[mode] += 1
        trajectory_path = Path(row["source_run"]) / "trajectory.json"
        trajectory = read_cached(trajectory_path)
        assistants = [m for m in trajectory.get("messages", []) if m.get("role") == "assistant"]
        turn = int(row["assistant_turn"])
        if turn < 0 or turn >= len(assistants):
            raise ValueError(f"row {index}: assistant turn out of range")
        row_decision = canonical_decision({"content": row["completion"], "tool_calls": row.get("completion_tool_calls")})
        if row_decision != canonical_decision(assistants[turn]):
            raise ValueError(f"row {index}: completion identity differs from its source trajectory")
        sampled = sampling_by_assistant_turn(trajectory).get(turn) or {}
        if row.get("completion_token_ids"):
            if row["completion_token_ids"] != sampled.get("token_ids"):
                raise ValueError(f"row {index}: token ids differ from rollout")
            exact_tokens += 1
        if mode == "ordinary_opd":
            if row["skill_prompt"] != row["prompt"] or row["distill_target"] != "bf16_teacher_reverse_kl":
                raise ValueError(f"row {index}: ordinary OPD provenance is invalid")
            if plain_fallback_valid:
                plain_fallback_valid = audit_ordinary_fallback(
                    row.get("revision_receipt", ""), row["source_run"], row.get("tool_repair_state", ""))
        else:
            skill = latest.get(row.get("skill_id"))
            if skill is None:
                raise ValueError(f"row {index}: correction target is not verifier-grounded")
            if mode == "skill_recovery":
                if skill.get("analysis_schema") != ANALYSIS_SCHEMA:
                    raise ValueError(
                        f"row {index}: legacy Steer schema cannot enter causal training"
                    )
                audit_distinct_mechanisms(skill)
                steps = {
                    step.get("step_id"): step for step in skill.get("steer_steps", [])
                }
                step = steps.get(row.get("steer_step_id"))
                completion_decision = row_decision
                expected_decision = step.get("expected_decision") if step else None
                local_kind = (skill.get("local_match_kinds") or {}).get(
                    row["source_run"]
                )
                terminal_match = (
                    decision_descriptor(expected_decision)["kind"] == "final_response"
                    and decision_descriptor(completion_decision)["kind"] == "final_response"
                    and row.get("source_success") is True
                    and (
                        step.get("verification_kind") == "verified_terminal_success"
                        or local_kind == "verified_terminal_success"
                    )
                )
                grounded = (
                    step is not None
                    and step.get("status") in {"locally_verified", "verified"}
                    and verified_prefix_matches(step, trajectory, turn)
                    and row.get("local_transition_verified") is True
                    and (
                        expected_decision == completion_decision
                        or terminal_match
                    )
                )
                if row["skill_prompt"] == row["prompt"] or not grounded:
                    raise ValueError(
                        f"row {index}: Steer recovery lacks a verified local transition"
                    )
            elif mode == "teacher_rescue":
                steps = {
                    step.get("step_id"): step for step in skill.get("steer_steps", [])
                }
                step = steps.get(row.get("steer_step_id"))
                grounded = (
                    step is not None
                    and step.get("status") == "teacher_rescue"
                    and verified_prefix_matches(step, trajectory, turn)
                    and row_decision == step.get("expected_decision")
                    and row["skill_prompt"] == row["prompt"]
                    and row.get("source_success") is True
                    and row.get("distill_target") == "bf16_teacher_forward_kl"
                )
                if not grounded:
                    raise ValueError(
                        f"row {index}: teacher rescue is not bound to its causal action"
                    )
    if not record_count:
        raise SystemExit("Skill OPD data is empty")
    if counts["skill_recovery"] + counts["teacher_rescue"] == 0 and not plain_fallback_valid:
        raise ValueError("Ordinary-only step lacks successful-rollout or exhausted-revision evidence")
    print("SKILL_AUDIT_SIGNAL status=passed " + " ".join(
        [f"records={record_count}"] + [f"{key}={value}" for key, value in counts.items()] +
        [f"exact_rollout_token_rows={exact_tokens}"]
    ))


if __name__ == "__main__":
    main()
