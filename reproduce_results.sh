#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONFIG=${STEER_CONFIG:-$ROOT/config.example.env}
set -a
source "$CONFIG"
set +a
: "${STEER_ASSET_ROOT:?Set STEER_ASSET_ROOT}"
: "${ENV_ROOT:?Set ENV_ROOT}"
: "${STEERDISTILL_ROOT:=$ROOT}"

mode=${1:-smoke}
case "$mode" in
  smoke)
    tmp=${SMOKE_ROOT:-/tmp/steerdistill-smoke}
    rm -rf "$tmp"
    mkdir -p "$tmp"
    head -n 1 "$PROMPT_MANIFEST" > "$tmp/prompts.jsonl"
    "$ENV_ROOT/bin/python" "$ROOT/record_run_manifest.py" \
      --output "$tmp/run_manifest.json" --asset-root "$STEER_ASSET_ROOT" \
      --step 0 --gpu-ids "${GPU_IDS:-0}"
    WORKERS_PER_ENDPOINT=${WORKERS_PER_ENDPOINT:-1} \
    MAX_NUM_SEQS=${MAX_NUM_SEQS:-1} \
    MAX_ITERATIONS=${MAX_ITERATIONS:-2} \
    MAX_TOKENS=${MAX_TOKENS:-128} \
      bash "$ROOT/run_tool_use_policy.sh" "$INITIAL_RUNTIME_W4" \
      "$tmp/rollout" "$tmp/prompts.jsonl" "${GPU_IDS:-0}" \
      "${BASE_PORT:-35510}" bfloat16 1
    test -s "$tmp/rollout/attempts.jsonl"
    echo "STEER_REPRODUCE_SIGNAL mode=smoke status=passed output=$tmp"
    ;;
  full)
    bash "$ROOT/run_benchmark.sh" full
    echo "STEER_REPRODUCE_SIGNAL mode=full status=completed"
    ;;
  *)
    echo "usage: reproduce_results.sh [smoke|full]" >&2
    exit 2
    ;;
esac
