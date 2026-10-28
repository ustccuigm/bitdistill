#!/usr/bin/env bash
set -euo pipefail
STEP=${1:?usage: train_online_step.sh STEP GPU_IDS}
GPU_IDS=${2:?}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
source "$ROOT/scripts/lib/precision.sh"
ENV=${ENV_ROOT:?}
TAG=$(printf 'step%06d' "$STEP")
RUN=${STEER_ONLINE_ROOT:?}
DATA="$RUN/steps/$TAG/train/steer_opd.jsonl"
STUDENT=${OPD_STUDENT_MASTER:?}
PREVIOUS=${OPD_PREVIOUS_OPTIMIZER_STEP:?}
STEPS=$((PREVIOUS + 1))
LEARNER="$RUN/checkpoints/learner"
HF="$RUN/checkpoints/student-$TAG-hf"
RUNTIME="$RUN/checkpoints/student-$TAG-${RUNTIME_SUFFIX:-awq-runtime}"
LOG="$RUN/steps/$TAG/train"
IFS=, read -r -a GPUS <<< "$GPU_IDS"
WORLD_SIZE=${#GPUS[@]}
GLOBAL_BATCH=${OPD_GLOBAL_BATCH_SIZE:-16}
MICRO_BATCH=${OPD_MICRO_BATCH_SIZE:-1}
[[ -s "$DATA" ]] || { echo "missing fresh trajectory data: $DATA" >&2; exit 2; }
for path in "$HF" "$RUNTIME"; do
  [[ ! -e "$path" ]] || { echo "partial export exists: $path" >&2; exit 2; }
done
"$ENV/bin/python" "$ROOT/scripts/data/audit_training_data.py" --data "$DATA" --store "$STEER_SKILL_STORE"
UPDATES=$("$ENV/bin/python" "$ROOT/src/steerdistill/training/online_step.py" --data "$DATA" \
  --global-batch-size "$GLOBAL_BATCH" --micro-batch-size "$MICRO_BATCH" \
  --world-size "$WORLD_SIZE" --expected-trajectories "${OPD_EXPECTED_TRAJECTORIES:-$GLOBAL_BATCH}" \
  --prompts "$RUN/steps/$TAG/prompts.jsonl" --benchmark "$BENCHMARK")
[[ "$UPDATES" == 1 ]] || { echo "expected exactly one optimizer update" >&2; exit 2; }
"$ENV/bin/python" "$ROOT/scripts/metadata/record_training_manifest.py" \
  --data "$DATA" --tokenizer "$STUDENT" --output "$LOG/training_manifest.json" \
  --run-manifest "$RUN/steps/$TAG/run_manifest.json" --max-length "${MODEL_MAX_LENGTH:-32768}"
CLIP_ARGS=(APPLY_CLIP=False)
RESUME=False
if (( PREVIOUS == 0 )); then
  [[ ! -e "$LEARNER" ]] || { echo "unexpected initial learner: $LEARNER" >&2; exit 2; }
  CLIP_ARGS=(APPLY_CLIP=True CLIP_PATH="${CLIP_PATH:?}")
else
  FOUND=$("$ENV/bin/python" "$ROOT/scripts/validate/check_training_signal.py" --latest-step "$LEARNER")
  (( FOUND == PREVIOUS )) || { echo "optimizer/rollout lineage mismatch" >&2; exit 2; }
  [[ -d "$LEARNER/checkpoint-$PREVIOUS/optimizer_0" && -s "$LEARNER/checkpoint-$PREVIOUS/scheduler.pt" ]] || {
    echo "missing optimizer or scheduler state" >&2; exit 2;
  }
  RESUME=True
  "$ENV/bin/python" "$ROOT/scripts/validate/check_optimizer_state.py" \
    --checkpoint "$LEARNER/checkpoint-$PREVIOUS" --step "$PREVIOUS"
fi
RECORDS=$(wc -l < "$DATA")
# Qwen3 uses FSDP activation checkpointing. The hybrid Qwen3.5 decoder uses
# model-level reentrant checkpointing instead; never enable both wrappers.
if [[ "${MODEL_FAMILY:-}" == qwen3_5_4b ]]; then
  GRADIENT_CHECKPOINTING=${GRADIENT_CHECKPOINTING:-True}
else
  GRADIENT_CHECKPOINTING=${GRADIENT_CHECKPOINTING:-False}
fi
STEER_LOGITS_CHUNK_SIZE=${STEER_LOGITS_CHUNK_SIZE:-1024}
STEER_BACKWARD_CHUNKS=${STEER_BACKWARD_CHUNKS:-True}
TURN_BATCH_SIZE=${ONLINE_TURN_BATCH_SIZE:-1}
# HF transports one pre-sharded trajectory batch; actual turn forwards use
# ONLINE_TURN_BATCH_SIZE rows are forwarded at a time and accumulated over
# every turn before a single update.
env CUDA_VISIBLE_DEVICES="$GPU_IDS" PYTHON_BIN="$ENV/bin/python" ACCELERATE_BIN="$ENV/bin/accelerate" \
BITS="${BITS:-4}" ACTIVATION_BITS="${ACTIVATION_BITS:-16}" GROUP_SIZE="${GROUP_SIZE:-64}" QUANT_TYPE="int${BITS:-4}-asym" "${CLIP_ARGS[@]}" \
MODEL_PATH="$STUDENT" SKILL_REFERENCE_MODEL_PATH="$STUDENT" TEACHER_MODEL_PATH="$TEACHER_MODEL" \
SKILL_DATA_PATH="$DATA" OUTPUT_DIR_OVERRIDE="$LEARNER" LOG_DIR_OVERRIDE="$LOG" \
NUM_GPUS="$WORLD_SIZE" DISTRIBUTED_BACKEND=fsdp2 TRAJECTORY_ONLINE=True \
  PER_DEVICE_TRAIN_BATCH_SIZE=1 GRADIENT_ACCUMULATION_STEPS=1 \
GRADIENT_CHECKPOINTING="$GRADIENT_CHECKPOINTING" \
STEER_LOGITS_CHUNK_SIZE="$STEER_LOGITS_CHUNK_SIZE" STEER_BACKWARD_CHUNKS="$STEER_BACKWARD_CHUNKS" \
MODEL_MAX_LENGTH="${MODEL_MAX_LENGTH:-32768}" MAX_TRAIN_SAMPLES="$RECORDS" \
MAX_STEPS="$STEPS" SAVE_STEPS=1 SAVE_TOTAL_LIMIT=2 \
MAY_RESUME="$RESUME" SKIP_FINAL_SAVE=True \
LEARNING_RATE="${LEARNING_RATE:-8e-6}" LR_SCHEDULER_TYPE=constant WARMUP_STEPS=0 \
MAIN_PROCESS_PORT="${TRAIN_PORT:-32600}" bash "$ROOT/scripts/train/train.sh"
CHECKPOINT="$LEARNER/checkpoint-$STEPS"
"$ENV/bin/python" "$ROOT/scripts/validate/check_optimizer_state.py" --checkpoint "$CHECKPOINT" \
  --step "$STEPS" --output "$LOG/optimizer_signal.json"
"$ENV/bin/python" "$ROOT/scripts/validate/check_training_signal.py" --state "$CHECKPOINT/trainer_state.json" \
  --steps "$STEPS" --previous-step "$PREVIOUS" --output "$LOG/training_signal.json"
PYTHON_BIN="$ENV/bin/python" MODEL_PATH="$STUDENT" BITS="${BITS:-4}" ACTIVATION_BITS="${ACTIVATION_BITS:-16}" GROUP_SIZE="${GROUP_SIZE:-64}" \
QUANT_TYPE="int${BITS:-4}-asym" WRITE_QUANTIZER_METADATA=1 \
  bash "$ROOT/scripts/lib/merge_fsdp_checkpoint.sh" "$HF" "$CHECKPOINT"
"$ENV/bin/python" "$ROOT/src/steerdistill/training/convert_hf_to_awq_runtime.py" \
  --source "$HF" --output "$RUNTIME" --bits "${BITS:-4}" --group-size "${GROUP_SIZE:-64}" --activation-bits "${ACTIVATION_BITS:-16}"
"$ENV/bin/python" "$ROOT/scripts/validate/validate_awq_runtime.py" \
  --source "$HF" --runtime "$RUNTIME" --bits "${BITS:-4}" --group-size "${GROUP_SIZE:-64}" --activation-bits "${ACTIVATION_BITS:-16}" --layers 0
echo "STEER_ONLINE_EXPORT_SIGNAL step=$STEP optimizer_step=$STEPS status=ready runtime=$RUNTIME"
