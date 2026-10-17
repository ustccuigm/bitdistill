import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Function
from tqdm import tqdm
import gc
# import bitsandbytes as bnb
import torch.nn as nn
from functools import partial
# import bitsandbytes.functional as bnbF

class Round(Function):
    @staticmethod
    def forward(self, input):
        sign = torch.sign(input)
        output = sign * torch.floor(torch.abs(input) + 0.5)
        return output

    @staticmethod
    def backward(self, grad_output):
        grad_input = grad_output.clone()
        return grad_input


def round_ste(x):
    """torch.round in forward, identity in backward.

    GPTQ export uses torch.round (ties-to-even).  Keeping the exact same
    rounding rule here is important at 4 bit; the old Round implementation
    rounded half values away from zero and could disagree with the export.
    """
    return (torch.round(x) - x).detach() + x


def asymmetric_quantize_tensor(
    w,
    n_bit=8,
    q_group_size=-1,
    ste=False,
    get_scale_zp=False,
    get_codes=False,
):
    """Canonical group-wise asymmetric quantization used by train and export.

    Quantization parameters are always calculated in FP32.  The dequantized
    tensor is cast back to the input dtype, matching QLinear compute while
    avoiding BF16-dependent scale/zero-point drift.
    """
    org_w_shape = w.shape
    org_w_dtype = w.dtype
    q = w.float()
    if q_group_size > 0:
        assert org_w_shape[-1] % q_group_size == 0
        q = q.reshape(-1, q_group_size)
    elif q_group_size == -1:
        q = q.reshape(-1, q.shape[-1])
    assert q.dim() == 2

    max_int = 2 ** n_bit - 1
    min_val = q.amin(dim=1, keepdim=True)
    max_val = q.amax(dim=1, keepdim=True)
    scales = (max_val - min_val).clamp(min=1e-5) / max_int
    # GPTQ stores scales as FP16.  Simulate that storage precision during
    # training so the fake-quantized forward is the same as packed inference.
    scales = scales.to(torch.float16).float()
    if (scales == 0).any():
        raise ValueError("FP16 GPTQ scale underflowed to zero")
    zeros = (-torch.round(min_val / scales)).clamp_(0, max_int)
    rounded = round_ste(q / scales) if ste else torch.round(q / scales)
    codes = torch.clamp(rounded + zeros, 0, max_int)
    dequant = ((codes - zeros) * scales).reshape(org_w_shape).to(org_w_dtype)

    outputs = [dequant]
    if get_scale_zp:
        outputs.extend((
            scales.view(org_w_shape[0], -1),
            zeros.view(org_w_shape[0], -1),
        ))
    if get_codes:
        outputs.append(codes.reshape(org_w_shape))
    return tuple(outputs) if len(outputs) > 1 else outputs[0]


# core quantization method (simulated quantization)
def pseudo_quantize_tensor(w, n_bit=8,
                           zero_point=True, q_group_size=-1,
                           inplace=False,
                           get_scale_zp=False
                           ):
    if zero_point:
        result = asymmetric_quantize_tensor(
            w,
            n_bit=n_bit,
            q_group_size=q_group_size,
            get_scale_zp=get_scale_zp,
        )
        if get_scale_zp:
            quantized, scales, zeros = result
            if inplace:
                w.copy_(quantized)
                quantized = w
            return quantized, scales, zeros
        if inplace:
            w.copy_(result)
            return w
        return result

    org_w_shape = w.shape
    if q_group_size > 0:
        assert org_w_shape[-1] % q_group_size == 0
        w = w.reshape(-1, q_group_size)
    elif q_group_size == -1:
        w = w.reshape(-1, w.shape[-1])
    assert w.dim() == 2
    max_val = w.abs().amax(dim=1, keepdim=True)
    max_val = max_val.clamp(min=1e-5)
    max_int = 2 ** (n_bit - 1) - 1
    min_int = - 2 ** (n_bit - 1)
    scales = max_val / max_int
    zeros = 0

    assert torch.isnan(scales).sum() == 0
    assert torch.isnan(w).sum() == 0

    if inplace:
        ((w.div_(scales).round_().add_(zeros)).clamp_(
            min_int, max_int).sub_(zeros)).mul_(scales)
    else:
        w = (torch.clamp(torch.round(w / scales) +
                         zeros, min_int, max_int) - zeros) * scales
    assert torch.isnan(w).sum() == 0

    w = w.reshape(org_w_shape)

    if get_scale_zp:
        return w, scales.view(w.shape[0], -1), zeros.view(w.shape[0], -1)
    else:
        return w



