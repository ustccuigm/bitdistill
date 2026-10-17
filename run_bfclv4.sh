#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
set -a
CONFIG=${STEER_CONFIG:-$ROOT/config.example.env}
source "$CONFIG"
set +a
: "${PROMPT_MANIFEST:?PROMPT_MANIFEST must point to the selected benchmark prompt manifest}"
export PROMPT_MANIFEST
export BENCHMARK=${BENCHMARK:-bfcl_v4}
export GPU_IDS=${1:-0,1,2,3,4,5,6,7}
exec bash "$ROOT/run_benchmark.sh" train
