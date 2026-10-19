#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
set -a
CONFIG=${STEER_CONFIG:-$ROOT/configs/steerdistill.example.env}
source "$CONFIG"
set +a
source "$ROOT/scripts/lib/run_paths.sh"
export TMPDIR=${TMPDIR:-$RUN_ROOT/tmp}
mkdir -p "$TMPDIR"

MODE=${1:-full}
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
