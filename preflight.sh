#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONFIG=${STEER_CONFIG:-$ROOT/config.example.env}
source "$CONFIG"

[[ -x "$ENV_ROOT/bin/python" ]] || { echo "missing Python: $ENV_ROOT/bin/python" >&2; exit 2; }
"$ENV_ROOT/bin/python" - <<'PY'
import importlib
import importlib.metadata
required = {
    "torch": "2.7.1",
    "transformers": "5.16.1",
    "accelerate": "1.13.0",
    "safetensors": "0.8.0",
}
for name, expected in required.items():
    try:
        actual = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError as error:
        raise SystemExit(f"missing Python dependency: {name}") from error
    if actual.split("+", 1)[0] != expected:
        raise SystemExit(f"{name}=={actual}; expected tested version {expected}")
    importlib.import_module(name)
PY
if [[ "$MODEL_FAMILY" == qwen3_5_4b ]]; then
  "$ENV_ROOT/bin/python" - <<'PY'
import importlib.metadata
from fla.ops.gated_delta_rule import chunk_gated_delta_rule
for package in ("flash-linear-attention", "fla-core"):
    actual = importlib.metadata.version(package)
    if actual != "0.4.2":
        raise SystemExit(f"{package}=={actual}; expected tested version 0.4.2")
PY
fi
"$INFERENCE_ENV_ROOT/bin/python" "$ROOT/common/check_runtime_support.py" "$TEACHER_MODEL"
"$INFERENCE_ENV_ROOT/bin/python" - <<'PY'
import importlib.util
from pathlib import Path
import subprocess
from torch.utils.cpp_extension import CUDA_HOME

if importlib.util.find_spec("flashinfer") is not None:
    compiler = Path(CUDA_HOME or "") / "bin/nvcc"
    if not compiler.is_file():
        raise SystemExit("FlashInfer JIT requires nvcc; set CUDA_HOME to the inference CUDA toolkit")
    result = subprocess.run([str(compiler), "--help"], capture_output=True, text=True, check=True)
    if "--compress-mode" not in result.stdout:
        raise SystemExit("The installed FlashInfer requires a newer nvcc: configure the tested CUDA 12.9 toolkit through CUDA_HOME")
    toolkit = Path(CUDA_HOME)
    if not any((toolkit / relative).is_file() for relative in
               ("include/curand.h", "targets/x86_64-linux/include/curand.h")):
        raise SystemExit("FlashInfer JIT requires cuRAND headers; install libcurand-dev in the inference CUDA toolkit")
    if not (toolkit / "lib64/libcudart.so").is_file():
        raise SystemExit("FlashInfer JIT requires CUDA_HOME/lib64/libcudart.so; see the Conda toolkit layout instructions in REPRODUCIBILITY.md")
PY

required=(
  "$ROOT/train/mytrainer.py"
  "$ROOT/train/data_loading.py"
  "$ROOT/common/launch_train.sh"
  "$ROOT/verified_teacher/generate_verified.py"
  "$ROOT/run_benchmark.sh"
  "$ROOT/run_online.py"
  "$ROOT/run_rollout_step.sh"
  "$ROOT/train_online_step.sh"
  "$ROOT/train/online_step.py"
)
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "STEERDISTILL_PREFLIGHT_SIGNAL status=failed missing=$path" >&2; exit 2; }
done

asset_files=(
  "$INITIAL_W4_MASTER/config.json"
  "$TEACHER_MODEL/config.json"
)
if [[ "$BENCHMARK_ENGINE" == "tool_env" ]]; then
  "${TOOL_ENV_PYTHON:-$(dirname "$TOOL_ENV_BIN")/python}" - <<'PY'
import inspect
from awm.core.agent import run_agent
source = inspect.getsource(run_agent)
if 'STEER_LOCAL_GATE_MODULE' not in source or 'local_transition_rejected' not in source:
    raise SystemExit('Installed tool adapter lacks the local transition patch; patch and reinstall it.')
PY
  asset_files+=(
    "$BENCHMARK_RL_TRAIN_DATA"
    "$BENCHMARK_CLIP_DATA"
    "$BENCHMARK_PROMPT_MANIFEST"
    "$BENCHMARK_SOURCE_ROOT/gen_tasks.jsonl"
    "$BENCHMARK_SOURCE_ROOT/gen_envs.jsonl"
    "$BENCHMARK_SOURCE_ROOT/gen_db.jsonl"
    "$BENCHMARK_SOURCE_ROOT/gen_sample.jsonl"
    "$BENCHMARK_SOURCE_ROOT/gen_verifier.pure_code.jsonl"
    "$TOOL_ENV_BIN"
  )
