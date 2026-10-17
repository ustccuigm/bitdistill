"""Select only a completed and checksum-verified online runtime for evaluation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_online import model_digest


def resolve(root, step):
    if step == "latest":
        state = json.loads((root / "latest.json").read_text())
        number = state["rollout_step"]
    else:
        number = int(step)
        if number < 1:
            raise ValueError("Evaluation step must be positive")
        state = json.loads((root / "steps" / f"step{number:06d}" / "complete.json").read_text())
    complete = json.loads((root / "steps" / f"step{number:06d}" / "complete.json").read_text())
    if state != complete or state["optimizer_step"] != state["previous_optimizer_step"] + 1:
        raise ValueError("Evaluation requires a committed online step")
    runtime = Path(state["output_runtime"])
    if not (runtime / "quant_config.json").is_file() or model_digest(runtime) != state["runtime_sha256"]:
        raise ValueError("Evaluation runtime does not match the completed step")
    return str(runtime), f"step{number:06d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--step", default="latest")
    args = parser.parse_args()
    print("\n".join(resolve(args.root, args.step)))
