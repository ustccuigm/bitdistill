#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../_bootstrap.sh"
source "$STEERDISTILL_ROOT/scripts/lib/load_config.sh"

: "${SEARCH_INDEX_PATH:?Set SEARCH_INDEX_PATH to the dense index}"
: "${SEARCH_CORPUS_PATH:?Set SEARCH_CORPUS_PATH to the retrieval corpus JSONL}"
: "${SEARCH_ENCODER_PATH:?Set SEARCH_ENCODER_PATH to the retrieval encoder}"
python="${SEARCH_RETRIEVER_PYTHON:-$BENCHMARK_ENV_ROOT/bin/python}"
port=$("$python" -c 'import sys, urllib.parse; print(urllib.parse.urlsplit(sys.argv[1]).port or 80)' \
  "${SEARCH_RETRIEVER_URL:-http://127.0.0.1:8000/retrieve}")
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
git -C "$BENCHMARK_ENVIRONMENTS_ROOT" show d511f043afe9199b8576fc99ea52e12d84841f32:examples/search/retriever/retrieval_server.py > "$work/retriever.py"
patch --silent -d "$work" -p1 < "$STEERDISTILL_ROOT/patches/search_retriever_cpu.patch"
CUDA_VISIBLE_DEVICES="" "$python" "$work/retriever.py" --index_path "$SEARCH_INDEX_PATH" \
  --corpus_path "$SEARCH_CORPUS_PATH" --retriever_model "$SEARCH_ENCODER_PATH" \
  --retriever_name e5 --topk 3 --port "$port"