fi
if [[ -n "${BENCHMARK_ONLINE_DATA_COMMAND:-}" ]]; then
  [[ -n "$BENCHMARK_STATE_SNAPSHOT_COMMAND" ]] || {
    echo "missing exact state restore adapter: BENCHMARK_STATE_SNAPSHOT_COMMAND" >&2
    exit 2
  }
fi
if [[ "$BENCHMARK_ENGINE" == sdar ]]; then
  asset_files+=("$SDAR_ROOT/agent_system/environments/prompts/__init__.py")
  case "$BENCHMARK" in
    webshop)
      if [[ -n "${JAVA_HOME:-}" ]]; then
        [[ -x "$JAVA_HOME/bin/javac" ]] || { echo "WebShop requires a JDK: JAVA_HOME/bin/javac is missing" >&2; exit 2; }
      else
        command -v javac >/dev/null || { echo "WebShop requires a JDK; set JAVA_HOME or add javac to PATH" >&2; exit 2; }
      fi
      "$BENCHMARK_ENV_ROOT/bin/python" -c 'from pyserini.search.lucene import LuceneSearcher'
      ;;
    alfworld) asset_files+=("$ALFWORLD_DATA/json_2.1.1/train") ;;
    search_qa) asset_files+=("$SEARCH_TRAIN_PARQUET" "$SEARCH_EVAL_PARQUET") ;;
  esac
  "$BENCHMARK_ENV_ROOT/bin/python" -c 'import pandas, omegaconf, textworld, fast_downward'
fi
EVALUATOR=${BENCHMARK_EVAL_COMMAND:-}
if [[ "$BENCHMARK" == tau2_bench ]]; then
  EVALUATOR=${TAU2_EVAL_COMMAND:-$EVALUATOR}
fi
if [[ -z "$EVALUATOR" ]]; then
  case "$BENCHMARK" in
    bfcl_v4)
      "$BENCHMARK_ENV_ROOT/bin/python" -c 'import bfcl_eval._llm_response_generation; from bfcl_eval.eval_checker.multi_turn_eval.func_source_code.memory_vector import ENCODER, ENCODER_DIM; assert ENCODER_DIM > 0'
      [[ -n "${SERPAPI_API_KEY:-}" ]] || { echo "Full BFCL V4 requires SERPAPI_API_KEY for web search" >&2; exit 2; }
      ;;
    tau2_bench)
      "$BENCHMARK_ENV_ROOT/bin/python" -c 'import tau2.run'
      [[ -n "${TAU2_USER_MODEL:-}${TAU2_USER_MODEL_PATH:-}" ]] || { echo "Configure the tau2 user simulator" >&2; exit 2; }
      ;;
  esac
fi

for path in "${asset_files[@]}"; do
  [[ -e "$path" ]] || { echo "STEERDISTILL_PREFLIGHT_SIGNAL status=failed missing_asset=$path" >&2; exit 2; }
done

grep -q '^class SkillKDTrainer' "$ROOT/train/mytrainer.py"
grep -q 'skill_opd' "$ROOT/common/launch_train.sh"
if grep -qE 'Arctic-AWM|run_awm|AWM_|awm_' "$ROOT/README.md" "$ROOT/config.example.env" "$ROOT/benchmarks"/*.sh "$ROOT/benchmarks"/*.env "$ROOT/benchmarks"/*.md "$ROOT/requirements.lock"; then
  echo "STEERDISTILL_PREFLIGHT_SIGNAL status=failed stale_public_name=1" >&2
  exit 2
fi

for script in "$ROOT"/*.sh "$ROOT"/common/*.sh; do
  bash -n "$script"
done

if [[ -s "$INITIAL_RUNTIME_W4/quant_config.json" ]]; then
  runtime_status=ready
else
  runtime_status=not_prepared
fi
echo "STEERDISTILL_PREFLIGHT_SIGNAL status=passed method=steerdistill benchmark=$BENCHMARK runtime=$runtime_status root=$ROOT"
