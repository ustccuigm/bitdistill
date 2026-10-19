#TODO Dataset Path
from transformers import AutoTokenizer, AutoConfig
from transformers.models.llama.modeling_llama import LlamaForCausalLM
from transformers.models.opt.modeling_opt import OPTForCausalLM
from transformers.models.bloom.modeling_bloom import BloomForCausalLM
from transformers import __version__ as transformers_version
from packaging import version
if version.parse(transformers_version) >= version.parse("4.41.0"):
    from transformers.models.phi3.modeling_phi3 import Phi3ForCausalLM
else:
    # a random but not model type
    Phi3ForCausalLM = int
if version.parse(transformers_version) >= version.parse("4.37.0"):
    from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM
else:
    Qwen2ForCausalLM = int
if version.parse(transformers_version) >= version.parse("4.50.0"):
    from transformers.models.gemma3.modeling_gemma3 import Gemma3ForConditionalGeneration
else:
    Gemma3ForConditionalGeneration = int
if version.parse(transformers_version) >= version.parse("4.51.0"):
    from transformers.models.qwen3.modeling_qwen3 import Qwen3ForCausalLM
else:
    Qwen3ForCausalLM = int
try:
    from transformers.models.gemma4_unified.modeling_gemma4_unified import (
        Gemma4UnifiedForCausalLM,
        Gemma4UnifiedForConditionalGeneration,
    )
except (ImportError, ModuleNotFoundError):
    Gemma4UnifiedForCausalLM = int
    Gemma4UnifiedForConditionalGeneration = int
import torch
from datasets import load_dataset
import random
import json
import os
import torch.nn as nn
import tqdm

from steerdistill.model_support import decoder_layers, load_model, move_text_embeddings


def get_calib_dataset(datasets="pileval", tokenizer=None, n_samples=128, block_size=1024,
                      data_path=None):
    if data_path is not None:
        return get_calib_dataset_local(
            tokenizer=tokenizer,
            n_samples=n_samples,
            block_size=block_size,
            data_path=data_path,
        )
    if datasets == "pile":
        return get_pile_dataset(tokenizer=tokenizer, n_samples=n_samples, block_size=block_size)
    elif datasets == "gsm8k":
        return get_calib_dataset_gsm8k(tokenizer=tokenizer, n_samples=n_samples, block_size=block_size)
    elif datasets == "code":
        return get_calib_dataset_code(tokenizer=tokenizer, n_samples=n_samples, block_size=block_size)
    elif datasets in {"merged_gmc", "openr1_math", "nemotron_code", "nemotron_math"}:
        env_key = {
            "merged_gmc": "MERGED_GMC_CALIB_PATH",
            "openr1_math": "OPENR1_MATH_CALIB_PATH",
            "nemotron_code": "NEMOTRON_CODE_CALIB_PATH",
            "nemotron_math": "NEMOTRON_MATH_CALIB_PATH",
        }[datasets]
        path = os.environ.get(env_key)
        if not path:
            raise ValueError(f"{env_key} is required for datasets={datasets!r}; pass data_path or set the variable.")
        return get_calib_dataset_json_dataset(tokenizer=tokenizer, n_samples=n_samples, block_size=block_size, data_path=path)
    elif datasets == "epicoder":
        return get_calib_dataset_epicoder(tokenizer=tokenizer, n_samples=n_samples, block_size=block_size)


def _calibration_record_to_text(item, tokenizer):
    if isinstance(item, str):
        return item
    if isinstance(item, list):
        if item and isinstance(item[0], list) and len(item[0]) == 2:
            return f"{item[0][0]}\n{item[0][1]}"
        return json.dumps(item, ensure_ascii=False)
    if not isinstance(item, dict):
        return str(item)
    # Chat templates expect structured native call arguments, not JSON strings.
    item = json.loads(json.dumps(item))
    messages = item.get("messages") or item.get("prompt")
    for message in messages if isinstance(messages, list) else []:
        if not isinstance(message, dict):
            continue
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            if isinstance(function.get("arguments"), str):
                function["arguments"] = json.loads(function["arguments"])
    template_args = {"tools": item["tools"]} if item.get("tools") else {}
    if isinstance(item.get("messages"), list):
        return tokenizer.apply_chat_template(item["messages"], tokenize=False, **template_args)
    if isinstance(item.get("prompt"), list):
        text = tokenizer.apply_chat_template(
            item["prompt"], tokenize=False, add_generation_prompt=True, **template_args
        )
        if item.get("completion") is not None:
            text += str(item["completion"])
        return text
    if item.get("prompt") is not None:
        return f"{item['prompt']}{item.get('completion', '')}"
    return str(item.get("text", json.dumps(item, ensure_ascii=False)))


