#!/usr/bin/env bash
# Shared repository paths for public shell entry points.
set -euo pipefail

SCRIPT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
STEERDISTILL_ROOT=${STEERDISTILL_ROOT:-$(cd "$SCRIPT_ROOT/.." && pwd)}
export STEERDISTILL_ROOT
export PYTHONPATH="$STEERDISTILL_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
