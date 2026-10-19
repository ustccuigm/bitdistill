#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

ROUTE="${1:?usage: launch_train.sh skill_opd}"
if [[ "$ROUTE" != skill_opd ]]; then
  echo "Only the SteerDistill skill_opd training route is supported" >&2
  exit 2
fi
TRAIN_DATA_PATH="${SKILL_DATA_PATH:?skill_opd requires SKILL_DATA_PATH}"
ROUTE_ARGS=(
  --train_kd True
  --kd_loss_type reverse
  --kd_loss_top_k 0
  --distill_ce_weight 0.0
  --distill_kl_weight 1.0
  --online_distill False
  --mixed_turn_distill False
  --skill_distill True
)

"$PYTHON_BIN" "$REPO_ROOT/scripts/lib/validate_model.py" "$MODEL_PATH"
APPLY_CLIP="${APPLY_CLIP:-True}"
CLIP_ARGS=()
QUANT_GRID_ARGS=()
SKILL_REFERENCE_ARGS=()
ONLINE_ARGS=()
if [[ "${TRAJECTORY_ONLINE:-False}" == True ]]; then
  ONLINE_ARGS=(--trajectory_online True
    --opd_global_batch_size "${OPD_GLOBAL_BATCH_SIZE:-16}"
    --opd_micro_batch_size "${OPD_MICRO_BATCH_SIZE:-1}"
    --online_turn_batch_size "${ONLINE_TURN_BATCH_SIZE:-1}"
    --online_previous_step "${OPD_PREVIOUS_OPTIMIZER_STEP:-0}"
    --ignore_data_skip True)
fi
CHECKPOINTING_ARGS=()
if [[ "${MODEL_FAMILY:-}" == qwen3_5_4b ]]; then
  # Reentrant recomputation avoids nonreentrant metadata assumptions in the
  # hybrid linear/full-attention decoder. FSDP activation wrapping stays off.
  CHECKPOINTING_ARGS=(--gradient_checkpointing_kwargs '{"use_reentrant":true}')
fi
if [[ -n "${SKILL_REFERENCE_MODEL_PATH:-}" ]]; then
  SKILL_REFERENCE_ARGS=(--skill_reference_model_name_or_path "$SKILL_REFERENCE_MODEL_PATH")
fi
if [[ -n "${QUANT_GRID_PATH:-}" ]]; then
  [[ -s "$QUANT_GRID_PATH/quantize_config.json" ]] || {
    echo "Missing fixed GPTQ grid: $QUANT_GRID_PATH" >&2
    exit 2
  }
  QUANT_GRID_ARGS=(--quant_grid_path "$QUANT_GRID_PATH")
fi
case "${APPLY_CLIP,,}" in
  true|1|yes)
    if [[ ! -f "$CLIP_PATH" ]]; then
      echo "Missing asymmetric clip cache: $CLIP_PATH" >&2
      echo "Run the SteerDistill clip preparation for the configured asset root first." >&2
      exit 2
    fi
    CLIP_ARGS=(--clip "$CLIP_PATH")
    ;;
  false|0|no)
    echo "STEERDISTILL_CLIP_SIGNAL status=skipped model=$MODEL_PATH"
    ;;
  *)
    echo "APPLY_CLIP must be True or False; got $APPLY_CLIP" >&2
    exit 2
    ;;
esac
if [[ ! -f "$TRAIN_DATA_PATH" ]]; then
  echo "Missing training data: $TRAIN_DATA_PATH" >&2
  exit 2
fi

EXPERIMENT_SUFFIX="${EXPERIMENT_TAG:+-$EXPERIMENT_TAG}"
OUTPUT_DIR="${OUTPUT_DIR_OVERRIDE:-$STEER_ASSET_ROOT/$ROUTE/checkpoints/int${BITS}-g${GROUP_SIZE}${EXPERIMENT_SUFFIX}}"
LOG_DIR="${LOG_DIR_OVERRIDE:-$STEER_ASSET_ROOT/$ROUTE/logs/int${BITS}-g${GROUP_SIZE}${EXPERIMENT_SUFFIX}}"
mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

