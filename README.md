# SteerDistill

**Quantizing LLM Agents via Online Teacher-Steered Trajectory Distillation**

[Getting started](#getting-started) · [Models and benchmarks](#models-and-benchmarks) · [Benchmark setup](docs/benchmarks.md) · [Case studies](https://github.com/ustccuigm/bitdistill/tree/gh-pages)

SteerDistill trains quantized LLM agents using online trajectories and
teacher-guided corrections. A frozen teacher provides steering during training;
the trained quantized student acts independently at inference time.

This repository starts from benchmark-specific, post-RL BF16 checkpoints and
provides data preparation, clipping calibration, quantized model export,
online distillation, and benchmark evaluation. Supply your own post-RL
checkpoints; model weights and benchmark data are downloaded separately.

## Models and benchmarks

All three model families use the shared quantization and training implementation.
Select a row with `MODEL_FAMILY` and a column with `BENCHMARK`.

| Model | `MODEL_FAMILY` | BFCL V4 | tau2-Bench | WebShop | ALFWorld | Search QA |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B | `qwen3_8b` | Included | Included | Included | Included | Included |
| Qwen3.5-4B | `qwen3_5_4b` | Included | Included | Included | Included | Included |
| Gemma 4 12B-it | `gemma4_12b` | Included | Included | Included | Included | Included |

| Benchmark | `BENCHMARK` | Training inputs | Evaluation metric |
| --- | --- | --- | --- |
| BFCL V4 | `bfcl_v4` | Executable tool-use tasks | Official Overall score |
| tau2-Bench | `tau2_bench` | Same tool-use tasks and checkpoint as BFCL V4 | Pass@1 over four trials per task |
| WebShop | `webshop` | WebShop training environments | Success rate |
| ALFWorld | `alfworld` | ALFWorld training environments | Success rate |
| Search QA | `search_qa` | NQ and HotpotQA training sets | Mean exact match across seven datasets |

For each model, BFCL V4 and tau2-Bench share one post-RL checkpoint and one
quantized training run. The other three benchmarks use separate checkpoints
and training runs: **12 training configurations and 15 evaluation configurations**.
See [benchmark setup](docs/benchmarks.md) for downloads, checkpoint variables,
data formats, and evaluator requirements.

## Requirements

- Linux, Bash, and NVIDIA GPUs; the default distributed training setup uses
  eight A100 80GB GPUs.
- Python 3.10 for training; separate inference and benchmark environments.
  The external tool-use adapter uses Python 3.12.
- The training dependencies in [requirements/training.lock](requirements/training.lock).
- A vLLM build supporting the selected model architecture and quantized kernels.

The environment versions, CUDA toolkit configuration, and external source
revisions are listed in [reproducibility.md](docs/reproducibility.md).

## Getting started

### Install the training package

```bash
git clone https://github.com/ustccuigm/bitdistill.git
cd bitdistill

export STEERDISTILL_ROOT="$PWD"
export STEER_ASSET_ROOT="$(dirname "$PWD")/steerdistill-assets"
export ENV_ROOT="$STEER_ASSET_ROOT/envs/train"

python3.10 -m venv "$ENV_ROOT"
"$ENV_ROOT/bin/python" -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
"$ENV_ROOT/bin/python" -m pip install -r requirements/training.lock
"$ENV_ROOT/bin/python" -m pip install --no-deps -e .
```

Prepare the inference, benchmark, and tool-adapter environments using
[the environment guide](docs/reproducibility.md), then configure their paths.

### Configure external assets

Use a private configuration file outside the checkout, for example
`$STEER_ASSET_ROOT/config.env`. Its contents should follow this template:

```bash
export STEERDISTILL_ROOT=/path/to/bitdistill
export STEER_ASSET_ROOT=/path/to/steerdistill-assets
export ENV_ROOT="$STEER_ASSET_ROOT/envs/train"
export INFERENCE_ENV_ROOT="$STEER_ASSET_ROOT/envs/inference"
export BENCHMARK_ENV_ROOT="$STEER_ASSET_ROOT/envs/benchmarks"

# Defaults remain overridable by each command below.
export MODEL_FAMILY=${MODEL_FAMILY:-qwen3_8b}
export BENCHMARK=${BENCHMARK:-bfcl_v4}

# Put checkpoint, dataset, adapter, and API settings here, before sourcing.
# Default checkpoint folders are listed in docs/benchmarks.md.
source "$STEERDISTILL_ROOT/configs/steerdistill.example.env"
```

```bash
export STEER_CONFIG="$STEER_ASSET_ROOT/config.env"
```

The per-model checkpoint variables select both the frozen teacher and the
initial student weights. To override one run directly, set `MODEL_SOURCE_PATH`
before sourcing the template. Setting only `TEACHER_MODEL` changes the teacher
but does not change the initial student checkpoint.

### Prepare, train, and evaluate

After placing the external inputs at the configured paths:

```bash
bash scripts/validate/preflight.sh
bash scripts/run/run_benchmark.sh prepare
bash scripts/run/run_benchmark.sh quantize
GPU_IDS=0,1,2,3,4,5,6,7 bash scripts/run/run_benchmark.sh train
bash scripts/run/run_benchmark.sh eval
```

`prepare` normalizes training records and computes clipping bounds; `quantize`
exports the initial quantized student. `train` updates the student and exports
each completed checkpoint. `eval` selects the latest committed checkpoint.
Use `EVAL_STEP=2` to evaluate a specific completed step. `full` runs preflight,
quantization, training, and evaluation in sequence.

### Run every model and benchmark

Run this from a shell containing common settings and per-model asset paths.
Let each command load `STEER_CONFIG`; avoid exporting derived paths such as
`RUN_ROOT`, `MODEL_SOURCE_PATH`, or `TEACHER_MODEL` across different routes.

```bash
set -e
for model in qwen3_8b qwen3_5_4b gemma4_12b; do
  MODEL_FAMILY="$model" BENCHMARK=bfcl_v4 \
    bash scripts/run/run_benchmark.sh full
  MODEL_FAMILY="$model" BENCHMARK=tau2_bench \
    bash scripts/run/run_benchmark.sh eval
  for benchmark in webshop alfworld search_qa; do
    MODEL_FAMILY="$model" BENCHMARK="$benchmark" \
      bash scripts/run/run_benchmark.sh full
  done
done
```

This sequence trains the shared tool-use model once per model family and
evaluates it on both tool-use benchmarks. All evaluation routes use the
quantized student without teacher guidance.

## Configuration defaults

| Setting | Default |
| --- | --- |
| Weight precision | 4-bit integers |
| Activation precision | 16-bit |
| Quantization group size | 64 |
| Training epochs | 2 |
| Trajectories per optimizer update | 16 |
| Learning rate | `8e-6` |
| Context window | 32,768 tokens |
| Task shuffle seed | 42 |

The runtime uses AWQ-compatible packing and Marlin kernels. Packing describes
the exported tensor layout; clipping and distillation are implemented by
SteerDistill. The configuration templates are in [configs/](configs/).

## Outputs

Artifacts are stored outside the checkout under
`$STEER_ASSET_ROOT/runs/<model-family>/<benchmark>/`:

```text
data/                       Normalized calibration records
checkpoints/                Clipping cache and initial quantized model
online/steps/stepNNNNNN/     Trajectories, repair records, and training signals
online/checkpoints/         Updated models and optimizer checkpoints
online/latest.json          Latest committed training step
eval/stepNNNNNN/            Evaluation results and trajectories
```

tau2-Bench reads training checkpoints from the corresponding BFCL V4 run and
writes evaluation results to its own directory.

## Repository layout

```text
configs/           Model, benchmark, and training configuration templates
docs/              Setup, reproducibility, and third-party notices
requirements/      Dependencies grouped by environment
scripts/           Preparation, training, evaluation, and validation commands
src/steerdistill/   Quantization, teacher guidance, training, and adapters
tests/             Unit tests and environment integration tests
patches/           External tool-adapter patches
licenses/          Third-party license texts
```

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 "$ENV_ROOT/bin/python" -B -m unittest discover -s tests -v
```

Environment integration tests are enabled with `STEER_TEST_ENVIRONMENTS=1`
after their external assets are configured. `preflight.sh` checks the selected
model, software environment, data, and benchmark prerequisites.
Source-archive checks are described in [reproducibility.md](docs/reproducibility.md#source-archives).

## Acknowledgments and license

We thank the authors of BitDistiller, the benchmark environments, and the
inference libraries used by this project. Attribution and component terms are
listed in [third-party notices](docs/third_party_notices.md).
SteerDistill is distributed under the [MIT License](LICENSE); model and dataset
licenses remain with their respective providers.
