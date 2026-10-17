#!/usr/bin/env python3
"""Build the task-to-state-snapshot map used by exact intervention restores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from store import SkillStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=int)
    args = parser.parse_args()

    rows = []
    for task_key, skill in sorted(
        SkillStore(args.store).latest_by_task(args.step).items()
    ):
        failed_dir = Path(str(skill.get("failed_run_dir", "")))
        divergence = skill.get("causal_divergence") or {}
        trigger = int(divergence.get("assistant_turn", -1))
        snapshot_dir = failed_dir / "snapshots" / f"turn_{trigger:04d}"
        manifest = snapshot_dir / "manifest.json"
        if trigger < 0 or not manifest.is_file():
            continue
        scenario, task_id = task_key.rsplit(":", 1)
        rows.append({
            "task_key": task_key,
            "scenario": scenario,
            "task_id": int(task_id),
            "snapshot_dir": str(snapshot_dir),
            "skill_id": skill["skill_id"],
            "skill_version": int(skill["version"]),
            "assistant_turn": trigger,
            "reference_run": skill["corrected_run_dir"],
            "reference_turn": int(divergence.get("corrected_assistant_turn", trigger)),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"STATE_SNAPSHOT_MANIFEST_SIGNAL rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
