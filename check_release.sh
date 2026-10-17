#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fail=0
forbidden='(BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9_-]{32,}|/mnt/|/home/|/root/|/remote-home|root@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'
if grep -RInE --exclude='check_release.sh' --exclude='*.pyc' --exclude='*.log' --exclude-dir=__pycache__ --exclude-dir=.git "$forbidden" \
    "$ROOT"; then
  echo "STEER_RELEASE_SIGNAL status=failed reason=forbidden_metadata" >&2
  fail=1
fi
for path in checkpoints steps online analysis validation logs skill_store; do
  [[ ! -e "$ROOT/$path" ]] || { echo "forbidden generated directory: $path" >&2; fail=1; }
done
if find "$ROOT" -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -print -quit | grep -q .; then
  echo "generated Python cache found" >&2
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
if (( fail )); then exit 2; fi
echo "STEER_RELEASE_SIGNAL status=passed root=$ROOT"
