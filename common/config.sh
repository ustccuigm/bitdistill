#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STEER_ASSET_ROOT="${STEER_ASSET_ROOT:?Set STEER_ASSET_ROOT before launching training}"
ENV_ROOT="${ENV_ROOT:?Set ENV_ROOT before launching training}"

PYTHON_BIN="${PYTHON_BIN:-$ENV_ROOT/bin/python}"
ACCELERATE_BIN="${ACCELERATE_BIN:-$ENV_ROOT/bin/accelerate}"
DEEPSPEED_BIN="${DEEPSPEED_BIN:-$ENV_ROOT/bin/deepspeed}"
MODEL_PATH="${MODEL_PATH:?Set MODEL_PATH to the configured BF16 source model or current student checkpoint}"
TOOL_ENV_SOURCE_PATH="${TOOL_ENV_SOURCE_PATH:-$STEER_ASSET_ROOT/common/data/tool_use_environment}"

BITS="${BITS:-4}"
GROUP_SIZE="${GROUP_SIZE:-64}"
QUANT_TYPE="${QUANT_TYPE:-int${BITS}-asym}"
CLIP_PATH="${CLIP_PATH:-$STEER_ASSET_ROOT/common/clip_cache/int${BITS}-g${GROUP_SIZE}.pt}"
CALIB_DATA_PATH="${CALIB_DATA_PATH:-$STEER_ASSET_ROOT/qat/data/teacher_generated.jsonl}"
PROMPT_ONLY_CALIB_DATA_PATH="${PROMPT_ONLY_CALIB_DATA_PATH:-${BENCHMARK_CLIP_DATA:-$STEER_ASSET_ROOT/common/data/clip/tool_use_calibration.jsonl}}"
RAW_PROMPT_PATH="${RAW_PROMPT_PATH:-${BENCHMARK_RL_TRAIN_DATA:-$STEER_ASSET_ROOT/common/data/prompts/tool_use_train.jsonl}}"
QAT_DATA_PATH="${QAT_DATA_PATH:-$STEER_ASSET_ROOT/qat/data/teacher_generated.jsonl}"
OFFLINE_DATA_PATH="${OFFLINE_DATA_PATH:-$STEER_ASSET_ROOT/offline_distill/data/teacher_topk.jsonl}"
TRAIN_DATA_PATH="${TRAIN_DATA_PATH:-$RAW_PROMPT_PATH}"
MODEL_MAX_LENGTH="${MODEL_MAX_LENGTH:-32768}"
MAX_STEPS="${MAX_STEPS:-63}"
NUM_GPUS="${NUM_GPUS:-8}"
PER_DEVICE_TRAIN_BATCH_SIZE="${PER_DEVICE_TRAIN_BATCH_SIZE:-16}"
GRADIENT_ACCUMULATION_STEPS="${GRADIENT_ACCUMULATION_STEPS:-1}"
MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES:-1000}"
LEARNING_RATE="${LEARNING_RATE:-8e-6}"
LR_SCHEDULER_TYPE="${LR_SCHEDULER_TYPE:-constant}"
WARMUP_STEPS="${WARMUP_STEPS:-0}"
GRADIENT_CHECKPOINTING="${GRADIENT_CHECKPOINTING:-True}"
DISTRIBUTED_BACKEND="${DISTRIBUTED_BACKEND:-fsdp2}"
SAVE_STEPS="${SAVE_STEPS:-4}"

if [[ "$GROUP_SIZE" != "64" ]]; then
  echo "This SteerDistill route is pinned to group_size=64; got $GROUP_SIZE" >&2
  exit 2
fi
if [[ ! "$BITS" =~ ^(2|4|8)$ ]]; then
  echo "BITS must be one of 2, 4, 8; got $BITS" >&2
  exit 2
fi
if (( PER_DEVICE_TRAIN_BATCH_SIZE < 1 )); then
  echo "per-device quantization batch size must be positive; got $PER_DEVICE_TRAIN_BATCH_SIZE" >&2
  exit 2
fi
if (( GRADIENT_ACCUMULATION_STEPS < 1 )); then
  echo "gradient accumulation must be positive; got $GRADIENT_ACCUMULATION_STEPS" >&2
  exit 2
fi
