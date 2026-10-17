"""Fail before calibration/training when the rollout runtime lacks the model."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    from vllm.model_executor.models import ModelRegistry
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
