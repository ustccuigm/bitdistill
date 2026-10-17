#!/usr/bin/env python3
"""Re-enter discovery and mark previously verified skill internalized/regressed."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import collect_runs
from store import SkillStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-runs", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--policy", required=True)
    args = parser.parse_args()
    store = SkillStore(args.store)
    runs = collect_runs(args.plain_runs)
    internalized = regressed = 0
    for key, record in store.latest_by_task().items():
        if record["status"] not in {"verified", "internalized", "regressed"}:
            continue
        # Discovery for step N is produced before step-N repair/validation.
        # It can evaluate only a Skill that was already verified in an earlier
        # step; otherwise the same no-Skill rollout would immediately mark a
        # newly verified Skill as regressed.
        validation_step = record.get("validation_step")
        if validation_step is None or int(validation_step) >= args.step:
            continue
        attempts = runs.get(key)
        if not attempts:
            continue
        all_success = all(run["success"] for run in attempts)
        status = "internalized" if all_success else "regressed"
        store.transition(
            record["skill_id"], status,
            discovery_step=args.step,
            discovery_policy=args.policy,
            discovery_attempts=len(attempts),
            discovery_successes=sum(run["success"] for run in attempts),
        )
        internalized += int(all_success)
        regressed += int(not all_success)
    store.compact()
    print(
        f"STEER_SKILL_STATUS_SIGNAL step={args.step} internalized={internalized} "
        f"regressed={regressed}"
    )


if __name__ == "__main__":
    main()
