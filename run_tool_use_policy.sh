#!/usr/bin/env bash
set -euo pipefail
export VLLM_RPC_BASE_PATH=${VLLM_RPC_BASE_PATH:-/tmp}

MODEL=${1:?usage: run_tool_use_policy.sh MODEL OUTPUT PROMPT_MANIFEST GPU_IDS BASE_PORT DTYPE ATTEMPTS}
OUTPUT=${2:?}
PROMPTS=${3:?}
GPU_IDS=${4:?}
BASE_PORT=${5:?}
DTYPE=${6:?}
ATTEMPTS=${7:?}

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ASSET_ROOT="${STEER_ASSET_ROOT:?Set STEER_ASSET_ROOT}"
ENV=${ENV_ROOT:?Set ENV_ROOT}
: "${TOOL_ENV_BIN:?Set TOOL_ENV_BIN to the executable tool-use environment adapter}"
: "${TOOL_ENV_SOURCE_PATH:?Set TOOL_ENV_SOURCE_PATH to the tool-use environment source}"
MODEL_SERVING_NAME=${MODEL_SERVING_NAME:-Qwen3-8B}
[[ -x "$TOOL_ENV_BIN" ]] || { echo "missing tool-use environment executable: $TOOL_ENV_BIN" >&2; exit 2; }
TOOL_PARSER_ARGS=(--enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser qwen3)
if grep -q '"model_type"[[:space:]]*:[[:space:]]*"qwen3_5"' "$MODEL/config.json"; then
  TOOL_PARSER_ARGS=(--enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser qwen3 --language-model-only)
elif grep -q '"model_type"[[:space:]]*:[[:space:]]*"gemma4_unified_text"' "$MODEL/config.json"; then
  TOOL_PARSER_ARGS=(--enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4 --enforce-eager)
fi
IFS=, read -r -a GPUS <<< "$GPU_IDS"
mkdir -p "$OUTPUT/logs"
PIDS=()
cleanup() {
  for pid in "${PIDS[@]}"; do kill -TERM "$pid" 2>/dev/null || true; done
  wait "${PIDS[@]}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_server() {
  local gpu=$1 port=$2
  # Standard AWQ metadata is automatically dispatched to the compatible
  # AWQ-Marlin kernel by this vLLM build. Do not force a conflicting name.
  local quant=()
  CUDA_VISIBLE_DEVICES="$gpu" "${INFERENCE_ENV_ROOT:-$ENV}/bin/python" -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" --served-model-name "$MODEL_SERVING_NAME" \
    --host 127.0.0.1 --port "$port" --dtype "$DTYPE" \
    --max-model-len 32768 --gpu-memory-utilization 0.88 \
    --max-num-seqs "${MAX_NUM_SEQS:-8}" --max-logprobs 32 \
    --trust-remote-code "${TOOL_PARSER_ARGS[@]}" "${quant[@]}" >"$OUTPUT/logs/server-$port.log" 2>&1 &
  PIDS+=("$!")
}
ENDPOINTS=()
if [[ -n "${POLICY_ENDPOINTS:-}" ]]; then
  IFS=, read -r -a PERSISTENT_ENDPOINTS <<< "$POLICY_ENDPOINTS"
  for endpoint in "${PERSISTENT_ENDPOINTS[@]}"; do
    endpoint=${endpoint%/}
    endpoint=${endpoint%/v1}
    curl -fsS "$endpoint/health" >/dev/null
    ENDPOINTS+=("$endpoint/v1")
  done
  echo "SKILL_POLICY_RUNTIME_SIGNAL mode=persistent endpoints=${#ENDPOINTS[@]} model=$MODEL"
else
  for index in "${!GPUS[@]}"; do
    port=$((BASE_PORT + index))
    start_server "${GPUS[$index]}" "$port"
  done
  for index in "${!GPUS[@]}"; do
    port=$((BASE_PORT + index))
    for attempt in $(seq 1 300); do
      curl -fsS "http://127.0.0.1:$port/health" >/dev/null 2>&1 && break
      sleep 2
    done
    curl -fsS "http://127.0.0.1:$port/health" >/dev/null
    ENDPOINTS+=("http://127.0.0.1:$port/v1")
  done
fi

EVENT_ARGS=()
if [[ -n "${RESULT_EVENTS_DIR:-}" ]]; then
  EVENT_ARGS+=(--result-events-dir "$RESULT_EVENTS_DIR")
fi
"$ENV/bin/python" "$ROOT/verified_teacher/generate_verified.py" \
  --tool-env "$TOOL_ENV_BIN" \
  --source-dir "$TOOL_ENV_SOURCE_PATH" \
  --prompt-manifest "$PROMPTS" --output-dir "$OUTPUT" \
  --model "$MODEL_SERVING_NAME" --tokenizer "$MODEL" --endpoints "${ENDPOINTS[@]}" \
  --seed "${SEED:-42}" \
  --attempts "$ATTEMPTS" --workers-per-endpoint "${WORKERS_PER_ENDPOINT:-8}" \
  --max-iterations "${MAX_ITERATIONS:-30}" --max-tokens "${MAX_TOKENS:-32768}" \
  --temperature "${ROLLOUT_TEMPERATURE:-0.7}" --behavior-logprobs \
  "${EVENT_ARGS[@]}"

echo "SKILL_POLICY_ROLLOUT_SIGNAL model=$MODEL output=$OUTPUT gpus=$GPU_IDS attempts=$ATTEMPTS"
