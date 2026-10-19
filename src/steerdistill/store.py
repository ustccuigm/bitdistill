#!/usr/bin/env python3
"""Append-only, versioned skill store."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from steerdistill.common import iter_jsonl


VALID_STATUS = {
    "proposed", "verified", "unresolved", "teacher_rescue",
    "locally_verified", "internalized", "regressed", "retired", "rescue_failed"
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SkillStore:
    def __init__(self, path: Path):
        self.path = path

    def events(self) -> list[dict]:
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                rows = [json.loads(line) for line in handle if line.strip()]
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return rows

    def latest_by_id(self) -> dict[str, dict]:
        return {row["skill_id"]: row for row in self.events()}

    def latest_by_task(self, step: int | None = None) -> dict[str, dict]:
        result = {}
        for row in self.events():
            if step is not None and int(row.get("step", -1)) != step:
                continue
            current = result.get(row["task_key"])
            candidate = (int(row["version"]), row.get("updated_at", ""))
            previous = (
                int(current["version"]), current.get("updated_at", "")
            ) if current else (-1, "")
            if candidate >= previous:
                result[row["task_key"]] = row
        return result

    def append(self, record: dict) -> None:
        missing = {
            "skill_id", "task_key", "version", "status", "skill"
        } - record.keys()
        if missing:
            raise ValueError(f"Skill record missing fields: {sorted(missing)}")
        if record["status"] not in VALID_STATUS:
            raise ValueError(f"Invalid skill status: {record['status']}")
        event = dict(record)
        event.setdefault("created_at", now())
        event["updated_at"] = now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def transition(self, skill_id: str, status: str, **evidence) -> dict:
        if status not in VALID_STATUS:
            raise ValueError(status)
        current = self.latest_by_id().get(skill_id)
        if current is None:
            raise KeyError(skill_id)
        updated = dict(current)
        updated["status"] = status
        updated.setdefault("status_history", []).append(
            {"status": status, "at": now(), **evidence}
        )
        updated.update(evidence)
        self.append(updated)
        return updated

    def compact(self, output: Path | None = None) -> Path:
        destination = output or self.path.with_suffix(".latest.jsonl")
        destination.parent.mkdir(parents=True, exist_ok=True)
        rows = sorted(self.latest_by_id().values(), key=lambda row: row["skill_id"])
        fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=destination.name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--compact", type=Path)
    args = parser.parse_args()
    store = SkillStore(args.store)
    output = store.compact(args.compact)
    print(f"SKILL_STORE_SIGNAL events={len(store.events())} latest={len(store.latest_by_id())} output={output}")


if __name__ == "__main__":
    main()
