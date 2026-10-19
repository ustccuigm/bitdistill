# Environments and reproducibility

## Training

Use Python 3.10 and the pins in
[`requirements/training.lock`](../requirements/training.lock). The reference
training environment uses PyTorch 2.7.1 with CUDA 12.6, Transformers 5.16.1,
Accelerate 1.13.0, and safetensors 0.8.0 on A100 80GB GPUs.
Qwen3.5 requires `flash-linear-attention==0.4.2`, `fla-core==0.4.2`, and
`einops==0.8.1`; these are included in the training requirements.

The default quantization configuration uses 4-bit integer weights, 16-bit
activations, and group size 64. Training defaults are two epochs, 16
trajectories per update, learning rate `8e-6`, and a 32,768-token context window.
Model and optimizer state continue across trajectory batches.

## Inference

Set `INFERENCE_ENV_ROOT` to the separate vLLM environment. The recorded
integration environment uses vLLM `0.28.1rc1.dev472+gd9105ea80.cu129`,
PyTorch `2.13.0+cu129`, and Transformers `5.16.1`. Its vLLM source revision
is `d9105ea80` from [vLLM](https://github.com/vllm-project/vllm).
Use that revision's installation instructions and matching CUDA wheels.
Older builds without Qwen3.5 or Gemma 4 registration cannot serve those routes.

FlashInfer compilation requires a CUDA 12.9 compiler toolkit, including
cuRAND headers. Set `CUDA_HOME` in the private configuration. For a separate
Conda toolkit prefix:

```bash
export INFERENCE_CUDA_ROOT="$STEER_ASSET_ROOT/envs/cuda12.9"
conda create -y -p "$INFERENCE_CUDA_ROOT" -c nvidia \
  cuda-nvcc=12.9 cuda-cudart-dev=12.9 cuda-cccl=12.9 libcurand-dev
export CUDA_HOME="$INFERENCE_CUDA_ROOT"
test -e "$CUDA_HOME/lib64" || ln -s targets/x86_64-linux/lib "$CUDA_HOME/lib64"
```

`preflight.sh` checks compiler support for `--compress-mode`, cuRAND headers,
and the CUDA runtime library. The inference toolkit is separate from the
training environment's CUDA dependencies.

## Benchmark environments

Set `BENCHMARK_ENV_ROOT` to the environment containing the official BFCL and
tau2 packages and the SDAR environment dependencies needed by the selected
route. Install them following their upstream documentation linked in
[benchmarks.md](benchmarks.md). The recorded BFCL/tau2 environment uses
Transformers 4.56.1, tokenizers 0.22.2, and huggingface-hub 0.36.2.

Install this package without replacing the benchmark environment's dependencies:

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m pip install --no-deps -e "$STEERDISTILL_ROOT"
"$BENCHMARK_ENV_ROOT/bin/python" -m pip install \
  -r "$STEERDISTILL_ROOT/requirements/bfcl-memory.txt"
"$BENCHMARK_ENV_ROOT/bin/python" -c 'from huggingface_hub import snapshot_download; snapshot_download("sentence-transformers/all-MiniLM-L6-v2", revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41", allow_patterns=["*.json", "*.txt", "model.safetensors", "1_Pooling/*"])'
```

The tool-use adapter has a separate Python 3.12 environment. Its compatibility
constraint is in [`requirements/tool-environment.txt`](../requirements/tool-environment.txt).
Apply the two patches and install it as described in the benchmark guide.
WebShop requires a JDK and Pyserini; the reference setup uses OpenJDK 21.
ALFWorld requires TextWorld and Fast Downward. Search QA requires a running
Search-R1 retrieval service.

## External source revisions

These revisions were recorded with the existing integration setup:

| Component | Revision | Source |
| --- | --- | --- |
| Tool-use adapter | `85e322f69279e3b3325b7377ec3bab788514e9cb` | [Repository](https://github.com/Snowflake-Labs/agent-world-model) |
| Tool adapter's `mcp-adapted-bench` submodule | `2dff8bdfc35082e5b6980c4954b6074159a15854` | Adapter submodule |
| SDAR | `d511f043afe9199b8576fc99ea52e12d84841f32` | [Repository](https://github.com/ZJU-REAL/SDAR) |
| BFCL sentence encoder | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | [Model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |

Record the installed BFCL, tau2, and other external repository revisions with
each experiment. The training requirements file does not lock these separate
source checkouts. Model and data downloads remain subject to upstream terms;
see [third-party notices](third_party_notices.md).

## Run records

The online entry point writes a manifest for each batch, recording package
versions, selected configuration, GPU names, seeds, external source revisions,
and input hashes. To record inputs independently after loading the configuration:

```bash
set -a
source "$STEER_CONFIG"
set +a
"$ENV_ROOT/bin/python" scripts/metadata/record_run_manifest.py \
  --output "$STEER_ASSET_ROOT/asset_manifest.json" \
  --asset-root "$STEER_ASSET_ROOT" --step 0 --gpu-ids 0,1,2,3,4,5,6,7
```

The default task shuffle seed is 42. Inference and environment execution can
still introduce sampling variation; preserve sampling settings and repetition
counts with reported results.

## Local checks

```bash
bash scripts/validate/preflight.sh
PYTHONDONTWRITEBYTECODE=1 "$ENV_ROOT/bin/python" -B -m unittest discover -s tests -v
```

Tests requiring external environments are opt-in.

## Source archives

Build a source archive from the committed code so editable-install metadata
and local Python caches are not included. Check its extracted contents:

```bash
release_dir=$(mktemp -d)
git archive HEAD | tar -x -C "$release_dir"
env -u STEERDISTILL_ROOT bash "$release_dir/scripts/validate/check_release.sh"
git archive --format=tar.gz --output="$STEER_ASSET_ROOT/steerdistill-source.tar.gz" HEAD
```

The release checker rejects credentials, private machine paths, datasets,
checkpoints, and generated Python artifacts in the source archive.
