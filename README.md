# SteerDistill

**Quantizing LLM Agents via Online Teacher-Steered Trajectory Distillation**

[Quickstart](#quickstart) · [Training](docs/training/README.md) · [Evaluation](docs/evaluation/README.md) · [Experiment data](docs/experiments/README.md) · [Case studies](https://ustccuigm.github.io/bitdistill/contents.html)

SteerDistill trains quantized LLM agents using online trajectories and
teacher-guided corrections. A frozen teacher provides steering during training;
the trained student acts independently at inference time.

The pipeline covers calibration-data preparation, clipping, quantized model
export, online distillation, and evaluation. Supply your own benchmark-specific,
post-RL BF16 checkpoints; model weights and benchmark data are downloaded separately.

## Models and benchmarks

**Models:** Qwen3-8B, Qwen3.5-4B, and Gemma 4 12B-it.

**Benchmarks:** BFCL V4, tau2-Bench, WebShop, ALFWorld, and Search QA.

For each model, BFCL V4 and tau2-Bench share one post-RL checkpoint and training
run. The other benchmarks use separate checkpoints and training runs.
See [benchmark setup](docs/benchmarks.md) for downloads and checkpoint paths.

## Quickstart

The default training setup uses eight A100 80GB GPUs on Linux. Follow the
[installation guide](docs/setup/README.md) to install the training, inference,
and benchmark environments, then configure the checkout once:

```bash
cp configs/local.example.env configs/local.env
chmod 600 configs/local.env
```

Set your environment and data paths in `configs/local.env`; launchers load it
automatically. For **Qwen3-8B on BFCL V4**, set `QWEN3_8B_TOOL_USE_MODEL` to your
post-RL BF16 checkpoint, prepare the [tool-use training inputs](docs/benchmarks.md#tool-use-training),
and configure `SERPAPI_API_KEY` for web-search evaluation. Run from the repository root:

```bash
bash scripts/run/run_benchmark.sh full --model qwen3_8b --benchmark bfcl_v4
```

This runs prerequisite checks, data preprocessing, clipping, quantized export,
online training, and evaluation. Outputs are saved under
`$STEER_ASSET_ROOT/runs/qwen3_8b/bfcl_v4/`.

## Workflow guides

| Guide | Contents |
| --- | --- |
| [Installation and configuration](docs/setup/README.md) | Dependencies, environments, checkpoint paths, and local settings |
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
