#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname "$0")/common/launch_train.sh" skill_opd
