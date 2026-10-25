# SteerDistill

**Quantizing LLM Agents via Online Teacher-Steered Trajectory Distillation**

[Quickstart](#quickstart-qwen3-8b-on-bfcl-v4) · [Setup](#getting-started) · [Data preparation](docs/data/README.md) · [Training](docs/training/README.md) · [Evaluation](docs/evaluation/README.md) · [Case studies](https://ustccuigm.github.io/bitdistill/contents.html)

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

Set environment, checkpoint, data, GPU, and private API settings in
`configs/local.env`. Launchers load this Git-ignored file automatically;
no manual `export` is required. The default route is Qwen3-8B with BFCL V4.
See [local configuration](docs/benchmarks.md#local-configuration) for overrides
and [checkpoint paths](docs/benchmarks.md#checkpoints) for each model.

### Check prerequisites

```bash
bash scripts/validate/preflight.sh
```

### Quickstart: Qwen3-8B on BFCL V4

After installation, prepare the [tool-use training inputs](docs/benchmarks.md#tool-use-training)
and set `QWEN3_8B_TOOL_USE_MODEL` in `configs/local.env` to your post-RL BF16
checkpoint. Configure `SERPAPI_API_KEY` for BFCL web-search evaluation.
Then run the complete route:

```bash
bash scripts/run/run_benchmark.sh full --model qwen3_8b --benchmark bfcl_v4
```

This runs prerequisite checks, calibration-data preprocessing, clipping,
quantized student export, online teacher-steered training, and BFCL V4
evaluation. Evaluation uses the latest completed student checkpoint without
teacher guidance. Artifacts are written under
`$STEER_ASSET_ROOT/runs/qwen3_8b/bfcl_v4/`; see [training outputs](docs/training/README.md#outputs).

## Workflow guides

| Guide | Contents |
| --- | --- |
| [Data preparation](docs/data/README.md) | Benchmark training inputs and calibration preprocessing |
| [Quantization and training](docs/training/README.md) | Separate commands for all three models, shared tool-use training, and training outputs |
| [Evaluation](docs/evaluation/README.md) | All five benchmarks, runtime prerequisites, and checkpoint selection |
| [Experiment data and figures](docs/experiments/README.md) | Result tables, the 40-case collection, and plotting commands |

## Acknowledgments and license

We thank the authors of BitDistiller, the benchmark environments, and the
inference libraries used by this project. Attribution and component terms are
listed in [third-party notices](docs/third_party_notices.md).
SteerDistill is distributed under the [MIT License](LICENSE); model and dataset
licenses remain with their respective providers.
