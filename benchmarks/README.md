# Paper benchmark matrix

The benchmark registry follows the SteerDistill paper exactly:

| Registry key | Paper benchmark | training data | Evaluation | BF16 checkpoint |
| --- | --- | --- | --- | --- |
| `bfcl_v4` | BFCL V4 | executable tool use | official BFCL V4 Overall | shared tool-use checkpoint |
| `tau2_bench` | tau^2-Bench | executable tool use | official tau^2 evaluator | shared tool-use checkpoint |
| `webshop` | WebShop | WebShop environment | WebShop success rate | WebShop checkpoint |
| `alfworld` | ALFWorld | ALFWorld environment | ALFWorld success rate | ALFWorld checkpoint |
| `search_qa` | Search QA | NQ and HotpotQA training sets | seven-dataset Search-R1 protocol | Search QA checkpoint |

Search QA evaluates NQ, TriviaQA, PopQA, HotpotQA, 2WikiMultiHopQA, MuSiQue,
and Bamboogle. NQ and HotpotQA are the in-domain training sources; the other
five datasets are evaluated out of domain. The registry exposes only the five
entries in this table.

## External paths

The source archive contains no model weights, model checkpoints, benchmark data,
or environment dumps. Set the path variables in
`benchmarks/paths.example.env` through the environment or a private config
file. For the paper protocol, the model path must identify the output of the
benchmark-specific BF16 RL stage. It is simultaneously used as the frozen
teacher and as the initial
full-precision master from which the W4 learner is created. No checkpoint is
provided by this repository.

For Qwen3-8B, set one path for each checkpoint group:

```bash
export QWEN3_8B_TOOL_USE_MODEL="$STEER_ASSET_ROOT/models/qwen3_8b/tool_use"
export QWEN3_8B_WEBSHOP_MODEL="$STEER_ASSET_ROOT/models/qwen3_8b/webshop"
export QWEN3_8B_ALFWORLD_MODEL="$STEER_ASSET_ROOT/models/qwen3_8b/alfworld"
export QWEN3_8B_SEARCH_QA_MODEL="$STEER_ASSET_ROOT/models/qwen3_8b/search_qa"
```

For Gemma 4 12B-it, set the four corresponding variables beginning with
`GEMMA4_12B_` and select `MODEL_FAMILY=gemma4_12b`. Supply the text
checkpoint with `model_type=gemma4_unified_text`; its decoder uses
`Gemma4UnifiedTextDecoderLayer` for FSDP and the `gemma4` tool and reasoning
parsers for inference. The selected Transformers and vLLM environments must
support this architecture.
The Gemma runtime is launched with `--enforce-eager`.

For Qwen3.5-4B, use the corresponding four variables beginning with
`QWEN35_4B_`. `bfcl_v4` and `tau2_bench` intentionally select the same
`*_TOOL_USE_MODEL` path. WebShop, ALFWorld, and Search QA select separate
paths. To use a different local layout, override the benchmark root and its
`*_RL_TRAIN_DATA`, `*_CLIP_DATA`, `*_PROMPT_MANIFEST`, and `*_SOURCE_ROOT`
variables. A CLIP stream defaults to that benchmark's training data, so calibration
never silently falls back to another benchmark.

## Public data sources

