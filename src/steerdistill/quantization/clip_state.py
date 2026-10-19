"""Apply the same asymmetric clipping bounds to export and validation weights."""
import torch


def load_bounds(path):
    from steerdistill.quantization.clip_utils import validate_clip_quantizer_metadata
    state = torch.load(path, map_location="cpu")
    validate_clip_quantizer_metadata(state, 4, 64)
    bounds = {}
    for name, maximum, minimum in state["clip"]:
        if name in bounds:
            raise ValueError(f"Duplicate clipping bound: {name}")
        bounds[name] = (maximum, minimum)
    if not bounds:
        raise ValueError("Empty clipping cache")
    return bounds


def clipped_weight(weight, bounds):
    maximum, minimum = (value.to(weight.device) for value in bounds)
    return torch.clamp(weight.reshape(*maximum.shape[:2], -1), minimum, maximum).reshape_as(weight)
