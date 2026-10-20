#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
usage() {
  echo "usage: run_benchmark.sh [prepare|quantize|train|eval|full] [--model MODEL] [--benchmark BENCHMARK]"
  echo "models: qwen3_8b, qwen3_5_4b, gemma4_12b"
  echo "benchmarks: bfcl_v4, tau2_bench, webshop, alfworld, search_qa"
}
MODE=full
CLI_MODEL=
CLI_BENCHMARK=
if [[ $# -gt 0 && "$1" != -* ]]; then
  MODE=$1
  shift
fi
case "$MODE" in
  prepare|quantize|train|eval|full) ;;
  *) usage >&2; exit 2 ;;
esac
while (( $# )); do
  case "$1" in
    --model|--benchmark)
      [[ $# -ge 2 && -n "$2" && "$2" != -* ]] || { echo "Missing value for $1" >&2; exit 2; }
      if [[ "$1" == --model ]]; then
        case "$2" in qwen3_8b|qwen3_5_4b|gemma4_12b) ;; *) echo "Unknown model: $2" >&2; exit 2 ;; esac
        export MODEL_FAMILY="$2"
        CLI_MODEL=$2
      else
        case "$2" in bfcl_v4|tau2_bench|webshop|alfworld|search_qa) ;; *) echo "Unknown benchmark: $2" >&2; exit 2 ;; esac
        export BENCHMARK="$2"
        CLI_BENCHMARK=$2
      fi
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done
source "$ROOT/scripts/lib/load_config.sh"
if [[ -n "$CLI_MODEL" && "$MODEL_FAMILY" != "$CLI_MODEL" ]] ||
   [[ -n "$CLI_BENCHMARK" && "$BENCHMARK" != "$CLI_BENCHMARK" ]]; then
  echo "Configuration overrides the requested route; keep the template's default-value assignments for MODEL_FAMILY and BENCHMARK." >&2
  exit 2
fi
source "$ROOT/scripts/lib/run_paths.sh"
export TMPDIR=${TMPDIR:-$RUN_ROOT/tmp}
mkdir -p "$TMPDIR"

GPU_IDS=${GPU_IDS:-0,1,2,3,4,5,6,7}

case "$MODE" in
  prepare) bash "$ROOT/scripts/prepare/prepare_quant_assets.sh" "$TEACHER_MODEL" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA" ;;
  quantize)
    bash "$ROOT/scripts/prepare/prepare_quant_assets.sh" "$INITIAL_W4_MASTER" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA"
    bash "$ROOT/scripts/prepare/prepare_initial_runtime.sh" "$INITIAL_W4_MASTER" "$INITIAL_RUNTIME_W4"
    ;;
  train)
    "$INFERENCE_ENV_ROOT/bin/python" "$ROOT/scripts/lib/check_runtime_support.py" "$TEACHER_MODEL"
    bash "$ROOT/scripts/prepare/prepare_quant_assets.sh" "$TEACHER_MODEL" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA"
    bash "$ROOT/scripts/prepare/prepare_initial_runtime.sh" "$INITIAL_W4_MASTER" "$INITIAL_RUNTIME_W4"
    bash "$ROOT/scripts/run/run_online.sh" "$GPU_IDS"
    ;;
  eval)
    bash "$ROOT/scripts/run/evaluate.sh" "${EVAL_STEP:-latest}"
    ;;
  full)
    bash "$ROOT/scripts/validate/preflight.sh"
    bash "$ROOT/scripts/run/run_benchmark.sh" quantize
    bash "$ROOT/scripts/run/run_benchmark.sh" train
    bash "$ROOT/scripts/run/run_benchmark.sh" eval
    ;;
  *) echo "usage: run_benchmark.sh [prepare|quantize|train|eval|full]" >&2; exit 2 ;;
esac
