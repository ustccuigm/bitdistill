#!/usr/bin/env python3
"""Select tool-use environment prompt rows for tasks that current quantized W4 failed."""

from __future__ import annotations

import argparse
from pathlib import Path

from steerdistill.common import collect_runs, iter_jsonl, task_key, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-runs", type=Path, required=True)
    parser.add_argument("--prompt-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selection", choices=("any_failure", "no_success"), default="any_failure")
    args = parser.parse_args()
    failed = set()
    for key, runs in collect_runs(args.plain_runs).items():
        if args.selection == "any_failure" and any(not run["success"] for run in runs):
            failed.add(key)
        elif args.selection == "no_success" and runs and not any(run["success"] for run in runs):
            failed.add(key)
    rows = []
    for row in iter_jsonl(args.prompt_manifest) or []:
        metadata = row.get("metadata") or {}
        key = task_key(metadata.get("scenario", "unknown"), metadata.get("task_id", -1))
        if key in failed:
            rows.append(row)
    count = write_jsonl(args.output, rows)
    print(f"FAILURE_MANIFEST_SIGNAL failed_tasks={len(failed)} rows={count} output={args.output}")


if __name__ == "__main__":
    main()
