# Benchmarks and external assets

This repository does not redistribute model weights, RL training data, or
benchmark environments. Store them under `STEER_ASSET_ROOT`, or override the
paths in a private `STEER_CONFIG` file.

## Supported configurations

| Model family | `MODEL_FAMILY` |
| --- | --- |
| Qwen3-8B | `qwen3_8b` |
| Qwen3.5-4B | `qwen3_5_4b` |
| Gemma 4 12B-it | `gemma4_12b` |

| Benchmark | `BENCHMARK` | Engine |
| --- | --- | --- |
| BFCLv4 | `bfcl_v4` | tool environment |
| tau2-bench | `tau2_bench` | tool environment |
| WebShop | `webshop` | SDAR |
| ALFWorld | `alfworld` | SDAR |
| Search QA | `search_qa` | SDAR |

BFCLv4 and tau2-bench use the same post-RL tool-use checkpoint for a given
model family. The remaining benchmarks use their own post-RL checkpoints.
The path variables are documented in
[`configs/benchmark-paths.example.env`](../configs/benchmark-paths.example.env).

## Required assets

For every selected benchmark, provide:

- a BF16 post-RL checkpoint through `TEACHER_MODEL` (or the matching model
  variable in `benchmark-paths.example.env`);
- `rl_train.jsonl` for online training and clipping calibration;
- prompt and environment files required by the benchmark adapter;
- a writable directory for `RUN_ROOT` outputs.

BFCLv4 additionally requires the tool-use environment and its data. The
adapter must expose exact state snapshot and restore support; apply the patches
in [`patches/`](../patches/) to the adapter checkout before installing it.
tau2-bench needs its configured user simulator. WebShop needs a JDK and the
upstream search index. ALFWorld and Search QA require the corresponding SDAR
assets. Keep benchmark API credentials in the private environment file.

## Running one benchmark

```bash
export MODEL_FAMILY=qwen3_8b
export BENCHMARK=webshop
export STEER_CONFIG=/path/to/steerdistill.env

bash scripts/validate/preflight.sh
bash scripts/run/run_benchmark.sh prepare
bash scripts/run/run_benchmark.sh quantize
GPU_IDS=0,1,2,3,4,5,6,7 bash scripts/run/run_benchmark.sh train
bash scripts/run/run_benchmark.sh eval
```

`prepare` normalizes benchmark records and creates the clipping cache.
`quantize` exports the initial W4A16 runtime. `train` runs the online learner;
`eval` evaluates the latest committed runtime. Outputs are rooted at
`$STEER_ASSET_ROOT/runs/$MODEL_FAMILY/$BENCHMARK` unless overridden.

## External sources

- BFCL and the tool-use environment: follow the upstream benchmark release and
  install the patched adapter described above.
- tau2-bench, WebShop, ALFWorld, and Search QA: install the exact upstream
  source revisions listed in [reproducibility.md](reproducibility.md).

The release checker intentionally rejects benchmark data and checkpoints inside
this source tree.
