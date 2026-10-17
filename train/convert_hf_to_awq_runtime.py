#!/usr/bin/env python3
"""Pack SteerDistill asymmetric W4 values into standard AutoAWQ GEMM layout.

This is a format conversion only.  It does not run AWQ calibration, rescaling,
or a second quantization algorithm: codes/scales/zero-points come directly from
the same ``asymmetric_quantize_tensor`` used by the QAT fake quantizer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from safetensors.torch import save_file
from transformers import AutoConfig, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quantization.quantizer import asymmetric_quantize_tensor
from model_support import load_model
from quantization.clip_state import load_bounds, clipped_weight


AWQ_ORDER = (0, 2, 4, 6, 1, 3, 5, 7)


def copy_processor_metadata(source: Path, output: Path) -> None:
    """Retain model loading metadata needed even by text-only agent tasks."""
    names = ("preprocessor_config.json", "video_preprocessor_config.json",
             "processor_config.json", "generation_config.json")
    for name in names:
        path = source / name
        if path.is_file():
            value = json.loads(path.read_text())
            (output / name).write_text(json.dumps(value, indent=2) + "\n")


def pack_awq(values: torch.Tensor, bits: int = 4) -> torch.Tensor:
    """Pack the final dimension using AutoAWQ's non-standard nibble order."""
    if bits != 4:
        raise ValueError("vLLM AWQ/Marlin runtime export supports W4 only.")
    factor = 32 // bits
    if values.shape[-1] % factor:
        raise ValueError(f"AWQ packed dimension must be divisible by {factor}: {values.shape}")
    output = torch.zeros(
        (*values.shape[:-1], values.shape[-1] // factor),
        dtype=torch.int32,
        device=values.device,
    )
    source = values.to(torch.int32)
    for slot, source_offset in enumerate(AWQ_ORDER):
        output |= source[..., source_offset::factor] << (slot * bits)
    return output


def quantized_linear_tensors(module, bits: int, group_size: int) -> dict[str, torch.Tensor]:
    _, scales, zeros, codes = asymmetric_quantize_tensor(
        module.weight,
        n_bit=bits,
        q_group_size=group_size,
        get_scale_zp=True,
        get_codes=True,
    )
    # AutoAWQ GEMM stores input-major qweight and group-major scales/zeros;
    # qweight and qzeros are packed along output channels.
    return {
        "qweight": pack_awq(codes.t().contiguous(), bits).cpu(),
        "qzeros": pack_awq(zeros.t().contiguous(), bits).cpu(),
        "scales": scales.t().contiguous().to(torch.float16).cpu(),
    }


def should_quantize(name: str, module: torch.nn.Module) -> bool:
    parts = name.split(".")
    return (isinstance(module, torch.nn.Linear) and parts[-1] != "lm_head"
            and not set(parts).intersection({"visual", "vision_tower", "multi_modal_projector"}))


def convert(source: Path, output: Path, bits: int, group_size: int, clip: Path | None = None) -> int:
    if bits != 4:
        raise ValueError("AWQ/Marlin route is W4A16 only.")
    config = AutoConfig.from_pretrained(source, trust_remote_code=True)
    model = load_model(
        source,
        config=config,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        device_map="cpu",
    ).eval()
    if clip is not None:
        bounds = load_bounds(clip)
        modules = dict(model.named_modules())
        with torch.no_grad():
            for name, values in bounds.items():
                if name not in modules or not should_quantize(name, modules[name]):
                    raise ValueError(f"Clip cache refers to a non-quantized layer: {name}")
                modules[name].weight.copy_(clipped_weight(modules[name].weight, values))
    state = dict(model.state_dict())
    converted = 0
    for name, module in model.named_modules():
        if not should_quantize(name, module):
            continue
        tensors = quantized_linear_tensors(module, bits, group_size)
        state.pop(f"{name}.weight", None)
        for suffix, tensor in tensors.items():
            state[f"{name}.{suffix}"] = tensor
        if module.bias is not None:
            state[f"{name}.bias"] = module.bias.detach().to(torch.float16).cpu()
        converted += 1
    if converted == 0:
        raise RuntimeError("No linear layers were converted to AWQ runtime layout.")
    for key, value in list(state.items()):
        if torch.is_tensor(value):
            state[key] = value.detach().cpu().contiguous()
            if state[key].dtype == torch.bfloat16:
                state[key] = state[key].to(torch.float16)
    # safetensors rejects two keys sharing one storage. Preserve tied-weight
    # semantics in config while cloning only duplicate storage views.
    seen_storage = {}
    for key, value in state.items():
        storage = (value.untyped_storage().data_ptr(), value.untyped_storage().nbytes())
        if storage in seen_storage:
            state[key] = value.clone()
        else:
            seen_storage[storage] = key

    output.mkdir(parents=True, exist_ok=True)
    quant_config = {
        "quant_method": "awq",
        "zero_point": True,
        "q_group_size": group_size,
        "w_bit": bits,
        # vLLM AWQ accepts the AutoAWQ names above; its AWQ-Marlin
        # compatibility detector reads these canonical aliases.
        "group_size": group_size,
        "bits": bits,
        "version": "gemm",
        "modules_to_not_convert": [
            name for name, module in model.named_modules()
            if isinstance(module, torch.nn.Linear) and not should_quantize(name, module)
        ],
    }
    (output / "quant_config.json").write_text(
        json.dumps(quant_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # Some vLLM releases look for quantize_config.json first.
    (output / "quantize_config.json").write_text(
        json.dumps(quant_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    save_file(state, output / "model.safetensors", metadata={"format": "pt"})
    model.config.quantization_config = quant_config
    model.config.torch_dtype = "float16"
    model.config.save_pretrained(output)
    AutoTokenizer.from_pretrained(source, trust_remote_code=True).save_pretrained(output)
    copy_processor_metadata(source, output)
    print(
        f"STEERDISTILL_AWQ_PACK_SIGNAL status=ready source={source} output={output} "
        f"bits={bits} group_size={group_size} linears={converted}",
        flush=True,
    )
    return converted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bits", type=int, default=4)
    parser.add_argument("--group-size", type=int, default=64)
    parser.add_argument("--clip", type=Path, help="Apply only for the initial BF16-to-W4 export")
    args = parser.parse_args()
    convert(args.source, args.output, args.bits, args.group_size, args.clip)


if __name__ == "__main__":
    main()
