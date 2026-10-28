#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:?usage: prepare_initial_runtime.sh MODEL_SOURCE OUTPUT}
OUTPUT=${2:?}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
source "$ROOT/scripts/lib/precision.sh"
ENV=${ENV_ROOT:?Set ENV_ROOT}
: "${CLIP_PATH:?Set CLIP_PATH to the benchmark calibration cache}"
[[ -s "$CLIP_PATH" ]] || { echo "missing clip cache: $CLIP_PATH" >&2; exit 2; }
[[ -s "$SOURCE/config.json" ]] || { echo "missing BF16 source model: $SOURCE" >&2; exit 2; }
if [[ -s "$OUTPUT/quant_config.json" ]]; then
  "$ENV/bin/python" -m steerdistill.runtime_validation \
    --source "$SOURCE" --runtime "$OUTPUT" --bits "${BITS:-4}" --group-size "${GROUP_SIZE:-64}" --activation-bits "${ACTIVATION_BITS:-16}" --layers 0 --clip "$CLIP_PATH"
  echo "INITIAL_AWQ_RUNTIME_SIGNAL status=cached output=$OUTPUT"
  exit 0
fi
[[ ! -e "$OUTPUT" ]] || { echo "partial AWQ runtime exists: $OUTPUT" >&2; exit 2; }
"$ENV/bin/python" "$ROOT/src/steerdistill/training/convert_hf_to_awq_runtime.py" \
  --source "$SOURCE" --output "$OUTPUT" --bits "${BITS:-4}" --group-size "${GROUP_SIZE:-64}" --activation-bits "${ACTIVATION_BITS:-16}" --clip "$CLIP_PATH"
"$ENV/bin/python" -m steerdistill.runtime_validation \
  --source "$SOURCE" --runtime "$OUTPUT" --bits "${BITS:-4}" --group-size "${GROUP_SIZE:-64}" --activation-bits "${ACTIVATION_BITS:-16}" --layers 0 --clip "$CLIP_PATH"
echo "INITIAL_AWQ_RUNTIME_SIGNAL status=ready output=$OUTPUT"
