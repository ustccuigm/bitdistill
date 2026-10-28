from steerdistill.quantization.qlinear import convertModelToQuant
from steerdistill.quantization.gptq_grid import load_gptq_grid
from steerdistill.quantization.clip_utils import apply_clip, validate_clip_quantizer_metadata

import io
import inspect
import json
import logging
import os
import random
from tqdm import tqdm
from typing import Dict

import torch
from torch.distributed.fsdp import (
    fully_shard,
    FSDPModule,
    ShardingStrategy,
    CPUOffload,
    CPUOffloadPolicy,
    OffloadPolicy,
    MixedPrecisionPolicy,
)
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
import torch.distributed as dist
from torch.utils.data import DataLoader

import transformers
from transformers import Trainer
from transformers.trainer_utils import get_last_checkpoint

from steerdistill.training.mytrainer import SkillKDTrainer
from steerdistill.training.data_loading import make_supervised_data_module
from steerdistill.training.debug import add_nan_inf_hooks
from steerdistill.training.arguments import ModelArguments, DataArguments, TrainingArguments
from steerdistill.model_support import (
    decoder_layers,
    is_conditional_generation,
    load_model,
    text_backbone,
)


os.environ['NCCL_DEBUG'] = 'ERROR'
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
from steerdistill.training.logger import STEERDISTILL_DEBUG, FSDP_DEBUG, log_info, log_steerdistill_debug, log_fsdp_debug
logger = logging.getLogger(__name__)


def _make_r_io_base(f, mode: str):
    if not isinstance(f, io.IOBase):
        f = open(f, mode=mode)
    return f

def jload(f, mode="r"):
    """Load a .json file into a dictionary."""
    f = _make_r_io_base(f, mode)
    jdict = json.load(f)
    f.close()
    return jdict


DEFAULT_PAD_TOKEN = "[PAD]"
DEFAULT_EOS_TOKEN = "</s>"
DEFAULT_BOS_TOKEN = "</s>"
DEFAULT_UNK_TOKEN = "</s>"


def safe_save_model_for_hf_trainer(trainer: transformers.Trainer, output_dir: str):
    """Collects the state dict and dump to disk."""
    if trainer.is_fsdp_enabled:
        # FSDP2 SHARDED_STATE_DICT checkpoints are saved collectively by
        # Trainer at save_steps. Calling state_dict() here and only consuming
        # it on rank 0 makes DTensor run a collective after the other ranks
        # have exited. Merge the saved distributed checkpoint out of process
        # with accelerate.utils.merge_fsdp_weights instead.
        trainer.accelerator.wait_for_everyone()
        last_checkpoint = get_last_checkpoint(output_dir)
        if last_checkpoint is None:
            raise RuntimeError(
                "FSDP final save requires a checkpoint. Configure save_steps "
                "to include the final optimizer step."
            )
        if trainer.args.should_save:
            logger.info(
                "FSDP_FINAL_SAVE_SIGNAL status=sharded checkpoint=%s; "
                "merge this checkpoint before HF/GPTQ export",
                last_checkpoint,
            )
        trainer.accelerator.wait_for_everyone()
        return

    state_dict = trainer.model.state_dict()
    if trainer.args.should_save:
        cpu_state_dict = {key: value.cpu() for key, value in state_dict.items()}
        del state_dict
        trainer._save(output_dir, state_dict=cpu_state_dict)  # noqa


def smart_tokenizer_and_embedding_resize(
    special_tokens_dict: Dict,
    tokenizer: transformers.PreTrainedTokenizer,
    model: transformers.PreTrainedModel,
):
    """Resize tokenizer and embedding.

    Note: This is the unoptimized version that may make your embedding size not be divisible by 64.
    """
    num_new_tokens = tokenizer.add_special_tokens(special_tokens_dict)
    model.resize_token_embeddings(len(tokenizer))

    if num_new_tokens > 0:
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg


def get_tokenizer(model_args: ModelArguments, training_args: TrainingArguments):
    logger.info(f"Loading tokenizer from {model_args.model_name_or_path}")
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=training_args.cache_dir,
        model_max_length=training_args.model_max_length,
        padding_side="right",
        use_fast=True,
        fix_mistral_regex=True,
    )
    if tokenizer.eos_token is None:
        tokenizer.add_special_tokens(
            {
                "eos_token": DEFAULT_EOS_TOKEN,
                "bos_token": DEFAULT_BOS_TOKEN,
                "unk_token": DEFAULT_UNK_TOKEN,
            }
        )
        logger.info("Tokenizer has not eos token")
    return tokenizer