def get_calib_dataset_local(tokenizer=None, n_samples=128, block_size=1024, data_path=None):
    """Build deterministic calibration blocks from local agent JSON/JSONL data."""
    if not data_path or not os.path.isfile(data_path):
        raise FileNotFoundError(f"Calibration data does not exist: {data_path}")
    token_stream = []
    eos_id = tokenizer.eos_token_id
    with open(data_path, "r", encoding="utf-8") as handle:
        if data_path.endswith(".json"):
            records = json.load(handle)
        else:
            records = (json.loads(line) for line in handle if line.strip())
        for item in records:
            text = _calibration_record_to_text(item, tokenizer)
            token_stream.extend(tokenizer.encode(text, add_special_tokens=False))
            if eos_id is not None:
                token_stream.append(eos_id)
            if len(token_stream) >= n_samples * block_size:
                break
    n_blocks = min(n_samples, len(token_stream) // block_size)
    if n_blocks < n_samples:
        raise ValueError(
            f"Calibration data has {len(token_stream)} tokens; requested "
            f"{n_samples} blocks of {block_size}. Refusing a silently reduced calibration run."
        )
    print(f" * Built {n_blocks} local calibration blocks from {data_path}")
    return [
        torch.tensor([token_stream[i * block_size:(i + 1) * block_size]], dtype=torch.long)
        for i in range(n_blocks)
    ]

def get_pile_dataset(tokenizer=None, n_samples=512, block_size=512):
    dataset = load_dataset("mit-han-lab/pile-val-backup", split="validation")
    dataset = dataset.map(lambda x: {
        'text': x['text']
    })
    dataset = dataset.shuffle(seed=42)
    samples = []
    n_run = 0

    for data in dataset:
        line = data["text"]
        line = line.strip()
        line_encoded = tokenizer.encode(line)
        if len(line_encoded) > 512:
            continue
        sample = torch.tensor([line_encoded])
        if sample.numel() == 0:
            continue
        samples.append(sample)
        n_run += 1
        if n_run == n_samples:
            break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]

# TODO: Don't do spliting when code and gsm8k
def get_calib_dataset_code(tokenizer=None, n_samples=512, block_size=512):
    dataset = load_dataset("json", data_files="nickrosh/Evol-Instruct-Code-80k-v1", split="train")

    dataset = dataset.shuffle(seed=42)
    samples = []
    n_run = 0

    for data in dataset:
        istr = data["instruction"]
        opt = data["output"]
        line = f"Instruction:\n{istr}\nOutput:\n"
        line += opt
        line = line.strip()
        line_encoded = tokenizer.encode(line)
        if len(line_encoded) > 512:
            continue
        sample = torch.tensor([line_encoded])
        if sample.numel() == 0:
            continue
        samples.append(sample)
        n_run += 1
        if n_run == n_samples:
            break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]

def get_calib_dataset_gsm8k(tokenizer=None, n_samples=512, block_size=512):
    data_path = os.environ.get("GSM8K_CALIB_PATH")
    if not data_path:
        raise ValueError("GSM8K_CALIB_PATH is required for datasets='gsm8k'; pass data_path or set the variable.")

    with open(data_path, 'r') as f:
        dataset_for_eval = f.readlines()

    dataset = [json.loads(item.strip()) for item in dataset_for_eval]
    random.seed(42)
    dataset = random.sample(dataset, k=min(n_samples * 10, len(dataset)))
    samples = []
    n_run = 0

    for data in dataset:
        istr = data["query"]
        opt = data["response"]
        line = f"Instruction:\n{istr}\nOutput:\n"
        line += opt
        line = line.strip()
        line_encoded = tokenizer.encode(line)
        if len(line_encoded) > 512:
            continue
        sample = torch.tensor([line_encoded])
        if sample.numel() == 0:
            continue
        samples.append(sample)
        n_run += 1
        if n_run == n_samples:
            break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]

def get_calib_dataset_json_dataset(tokenizer=None, n_samples=512, block_size=512, data_path=None):
    if data_path is None:
        raise ValueError("data_path must be provided for clip calibration dataset!")

    samples = []
    n_run = 0

    with open(data_path, 'r', encoding='utf-8') as f:
        for _, data in tqdm.tqdm(enumerate(f)):
            item = json.loads(data.strip())
            istr = item[0][0]
            opt = item[0][1]
            line = f"{istr}\n\n{opt}"
            line = line.strip()
            line_encoded = tokenizer.encode(line)
            if len(line_encoded) > 512:
                line_encoded = line_encoded[:512]
            sample = torch.tensor([line_encoded])
            if sample.numel() == 0:
                continue
            samples.append(sample)
            n_run += 1
            if n_run == n_samples:
                break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]

