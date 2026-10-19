"""Official tau2 base splits, four independent trials per task."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
from steerdistill.benchmarks.runtime import Runtime
from steerdistill.teacher.response_bridge import bridge_endpoint
from steerdistill.quantization.clip_provenance import model_identity


def selected_tasks(selected, load_tasks):
    result = {}
    for domain in ("airline", "retail", "telecom"):
        available = {task.id for task in load_tasks(domain, "base")}
        if not available:
            raise ValueError(f"Empty tau2 base split: {domain}")
        if selected is None:
            result[domain] = sorted(available)
            continue
        ids = selected[domain]
        if (not isinstance(ids, list) or not ids
                or not all(isinstance(value, str) for value in ids)
                or len(set(ids)) != len(ids) or not set(ids) <= available):
            raise ValueError(f"Invalid or unknown task IDs for {domain}")
        result[domain] = sorted(ids)
    return result


def bind_output(output, manifest):
    path = output / "manifest.json"
    if path.exists():
        if json.loads(path.read_text()) != manifest:
            raise ValueError("Evaluation inputs changed; use a new output directory")
    elif any((output / (domain + ".json")).exists() for domain in ("airline", "retail", "telecom")):
        raise ValueError("Existing tau2 results have no input manifest; use a new output directory")
    output.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpus", default="0")
    parser.add_argument("--task-ids", type=Path, help="JSON object mapping all three domains to selected task IDs")
    args = parser.parse_args()
    selected = json.loads(args.task_ids.read_text()) if args.task_ids else None
    if selected is not None and (not isinstance(selected, dict) or set(selected) != {"airline", "retail", "telecom"}):
        raise ValueError("Task selection must specify airline, retail and telecom")
    from tau2.run import run_domain, load_tasks
    from tau2.data_model.simulation import RunConfig
    tasks_by_domain = selected_tasks(selected, load_tasks)
    user_model = os.getenv("TAU2_USER_MODEL")
    user_args = json.loads(os.getenv("TAU2_USER_ARGS", '{"temperature": 0.0}'))
    if any("key" in key.lower() for key in user_args):
        raise ValueError("Pass user simulator credentials through environment variables, not saved model arguments")
    local_user = os.getenv("TAU2_USER_MODEL_PATH")
    if not user_model and not local_user:
        raise ValueError("Set TAU2_USER_MODEL or TAU2_USER_MODEL_PATH for the benchmark user simulator")
    port = int(os.getenv("EVAL_PORT", "34400"))
    args.output.mkdir(parents=True, exist_ok=True)
    bind_output(args.output, {
        "runtime": model_identity(args.runtime), "model": args.model,
        "tasks": tasks_by_domain, "trials": 4,
        "scope": "subset" if selected is not None else "full",
        "seed": int(os.getenv("EVAL_SEED", "300")),
        "max_tokens": int(os.getenv("EVAL_MAX_TOKENS", "32768")),
        "user_model": user_model, "user_args": user_args,
        "local_user": model_identity(local_user) if local_user else None,
    })
    reports = {}
    with ExitStack() as stack:
        student = stack.enter_context(Runtime(args.runtime, args.model, args.gpus, port,
            args.output / "runtime.log", quantized=True, tool_calls=True))
        student_url = stack.enter_context(bridge_endpoint(student.url))
        if local_user:
            user = stack.enter_context(Runtime(local_user, "benchmark-user", os.environ["TAU2_USER_GPU"],
                port + 1, args.output / "user-runtime.log", tool_calls=True))
            user_model = "openai/benchmark-user"
            user_args.update(api_base=stack.enter_context(bridge_endpoint(user.url)), api_key="EMPTY")
            user_args.setdefault("max_tokens", int(os.getenv("EVAL_MAX_TOKENS", "32768")))
        for domain in ("airline", "retail", "telecom"):
            task_ids = tasks_by_domain[domain]
            expected_ids = set(task_ids)
            result = run_domain(RunConfig(
                domain=domain, task_split_name="base", task_ids=task_ids, num_trials=4,
                llm_agent="openai/" + args.model,
                llm_args_agent={"api_base": student_url, "api_key": "EMPTY", "temperature": 0.0,
                                "max_tokens": int(os.getenv("EVAL_MAX_TOKENS", "32768"))},
                llm_user=user_model, llm_args_user=user_args,
                seed=int(os.getenv("EVAL_SEED", "300")),
                max_concurrency=int(os.getenv("EVAL_WORKERS", "4")),
                save_to=str((args.output / domain).resolve()),
            ))
            pairs = [(simulation.task_id, simulation.trial) for simulation in result.simulations]
            expected = {(identity, trial) for identity in expected_ids for trial in range(4)}
            if len(pairs) != len(expected) or set(pairs) != expected:
                raise ValueError(f"Incomplete tau2 {domain}: {len(pairs)} results for {len(expected)} task/trial pairs")
            failed = [simulation for simulation in result.simulations
                      if not simulation.messages or simulation.reward_info is None
                      or simulation.termination_reason.value in {"agent_error", "user_error"}]
            if failed:
                raise RuntimeError(f"tau2 {domain} has {len(failed)} runtime errors; inspect saved trajectories")
            successes = sum(simulation.reward_info.reward == 1. for simulation in result.simulations)
            reports[domain] = {"tasks": len(expected_ids), "trials": 4, "successes": successes,
                               "pass_at_1": 100 * successes / len(expected)}
    report = {"status": "complete", "benchmark": "tau2_bench", "domains": reports,
              "scope": "subset" if selected is not None else "full",
              "user_simulator": {"model": user_model, "local": bool(local_user)},
              "pass_at_1": 100 * sum(row["successes"] for row in reports.values())
                           / sum(row["tasks"] * row["trials"] for row in reports.values())}
    (args.output / "scores.json").write_text(json.dumps(report, indent=2) + "\n")
    print("STEER_EVAL_SIGNAL " + json.dumps(report))


if __name__ == "__main__":
    main()
