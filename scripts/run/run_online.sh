#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
set -a
source "${STEER_CONFIG:-$ROOT/configs/steerdistill.example.env}"
set +a
exec "$ENV_ROOT/bin/python" "$ROOT/scripts/run/online.py" --gpu-ids "${1:-0,1,2,3,4,5,6,7}"
