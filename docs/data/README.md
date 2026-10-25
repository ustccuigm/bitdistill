# Data preparation

[Project overview](../../README.md)

Run the commands below from the repository root.

Download the training data and install the benchmark environments following
[benchmark setup](../../docs/benchmarks.md#data-and-environment-downloads).

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
