#!/usr/bin/env bash
# Source before resolving paths so precision variants cannot share checkpoints.
export QUANT_PRECISION=${QUANT_PRECISION:-w4a16}
case "$QUANT_PRECISION" in
  w4a16) _bits=4; _activation_bits=16 ;;
  w2a16) _bits=2; _activation_bits=16 ;;
  w4a8) _bits=4; _activation_bits=8 ;;
  *) echo "Unknown QUANT_PRECISION=$QUANT_PRECISION" >&2; return 2 ;;
esac
if [[ "${BITS:-$_bits}" != "$_bits" || "${ACTIVATION_BITS:-$_activation_bits}" != "$_activation_bits" ]]; then
  echo "BITS/ACTIVATION_BITS conflict with QUANT_PRECISION=$QUANT_PRECISION" >&2
  return 2
fi
export BITS=$_bits ACTIVATION_BITS=$_activation_bits GROUP_SIZE=${GROUP_SIZE:-64}
if [[ "$GROUP_SIZE" != 64 ]]; then
  echo "The public SteerDistill routes use GROUP_SIZE=64" >&2
  return 2
fi
export QUANT_TYPE=int${BITS}-asym
if [[ "$QUANT_PRECISION" == w4a16 ]]; then
  export RUNTIME_SUFFIX=awq-runtime
else
  export RUNTIME_SUFFIX=${QUANT_PRECISION}-runtime
fi
unset _bits _activation_bits
