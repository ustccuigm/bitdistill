#!/usr/bin/env python3
"""Consume verifier events and repair each newly failed task without a batch barrier.

The W4 discovery producer and this consumer run concurrently.  The first rejected
trajectory for a task opens one causal repair transaction immediately.  Further
plain failures for that task remain ordinary OPD evidence but do not create
conflicting Skill versions in parallel.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from common import iter_jsonl, read_json, task_key, write_jsonl
from store import SkillStore


def emit(message: str) -> None:
    print(message, flush=True)


def run(command: list[str], *, env: dict[str, str] | None = None, log: Path | None = None) -> None:
    merged = {**os.environ, **(env or {})}
    emit("SKILL_REPAIR_COMMAND " + " ".join(command))
    if log is None:
        result = subprocess.run(command, env=merged)
    else:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            result = subprocess.run(command, env=merged, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")


def launch(command: list[str], *, env: dict[str, str], log: Path) -> tuple[subprocess.Popen, object]:
    merged = {**os.environ, **env}
    log.parent.mkdir(parents=True, exist_ok=True)
    handle = log.open("a", encoding="utf-8")
    process = subprocess.Popen(command, env=merged, stdout=handle, stderr=subprocess.STDOUT)
    return process, handle


def wait_pair(processes: list[tuple[subprocess.Popen, object, str]]) -> None:
    failures = []
    for process, handle, name in processes:
        code = process.wait()
        handle.close()
        if code:
            failures.append(f"{name}={code}")
    if failures:
        raise RuntimeError("counterfactual rollout failed: " + ", ".join(failures))


def restored_state(path: Path, resume_system_errors: bool) -> tuple[set[str], set[str]]:
    """Return completed event/task IDs without concealing failed transactions."""
    latest: dict[str, dict] = {}
    for row in iter_jsonl(path) or []:
        event_id = row.get("event_id")
        if event_id:
            latest[str(event_id)] = row
    processed, repaired = set(), set()
    for event_id, row in latest.items():
        if row.get("repair_status") == "system_error":
            if not resume_system_errors:
                raise RuntimeError("Previous repair failed with a system error; inspect before retry")
            # The caller must explicitly authorize this narrow recovery after
            # fixing the underlying infrastructure fault. Keep the old state
            # record as audit evidence and rerun only this unfinished event.
            continue
        processed.add(event_id)
        if row.get("repair_complete") and row.get("task_key"):
            repaired.add(str(row["task_key"]))
    return processed, repaired


class RepairConsumer:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.route = args.route
        self.python = args.python
        self.store_path = args.store
        self.prompts = {}
        for row in iter_jsonl(args.prompt_manifest) or []:
            meta = row.get("metadata") or {}
            self.prompts[task_key(meta.get("scenario", "unknown"), meta.get("task_id", -1))] = row
        self.processed_events, self.repaired_tasks = restored_state(
            args.state, args.resume_system_errors
        )
        self.repair_failures: dict[str, int] = {}
        self.state_lock = threading.Lock()

    def record_state(self, row: dict) -> None:
        self.args.state.parent.mkdir(parents=True, exist_ok=True)
        with self.state_lock:
            with self.args.state.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def event_plain_root(self, event: dict, root: Path) -> Path:
        scenario = str(event["scenario"])
        task_id = int(event["task_id"])
        attempt = int(event["attempt"])
        source = Path(event["run_dir"])
        link = root / "runs" / scenario / f"task_{task_id}" / f"attempt_{attempt}"
        link.mkdir(parents=True, exist_ok=True)
        # Path.glob does not recurse into a directory symlink.  Link the files
        # inside a real attempt directory so collect_runs sees trajectory.json
        # while the immutable verifier evidence remains identity-preserving.
        for name in ("trajectory.json", "verify.code.json", "verify.log", "agent.log", "snapshots"):
            source_file = source / name
            destination = link / name
            if source_file.exists() and not destination.exists():
                destination.symlink_to(source_file)
        return root

    def build_pairs(self, plain_runs: Path, work: Path, suffix: str) -> Path | None:
        pairs = work / f"{suffix}.pairs.jsonl"
        unresolved = work / f"{suffix}.unresolved.jsonl"
        run(
            [
                self.python, str(self.route / "build_counterfactuals.py"),
                "--plain-runs", str(plain_runs),
                "--shadow-runs", str(work / "shadow" / "runs"),
                "--teacher-runs", str(work / "teacher" / "runs"),
                "--output", str(pairs), "--unresolved", str(unresolved),
                "--prompt-manifest", str(self.args.prompt_manifest),
                "--step", str(self.args.step),
                "--plain-policy", str(self.args.runtime),
                "--shadow-policy", str(self.args.master),
                "--teacher-policy", str(self.args.teacher),
            ]
        )
        return pairs if pairs.is_file() and pairs.stat().st_size else None

    def analyze(self, pairs: Path, work: Path) -> None:
        run(
            [
                "bash", str(self.route / "analyze_with_server.sh"),
                str(self.args.teacher), str(pairs), str(self.store_path),
                "0", "1", str(self.args.teacher),
            ],
            env={
                "ANALYZER_ENDPOINT": self.args.teacher_endpoints.split(",")[0],
                "ANALYZER_SERVED_MODEL": os.environ.get("MODEL_SERVING_NAME", "Qwen3-8B"),
            },
            log=work / "logs" / "analyze.log",
        )

    def counterfactuals(self, prompt: Path, work: Path) -> None:
        common = [str(prompt), self.args.counterfactual_attempts]
        shadow_cmd = [
            "bash", str(self.route / "run_tool_use_policy.sh"), str(self.args.master),
            str(work / "shadow"), common[0], "0", "1", "bfloat16", common[1],
        ]
        teacher_cmd = [
            "bash", str(self.route / "run_tool_use_policy.sh"), str(self.args.teacher),
            str(work / "teacher"), common[0], "0", "1", "bfloat16", common[1],
        ]
        processes = [
            (*launch(shadow_cmd, env={"POLICY_ENDPOINTS": self.args.shadow_endpoints},
                     log=work / "logs" / "shadow.log"), "shadow"),
            (*launch(teacher_cmd, env={"POLICY_ENDPOINTS": self.args.teacher_endpoints},
                     log=work / "logs" / "teacher.log"), "teacher"),
        ]
        wait_pair(processes)

    def latest_status(self, key: str) -> str:
        row = SkillStore(self.store_path).latest_by_task(self.args.step).get(key)
        return str((row or {}).get("status", "missing"))

    def latest_record(self, key: str) -> dict:
        return SkillStore(self.store_path).latest_by_task(self.args.step).get(key) or {}

    def recorded_run_root(self, run_dir: str, root: Path) -> Path:
        trajectory = json.loads((Path(run_dir) / "trajectory.json").read_text(encoding="utf-8"))
        event = {
            "scenario": trajectory["scenario"],
            "task_id": trajectory["task_id"],
            "attempt": int(Path(run_dir).name.removeprefix("attempt_")),
            "run_dir": run_dir,
        }
        return self.event_plain_root(event, root)

    def validate(self, prompt: Path, work: Path, key: str, worker_id: int) -> str:
        budget = max(1, int(self.args.validation_attempts))
        pairs = work / "initial.pairs.jsonl"
        revision = 1
        fixed_reference = None
        while True:
            pair = next(iter(iter_jsonl(pairs)), None)
            if pair is None:
                raise RuntimeError("repair has no bound counterfactual pair")
            reference = str(Path(pair["corrected_trajectory_path"]).resolve())
            fixed_reference = fixed_reference or reference
            if reference != fixed_reference:
                raise RuntimeError("repair changed its fixed teacher reference")
            turn = int(pair["divergence"]["assistant_turn"])
            feedback = []
            status = self.latest_status(key)
            for attempt in range(1, budget + 1):
                if status == "retired":
                    return "retired"
                output = work / "skill_aware" / f"revision{revision:03d}-attempt{attempt:02d}"
                self.validate_attempt(prompt, output, key, worker_id, "steer")
                status = self.latest_status(key)
                if status in {"verified", "locally_verified"}:
                    break
                if status != "unresolved":
                    raise RuntimeError(f"unexpected validation status: {status}")
                record = self.latest_record(key)
                feedback.append({
                    "attempt": attempt,
                    "steering_prompt": record["skill"],
                    "local_feedback": record.get("local_feedback", []),
                    "candidate_trajectories": [
                        read_json(Path(directory) / "trajectory.json")
                        for directory in record.get("verification_runs", [])
                    ],
                })
                if attempt < budget:
                    # Keep the original history, reference and turn fixed.
                    # Failed candidates are feedback, never new repair anchors.
                    retry = dict(pair, retry_feedback=feedback)
                    retry_path = work / f"retry-{revision:03d}-{attempt:02d}.pairs.jsonl"
                    write_jsonl(retry_path, [retry])
                    self.analyze(retry_path, work)
                    status = self.latest_status(key)
            if status == "unresolved":
                return "retained_after_exhausted_retries"
            record = self.latest_record(key)
            if status == "verified":
                return status
            continuation = record.get("retained_run_dir")
            if not continuation:
                raise RuntimeError(f"accepted correction lacks retained trajectory: {key}")
            plain = self.recorded_run_root(continuation, work / f"continuation-{revision:03d}")
            revision += 1
            pairs = self.build_pairs(plain, work, f"revision-{revision:03d}")
            if pairs is None:
                return "retained_without_further_divergence"
            self.analyze(pairs, work)

    def validate_attempt(self, prompt: Path, output: Path, key: str,
                         worker_id: int, mode: str) -> None:
        run([
            "bash", str(self.route / "run_skill_aware_validation.sh"),
            str(self.args.runtime), str(self.store_path), str(output),
            str(prompt), "0", str(self.args.proxy_port + worker_id * 20),
            "1", str(self.args.step),
        ], env={
            "W4_HOT_ENDPOINTS": self.args.w4_endpoints,
            "SKILL_TASK_KEY": key, "SKILL_PROXY_MODE": mode,
        }, log=output / "validation.log")
        emit(f"SKILL_REPAIR_SIGNAL task={key} mode={mode} status={self.latest_status(key)}")

    def repair(self, event_id: str, event: dict, worker_id: int) -> str:
        key = task_key(event["scenario"], event["task_id"])
        work = self.args.work_root / event_id
        work.mkdir(parents=True, exist_ok=True)
        prompt_row = self.prompts.get(key)
        if prompt_row is None:
            raise RuntimeError(f"prompt missing for {key}")
        prompt = work / "prompt.jsonl"
        write_jsonl(prompt, [prompt_row])
        plain = self.event_plain_root(event, work / "plain")
        emit(
            f"SKILL_REPAIR_SIGNAL task={key} event={event_id} "
            f"status=counterfactual_started"
        )
        self.counterfactuals(prompt, work)
        pairs = self.build_pairs(plain / "runs", work, "initial")
        if pairs is None:
            return "no_verified_counterfactual"
        self.analyze(pairs, work)
        if self.latest_status(key) == "missing":
            return "no_verified_counterfactual"
        return self.validate(prompt, work, key, worker_id)

    def consume(self) -> None:
        self.args.events_dir.mkdir(parents=True, exist_ok=True)
        scheduled_tasks = set(self.repaired_tasks)
        free_workers = list(range(self.args.repair_workers))
        futures: dict[concurrent.futures.Future, tuple[str, dict, str, int]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.repair_workers) as pool:
            while True:
                for future in list(futures):
                    if not future.done():
                        continue
                    event_id, event, key, worker_id = futures.pop(future)
                    free_workers.append(worker_id)
                    try:
                        repair_status = future.result()
                    except Exception as exc:
                        failures = self.repair_failures.get(event_id, 0) + 1
                        self.repair_failures[event_id] = failures
                        scheduled_tasks.discard(key)
                        emit(
                            f"SKILL_REPAIR_ERROR event={event_id} task={key} "
                            f"attempt={failures}/{self.args.system_retries} error={exc!r}"
                        )
                        if failures < self.args.system_retries:
                            continue
                        self.record_state({"event_id": event_id, "task_key": key,
                                           "repair_status": "system_error", "repair_complete": False})
                        raise RuntimeError(f"Repair exhausted system retries for {key}") from exc
                    self.repaired_tasks.add(key)
                    self.record_state({
                        "event_id": event_id, "task_key": key,
                        "rollout_status": "rejected", "repair_status": repair_status,
                        "repair_complete": True,
                        "counterfactual_attempts": int(self.args.counterfactual_attempts),
                        "validation_attempts": int(self.args.validation_attempts),
                    })
                    self.processed_events.add(event_id)
                    emit(
                        f"SKILL_STREAM_SIGNAL event={event_id} task={key} "
                        f"rollout=rejected repair={repair_status}"
                    )

                pending = [
                    path for path in sorted(self.args.events_dir.glob("*.json"))
                    if path.stem not in self.processed_events
                    and path.stem not in {meta[0] for meta in futures.values()}
                ]
                made_progress = False
                for path in pending:
                    event_id = path.stem
                    event = json.loads(path.read_text(encoding="utf-8"))
                    key = task_key(event["scenario"], event["task_id"])
                    status = str(event.get("status"))
                    if status != "rejected":
                        if status != "accepted":
                            raise RuntimeError(f"Invalid rollout execution status: {status}")
                        self.record_state({
                            "event_id": event_id, "task_key": key,
                            "rollout_status": status, "repair_status": "not_required",
                            "repair_complete": False,
                        })
                        self.processed_events.add(event_id)
                        emit(
                            f"SKILL_STREAM_SIGNAL event={event_id} task={key} "
                            f"rollout={status} repair=not_required"
                        )
                        made_progress = True
                    elif key in scheduled_tasks:
                        self.record_state({
                            "event_id": event_id, "task_key": key,
                            "rollout_status": status,
                            "repair_status": "merged_with_task_repair",
                            "repair_complete": False,
                        })
                        self.processed_events.add(event_id)
                        made_progress = True
                    elif free_workers:
                        worker_id = free_workers.pop(0)
                        scheduled_tasks.add(key)
                        future = pool.submit(self.repair, event_id, event, worker_id)
                        futures[future] = (event_id, event, key, worker_id)
                        made_progress = True

                if self.args.discovery_done.is_file() and not pending and not futures:
                    break
                if not made_progress:
                    time.sleep(0.25)
        emit(
            f"SKILL_STREAM_SUMMARY events={len(self.processed_events)} "
            f"repaired_tasks={len(self.repaired_tasks)} status=drained"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--events-dir", type=Path, required=True)
    parser.add_argument("--discovery-done", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--prompt-manifest", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--teacher", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--w4-endpoints", required=True)
    parser.add_argument("--shadow-endpoints", required=True)
    parser.add_argument("--teacher-endpoints", required=True)
    parser.add_argument("--counterfactual-attempts", default="4")
    parser.add_argument("--validation-attempts", default="4")
    # Keep proxies below Linux's default ephemeral range (32768-60999), since
    # tool-use environment allocates many temporary MCP ports while repairs run concurrently.
    parser.add_argument("--proxy-port", type=int, default=25000)
    parser.add_argument("--repair-workers", type=int, default=4)
    parser.add_argument("--system-retries", type=int, default=3)
    parser.add_argument("--resume-system-errors", action="store_true",
                        help="Retry only prior system-error events after their root cause is fixed")
    parser.add_argument("--python", required=True)
    RepairConsumer(parser.parse_args()).consume()


if __name__ == "__main__":
    main()
