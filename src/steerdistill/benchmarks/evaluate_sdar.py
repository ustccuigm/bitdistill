"""Full native benchmark evaluation, using upstream task splits and rewards."""
import argparse
from collections import defaultdict
from contextlib import ExitStack
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys

from steerdistill.benchmarks.native_inference import environment_action, sample_action
from steerdistill.benchmarks.online_rollout import generate
from steerdistill.benchmarks.prepare_sdar_tasks import tasks
from steerdistill.benchmarks.runtime import Runtime
from steerdistill.benchmarks.sdar_environment import EvaluationEnvironment as Environment, state_hash

from steerdistill.quantization.clip_provenance import model_identity
from steerdistill.generation_budget import ContextWindowExceeded
from steerdistill.generation_evidence import INCOMPLETE_FINISH_REASONS


_SEARCH_BLOCK = re.compile(r"<(search|answer)>\s*.+?\s*</\1>", re.IGNORECASE | re.DOTALL)


def search_action_input(response):
    """Prepare a single SearchQA turn for the native environment."""
    _, closed, body = response.rpartition("</think>")
    if not closed and "<think>" in body:
        return "Invalid action"
    first = _SEARCH_BLOCK.search(body)
    if first is None:
        return "Invalid action"
    # Later blocks were generated before the environment returned its observation.
    if _SEARCH_BLOCK.search(body, first.end()):
        return body[:first.end()]
    return body


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
    native = getattr(args, "native_text", False)
    try:
        while not env.done:
            prompt = [{"role": "user", "content": env.prompt()}]
            try:
                if native:
                    response, metadata = sample_action(args.urls[identity % len(args.urls)], args.model, prompt,
                        args.seed + identity * 10000 + env.turn, args.temperature)
                else:
                    response, metadata = generate(args.url, args.model, prompt,
                        args.seed + identity * 1009 + env.turn, training=False)
            except ContextWindowExceeded as error:
                termination = {"reason": "context_length", "error": error.as_error()}
                break
            if metadata.get("finish_reason") in INCOMPLETE_FINISH_REASONS and not (
                    native and metadata.get("finish_reason") == "length"):
                termination = {"reason": "incomplete_generation", "response": response, "generation": metadata}
                break
            action_input = search_action_input(response) if args.benchmark == "search_qa" else response
            if native and args.benchmark != "search_qa":
                action_input = environment_action(args.benchmark, response)
            transition = env.step(action_input)
            trajectory.append({"prompt": prompt, "response": response, "generation": metadata,
                               "transition": transition})
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


def validate_split(benchmark, all_tasks):
    if not all_tasks:
        raise ValueError("Evaluation split is empty")
    if len({int(task["task_id"]) for task in all_tasks}) != len(all_tasks):
        raise ValueError("Duplicate evaluation task IDs would share a result file")
    if benchmark == "webshop" and len(all_tasks) != 500:
        raise ValueError("WebShop full evaluation requires all 500 held-out tasks")
    if benchmark == "search_qa":
        expected = {"nq", "triviaqa", "popqa", "hotpotqa", "2wikimultihopqa", "musique", "bamboogle"}
        actual = {task["data_source"].strip().lower() for task in all_tasks}
        if actual != expected:
            raise ValueError(f"Search QA requires seven datasets: found {actual}")


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
    parser.add_argument("--split", choices=("test", "eval_in_distribution", "eval_out_of_distribution"))
    args = parser.parse_args()
    args.native_text = json.loads((args.runtime / "config.json").read_text())["model_type"] == "qwen3"
    args.temperature = 0.0 if args.benchmark == "search_qa" else 0.4
    os.environ["STEER_BENCHMARK"] = args.benchmark
    split = "eval_out_of_distribution" if args.benchmark == "alfworld" else "test"
    split = args.split or split
    if (args.benchmark == "alfworld") == (split == "test"):
        parser.error(f"Unsupported split {split} for {args.benchmark}")
    all_tasks = list(tasks(args.benchmark, split))
    validate_split(args.benchmark, all_tasks)
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
    manifest = {"generation_contract_version": 2, "benchmark": args.benchmark, "split": split, "seed": args.seed,
                "runtime": model_identity(args.runtime), "tasks_hash": state_hash(all_tasks),
                "tasks": len(all_tasks), "temperature": os.getenv("ROLLOUT_TEMPERATURE", "0.7"),
                "context_window": os.getenv("MODEL_MAX_LENGTH", "32768"),
                "max_tokens": os.getenv("MAX_TOKENS", "32768"),
                "action_max_tokens": os.getenv("ACTION_MAX_TOKENS", "4096"),
                "action_stop": "</action>" if args.benchmark in {"webshop", "alfworld"} else None}
    if args.benchmark == "search_qa":
        manifest["action_policy"] = "first-complete-action-on-multiple-blocks"
    if args.benchmark in {"webshop", "alfworld"}:
        manifest["history_policy"] = "two-executed-actions"
    if args.native_text:
        manifest.update(generation_contract_version=3, thinking=True, temperature=args.temperature,
                        context_window=min(16384, int(os.getenv("MODEL_MAX_LENGTH", "32768"))),
                        max_tokens=8192, top_p=1.0, seed_stride=10000, action_stop=None)
        manifest.pop("action_max_tokens")
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("Evaluation inputs changed; use a new output directory")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    scores = defaultdict(lambda: {"tasks": 0, "successes": 0, "reward_sum": 0.})
    with ExitStack() as servers:
        gpu_groups = args.gpus.split(",") if args.native_text else [args.gpus]
        port = int(os.getenv("EVAL_PORT", "34400"))
        args.urls = []
        for index, group in enumerate(gpu_groups):
            log = "runtime.log" if len(gpu_groups) == 1 else f"runtime-{index}.log"
            runtime = servers.enter_context(Runtime(args.runtime, args.model, group, port + index,
                                                     args.output / log, quantized=True))
            args.urls.append(runtime.url)
        args.url = args.urls[0]
        with multiprocessing.get_context("spawn").Pool(args.workers) as pool:
            for count, (source, success, score) in enumerate(pool.imap_unordered(
                    evaluate_task, ((args, task) for task in all_tasks), chunksize=1), 1):
                dataset = source.strip().lower() if args.benchmark == "search_qa" else source
                group = scores[dataset]
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
    if args.benchmark == "search_qa":
        report["micro_em"] = 100 * sum(g["successes"] for g in scores.values()) / len(all_tasks)
    report["split"] = split
    (args.output / "scores.json").write_text(json.dumps(report, indent=2) + "\n")
    print("STEER_EVAL_SIGNAL " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
