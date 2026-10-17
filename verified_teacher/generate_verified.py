#!/usr/bin/env python3
"""Generate tool-use environment teacher trajectories and keep only code-verifier successes."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from response_bridge import bridge_endpoint
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transition_policy import compile_policy


LOCK = threading.Lock()


def publish_result_event(events_dir: Path, record: dict) -> Path:
    """Atomically publish one completed verifier result for streaming consumers."""
    events_dir.mkdir(parents=True, exist_ok=True)
    identity = (
        f"{record['scenario']}|{record['task_id']}|{record['attempt']}|"
        f"{record['run_dir']}"
    )
    event_id = hashlib.sha256(identity.encode()).hexdigest()[:20]
    destination = events_dir / f"{event_id}.json"
    fd, temporary = tempfile.mkstemp(dir=events_dir, prefix=f".{event_id}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination


def jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_snapshot_manifest(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    result = {}
    for row in jsonl(path):
        key = f"{row['scenario']}:{row['task_id']}"
        result[key] = str(row["snapshot_dir"])
    return result


def preserve_snapshot_prefix(restore_snapshot: Path, output: Path) -> None:
    """Keep earlier immutable states without aliasing the writable retry anchor."""
    anchor = json.loads((restore_snapshot / "manifest.json").read_text())["iteration"]
    snapshots = output / "snapshots"
    snapshots.mkdir(exist_ok=True)
    for index in range(anchor):
        source = restore_snapshot.parent / f"turn_{index:04d}"
        if not (source / "manifest.json").is_file():
            raise ValueError("Retained prefix is missing a state snapshot")
        destination = snapshots / source.name
        if not destination.exists():
            destination.symlink_to(source.resolve(), target_is_directory=True)


def terminate_tagged_processes(token: str) -> int:
    """Reap every descendant that inherited this attempt's environment tag."""
    marker = f"TOOL_ENV_RUN_TOKEN={token}".encode()
    targets = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            environ = (entry / "environ").read_bytes().split(b"\0")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if marker in environ:
            targets.append(int(entry.name))
    for pid in targets:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    if targets:
        time.sleep(0.5)
    for pid in targets:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return len(targets)


def run_command(
    command: list[str],
    log_path: Path,
    timeout: int,
    run_token: str | None = None,
    extra_env: dict | None = None,
) -> tuple[int, str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        # The tool-use environment executable is an external process. Pass only runtime values
        # it needs instead of inheriting unrelated credentials from the host.
        allowed = {
            "PATH", "HOME", "USER", "LANG", "LC_ALL", "CUDA_VISIBLE_DEVICES",
            "PYTHONPATH", "VIRTUAL_ENV", "HF_HOME", "HF_HUB_CACHE",
            "TRANSFORMERS_CACHE", "TOKENIZERS_PARALLELISM", "NCCL_DEBUG",
            "OPENAI_BASE_URL", "AZURE_ENDPOINT_URL",
        }
        env = {key: value for key, value in os.environ.items() if key in allowed}
        # Verification uses local assets; never forward a host API credential.
        env["OPENAI_API_KEY"] = "EMPTY"
        env.update(extra_env or {})
        if run_token is not None:
            env["TOOL_ENV_RUN_TOKEN"] = run_token
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            start_new_session=True,
        )
        try:
            return process.wait(timeout=timeout), "complete"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            return 124, "timeout"
        finally:
            if run_token is not None:
                terminate_tagged_processes(run_token)


def already_done(run_dir: Path) -> dict | None:
    verify = run_dir / "verify.code.json"
    if not verify.is_file():
        return None
    try:
        return json.loads(verify.read_text(encoding="utf-8"))
    except Exception:
        return None