@torch.no_grad()
def real_quantize_model_weight(
    model, w_bit, q_config,
    init_only=False
):
    from .qmodule import WQLinear
    from .pre_quant import get_blocks, get_named_linears, set_op_by_name
    assert q_config["zero_point"], "We only support zero_point quantization now."
    
    layers = get_blocks(model)
    for i in tqdm(range(len(layers)), desc="real weight quantization..." + ("(init only)" if init_only else "")):
        layer = layers[i]
        named_linears = get_named_linears(layer)
        # scale_activations(layer)

        for name, module in named_linears.items():
            if init_only:
                q_linear = WQLinear.from_linear(
                    module, w_bit, q_config['q_group_size'], True)
                q_linear.to(next(layer.parameters()).device)
                set_op_by_name(layer, name, q_linear)
            else:
                module.cuda()
                module.weight.data, scales, zeros = pseudo_quantize_tensor(module.weight.data, n_bit=w_bit, get_scale_zp=True, **q_config)
                # scales = scales.t().contiguous()
                # zeros = zeros.t().contiguous()
                q_linear = WQLinear.from_linear(
                    module, w_bit, q_config['q_group_size'], False, scales, zeros)
                module.cpu()
                q_linear.to(next(layer.parameters()).device)
                set_op_by_name(layer, name, q_linear)
                torch.cuda.empty_cache()
                gc.collect()
                
    torch.cuda.empty_cache()
    gc.collect()




def pseudo_quantize_n2f3_tensor(w, q_group_size=-1):
    quantizer = SteN2F3Quantizer(q_group_size=q_group_size)
    w = quantizer(w)
    return w


class SteIntAsymQuantizer(nn.Module):
    """Group-wise asymmetric INT quantizer with an STE rounding operation."""

    def __init__(self, bit=2, q_group_size=64):
        super().__init__()
        if bit not in (2, 3, 4, 8):
            raise ValueError(f"Unsupported asymmetric INT width: {bit}. Choose one of 2, 3, 4, 8.")
        self.q_group_size = q_group_size
        self.bit = bit

    def forward(self, x):
        if os.environ.get("STEERDISTILL_DEBUG", "0") == "1" and not torch.isfinite(x).all():
            raise ValueError("Non-finite value before asymmetric INT quantization")
        x = asymmetric_quantize_tensor(
            x,
            n_bit=self.bit,
            q_group_size=self.q_group_size,
            ste=True,
        )
        if os.environ.get("STEERDISTILL_DEBUG", "0") == "1" and not torch.isfinite(x).all():
            raise ValueError("Non-finite value after asymmetric INT quantization")
        return x


class SteIntAsymFixedGridQuantizer(nn.Module):
    """STE W4 quantization on a rollout checkpoint's fixed GPTQ grid."""

    def __init__(self, scales, zeros, bit=4, q_group_size=64):
        super().__init__()
        if bit not in (2, 3, 4, 8):
            raise ValueError(f"Unsupported asymmetric INT width: {bit}")
        if scales.shape != zeros.shape or scales.dim() != 2:
            raise ValueError("Fixed scales/zeros must share [out, groups] shape")
        self.bit = bit
        self.q_group_size = q_group_size
        self.register_buffer("fixed_scales", scales.half(), persistent=False)
        self.register_buffer("fixed_zeros", zeros.to(torch.uint8), persistent=False)

    def forward(self, x):
        shape = x.shape
        if shape[0] != self.fixed_scales.shape[0]:
            raise ValueError("Fixed GPTQ grid output dimension mismatch")
        grouped = x.float().reshape(-1, self.q_group_size)
        scales = self.fixed_scales.float().reshape(-1, 1)
        zeros = self.fixed_zeros.float().reshape(-1, 1)
        if grouped.shape[0] != scales.shape[0]:
            raise ValueError("Fixed GPTQ grid group count mismatch")
        codes = torch.clamp(
            round_ste(grouped / scales) + zeros,
            0,
            (1 << self.bit) - 1,
        )
        return ((codes - zeros) * scales).reshape(shape).to(x.dtype)


