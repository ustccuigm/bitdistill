"""Small compatibility layer for causal and conditional-generation LMs.

Qwen3.5 exposes a conditional-generation wrapper around a text decoder while
Qwen3 uses a causal-generation wrapper. The quantizer only needs the text
decoder blocks and logits, so both wrappers can use the same training path.
"""

from __future__ import annotations

import transformers


def load_model(path, **kwargs):
    """Select the checkpoint's architecture without masking loading errors."""
    config = kwargs.pop("config", None) or transformers.AutoConfig.from_pretrained(path)
    if config.model_type == "qwen3_5":
        try:
            from fla.ops.gated_delta_rule import chunk_gated_delta_rule
        except ImportError as error:
            raise ImportError("Qwen3.5 requires the pinned FLA packages in requirements.lock; the PyTorch fallback exceeds the training memory budget.") from error
    conditional = any("ForConditionalGeneration" in a for a in (config.architectures or []))
    loader = transformers.AutoModelForImageTextToText if conditional else transformers.AutoModelForCausalLM
    model = loader.from_pretrained(path, config=config, **kwargs)
    if conditional:
        backbone = text_backbone(model)
        text_params = {id(p) for p in backbone.parameters()}
        text_params.update(id(p) for p in model.get_output_embeddings().parameters())
        for param in model.parameters():
            if id(param) not in text_params:
                param.requires_grad_(False)
    return model


def is_conditional_generation(model):
    """Return whether the checkpoint uses the multimodal conditional wrapper."""
    architectures = getattr(getattr(model, "config", None), "architectures", None) or []
    return any("ForConditionalGeneration" in name for name in architectures)


def text_backbone(model):
    """Return the module that owns the decoder layer list."""
    candidates = [
        getattr(model, "model", None),
        getattr(model, "language_model", None),
        getattr(getattr(model, "model", None), "language_model", None),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if hasattr(candidate, "layers"):
            return candidate
        nested = getattr(candidate, "model", None)
        if nested is not None and hasattr(nested, "layers"):
            return nested
    raise NotImplementedError(
        f"Cannot locate decoder layers in {type(model).__name__}; "
        "expected model.layers or model.language_model.model.layers."
    )


def decoder_layers(model):
    return text_backbone(model).layers


def move_text_embeddings(model, device):
    backbone = text_backbone(model)
    for name in ("embed_tokens", "rotary_emb"):
        module = getattr(backbone, name, None)
        if module is not None:
            setattr(backbone, name, module.to(device))
