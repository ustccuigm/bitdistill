# SteerDistill

**Quantizing LLM Agents via Online Teacher-Steered Trajectory Distillation**

[Setup](#getting-started) · [Data preparation](#data-preparation) · [Training](#quantization-and-training) · [Evaluation](#evaluation) · [Case studies](https://github.com/ustccuigm/bitdistill/tree/gh-pages)

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
`source` line. The Bash launchers load this file automatically and pass its
settings to subprocesses; no manual `export` is required.
`configs/local.env` is excluded from Git.

The template selects Qwen3-8B and BFCL V4 by default. Model and data locations
are documented in [benchmark setup](docs/benchmarks.md). The commands below
select routes with `--model` and `--benchmark`. Keep the template's
`${MODEL_FAMILY:-...}` and `${BENCHMARK:-...}` assignments so command-line
selections can override the defaults. Set training GPUs with `GPU_IDS`.

### Check prerequisites

```bash
bash scripts/validate/preflight.sh
```

## Data preparation

Download the training data and install the benchmark environments following
[benchmark setup](docs/benchmarks.md#data-and-environment-downloads).

**BFCL V4 and tau2-Bench:** provide the shared tool-use training records,
executable prompt manifest, and environment tables. tau2-Bench does not require
a second training dataset. Its evaluation uses the official tau2 environment.

**WebShop, ALFWorld, and Search QA:** export training tasks from their native
environments using the Python entry point below. Search QA uses NQ and HotpotQA
training records. Each export is performed once and shared by all three models.

```bash
(
  set -e
  source scripts/_bootstrap.sh
  source scripts/lib/load_config.sh

  "$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.prepare_sdar_tasks \
    --benchmark webshop --split train --output "$WEBSHOP_RL_TRAIN_DATA"
  "$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.prepare_sdar_tasks \
    --benchmark alfworld --split train --output "$ALFWORLD_RL_TRAIN_DATA"
  "$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.prepare_sdar_tasks \
    --benchmark search_qa --split train --output "$SEARCH_QA_RL_TRAIN_DATA"
)
```

Run only the exports needed for your benchmarks. The parentheses keep these
configuration variables out of the shell used to launch different training routes.
The quantization launcher also generates missing native training records.

Calibration records are normalized and deduplicated automatically before
clipping. To inspect this preprocessing independently:

```bash
.venv/bin/python -m steerdistill.benchmarks.prepare_data \
  --input /path/to/rl_train.jsonl \
  --output /path/to/prepared/calibration.jsonl
```

## Quantization and training

Each example starts from the corresponding post-RL BF16 checkpoint.
`quantize` prepares calibration data, computes clipping bounds, and exports
the initial quantized student. `train` runs online teacher-steered distillation
and exports completed student checkpoints. These launchers coordinate the
Python calibration, export, and distributed-training programs and check cached
artifacts before reuse.

For every model, run the tool-use training route once for **both BFCL V4 and
tau2-Bench**. WebShop, ALFWorld, and Search QA each require their own post-RL
checkpoint and training run. The examples below are independent experiments,
not consecutive stages of one model.

### Qwen3-8B

Set the `QWEN3_8B_*_MODEL` paths in `configs/local.env`, or place the four
checkpoints under `models/qwen3_8b/` in the asset directory.

```bash
# BFCL V4 + tau2-Bench: shared tool-use checkpoint
bash scripts/run/run_benchmark.sh quantize --model qwen3_8b --benchmark bfcl_v4
bash scripts/run/run_benchmark.sh train --model qwen3_8b --benchmark bfcl_v4

# WebShop
bash scripts/run/run_benchmark.sh quantize --model qwen3_8b --benchmark webshop
bash scripts/run/run_benchmark.sh train --model qwen3_8b --benchmark webshop

# ALFWorld
bash scripts/run/run_benchmark.sh quantize --model qwen3_8b --benchmark alfworld
bash scripts/run/run_benchmark.sh train --model qwen3_8b --benchmark alfworld

# Search QA
bash scripts/run/run_benchmark.sh quantize --model qwen3_8b --benchmark search_qa
bash scripts/run/run_benchmark.sh train --model qwen3_8b --benchmark search_qa
```

### Qwen3.5-4B

Set the `QWEN35_4B_*_MODEL` paths, or use `models/qwen3_5_4b/` in the asset
directory. This route requires the FLA dependencies in the training lock file
and an inference environment supporting the `qwen3_5` architecture.

```bash
# BFCL V4 + tau2-Bench: shared tool-use checkpoint
bash scripts/run/run_benchmark.sh quantize --model qwen3_5_4b --benchmark bfcl_v4
bash scripts/run/run_benchmark.sh train --model qwen3_5_4b --benchmark bfcl_v4

# WebShop
bash scripts/run/run_benchmark.sh quantize --model qwen3_5_4b --benchmark webshop
bash scripts/run/run_benchmark.sh train --model qwen3_5_4b --benchmark webshop

# ALFWorld
bash scripts/run/run_benchmark.sh quantize --model qwen3_5_4b --benchmark alfworld
bash scripts/run/run_benchmark.sh train --model qwen3_5_4b --benchmark alfworld

# Search QA
bash scripts/run/run_benchmark.sh quantize --model qwen3_5_4b --benchmark search_qa
bash scripts/run/run_benchmark.sh train --model qwen3_5_4b --benchmark search_qa
```

### Gemma 4 12B-it

Set the `GEMMA4_12B_*_MODEL` paths, or use `models/gemma4_12b/` in the asset
directory. Supply a text checkpoint with architecture `gemma4_unified_text`;
the runtime selects eager execution for this model.

```bash
# BFCL V4 + tau2-Bench: shared tool-use checkpoint
bash scripts/run/run_benchmark.sh quantize --model gemma4_12b --benchmark bfcl_v4
bash scripts/run/run_benchmark.sh train --model gemma4_12b --benchmark bfcl_v4

# WebShop
bash scripts/run/run_benchmark.sh quantize --model gemma4_12b --benchmark webshop
bash scripts/run/run_benchmark.sh train --model gemma4_12b --benchmark webshop

# ALFWorld
bash scripts/run/run_benchmark.sh quantize --model gemma4_12b --benchmark alfworld
bash scripts/run/run_benchmark.sh train --model gemma4_12b --benchmark alfworld

# Search QA
bash scripts/run/run_benchmark.sh quantize --model gemma4_12b --benchmark search_qa
bash scripts/run/run_benchmark.sh train --model gemma4_12b --benchmark search_qa
```

Use `prepare` instead of `quantize` to stop after clipping. Use `full` to run
preflight, quantization, training, and evaluation for a selected route.

## Evaluation

The Python evaluators below accept an explicit trained quantized checkpoint
and apply to all three model families. Replace `/path/to/...` with the exported
student directory, not the BF16 source checkpoint. The `--model` argument is
the local serving name; architecture and tool parsers are read from the checkpoint.
No evaluator uses the distillation teacher or steering.

Open a separate shell for direct Python evaluation, then load the environment
paths and private settings once:

```bash
source scripts/_bootstrap.sh
source scripts/lib/load_config.sh
```

### BFCL V4

Uses the official scoring categories and Overall score. Install the memory
dependencies and configure `SERPAPI_API_KEY` for web-search tasks.

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.evaluate_bfcl \
  --runtime /path/to/quantized-tool-use-checkpoint --model steerdistill \
  --output /path/to/results/bfcl_v4 --gpus 0
```

### tau2-Bench

Use the **same checkpoint as BFCL V4**. Configure `TAU2_USER_MODEL` and its API
settings in `configs/local.env`. Evaluation covers airline, retail, and telecom
with four trials per task; the user simulator is separate from the student.

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.evaluate_tau2 \
  --runtime /path/to/quantized-tool-use-checkpoint --model steerdistill \
  --output /path/to/results/tau2_bench --gpus 0
```

### WebShop

Uses the WebShop-specific checkpoint and the 500 held-out shopping goals.
The catalog, search index, JDK, and Pyserini must be installed.

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.evaluate_sdar \
  --benchmark webshop --runtime /path/to/quantized-webshop-checkpoint \
  --model steerdistill --output /path/to/results/webshop --gpus 0 --workers 4
```

### ALFWorld

Uses the ALFWorld-specific checkpoint and unseen evaluation games. Install
the game data, TextWorld, and Fast Downward planner.

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.evaluate_sdar \
  --benchmark alfworld --runtime /path/to/quantized-alfworld-checkpoint \
  --model steerdistill --output /path/to/results/alfworld --gpus 0 --workers 4
```

### Search QA

Uses the Search-QA-specific checkpoint. Start the retrieval service configured
by `SEARCH_RETRIEVER_URL` and provide all seven evaluation datasets: NQ,
TriviaQA, PopQA, HotpotQA, 2WikiMultiHopQA, MuSiQue, and Bamboogle. Results
include per-dataset exact match and their unweighted mean.

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m steerdistill.benchmarks.evaluate_sdar \
  --benchmark search_qa --runtime /path/to/quantized-search-qa-checkpoint \
  --model steerdistill --output /path/to/results/search_qa --gpus 0 --workers 4
```

Use a distinct output directory for each model, benchmark, and checkpoint.
To select the latest completed training checkpoint automatically, run this
alternative from a fresh shell; change the model and benchmark as needed:

```bash
bash scripts/run/run_benchmark.sh eval --model qwen3_8b --benchmark bfcl_v4
bash scripts/run/run_benchmark.sh eval --model qwen3_8b --benchmark tau2_bench
```

Set `EVAL_STEP` in `configs/local.env` to select a specific completed update.
The [all-configuration example](docs/benchmarks.md#running-all-configurations)
covers the 12 training runs and 15 evaluations.

## Experiment data and figures

Organized [experiment data and figures](https://github.com/ustccuigm/bitdistill/tree/gh-pages/experiments)
and the existing [40-case collection](https://github.com/ustccuigm/bitdistill/tree/gh-pages/data/cases)
are maintained on `gh-pages`. The `main` branch contains the implementation,
plotting scripts, and documentation, without duplicating these datasets.
Plot the quantitative results without running model inference:

```bash
python -m pip install -r requirements/figures.txt
git fetch origin gh-pages
git worktree add --detach ../bitdistill-pages origin/gh-pages
python scripts/figures/plot_results.py \
  --data ../bitdistill-pages/experiments/data \
  --output ../bitdistill-pages/experiments/figures
```

See [figure generation](docs/figures.md) for data checks and PDF-coordinate extraction.

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
