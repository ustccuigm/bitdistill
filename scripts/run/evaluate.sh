#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
source "$ROOT/scripts/lib/run_paths.sh"
STEP=${1:-latest}
if [[ "$STEP" == latest ]]; then
  RECEIPT="$STEER_ONLINE_ROOT/latest.json"
else
  [[ "$STEP" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid evaluation step: $STEP" >&2; exit 2; }
  RECEIPT="$STEER_ONLINE_ROOT/steps/$(printf 'step%06d' "$STEP")/complete.json"
fi
[[ -s "$RECEIPT" ]] || { echo "Missing trained runtime receipt: $RECEIPT" >&2; exit 2; }
SELECTION=$("$ENV_ROOT/bin/python" "$ROOT/scripts/lib/resolve_online_checkpoint.py" \
  --root "$STEER_ONLINE_ROOT" --step "$STEP")
mapfile -t SELECTED <<< "$SELECTION"
export EVAL_RUNTIME=${SELECTED[0]}
TAG=${SELECTED[1]}
export EVAL_OUTPUT_DIR="$RUN_ROOT/eval/$TAG"
export EVAL_MODEL_NAME="$MODEL_SERVING_NAME"
[[ -s "$EVAL_RUNTIME/quant_config.json" ]] || { echo "Missing trained runtime: $EVAL_RUNTIME" >&2; exit 2; }
COMMAND=${BENCHMARK_EVAL_COMMAND:-}
if [[ "$BENCHMARK" == tau2_bench ]]; then
  COMMAND=${TAU2_EVAL_COMMAND:-$COMMAND}
fi
mkdir -p "$EVAL_OUTPUT_DIR"
TASK_ARGS=()
if [[ -n "${EVAL_TASK_IDS:-}" ]]; then
  [[ -s "$EVAL_TASK_IDS" ]] || { echo "Missing evaluation task selection: $EVAL_TASK_IDS" >&2; exit 2; }
  TASK_ARGS=(--task-ids "$EVAL_TASK_IDS")
fi
# Search QA is only valid when the pinned retriever is reachable.  Do not
# allow an adapter to turn retrieval failures into completed benchmark rows.
if [[ "$BENCHMARK" == "search_qa" ]]; then
  RETRIEVER_URL=${SEARCH_RETRIEVER_URL:-http://127.0.0.1:8000/retrieve}
  RETRIEVER_URL=${RETRIEVER_URL%/retrieve}
  curl --fail --silent --show-error --max-time 10 "$RETRIEVER_URL/docs" >/dev/null || {
    echo "Search QA retriever is unavailable: $RETRIEVER_URL" >&2
    exit 2
  }
fi
# Only the student artifact is supplied. Evaluators must save their official
# scores and trajectories in EVAL_OUTPUT_DIR and return nonzero on failure.
if [[ -n "$COMMAND" ]]; then
  bash -lc "$COMMAND" 2>&1 | tee "$EVAL_OUTPUT_DIR/eval.log"
elif [[ "$BENCHMARK_ENGINE" == sdar ]]; then
  "$BENCHMARK_ENV_ROOT/bin/python" "$ROOT/src/steerdistill/benchmarks/evaluate_sdar.py" \
    --benchmark "$BENCHMARK" --runtime "$EVAL_RUNTIME" --model "$EVAL_MODEL_NAME" \
    --output "$EVAL_OUTPUT_DIR" --gpus "${EVAL_GPU_IDS:-0}" \
    --workers "${EVAL_WORKERS:-4}" "${TASK_ARGS[@]}" 2>&1 | tee "$EVAL_OUTPUT_DIR/eval.log"
else
  case "$BENCHMARK" in
    bfcl_v4) EVAL_SCRIPT=evaluate_bfcl.py ;;
    tau2_bench) EVAL_SCRIPT=evaluate_tau2.py ;;
    *) echo "Unsupported evaluation benchmark: $BENCHMARK" >&2; exit 2 ;;
  esac
  "$BENCHMARK_ENV_ROOT/bin/python" "$ROOT/src/steerdistill/benchmarks/$EVAL_SCRIPT" \
    --runtime "$EVAL_RUNTIME" --model "$EVAL_MODEL_NAME" --output "$EVAL_OUTPUT_DIR" \
    --gpus "${EVAL_GPU_IDS:-0}" "${TASK_ARGS[@]}" 2>&1 | tee "$EVAL_OUTPUT_DIR/eval.log"
fi
echo "STEER_EVAL_SIGNAL status=command_completed benchmark=$BENCHMARK step=$TAG output=$EVAL_OUTPUT_DIR"
