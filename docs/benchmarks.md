# Model and benchmark setup

Commands below run from the repository root. Keep checkpoints, datasets,
environment installations, and outputs under `STEER_ASSET_ROOT`.

## Checkpoints

The quantization stage takes the benchmark-specific BF16 checkpoint produced
by RL as input. It initializes both the frozen teacher and the student master
weights from this checkpoint. This repository does not distribute those
post-RL checkpoints.

| Model | Registry key | Base model | Required checkpoint architecture |
| --- | --- | --- | --- |
| Qwen3-8B | `qwen3_8b` | [Qwen/Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | `qwen3` |
| Qwen3.5-4B | `qwen3_5_4b` | [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | `qwen3_5` |
| Gemma 4 12B-it | `gemma4_12b` | [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) | `gemma4_unified_text` |

The Gemma route expects the text checkpoint. Model-specific FSDP wrapping and
tool parsers are selected from the checkpoint architecture. Qwen3.5 requires
the FLA training dependencies; Gemma inference uses eager execution.

Each model has four checkpoint groups. BFCL V4 and tau2-Bench share `tool_use`.

| Group | Qwen3-8B override | Qwen3.5-4B override | Gemma override |
| --- | --- | --- | --- |
| Tool use | `QWEN3_8B_TOOL_USE_MODEL` | `QWEN35_4B_TOOL_USE_MODEL` | `GEMMA4_12B_TOOL_USE_MODEL` |
| WebShop | `QWEN3_8B_WEBSHOP_MODEL` | `QWEN35_4B_WEBSHOP_MODEL` | `GEMMA4_12B_WEBSHOP_MODEL` |
| ALFWorld | `QWEN3_8B_ALFWORLD_MODEL` | `QWEN35_4B_ALFWORLD_MODEL` | `GEMMA4_12B_ALFWORLD_MODEL` |
| Search QA | `QWEN3_8B_SEARCH_QA_MODEL` | `QWEN35_4B_SEARCH_QA_MODEL` | `GEMMA4_12B_SEARCH_QA_MODEL` |

Defaults resolve to `models/<registry-key>/<group>/` under `STEER_ASSET_ROOT`.
For example, `models/qwen3_5_4b/tool_use/` must contain the model configuration,
tokenizer, and safetensors weights. Set overrides before sourcing
[`steerdistill.example.env`](../configs/steerdistill.example.env).

## Data and environment downloads

| Benchmark | Public sources | Local prerequisites |
| --- | --- | --- |
| BFCL V4 | [Official evaluator](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard), [tool-use training data](https://huggingface.co/datasets/Snowflake/AgentWorldModel-1K), [tool adapter](https://github.com/Snowflake-Labs/agent-world-model) | Training records, prompt manifest, generated environment tables, patched adapter; `SERPAPI_API_KEY` for web-search evaluation |
| tau2-Bench | [Official environment and evaluator](https://github.com/sierra-research/tau2-bench) | Shared tool-use training inputs; configured user simulator for evaluation |
| WebShop | [Environment and data instructions](https://github.com/princeton-nlp/WebShop), [SDAR integration](https://github.com/ZJU-REAL/SDAR) | SDAR catalog, search index, JDK and Pyserini |
| ALFWorld | [Environment and data instructions](https://github.com/alfworld/alfworld), [SDAR integration](https://github.com/ZJU-REAL/SDAR) | Game files, TextWorld, and Fast Downward planner |
| Search QA | [Search-R1](https://github.com/PeterGriffinJin/Search-R1), [NQ/HotpotQA training data](https://huggingface.co/datasets/PeterJinGo/nq_hotpotqa_train) | Training and evaluation Parquet files, retrieval corpus/index, running retrieval service |

Follow upstream download and installation instructions and retain their
licenses. Source revisions and separate environment setup are documented in
[reproducibility.md](reproducibility.md).

### Tool-use training

Set `TOOL_ENV_ADAPTER_ROOT`, `TOOL_ENV_BIN`, and `TOOL_ENV_PYTHON` to the
adapter checkout, executable, and Python 3.12 interpreter. The adapter must
support `snapshot_dir` and `restore_snapshot`. Apply the context and local
transition patches in this order from its checkout:

```bash
cd "$TOOL_ENV_ADAPTER_ROOT"
patch -p1 < "$STEERDISTILL_ROOT/patches/tool_environment_context.patch"
patch -p1 < "$STEERDISTILL_ROOT/patches/tool_environment_transition.patch"
"$TOOL_ENV_PYTHON" -m pip install -e . \
  -r "$STEERDISTILL_ROOT/requirements/tool-environment.txt"
```

The default BFCL asset directory is `benchmarks/bfcl_v4/` and contains:

```text
rl_train.jsonl
prompts.jsonl
environment/
  gen_tasks.jsonl
  gen_envs.jsonl
  gen_db.jsonl
  gen_sample.jsonl
  gen_verifier.pure_code.jsonl
```

`prompts.jsonl` is the executable task manifest; task identity is carried in
`metadata.scenario` and `metadata.task_id`. Use the exported environment data
and verifier tables from the same task collection. tau2-Bench uses these
same training inputs and the corresponding trained checkpoint.

### Native environments

Set the following in the private configuration before sourcing the template:

```bash
export SDAR_ROOT="$STEER_ASSET_ROOT/vendor/SDAR"
export ALFWORLD_DATA="$STEER_ASSET_ROOT/benchmarks/alfworld/data"
export SEARCH_TRAIN_PARQUET="$STEER_ASSET_ROOT/benchmarks/search_qa/train.parquet"
export SEARCH_EVAL_PARQUET="$STEER_ASSET_ROOT/benchmarks/search_qa/test.parquet"
export SEARCH_RETRIEVER_URL=http://127.0.0.1:8000/retrieve
# For WebShop, configure JAVA_HOME to the installed JDK if needed.
```

`prepare` exports initial policy contexts from the native training environment
when its `rl_train.jsonl` is absent. WebShop uses the SDAR catalog and training
goals from index 500 onward. ALFWorld uses its training game collection.
Search QA uses NQ and HotpotQA training records; answers remain task metadata
and are excluded from calibration prompts. Start the Search-R1 retrieval
service before online training or evaluation.

### Calibration input

`BENCHMARK_CLIP_DATA` defaults to the selected benchmark's RL training data.
The normalizer accepts prompt records or structured conversations, preserves
tool calls and schemas, removes empty message turns and duplicate records,
and rejects explicit evaluation splits and raw product catalogs. It saves
normalized data and a preparation report under `RUN_ROOT/data/`.

Genuine prompt-only records can be used for clipping. Assistant training
targets are generated by the online trajectory pipeline. Cached clipping
bounds are reused only when model, tokenizer, data, and search parameters match.

## Evaluation

Use `MODEL_FAMILY=<key> BENCHMARK=<key> bash scripts/run/run_benchmark.sh eval`
after training. `EVAL_STEP` defaults to `latest`; `EVAL_GPU_IDS` defaults to `0`.
The evaluator loads a completed quantized student checkpoint and uses no
teacher steering.

| Route | Evaluation scope and settings |
| --- | --- |
| BFCL V4 | Official scoring categories and Overall score. Install `requirements/bfcl-memory.txt` and cache the sentence encoder for memory categories. Web search requires `SERPAPI_API_KEY`. |
| tau2-Bench | Airline, retail, and telecom base splits, four trials per task. Set `TAU2_USER_MODEL` and optional JSON `TAU2_USER_ARGS`, or use `TAU2_USER_MODEL_PATH` with `TAU2_USER_GPU`. |
| WebShop | Held-out goal IDs 0-499, using environment success. |
| ALFWorld | Unseen evaluation games (`eval_out_of_distribution`). |
| Search QA | NQ, TriviaQA, PopQA, HotpotQA, 2WikiMultiHopQA, MuSiQue, and Bamboogle; per-dataset exact match and its unweighted mean. |

The selected data files determine the available evaluation tasks. Supply all
seven Search QA datasets in `SEARCH_EVAL_PARQUET` for the paper's protocol.
Use the same retrieval corpus and index across the experiment.

The tau2 user simulator is part of the environment, separate from the
distillation teacher. Keep its credentials in environment variables.
Native evaluators write `scores.json` and task trajectories; BFCL retains
its official result and score files. Outputs live in
`runs/<model-family>/<benchmark>/eval/stepNNNNNN/` under the asset root.

## Configuration reference

[`benchmark-paths.example.env`](../configs/benchmark-paths.example.env)
lists every model and data path. [`steerdistill.example.env`](../configs/steerdistill.example.env)
defines training defaults. Use the all-model command in the
[main README](../README.md#run-every-model-and-benchmark) to run the 12 training
configurations and 15 evaluations without training the shared tool-use model twice.
