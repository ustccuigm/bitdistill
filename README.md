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

**Models:** Qwen3-8B, Qwen3.5-4B, and Gemma 4 12B-it.

**Benchmarks:** BFCL V4, tau2-Bench, WebShop, ALFWorld, and Search QA.

All model families use the shared quantization and training pipeline. For each
model, BFCL V4 and tau2-Bench share one post-RL checkpoint and training run;
the other benchmarks use separate checkpoints. See [benchmark setup](docs/benchmarks.md)
for model keys, downloads, data formats, and evaluation protocols.

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

python3.10 -m venv .venv
.venv/bin/python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
.venv/bin/python -m pip install -r requirements/training.lock
.venv/bin/python -m pip install --no-deps -e .
```

Prepare the inference, benchmark, and tool-adapter environments using
[the environment guide](docs/reproducibility.md), then configure their paths.

### Configure once

```bash
cp configs/local.example.env configs/local.env
chmod 600 configs/local.env
```

Edit `configs/local.env` to select the model and benchmark and set environment,
checkpoint, data, and private API settings. Keep custom settings above its final
`source` line. The scripts load this file automatically and pass its settings
to subprocesses; no manual `export` or environment activation is required.
`configs/local.env` is excluded from Git.

The template selects Qwen3-8B and BFCL V4 by default. Model and data locations
are documented in [benchmark setup](docs/benchmarks.md). To select another
route, change `MODEL_FAMILY` and `BENCHMARK` in the file before running.

### Check prerequisites

```bash
bash scripts/validate/preflight.sh
```

### Prepare calibration data and quantize

```bash
bash scripts/run/run_benchmark.sh prepare
bash scripts/run/run_benchmark.sh quantize
```

`prepare` normalizes training records and computes clipping bounds; `quantize`
exports the initial quantized student, reusing matching calibration results.

### Train the quantized student

```bash
bash scripts/run/run_benchmark.sh train
```

Training generates online trajectories, applies teacher-guided corrections,
and updates the student. Completed updates export quantized checkpoints.
Set training GPUs with `GPU_IDS` in `configs/local.env`.

### Evaluate

```bash
bash scripts/run/run_benchmark.sh eval
```

Evaluation uses the latest completed quantized checkpoint without teacher
guidance. Select another completed step with `EVAL_STEP` in `configs/local.env`.
To evaluate the shared tool-use checkpoint on tau2-Bench, change `BENCHMARK`
to `tau2_bench` and run the same evaluation command.

For the complete sequence, use:

```bash
bash scripts/run/run_benchmark.sh full
```

For all three models and five benchmarks, see
[running all configurations](docs/benchmarks.md#running-all-configurations).

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
.venv/bin/python -B -m unittest discover -s tests -v
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