TRAIN_ENTRY="$REPO_ROOT/src/steerdistill/training/train.py"
case "$DISTRIBUTED_BACKEND" in
  deepspeed)
    LAUNCH_CMD=("$DEEPSPEED_BIN" --num_gpus "$NUM_GPUS" "$TRAIN_ENTRY")
    BACKEND_ARGS=(--deepspeed "${DEEPSPEED_CONFIG:-$REPO_ROOT/src/steerdistill/training/config/zero.json}")
    ;;
  fsdp2)
    FSDP_CONFIG=${FSDP_CONFIG:-$REPO_ROOT/src/steerdistill/training/config/$("$PYTHON_BIN" "$REPO_ROOT/scripts/lib/select_fsdp.py" "$MODEL_PATH")}
    [[ -s "$FSDP_CONFIG" ]] || { echo "Missing FSDP config: $FSDP_CONFIG" >&2; exit 2; }
    echo "STEER_FSDP_SIGNAL config=$FSDP_CONFIG processes=$NUM_GPUS"
    LAUNCH_CMD=("$ACCELERATE_BIN" launch --config_file "$FSDP_CONFIG" --num_processes "$NUM_GPUS" --main_process_port "${MAIN_PROCESS_PORT:-29500}" "$TRAIN_ENTRY")
    BACKEND_ARGS=()
    ;;
  *)
    echo "Unknown DISTRIBUTED_BACKEND=$DISTRIBUTED_BACKEND; expected deepspeed or fsdp2" >&2
    exit 2
    ;;
esac

"${LAUNCH_CMD[@]}" \
  --model_name_or_path "$MODEL_PATH" \
  --teacher_model_name_or_path "${TEACHER_MODEL_PATH:-$MODEL_PATH}" \
  "${SKILL_REFERENCE_ARGS[@]}" \
  --data_path "$TRAIN_DATA_PATH" \
  --model_max_length "$MODEL_MAX_LENGTH" \
  --output_dir "$OUTPUT_DIR" \
  --max_steps "$MAX_STEPS" \
  --bf16 True \
  --seed "${SEED:-42}" \
  --per_device_train_batch_size "$PER_DEVICE_TRAIN_BATCH_SIZE" \
  --gradient_accumulation_steps "$GRADIENT_ACCUMULATION_STEPS" \
  --eval_strategy no \
  --save_strategy "${SAVE_STRATEGY:-steps}" \
  --save_steps "$SAVE_STEPS" \
  --save_total_limit "${SAVE_TOTAL_LIMIT:-4}" \
  --learning_rate "$LEARNING_RATE" \
  --lr_scheduler_type "$LR_SCHEDULER_TYPE" \
  --warmup_steps "$WARMUP_STEPS" \
  --weight_decay 0.0 \
  --logging_steps 1 \
  --report_to none \
  --remove_unused_columns False \
  --bits "$BITS" \
  --quant_type "$QUANT_TYPE" \
  --q_group_size "$GROUP_SIZE" \
  "${QUANT_GRID_ARGS[@]}" \
  "${CLIP_ARGS[@]}" \
  --gradient_checkpointing "$GRADIENT_CHECKPOINTING" \
  "${CHECKPOINTING_ARGS[@]}" \
  --max_train_samples "$MAX_TRAIN_SAMPLES" \
  --skip_final_save "${SKIP_FINAL_SAVE:-False}" \
  --may_resume "${MAY_RESUME:-True}" \
  "${ONLINE_ARGS[@]}" \
  "${BACKEND_ARGS[@]}" \
  "${ROUTE_ARGS[@]}" \
  2>&1 | tee "$LOG_DIR/train.log"
