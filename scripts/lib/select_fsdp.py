"""Select wrapping from the checkpoint architecture, never from its filename."""
import json
import sys
from pathlib import Path


def select(config):
    model_type = config.get("model_type")
    configs = {
        "qwen3": "fsdp2_8gpu.yaml",
        "qwen3_5": "fsdp2_8gpu_qwen3_5.yaml",
        "gemma4_unified_text": "fsdp2_8gpu_gemma4.yaml",
    }
    if model_type not in configs:
        raise ValueError(f"Unsupported model_type={model_type!r}; set FSDP_CONFIG explicitly")
    return configs[model_type]


if __name__ == "__main__":
    print(select(json.loads((Path(sys.argv[1]) / "config.json").read_text())))
