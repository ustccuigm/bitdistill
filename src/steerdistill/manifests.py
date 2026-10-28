#!/usr/bin/env python3
"""Record reproducibility metadata without writing private absolute paths."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
from pathlib import Path


PACKAGES = (
    "torch", "transformers", "accelerate", "vllm", "triton",
    "safetensors", "fastapi", "uvloop", "datasets", "tokenizers",
    "flash-linear-attention", "fla-core", "einops",
)
ASSET_VARIABLES = ("BENCHMARK_RL_TRAIN_DATA", "BENCHMARK_CLIP_DATA",
                   "BENCHMARK_PROMPT_MANIFEST", "CLIP_PATH")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def revision(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--gpu-ids", required=True)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    files = {}
    inputs = {key: Path(os.environ[key]) for key in ASSET_VARIABLES if os.getenv(key)}
    for role in ("TEACHER_MODEL", "INITIAL_W4_MASTER"):
        if os.getenv(role):
            model = Path(os.environ[role])
            for path in sorted(model.glob("*.json")) + sorted(model.glob("*.safetensors")):
                inputs[f"{role}/{path.name}"] = path
    if os.getenv("BENCHMARK_SOURCE_ROOT"):
        environment = Path(os.environ["BENCHMARK_SOURCE_ROOT"])
        for path in sorted(environment.glob("gen_*.jsonl")):
            inputs[f"environment/{path.name}"] = path
    for label, path in inputs.items():
        if path.is_file():
            files[label] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        else:
            files[label] = {"missing": True}

    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None

    gpu_names = []
    try:
        import torch
        gpu_names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception:
        pass

    tool_env_root = Path(os.environ.get(
        "TOOL_ENV_ADAPTER_ROOT", str(root / "vendor/tool-use-environment")
    ))
    payload = {
        "schema": 1,
        "step": args.step,
        "gpu_ids": args.gpu_ids,
        "gpu_names": gpu_names,
        "packages": versions,
        "python": os.sys.version.split()[0],
        "config": {
            key: os.environ.get(key)
            for key in (
                "BENCHMARK", "DISCOVERY_ATTEMPTS", "COUNTERFACTUAL_ATTEMPTS",
                "VALIDATION_ATTEMPTS", "ONLINE_TURN_BATCH_SIZE",
                "LEARNING_RATE", "MODEL_MAX_LENGTH", "ROLLOUT_TEMPERATURE",
                "PYTHONHASHSEED", "SEED", "MODEL_FAMILY", "MAX_TOKENS",
                "OPD_GLOBAL_BATCH_SIZE", "OPD_MICRO_BATCH_SIZE", "OPD_EPOCHS",
                "OPD_MAX_STEPS", "OPD_SEED", "OPD_PREVIOUS_OPTIMIZER_STEP",
                "QUANT_PRECISION", "BITS", "ACTIVATION_BITS", "GROUP_SIZE",
            )
            if os.environ.get(key) is not None
        },
        "source_revisions": {
            "sdar": revision(Path(os.environ.get("SDAR_ROOT", str(root / "vendor/SDAR")))),
            "tool_use_environment": revision(tool_env_root),
            "tool_use_evaluation": revision(tool_env_root / "mcp-adapted-bench"),
        },
        "assets": files,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"STEER_MANIFEST_SIGNAL status=written output={args.output} files={len(files)}")


if __name__ == "__main__":
    main()
