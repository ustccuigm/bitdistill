# Quantization precision

The same calibration, online steering, and evaluation entry points accept
`--precision w4a16` (default), `--precision w2a16`, and `--precision w4a8`.
Set `QUANT_PRECISION` in `configs/local.env` to make a choice persistent.
The small files in `configs/w2a16.env` and `configs/w4a8.env` can also be
sourced above the final configuration source line in that file.

## Install the inference plugin

Install the package in both the training and inference environments:

```bash
"$INFERENCE_ENV_ROOT/bin/python" -m pip install --no-deps -e .
```

vLLM discovers the `steerdistill` entry point through its general plugin
interface. If `VLLM_PLUGINS` is set explicitly, include `steerdistill` in it.
Use the inference version and CUDA toolkit in [the environment guide](../reproducibility.md).

## 2-bit weights, 16-bit activations

```bash
bash scripts/run/run_benchmark.sh full --model qwen3_8b --benchmark bfcl_v4 --precision w2a16
```

Weights use asymmetric group-wise INT2 with group size 64, FP16 scales,
and four representable codes per group. Calibration is rerun for the 2-bit
quantizer; a 4-bit clipping cache is rejected. The learner retains floating
master weights and uses a straight-through gradient estimator.

## 4-bit weights, 8-bit activations

```bash
bash scripts/run/run_benchmark.sh full --model qwen3_8b --benchmark bfcl_v4 --precision w4a8
```

The weights use the existing asymmetric INT4 quantizer. Every quantized
language-model linear layer quantizes its input dynamically per token to
symmetric INT8, with scale `max(abs(input)) / 127`. Training and inference
share this definition. For row-parallel layers, inference reduces the maximum
across tensor-parallel shards before quantizing. Attention operations,
normalization, residual streams, embeddings, the output head, and excluded
vision modules retain their compute precision; KV-cache quantization is not
part of this configuration. Clipping calibration optimizes the weight error;
dynamic activation scales require no separate calibration cache.

## Runtime and output locations

Both additional precisions use a packed reference vLLM backend: weights are
stored as INT32 containers holding 2-bit or 4-bit codes and are dequantized
for each linear operation. INT8 activations are quantized and dequantized
before the matrix multiply. Arithmetic uses the configured 16-bit compute
dtype. This implements the numerical quantization schemes, not fused INT2
or W4A8 GEMM acceleration; do not use this backend to claim low-bit kernel
speedups. The default 4-bit/16-bit route retains its existing optimized backend.

Non-default artifacts live under
`runs/<model>/<benchmark>/<precision>/`, with separate clipping caches,
optimizer states, and runtime exports. BFCL V4 and tau2-Bench continue to
share training artifacts within each precision. The model and benchmark
arguments support the same choices as the default route.

For separate stages, replace `full` with `prepare`, `quantize`, `train`, or
`eval`, retaining the same `--precision` argument on every command.
