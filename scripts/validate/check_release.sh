#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../_bootstrap.sh"
ROOT="$STEERDISTILL_ROOT"
fail=0
forbidden='(BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9_-]{32,}|/mnt/|/root/|/remote-home|root@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'
if grep -RInE --exclude='check_release.sh' --exclude='*.pyc' --exclude='*.log' --exclude-dir=__pycache__ --exclude-dir=.git "$forbidden" \
    "$ROOT"; then
  echo "STEER_RELEASE_SIGNAL status=failed reason=forbidden_metadata" >&2
  fail=1
fi
# Four published transcripts contain model-generated /home/user examples.
# Exempt only their reviewed contents from the home-path check, never secrets.
while IFS= read -r -d '' path; do
  expected=
  case "${path#"$ROOT/"}" in
    experiments/cases/033_multi_turn_miss_param_26/BitDistiller/trajectory.json) expected=f7b094f70a92b3e26107a8356de744cbf95cc01fefb7692b1ba1d3507c56fb40 ;;
    experiments/cases/033_multi_turn_miss_param_26/BitDistiller/cot_and_actions.txt) expected=bbe32a1ebd4e5ac01291edb02f59f405b55f5fb0a02e69c179a0ebbc72112623 ;;
    experiments/cases/033_multi_turn_miss_param_26/EfficientQAT/trajectory.json) expected=f304b964388e172d2830da339e3074846c9bbed9fca5300f41f9a90d87690b0a ;;
    experiments/cases/033_multi_turn_miss_param_26/EfficientQAT/cot_and_actions.txt) expected=eeff1e2fb4c2f573ae1200f40891bd55913a94c09458384fde3ec03819dbdb76 ;;
  esac
  actual=$(sha256sum "$path")
  if [[ -z "$expected" || "${actual%% *}" != "$expected" ]]; then
    echo "forbidden home path: ${path#"$ROOT/"}" >&2
    fail=1
  fi
done < <(grep -RIlZ --exclude='check_release.sh' --exclude='*.pyc' --exclude='*.log' --exclude-dir=__pycache__ --exclude-dir=.git '/home/' "$ROOT" || true)
for path in checkpoints steps online analysis validation logs skill_store; do
  [[ ! -e "$ROOT/$path" ]] || { echo "forbidden generated directory: $path" >&2; fail=1; }
done
if find "$ROOT" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.egg-info' -o -name 'build' -o -name 'dist' \) -print -quit | grep -q .; then
  echo "generated Python build artifact found" >&2
  fail=1
fi
if find "$ROOT" -type f \( -name '*.orig' -o -name '*~' -o -name '*.swp' -o -name '.DS_Store' \) -print -quit | grep -q .; then
  echo "editor backup artifact found" >&2
  fail=1
fi
if find "$ROOT" -type f \( -name '*.safetensors' -o -name '*.bin' -o -name '*.pt' -o -name '*.jsonl' -o -name '*.zip' \) -print -quit | grep -q .; then
  echo "generated model/data artifact found" >&2
  fail=1
fi
for pattern in '*.py' '*.sh'; do
  if find "$ROOT" -maxdepth 1 -type f -name "$pattern" -print -quit | grep -q .; then
    echo "root-level executable source must live under src/ or scripts/: $pattern" >&2
    fail=1
  fi
done
if (( fail )); then exit 2; fi
echo "STEER_RELEASE_SIGNAL status=passed root=$ROOT"
