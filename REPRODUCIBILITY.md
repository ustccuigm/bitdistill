# Reproducibility Record

This file records the revisions and package versions used for the checked
supplementary package. Model and dataset files remain external and are never
included in the source archive.

## Tested software

The exact Python package pins are in `requirements.lock`. The tested external
source revisions were:

| Component | Revision | Source |
|---|---|---|
| Tool-use environment adapter | `85e322f69279e3b3325b7377ec3bab788514e9cb` | https://github.com/Snowflake-Labs/agent-world-model |
| mcp-adapted-bench | `2dff8bdfc35082e5b6980c4954b6074159a15854` | tool-use environment repository submodule |
| SDAR environments | `d511f043afe9199b8576fc99ea52e12d84841f32` | https://github.com/ZJU-REAL/SDAR |
| BitDistiller | source snapshot; no Git metadata in the supplied tree | https://github.com/DD-DuDa/BitDistiller |

The training environment uses A100-SXM4 80GB devices and CUDA 12.6,
with the package versions listed in `requirements.lock`. Inference is
selected separately by `INFERENCE_ENV_ROOT`; the integration environment
uses vLLM `0.28.1rc1.dev472+gd9105ea80.cu129`, PyTorch `2.13.0+cu129`, and
Transformers `5.16.1`. vLLM 0.10.1 does not support Qwen3.5 and must not be
used for that route. Model registration, kernel loading, actual inference,
and complete benchmark execution are distinct checks.
The inference environment also needs a CUDA 12.9 compiler toolkit for
FlashInfer JIT compilation. A system CUDA 12.4 compiler rejects its
`--compress-mode` option even when PyTorch's bundled CUDA libraries load.
Install the toolkit separately and export `CUDA_HOME` to that prefix before
starting inference; do not replace the training toolkit. For example:

```bash
conda create -y -p "$INFERENCE_CUDA_ROOT" cuda-nvcc=12.9 cuda-cudart-dev=12.9 cuda-cccl=12.9 libcurand-dev
export CUDA_HOME="$INFERENCE_CUDA_ROOT"
# Conda stores libraries under targets; FlashInfer expects lib64.
test -e "$CUDA_HOME/lib64" || ln -s targets/x86_64-linux/lib "$CUDA_HOME/lib64"
```

Qwen3.5 training requires `flash-linear-attention==0.4.2`, `fla-core==0.4.2`,
and `einops==0.8.1`. Transformers dispatches its gated delta rule to FLA
automatically when these packages are importable. The pure PyTorch fallback
exhausted A100 80GB memory during backward with per-device batch size 4;
preflight therefore checks the FLA dependency rather than reducing context
coverage or batch size.

`BENCHMARK_ENV_ROOT` selects the CPU benchmark environment. Install the
official BFCL and tau2 source packages there, and the SDAR environment
dependencies for native environment routes. Keep it separate from training:
the checked BFCL/tau2 environment uses Transformers `4.56.1`, tokenizers
`0.22.2`, and huggingface-hub `0.36.2`. Letting a benchmark installation
upgrade training dependencies can break model loading.

BFCL vector-memory scoring also requires the pinned CPU dependencies and
the official sentence encoder. Prepare them in the benchmark environment:

```bash
"$BENCHMARK_ENV_ROOT/bin/python" -m pip install -r requirements-bfcl-memory.txt
"$BENCHMARK_ENV_ROOT/bin/python" -c 'from huggingface_hub import snapshot_download; print(snapshot_download("sentence-transformers/all-MiniLM-L6-v2", allow_patterns=["*.json", "*.txt", "model.safetensors", "1_Pooling/*"]))'
```

The checked encoder revision is `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`;
record the returned snapshot revision if the upstream default changes.
The official evaluator loads this encoder on CPU. `HF_ENDPOINT` can select a
Hugging Face mirror for downloading; once cached, `HF_HUB_OFFLINE=1` avoids
network requests during scoring. Preflight imports the official vector-memory
module so missing packages or model files fail before GPU evaluation starts.

## External asset manifest

After downloading the public assets, generate a machine-independent manifest:

```bash
"$ENV_ROOT/bin/python" record_run_manifest.py \
  --output asset_manifest.json \
  --asset-root "$STEER_ASSET_ROOT" \
  --step 0 --gpu-ids "0,1,2,3,4,5,6,7"
```

The manifest stores only relative asset names, SHA256 values, software
versions, GPU names, seed-related configuration, and source revisions. It does
not store private absolute paths or credentials.

The required public assets are:

- `Qwen/Qwen3-8B` base model: https://huggingface.co/Qwen/Qwen3-8B
- `Qwen/Qwen3.5-4B` base model: https://huggingface.co/Qwen/Qwen3.5-4B
- `google/gemma-4-12B-it` base model: https://huggingface.co/google/gemma-4-12B-it
  (the quantization route uses its `gemma4_unified_text` text checkpoint).
- BF16 teacher: the paper's benchmark-specific post-RL checkpoint; its local path and
  checksum are recorded through `TEACHER_MODEL` and the run manifest.
- `Snowflake/AgentWorldModel-1K`:
  https://huggingface.co/datasets/Snowflake/AgentWorldModel-1K

The asset manifest covers the model config, tokenizer metadata, prompt
manifest, tool-use environment source tables, and verifier source. Weight files are large and
are represented by their relative file names and hashes when the manifest is
generated.

## Randomness

The rollout seed defaults to `42` and is passed to the task scheduler. The
manifest also records `PYTHONHASHSEED`, rollout temperature, attempt budgets,
and GPU IDs. vLLM and tool-use environment can still introduce sampling variance; reported
benchmark numbers should therefore include the number of seeds or repeated
runs used to obtain them.

## Exact intervention state

The intervention route captures a snapshot before the first model decision and
after every completed environment action. For the local tool-use adapter, the
snapshot contains a transaction-consistent SQLite copy, the full message
history, the trajectory prefix, the assistant-turn count, and a checksum of
the logical database state. A retry loads a private writable database copy and
the saved message history before the Steer is injected. The proxy fails closed
when a request reaches the intervention turn without a restored snapshot.

The native WebShop adapter captures the active browser/session state and
reconstructs derived DOM nodes from saved HTML. The ALFWorld adapter records
both logical facts and native SAS planner state, including admissible actions;
it clears and reuses planner instances when environments close. Search QA captures
the conversation and retrieval state and propagates retrieval errors. Native
adapters include Python and NumPy RNG states in snapshots.

Custom benchmark adapters must expose the same contract through
`BENCHMARK_STATE_SNAPSHOT_COMMAND`. Their
`steer_opd.jsonl` rows must carry the snapshot
identifier, conversation prefix, environment state identifier, random-state
identifier when applicable, and before/after state hashes. Prefix replay is not
accepted as a substitute for exact restoration.

The external tool-use environment adapter checkout used by the local tool-use route must
provide the `snapshot_dir` and `restore_snapshot` agent options. These
options are part of the pinned adapter source revision, not a behavior inferred
from the trajectory log.

## Steering scope

The skill store is retained for audit and version tracking. It is not a
cross-trajectory prompt memory: runtime selection is restricted to the active
step, and analyzer revisions reuse a prior prompt only when the record belongs
to the same repair lineage. A new trajectory starts without steering history;
within one repair lineage, the Teacher rewrites one integrated instruction for
each retry.
