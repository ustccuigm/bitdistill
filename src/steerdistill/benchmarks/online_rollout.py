"""Online revision for the native WebShop, ALFWorld, and Search QA environments."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import urllib.request

REPOSITORY_ROOT = Path(os.environ.get("STEERDISTILL_ROOT", Path(__file__).resolve().parents[3])).resolve()
from steerdistill.analysis import AnalysisRejected, grounded_analysis, normalize_steer
from steerdistill.common import canonical_decision, causal_action_delta, inject_skill, stable_id, write_jsonl
from steerdistill.materialize import rows_from_run
from steerdistill.store import SkillStore
from steerdistill.benchmarks.sdar_environment import Environment, state_hash
from steerdistill.quantization.clip_provenance import model_identity
from steerdistill.generation_budget import ContextWindowExceeded, apply_budget


def generate(url, model, messages, seed):
    payload = {"model": model, "messages": messages, "temperature": float(os.getenv("ROLLOUT_TEMPERATURE", "0.7")),
               "max_tokens": int(os.getenv("MAX_TOKENS", "32768")), "seed": seed}
    benchmark = os.getenv("STEER_BENCHMARK") or os.getenv("BENCHMARK")
    if benchmark in {"webshop", "alfworld"}:
        payload["max_tokens"] = min(payload["max_tokens"], int(os.getenv("ACTION_MAX_TOKENS", "4096")))
        # These environments consume one closed action, not an unbounded suffix.
        payload.update(stop=["</action>"], include_stop_str_in_output=True)
    apply_budget(url, payload)
    request = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer EMPTY"})
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.load(response)
    choice = result["choices"][0]
    message = choice["message"]
    text = message.get("content") or ""
    reasoning = message.get("reasoning_content") or message.get("reasoning")
    if reasoning and "<think>" not in text:
        text = f"<think>{reasoning}</think>{text}"
    if not text.strip():
        raise ValueError("Runtime generated an empty assistant response")
    return text, {"finish_reason": choice.get("finish_reason"), "usage": result.get("usage", {}), "seed": seed,
                  "max_tokens": payload["max_tokens"], "stop": payload.get("stop", [])}


def write_run(directory, trajectory, success):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "trajectory.json").write_text(json.dumps(trajectory, indent=2) + "\n")
    (directory / "verify.code.json").write_text(json.dumps({
        "reward_type": "complete" if success else "incomplete",
        "verify_result": {"execution_status": "success" if success else "failed"},
    }) + "\n")
    return {"run_dir": str(directory), "trajectory": trajectory, "success": success}


def rollout(environment, directory, url, model, seed, prefix=None, steer=None, first_response=None):
    trajectory = copy.deepcopy(prefix) if prefix else {
        "scenario": environment.benchmark, "task_id": environment.task["task_id"], "messages": [], "transitions": []}
    if prefix is None:
        trajectory["messages"].append({"role": "user", "content": environment.prompt()})
    snapshots = []
    while not environment.done:
        turn = len(trajectory["transitions"])
        snapshots.append(environment.save_snapshot(directory / "snapshots" / f"turn{turn:04d}.pkl"))
        environment.restore(snapshots[-1])
        prompt = [{"role": "user", "content": environment.prompt()}]
        conditioned = inject_skill(prompt, steer) if steer else prompt
        if first_response is not None:
            text, metadata = first_response
            first_response = None
        else:
            try:
                text, metadata = generate(url, model, conditioned, seed + turn)
            except ContextWindowExceeded as error:
                trajectory["termination_reason"] = "context_length"
                trajectory["context_boundary"] = error.as_error()
                snapshots.pop()
                break
        trajectory["messages"].append({"role": "assistant", "content": text, "model_prompt": prompt,
                                        "generation": metadata})
        transition = environment.step(text)
        transition["before_state_hash"] = snapshots[-1].get("transition_hash", snapshots[-1]["semantic_hash"])
        transition["before_alignment_state_hash"] = snapshots[-1]["alignment_hash"]
        transition["prompt_hash"] = state_hash(prompt)
        trajectory["transitions"].append(transition)
        trajectory["messages"].append({"role": "user", "content": transition["observation"]})
        steer = None
        if metadata.get("finish_reason") == "length":
            trajectory["termination_reason"] = "generation_length"
            break
    run = write_run(directory, trajectory, environment.success)
    run["snapshots"] = snapshots
    return run


def divergence(candidate, reference):
    left, right = candidate["transitions"], reference["transitions"]
    for row in (*left, *right):
        if not row.get("alignment_state_hash") or not row.get("before_alignment_state_hash"):
            raise ValueError("State-only localization requires explicit alignment state hashes")
    def after(row):
        return row["alignment_state_hash"]
    def before(row):
        return row["before_alignment_state_hash"]
    i = j = 0
    while i < len(left) and j < len(right):
        if after(left[i]) == after(right[j]) and before(left[i]) == before(right[j]):
            i += 1
            j += 1
        elif after(left[i]) == before(left[i]):
            # A state-preserving failed/irrelevant action is the causal turn;
            # it must not be skipped simply because its effect is empty.
            return i, j
        elif after(right[j]) == before(right[j]):
            j += 1
        else:
            return i, j
    return (i, j) if i < len(left) and j < len(right) else None


def prefix_at(trajectory, turn):
    prefix = copy.deepcopy(trajectory)
    prefix.pop("termination_reason", None)
    prefix.pop("context_boundary", None)
    count = 0
    for index, message in enumerate(prefix["messages"]):
        if message["role"] == "assistant":
            if count == turn:
                prefix["messages"] = prefix["messages"][:index]
                break
            count += 1
    prefix["transitions"] = prefix["transitions"][:turn]
    return prefix


def revise(environment, initial, plain, directory, args, seed):
    references = []
    for attempt in range(args.reference_attempts):
        environment.restore(initial)
        reference = rollout(environment, directory / "teacher" / str(attempt), args.teacher_url, args.model, seed + 10000 * (attempt + 1))
        references.append(reference)
        if reference["success"]:
            break
    if not references[-1]["success"]:
        return plain, {}, {}, None, {"reference_found": False, "attempted": 0,
            "reference_runs": [run["run_dir"] for run in references], "fallback": "no_successful_reference"}
    reference = references[-1]
    retained = plain
    accepted_steers, accepted_steps = {}, {}
    memory, previous, attempted = "", None, 0
    identity = stable_id("steer", str(directory))
    fallback = None
    revision = 0
    while not retained["success"]:
        position = divergence(retained["trajectory"], reference["trajectory"])
        if position is None:
            fallback = "no_alignable_divergence"
            break
        turn, reference_turn = position
        revision += 1
        prefix = prefix_at(retained["trajectory"], turn)
        before = retained["snapshots"][turn]
        failed_message = [m for m in retained["trajectory"]["messages"] if m["role"] == "assistant"][turn]
        reference_message = [m for m in reference["trajectory"]["messages"] if m["role"] == "assistant"][reference_turn]
        delta = causal_action_delta(canonical_decision(failed_message), canonical_decision(reference_message))
        feedback = []
        accepted = None
        active_memory, active_previous = memory, previous
        for attempt in range(args.retries):
            environment.restore(before)
            prompt = [{"role": "user", "content": environment.prompt()}]
            payload = {"task": environment.description, "current_context": prompt,
                       "failed_decision": failed_message,
                       "failed_transition": retained["trajectory"]["transitions"][turn],
                       "reference_decision": reference_message,
                       "reference_transition": reference["trajectory"]["transitions"][reference_turn],
                       "reference_verified_success": True,
                       "declared_first_divergence": {"assistant_turn": turn},
                       "action_delta": delta, "failure_type": delta["failure_type"],
                       "same_recovery_lineage": bool(accepted_steps), "previous_steer": active_memory,
                       "verifier_feedback": feedback}
            attempted += 1
            trial = directory / "repairs" / f"revision{revision:04d}" / f"turn{turn:04d}" / f"attempt{attempt:02d}"
            trial.mkdir(parents=True, exist_ok=True)
            try:
                analysis = grounded_analysis(args.teacher_url, "EMPTY", args.model, payload,
                                             active_previous, same_lineage=bool(accepted_steps))
                _, instruction = normalize_steer(analysis["steer"])
                response = generate(args.student_url, args.model, inject_skill(prompt, instruction), seed + attempted + 500000)
            except AnalysisRejected as error:
                failure = {"accepted": False, "termination_reason": "analysis_rejected",
                           "violations": error.violations, "analysis": error.analysis}
                (trial / "steering.json").write_text(json.dumps(failure, indent=2) + "\n")
                feedback.append(failure)
                continue
            except ContextWindowExceeded as error:
                failure = {"accepted": False, "termination_reason": "context_length", "error": error.as_error()}
                (trial / "steering.json").write_text(json.dumps(failure, indent=2) + "\n")
                feedback.append(failure)
                continue
            transition = environment.step(response[0])
            target = reference["trajectory"]["transitions"][reference_turn]
            local_ok = transition["valid"] and (transition["state_hash"] == target["state_hash"]
                                                or transition["success"] and target["success"])
            (trial / "steering.json").write_text(json.dumps({"analysis": analysis, "raw_steering_prompt": instruction,
                "response": response[0], "transition": transition, "accepted": local_ok}, indent=2) + "\n")
            if not local_ok:
                feedback.append({"steer": instruction, "response": response[0], "transition": transition, "expected": target})
                continue
            # Continue from the exact verified transition, without replaying its action.
            transition["before_state_hash"] = before.get("transition_hash", before["semantic_hash"])
            transition["before_alignment_state_hash"] = before["alignment_hash"]
            transition["prompt_hash"] = state_hash(prompt)
            prefix["messages"].append({"role": "assistant", "content": response[0],
                                       "model_prompt": prompt, "generation": response[1]})
            prefix["transitions"].append(transition)
            prefix["messages"].append({"role": "user", "content": transition["observation"]})
            if response[1].get("finish_reason") == "length":
                prefix["termination_reason"] = "generation_length"
                accepted = write_run(trial / "accepted", prefix, environment.success)
                accepted["snapshots"] = []
            else:
                accepted = rollout(environment, trial / "accepted", args.student_url, args.model, seed,
                                   prefix=prefix)
            accepted["snapshots"] = retained["snapshots"][:turn + 1] + accepted["snapshots"]
            accepted_steers = {t: value for t, value in accepted_steers.items() if t < turn}
            accepted_steps = {t: value for t, value in accepted_steps.items() if t < turn}
            accepted_steers[turn] = instruction
            step = {"index": len(accepted_steps) + 1, "step_id": stable_id("step", str(trial)),
                    "assistant_turn": turn, "status": "locally_verified", "integrated_steer": instruction,
                    "steer": instruction, "expected_decision": canonical_decision({"content": response[0]}),
                    "causal_signature": delta["signature"], "failure_mechanism": analysis["failure_mechanism"],
                    "relation_to_prior": analysis["relation_to_prior"], "verification_run_dir": accepted["run_dir"],
                    "verification_kind": "verified_terminal_success" if transition["success"] else "verified_action_transition"}
            accepted_steps[turn] = step
            memory = instruction
            previous = {"status": "locally_verified", "steer_steps": list(accepted_steps.values())}
            break
        if accepted is None:
            fallback = "steering_exhausted"
            break
        retained = accepted
    if not accepted_steps:
        return plain, {}, {}, None, {"reference_found": True, "attempted": attempted,
            "reference_runs": [run["run_dir"] for run in references], "fallback": fallback}
    record = {"skill_id": identity, "task_key": f"{args.benchmark}:{environment.task['task_id']}",
              "version": 1, "step": args.step, "status": "verified" if retained["success"] else "locally_verified",
              "skill": memory, "analysis_schema": "causal-steer-v2", "steer_steps": list(accepted_steps.values())}
    SkillStore(args.store).append(record)
    return retained, accepted_steers, accepted_steps, record, {"reference_found": True, "attempted": attempted,
        "reference_runs": [run["run_dir"] for run in references], "fallback": fallback}


def task_items(path):
    seen = set()
    with path.open() as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            identity = int(row["task"]["task_id"])
            if identity in seen:
                raise ValueError(f"Duplicate task ID: {identity}")
            seen.add(identity)
            if row["split"] != "train":
                raise ValueError("Online quantization must use training tasks")
            yield row


def run_task(item):
    args, task_record = item
    identity = int(task_record["task"]["task_id"])
    environment = None
    counts = {"tasks": 1, "trajectories": 0, "reference_found": 0, "attempted": 0}
    try:
        for attempt in range(args.attempts):
            directory = args.output / "tasks" / str(identity) / str(attempt)
            completed = directory / "completed.json"
            if completed.is_file():
                saved = json.loads(completed.read_text())
                shard = directory / "training_rows.jsonl"
                if hashlib.sha256(shard.read_bytes()).hexdigest() != saved["rows_sha256"]:
                    raise ValueError(f"Corrupt resumed training shard: {shard}")
                counts["trajectories"] += 1
                for key in ("reference_found", "attempted"):
                    counts[key] += saved[key]
                continue
            if environment is None:
                environment = Environment(args.benchmark, task_record["task"])
                initial = environment.snapshot()
            seed = int(os.getenv("SEED", "42")) + args.step * 1000000 + identity * 1009 + attempt * 101
            environment.restore(initial)
            plain = rollout(environment, directory / "plain", args.student_url, args.model, seed)
            summary = {"reference_found": False, "attempted": 0, "reference_runs": [], "fallback": "already_successful"}
            if plain["success"]:
                retained, steers, steps, record = plain, {}, {}, None
            else:
                retained, steers, steps, record, summary = revise(environment, initial, plain, directory, args, seed)
            modes = {turn: "skill_recovery" for turn in steps}
            task_rows = rows_from_run(retained, "revised", record, steers, modes, steps)
            if not task_rows:
                raise ValueError(f"Task {identity} produced no real assistant turns")
            for row in task_rows:
                turn = row["assistant_turn"]
                transition = retained["trajectory"]["transitions"][turn]
                row.update(benchmark=args.benchmark, step=args.step, verifier={"success": retained["success"]},
                    revision_receipt=str(completed),
                    restore_verified=True, state_snapshot={"snapshot_id": stable_id("snapshot", str(directory) + f":{turn}"),
                        "prefix_hash": transition["prompt_hash"], "before_state_hash": transition["before_state_hash"],
                        "after_state_hash": transition["state_hash"]})
            shard = directory / "training_rows.jsonl"
            temporary = shard.with_suffix(".tmp")
            write_jsonl(temporary, task_rows)
            temporary.replace(shard)
            receipt = {**summary, "rows": len(task_rows), "plain_run": plain["run_dir"],
                       "retained_run": retained["run_dir"], "accepted_interventions": len(steps),
                       "reference_attempts": args.reference_attempts, "steering_retries": args.retries,
                       "rows_sha256": hashlib.sha256(shard.read_bytes()).hexdigest()}
            temporary = completed.with_suffix(".tmp")
            temporary.write_text(json.dumps(receipt) + "\n")
            temporary.replace(completed)
            counts["trajectories"] += 1
            for key in ("reference_found", "attempted"):
                counts[key] += int(summary[key])
    finally:
        if environment is not None:
            environment.close()
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--student-url", required=True)
    parser.add_argument("--teacher-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--reference-attempts", type=int, default=4)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    os.environ["STEER_BENCHMARK"] = args.benchmark
    if min(args.attempts, args.reference_attempts, args.retries, args.workers) < 1:
        raise ValueError("Attempts and workers must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    settings = {key: str(value) for key, value in vars(args).items() if key != "workers"}
    settings["tasks_sha256"] = hashlib.sha256(args.tasks.read_bytes()).hexdigest()
    settings["temperature"] = os.getenv("ROLLOUT_TEMPERATURE", "0.7")
    settings["max_tokens"] = os.getenv("MAX_TOKENS", "32768")
    settings["action_max_tokens"] = os.getenv("ACTION_MAX_TOKENS", "4096")
    settings["seed"] = os.getenv("SEED", "42")
    source_files = (
        "src/steerdistill/benchmarks/online_rollout.py",
        "src/steerdistill/benchmarks/sdar_environment.py",
        "src/steerdistill/analysis.py",
    )
    settings["method_sources"] = {
        name: hashlib.sha256((REPOSITORY_ROOT / name).read_bytes()).hexdigest()
        for name in source_files
    }
    settings["student_weights"] = model_identity(os.environ["STEER_RUNTIME_PATH"])
    settings["teacher_weights"] = model_identity(os.environ["STEER_TEACHER_MODEL"])
    run_config = args.output / "online_config.json"
    if run_config.exists() and json.loads(run_config.read_text()) != settings:
        raise ValueError("Online run inputs changed; use a new output directory")
    run_config.write_text(json.dumps(settings, indent=2) + "\n")
    counts = {"tasks": 0, "trajectories": 0, "reference_found": 0, "attempted": 0}
    with multiprocessing.get_context("spawn").Pool(args.workers) as pool:
        for result in pool.imap_unordered(run_task, ((args, task) for task in task_items(args.tasks)), chunksize=1):
            for key in counts:
                counts[key] += result[key]
            print("STEER_ONLINE_SIGNAL " + json.dumps(counts), flush=True)
    destination = args.output / "train/steer_opd.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    with temporary.open("w") as stream:
        for task in task_items(args.tasks):
            for attempt in range(args.attempts):
                shard = args.output / "tasks" / str(int(task["task"]["task_id"])) / str(attempt) / "training_rows.jsonl"
                with shard.open() as source:
                    shutil.copyfileobj(source, stream)
    temporary.replace(destination)
    (args.output / "train/revision_manifest.json").write_text(json.dumps(counts, indent=2) + "\n")


if __name__ == "__main__":
    main()
