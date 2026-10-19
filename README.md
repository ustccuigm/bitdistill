# SteerDistill

Code for **SteerDistill: Quantizing LLM Agents via Online Teacher-Steered
Trajectory Distillation**. The repository provides the W4A16 quantization,
online training, and evaluation entry points used with the paper's benchmark
adapters. Model checkpoints, benchmark data, and environment installations are
external inputs and are not included in this repository.

## Repository layout

```text
configs/                  Public configuration templates
docs/                     Benchmark setup, reproducibility, and notices
patches/                  Required patches for external adapters
scripts/
  prepare/                Data normalization, clipping, and runtime export
  run/                    Benchmark, rollout, and evaluation entry points
  train/                  Distributed training launchers
  validate/               Preflight and release checks
src/steerdistill/         Importable Python package
tests/                    Unit and integration-contract tests
```

All generated artifacts belong under `STEER_ASSET_ROOT` rather than the source
checkout. This includes model copies, clipping caches, run directories,
checkpoints, logs, and benchmark outputs.

## Installation

The reference configuration uses Linux, CUDA, Python 3.10, and a separate
environment for benchmark-specific dependencies. The default W4A16 run uses
eight A100-class GPUs.

```bash
git clone https://github.com/ustccuigm/bitdistill.git
cd bitdistill

python3.10 -m venv /path/to/steerdistill-env
/path/to/steerdistill-env/bin/python -m pip install --upgrade pip
/path/to/steerdistill-env/bin/python -m pip install -r requirements.lock
/path/to/steerdistill-env/bin/python -m pip install -e .
```

`requirements-tool-env.txt` is for the separate tool-environment adapter. See
[docs/reproducibility.md](docs/reproducibility.md) for tested versions, CUDA
requirements, external revisions, and adapter installation.

## Configuration

Create a private environment file outside the repository and point
`STEER_CONFIG` to it. It should set external locations before sourcing the
public template:

```bash
export STEER_CONFIG=/path/to/steerdistill.env
```

```bash
export STEER_ASSET_ROOT=/path/to/steerdistill-assets
export ENV_ROOT=/path/to/steerdistill-env
export INFERENCE_ENV_ROOT=/path/to/inference-env
export BENCHMARK_ENV_ROOT=/path/to/benchmark-env

# Select one model family and benchmark for this shell.
export MODEL_FAMILY=qwen3_8b
export BENCHMARK=bfcl_v4
source /path/to/bitdistill/configs/steerdistill.example.env
```

The public templates are [configs/steerdistill.example.env](configs/steerdistill.example.env)
and [configs/benchmark-paths.example.env](configs/benchmark-paths.example.env).
Set `TEACHER_MODEL` (the benchmark-specific BF16 post-RL checkpoint) and any
model/data overrides in the private file. BFCLv4 and tau2-bench share their
tool-use checkpoint; WebShop, ALFWorld, and Search QA each use a
benchmark-specific checkpoint. The required external data and adapter setup
are listed in [docs/benchmarks.md](docs/benchmarks.md).

Keep access tokens, API keys, local paths, and model weights outside the
repository.

## Commands

All public commands are relative to the repository root and load
`$STEER_CONFIG` when it is set.

```bash
# Check the selected configuration and required external inputs.
bash scripts/validate/preflight.sh

# Normalize calibration data and create the clipping cache.
bash scripts/run/run_benchmark.sh prepare

# Export the initial clipped W4A16 runtime.
bash scripts/run/run_benchmark.sh quantize

# Run online SteerDistill training.
GPU_IDS=0,1,2,3,4,5,6,7 bash scripts/run/run_benchmark.sh train

# Evaluate the latest committed online checkpoint.
bash scripts/run/run_benchmark.sh eval
```

`full` runs `preflight`, `quantize`, `train`, and `eval` in that order. The
online scheduler uses the configuration defaults of two epochs, global
trajectory batch size 16, group size 64, W4A16, and learning rate `8e-6`.
Benchmark-specific preparation and evaluation requirements are documented in
[docs/benchmarks.md](docs/benchmarks.md).

## Validation and release checks

```bash
python -m compileall -q src scripts tests
python -m unittest discover -s tests -v
bash scripts/validate/check_release.sh
```

`preflight.sh` validates a configured external run. Unit tests cover local
data, training, quantization, and adapter contracts; benchmark environment
tests require their corresponding external assets.

## Citation and license

Please cite the accompanying paper when using this code. The project is
released under the [MIT License](LICENSE). External components and their
licenses are listed in [docs/third_party_notices.md](docs/third_party_notices.md).
