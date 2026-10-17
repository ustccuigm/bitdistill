"""Full native benchmark evaluation, using upstream task splits and rewards."""
import argparse
from collections import defaultdict
import json
import multiprocessing
import os
from pathlib import Path
import sys

from online_rollout import generate
from prepare_sdar_tasks import tasks
from runtime import Runtime
from sdar_environment import Environment, state_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quantization.clip_provenance import model_identity
from generation_budget import ContextWindowExceeded


def evaluate_task(item):
    args, task = item
    identity = int(task["task_id"])
    output = args.output / "tasks" / f"{identity}.json"
    if output.exists():
        result = json.loads(output.read_text())
        if result.get("task_hash") != state_hash(task):
            raise ValueError(f"Evaluation task changed: {output}")
        return result["data_source"], result["success"], result["score"]
    env = Environment(args.benchmark, task)
    trajectory = []
    termination = None
    try:
        while not env.done:
            prompt = [{"role": "user", "content": env.prompt()}]
            try:
                response, metadata = generate(args.url, args.model, prompt, args.seed + identity * 1009 + env.turn)
            except ContextWindowExceeded as error:
                termination = {"reason": "context_length", "error": error.as_error()}
                break
            transition = env.step(response)
            trajectory.append({"prompt": prompt, "response": response, "generation": metadata,
                               "transition": transition})
            if metadata.get("finish_reason") == "length":
                termination = {"reason": "generation_length"}
                break
        result = {"task": task, "task_hash": state_hash(task), "data_source": task.get("data_source", args.benchmark),
                  "success": env.success, "score": float(env.score), "trajectory": trajectory,
                  "termination": termination}
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False) + "\n")
        temporary.replace(output)
        return result["data_source"], result["success"], result["score"]
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", choices=("webshop", "alfworld", "search_qa"), required=True)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--gpus", default="0")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--task-ids", type=Path, help="JSON list of task IDs; omitted means the full split")
    args = parser.parse_args()
    os.environ["STEER_BENCHMARK"] = args.benchmark
    split = "eval_out_of_distribution" if args.benchmark == "alfworld" else "test"
    all_tasks = list(tasks(args.benchmark, split))
    if not all_tasks:
        raise ValueError("Evaluation split is empty")
    if args.benchmark == "webshop" and len(all_tasks) != 500:
        raise ValueError("WebShop full evaluation requires all 500 held-out tasks")
    if args.benchmark == "search_qa":
        expected = {"nq", "triviaqa", "popqa", "hotpotqa", "2wikimultihopqa", "musique", "bamboogle"}
        actual = {task["data_source"].lower() for task in all_tasks}
        if actual != expected:
            raise ValueError(f"Search QA requires seven datasets: found {actual}")
    full_task_count = len(all_tasks)
    if args.task_ids:
        selected = json.loads(args.task_ids.read_text())
        if not isinstance(selected, list) or not selected or len({str(x) for x in selected}) != len(selected):
            raise ValueError("Task selection must be a nonempty JSON list of unique IDs")
        selected = {str(x) for x in selected}
        all_tasks = [task for task in all_tasks if str(task["task_id"]) in selected]
        if {str(task["task_id"]) for task in all_tasks} != selected:
            raise ValueError("Task selection contains IDs outside the evaluation split")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"benchmark": args.benchmark, "split": split, "seed": args.seed,
                "runtime": model_identity(args.runtime), "tasks_hash": state_hash(all_tasks),
                "tasks": len(all_tasks), "temperature": os.getenv("ROLLOUT_TEMPERATURE", "0.7"),
                "context_window": os.getenv("MODEL_MAX_LENGTH", "32768"),
                "max_tokens": os.getenv("MAX_TOKENS", "32768"),
                "action_max_tokens": os.getenv("ACTION_MAX_TOKENS", "4096"),
                "action_stop": "</action>" if args.benchmark in {"webshop", "alfworld"} else None}
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("Evaluation inputs changed; use a new output directory")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    scores = defaultdict(lambda: {"tasks": 0, "successes": 0, "reward_sum": 0.})
    with Runtime(args.runtime, args.model, args.gpus, int(os.getenv("EVAL_PORT", "34400")),
                 args.output / "runtime.log", quantized=True) as runtime:
        args.url = runtime.url
        with multiprocessing.get_context("spawn").Pool(args.workers) as pool:
            for count, (source, success, score) in enumerate(pool.imap_unordered(
                    evaluate_task, ((args, task) for task in all_tasks), chunksize=1), 1):
                group = scores[source]
                group["tasks"] += 1
                group["successes"] += int(success)
                group["reward_sum"] += score
                if count % 100 == 0 or count == len(all_tasks):
                    print(f"STEER_EVAL_PROGRESS benchmark={args.benchmark} completed={count} expected={len(all_tasks)}", flush=True)
    for group in scores.values():
        group["score"] = 100 * group["successes"] / group["tasks"]
    report = {"status": "complete", "benchmark": args.benchmark, "tasks": len(all_tasks),
              "scope": "subset" if args.task_ids else "full", "full_split_tasks": full_task_count,
              "metric": "EM" if args.benchmark == "search_qa" else "SR", "datasets": dict(scores),
              "score": sum(group["score"] for group in scores.values()) / len(scores)}
    (args.output / "scores.json").write_text(json.dumps(report, indent=2) + "\n")
    print("STEER_EVAL_SIGNAL " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
