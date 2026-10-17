#!/usr/bin/env bash
set -euo pipefail
export VLLM_RPC_BASE_PATH=${VLLM_RPC_BASE_PATH:-/tmp}
STEP=${1:?usage: run_tool_rollout_step.sh STEP GPU_IDS}
GPU_IDS=${2:?}
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV=${ENV_ROOT:?}
ROUTE="$ROOT"
TAG=$(printf 'step%06d' "$STEP")
STEP_DIR="${STEER_ONLINE_ROOT:?}/steps/$TAG"
STORE=${STEER_SKILL_STORE:?}
PROMPTS=${PROMPT_MANIFEST:?}
TEACHER=${TEACHER_MODEL:?}
MASTER=${OPD_STUDENT_MASTER:?}
RUNTIME=${OPD_STUDENT_RUNTIME:?}
mkdir -p "$STEP_DIR/logs" "$(dirname "$STORE")"
IFS=, read -r -a GPUS <<< "$GPU_IDS"
(( ${#GPUS[@]} >= 8 )) || {
  echo "streaming repair requires eight GPUs (4 W4 + 2 shadow + 2 teacher)" >&2
  exit 2
}
W4_GPUS=("${GPUS[@]:0:4}")
SHADOW_GPUS=("${GPUS[@]:4:2}")
TEACHER_GPUS=("${GPUS[@]:6:2}")
SERVER_PIDS=()
OTHER_PIDS=()

cleanup() {
  trap - EXIT INT TERM
  for pid in "${OTHER_PIDS[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  for pid in "${SERVER_PIDS[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  wait "${OTHER_PIDS[@]}" "${SERVER_PIDS[@]}" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_server() {
  local gpu=$1 model=$2 port=$3 engine_port=$4 dtype=$5 label=$6
  # vLLM otherwise samples an internal torch.distributed rendezvous port.
  # A vLLM replica consumes more than one adjacent internal port. Keep the
  # bases twenty ports apart so eight replicas cannot overlap each other.
  if ss -H -ltn "sport = :$engine_port" | grep -q .; then
    echo "vLLM engine port already in use: $engine_port" >&2
    exit 2
  fi
  local tool_args=()
  if grep -q '"model_type"[[:space:]]*:[[:space:]]*"qwen3_5"' "$model/config.json"; then
    tool_args=(--enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser qwen3 --language-model-only)
  elif grep -q '"model_type"[[:space:]]*:[[:space:]]*"gemma4_unified_text"' "$model/config.json"; then
    tool_args=(--enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4 --enforce-eager)
  elif [[ "$label" == "w4" || "$label" == "shadow" || "$label" == "teacher" ]]; then
    tool_args=(--enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser qwen3)
  fi
  local attempts=${VLLM_START_RETRIES:-3}
  local attempt pid log
  for attempt in $(seq 1 "$attempts"); do
    log="$STEP_DIR/logs/${label}-${port}.log"
    if (( attempt > 1 )); then
      log="$STEP_DIR/logs/${label}-${port}.retry${attempt}.log"
    fi
    CUDA_VISIBLE_DEVICES="$gpu" VLLM_PORT="$engine_port" setsid "${INFERENCE_ENV_ROOT:-$ENV}/bin/python" \
      -m vllm.entrypoints.openai.api_server \
      --model "$model" --served-model-name "${MODEL_SERVING_NAME:-Qwen3-8B}" \
      --host 127.0.0.1 --port "$port" --dtype "$dtype" \
      --max-model-len "${MODEL_MAX_LENGTH:-32768}" --gpu-memory-utilization "${STREAM_GPU_MEMORY_UTILIZATION:-0.82}" \
      --max-num-seqs "${MAX_NUM_SEQS:-8}" --max-logprobs 32 --trust-remote-code "${tool_args[@]}" \
      >"$log" 2>&1 &
    pid=$!
    for _ in $(seq 1 300); do
      if curl -fsS "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
        SERVER_PIDS+=("$pid")
        echo "STEER_VLLM_READY_SIGNAL label=$label gpu=$gpu port=$port attempt=$attempt"
        return 0
      fi
      kill -0 "$pid" 2>/dev/null || break
      sleep 2
    done
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    echo "STEER_VLLM_RETRY_SIGNAL label=$label gpu=$gpu port=$port attempt=$attempt" >&2
    sleep 5
  done
  echo "vLLM failed readiness after $attempts attempts: $label on GPU $gpu" >&2
  return 1
}

W4_ENDPOINTS=()
for index in "${!W4_GPUS[@]}"; do
  port=$((34000 + index)); engine_port=$((45000 + 20 * index))
  start_server "${W4_GPUS[$index]}" "$RUNTIME" "$port" "$engine_port" bfloat16 w4 || exit 2
  W4_ENDPOINTS+=("http://127.0.0.1:$port")
done
SHADOW_ENDPOINTS=()
for index in "${!SHADOW_GPUS[@]}"; do
  port=$((34100 + index)); engine_port=$((45200 + 20 * index))
  start_server "${SHADOW_GPUS[$index]}" "$MASTER" "$port" "$engine_port" bfloat16 shadow || exit 2
  SHADOW_ENDPOINTS+=("http://127.0.0.1:$port")
done
TEACHER_ENDPOINTS=()
for index in "${!TEACHER_GPUS[@]}"; do
  port=$((34200 + index)); engine_port=$((45400 + 20 * index))
  start_server "${TEACHER_GPUS[$index]}" "$TEACHER" "$port" "$engine_port" bfloat16 teacher || exit 2
  TEACHER_ENDPOINTS+=("http://127.0.0.1:$port")
done

join_by_comma() { local IFS=,; echo "$*"; }
W4_CSV=$(join_by_comma "${W4_ENDPOINTS[@]}")
SHADOW_CSV=$(join_by_comma "${SHADOW_ENDPOINTS[@]}")
TEACHER_CSV=$(join_by_comma "${TEACHER_ENDPOINTS[@]}")
echo "STEER_STREAM_RUNTIME_SIGNAL step=$STEP w4=${#W4_ENDPOINTS[@]} shadow=${#SHADOW_ENDPOINTS[@]} teacher=${#TEACHER_ENDPOINTS[@]}"

EVENTS="$STEP_DIR/events"
DISCOVERY_DONE="$STEP_DIR/discovery.done"
RESUME_DISCOVERY=${RESUME_DISCOVERY:-0}
RESUME_SYSTEM_ERRORS=${RESUME_SYSTEM_ERRORS:-0}
REPAIR_RESUME_ARGS=()
if [[ "$RESUME_SYSTEM_ERRORS" == "1" ]]; then
  REPAIR_RESUME_ARGS+=(--resume-system-errors)
fi
if [[ "$RESUME_DISCOVERY" == "1" ]]; then
  [[ -d "$EVENTS" ]] || { echo "missing discovery events for resume: $EVENTS" >&2; exit 2; }
  touch "$DISCOVERY_DONE"
  echo "STEER_DISCOVERY_RESUME_SIGNAL step=$STEP events=$(find "$EVENTS" -maxdepth 1 -type f -name '*.json' | wc -l)"
else
  rm -f "$DISCOVERY_DONE"
fi
setsid "$ENV/bin/python" "$ROUTE/stream_repair.py" \
  --route "$ROUTE" --events-dir "$EVENTS" --discovery-done "$DISCOVERY_DONE" \
  --state "$STEP_DIR/stream.state.jsonl" --work-root "$STEP_DIR/repairs" \
  --prompt-manifest "$PROMPTS" --store "$STORE" --runtime "$RUNTIME" \
  --master "$MASTER" --teacher "$TEACHER" --step "$STEP" \
  --w4-endpoints "$W4_CSV" --shadow-endpoints "$SHADOW_CSV" \
  --teacher-endpoints "$TEACHER_CSV" \
  --counterfactual-attempts "${COUNTERFACTUAL_ATTEMPTS:-4}" \
  --validation-attempts "${VALIDATION_ATTEMPTS:-4}" \
  --repair-workers "${REPAIR_WORKERS:-4}" \
  --python "$ENV/bin/python" \
  "${REPAIR_RESUME_ARGS[@]}" \
  >"$STEP_DIR/logs/stream-repair.log" 2>&1 &
REPAIR_PID=$!
OTHER_PIDS+=("$REPAIR_PID")

if [[ "$RESUME_DISCOVERY" != "1" ]]; then
  POLICY_ENDPOINTS="$W4_CSV" RESULT_EVENTS_DIR="$EVENTS" \
    bash "$ROUTE/run_tool_use_policy.sh" "$RUNTIME" "$STEP_DIR/plain" "$PROMPTS" \
    "$GPU_IDS" 34000 bfloat16 "1"
  touch "$DISCOVERY_DONE"
fi
if ! wait "$REPAIR_PID"; then
  echo "stream repair consumer failed; see $STEP_DIR/logs/stream-repair.log" >&2
  exit 2
fi
OTHER_PIDS=()

if [[ -s "$STORE" ]]; then
  "$ENV/bin/python" "$ROUTE/update_skill_status.py" --plain-runs "$STEP_DIR/plain/runs" \
    --store "$STORE" --step "$STEP" --policy "$RUNTIME"
fi

# Free inference replicas before allocating the eight-GPU learner.
for pid in "${SERVER_PIDS[@]}"; do
  kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
done
wait "${SERVER_PIDS[@]}" 2>/dev/null || true
SERVER_PIDS=()

mkdir -p "$STEP_DIR/train"
"$ENV/bin/python" "$ROUTE/materialize_training_data.py" \
  --plain-runs "$STEP_DIR/plain/runs" --skill-runs "$STEP_DIR/repairs" \
  --teacher-runs "$STEP_DIR/repairs" --store "$STORE" \
  --output "$STEP_DIR/train/steer_opd.jsonl" --step "$STEP" \
  --repair-state "$STEP_DIR/stream.state.jsonl"
"$ENV/bin/python" "$ROUTE/audit_training_data.py" \
  --data "$STEP_DIR/train/steer_opd.jsonl" --store "$STORE"
echo "STEER_ROLLOUT_SIGNAL step=$STEP status=ready scheduler=streaming"
