"""Verify actual Adam update counters without loading full optimizer moments."""
import argparse
import json
from pathlib import Path

import torch
from torch.distributed.checkpoint import FileSystemReader, load


def check(checkpoint, expected_step):
    reader = FileSystemReader(checkpoint / "optimizer_0")
    metadata = reader.read_metadata()
    keys = [key for key in metadata.state_dict_metadata if key.endswith(".step")]
    if not keys:
        raise ValueError("Optimizer checkpoint has no Adam update counters")
    state = {key: torch.empty((), dtype=metadata.state_dict_metadata[key].properties.dtype)
             for key in keys}
    load(state, storage_reader=reader)
    values = [value.item() for value in state.values()]
    if any(value != expected_step for value in values):
        raise ValueError(f"Optimizer counters do not match step {expected_step}: {min(values)}..{max(values)}")
    scheduler = torch.load(checkpoint / "scheduler.pt", map_location="cpu", weights_only=True)
    if scheduler.get("last_epoch") != expected_step:
        raise ValueError("Learning-rate scheduler did not advance with the optimizer")
    return {"status": "passed", "optimizer_step": expected_step,
            "parameter_counters": len(values), "scheduler_step": scheduler["last_epoch"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.checkpoint, args.step)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("STEER_OPTIMIZER_STATE_SIGNAL " + json.dumps(result, sort_keys=True))
