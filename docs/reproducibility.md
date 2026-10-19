# Reproducibility

## Software environment

Use the versions pinned in `requirements/training.lock` for the training environment.
Benchmark adapters may require a separate environment because their dependency
sets are not interchangeable. The tool-use adapter uses
`requirements/tool-environment.txt`.

The reference W4A16 configuration uses CUDA-capable A100-class GPUs, group
size 64, two epochs, trajectory batch size 16, and learning rate `8e-6`.
Set `MODEL_MAX_LENGTH=32768` unless a benchmark-specific resource constraint
requires a different value.

## External inputs

Keep these inputs outside the checkout and record their revision or checksum in
your run directory:

- the benchmark-specific post-RL BF16 checkpoint;
- the benchmark RL training records and prompts;
- benchmark source trees, adapters, and environment data;
- the user simulator or API configuration required by the selected benchmark.

The template in `configs/benchmark-paths.example.env` defines the expected
layout. `scripts/metadata/record_run_manifest.py` records the selected
configuration, external input hashes, seed, and runtime metadata for a run.

## Validation sequence

```bash
bash scripts/validate/preflight.sh
python -m unittest discover -s tests -v
bash scripts/run/run_benchmark.sh prepare
bash scripts/run/run_benchmark.sh quantize
bash scripts/run/run_benchmark.sh train
bash scripts/run/run_benchmark.sh eval
```

Run `bash scripts/validate/check_release.sh` before creating a source archive.
It rejects local paths, credentials, generated weights, benchmark data, and
Python cache artifacts.
