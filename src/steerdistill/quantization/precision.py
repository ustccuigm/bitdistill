"""Shared numerical contract for training and packed reference inference."""
import torch


class _ActivationSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, quantized):
        return quantized

    @staticmethod
    def backward(ctx, grad):
        return grad, None


def validate_precision(bits, activation_bits):
    if (bits, activation_bits) not in {(4, 16), (2, 16), (4, 8)}:
        raise ValueError(f"Unsupported precision W{bits}A{activation_bits}")


def quantize_activation(x, bits=16, *, ste=False, maximum=None):
    """Dynamic symmetric INT8 per token; residuals and attention stay in compute dtype."""
    if bits == 16:
        return x
    if bits != 8:
        raise ValueError("Activation bits must be 8 or 16")
    values = x.float()
    maximum = values.abs().amax(dim=-1, keepdim=True) if maximum is None else maximum
    scale = maximum.clamp_min(torch.finfo(torch.float32).tiny) / 127
    restored = (values.div(scale).round().clamp(-127, 127) * scale).to(x.dtype)
    return _ActivationSTE.apply(x, restored) if ste else restored


def pack_codes(values, bits):
    if bits not in (2, 4):
        raise ValueError("Packed reference weights support 2 or 4 bits")
    factor = 32 // bits
    if values.shape[-1] % factor:
        raise ValueError(f"Packed output dimension must be divisible by {factor}")
    values = values.to(torch.int32)
    output = torch.zeros((*values.shape[:-1], values.shape[-1] // factor),
                         dtype=torch.int32, device=values.device)
    for index in range(factor):
        output |= values[..., index::factor] << (bits * index)
    return output


def unpack_codes(values, bits):
    shifts = torch.arange(0, 32, bits, device=values.device, dtype=torch.int32)
    return ((values.unsqueeze(-1) >> shifts) & ((1 << bits) - 1)).flatten(-2)
