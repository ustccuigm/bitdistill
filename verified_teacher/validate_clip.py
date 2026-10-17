#!/usr/bin/env python3
"""Fail closed unless an asymmetric clip cache is complete and finite."""

import argparse
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("clip", type=Path)
    parser.add_argument(
        "--expected-linears",
        type=int,
        default=None,
        help="Optional architecture-specific linear-layer count; inferred otherwise.",
    )
    parser.add_argument("--bits", type=int)
    parser.add_argument("--group-size", type=int)
    args = parser.parse_args()
    value = torch.load(args.clip, map_location="cpu")
    if args.bits is not None or args.group_size is not None:
        if args.bits is None or args.group_size is None:
            raise ValueError("--bits and --group-size must be provided together")
        metadata = value.get("quantizer", {}) if isinstance(value, dict) else {}
        expected = {
            "version": "int-asym-fp32-fp16scale-v1",
            "bits": args.bits,
            "group_size": args.group_size,
        }
        for key, expected_value in expected.items():
            if metadata.get(key) != expected_value:
                raise ValueError(
                    f"clip quantizer mismatch: {key}={metadata.get(key)!r}, "
                    f"expected {expected_value!r}"
                )
    rows = value.get("clip") if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError("clip entries must be a nonempty list")
    if args.expected_linears is not None and len(rows) != args.expected_linears:
        raise ValueError(
            f"expected {args.expected_linears} clipped linears, got {len(rows)}"
        )
    names = set()
    for index, row in enumerate(rows):
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise ValueError(f"invalid clip row {index}")
        name, max_val, min_val = row
        if not isinstance(name, str) or not name:
            raise ValueError(f"invalid clipped linear name: {name!r}")
        if (not torch.is_tensor(max_val) or not torch.is_tensor(min_val)
                or max_val.numel() == 0 or max_val.shape != min_val.shape):
            raise ValueError(f"invalid clip bound shapes: {name}")
        if name in names:
            raise ValueError(f"duplicate clipped linear: {name}")
        names.add(name)
        if not torch.isfinite(max_val).all() or not torch.isfinite(min_val).all():
            raise ValueError(f"non-finite clip bound: {name}")
        if not torch.all(max_val >= min_val):
            raise ValueError(f"reversed clip bounds: {name}")
    print(
        f"CLIP_VALIDATION_SIGNAL status=passed file={args.clip} "
        f"linears={len(rows)} bits={args.bits} group_size={args.group_size}",
        flush=True,
    )


if __name__ == "__main__":
    main()