def get_model_kwargs(model_args: ModelArguments, training_args: TrainingArguments):
    n_gpus = torch.cuda.device_count()
    max_memory = f'80000MB'
    max_memory = {i: max_memory for i in range(n_gpus)}
    device_map = "auto"

    if "34B" in model_args.model_name_or_path:
        device_map = None

    # if we are in a distributed setting, we need to set the device map and max memory per device
    if os.environ.get('LOCAL_RANK') is not None:
        # Accelerate/FSDP owns device placement. Loading a full 8B model onto
        # every local GPU before sharding causes a large transient memory spike.
        device_map = None
        max_memory = None
    
    if training_args.use_flash_attn:
        attn_implementation = "flash_attention_2"
    else:
        # Native PyTorch SDPA avoids materializing the full 4K x 4K attention
        # matrix and is available on the target 4090 hosts without flash-attn.
        attn_implementation = "sdpa"

    model_kwargs = {
        "max_memory": max_memory,
        "device_map": device_map,
        "attn_implementation": attn_implementation,
    }
    return model_kwargs


def train():
    # os.environ["TOKENIZERS_PARALLELISM"] = "false"

    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()
    if not training_args.skill_distill or not training_args.train_kd or training_args.train_rlvr:
        raise ValueError("Use train_online_step.sh for the SteerDistill training route")

    if os.environ.get("LOCAL_RANK") is not None and not dist.is_initialized():
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        dist.init_process_group(backend="nccl")

    random.seed(training_args.seed)
    model_kwargs = get_model_kwargs(model_args, training_args)

    tokenizer = get_tokenizer(model_args, training_args)
    data_module = make_supervised_data_module(tokenizer=tokenizer, data_args=data_args)
    if training_args.trajectory_online:
        from steerdistill.training.online_step import prepare_online_data
        if not training_args.skill_distill or training_args.deepspeed:
            raise ValueError("Trajectory online training requires the FSDP SteerDistill route")
        data_module = prepare_online_data(data_module, training_args)

    teacher_model = None
    skill_reference_model = None
    mean_prob = 0
    phase_reference_offload = (
        training_args.skill_distill
        and training_args.reference_phase_offload
        and not training_args.deepspeed
    )
    if training_args.train_kd and not training_args.offline_soft_labels:
        teacher_path = (
            model_args.teacher_model_name_or_path
            or model_args.model_name_or_path
        )
        logger.info("loading Teacher Model from %s...", teacher_path)
        teacher_model = load_model(
            teacher_path,
            torch_dtype=torch.bfloat16,
            **model_kwargs
        )
        if training_args.deepspeed:
            # Match SteerDistill's official DeepSpeed launch: the frozen BF16
            # teacher is replicated on each rank and the QAT student is managed
            # by ZeRO-2 through Trainer.
            teacher_model.cuda()
        else:
            fsdp_kwargs = {
                "reshard_after_forward": True,
                "mp_policy": MixedPrecisionPolicy(
                    param_dtype=torch.bfloat16,
                    reduce_dtype=torch.float32,
                ),
                # Frozen references are only needed for a logits forward. Keep
                # their idle shards in host memory so long-context student
                # backward has the GPU budget it needs.
                "offload_policy": OffloadPolicy() if phase_reference_offload else CPUOffloadPolicy(pin_memory=True),
            }
            for layer in decoder_layers(teacher_model):
                fully_shard(layer, **fsdp_kwargs)
            # The conditional wrapper calls the text embedding before the
            # backbone forward. Keep embedding ownership at the outer root,
            # whose pre-forward hook runs before that access.
            fully_shard(teacher_model, **fsdp_kwargs)
        # teacher_model = FSDP(teacher_model,
        #                      sharding_strategy=ShardingStrategy.FULL_SHARD,
        #                      cpu_offload=CPUOffload(offload_params=True))
        teacher_model.eval()
        for param in teacher_model.parameters():
            param.requires_grad = False
        teacher_model.config.use_cache = False
        if tokenizer.pad_token is None:
            smart_tokenizer_and_embedding_resize(
                special_tokens_dict=dict(pad_token=DEFAULT_PAD_TOKEN),
                tokenizer=tokenizer,
                model=teacher_model,
            )
        logger.info("Teacher Model loaded")

        if training_args.kd_loss_type == "cakld":
            logger.info("Get the main Prob!")
            probDataloader = DataLoader(
                data_module['train_dataset'],
                shuffle=False,
                collate_fn=data_module['data_collator'],
                batch_size=training_args.per_device_train_batch_size,
                drop_last=False,
            )

            prob = 0
            for step, batch in tqdm(enumerate(probDataloader)):
                if step > training_args.cakld_steps:
                    break
                batch = {k: v.to(teacher_model.device) for k, v in batch.items()}
                batch.pop("labels", None)
                device = f"cuda:{int(os.environ.get('LOCAL_RANK', '0'))}"
                log_fsdp_debug(logger, f"Coeff step {step}: before allocated memory = {torch.cuda.memory_allocated(device) / 1024 ** 3:.2f} GB, reserved: {torch.cuda.memory_reserved(device) / 1024 ** 3:.2f} GB")
                with torch.no_grad():
                    outputs = teacher_model(**batch)
                log_fsdp_debug(logger, f"Coeff step {step}: after allocated memory = {torch.cuda.memory_allocated(device) / 1024 ** 3:.2f} GB, reserved: {torch.cuda.memory_reserved(device) / 1024 ** 3:.2f} GB")
                logits = outputs.get("logits").contiguous()
                prob1 = torch.nn.functional.softmax(logits, dim=-1)
                prob1 = torch.max(prob1, dim=-1).values
                prob += prob1.mean()
                del logits, outputs
            mean_prob = prob / training_args.cakld_steps
            mean_prob = torch.Tensor(mean_prob.to(teacher_model.device))
            dist.all_reduce(mean_prob, op=dist.ReduceOp.SUM)
            mean_prob = mean_prob / dist.get_world_size()
            logger.info(f"Get the coefficient: {mean_prob}")
    if training_args.skill_distill:
        if not training_args.train_kd:
            raise ValueError("skill_distill requires train_kd=True.")
        reference_path = model_args.skill_reference_model_name_or_path
        if not reference_path:
            raise ValueError("skill_distill requires --skill_reference_model_name_or_path.")
        logger.info("Loading frozen previous-step W4 Skill reference from %s", reference_path)
        skill_reference_model = load_model(
            reference_path,
            torch_dtype=torch.bfloat16,
            **model_kwargs,
        )
        skill_reference_model, _ = convertModelToQuant(
            skill_reference_model,
            compute_dtype=torch.bfloat16,
            quant_type=training_args.quant_type,
            q_group_size=training_args.q_group_size,
            w_bit=training_args.bits,
            activation_bits=training_args.activation_bits,
        )
        if training_args.clip is not None:
            reference_clip = torch.load(training_args.clip, map_location="cpu")
            validate_clip_quantizer_metadata(reference_clip, training_args.bits, training_args.q_group_size)
            apply_clip(skill_reference_model, reference_clip)
            del reference_clip
        if training_args.deepspeed:
            skill_reference_model.cuda()
        else:
            reference_fsdp_kwargs = {
                "reshard_after_forward": True,
                "mp_policy": MixedPrecisionPolicy(
                    param_dtype=torch.bfloat16, reduce_dtype=torch.float32,
                ),
                # The W4 reference is frozen and is queried one turn at a
                # time. CPU offload prevents it from competing with the
                # trainable student's long-context activations.
                "offload_policy": OffloadPolicy() if phase_reference_offload else CPUOffloadPolicy(pin_memory=True),
            }
            for layer in decoder_layers(skill_reference_model):
                fully_shard(layer, **reference_fsdp_kwargs)
            fully_shard(skill_reference_model, **reference_fsdp_kwargs)
        skill_reference_model.eval()
        skill_reference_model.config.use_cache = False
        for param in skill_reference_model.parameters():
            param.requires_grad = False
        logger.info("Frozen same-quantizer W4 Skill reference loaded")
    if phase_reference_offload:
        # NVIDIA NeMo-RL keeps frozen references off the training GPU between
        # phases, then onloads them once for teacher logprob inference. This
        # avoids per-layer CPU transfers during every forward.
        for reference in (teacher_model, skill_reference_model):
            if reference is not None:
                reference.to("cpu")
        logger.info("STEER_REFERENCE_PHASE_SIGNAL phase=cpu status=ready")
    torch.cuda.empty_cache()

    logger.info(f"Loading model from {model_args.model_name_or_path}")
    model = load_model(
        model_args.model_name_or_path,
        torch_dtype=torch.bfloat16,
        **model_kwargs
    )

    if training_args.quant_type is not None:
        logger.info("Converting the model to qat, this may take a while...")
        quant_grid = None
        if training_args.quant_grid_path is not None:
            quant_grid = load_gptq_grid(
                training_args.quant_grid_path,
                training_args.bits,
                training_args.q_group_size,
            )
            logger.info(
                "W4_FIXED_GRID_SIGNAL: status=loaded layers=%d source=%s",
                len(quant_grid), training_args.quant_grid_path,
            )
        model, _ = convertModelToQuant(
            model,
            compute_dtype=torch.bfloat16,
            quant_type=training_args.quant_type,
            q_group_size=training_args.q_group_size,
            w_bit=training_args.bits,
            activation_bits=training_args.activation_bits,
            quant_grid=quant_grid,
        )
        # Persist quantizer provenance so an old checkpoint cannot be silently
        # re-exported under a different fake-quant definition.
        model.config.steerdistill_quantization = {
            "version": (
                "int-asym-fixed-gptq-grid-v1"
                if quant_grid is not None
                else "int-asym-fp32-fp16scale-v1"
            ),
            "quant_type": training_args.quant_type,
            "bits": training_args.bits,
            "activation_bits": training_args.activation_bits,
            "group_size": training_args.q_group_size,
        }
        if training_args.quant_grid_path is not None:
            model.config.steerdistill_quantization["grid_path"] = (
                training_args.quant_grid_path
            )

    if training_args.clip is not None:
        logger.info(f"Loading pre-computed Clipping results from {training_args.clip}")
        clip_results = torch.load(training_args.clip, map_location="cpu")
        if training_args.quant_type is not None:
            validate_clip_quantizer_metadata(
                clip_results,
                training_args.bits,
                training_args.q_group_size,
            )
        apply_clip(model, clip_results)
        logger.info("Clipping init successfully!")
    model.config.use_cache = False
    model.kd_loss_scale = 1.0

    if tokenizer.pad_token is None:
        logger.info("Tokenizer has not padding token")
        smart_tokenizer_and_embedding_resize(
            special_tokens_dict=dict(pad_token=DEFAULT_PAD_TOKEN),
            tokenizer=tokenizer,
            model=model,
        )

    if STEERDISTILL_DEBUG:    
        add_nan_inf_hooks(model)
        # hook_last_hidden(model)

    logger.info("Waiting for other processes to synchronize...")
    torch.distributed.barrier()
    if int(os.environ.get('LOCAL_RANK', '0')) == 0:
        logger.info(f"Training_args: {training_args}")

    logger.info("Starting trainer...")
    trainer_text_processor = (
        {"processing_class": tokenizer}
        if "processing_class" in inspect.signature(Trainer.__init__).parameters
        else {"tokenizer": tokenizer}
    )
    trainer = SkillKDTrainer(
        model=model, teacher_model=teacher_model,
        skill_reference_model=skill_reference_model, args=training_args, **data_module,
        **trainer_text_processor,
    )

    try:
        last_ckpt: str = get_last_checkpoint(training_args.output_dir)
    except Exception as e:
        last_ckpt = None
    
    if training_args.trajectory_online:
        previous = training_args.online_previous_step
        if training_args.max_steps != previous + 1:
            raise ValueError("Online training must perform exactly one new optimizer update")
        if previous:
            expected = os.path.join(training_args.output_dir, f"checkpoint-{previous}")
            if last_ckpt != expected or not training_args.may_resume:
                raise ValueError("Online optimizer checkpoint does not match the sampling step")
            trainer.train(resume_from_checkpoint=expected)
        elif last_ckpt is not None:
            raise ValueError("Initial online step cannot reuse an existing learner")
        else:
            trainer.train()
    elif training_args.may_resume and last_ckpt is not None:
        while True:
            try:
                logger.info(f"Try resuming training from checkpoint...: {last_ckpt}")
                trainer.train(resume_from_checkpoint=last_ckpt)
                break
            except FileNotFoundError as e:
                logger.warning(f"Checkpoint {last_ckpt} not found or corrupted.")
                # Try the previous checkpoint
                # Extract the current checkpoint step
                ckpt_step = int(last_ckpt.strip('/').split("-")[-1])
                last_ckpt = os.path.join(training_args.output_dir, f"checkpoint-{int(ckpt_step - training_args.save_steps)}")
    else:
        logger.info(f"Starting training from scratch.")
        trainer.train()

    trainer.save_state()
    if not training_args.skip_final_save:
        safe_save_model_for_hf_trainer(trainer=trainer, output_dir=training_args.output_dir)
    else:
        logger.info("Skipping final root checkpoint save; optimizer-step checkpoints are retained.")
    if dist.is_initialized():
        dist.destroy_process_group()

if __name__ == "__main__":
    train()
