#!/usr/bin/env python3
"""Pair failed SteerDistill-W4 trajectories with verified counterfactuals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from steerdistill.common import collect_runs, first_divergence, iter_jsonl, task_key, write_jsonl


def choose_success(runs: list[dict]) -> dict | None:
    successes = [run for run in runs if run["success"]]
    return successes[0] if successes else None


def task_texts(prompt_manifest: Path | None) -> dict[str, str]:
    result = {}
    if prompt_manifest is None:
        return result
    for row in iter_jsonl(prompt_manifest) or []:
        metadata = row.get("metadata") or {}
        key = task_key(metadata.get("scenario", "unknown"), metadata.get("task_id", -1))
        text = row.get("task") or row.get("text") or row.get("prompt") or ""
        if row.get("prompt"):
            matches = re.findall(
                r"<\|im_start\|>user\n(.*?)(?:<\|im_end\|>|$)",
                str(row["prompt"]),
                re.S,
            )
            if matches:
                # tool-use environment training prompts contain the real task as the first user
                # turn and may serialize tool observations as later user turns.
                # The last match is often a 20K+ <tool_response>, which cannot
                # identify the task in a fresh environment request.
                text = matches[0].strip()
        result[key] = str(text)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-runs", type=Path, required=True)
    parser.add_argument("--shadow-runs", type=Path, required=True)
    parser.add_argument("--teacher-runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--prompt-manifest", type=Path)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--plain-policy", required=True)
    parser.add_argument("--shadow-policy", required=True)
    parser.add_argument("--teacher-policy", required=True)
    args = parser.parse_args()

    plain = collect_runs(args.plain_runs)
    shadow = collect_runs(args.shadow_runs)
    teacher = collect_runs(args.teacher_runs)
    texts = task_texts(args.prompt_manifest)
    paired, unresolved = [], []
    for key, runs in sorted(plain.items()):
        failures = [run for run in runs if not run["success"]]
        if not failures:
            continue
        # The paper fixes one successful frozen full-precision teacher
        # reference for revision. A shadow/master success is not an equivalent
        # reference and therefore cannot silently become a correction source.
        corrected = choose_success(teacher.get(key, []))
        source_kind = "teacher"
        source_policy = args.teacher_policy
        for failure in failures:
            base = {
                "step": args.step,
                "task_key": key,
                "task_text": texts.get(key, ""),
                "plain_policy": args.plain_policy,
                "failed_run_dir": failure["run_dir"],
                "failed_trajectory_path": failure["trajectory_path"],
            }
            if corrected is None:
                unresolved.append({**base, "reason": "no_verified_counterfactual"})
                continue
            paired.append(
                {
                    **base,
                    "source_kind": source_kind,
                    "source_policy": source_policy,
                    "corrected_run_dir": corrected["run_dir"],
                    "corrected_trajectory_path": corrected["trajectory_path"],
                    "divergence": first_divergence(
                        failure["trajectory"], corrected["trajectory"]
                    ),
                }
            )
    pair_count = write_jsonl(args.output, paired)
    unresolved_count = write_jsonl(args.unresolved, unresolved)
    print(
        f"COUNTERFACTUAL_PAIR_SIGNAL step={args.step} failures={pair_count + unresolved_count} "
        f"paired={pair_count} unresolved={unresolved_count}"
    )


if __name__ == "__main__":
    main()
