"""Validate the output contract of a non-tool benchmark online adapter."""
import argparse
import json
from pathlib import Path


def validate(row, index, benchmark):
    if not isinstance(row, dict):
        raise ValueError(f"row {index}: expected object")
    if row.get("benchmark") != benchmark:
        raise ValueError(f"row {index}: benchmark is not {benchmark!r}")
    if not str(row.get("task_key") or "").strip():
        raise ValueError(f"row {index}: missing stable task_key")
    if not str(row.get("completion") or "").strip() and not row.get("completion_tool_calls"):
        raise ValueError(f"row {index}: missing real assistant completion")
    if not str(row.get("source_run") or "").strip():
        raise ValueError(f"row {index}: missing source_run")
    verifier = row.get("verifier")
    if not isinstance(verifier, dict) or "success" not in verifier:
        raise ValueError(f"row {index}: verifier.success is required")
    snapshot = row.get("state_snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError(f"row {index}: exact state_snapshot is required")
    for key in ("snapshot_id", "prefix_hash", "before_state_hash", "after_state_hash"):
        if not str(snapshot.get(key) or "").strip():
            raise ValueError(f"row {index}: state_snapshot.{key} is required")
    if row.get("restore_verified") is not True:
        raise ValueError(f"row {index}: restore_verified must be true")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--step", type=int, required=True)
    args = parser.parse_args()
    count = 0
    with args.data.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream, 1):
            if not line.strip():
                continue
            validate(json.loads(line), index, args.benchmark)
            count += 1
    if not count:
        raise ValueError("adapter output is empty")
    print(f"STEER_ADAPTER_CONTRACT_SIGNAL status=passed benchmark={args.benchmark} step={args.step} records={count}")


if __name__ == "__main__":
    main()