def get_calib_dataset_nemotron(tokenizer=None, n_samples=512, block_size=512, split=None):
    if split is None:
        raise ValueError("split must be provided for nemotron clip calibration dataset!")

    dataset = load_dataset("nvidia/Llama-Nemotron-Post-Training-Dataset", "SFT", split=split)
    samples = []
    n_run = 0

    for data in dataset:
        istr = data["input"][0]['content']
        opt = data["output"]
        line = f"{istr}\n\n{opt}"
        line = line.strip()
        line_encoded = tokenizer.encode(line)
        if len(line_encoded) > 512:
            continue
        sample = torch.tensor([line_encoded])
        if sample.numel() == 0:
            continue
        samples.append(sample)
        n_run += 1
        if n_run == n_samples:
            break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]

def get_calib_dataset_epicoder(tokenizer=None, n_samples=512, block_size=512):
    dataset = load_dataset("microsoft/EpiCoder-func-380k", split="train")
    samples = []
    n_run = 0

    for data in dataset:
        istr = data["instruction"]
        opt = data["output"]
        line = f"{istr}\n\n<think></think>\n{opt}"
        line = line.strip()
        line_encoded = tokenizer.encode(line)
        if len(line_encoded) > 512:
            continue
        sample = torch.tensor([line_encoded])
        if sample.numel() == 0:
            continue
        samples.append(sample)
        n_run += 1
        if n_run == n_samples:
            break
    # now concatenate all samples and split according to block size
    cat_samples = torch.cat(samples, dim=1)
    n_split = cat_samples.shape[1] // block_size
    print(f" * Split into {n_split} blocks")
    return [cat_samples[:, i*block_size:(i+1)*block_size] for i in range(n_split)]


def get_blocks(model):
    return decoder_layers(model)

def append_str_prefix(x, prefix):
    if isinstance(x, str):
        return prefix + x
    elif isinstance(x, tuple):
        return tuple([append_str_prefix(y, prefix) for y in x])
    elif isinstance(x, list):
        return [append_str_prefix(y, prefix) for y in x]
    else:
        return x

def move_embed(model, device):
    move_text_embeddings(model, device)

def get_named_linears(module):
    return {name: m for name, m in module.named_modules() if isinstance(m, nn.Linear)}

def get_op_by_name(module, op_name):
    # get the op by its name relative to the module
    for name, m in module.named_modules():
        if name == op_name:
            return m
    raise ValueError(f"Cannot find op {op_name} in module {module}")

def get_op_name(module, op):
    # get the name of the op relative to the module
    for name, m in module.named_modules():
        if m is op:
            return name
    raise ValueError(f"Cannot find op {op} in module {module}")


def build_model_and_enc(model_path):
    # if not os.path.exists(model_path):  # look into ssd
    #     raise FileNotFoundError(f"{model_path} not found!")
    print(f"* Building model {model_path}")

    # all hf model
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)

    enc = AutoTokenizer.from_pretrained(
        model_path, trust_remote_code=True, fix_mistral_regex=True
    )

    kwargs = {"torch_dtype": torch.bfloat16, "low_cpu_mem_usage": True}
    model = load_model(model_path, config=config, trust_remote_code=True, **kwargs)

    model.eval()

    return model, enc

@torch.no_grad()
def apply_clip(module, clip_results):
    if not isinstance(clip_results, list):
        clip_list = clip_results["clip"]
    else:
        clip_list = clip_results
    if len(clip_list) == 0:
        return
    if len(clip_list[0]) == 3:
        for name, max_val, min_val in clip_list:
            layer = get_op_by_name(module, name)
            # Respect the model's existing placement. During FSDP startup the
            # full model is intentionally on CPU; moving every clipped linear
            # to CUDA here would materialize the entire 8B model on each rank.
            max_val = max_val.to(layer.weight.device)
            min_val = min_val.to(layer.weight.device)
            org_shape = layer.weight.shape
            layer.weight.data = layer.weight.data.reshape(*max_val.shape[:2], -1)
            layer.weight.data = torch.clamp(layer.weight.data, min_val, max_val)
            layer.weight.data = layer.weight.data.reshape(org_shape)
    else:
        raise 1


def validate_clip_quantizer_metadata(clip_results, bits, group_size):
    """Reject clip caches optimized for a different quantizer definition."""
    metadata = clip_results.get("quantizer", {}) if isinstance(clip_results, dict) else {}
    expected = {
        "version": "int-asym-fp32-fp16scale-v1",
        "bits": bits,
        "group_size": group_size,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(
                f"Clip quantizer metadata mismatch: {key}={metadata.get(key)!r}, "
                f"expected {value!r}. Regenerate the clip cache."
            )
