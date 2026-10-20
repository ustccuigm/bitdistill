#!/usr/bin/env bash
# Source from entry points after _bootstrap.sh. Keep settings available to children.
CONFIG=${STEER_CONFIG:-$STEERDISTILL_ROOT/configs/local.env}
if [[ ! -f "$CONFIG" && -z "${STEER_CONFIG:-}" ]]; then
  CONFIG="$STEERDISTILL_ROOT/configs/steerdistill.example.env"
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "Configuration not found: $CONFIG" >&2
  return 2
fi
# Resolve relative custom paths before any child process changes directory.
CONFIG=$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")
export STEER_CONFIG="$CONFIG"
case $- in *a*) _STEER_CONFIG_ALLEXPORT=1 ;; *) _STEER_CONFIG_ALLEXPORT=0 ;; esac
set -a
source "$CONFIG"
if [[ "$_STEER_CONFIG_ALLEXPORT" == 0 ]]; then
  set +a
fi
unset _STEER_CONFIG_ALLEXPORT
