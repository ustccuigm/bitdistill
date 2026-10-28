#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

HF_OUTPUT="${1:?usage: merge_fsdp_checkpoint.sh HF_OUTPUT [CHECKPOINT_DIR]}"
CHECKPOINT_DIR="${2:-}"

if [[ -z "$CHECKPOINT_DIR" ]]; then
  CHECKPOINT_DIR="$(find "$HF_OUTPUT" -maxdepth 1 -type d -name 'checkpoint-*' -print | sort -V | tail -n 1)"
fi
SHARDED_MODEL="$CHECKPOINT_DIR/pytorch_model_fsdp_0"
if [[ ! -s "$SHARDED_MODEL/.metadata" ]]; then
  echo "Missing FSDP model metadata: $SHARDED_MODEL/.metadata" >&2
  exit 2
fi

mkdir -p "$HF_OUTPUT"
"$PYTHON_BIN" - "$SHARDED_MODEL" "$HF_OUTPUT" <<'PY'
import sys
from accelerate.utils import merge_fsdp_weights

merge_fsdp_weights(sys.argv[1], sys.argv[2], safe_serialization=True)
PY

# The distributed checkpoint only contains weights. Reuse the immutable base
# model metadata/tokenizer; remove its shard index because the merged output is
# a single safetensors file.
cp "$MODEL_PATH"/*.json "$HF_OUTPUT/"
cp "$MODEL_PATH"/*.jinja "$HF_OUTPUT/" 2>/dev/null || true
cp "$MODEL_PATH"/*.txt "$HF_OUTPUT/" 2>/dev/null || true
# Some FSDP checkpoint formats include a config.  When present, it must win
# over the immutable base model config copied above.
if [[ -s "$CHECKPOINT_DIR/config.json" ]]; then
  cp "$CHECKPOINT_DIR/config.json" "$HF_OUTPUT/config.json"
fi
if [[ "${WRITE_QUANTIZER_METADATA:-0}" == 1 ]]; then
  "$PYTHON_BIN" - "$HF_OUTPUT/config.json" "$BITS" "$GROUP_SIZE" "$QUANT_TYPE" "${ACTIVATION_BITS:-16}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
config = json.loads(path.read_text())
config["steerdistill_quantization"] = {
    "version": "int-asym-fp32-fp16scale-v1",
    "quant_type": sys.argv[4],
    "bits": int(sys.argv[2]),
    "activation_bits": int(sys.argv[5]),
    "group_size": int(sys.argv[3]),
}
path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
PY
fi
rm -f "$HF_OUTPUT/model.safetensors.index.json"
[[ -s "$HF_OUTPUT/model.safetensors" ]]

echo "FSDP_MERGE_SIGNAL status=ready checkpoint=$CHECKPOINT_DIR output=$HF_OUTPUT"