def worker(job, args, endpoint: str) -> dict:
    scenario, task_id, task, attempt = job
    run_dir = args.output_dir / "runs" / scenario / f"task_{task_id}" / f"attempt_{attempt}"
    result = already_done(run_dir)
    restore_snapshot = None
    agent_rc, state = 0, "cached"
    verify_rc, verify_state = None, "cached" if result is not None else "not_run"
    if result is None:
        run_dir.mkdir(parents=True, exist_ok=True)
        policy = args.transition_policies[f"{scenario}:{task_id}"]
        (run_dir / "transition_policy.json").write_text(json.dumps(policy, sort_keys=True) + "\n")
        run_token = hashlib.sha256(str(run_dir).encode()).hexdigest()
        task_key = f"{scenario}:{task_id}"
        restore_snapshot = args.snapshot_map.get(task_key)
        if args.snapshot_manifest is not None and restore_snapshot is None:
            raise RuntimeError(
                f"missing exact state snapshot for {task_key}; "
                "the paper route does not fall back to prefix replay"
            )
        agent = [
            str(args.tool_env), "agent", "--scenario", scenario, "--task_id", str(task_id),
            "--api_url", endpoint, "--model", args.model,
            "--tasks_path", str(args.source_dir / "gen_tasks.jsonl"),
            "--envs_path", str(args.source_dir / "gen_envs.jsonl"),
            "--db_path", str(args.source_dir / "gen_db.jsonl"),
            "--sample_path", str(args.source_dir / "gen_sample.jsonl"),
            "--max_iterations", str(args.max_iterations),
            "--max_tokens", str(args.max_tokens), "--temperature", str(args.temperature),
            "--verbose", "False", "--output_dir", str(run_dir),
            "--snapshot_dir", str(run_dir / "snapshots"),
        ]
        if restore_snapshot is not None:
            agent.extend(["--restore_snapshot", restore_snapshot])
            # The retained prefix must remain state-auditable after replacing
            # its suffix. Never write through the original anchor snapshot.
            preserve_snapshot_prefix(Path(restore_snapshot), run_dir)
        gate_env = {}
        if args.local_transition_gate:
            spec = next(row for row in jsonl(args.snapshot_manifest)
                        if f"{row['scenario']}:{row['task_id']}" == task_key)
            gate_path = run_dir / "local_gate_input.json"
            gate_path.write_text(json.dumps(spec) + "\n")
            gate_env = {"STEER_LOCAL_GATE": str(gate_path.resolve()),
                        "STEER_LOCAL_GATE_MODULE": str(Path(__file__).resolve().parents[1] / "transition_verifier.py")}
        if args.behavior_logprobs:
            agent.extend(["--behavior_logprobs", "True"])
        # Bind sampling to each attempt even when the external environment
        # derives its original seed only from the shared prompt.
        with bridge_endpoint(endpoint, f"{args.seed}:{scenario}:{task_id}:{attempt}", args.tokenizer) as local_endpoint:
            agent[agent.index("--api_url") + 1] = local_endpoint
            agent_rc, state = run_command(
                agent,
                run_dir / "agent.log",
                args.timeout,
                run_token=run_token,
                extra_env=gate_env,
            )
        if agent_rc == 0 and (run_dir / "trajectory.json").is_file():
            verify = [
                str(args.tool_env), "verify", "--input", str(run_dir), "--mode", "code",
                "--verifier_code_path", str(args.source_dir / "gen_verifier.pure_code.jsonl"),
            ]
            verify_rc, verify_state = run_command(
                verify, run_dir / "verify.log", args.verify_timeout
            )
        result = already_done(run_dir)

    reward_type = result.get("reward_type") if result else None
    execution = (result or {}).get("verify_result", {}).get("execution_status")
    status = "accepted" if reward_type == "complete" and execution == "success" else "rejected"
    if agent_rc != 0 or verify_rc not in (0, None) or result is None:
        raise RuntimeError(f"Tool environment execution failed: {run_dir}; inspect agent.log and verify.log")
    trajectory = json.loads((run_dir / "trajectory.json").read_text())
    assistants = [row for row in trajectory.get("messages", []) if row.get("role") == "assistant"]
    if not assistants or any(not str(row.get("content") or "").strip() and not row.get("tool_calls") for row in assistants):
        raise RuntimeError(f"Tool environment saved an empty assistant response: {run_dir}")
    record = {
        "scenario": scenario, "task_id": task_id, "task": task, "attempt": attempt,
        "endpoint": endpoint, "run_dir": str(run_dir), "status": status,
        "reward_type": reward_type, "execution_status": execution,
        "agent_returncode": agent_rc, "state": state,
        "verify_returncode": verify_rc, "verify_state": verify_state,
        "termination_reason": trajectory.get("termination_reason"),
        "truncated": bool(trajectory.get("truncated", False)),
        "state_restore": (
            "exact_snapshot" if restore_snapshot is not None
            else "snapshot_capture"
        ),
        "restore_snapshot": restore_snapshot,
        "snapshot_dir": str(run_dir / "snapshots"),
    }
    with LOCK:
        with (args.output_dir / "attempts.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        if args.result_events_dir is not None:
            publish_result_event(args.result_events_dir, record)
    print(
        f"TEACHER_VERIFY_SIGNAL scenario={scenario} task={task_id} attempt={attempt} "
        f"status={status} reward={reward_type} endpoint={endpoint}", flush=True,
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-env", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--prompt-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen3-8B")
    parser.add_argument("--tokenizer", type=Path, required=True,
                        help="Tokenizer from the policy runtime; preserves original text tool calls.")
    parser.add_argument("--endpoints", nargs="+", required=True)
    parser.add_argument("--attempts", type=int, default=8)
    parser.add_argument("--workers-per-endpoint", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--max-iterations", type=int, default=30)
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument(
        "--result-events-dir",
        type=Path,
        help=(
            "Atomically publish one JSON event after every verifier result. "
            "This lets a repair consumer start on a rejected trajectory "
            "without waiting for the full rollout budget."
        ),
    )
    parser.add_argument(
        "--verify-timeout",
        type=int,
        default=300,
        help="Independent timeout for deterministic code verification.",
    )
    parser.add_argument(
        "--behavior-logprobs",
        action="store_true",
        help="Record exact sampled token ids/logprobs from local vLLM.",
    )
    parser.add_argument(
        "--snapshot-manifest",
        type=Path,
        help="Task-to-snapshot mapping for exact state restoration.",
    )
    parser.add_argument("--local-transition-gate", action="store_true")
    args = parser.parse_args()
    if args.local_transition_gate and args.snapshot_manifest is None:
        parser.error("--local-transition-gate requires --snapshot-manifest")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.snapshot_map = load_snapshot_manifest(args.snapshot_manifest)

    prompts = []
    for row in jsonl(args.prompt_manifest):
        meta = row["metadata"]
        prompts.append((meta["scenario"], meta["task_id"]))
    if args.max_tasks:
        prompts = prompts[:args.max_tasks]
    scenarios = {scenario for scenario, _ in prompts}
    environment_sources = {row["scenario"]: row["full_code"]
                           for row in jsonl(args.source_dir / "gen_envs.jsonl") if row["scenario"] in scenarios}
    requested = set(prompts)
    args.transition_policies = {}
    for row in jsonl(args.source_dir / "gen_verifier.pure_code.jsonl"):
        key = (row["scenario"], int(row["task_idx"]))
        if key in requested:
            identity = f"{key[0]}:{key[1]}"
            args.transition_policies[identity] = compile_policy(environment_sources[key[0]],
                row["verification"]["code"], identity)
    if len(args.transition_policies) != len(requested):
        raise ValueError("Missing task verifier for transition-policy construction")
    tasks_by_scenario = {row["scenario"]: row["tasks"] for row in jsonl(args.source_dir / "gen_tasks.jsonl")}
    jobs = [
        (scenario, task_id, tasks_by_scenario[scenario][task_id], attempt)
        for attempt in range(args.attempts)
        for scenario, task_id in prompts
        if already_done(
            args.output_dir / "runs" / scenario / f"task_{task_id}" / f"attempt_{attempt}"
        ) is None
    ]
    random.Random(args.seed).shuffle(jobs)
    worker_count = len(args.endpoints) * args.workers_per_endpoint
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [
            pool.submit(worker, job, args, args.endpoints[index % len(args.endpoints)])
            for index, job in enumerate(jobs)
        ]
        accepted = rejected = 0
        for future in concurrent.futures.as_completed(futures):
            if future.result()["status"] == "accepted":
                accepted += 1
            else:
                rejected += 1
    print(f"TEACHER_DATA_SIGNAL accepted={accepted} rejected={rejected}", flush=True)


if __name__ == "__main__":
    main()
