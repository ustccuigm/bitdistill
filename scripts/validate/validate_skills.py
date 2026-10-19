#!/usr/bin/env python3
"""Commit skill only when real AWQ/Marlin W4 passes the verifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from steerdistill.common import (
    assistant_turns,
    canonical_decision,
    causal_transition_match,
    collect_runs,
    failure_signature,
    iter_jsonl,
    prefix_before_assistant_turn,
    prompt_fingerprint,
    read_json,
)
from steerdistill.store import SkillStore


def transition_with_steps(
    store: SkillStore,
    skill: dict,
    status: str,
    steps: list[dict],
    **evidence,
) -> dict:
    """Persist validation status without rebuilding the Teacher prompt."""
    if status in {"verified", "locally_verified"} and steps:
        active = steps[-1]
        steps = [step for step in steps[:-1]
                 if int(step["assistant_turn"]) < int(active["assistant_turn"])] + [active]
    integrated = "" if status == "teacher_rescue" else skill.get("skill", "")
    return store.transition(
        skill["skill_id"],
        status,
        steer_steps=steps,
        skill=integrated,
        steer=integrated,
        **evidence,
    )


def retained_replacement(skill: dict, run: dict, trigger: int, kind: str) -> dict:
    """Replace the old suffix and its intervention map as one transaction."""
    interventions = [dict(item) for item in skill.get("retained_interventions", [])
                     if int(item["assistant_turn"]) < trigger]
    step = skill["steer_steps"][-1]
    interventions.append({
        "assistant_turn": trigger,
        "distill_mode": "teacher_rescue" if kind == "teacher_rescue" else "skill_recovery",
        "steering_prompt": skill["skill"] if kind != "teacher_rescue" else "",
        "skill_id": skill["skill_id"], "skill_version": skill["version"],
        "steer_step_id": step["step_id"], "steer_step_index": step["index"],
        "verification_run_dir": run["run_dir"],
        "expected_decision": canonical_decision(assistant_turns(run["trajectory"])[trigger]),
        "local_transition_verified": True,
    })
    return {"retained_run_dir": run["run_dir"], "retained_interventions": interventions,
            "continuation_run_dir": run["run_dir"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--role-log-root", type=Path, required=True)
    parser.add_argument(
        "--task-key",
        help="Restrict transitions to one repair transaction (required for concurrent repair).",
    )
    parser.add_argument(
        "--rescue", action="store_true",
        help="Validate a teacher-action replay followed by a free-running W4 suffix.",
    )
    args = parser.parse_args()
    store = SkillStore(args.store)
    latest = store.latest_by_task(args.step)
    runs = collect_runs(args.runs)
    injected = set()
    for path in args.role_log_root.glob("proxy-*.jsonl"):
        for row in iter_jsonl(path) or []:
            authenticated_role = (
                row.get("teacher_rescued") if args.rescue else row.get("injected")
            )
            if authenticated_role:
                injected.add((row.get("skill_id"), int(row.get("skill_version", -1)), row.get("prefix_fingerprint")))
    verified = locally_verified = unresolved = rescued = 0
    for key, skill in sorted(latest.items()):
        if args.task_key and key != args.task_key:
            continue
        eligible = {"unresolved"} if args.rescue else {"proposed", "regressed"}
        if skill["status"] not in eligible:
            continue
        candidates = runs.get(key, [])
        trigger = int(skill["causal_divergence"]["assistant_turn"])
        reference_trigger = int(
            skill["causal_divergence"].get(
                "corrected_assistant_turn", skill["causal_divergence"].get("assistant_turn", trigger)
            )
        )
        authenticated = []
        for run in candidates:
            fingerprint = prompt_fingerprint(prefix_before_assistant_turn(run["trajectory"], trigger))
            if (skill["skill_id"], int(skill["version"]), fingerprint) in injected:
                authenticated.append(run)
        raw_successes = [run for run in authenticated if run["success"]]
        reference_path = Path(str(skill.get("corrected_run_dir", ""))) / "trajectory.json"
        reference = read_json(reference_path) if reference_path.is_file() else None
        recorded_steps = list(skill.get("steer_steps") or [])
        expected_decision = (
            recorded_steps[-1].get("expected_decision")
            if recorded_steps else (skill.get("divergence") or {}).get("corrected_decision")
        )
        local_matches = []
        local_match_kinds = {}
        local_feedback = []
        if reference is not None:
            for run in authenticated:
                matched, kind = causal_transition_match(
                    run["trajectory"],
                    reference,
                    trigger,
                    expected_decision,
                    candidate_success=bool(run["success"]),
                    reference_target=reference_trigger,
                )
                if reference.get("snapshot_root") and kind != "verified_terminal_success":
                    receipt_path = Path(run["run_dir"]) / "local_gate.json"
                    if not receipt_path.is_file():
                        # A final answer cannot satisfy an expected tool action.
                        turns = [m for m in run["trajectory"]["messages"] if m.get("role") == "assistant"]
                        if trigger < len(turns) and not turns[trigger].get("tool_calls"):
                            matched, kind = False, "premature_termination"
                        else:
                            raise ValueError("Tool adapter did not check the intervention before continuation")
                    else:
                        receipt = read_json(receipt_path)
                        if (receipt.get("checked_before_continuation") is not True
                                or receipt.get("assistant_turn") != trigger
                                or receipt.get("reference_turn") != reference_trigger
                                or Path(receipt["reference_run"]).resolve() != reference_path.parent.resolve()
                                or receipt.get("accepted") != matched):
                            raise ValueError("Local transition gate evidence mismatch")
                if matched:
                    local_matches.append(run)
                    local_match_kinds[run["run_dir"]] = kind
                local_feedback.append({"run_dir": run["run_dir"], "accepted": matched, "reason": kind})
        causal_successes = [run for run in local_matches if run["success"]]
        evidence = {
            "validation_step": args.step,
            "validation_policy": args.policy,
            "validation_attempts": len(candidates),
            "skill_authenticated_attempts": len(authenticated),
            "validation_successes": len(causal_successes),
            "raw_final_successes": len(raw_successes),
            "verification_runs": [run["run_dir"] for run in authenticated],
            "local_transition_matches": len(local_matches),
            "local_match_kinds": local_match_kinds,
            "local_feedback": local_feedback,
        }
        steps = [dict(step) for step in recorded_steps]
        if not steps:
            steps = [{
                "index": 1, "step_id": f"legacy-{skill['skill_id']}",
                "assistant_turn": trigger, "steer": skill["skill"],
                "reference_assistant_turn": reference_trigger,
                "failure_mechanism": skill.get("failure_mechanism", ""),
                "status": "proposed",
            }]
        if args.rescue:
            # Takeover is a fallback for the whole task. A locally matching
            # teacher action with a failed suffix does not count as success.
            rescue_successes = [run for run in local_matches if run["success"]]
            chosen = rescue_successes[0] if rescue_successes else None
            if chosen is not None:
                steps[-1].update({
                    "status": "teacher_rescue",
                    "verification_run_dir": chosen["run_dir"],
                    "verification_kind": local_match_kinds[chosen["run_dir"]],
                    "rescue_transition_verified": True,
                    "rescue_final_success": bool(chosen["success"]),
                    "corrected_run_dir": chosen["run_dir"],
                })
                evidence.update({
                    "continuation_run_dir": chosen["run_dir"],
                    "rescue_transition_verified": True,
                    "rescue_final_success": bool(chosen["success"]),
                })
                evidence.update(retained_replacement(skill, chosen, trigger, "teacher_rescue"))
            else:
                steps[-1].update({
                    "status": "rescue_failed",
                    "rescue_transition_verified": False,
                    "rescue_final_success": False,
                })
                evidence.update({
                    "rescue_transition_verified": False,
                    "rescue_final_success": False,
                })
            status = "teacher_rescue" if chosen is not None else "rescue_failed"
            transition_with_steps(store, skill, status, steps, **evidence)
            rescued += 1
        elif causal_successes:
            chosen = causal_successes[0]
            steps[-1].update({
                "status": "verified",
                "verification_run_dir": chosen["run_dir"],
                "verification_kind": local_match_kinds[chosen["run_dir"]],
                "expected_decision": canonical_decision(assistant_turns(chosen["trajectory"])[trigger]),
            })
            evidence.update(retained_replacement(skill, chosen, trigger, "steer"))
            transition_with_steps(store, skill, "verified", steps, **evidence)
            verified += 1
            status = "verified"
        elif local_matches:
            chosen = local_matches[0]
            steps[-1].update({
                "status": "locally_verified",
                "verification_run_dir": chosen["run_dir"],
                "verification_kind": local_match_kinds[chosen["run_dir"]],
                "expected_decision": canonical_decision(assistant_turns(chosen["trajectory"])[trigger]),
            })
            evidence.update(retained_replacement(skill, chosen, trigger, "steer"))
            transition_with_steps(
                store, skill, "locally_verified", steps,
                **evidence,
            )
            locally_verified += 1
            status = "locally_verified"
        else:
            signatures = sorted({failure_signature(run) for run in authenticated})
            if not authenticated:
                signatures = ["skill_not_reached"]
            previous = set(skill.get("failure_signatures") or [])
            evidence["failure_signatures"] = sorted(previous | set(signatures))
            # The controller feeds this rejected attempt back into steering
            # refinement at the same restored state and fixed reference.
            steps[-1]["status"] = "unresolved"
            transition_with_steps(store, skill, "unresolved", steps, **evidence)
            unresolved += 1
            status = "unresolved"
        print(
            f"SKILL_VERIFY_SIGNAL task={key} id={skill['skill_id']} "
            f"status={status} successes={len(causal_successes)} "
            f"raw_successes={len(raw_successes)} "
            f"local_transitions={len(local_matches)} attempts={len(candidates)}",
            flush=True,
        )
    store.compact()
    print(
        f"SKILL_VERIFY_SUMMARY verified={verified} locally_verified={locally_verified} "
        f"unresolved={unresolved} teacher_rescue={rescued}"
    )


if __name__ == "__main__":
    main()
