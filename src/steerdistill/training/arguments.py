import json
from dataclasses import dataclass, field
import transformers
from typing import Optional, Dict


def arg_dict(arg: str) -> Dict[str, float]:
    """Convert a JSON-like string of key-value pairs into a dictionary."""
    if not arg:
        return {}
    if arg.startswith("{") and arg.endswith("}"):
        return json.loads(arg)
    else:
        return dict(item.split("=") for item in arg.split(","))

@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(default="facebook/opt-125m")
    teacher_model_name_or_path: Optional[str] = field(
        default=None,
        metadata={"help": "Frozen teacher checkpoint; defaults to the student initialization."},
    )
    skill_reference_model_name_or_path: Optional[str] = field(
        default=None,
        metadata={"help": "Frozen previous-step W4 master used for Skill-aware recovery targets."},
    )


@dataclass
class DataArguments:
    data_path: str = field(default=None, metadata={"help": "Path to the training data."})
    max_train_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of training examples to this "
            "value if set."
        },
    )

@dataclass
class TrainingArguments(transformers.TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")
    model_max_length: int = field(
        default=32768,
        metadata={
            "help": "Maximum sequence length. The SteerDistill route keeps complete "
            "assistant responses and fails on responses longer than this window."
        },
    )
    overwrite_output_dir: bool = field(default=False)
    bits: int = field(
        default=2,
        metadata={"help": "Weight bit width. Asymmetric INT supports 2, 3, 4, or 8."}
    )
    q_group_size: int = field(
        default=64,
        metadata={"help": "Quantization Group Size."}
    )
    activation_bits: int = field(default=16, metadata={"help": "16 or dynamic per-token symmetric INT8 linear inputs."})
    quant_type: str = field(
        default="int2-asym",
        metadata={"help": "Quantization type: ste-n2f3 or int{2,3,4,8}-asym."}
    )
    quant_grid_path: Optional[str] = field(
        default=None,
        metadata={
            "help": "Optional GPTQ checkpoint whose per-layer W4 scale/zero grid "
            "is shared by learner forward and rollout export."
        },
    )
    clip: str = field(
        default=None,
        metadata={"help": "The path of clip cache"}
    )
    train_kd: bool = field(default=False, metadata={"help": 'Whether to use KD to QAT'})
    train_rlvr: bool = field(default=False, metadata={"help": "Train with a clipped on-policy RLVR objective."})
    rlvr_clip_epsilon: float = field(default=0.2, metadata={"help": "PPO/GRPO ratio clipping epsilon."})
    rlvr_beta: float = field(default=0.01, metadata={"help": "Sampled-action KL penalty coefficient."})
    rlvr_tis_cap: float = field(
        default=2.0,
        metadata={"help": "Upper cap for old-policy/rollout truncated importance weights."},
    )
    kd_tmp: int = field(
        default=1,
        metadata={"help": "Temperature of KD"}
    )
    kd_loss_type: str = field(
        default=None,
        metadata={"help": "Type of loss function when KD-QAT"}
    )
    kd_loss_top_k: int = field(
        default=0,
        metadata={"help": "Top K logits to calculate loss. 0 means all logits."}
    )
    distill_ce_weight: float = field(
        default=0.0,
        metadata={"help": "Weight of assistant-token hard-label CE in a distillation run."},
    )
    distill_kl_weight: float = field(
        default=1.0,
        metadata={"help": "Weight of the soft-label KL objective in a distillation run."},
    )
    trajectory_online: bool = field(default=False)
    opd_global_batch_size: int = field(default=16)
    opd_micro_batch_size: int = field(default=1)
    reference_phase_offload: bool = field(default=True)
    online_turn_batch_size: int = field(default=4)
    online_previous_step: int = field(default=0)
    online_distill: bool = field(
        default=False,
        metadata={"help": "Sample fresh student continuations before reverse-KL distillation."},
    )
    mixed_turn_distill: bool = field(
        default=False,
        metadata={
            "help": "Use per-record student/teacher rollout roles: reverse KL "
            "on student turns and forward KL on teacher/critique turns."
        },
    )
    qguard_opd: bool = field(
        default=False,
        metadata={
            "help": "Enable reverse-KL-only Q-Guard decision/turn weighting."
        },
    )
    boundary_opd: bool = field(
        default=False,
        metadata={
            "help": "Reverse KL on W4 turns and decision-only forward KL on "
            "the first teacher/W4 boundary correction."
        },
    )
    skill_distill: bool = field(
        default=False,
        metadata={
            "help": "Ordinary reverse-KL OPD plus verifier-approved Skill recovery distillation."
        },
    )
    qguard_decision_weight: float = field(
        default=2.0,
        metadata={"help": "Within-turn weight for structured decision tokens."},
    )
    qguard_turn_norm_start_ratio: float = field(
        default=0.1,
        metadata={"help": "Global progress at which turn normalization starts."},
    )
    qguard_turn_norm_end_ratio: float = field(
        default=0.7,
        metadata={"help": "Global progress at which turn normalization reaches one."},
    )
    qguard_turn_norm_max_alpha: float = field(
        default=1.0,
        metadata={
            "help": "Maximum turn-normalized mixture weight; 1 preserves legacy behavior."
        },
    )
    qguard_progress_start: float = field(
        default=0.0,
        metadata={"help": "Global multi-step progress at this trainer invocation's start."},
    )
    qguard_progress_end: float = field(
        default=1.0,
        metadata={"help": "Global multi-step progress at this trainer invocation's end."},
    )
    offline_soft_labels: bool = field(
        default=False,
        metadata={"help": "Use cached teacher top-k logprobs instead of loading a teacher model."},
    )
    online_rollout_max_new_tokens: int = field(
        default=16,
        metadata={"help": "Number of student tokens sampled for each online distillation step."},
    )
    online_rollout_temperature: float = field(
        default=1.0,
        metadata={"help": "Student sampling temperature used by online distillation."},
    )
    cakld_steps: int = field(
        default=10,
        metadata={"help": "How many step to caculate the coefficient of CAKLD."}
    )

    mkld_warmup_steps: int = field(
        default=50,
        metadata={"help": "Number of warmup steps (warmup means using cakld loss) for MKLD loss."}
    )
    mkld_reverse: bool = field(
        default=False,
        metadata={"help": "Whether to reverse the MKLD loss masks."}
    )

    ranking_type: str = field(
        default="none",
        metadata={"help": "Type of ranking loss to use. Should be one of [`none`, `dcg_pair_logistic`]."}
    )
    ranking_R: int = field(
        default=32,
        metadata={"help": "Top-R for ranking loss."}
    )
    ranking_beta: float = field(
        default=10000,
        metadata={"help": "Beta parameter for ranking loss."}
    )

    use_teacher_entropy_coeff: bool = field(
        default=False,
        metadata={"help": "Whether to use teacher-entropy as token-level KD coefficient."}
    )

    token_curriculum: Optional[str] = field(
        default=None,
        metadata={"help": "The token-level teacher-entropy curriculum learning setting. "
                  "If not set, no curriculum learning is used. Choices: [None, 'const', 'linear', 'exponential']. Default: None."}
    )
    token_curriculum_min: Optional[float] = field(
        default=None,
        metadata={"help": "The minimum value of the token-level curriculum threshold. "
                  "When exponential is used, this value will be used as the starting point. Default: None."}
    )
    token_curriculum_max: Optional[float] = field(
        default=None,
        metadata={"help": "The maximum value of the token-level curriculum threshold. Default: None."}
    )
    token_curriculum_exp_base: Optional[float] = field(
        default=None,
        metadata={"help": "The exponential base for exponential curriculum learning. Default: None."}
    )
    token_curriculum_end_step: Optional[int] = field(
        default=None,
        metadata={"help": "The step at which the token-level curriculum reaches its maximum threshold. Default: None."}
    )

    wasserstein_sinkhorn_reg: float = field(
        default=0.1,
        metadata={"help": "The regularization coefficient for Sinkhorn algorithm in Wasserstein loss."}
    )
    wasserstein_num_iters: int = field(
        default=10,
        metadata={"help": "The number of iterations for Sinkhorn algorithm in Wasserstein loss."}
    )

    use_flash_attn: bool = field(
        default=False,
        metadata={"help": "Whether to use Flash Attention"}
    )
    lr_scheduler_kwargs: Optional[arg_dict] = field(
        default=None,
        metadata={
            "help": "Additional kwargs for the learning rate scheduler. "
            "This is a JSON string that will be parsed into a dictionary."
        },
    )
    may_resume: bool = field(
        default=False,
        metadata={"help": "Whether to resume training from the last checkpoint."}
    )
    skip_final_save: bool = field(
        default=False,
        metadata={"help": "Skip the final root checkpoint save while retaining step checkpoints."},
    )
