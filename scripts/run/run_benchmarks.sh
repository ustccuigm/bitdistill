#!/usr/bin/env bash
set -euo pipefail

runner="$(dirname "${BASH_SOURCE[0]}")/run_benchmark.sh"
# All evaluations in this batch use the corresponding training receipt.
export STEER_EVAL_FROM_TRAINING=1
models=("$@")
if (( ${#models[@]} == 0 )); then models=(qwen3_8b qwen3_5_4b gemma4_12b); fi
for model in "${models[@]}"; do
  bash "$runner" full --model "$model" --benchmark bfcl_v4
  bash "$runner" eval --model "$model" --benchmark tau2_bench
  for benchmark in webshop alfworld search_qa; do
    bash "$runner" full --model "$model" --benchmark "$benchmark"
  done
done
