#!/usr/bin/env bash
set -euo pipefail

MODEL=${1:?usage: run_skill_aware_validation.sh MODEL STORE OUTPUT PROMPTS GPU_IDS BASE_PORT ATTEMPTS STEP}
STORE=${2:?}
OUTPUT=${3:?}
PROMPTS=${4:?}
GPU_IDS=${5:?}
BASE_PORT=${6:?}
ATTEMPTS=${7:?}
STEP=${8:?}
PROXY_MODE=${SKILL_PROXY_MODE:-steer}
if [[ "$PROXY_MODE" != "steer" ]]; then
  echo "Only W4 steering is supported by this training route" >&2
  exit 2
fi
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ASSET_ROOT="${STEER_ASSET_ROOT:?Set STEER_ASSET_ROOT}"
ENV=${ENV_ROOT:?Set ENV_ROOT}
# The external adapter chooses its executable; the source release never
# assumes a local checkout name or virtual-environment layout.
TOOL_ENV_BIN=${TOOL_ENV_BIN:?Set TOOL_ENV_BIN to the tool-use environment executable}
TOOL_ENV_SOURCE_PATH=${TOOL_ENV_SOURCE_PATH:-$ASSET_ROOT/common/data/tool_use_environment}
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
ENDPOINTS=()
UPSTREAMS=()
if [[ -n "${W4_HOT_ENDPOINTS:-}" ]]; then
  IFS=, read -r -a UPSTREAMS <<< "$W4_HOT_ENDPOINTS"
else
  for index in "${!GPUS[@]}"; do
    server_port=$((BASE_PORT + index * 2))
    CUDA_VISIBLE_DEVICES="${GPUS[$index]}" "${INFERENCE_ENV_ROOT:-$ENV}/bin/python" \
      -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name "$MODEL_SERVING_NAME" \
      --host 127.0.0.1 --port "$server_port" --dtype bfloat16 \
      --max-model-len 32768 --gpu-memory-utilization 0.88 \
      --max-num-seqs "${MAX_NUM_SEQS:-8}" --max-logprobs 32 --trust-remote-code \
      "${TOOL_PARSER_ARGS[@]}" \
      >"$OUTPUT/logs/server-$server_port.log" 2>&1 &
    PIDS+=("$!")
    for _ in $(seq 1 300); do
      curl -fsS "http://127.0.0.1:$server_port/health" >/dev/null 2>&1 && break
      sleep 2
    done
    UPSTREAMS+=("http://127.0.0.1:$server_port")
  done
fi
for index in "${!UPSTREAMS[@]}"; do
  proxy_port=$((BASE_PORT + index * 2 + 1))
  upstream=${UPSTREAMS[$index]%/}
  curl -fsS "$upstream/health" >/dev/null
  PROXY_ARGS=(--mode "$PROXY_MODE")
  "$ENV/bin/python" "$ROOT/skill_proxy.py" \
    --upstream "$upstream" --store "$STORE" \
    --role-log "$OUTPUT/proxy-$proxy_port.jsonl" --port "$proxy_port" \
    --step "$STEP" \
    "${PROXY_ARGS[@]}" \
    >"$OUTPUT/logs/proxy-$proxy_port.log" 2>&1 &
  proxy_pid=$!
  PIDS+=("$proxy_pid")
  ready=0
  for _ in $(seq 1 120); do
    kill -0 "$proxy_pid" 2>/dev/null || break
    if curl -fsS "http://127.0.0.1:$proxy_port/health" >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  (( ready == 1 )) || {
    echo "Skill proxy failed readiness on port $proxy_port" >&2
    exit 22
  }
  ENDPOINTS+=("http://127.0.0.1:$proxy_port/v1")
done
SNAPSHOT_MANIFEST="$OUTPUT/snapshot_manifest.jsonl"
"$ENV/bin/python" "$ROOT/build_snapshot_manifest.py"   --store "$STORE" --output "$SNAPSHOT_MANIFEST" --step "$STEP"
"$ENV/bin/python" "$ROOT/verified_teacher/generate_verified.py" \
  --tool-env "$TOOL_ENV_BIN" \
  --source-dir "$TOOL_ENV_SOURCE_PATH" --prompt-manifest "$PROMPTS" \
  --output-dir "$OUTPUT" --model "$MODEL_SERVING_NAME" --tokenizer "$MODEL" --endpoints "${ENDPOINTS[@]}" \
  --seed "${SEED:-42}" \
  --attempts "$ATTEMPTS" --workers-per-endpoint "${WORKERS_PER_ENDPOINT:-8}" \
  --max-iterations "${MAX_ITERATIONS:-30}" --max-tokens "${MAX_TOKENS:-32768}" \
  --temperature "${ROLLOUT_TEMPERATURE:-0.7}" --behavior-logprobs \
  --snapshot-manifest "$SNAPSHOT_MANIFEST" --local-transition-gate
TASK_ARGS=()
if [[ -n "${SKILL_TASK_KEY:-}" ]]; then
  TASK_ARGS+=(--task-key "$SKILL_TASK_KEY")
fi
"$ENV/bin/python" "$ROOT/validate_skills.py" \
  --runs "$OUTPUT/runs" --store "$STORE" --step "$STEP" --policy "$MODEL" \
  --role-log-root "$OUTPUT" "${TASK_ARGS[@]}"
