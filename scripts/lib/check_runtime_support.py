"""Fail before calibration/training when the rollout runtime lacks the model."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    from vllm.model_executor.models import ModelRegistry
    if os.getenv("QUANT_PRECISION", "w4a16") != "w4a16":
        from vllm.plugins import load_general_plugins
        from vllm.model_executor.layers.quantization import get_quantization_config
        load_general_plugins()
        get_quantization_config("steerdistill")
    config = json.loads((args.model / "config.json").read_text())
    architectures = config.get("architectures") or []
    from vllm.config import ModelConfig
    # Resolve through the same native/Transformers dispatch used by the server.
    # A registry-only check incorrectly rejects compatible Transformers models.
    model_config = ModelConfig(model=str(args.model), trust_remote_code=True,
                               dtype="bfloat16", max_model_len=32768)
    _, resolved = ModelRegistry.resolve_model_cls(architectures, model_config)
    print(f"STEER_RUNTIME_SUPPORT_SIGNAL architectures={architectures} backend={resolved} status=resolved")


if __name__ == "__main__":
    main()
