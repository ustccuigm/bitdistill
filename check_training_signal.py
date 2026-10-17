"""Require completed optimizer steps and finite loss/gradients before export."""
import argparse
import json
import math
from pathlib import Path


def latest_step(learner):
    checkpoints = [path for path in learner.glob("checkpoint-*")
                   if path.is_dir() and path.name[11:].isdigit()]
    if not checkpoints:
        raise ValueError("No optimizer checkpoint exists")
    path = max(checkpoints, key=lambda p: int(p.name[11:]))
    step = int(path.name[11:])
    if json.loads((path / "trainer_state.json").read_text()).get("global_step") != step:
        raise ValueError("Optimizer checkpoint step mismatch")
    return step


def check(state, expected_steps, previous_step=None):
    if expected_steps < 1 or state.get("global_step") != expected_steps:
        raise ValueError("Training did not complete the requested optimizer steps")
    history = state.get("log_history") or []
    if previous_step is not None:
        if expected_steps != previous_step + 1:
            raise ValueError("Online training must perform exactly one new optimizer update")
        history = [row for row in history if previous_step < row.get("step", -1) <= expected_steps]
        if [row["step"] for row in history if "loss" in row] != [expected_steps]:
            raise ValueError("Missing or repeated new optimizer-step loss")
    losses = [row["loss"] for row in history if "loss" in row]
    gradients = [row["grad_norm"] for row in history if "grad_norm" in row]
    if not losses or not gradients:
        raise ValueError("Training must record both loss and gradient norms")
    if not all(isinstance(value, (int, float)) and math.isfinite(value)
               for value in losses + gradients):
        raise ValueError("Non-finite training loss or gradient norm")
    if not any(value > 0 for value in gradients):
        raise ValueError("All recorded gradient norms are zero")
    return {"status": "passed", "optimizer_steps": expected_steps,
            "global_step": expected_steps, "previous_step": previous_step,
            "loss_records": len(losses), "gradient_records": len(gradients),
            "first_loss": losses[0], "last_loss": losses[-1],
            "min_grad_norm": min(gradients), "max_grad_norm": max(gradients)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest-step", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--previous-step", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.latest_step:
        print(latest_step(args.latest_step))
        return
    if not all((args.state, args.steps, args.output)):
        parser.error("--state, --steps and --output are required together")
    result = check(json.loads(args.state.read_text()), args.steps, args.previous_step)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("STEER_TRAINING_SIGNAL " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
