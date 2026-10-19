#!/usr/bin/env bash
set -euo pipefail
STEP=${1:?usage: run_rollout_step.sh STEP GPU_IDS}
GPU_IDS=${2:?}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
TAG=$(printf 'step%06d' "$STEP")
STEP_DIR="${STEER_ONLINE_ROOT:?}/steps/$TAG"
mkdir -p "$STEP_DIR/train" "$STEP_DIR/logs"
if [[ -n "${GPU_POOL_LOCK:-}" ]]; then
  exec 9>"$GPU_POOL_LOCK"
  if [[ "$BENCHMARK_ENGINE" == tool_env ]]; then
    flock -x 9
  else
    flock -s 9
  fi
fi
"$ENV_ROOT/bin/python" "$ROOT/scripts/metadata/record_run_manifest.py" \
  --output "$STEP_DIR/run_manifest.json" --asset-root "$STEER_ASSET_ROOT" \
  --step "$STEP" --gpu-ids "$GPU_IDS"
if [[ "$BENCHMARK_ENGINE" == tool_env ]]; then
  bash "$ROOT/scripts/run/run_tool_rollout_step.sh" "$STEP" "$GPU_IDS"
else
  if [[ -n "${BENCHMARK_ONLINE_DATA_COMMAND:-}" ]]; then
    : "${BENCHMARK_STATE_SNAPSHOT_COMMAND:?custom adapters must support exact state restore}"
    ADAPTER=(bash -lc "$BENCHMARK_ONLINE_DATA_COMMAND")
  else
    [[ "$BENCHMARK_ENGINE" == sdar ]] || { echo "unsupported environment: $BENCHMARK_ENGINE" >&2; exit 2; }
    ADAPTER=("${BENCHMARK_ENV_ROOT:-$ENV_ROOT}/bin/python" "$ROOT/src/steerdistill/benchmarks/run_online.py")
  fi
  STEER_STEP="$STEP" STEER_STEP_DIR="$STEP_DIR" \
    STEER_BENCHMARK="$BENCHMARK" STEER_MODEL_FAMILY="$MODEL_FAMILY" \
    STEER_MODEL_PATH="$OPD_STUDENT_MASTER" STEER_RUNTIME_PATH="$OPD_STUDENT_RUNTIME" \
    STEER_TEACHER_MODEL="$TEACHER_MODEL" STEER_GPU_IDS="$GPU_IDS" \
    STEER_INITIAL_W4_MASTER="$INITIAL_W4_MASTER" STEER_CLIP_PATH="$CLIP_PATH" \
    STEER_STATE_RESTORE_REQUIRED=1 DISCOVERY_ATTEMPTS=1 \
    "${ADAPTER[@]}"
  "$ENV_ROOT/bin/python" "$ROOT/src/steerdistill/benchmarks/validate_adapter_output.py" \
    --data "$STEP_DIR/train/steer_opd.jsonl" --benchmark "$BENCHMARK" --step "$STEP"
fi
"$ENV_ROOT/bin/python" "$ROOT/scripts/data/audit_training_data.py" \
  --data "$STEP_DIR/train/steer_opd.jsonl" --store "$STEER_SKILL_STORE"
if [[ -n "${GPU_POOL_LOCK:-}" ]]; then
  flock -u 9
  flock -x 9
fi
bash "$ROOT/scripts/train/train_online_step.sh" "$STEP" "${TRAIN_GPU_IDS:-$GPU_IDS}"
