#!/usr/bin/env python3
"""Validate AWQ runtime tensors against SteerDistill's W4 fake quantizer."""

from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from pathlib import Path

import torch
from safetensors import safe_open

from steerdistill.quantization.quantizer import asymmetric_quantize_tensor
from steerdistill.quantization.clip_state import load_bounds, clipped_weight

AWQ_ORDER = (0, 2, 4, 6, 1, 3, 5, 7)


def behavioral_metadata(path: Path) -> dict:
    metadata = json.loads(path.read_text())
    if path.name == "generation_config.json":
        # save_pretrained records the writer version without changing generation.
        metadata.pop("transformers_version", None)
    return metadata


def unpack_awq(packed: torch.Tensor, bits: int = 4) -> torch.Tensor:
    factor = 32 // bits
    output = torch.empty(
        (*packed.shape[:-1], packed.shape[-1] * factor), dtype=torch.int64
    )
    mask = (1 << bits) - 1
    for slot, destination_offset in enumerate(AWQ_ORDER):
        output[..., destination_offset::factor] = (
            packed.to(torch.int64) >> (slot * bits)
        ) & mask
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--bits", type=int, default=4)
    parser.add_argument("--group-size", type=int, default=64)
    parser.add_argument("--layers", type=int, default=0, help="0 validates every packed linear")
    parser.add_argument("--clip", type=Path)
    args = parser.parse_args()
    for name in ("preprocessor_config.json", "video_preprocessor_config.json",
                 "processor_config.json", "generation_config.json"):
        source_metadata = args.source / name
        if source_metadata.is_file():
            runtime_metadata = args.runtime / name
            if not runtime_metadata.is_file() or behavioral_metadata(runtime_metadata) != behavioral_metadata(source_metadata):
                raise ValueError(f"Runtime is missing or has changed model processor metadata: {name}")
    bounds = load_bounds(args.clip) if args.clip else {}
    config = json.loads((args.runtime / "quant_config.json").read_text())
    expected_config = {
        "quant_method": "awq", "zero_point": True,
        "q_group_size": args.group_size, "w_bit": args.bits, "version": "gemm",
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(f"AWQ runtime config mismatch {key}={config.get(key)!r}, expected {expected!r}")

    source_files = sorted(args.source.glob("*.safetensors"))
    if not source_files:
        raise FileNotFoundError(f"No source safetensors under {args.source}")
    with ExitStack() as stack:
        sources = [stack.enter_context(safe_open(path, framework="pt", device="cpu")) for path in source_files]
        runtime = stack.enter_context(
            safe_open(args.runtime / "model.safetensors", framework="pt", device="cpu")
        )
        source_by_key = {
            key: handle for handle in sources for key in handle.keys()
        }
        prefixes = sorted(key[:-8] for key in runtime.keys() if key.endswith(".qweight"))
        if args.layers:
            prefixes = prefixes[:args.layers]
        if not prefixes:
            raise ValueError("AWQ runtime checkpoint contains no qweight tensors")
        max_error = 0.0
        for prefix in prefixes:
            weight = source_by_key[f"{prefix}.weight"].get_tensor(f"{prefix}.weight")
            if prefix in bounds:
                weight = clipped_weight(weight, bounds[prefix])
            _, expected_scales, expected_zeros, expected_codes = asymmetric_quantize_tensor(
                weight,
                n_bit=args.bits,
                q_group_size=args.group_size,
                get_scale_zp=True,
                get_codes=True,
            )
            codes = unpack_awq(runtime.get_tensor(f"{prefix}.qweight"), args.bits).t()
            zeros = unpack_awq(runtime.get_tensor(f"{prefix}.qzeros"), args.bits).t()
            scales = runtime.get_tensor(f"{prefix}.scales").float().t()
            if not torch.equal(codes, expected_codes.long()):
                raise ValueError(f"{prefix}: AWQ qweight codes differ from SteerDistill")
            if not torch.equal(zeros, expected_zeros.long()):
                raise ValueError(f"{prefix}: AWQ qzeros differ from SteerDistill")
            if not torch.equal(scales, expected_scales.float()):
                raise ValueError(f"{prefix}: AWQ scales differ from SteerDistill")
            groups = torch.arange(weight.shape[1]) // args.group_size
            restored = (codes - zeros[:, groups]) * scales[:, groups]
            expected_dequant = (expected_codes - expected_zeros[:, groups]) * expected_scales[:, groups]
            error = (restored.float() - expected_dequant.float()).abs().max().item()
            max_error = max(max_error, error)
        print(
            f"STEERDISTILL_AWQ_VALIDATE_SIGNAL status=passed layers={len(prefixes)} "
            f"bits={args.bits} group_size={args.group_size} max_error={max_error:.9g}",
            flush=True,
        )


if __name__ == "__main__":
    main()
