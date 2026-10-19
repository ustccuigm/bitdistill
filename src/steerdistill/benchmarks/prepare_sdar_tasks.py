"""Export real policy contexts from the selected upstream training split."""
import argparse
import json
import os
from pathlib import Path
from steerdistill.benchmarks.sdar_environment import Environment, configure


def json_value(value):
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if hasattr(value, "tolist"):
        return json_value(value.tolist())
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value


def tasks(benchmark, split):
    root = configure()
    if benchmark == "webshop":
        probe = Environment(benchmark, {"task_id": 0})
        count = len(probe.env.server.goals)
        probe.close()
        indices = range(500, count) if split == "train" else range(min(500, count))
        for index in indices:
            yield {"task_id": index, "seed": 42}
    elif benchmark == "alfworld":
        import yaml
        from agent_system.environments.env_package.alfworld.alfworld.agents.environment.alfred_tw_env import AlfredTWEnv
        config = yaml.safe_load((root / "agent_system/environments/env_package/alfworld/configs/config_tw.yaml").read_text())
        config["dataset"]["num_train_games"] = -1
        config["dataset"]["num_eval_games"] = -1
        collection = AlfredTWEnv(config, train_eval="train" if split == "train" else split)
        for index, gamefile in enumerate(sorted(collection.game_files)):
            yield {"task_id": index, "gamefile": gamefile, "seed": 42}
    else:
        import pandas as pd
        source = Path(os.environ["SEARCH_TRAIN_PARQUET" if split == "train" else "SEARCH_EVAL_PARQUET"])
        for index, row in pd.read_parquet(source).iterrows():
            value = row.to_dict()
            extras = value.get("env_kwargs")
            if not isinstance(extras, dict):
                reward = value.get("reward_model") or {}
                extras = {"question": value["question"], "ground_truth": reward.get("ground_truth", value.get("golden_answers")),
                          "data_source": value["data_source"]}
            if extras.get("ground_truth") is None:
                raise ValueError(f"Search row {index} has no verifier answer")
            extras = json_value(extras)
            if split == "train" and str(extras["data_source"]).lower() not in {"nq", "hotpotqa"}:
                raise ValueError(f"Unexpected Search QA training source: {extras['data_source']}")
            yield {**extras, "task_id": int(index), "seed": 42}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, choices=("webshop", "alfworld", "search_qa"))
    parser.add_argument("--split", default="train", choices=("train", "test", "eval_in_distribution", "eval_out_of_distribution"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    resumed_tasks = []
    if temporary.exists():
        with temporary.open() as existing:
            for line in existing:
                row = json.loads(line)
                if row.get("benchmark") != args.benchmark or row.get("split") != args.split or not row.get("prompt"):
                    raise ValueError("Partial task export has a different data contract")
                resumed_tasks.append(row["task"])
    count = 0
    with temporary.open("a") as stream:
        for task in tasks(args.benchmark, args.split):
            if count < len(resumed_tasks):
                if task != resumed_tasks[count]:
                    raise ValueError("Upstream task inputs changed during export; choose a new output")
                count += 1
                continue
            if args.benchmark == "search_qa":
                from agent_system.environments.prompts import SEARCH_TEMPLATE_NO_HIS
                prompt = SEARCH_TEMPLATE_NO_HIS.format(task_description=task["question"])
            else:
                environment = Environment(args.benchmark, task)
                try:
                    prompt = environment.prompt()
                finally:
                    environment.close()
            row = {"prompt": [{"role": "user", "content": prompt}],
                   "task": task, "split": args.split, "benchmark": args.benchmark}
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
            stream.flush()
            if count % 100 == 0:
                print(f"STEER_TASKS_PROGRESS benchmark={args.benchmark} tasks={count}", flush=True)
    if not count:
        raise ValueError("No tasks found in selected upstream split")
    if count < len(resumed_tasks):
        raise ValueError("Upstream split shrank during export")
    temporary.replace(args.output)
    print(f"STEER_TASKS_SIGNAL benchmark={args.benchmark} split={args.split} tasks={count}")


if __name__ == "__main__":
    main()
