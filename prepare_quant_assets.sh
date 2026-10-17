#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
set -a
CONFIG=${STEER_CONFIG:-$ROOT/config.example.env}
source "$CONFIG"
source "$ROOT/benchmarks/select.sh"
set +a
source "$ROOT/common/run_paths.sh"

MODEL=${1:-$TEACHER_MODEL}
CLIP_OUTPUT=${2:-$CLIP_PATH}
CALIB_DATA=${3:-$BENCHMARK_CLIP_DATA}
[[ -s "$MODEL/config.json" ]] || { echo "missing BF16 source model config: $MODEL" >&2; exit 2; }
if [[ "$BENCHMARK_ENGINE" == sdar && ! -s "$BENCHMARK_RL_TRAIN_DATA" ]]; then
  "$BENCHMARK_ENV_ROOT/bin/python" "$ROOT/benchmarks/prepare_sdar_tasks.py" \
    --benchmark "$BENCHMARK" --split train --output "$BENCHMARK_RL_TRAIN_DATA"
fi
[[ -s "$CALIB_DATA" ]] || { echo "missing $BENCHMARK calibration/RL data: $CALIB_DATA" >&2; exit 2; }
NORMALIZED_DATA="$RUN_ROOT/data/clip_calibration.jsonl"
"$ENV_ROOT/bin/python" "$ROOT/benchmarks/prepare_data.py" --input "$CALIB_DATA" --output "$NORMALIZED_DATA"

mkdir -p "$(dirname "$CLIP_OUTPUT")" "$LOG_ROOT"
PROVENANCE_ARGS=(--model "$MODEL" --data "$NORMALIZED_DATA" --clip "$CLIP_OUTPUT"
  --samples "${CLIP_SAMPLES:-128}" --seqlen "${CLIP_SEQLEN:-1024}" --grid "${CLIP_GRID:-20}")
if [[ -s "$CLIP_OUTPUT" ]]; then
  "$ENV_ROOT/bin/python" "$ROOT/quantization/clip_provenance.py" check "${PROVENANCE_ARGS[@]}"
  "$ENV_ROOT/bin/python" "$ROOT/verified_teacher/validate_clip.py" "$CLIP_OUTPUT" --bits 4 --group-size 64
  echo "STEER_CLIP_SIGNAL status=cached benchmark=$BENCHMARK model=$MODEL output=$CLIP_OUTPUT"
  exit 0
fi

"$ENV_ROOT/bin/python" "$ROOT/quantization/autoclip.py" \
  --model_path "$MODEL" --calib_data_path "$NORMALIZED_DATA" \
  --quant_type int --w_bit 4 --q_group_size 64 \
  --n_samples "${CLIP_SAMPLES:-128}" --seqlen "${CLIP_SEQLEN:-1024}" \
  --calib_batch_size "${CLIP_BATCH_SIZE:-1}" --clip_n_grid "${CLIP_GRID:-20}" \
  --clip_num_gpus "${CLIP_NUM_GPUS:-1}" \
  --run_clip --dump_clip "$CLIP_OUTPUT" \
  2>&1 | tee "$LOG_ROOT/clip.log"
"$ENV_ROOT/bin/python" "$ROOT/verified_teacher/validate_clip.py" \
  "$CLIP_OUTPUT" --bits 4 --group-size 64
"$ENV_ROOT/bin/python" "$ROOT/quantization/clip_provenance.py" record "${PROVENANCE_ARGS[@]}"
echo "STEER_CLIP_SIGNAL status=ready benchmark=$BENCHMARK model_group=$MODEL_GROUP output=$CLIP_OUTPUT"
