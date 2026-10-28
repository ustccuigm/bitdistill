import torch
from torch import Tensor, device, dtype, nn
from steerdistill.quantization.quantizer import *
from steerdistill.quantization.precision import quantize_activation

def convertModelToQuant(model,
                        modules_to_not_convert=["lm_head"],
                        current_key_name=None,
                        has_been_replaced=False,
                        compute_dtype=torch.bfloat16,
                        quant_type="clsq-n2f3",
                        q_group_size=64,
                        w_bit=None,
                        quant_grid=None, activation_bits=16):
    for name, module in model.named_children():
        if name in {"visual", "vision_tower", "multi_modal_projector"}:
            continue
        if current_key_name is None:
            current_key_name = []
        current_key_name.append(name)
        full_name = ".".join(current_key_name)
        if (isinstance(module, nn.Linear)) and name not in modules_to_not_convert:
            in_features = module.in_features
            out_features = module.out_features
            weight = module.weight
            bias = module.bias

            fixed_grid = None if quant_grid is None else quant_grid.get(full_name)
            if quant_grid is not None and fixed_grid is None:
                raise ValueError(f"Missing fixed GPTQ grid for linear layer {full_name}")
            model._modules[name] = QLinear(
                in_features,
                out_features,
                module.bias is not None,
                compute_dtype=compute_dtype,
                quant_type=quant_type,
                q_group_size=q_group_size,
                w_bit=w_bit,
                fixed_grid=fixed_grid,
                activation_bits=activation_bits,
            )

            model._modules[name].weight = weight
            model._modules[name].bias = bias
            has_been_replaced = True
            # Store the module class in case we need to transpose the weight later
            model._modules[name].source_cls = type(module)
        if len(list(module.children())) > 0:
            _, has_been_replaced = convertModelToQuant(
                module,
                modules_to_not_convert,
                current_key_name,
                has_been_replaced,
                compute_dtype,
                quant_type,
                q_group_size,
                w_bit,
                quant_grid,
                activation_bits,
            )
        # Remove the last key for recursion
        current_key_name.pop(-1)
    return model, has_been_replaced

class QLinear(nn.Linear):
    def __init__(self, input_features, output_features, bias=True, compute_dtype=torch.bfloat16,
                 quant_type="ste-n2f3", q_group_size=64, w_bit=None, device=None,
                 fixed_grid=None, activation_bits=16):
        super().__init__(input_features, output_features, bias, device)

        if quant_type == "ste-n2f3":
            self.weight_quantizer = SteN2F3Quantizer(q_group_size=q_group_size)
        elif quant_type.startswith("int") and quant_type.endswith("-asym"):
            encoded_width = quant_type[len("int"):-len("-asym")]
            bit = int(encoded_width) if encoded_width else w_bit
            if bit is None:
                raise ValueError("w_bit is required when quant_type='int-asym'.")
            if w_bit is not None and bit != w_bit:
                raise ValueError(f"Conflicting bit widths: quant_type={quant_type}, w_bit={w_bit}.")
            if fixed_grid is None:
                self.weight_quantizer = SteIntAsymQuantizer(
                    bit=bit, q_group_size=q_group_size
                )
            else:
                self.weight_quantizer = SteIntAsymFixedGridQuantizer(
                    fixed_grid[0], fixed_grid[1], bit=bit,
                    q_group_size=q_group_size,
                )
        else:
            raise ValueError(
                f"Unsupported quant_type={quant_type}. Use ste-n2f3 or int{{2,3,4,8}}-asym."
            )
        # self.quant_type = quant_type
        self.compute_dtype = compute_dtype
        if activation_bits not in (8, 16):
            raise ValueError("Activation precision must be 8 or 16")
        self.activation_bits = activation_bits

    def forward(self, x: torch.Tensor):
        if self.bias is not None and self.bias.dtype != x.dtype:
            self.bias.data = self.bias.data.to(x.dtype)

        inp_dtype = x.dtype

        if self.compute_dtype is not None:
            x = x.to(self.compute_dtype)

        bias = None if self.bias is None else self.bias.to(self.compute_dtype)
        out = None

        quantize_weight = self.weight_quantizer(self.weight.to(self.compute_dtype))
        x = quantize_activation(x, self.activation_bits, ste=self.training)
        out = F.linear(x, quantize_weight, bias).to(inp_dtype)

        return out