| Benchmark | Upstream data and environment instructions |
| --- | --- |
| BFCL V4 | [BFCL](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard); the tool-use RL environment training data is [AgentWorldModel-1K](https://huggingface.co/datasets/Snowflake/AgentWorldModel-1K) |
| tau^2-Bench | [tau2-bench](https://github.com/sierra-research/tau2-bench); training uses the same executable tool-use inputs as BFCL V4 |
| WebShop | [WebShop](https://github.com/princeton-nlp/WebShop), including its setup and dataset download instructions |
| ALFWorld | [ALFWorld](https://github.com/alfworld/alfworld); install its environment, then run `alfworld-download -f` |
| Search QA | [Search-R1](https://github.com/PeterGriffinJin/Search-R1), [NQ/HotpotQA training data](https://huggingface.co/datasets/PeterJinGo/nq_hotpotqa_train), and the pinned retrieval corpus/index |

Install [SDAR](https://github.com/ZJU-REAL/SDAR) at revision
`d511f043afe9199b8576fc99ea52e12d84841f32` and its benchmark dependencies,
then set `SDAR_ROOT`, `ALFWORLD_DATA`, `SEARCH_TRAIN_PARQUET`, and
`SEARCH_EVAL_PARQUET`. `BENCHMARK_ENV_ROOT` selects the Python environment
containing those dependencies; it can differ from the training environment.
For Search QA, prepare the corpus and index using the Search-R1 retrieval
setup instructions and start its retrieval service before training or evaluation.
Set `SEARCH_RETRIEVER_URL` to its `/retrieve` endpoint; the default is
`http://127.0.0.1:8000/retrieve`. The same corpus and retriever must be used
for the selected training and evaluation protocol.
WebShop also requires a JDK compatible with the installed Pyserini package.
Set `JAVA_HOME` to that JDK or expose `javac` on `PATH`; the environment
integration was checked with OpenJDK 21. Preflight imports the Lucene searcher
to catch missing Java dependencies before rollout.
If benchmark packages are provided as an external source tree, set
`BENCHMARK_PYTHONPATH` to its `site-packages` directory so preflight,
task export, and evaluation use the same dependency set.
`prepare` exports native training tasks and their initial policy contexts to
`*_RL_TRAIN_DATA` when that file is absent. Raw product catalogs,
evaluation questions, and evaluator annotations are not substitute RL
training records. Point `*_CLIP_DATA` at these inputs; the pipeline performs
the normalization and cleaning automatically. Search verifier answers remain
in task metadata and are excluded from calibration prompts. WebShop uses the
SDAR 1K catalog configuration, training goal IDs from 500 onward, and all 500
held-out test goals. ALFWorld uses the complete training game collection and
the complete unseen evaluation split. Search uses all NQ/HotpotQA training
records and all seven evaluation datasets, without a default episode limit.

## Complete route

For every benchmark the intended sequence is:

```bash
# First configure the external assets and environments from the main README.
cd "$STEERDISTILL_ROOT"
export BENCHMARK=bfcl_v4       # tau2_bench, webshop, alfworld, or search_qa
export MODEL_FAMILY=qwen3_8b   # or qwen3_5_4b or gemma4_12b

bash "$STEERDISTILL_ROOT/run_benchmark.sh" prepare
bash "$STEERDISTILL_ROOT/run_benchmark.sh" quantize
bash "$STEERDISTILL_ROOT/run_benchmark.sh" train
bash "$STEERDISTILL_ROOT/run_benchmark.sh" eval
```

Alternatively, `bash run_benchmark.sh full` runs prerequisites, cleaning,
CLIP, initial W4 export, online training, trained W4 export, and evaluation.
Stages reuse matching calibration caches and prepared runtimes. Training
defaults are W4A16, group size 64, two epochs, 16 trajectories per optimizer
update, and learning rate `8e-6`.

For each model, train the shared tool-use route once and evaluate both tool
benchmarks; run the other three routes independently:

```bash
for model in qwen3_8b qwen3_5_4b gemma4_12b; do
  MODEL_FAMILY="$model" BENCHMARK=bfcl_v4 bash run_benchmark.sh full
  MODEL_FAMILY="$model" BENCHMARK=tau2_bench bash run_benchmark.sh eval
  for benchmark in webshop alfworld search_qa; do
    MODEL_FAMILY="$model" BENCHMARK="$benchmark" bash run_benchmark.sh full
  done
done
```

Run this from a shell containing only common configuration and per-model asset
overrides, without a route-specific `RUN_ROOT`, `MODEL_SOURCE_PATH`, or
`TEACHER_MODEL`. This selects 12 training routes and 15 evaluation routes.
For custom training roots, set `TRAINING_RUN_ROOT` consistently when evaluating
the shared BFCL/tau2 checkpoint.

`prepare` validates the benchmark's RL training data, removes empty message
turns and duplicate conversations, and writes normalized calibration data
with counts and SHA256 hashes under `RUN_ROOT/data`. Invalid records and
explicit evaluation splits fail with the source line number. Genuine
prompt-only RL inputs are valid for calibration; they are never converted
into fabricated assistant targets for training. Native tool calls and tool
schemas are preserved. It then runs the asymmetric INT4, group-size-64
clipping search. A reused cache must match the model weights, tokenizer,
normalized data, search parameters, and cache checksum.
`quantize` exports the initial clipped W4 runtime and checks every quantized
linear against the same source and clipping bounds. The initial clipping is
not reapplied to trained weights during online-step export.
The total context window defaults to 32768 tokens. Generation is budgeted
using the server tokenizer after rendering the full prompt, tool schema, and
any steering instruction. The output allowance is the remaining context,
bounded by an explicitly configured `MAX_TOKENS`; no default 2048-token
generation cap is applied. Text-based tool environments retain the sampled
reasoning and action tokens before native API parsing can discard them.
WebShop and ALFWorld additionally cap each response at `ACTION_MAX_TOKENS`
(4096 by default) and stop at `</action>`, retaining the closing tag and all
preceding reasoning. This applies to teacher and student requests.
`train` runs fresh 16-trajectory online batches from that benchmark's data/environment and
stores generated files under the external
`$STEER_ASSET_ROOT/runs/<model-family>/<benchmark>/` directory. BFCL V4 and
tau^2-Bench deliberately share the BFCL training root because the paper uses
one tool-use BF16 checkpoint and one quantized training route for both; their
evaluation outputs remain separate. The other three benchmarks have their own
checkpoints, online steps, logs, and skill stores. `RUN_ROOT` may override this
location for an independent run. `eval` runs the pinned evaluator
specified by the benchmark configuration. At deployment the quantized student
is evaluated without teacher or steering prompts.

BFCL V4 and tau^2-Bench both train through the executable tool-use adapter.
Their evaluation routes call the official benchmark packages. BFCL uses all
scoring categories and native vLLM tool parsing for each model; full Overall
evaluation requires `SERPAPI_API_KEY` for the web-search categories.
tau^2-Bench evaluates every task in the airline, retail, and telecom base
splits, with four independent trials per task. Set `TAU2_USER_MODEL` and,
if necessary, `TAU2_USER_ARGS` for the user simulator. Keep credentials in
environment variables. A local simulator can instead be configured with
`TAU2_USER_MODEL_PATH` and `TAU2_USER_GPU`. The selected simulator is part of
the evaluation protocol and must match the experiment being reported.

WebShop, ALFWorld, and Search QA use the upstream SDAR transitions, prompts,
and reward functions. The evaluator saves every task trajectory and checks
full split coverage. Search retrieval failures stop execution; they are not
counted as model failures. `BENCHMARK_EVAL_COMMAND` and `TAU2_EVAL_COMMAND`
remain optional overrides for another installed official evaluator wrapper.

The evaluation wrapper receives `EVAL_RUNTIME`, `EVAL_OUTPUT_DIR`, and
`EVAL_MODEL_NAME`. It must load that trained student runtime, save the official
scores and trajectories, and fail on evaluator errors.

## Runtime behavior

The shared quantization, data audit, training, checkpoint merge, and AWQ
export stages support all three model families. Native online adapters
are included for WebShop, ALFWorld, and Search QA. They capture and restore
the actual environment state, including the ALFWorld planner state, rather
than replaying a prefix. Task-level output shards permit interrupted runs to
resume after verifying their checksums. Multi-step repairs retain accepted
prefixes, remove failed suffixes, and use the actual generation context as
the training prompt. An ordinary-only batch is accepted only when its source
trajectories succeeded or recorded recovery attempts exhausted the allowed
fallbacks.

The pinned inference build uses CUDA 12.9. Its FlashInfer sampling kernels
compile on first use, so set `CUDA_HOME` to a compatible toolkit before
launching inference. The system CUDA 12.4 compiler rejects the required
`--compress-mode` flag; a compatible driver alone does not supply the compiler.
Preflight checks this flag before any rollout starts.

`INFERENCE_ENV_ROOT` selects the vLLM environment independently of the
training `ENV_ROOT`. The old vLLM 0.10.1 runtime does not register
`Qwen3_5ForConditionalGeneration`; it is not a supported Qwen3.5 rollout
runtime. The entry point checks model registration before starting training.

`run_benchmark.sh full` checks prerequisites, runs calibration and initial
quantization, trains the requested online steps, and evaluates the final trained
runtime. It stops at the first failure. `OPD_EPOCHS=2` controls shuffled passes
through the training tasks; `OPD_MAX_STEPS=0` runs both complete epochs without
an update cap. A positive value explicitly caps updates. Each update uses
`OPD_GLOBAL_BATCH_SIZE=16` fresh trajectories, and the incomplete final batch
of each epoch is retained. Empty ranks contribute zero-loss padding, so every
real trajectory is used exactly once per epoch. `OPD_MAX_STEPS=1` tests one
batch, not full coverage.
Before exporting a trained checkpoint, the pipeline checks completed optimizer
steps, finite loss, finite gradient norms, and at least one nonzero gradient.
The resulting `online/steps/stepNNNNNN/train/training_signal.json` is a training
record containing these optimizer statistics. Evaluation scores are written
separately by the benchmark evaluator.

Static benchmark questions, product catalogs, evaluation annotations, and
placeholder newline completions are not online training trajectories. Never
serialize these objects into the policy prompt to make a training run pass.
Calibration must come from the selected benchmark's RL training split;
evaluation answers and test episodes must not enter calibration or training.

## Evaluation subsets

Evaluation uses the complete official split by default. To evaluate a selected
set of tasks, set `EVAL_TASK_IDS` to an external JSON file before running
`run_benchmark.sh eval`, or pass `--task-ids` to the Python evaluator.

- WebShop, ALFWorld and Search QA: a JSON list of evaluation task IDs.
- BFCL V4: the upstream category-to-task-IDs JSON object. Include the prerequisite
  entries required by selected memory tasks. Web-search tasks require the search API key.
- tau2: an object with `airline`, `retail` and `telecom` keys, each containing a
  nonempty list of task IDs from that domain's base split. Each selected task
  still runs four trials.

Unknown IDs are rejected. Use a separate output directory for each selection.
Reports record `scope: subset`; BFCL writes this in `evaluation_scope.json`.
Subset scores are not full benchmark scores.

## Data contract

Each RL JSONL must contain either the explicit `prompt`/`completion` form
accepted by `train/data_loading.py`, a `messages` trajectory, or the legacy
`[[prompt, completion]]` form. For online trajectory revision, the selected
environment adapter must emit the same verifier-backed trajectory fields used
by `materialize_training_data.py`: the interaction history, assistant
responses, action/environment transitions, success state, and a stable task
key. The adapter must provide an exact state snapshot before the intervention
turn and a restore operation that starts the teacher or steered student from
that snapshot. A snapshot record must include the conversation prefix,
environment state identifier, random-state identifier when the environment is
stochastic, and before/after state hashes. Prefix replay is not accepted as a
substitute for restore. The code rejects a route whose adapter contract is not
declared, rather than treating a static SFT file as an online
SteerDistill run.
