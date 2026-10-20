#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
source "$ROOT/scripts/lib/load_config.sh"
exec "$ENV_ROOT/bin/python" "$ROOT/scripts/run/online.py" --gpu-ids "${1:-${GPU_IDS:-0,1,2,3,4,5,6,7}}"
