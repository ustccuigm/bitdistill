# Installation and configuration

[Project overview](../../README.md)

Run the commands below from the repository root.

- Linux, Bash, and NVIDIA GPUs; the default distributed training setup uses
  eight A100 80GB GPUs.
- Python 3.10 for training; separate inference and benchmark environments.
  The external tool-use adapter uses Python 3.12.
- The training dependencies in [requirements/training.lock](../../requirements/training.lock).
- A vLLM build supporting the selected model architecture and quantized kernels.

The environment versions, CUDA toolkit configuration, and external source
revisions are listed in [reproducibility.md](../../docs/reproducibility.md).

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
[the environment guide](../../docs/reproducibility.md), then configure their paths.

### Configure once

```bash
cp configs/local.example.env configs/local.env
chmod 600 configs/local.env
```

Set environment, checkpoint, data, GPU, and private API settings in
`configs/local.env`. Launchers load this Git-ignored file automatically;
no manual `export` is required. The default route is Qwen3-8B with BFCL V4.
See [local configuration](../../docs/benchmarks.md#local-configuration) for overrides
and [checkpoint paths](../../docs/benchmarks.md#checkpoints) for each model.

### Check prerequisites

```bash
bash scripts/validate/preflight.sh
```
