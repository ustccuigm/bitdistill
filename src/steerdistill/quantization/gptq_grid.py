"""Load per-linear GPTQ scales and mathematical zero points."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from safetensors import safe_open


def unpack(packed: torch.Tensor, bits: int, count: int, axis: int) -> torch.Tensor:
    factor = 32 // bits
    mask = (1 << bits) - 1
    parts = [((packed >> (index * bits)) & mask) for index in range(factor)]
    if axis == 0:
        return torch.stack(parts, dim=1).reshape(-1, packed.shape[1])[:count]
    return torch.stack(parts, dim=2).reshape(packed.shape[0], -1)[:, :count]


def decode_zero_points(
    encoded: torch.Tensor, bits: int, checkpoint_format: str
) -> torch.Tensor:
    if checkpoint_format == "gptq":
        return (encoded + 1) & ((1 << bits) - 1)
    if checkpoint_format == "gptq_v2":
        return encoded
    raise ValueError(f"Unsupported GPTQ checkpoint_format={checkpoint_format!r}")


def load_gptq_grid(
    model_path: str | Path, bits: int, group_size: int
) -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    """Return `{linear_name: (scales, zeros)}` in `[out, groups]` layout."""
    model_path = Path(model_path)
    config = json.loads((model_path / "quantize_config.json").read_text())
    for key, expected in {
        "bits": bits,
        "group_size": group_size,
        "sym": False,
    }.items():
        if config.get(key) != expected:
            raise ValueError(
                f"GPTQ grid mismatch: {key}={config.get(key)!r}, expected {expected!r}"
            )
    checkpoint_format = config.get("checkpoint_format")
    grid: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    with safe_open(
        model_path / "model.safetensors", framework="pt", device="cpu"
    ) as packed:
        prefixes = sorted(key[:-7] for key in packed.keys() if key.endswith(".scales"))
        for prefix in prefixes:
            scales = packed.get_tensor(prefix + ".scales").T.contiguous().half()
            qzeros = packed.get_tensor(prefix + ".qzeros")
            encoded = unpack(qzeros, bits, scales.shape[0], axis=1).T.contiguous()
            zeros = decode_zero_points(encoded, bits, checkpoint_format)
            grid[prefix] = (scales, zeros.to(torch.uint8))
    if not grid:
        raise ValueError(f"No GPTQ linear grids found in {model_path}")
    return grid
