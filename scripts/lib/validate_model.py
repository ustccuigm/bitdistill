#!/usr/bin/env python3
"""Fast structural validation for supported Hugging Face checkpoints."""

import argparse
import json
from pathlib import Path

from safetensors import safe_open


EXPECTED_SHARDS = {
    "model-00001-of-00004.safetensors": 4_964_086_808,
    "model-00002-of-00004.safetensors": 4_999_837_496,
    "model-00003-of-00004.safetensors": 4_983_084_680,
    "model-00004-of-00004.safetensors": 1_434_507_768,
}


def required_model_keys(config: dict) -> set[str]:
    model_type = str(config.get("model_type", ""))
    text_config = config.get("text_config") if isinstance(config.get("text_config"), dict) else {}
    num_layers = int(config.get("num_hidden_layers", 0) or text_config.get("num_hidden_layers", 0) or 0)
    if num_layers <= 0:
        raise ValueError("config.json has no positive num_hidden_layers")

    if model_type == "qwen3_5":
        prefix = "model.language_model."
        required = {prefix + "embed_tokens.weight", prefix + "norm.weight"}
        # Qwen3.5 alternates linear-attention and full-attention blocks, so
        # there is no single q_proj/v_proj schema shared by every layer.
        required.update(f"{prefix}layers.{layer}." for layer in range(num_layers))
        return required

    required = {"model.embed_tokens.weight", "model.norm.weight"}
    if not bool(config.get("tie_word_embeddings", False)):
        required.add("lm_head.weight")
    for layer in range(num_layers):
        for projection in (
            "self_attn.q_proj", "self_attn.k_proj",
            "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj",
        ):
            required.add(f"model.layers.{layer}.{projection}.weight")
        if model_type != "gemma4_unified_text" or (layer + 1) % 6:
            required.add(f"model.layers.{layer}.self_attn.v_proj.weight")
    return required


def check_missing(required: set[str], actual: set[str], model_type: str) -> list[str]:
    if model_type != "qwen3_5":
        return sorted(required - actual)
    prefix = "model.language_model.layers."
    missing = [key for key in required if not any(name.startswith(key) for name in actual)]
    return sorted(missing)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir")
    args = parser.parse_args()
    root = Path(args.model_dir)
    config_path = root / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    required = required_model_keys(config)
    index_path = root / "model.safetensors.index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        weight_map = index.get("weight_map")
        if not isinstance(weight_map, dict) or not weight_map:
            raise ValueError("Invalid or empty safetensors weight_map")
        indexed_shards = set(weight_map.values())
        tensor_count = 0
        actual_keys = set()
        for name in sorted(indexed_shards):
            path = root / name
            if not path.is_file() or path.stat().st_size <= 0:
                raise ValueError(f"Missing or empty indexed shard: {name}")
            with safe_open(path, framework="pt", device="cpu") as handle:
                shard_keys = set(handle.keys())
                actual_keys.update(shard_keys)
                tensor_count += len(shard_keys)
        missing_indexed = sorted(set(weight_map) - actual_keys)
        unexpected = sorted(actual_keys - set(weight_map))
        if missing_indexed or unexpected:
            raise ValueError(
                f"Shard/index mismatch: missing={missing_indexed[:8]} unexpected={unexpected[:8]}"
            )
        missing = check_missing(required, actual_keys, str(config.get("model_type", "")))
        if missing:
            raise ValueError(f"Sharded checkpoint is missing {len(missing)} tensors: {missing[:8]}")
        if indexed_shards == set(EXPECTED_SHARDS):
            for name, expected_size in EXPECTED_SHARDS.items():
                actual_size = (root / name).stat().st_size
                if actual_size != expected_size:
                    raise ValueError(f"Incomplete {name}: size={actual_size}, expected={expected_size}")
        print(
            f"MODEL_DOWNLOAD_SIGNAL format=sharded shards={len(indexed_shards)} "
            f"model_type={config.get('model_type', 'unknown')} tensors={tensor_count} "
            f"bytes={sum((root / name).stat().st_size for name in indexed_shards)}",
            flush=True,
        )
        return

    model_path = root / "model.safetensors"
    if not model_path.is_file():
        raise FileNotFoundError(f"Neither {index_path} nor {model_path} exists")
    with safe_open(model_path, framework="pt", device="cpu") as handle:
        keys = set(handle.keys())
    missing = check_missing(required, keys, str(config.get("model_type", "")))
    if missing:
        raise ValueError(f"Merged checkpoint is missing {len(missing)} tensors: {missing[:8]}")
    print(
        f"MODEL_DOWNLOAD_SIGNAL format=single shards=1 model_type={config.get('model_type', 'unknown')} "
        f"tensors={len(keys)} bytes={model_path.stat().st_size}", flush=True
    )


if __name__ == "__main__":
    main()
