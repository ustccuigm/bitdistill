"""Packed W2A16/W4A8 reference execution through vLLM's plugin interface.

Weights stay bit-packed between calls. GEMMs use dequantized compute-dtype
operands; this backend makes no low-bit GEMM speedup claim.
"""
import torch
from steerdistill.quantization.precision import unpack_codes, quantize_activation, validate_precision


def register():
    from vllm.model_executor.layers.quantization import register_quantization_config
    from vllm.model_executor.layers.quantization.base_config import QuantizationConfig
    from vllm.model_executor.layers.linear import LinearBase, LinearMethodBase, UnquantizedLinearMethod, RowParallelLinear
    from vllm.model_executor.layers.vocab_parallel_embedding import ParallelLMHead
    from vllm.model_executor.parameter import PackedvLLMParameter, GroupQuantScaleParameter

    @register_quantization_config("steerdistill")
    class SteerDistillConfig(QuantizationConfig):
        def __init__(self, bits, activation_bits, group_size, excluded):
            super().__init__()
            validate_precision(bits, activation_bits)
            self.bits, self.activation_bits, self.group_size = bits, activation_bits, group_size
            self.excluded = excluded

        @classmethod
        def get_name(cls): return "steerdistill"
        @classmethod
        def get_supported_act_dtypes(cls): return [torch.float16, torch.bfloat16]
        @classmethod
        def get_min_capability(cls): return 80
        @staticmethod
        def get_config_filenames(): return ["quant_config.json"]
        @classmethod
        def from_config(cls, config):
            return cls(config["bits"], config["activation_bits"], config["group_size"], config.get("modules_to_not_convert", []))
        def get_quant_method(self, layer, prefix):
            if isinstance(layer, ParallelLMHead) or prefix in self.excluded or any(p in prefix.split('.') for p in ('visual', 'vision_tower', 'multi_modal_projector')):
                return UnquantizedLinearMethod() if isinstance(layer, LinearBase) else None
            if isinstance(layer, LinearBase):
                return PackedReferenceMethod(self, isinstance(layer, RowParallelLinear))
            return None

    class PackedReferenceMethod(LinearMethodBase):
        def __init__(self, config, row_parallel):
            self.config, self.row_parallel = config, row_parallel

        def create_weights(self, layer, input_size_per_partition, output_partition_sizes,
                           input_size, output_size, params_dtype, **attrs):
            c = self.config
            factor = 32 // c.bits
            k, n = input_size_per_partition, sum(output_partition_sizes)
            if k % c.group_size or any(v % factor for v in output_partition_sizes):
                raise ValueError("Tensor-parallel shard is not aligned to quantization groups/packing")
            loader = attrs.get("weight_loader")
            for name, rows, dtype in (("qweight", k, torch.int32), ("qzeros", k // c.group_size, torch.int32)):
                param = PackedvLLMParameter(data=torch.empty(rows, n // factor, dtype=dtype),
                    input_dim=0, output_dim=1, packed_dim=1, packed_factor=factor, weight_loader=loader)
                layer.register_parameter(name, param)
            layer.register_parameter("scales", GroupQuantScaleParameter(
                data=torch.empty(k // c.group_size, n, dtype=torch.float16),
                input_dim=0, output_dim=1, weight_loader=loader))

        def apply(self, layer, x, bias=None):
            c = self.config
            maximum = None
            if c.activation_bits == 8 and self.row_parallel:
                from vllm.distributed import get_tp_group
                group = get_tp_group()
                if group.world_size > 1:
                    maximum = x.float().abs().amax(-1, keepdim=True)
                    torch.distributed.all_reduce(maximum, op=torch.distributed.ReduceOp.MAX, group=group.device_group)
            x = quantize_activation(x, c.activation_bits, maximum=maximum)
            codes = unpack_codes(layer.qweight, c.bits)
            zeros = unpack_codes(layer.qzeros, c.bits).repeat_interleave(c.group_size, dim=0)
            scales = layer.scales.float().repeat_interleave(c.group_size, dim=0)
            weight = ((codes.float() - zeros) * scales).to(x.dtype)
            return torch.nn.functional.linear(x, weight.T, bias)
