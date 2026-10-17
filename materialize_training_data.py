#!/usr/bin/env python3
"""Materialize identity-safe ordinary OPD and verified recovery distillation."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    api_messages,
    canonical_decision,
    collect_runs,
    inject_skill,
    is_success,
    read_json,
    sampling_by_assistant_turn,
    task_key,
    write_jsonl,
)
from store import SkillStore


def assistant_completion(message: dict) -> str:
    """Keep native tool calls as a supervised completion when content is empty."""
    content = message.get("content")
    if message.get("tool_calls"):
        action = canonical_decision(message)
        return f"{content}\n{action}" if content is not None and str(content) else action
    if content is not None and str(content):
        return str(content)
    return ""


def rows_from_run(
    run: dict,
    mode: str,
    skill: dict | None = None,
    intervention_steers: dict[int, str] | None = None,
    intervention_modes: dict[int, str] | None = None,
    intervention_steps: dict[int, dict] | None = None,
) -> list[dict]:
    trajectory = run["trajectory"]
    sampling = sampling_by_assistant_turn(trajectory)
    intervention_steers = intervention_steers or {}
    intervention_modes = intervention_modes or {}
    intervention_steps = intervention_steps or {}
    if mode in {"skill_recovery", "teacher_rescue"} and skill is not None:
        trigger = int(skill["causal_divergence"]["assistant_turn"])
        if mode == "skill_recovery":
            intervention_steers = {trigger: skill.get("skill", "")}
        intervention_modes.setdefault(trigger, mode)
    prefix, rows, assistant_turn = [], [], 0
    for message_index, message in enumerate(trajectory.get("messages", [])):
        if message.get("role") == "assistant":
            completion = assistant_completion(message)
            turn_mode = intervention_modes.get(
                assistant_turn,
                "skill_recovery" if assistant_turn in intervention_steers else "ordinary_opd",
            )
            has_native_tool_call = bool(message.get("tool_calls"))
            include = (bool(completion) or has_native_tool_call) and (
                mode in {"ordinary_opd", "revised"}
                or assistant_turn in intervention_steers
            )
            if include:
                # Some benchmark protocols render the environment history into
                # a single user prompt. Preserve the actual generation context.
                prompt = api_messages(message.get("model_prompt", prefix))
                skill_text = intervention_steers.get(assistant_turn)
                skill_prompt = inject_skill(prompt, skill_text) if skill_text else prompt
                row = {
                    "prompt": prompt,
                    "skill_prompt": skill_prompt,
                    "completion": completion,
                    "distill_mode": turn_mode,
                    "task_key": f"{trajectory.get('scenario')}:{trajectory.get('task_id')}",
                    "source_run": run["run_dir"],
                    "source_success": run["success"],
                    "assistant_turn": assistant_turn,
                    "message_index": message_index,
                    # A length-limited response did not generate an EOS token.
                    "add_eos": (message.get("generation") or {}).get("finish_reason") != "length",
                    "distill_target": {
                        "ordinary_opd": "bf16_teacher_reverse_kl",
                        "skill_recovery": "previous_w4_skill_forward_kl",
                        "teacher_rescue": "bf16_teacher_forward_kl",
                    }[turn_mode],
                }
                if skill is not None:
                    step = intervention_steps.get(assistant_turn, {})
                    row.update({
                        "skill_id": skill["skill_id"],
                        "skill_version": skill["version"],
                        "steer_step_id": step.get("step_id", skill.get("steer_step_id")),
                        "steer_step_index": step.get("index", skill.get("steer_step_index")),
                        "local_transition_verified": bool(
                            step.get("status") in {"locally_verified", "verified"}
                            or skill.get("local_transition_verified", False)
                        ),
                    })
                if message.get("tool_calls"):
                    row["completion_tool_calls"] = message["tool_calls"]
                    row["completion_content"] = message.get("content") or ""
                sampled = sampling.get(assistant_turn) or {}
                token_ids, logprobs = sampled.get("token_ids"), sampled.get("logprobs")
                if isinstance(token_ids, list) and token_ids:
                    row["completion_token_ids"] = token_ids
                    row["add_eos"] = False
                    if isinstance(logprobs, list) and len(logprobs) == len(token_ids):
                        row["rollout_logprobs"] = logprobs
                rows.append(row)
            assistant_turn += 1
        prefix.append(message)
    return rows


def load_recorded_run(run_dir: str, root: Path, expected_key: str) -> dict | None:
    """Load only an explicitly recorded verifier run under the requested root."""
    directory = Path(run_dir).resolve()
    try:
        directory.relative_to(root.resolve())
    except ValueError:
        return None
    trajectory_path = directory / "trajectory.json"
    if not trajectory_path.is_file():
        return None
    trajectory = read_json(trajectory_path)
    actual_key = task_key(trajectory.get("scenario", "unknown"), trajectory.get("task_id", -1))
    if actual_key != expected_key:
        return None
    return {
        "run_dir": str(directory),
        "trajectory_path": str(trajectory_path),
        "trajectory": trajectory,
        "success": is_success(directory),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-runs", type=Path, required=True)
    parser.add_argument("--skill-runs", type=Path, required=True)
    parser.add_argument("--teacher-runs", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--repair-state", type=Path)
    args = parser.parse_args()

    latest = SkillStore(args.store).latest_by_task(args.step)
    rows = []
    plain_runs = collect_runs(args.plain_runs)
    latest = SkillStore(args.store).latest_by_task(args.step)
    revised_keys = {
        key for key, skill in latest.items()
        if any(step.get("status") in {"locally_verified", "verified", "teacher_rescue"}
               and (step.get("status") != "teacher_rescue" or step.get("rescue_final_success"))
               for step in skill.get("steer_steps", []))
    }
    for key, runs in plain_runs.items():
        if key in revised_keys:
            continue
        for run in runs:
            ordinary = rows_from_run(run, "ordinary_opd")
            if args.repair_state:
                for row in ordinary:
                    row["tool_repair_state"] = str(args.repair_state)
            rows.extend(ordinary)

    for key, skill in sorted(latest.items()):
        steps = list(skill.get("steer_steps") or [])
        if not steps and skill["status"] == "verified":
            steps = [{
                "index": 1, "step_id": f"legacy-{skill['skill_id']}",
                "assistant_turn": int(skill["causal_divergence"]["assistant_turn"]),
                "steer": skill["skill"], "status": "verified",
                "verification_run_dir": (skill.get("verification_runs") or [None])[0],
            }]
        accepted_steps = [
            step for step in steps
            if step.get("status") in {"locally_verified", "verified", "teacher_rescue"}
            and step.get("verification_run_dir")
            and (step.get("status") != "teacher_rescue" or step.get("rescue_final_success"))
        ]
        if accepted_steps:
            # The final accepted trajectory contains the accepted revisions and
            # its unsteered continuation. Old failed suffixes are intentionally
            # absent from this run and therefore cannot receive loss.
            run_dir = accepted_steps[-1]["verification_run_dir"]
            revised = load_recorded_run(run_dir, args.skill_runs, key)
            if revised is not None:
                steer_map = {
                    int(step["assistant_turn"]): step.get("integrated_steer") or skill["skill"]
                    for step in accepted_steps
                    if step.get("status") != "teacher_rescue"
                }
                mode_map = {
                    int(step["assistant_turn"]): (
                        "teacher_rescue"
                        if step.get("status") == "teacher_rescue"
                        else "skill_recovery"
                    )
                    for step in accepted_steps
                }
                step_map = {int(step["assistant_turn"]): step for step in accepted_steps}
                rows.extend(rows_from_run(revised, "revised", skill, steer_map, mode_map, step_map))

        # Exhausted steering retries leave the last accepted trajectory intact.
        # Failed candidates are not verifier-approved correction targets.

    if not rows:
        raise SystemExit("No assistant turns found in W4 discovery runs")
    count = write_jsonl(args.output, rows)
    counts = {mode: sum(row["distill_mode"] == mode for row in rows) for mode in (
        "ordinary_opd", "skill_recovery", "teacher_rescue"
    )}
    print(f"SKILL_DATA_SIGNAL step={args.step} records={count} " + " ".join(
        f"{key}={value}" for key, value in counts.items()
    ))


if __name__ == "__main__":
    main()
