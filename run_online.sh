#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
set -a
source "${STEER_CONFIG:-$ROOT/config.example.env}"
set +a
exec "$ENV_ROOT/bin/python" "$ROOT/run_online.py" --gpu-ids "${1:-0,1,2,3,4,5,6,7}"
