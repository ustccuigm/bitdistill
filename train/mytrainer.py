"""SteerDistill token-normalized online trajectory distillation."""
import logging
import os

import torch
from torch.nn import functional as F
from transformers import Trainer

from arguments import TrainingArguments

logger = logging.getLogger(__name__)


class SkillKDTrainer(Trainer):
    """Identity-safe Skill OPD with no routing or loss-scale hyperparameters."""

    def __init__(self, teacher_model, skill_reference_model, args: TrainingArguments, **kwargs):
        super().__init__(args=args, **kwargs)
        if teacher_model is None or skill_reference_model is None:
            raise ValueError("Skill OPD requires frozen BF16 teacher and sampling-step W4 reference.")
        if args.kd_loss_type != "reverse" or args.kd_loss_top_k != 0:
            raise ValueError("Skill OPD keeps full-vocabulary reverse KL as its base OPD objective.")
        if args.distill_ce_weight != 0.0 or args.distill_kl_weight != 1.0:
            raise ValueError("Skill OPD uses one token-normalized KL objective.")
        if args.online_distill or args.mixed_turn_distill or args.qguard_opd or args.boundary_opd:
            raise ValueError("Skill OPD is an independent external-rollout route.")
        self.teacher_model = teacher_model
        self.skill_reference_model = skill_reference_model
        self.reference_phase_offload = getattr(args, "reference_phase_offload", True)
        if getattr(args, "trajectory_online", False):
            # compute_loss normalizes over the full accumulation batch below.
            # Prevent Trainer from dividing a second time by microbatch count.
            self.model_accepts_loss_kwargs = True
            if self.accelerator.gradient_accumulation_steps != 1:
                raise ValueError("Trainer must own gradient accumulation in online mode")

    def _get_train_sampler(self, train_dataset=None):
        if getattr(self.args, "trajectory_online", False):
            from torch.utils.data import SequentialSampler
            return SequentialSampler(train_dataset if train_dataset is not None else self.train_dataset)
        return super()._get_train_sampler(train_dataset)

    def _move_references(self, device, need_teacher=False, need_skill=False):
        """Stage only the frozen reference needed by the current microbatch.

        The student stays resident on the training GPU. A global online batch
        can contain both ordinary and repaired turns, so keeping both frozen
        references resident wastes the memory needed by long-context logits.
        This remains phase-level movement: complete references move as units,
        never individual decoder layers.
        """
        if not self.reference_phase_offload or not torch.cuda.is_available():
            return
        references = (
            (self.teacher_model, bool(need_teacher)),
            (self.skill_reference_model, bool(need_skill)),
        )
        for reference, active in references:
            if reference is not None:
                reference.to(device if device.type == "cuda" and active else "cpu")
        if device.type == "cpu":
            torch.cuda.empty_cache()
        active = []
        if need_teacher:
            active.append("teacher")
        if need_skill:
            active.append("w4_reference")
        logger.info(
            "STEER_REFERENCE_PHASE_SIGNAL phase=%s device=%s active=%s",
            "gpu" if device.type == "cuda" else "cpu",
            device,
            "+".join(active) if active else "none",
        )

    def get_batch_samples(self, epoch_iterator, num_batches, device):
        if not getattr(self.args, "trajectory_online", False):
            return super().get_batch_samples(epoch_iterator, num_batches, device)
        from online_step import collect_update_batch
        return collect_update_batch(
            epoch_iterator, num_batches, device,
            optimizer_step=self.state.global_step + 1,
        )

    def training_step(self, model, inputs, num_items_in_batch=None):
        phase_switch = self.reference_phase_offload and torch.cuda.is_available()
        try:
            if not getattr(self.args, "trajectory_online", False):
                if phase_switch:
                    self._move_references(
                        torch.device("cuda", torch.cuda.current_device()),
                        need_teacher=True,
                    )
                return super().training_step(model, inputs, num_items_in_batch)
            from online_step import iter_collective_microbatches
            total = torch.zeros((), device=self.args.device)
            microbatches = list(iter_collective_microbatches(inputs, self.args.device))
            local_teacher = any(
                bool(batch["skill_distill_modes"].eq(0).any()
                     or batch["skill_distill_modes"].eq(2).any())
                for batch in microbatches
            )
            local_skill = any(
                bool(batch["skill_distill_modes"].eq(1).any()
                     or batch["skill_distill_modes"].eq(3).any())
                for batch in microbatches
            )
            modes_device = microbatches[0]["skill_distill_modes"].device
            need_teacher = self._global_any(local_teacher, modes_device)
            need_skill = self._global_any(local_skill, modes_device)
            if phase_switch and not (need_teacher and need_skill):
                # NVIDIA-style global-batch staging: a homogeneous batch moves
                # its single frozen reference once, then accumulates all turns.
                self._move_references(
                    torch.device("cuda", torch.cuda.current_device()),
                    need_teacher=need_teacher,
                    need_skill=need_skill,
                )
            try:
                for batch in microbatches:
                    microbatch = dict(batch)
                    if phase_switch and need_teacher and need_skill:
                        # Mixed ordinary/repair batches cannot keep both frozen
                        # references resident on an 8B learner GPU.
                        modes = microbatch["skill_distill_modes"]
                        local_micro_teacher = bool(modes.eq(0).any() or modes.eq(2).any())
                        local_micro_skill = bool(modes.eq(1).any() or modes.eq(3).any())
                        micro_teacher = self._global_any(local_micro_teacher, modes.device)
                        micro_skill = self._global_any(local_micro_skill, modes.device)
                        self._move_references(
                            torch.device("cuda", torch.cuda.current_device()),
                            need_teacher=micro_teacher,
                            need_skill=micro_skill,
                        )
                    total += super().training_step(model, microbatch, num_items_in_batch)
                    if phase_switch and need_teacher and need_skill:
                        self._move_references(torch.device("cpu"))
            finally:
                if phase_switch and not (need_teacher and need_skill):
                    self._move_references(torch.device("cpu"))
            return total
        finally:
            if phase_switch:
                self._move_references(torch.device("cpu"))

    @staticmethod
    def _kl_sum(student_logits, reference_logits, reverse: bool):
        if student_logits.shape != reference_logits.shape:
            raise ValueError(f"Aligned logits differ: {student_logits.shape} vs {reference_logits.shape}")
        total = student_logits.new_zeros((), dtype=torch.float32)
        for start in range(0, student_logits.shape[0], 16):
            student_lp = F.log_softmax(student_logits[start:start + 16].float(), dim=-1)
            reference_lp = F.log_softmax(reference_logits[start:start + 16].float(), dim=-1)
            if reverse:
                total = total + F.kl_div(reference_lp, student_lp, reduction="sum", log_target=True)
            else:
                total = total + F.kl_div(student_lp, reference_lp, reduction="sum", log_target=True)
        return total

    @staticmethod
    def _flatten_rows(logits, labels, row_mask):
        pieces, tokens = [], []
        for row in row_mask.nonzero(as_tuple=False).flatten().tolist():
            active = labels[row].ne(-100)
            if active.any():
                pieces.append(logits[row][active])
                tokens.append(labels[row][active])
        if not pieces:
            return logits.new_empty((0, logits.shape[-1])), labels.new_empty((0,))
        return torch.cat(pieces), torch.cat(tokens)

    @staticmethod
    def _global_any(local_value: bool, device) -> bool:
        """Keep optional frozen-reference forwards collective-safe under FSDP."""
        flag = torch.tensor(int(local_value), device=device, dtype=torch.int32)
        if torch.distributed.is_available() and torch.distributed.is_initialized():
            torch.distributed.all_reduce(flag, op=torch.distributed.ReduceOp.MAX)
        return bool(flag.item())

    @staticmethod
    def _forward_hidden_at_positions(model, model_inputs, positions):
        """Use the FSDP root forward while bypassing the vocabulary projection."""
        lm_head = getattr(model, "lm_head", None)
        if lm_head is None:
            return None
        original_forward = lm_head.forward
        captured_weight = None
        captured_hidden = None

        def identity_forward(hidden_states):
            nonlocal captured_weight, captured_hidden
            captured_hidden = hidden_states
            # The probe runs while the FSDP root has materialized the tied
            # lm-head parameter. Capture that regular tensor before the root
            # reshard hook releases its DTensor storage.
            original_forward(hidden_states[:, :1, :])
            weight = lm_head.weight
            full_tensor = getattr(weight, "full_tensor", None)
            captured_weight = (
                full_tensor().clone() if full_tensor is not None
                else weight.clone()
            )
            return hidden_states

        lm_head.forward = identity_forward
        try:
            outputs = model(
                **model_inputs,
                logits_to_keep=positions,
            )
            return captured_hidden, captured_weight
        finally:
            lm_head.forward = original_forward

    @staticmethod
    def _project_logits(model, hidden, weight):
        logits = F.linear(hidden, weight)
        config = getattr(model, "config", None)
        if config is not None and hasattr(config, "get_text_config"):
            config = config.get_text_config()
        cap = getattr(config, "final_logit_softcapping", None)
        if cap is not None:
            logits = torch.tanh(logits / cap) * cap
        return logits

    @staticmethod
    def _response_positions(labels):
        rows = [row[1:].ne(-100).nonzero(as_tuple=False).flatten() for row in labels]
        width = max(1, max(row.numel() for row in rows))
        positions = labels.new_zeros((len(rows), width))
        tokens = labels.new_full((len(rows), width), -100)
        for index, row in enumerate(rows):
            positions[index, :row.numel()] = row
            tokens[index, :row.numel()] = labels[index, row + 1]
        return positions, tokens

    @staticmethod
    def _aligned_forward(model, inputs, positions, hidden=False):
        selected, inverse = positions.flatten().unique(sorted=True, return_inverse=True)
        if hidden:
            values, weight = SkillKDTrainer._forward_hidden_at_positions(model, inputs, selected)
        else:
            values = model(**inputs, logits_to_keep=selected).logits
        indices = inverse.reshape_as(positions).unsqueeze(-1).expand(-1, -1, values.shape[-1])
        aligned = values.gather(1, indices)
        return (aligned, weight) if hidden else aligned

    @staticmethod
    def _full_linear_weight(linear):
        weight = linear.weight
        full_tensor = getattr(weight, "full_tensor", None)
        return full_tensor() if full_tensor is not None else weight

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        skill_input_ids = inputs.pop("skill_input_ids")
        skill_attention_mask = inputs.pop("skill_attention_mask")
        skill_labels = inputs.pop("skill_labels")
        modes = inputs.pop("skill_distill_modes")
        online_mask = inputs.pop("online_row_mask", None)
        inputs.pop("online_record_ids", None)

        # Ordinary OPD and teacher takeover use the unsteered prefix; verified
        # recovery and direct Steer targets use the injected prefix. These
        # rendered contexts legitimately have different lengths, so their
        # selected completion positions cannot be shared.
        base_row_mask = modes.eq(0) | modes.eq(2)
        skill_row_mask = modes.eq(1) | modes.eq(3)
        if online_mask is not None:
            base_row_mask = base_row_mask & online_mask
            skill_row_mask = skill_row_mask & online_mask
        need_base = self._global_any(bool(base_row_mask.any()), modes.device)
        need_skill = self._global_any(bool(skill_row_mask.any()), modes.device)
        if not need_base and not need_skill:
            if online_mask is None:
                raise ValueError("Skill OPD batch has no active distillation rows.")
            # OnlineGlobalBatches pads an empty rank with a real-shaped dummy
            # row. In a distributed run _global_any selects the branch used by
            # the active ranks; this local fallback keeps single-process
            # validation graph-connected while contributing zero tokens.
            need_base = True

        def prediction_positions(target_labels):
            selected = (
                target_labels[..., 1:].ne(-100).any(dim=0)
                .nonzero(as_tuple=False).flatten()
            )
            # Empty local shards still participate in collective FSDP forwards.
            return selected if selected.numel() else target_labels.new_zeros(1)

        base_positions = prediction_positions(labels)
        skill_positions = prediction_positions(skill_labels)
        base_inputs = inputs
        skill_inputs = {
            "input_ids": skill_input_ids,
            "attention_mask": skill_attention_mask,
        }

        # A full-vocabulary logit tensor for a 32K-token row is several GB.
        # Keep each transformer forward on GPU, but materialize only a bounded
        # token slice at a time. The scalar terms still contribute to one
        # token-normalized optimizer update.
        logits_chunk_size = max(1, int(os.environ.get("STEER_LOGITS_CHUNK_SIZE", "256")))
        chunk_backward = (
            online_mask is not None
            and os.environ.get("STEER_BACKWARD_CHUNKS", "0").lower()
            in {"1", "true", "yes"}
        )
        if chunk_backward:
            from online_step import global_token_loss
        total_sum = None
        total_count = 0
        term_sums = {}
        token_counts = {}
        row_counts = {}
        last_student_outputs = None
        mode_specs = (
            (0, "ordinary_reverse", True),
            (1, "skill_forward", False),
            (2, "rescue_forward", False),
            (3, "steer_forward", False),
        )
        for mode, name, reverse in mode_specs:
            term_sums[name] = None
            token_counts[name] = 0
            row_mask = modes.eq(mode)
            if online_mask is not None:
                row_mask = row_mask & online_mask
            row_counts[name] = int(row_mask.sum().item())

        branches = []
        if need_base:
            branches.append((
                base_inputs, labels, base_positions, self.teacher_model,
                ((0, "ordinary_reverse", True), (2, "rescue_forward", False)),
            ))
        if need_skill:
            branches.append((
                skill_inputs, skill_labels, skill_positions,
                self.skill_reference_model,
                ((1, "skill_forward", False), (3, "steer_forward", False)),
            ))

        for branch_inputs, branch_labels, positions, reference_model, branch_specs in branches:
            learner_positions, selected_labels = self._response_positions(labels)
            reference_positions, reference_labels = self._response_positions(branch_labels)
            if not torch.equal(selected_labels, reference_labels):
                raise ValueError("Learner and reference response tokens differ")
            student_hidden = student_lm_weight = None
            reference_hidden = reference_lm_weight = None
            student_outputs = None
            if getattr(model, "lm_head", None) is not None:
                student_hidden, student_lm_weight = self._aligned_forward(
                    model, base_inputs, learner_positions, hidden=True
                )
            with torch.no_grad():
                if getattr(reference_model, "lm_head", None) is not None:
                    reference_hidden, reference_lm_weight = self._aligned_forward(
                        reference_model, branch_inputs, reference_positions, hidden=True
                    )

            # Chunk-local projection VJPs avoid retaining a complete 32K
            # vocabulary graph. Propagate them through the FSDP model once per
            # context branch, so all ranks execute the same collective pattern.
            student_hidden_graph = student_hidden
            student_weight_graph = student_lm_weight
            if chunk_backward and student_hidden is not None:
                student_hidden = student_hidden.detach().requires_grad_(True)
                student_lm_weight = student_lm_weight.detach().requires_grad_(True)

            for start in range(0, selected_labels.shape[1], logits_chunk_size):
                end = min(start + logits_chunk_size, selected_labels.shape[1])
                if student_hidden is not None:
                    student_logits = self._project_logits(
                        model, student_hidden[:, start:end, :], student_lm_weight
                    )
                else:
                    student_logits = self._aligned_forward(
                        model, base_inputs, learner_positions[:, start:end])
                if reference_hidden is not None:
                    reference_logits = self._project_logits(
                        reference_model, reference_hidden[:, start:end, :], reference_lm_weight
                    )
                else:
                    with torch.no_grad():
                        reference_logits = self._aligned_forward(
                            reference_model, branch_inputs, reference_positions[:, start:end])

                zero = student_logits.reshape(-1)[0].float() * 0
                if total_sum is None:
                    total_sum = zero.detach() if chunk_backward else zero
                chunk_sum = zero if chunk_backward else None
                for mode, name, reverse in branch_specs:
                    row_mask = modes.eq(mode)
                    if online_mask is not None:
                        row_mask = row_mask & online_mask
                    if not row_mask.any():
                        continue
                    student_flat, student_tokens = self._flatten_rows(
                        student_logits, selected_labels[:, start:end], row_mask
                    )
                    reference_flat, reference_tokens = self._flatten_rows(
                        reference_logits, selected_labels[:, start:end], row_mask
                    )
                    if not torch.equal(student_tokens, reference_tokens):
                        raise ValueError(f"{name} completion-token alignment failed.")
                    count = student_tokens.numel()
                    term = self._kl_sum(student_flat, reference_flat, reverse) if count else zero
                    if chunk_backward:
                        chunk_sum = chunk_sum + term
                        detached_term = term.detach()
                        term_sums[name] = (
                            detached_term if term_sums[name] is None
                            else term_sums[name] + detached_term
                        )
                    else:
                        total_sum = total_sum + term
                        term_sums[name] = (
                            term if term_sums[name] is None else term_sums[name] + term
                        )
                    token_counts[name] += count
                    total_count += count

                if chunk_backward:
                    self.accelerator.backward(
                        global_token_loss(chunk_sum, num_items_in_batch),
                        retain_graph=False,
                    )
                    total_sum = total_sum + chunk_sum.detach()
                    del chunk_sum
                student_outputs = None
                del student_logits, reference_logits

            if chunk_backward and student_hidden_graph is not None:
                torch.autograd.backward(
                    (student_hidden_graph, student_weight_graph),
                    (student_hidden.grad, student_lm_weight.grad),
                )
            del student_hidden, reference_hidden

        if total_sum is None:
            raise ValueError("Skill OPD batch has no prediction positions.")
        signal = {
            name: (term_sums[name] if term_sums[name] is not None else total_sum * 0,
                   token_counts[name], row_counts[name])
            for _, name, _ in mode_specs
        }
        if total_count == 0 and online_mask is None:
            raise ValueError("Skill OPD batch has no active distillation tokens.")
        if online_mask is not None:
            from online_step import global_token_loss
            loss = global_token_loss(total_sum, num_items_in_batch)
        else:
            loss = total_sum / total_count
        if not torch.isfinite(loss):
            raise ValueError("Non-finite Skill OPD loss.")
        logger.info(
            "SKILL_OPD_SIGNAL: loss=%.8f ordinary_reverse=%.8f skill_forward=%.8f "
            "rescue_forward=%.8f steer_forward=%.8f ordinary_rows=%d "
            "skill_rows=%d rescue_rows=%d steer_rows=%d ordinary_tokens=%d "
            "skill_tokens=%d rescue_tokens=%d steer_tokens=%d tokens=%d",
            loss.detach().float().item(),
            *[(value[0] / max(value[1], 1)).detach().float().item() for value in signal.values()],
            *[value[2] for value in signal.values()],
            *[value[1] for value in signal.values()], total_count,
        )
        if chunk_backward:
            # The real gradients were produced above; Trainer will invoke its
            # ordinary backward once more on this detached reporting scalar.
            # Keep that final call graph-free so it cannot retain the last
            # long-context checkpoint graph or add a second model gradient.
            loss = loss.detach().requires_grad_(True)
        return (loss, last_student_outputs) if return_outputs else loss
