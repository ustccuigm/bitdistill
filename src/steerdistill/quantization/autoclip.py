import torch
import torch.nn as nn
import gc
import argparse
import os
import sys
from steerdistill.quantization.clip_utils import *
from steerdistill.quantization.quantizer import pseudo_quantize_tensor, pseudo_quantize_n2f3_tensor
from tqdm import tqdm
from collections import defaultdict
import functools
from concurrent.futures import ThreadPoolExecutor

@torch.no_grad()
def auto_2clip_layer(w, input_feat, n_bit, q_config,
                    n_grid=20,
                    max_shrink=0.5,
                    n_sample_token=512):
    if n_grid < 2:
        raise ValueError("n_grid must be at least 2 for asymmetric clipping search.")
    assert w.dim() == 2
    org_w_shape = w.shape
    # w           [co, ci]      -> [co, 1, n_group, group size]
    # input_feat  [n_token, ci] -> [1, n_token, n_group, group size]

    group_size = q_config["q_group_size"] if q_config["q_group_size"] > 0 else w.shape[1]

    input_feat = input_feat.view(-1, input_feat.shape[-1])
    input_feat = input_feat.reshape(1, input_feat.shape[0], -1, group_size)
    sample_stride = max(1, input_feat.shape[1] // n_sample_token)
    input_feat = input_feat[:, 0::sample_stride]
    w = w.reshape(w.shape[0], 1, -1, group_size)

    # Projection widths in multimodal/conditional-generation models are not
    # always divisible by the historical 256/64 choices. Choose a bounded
    # divisor instead of rejecting an otherwise valid text decoder layer.
    oc_batch_size = min(256, w.shape[0])
    while w.shape[0] % oc_batch_size:
        oc_batch_size //= 2
    if oc_batch_size < 1:
        oc_batch_size = w.shape[0]
    w_all = w
    best_max_val_all = []
    best_min_val_all = []
    for i_b in range(w.shape[0] // oc_batch_size):
        w = w_all[i_b * oc_batch_size: (i_b + 1) * oc_batch_size]

        org_max_val = w.amax(dim=-1, keepdim=True)  # co, 1, n_group, 1
        org_min_val = w.amin(dim=-1, keepdim=True)

        best_max_val = org_max_val.clone()
        best_min_val = org_min_val.clone()

        min_errs = torch.ones_like(org_max_val) * 1e9
        input_feat = input_feat.to(w.device)
        org_out = (input_feat * w).sum(dim=-1)  # co, n_token, n_group

        for i_s_p in range(int(max_shrink * n_grid)):
            max_val = org_max_val * (1 - i_s_p / n_grid)
            for i_s_n in range(int(max_shrink * n_grid)):
                min_val = org_min_val * (1 - i_s_n / n_grid)
                # min_val = - max_val
                cur_w = torch.clamp(w, min_val, max_val)
                if q_config["quant_type"] == "int":
                    q_w = pseudo_quantize_tensor(cur_w, n_bit=n_bit, zero_point=True, q_group_size=q_config['q_group_size'])
                elif q_config["quant_type"] == "nf3":
                    q_w = pseudo_quantize_n2f3_tensor(cur_w, q_group_size=q_config['q_group_size'])
                else:
                    quant_type = q_config["quant_type"]
                    raise ValueError(f"Has no support {quant_type}. Valid quant_type:[int, nf3]")
                    
                cur_out = (input_feat * q_w).sum(dim=-1)

                err = (cur_out - org_out).pow(2).mean(dim=1).view(min_errs.shape)

                del cur_w
                del cur_out
                cur_best_idx = err < min_errs
                min_errs[cur_best_idx] = err[cur_best_idx]
                best_max_val[cur_best_idx] = max_val[cur_best_idx]
                best_min_val[cur_best_idx] = min_val[cur_best_idx]

        best_max_val_all.append(best_max_val)
        best_min_val_all.append(best_min_val)
    print("loss:", err.mean().item())
    best_max_val = torch.cat(best_max_val_all, dim=0)
    best_min_val = torch.cat(best_min_val_all, dim=0)
    del input_feat
    del org_out
    gc.collect()
    torch.cuda.empty_cache()
    return best_max_val.squeeze(1), best_min_val.squeeze(1)

    
@torch.no_grad()
def auto_clip_block(module,
                    w_bit, q_config,
                    input_feat, n_grid=20, clip_num_gpus=1):

    named_linears = {name: m for name,
                     m in module.named_modules() if isinstance(m, nn.Linear)}

    names = [
        name for name in named_linears
        # due to qk bmm, it is hard to clip precisely
        if not any(part in name for part in ["q_", "k_", "query", "key", "Wqkv"])
    ]

    def clip_one(index_and_name):
        index, name = index_and_name
        device = torch.device("cuda", index % clip_num_gpus)
        with torch.cuda.device(device):
            linear = named_linears[name].to(device)
            max_val, min_val = auto_2clip_layer(
                linear.weight, input_feat[name], n_bit=w_bit,
                q_config=q_config, n_grid=n_grid)
            linear.cpu()
        # Keeping cache tensors on CPU makes the result independent of the
        # scheduling device and prevents all per-layer results accumulating in
        # GPU memory. ThreadPoolExecutor.map preserves the canonical name order.
        return name, max_val.cpu(), min_val.cpu()

    clip_num_gpus = max(1, min(clip_num_gpus, torch.cuda.device_count(), len(names)))
    if clip_num_gpus == 1:
        return [clip_one(item) for item in enumerate(names)]
    with ThreadPoolExecutor(max_workers=clip_num_gpus) as executor:
        return list(executor.map(clip_one, enumerate(names)))

@torch.no_grad()
def run_clip(
    model, enc,
    w_bit, q_config,
    n_samples=128, seqlen=1024,
    datasets="pile", data_path=None, calib_batch_size=1, clip_n_grid=20,
    clip_num_gpus=1,
):
    print(f"Using {datasets} dataset to do calibation")
    # Calibration blocks are independent examples. Qwen3 otherwise threads a
    # DynamicCache through direct decoder-layer calls below, causing KV state
    # to grow across all 128 blocks until a 24 GiB GPU is exhausted.
    model.config.use_cache = False
    samples = get_calib_dataset(
              datasets=datasets, tokenizer=enc, n_samples=n_samples, block_size=seqlen,
              data_path=data_path)
    samples = torch.cat(samples, dim=0)

    inps = []
    layer_kwargs = {}
    
    layers = get_blocks(model)

    layers[0] = layers[0].cuda()
    move_embed(model, "cuda")

    # get input and kwargs to layer 0
    # with_kwargs is only supported in PyTorch 2.0
    # use this Catcher hack for now
    class Catcher(nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module
            # Transformers' Qwen3Model selects a causal mask from each decoder
            # layer's attention type before invoking the layer.  Keep that
            # public layer attribute visible while the first block is wrapped.
            if hasattr(module, "attention_type"):
                self.attention_type = module.attention_type

        def forward(self, inp, **kwargs):
            inps.append(inp.detach().cpu())
            layer_kwargs.update(kwargs)
            raise ValueError  # early exit to break later inference

    # patch layer 0 to catch input and kwargs
    layers[0] = Catcher(layers[0])
    # Only embeddings/rotary state and the catcher-wrapped first block need to
    # be resident. Capture hidden states in micro-batches and keep them on CPU.
    embedding_device = next(model.get_input_embeddings().parameters()).device
    for start in range(0, samples.shape[0], calib_batch_size):
        try:
            model(
                samples[start:start + calib_batch_size].to(embedding_device),
                use_cache=False,
            )
        except ValueError:  # work with early exit
            pass
    del samples
    layers[0] = layers[0].module  # restore
    inps = torch.cat(inps, dim=0)
    layer_kwargs.pop("past_key_values", None)
    layer_kwargs["use_cache"] = False

    # Gemma 4 is heterogeneous: sliding-attention and full-attention blocks
    # can use different head dimensions (and therefore different rotary
    # embeddings).  The Catcher above observes only block 0, so blindly
    # replaying its position embeddings in every block fails as soon as the
    # layer type changes.  Cache the per-type context tensors while the text
    # embeddings/rotary module are still on CUDA, then select the matching
    # tensors during the layer-wise replay below.
    gemma4_layer_context = None
    if isinstance(model, (Gemma4UnifiedForCausalLM, Gemma4UnifiedForConditionalGeneration)):
        text_model = (
            model.model
            if isinstance(model, Gemma4UnifiedForCausalLM)
            else model.model.language_model
        )
        position_ids = layer_kwargs["position_ids"].to(inps.device)
        rotary_device = next(text_model.rotary_emb.parameters(), None)
        rotary_device = (
            rotary_device.device
            if rotary_device is not None
            else next(text_model.rotary_emb.buffers()).device
        )
        rotary_input = inps[:calib_batch_size].to(rotary_device)
        position_ids = position_ids.to(rotary_device)
        position_embeddings = {
            layer_type: tuple(
                tensor.cpu()
                for tensor in text_model.rotary_emb(rotary_input, position_ids, layer_type)
            )
            for layer_type in sorted(set(model.config.layer_types))
        }
        # At the configured 1024-token calibration length, Gemma 4's sliding
        # window is also 1024, so the captured causal mask is numerically the
        # same for both layer types.  Keep it on CPU and copy it to the active
        # layer device below.  This avoids retaining calibration state on GPU.
        attention_mask = layer_kwargs.get("attention_mask")
        gemma4_layer_context = {
            "position_embeddings": position_embeddings,
            "attention_mask": attention_mask.cpu() if attention_mask is not None else None,
        }
        layer_kwargs.pop("position_embeddings", None)
        layer_kwargs.pop("attention_mask", None)

    layers[0] = layers[0].cpu()
    move_embed(model, "cpu")
    
    gc.collect()
    torch.cuda.empty_cache()

    clip_results = {
        "clip": [],
        "quantizer": {
            "version": "int-asym-fp32-fp16scale-v1",
            "bits": w_bit,
            "group_size": q_config["q_group_size"],
        },
    }

    # solve layer by layer
    for i in tqdm(range(len(layers)), desc="Running Asymmetric Clipping..."):
        layer = layers[i]
        layer = layer.cuda()
        named_linears = get_named_linears(layer)

        # Firstly, get a bounded token sample for every linear layer.
        n_micro_batches = (inps.shape[0] + calib_batch_size - 1) // calib_batch_size
        tokens_per_micro_batch = max(1, (512 + n_micro_batches - 1) // n_micro_batches)

        def cache_input_hook(m, x, y, name, feat_dict):
            x = x[0].detach().reshape(-1, x[0].shape[-1])
            stride = max(1, x.shape[0] // tokens_per_micro_batch)
            feat_dict[name].append(x[::stride][:tokens_per_micro_batch].cpu())

        input_feat = defaultdict(list)
        handles = []
        for name in named_linears:
            if any(part in name for part in ["q_", "k_", "query", "key", "Wqkv"]):
                continue
            handles.append(named_linears[name].register_forward_hook(
                functools.partial(cache_input_hook, name=name,
                                  feat_dict=input_feat)))
        # Propagate calibration activations one micro-batch at a time. The
        # training batch size is unrelated and remains unchanged.
        next_inps = []
        for start in range(0, inps.shape[0], calib_batch_size):
            micro_inps = inps[start:start + calib_batch_size].to(next(layer.parameters()).device)
            replay_kwargs = layer_kwargs
            if gemma4_layer_context is not None:
                layer_type = model.config.layer_types[i]
                replay_kwargs = dict(layer_kwargs)
                replay_kwargs["position_embeddings"] = tuple(
                    tensor.to(micro_inps.device)
                    for tensor in gemma4_layer_context["position_embeddings"][layer_type]
                )
                attention_mask = gemma4_layer_context["attention_mask"]
                replay_kwargs["attention_mask"] = (
                    attention_mask.to(micro_inps.device)
                    if attention_mask is not None
                    else None
                )
            layer_output = layer(micro_inps, **replay_kwargs)
            # Recent Transformers Qwen3 decoder layers return hidden states
            # directly, while older model families return a tuple.  Indexing
            # an already-tensor output would drop its batch dimension and make
            # the next layer's rotary embeddings incompatible.
            micro_out = layer_output[0] if isinstance(layer_output, tuple) else layer_output
            next_inps.append(micro_out.detach().cpu())
            del micro_inps, micro_out, layer_output
        inps = torch.cat(next_inps, dim=0)
        del next_inps
        for h in handles:
            h.remove()

        # now solve for clipping
        input_feat = {k: torch.cat(v, dim=0) for k, v in input_feat.items()}

        # Clear GPU memory
        torch.cuda.empty_cache()

        clip_list = auto_clip_block(layer,
                                    w_bit=w_bit, q_config=q_config,
                                    input_feat=input_feat, n_grid=clip_n_grid,
                                    clip_num_gpus=clip_num_gpus)
        
        apply_clip(layer, clip_list)
        # append prefix to make names global
        clip_results["clip"] += append_str_prefix(clip_list, get_op_name(model, layer) + ".")

        layer = layer.cpu()
        # Haotian: check activation replacement
        del input_feat
        gc.collect()
        torch.cuda.empty_cache()
        
    return clip_results


def main(args, q_config):
    if args.dump_clip and os.path.exists(args.dump_clip):
        print(f"Found existing AWQ results {args.dump_clip}, exit.")
        exit()

    model, enc = build_model_and_enc(args.model_path)

    if args.run_clip:
        assert args.dump_clip, "Please save the awq results with --dump_awq"

        clip_results = run_clip(
            model, enc,
            w_bit=args.w_bit, q_config=q_config,
            n_samples=args.n_samples, seqlen=args.seqlen, datasets=args.calib_dataset,
            data_path=args.calib_data_path, calib_batch_size=args.calib_batch_size,
            clip_n_grid=args.clip_n_grid,
            clip_num_gpus=args.clip_num_gpus,
        )

        if args.dump_clip:
            dirpath = os.path.dirname(args.dump_clip)
            os.makedirs(dirpath, exist_ok=True)
            # Publish the cache atomically. Downstream materialization jobs may
            # be waiting for this path and must never observe a partially
            # written multi-hundred-MiB torch archive.
            temporary_path = f"{args.dump_clip}.tmp.{os.getpid()}"
            torch.save(clip_results, temporary_path)
            os.replace(temporary_path, args.dump_clip)
            print("Clipping results saved at", args.dump_clip)
            
        exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, help='path of the hf model')
    parser.add_argument('--batch_size', type=int, default=8, help='batch size')
    parser.add_argument('--w_bit', type=int, default=2, help='bits of weight')
    parser.add_argument('--q_group_size', type=int, default=64)
    parser.add_argument('--quant_type', type=str, default="int", help="quant_type", choices=["int", "nf3"])
    parser.add_argument('--no_zero_point', action='store_true',
                        help="disable zero_point")
    parser.add_argument('--run_clip', action='store_true',
                        help="perform asym-clipping search process")
    parser.add_argument('--dump_clip', type=str, default=None,
                        help="save the asym-clipping search results")
    parser.add_argument('--n_samples', type=int, default=128,
                        help="Number of calibration data samples.")
    parser.add_argument('--seqlen', type=int, default=1024,
                        help="Length usage of each calibration data.")
    parser.add_argument('--calib_batch_size', type=int, default=1,
                        help='Micro-batch size for clipping activation collection.')
    parser.add_argument('--clip_n_grid', type=int, default=20,
                        help='Asymmetric positive/negative clipping grid resolution.')
    parser.add_argument('--clip_num_gpus', type=int, default=1,
                        help='Parallelize independent Linear searches within each layer.')
    parser.add_argument('--calib_data_path', type=str, default=None,
                        help='Optional local JSON/JSONL data; overrides calib_dataset.')
    parser.add_argument("--calib_dataset", type=str, default="pile",
            choices=["pile", "gsm8k","code", "openr1_math", "merged_gmc", "nemotron_code", "nemotron_math", "epicoder"],
            help="Where to extract calibration data from.",
        )

    args = parser.parse_args()

    q_config = {
        "zero_point": not args.no_zero_point,   # by default True
        "q_group_size": args.q_group_size,      # whether to use group quantization
        "quant_type": args.quant_type
    }

    print("Quantization config:", q_config)
    main(args, q_config)
