# Quantization and training

[Project overview](../../README.md)

Run the commands below from the repository root.

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
