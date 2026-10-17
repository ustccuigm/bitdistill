#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
set -a
CONFIG=${STEER_CONFIG:-$ROOT/config.example.env}
source "$CONFIG"
set +a
source "$ROOT/common/run_paths.sh"
export TMPDIR=${TMPDIR:-$RUN_ROOT/tmp}
mkdir -p "$TMPDIR"

MODE=${1:-full}
GPU_IDS=${GPU_IDS:-0,1,2,3,4,5,6,7}

case "$MODE" in
  prepare) bash "$ROOT/prepare_quant_assets.sh" "$TEACHER_MODEL" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA" ;;
  quantize)
    bash "$ROOT/prepare_quant_assets.sh" "$INITIAL_W4_MASTER" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA"
    bash "$ROOT/prepare_initial_runtime.sh" "$INITIAL_W4_MASTER" "$INITIAL_RUNTIME_W4"
    ;;
  train)
    "$INFERENCE_ENV_ROOT/bin/python" "$ROOT/common/check_runtime_support.py" "$TEACHER_MODEL"
    bash "$ROOT/prepare_quant_assets.sh" "$TEACHER_MODEL" "$CLIP_PATH" "$BENCHMARK_CLIP_DATA"
    bash "$ROOT/prepare_initial_runtime.sh" "$INITIAL_W4_MASTER" "$INITIAL_RUNTIME_W4"
    bash "$ROOT/run_online.sh" "$GPU_IDS"
    ;;
  eval)
    bash "$ROOT/benchmarks/evaluate.sh" "${EVAL_STEP:-latest}"
    ;;
  full)
    bash "$ROOT/preflight.sh"
    bash "$ROOT/run_benchmark.sh" quantize
    bash "$ROOT/run_benchmark.sh" train
    bash "$ROOT/run_benchmark.sh" eval
    ;;
  *) echo "usage: run_benchmark.sh [prepare|quantize|train|eval|full]" >&2; exit 2 ;;
esac