class SteInt2AsymQuantizer(SteIntAsymQuantizer):
    def __init__(self, q_group_size=64):
        super().__init__(bit=2, q_group_size=q_group_size)


class SteInt3AsymQuantizer(SteIntAsymQuantizer):
    def __init__(self, q_group_size=128):
        super().__init__(bit=3, q_group_size=q_group_size)

class SteN2F3Quantizer(nn.Module):
    def __init__(self, q_group_size=128):
        super().__init__()
        self.q_group_size = q_group_size
    
    def forward(self, x):
        org_w_shape = x.shape

        # reshape to groupsize
        if self.q_group_size > 0:
            assert org_w_shape[-1] % self.q_group_size == 0
            qx = x.reshape(-1, self.q_group_size)
        elif self.q_group_size == -1:
            qx = x.reshape(-1, x.shape[-1])
        assert qx.dim() == 2

        # Get the Min Max
        max_val = qx.amax(dim=1, keepdim=True)
        min_val = qx.amin(dim=1, keepdim=True)

        
        scale_pos = torch.abs(max_val)
        scale_neg = torch.abs(min_val)

        dev = qx.device
        x_pos = torch.zeros_like(qx)
        x_neg = torch.zeros_like(qx)
        x_pos = torch.where(qx >= 0, qx, x_pos)
        x_neg = torch.where(qx < 0, qx, x_neg)
        q_pos = x_pos / scale_pos
        q_neg = x_neg / scale_neg

        q_pos, q_neg = self.round_pass(q_pos, q_neg, dev)

        qx = q_pos * scale_pos + q_neg * scale_neg

        qx = qx.reshape(org_w_shape)

        return qx
    
    def round_n2f3(self, q_pos, q_neg, dev):
        q_pos = torch.where(q_pos >= 0.8114928305149078,                                        torch.tensor(1.0).to(dev), q_pos)
        q_pos = torch.where((q_pos < 0.8114928305149078)    & (q_pos >= 0.5024898052215576),    torch.tensor(0.6229856610298157).to(dev), q_pos)
        q_pos = torch.where((q_pos < 0.5024898052215576)    & (q_pos >= 0.2826657369732857),    torch.tensor(0.3819939494132996).to(dev), q_pos)
        q_pos = torch.where((q_pos < 0.2826657369732857)    & (q_pos >= 0.0916687622666359),    torch.tensor(0.1833375245332718).to(dev), q_pos)
        q_pos = torch.where(q_pos < 0.0916687622666359,                                        torch.tensor(0).to(dev), q_pos)

        q_neg = torch.where(q_neg >= -0.1234657019376755,                                     torch.tensor(0).to(dev), q_neg)
        q_neg = torch.where((q_neg < -0.1234657019376755)   & (q_neg >= -0.39097706973552704),   torch.tensor(-0.2469314038753510).to(dev), q_neg)
        q_neg = torch.where((q_neg < -0.39097706973552704)   & (q_neg >= -0.7675113677978516),   torch.tensor(-0.5350227355957031).to(dev), q_neg)
        q_neg = torch.where(q_neg < -0.7675113677978516,                                        torch.tensor(-1.0).to(dev), q_neg)

        return q_pos, q_neg

    def round_pass(self, q_pos, q_neg, dev):
        y_grad_pos, y_grad_neg = q_pos, q_neg
        y_pos, y_neg = self.round_n2f3(q_pos, q_neg, dev)
        
        return (y_pos - y_grad_pos).detach() + y_grad_pos, (y_neg - y_grad_neg).detach() + y_grad_neg
