#!/usr/bin/env bash
set -euo pipefail

MODEL=${1:?usage: analyze_with_server.sh MODEL PAIRS STORE GPU PORT POLICY_ID}
PAIRS=${2:?}
STORE=${3:?}
GPU=${4:?}
PORT=${5:?}
POLICY_ID=${6:?}
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV=${ENV_ROOT:?Set ENV_ROOT}
LOG_DIR=$(dirname "$STORE")/logs
mkdir -p "$LOG_DIR"
if [[ -n "${ANALYZER_ENDPOINT:-}" ]]; then
  ENDPOINT=${ANALYZER_ENDPOINT%/}
  ENDPOINT=${ENDPOINT%/v1}
  curl -fsS "$ENDPOINT/health" >/dev/null
  "$ENV/bin/python" "$ROOT/analyze_skills.py" \
    --pairs "$PAIRS" --store "$STORE" --api-url "$ENDPOINT/v1" \
    --api-key EMPTY --model "${ANALYZER_SERVED_MODEL:-${MODEL_SERVING_NAME:-Qwen3-8B}}" \
    --analyzer-policy "$POLICY_ID"
  exit 0
fi
CUDA_VISIBLE_DEVICES="$GPU" "${INFERENCE_ENV_ROOT:-$ENV}/bin/python" -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name skill-analyzer \
  --host 127.0.0.1 --port "$PORT" --dtype bfloat16 \
  --max-model-len 32768 --gpu-memory-utilization 0.88 \
  --max-num-seqs 8 --trust-remote-code >"$LOG_DIR/analyzer-$PORT.log" 2>&1 &
PID=$!
trap 'kill -TERM "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true' EXIT INT TERM
for _ in $(seq 1 300); do
  curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  sleep 2
done
curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null
"$ENV/bin/python" "$ROOT/analyze_skills.py" \
  --pairs "$PAIRS" --store "$STORE" --api-url "http://127.0.0.1:$PORT/v1" \
  --api-key EMPTY --model skill-analyzer --analyzer-policy "$POLICY_ID"
