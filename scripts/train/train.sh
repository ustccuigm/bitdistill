#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname "$0")/../lib/launch_train.sh" skill_opd
