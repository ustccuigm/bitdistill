from dataclasses import dataclass
from array import array
import copy
import json
import logging
import os
import random
from typing import Dict, Sequence

import torch
from torch.utils.data import Dataset, Subset
import transformers
from steerdistill.training.chat_templates import normalize_tool_arguments as _normalize_chat_tool_arguments

try:
    import msgspec
except ImportError:  # Keep the repository usable in the minimal base env.
    msgspec = None


IGNORE_INDEX = -100
logger = logging.getLogger(__name__)


def _extract_prompt_completion(item, tokenizer):
    """Accept legacy SteerDistill pairs and explicit prompt/completion JSONL."""
    if isinstance(item, list):
        if not item or not isinstance(item[0], list) or len(item[0]) != 2:
            raise ValueError("Legacy records must have the form [[prompt, completion]].")
        return {"prompt": str(item[0][0]), "completion": str(item[0][1])}

    if not isinstance(item, dict):
        raise ValueError(f"Unsupported training record type: {type(item).__name__}")

    if "prompt" in item and ("completion" in item or "label" in item):
        prompt = item["prompt"]
        if isinstance(prompt, list):
            # Native rollout materialization stores the exact collection-time
            # prompt tokens.  Re-rendering tens of thousands of long tool
            # histories on every distributed rank is both expensive and can
            # introduce template drift.  The collator consumes these IDs
            # directly, so a rendered ordinary prompt is unnecessary.
            if item.get("prompt_token_ids"):
                prompt = ""
            # Otherwise retain the structured history and render it lazily in
            # the collator.  Distributed sampling then renders each training
            # example on only the rank that consumes it, rather than eagerly
            # rendering the full dataset on every rank.
        completion = item.get("completion")
        if item.get("completion_tool_calls") and "completion_content" in item:
            completion = item["completion_content"]
        if completion is None:
            # BFCL stores the supervised tool-call trajectory in `label` rather
            # than an assistant-message field. Keep its structure losslessly.
            label = item.get("label", "")
            if label is None:
                label = ""
            completion = label if isinstance(label, str) else json.dumps(label, ensure_ascii=False)
        example = {"prompt": prompt, "completion": str(completion)}
        for key in (
            "task_key", "source_run", "assistant_turn",
            "prompt_token_ids", "completion_token_ids",
            "prompt_suffix_token_ids",
            "teacher_topk_ids", "teacher_topk_logprobs",
            "old_logprobs", "rollout_logprobs", "advantage", "trajectory_weight",
            "add_eos", "behavior_logprob_source", "distill_role",
            "decision_token_mask", "turn_reliability_weight",
            "steer_decision_char_span", "failed_completion",
            "failed_decision_char_span",
            "skill_prompt", "skill_marker", "completion_tool_calls",
            "distill_mode", "skill_id", "skill_version",
        ):
            if key in item:
                example[key] = item[key]
        return example

    if "messages" in item:
        messages = item["messages"]
        assistant_indices = [i for i, message in enumerate(messages) if message.get("role") == "assistant"]
        if not assistant_indices:
            raise ValueError("A messages record must contain at least one assistant message.")
        last_assistant = assistant_indices[-1]
        if last_assistant != len(messages) - 1:
            raise ValueError("The final message must be the assistant completion.")
        assistant = messages[last_assistant]
        record = dict(item)
        record["prompt"] = messages[:last_assistant]
        record["completion"] = assistant.get("content") or ""
        if assistant.get("tool_calls"):
            record["completion_tool_calls"] = assistant["tool_calls"]
        return _extract_prompt_completion(record, tokenizer)

    raise ValueError("Each record must contain [[prompt, completion]], prompt/completion, or messages.")


class IndexedJsonlDataset(Dataset):
    """Keep byte offsets in memory and decode only the rows a rank consumes."""
    def __init__(self, path, tokenizer):
        self.path, self.tokenizer = path, tokenizer
        self.offsets = array("Q")
        self._handle, self._pid = None, None
        with open(path, "rb") as stream:
            while True:
                offset = stream.tell()
                line = stream.readline()
                if not line:
                    break
                if line.strip():
                    self.offsets.append(offset)
        if not self.offsets:
            raise ValueError("Training data is empty")

    def __len__(self):
        return len(self.offsets)

    def __getitem__(self, index):
        if self._handle is None or self._pid != os.getpid():
            if self._handle is not None:
                self._handle.close()
            self._handle = open(self.path, "rb")
            self._pid = os.getpid()
        self._handle.seek(self.offsets[index])
        line = self._handle.readline()
        item = msgspec.json.decode(line) if msgspec is not None else json.loads(line)
        return _extract_prompt_completion(item, self.tokenizer)

    def __getstate__(self):
        state = self.__dict__.copy()
        state.update(_handle=None, _pid=None)
        return state

    def __del__(self):
        handle = getattr(self, "_handle", None)
        if handle is not None:
            handle.close()


@dataclass
class DataCollatorForSupervisedDataset:
    tokenizer: transformers.PreTrainedTokenizer

    def _span_tokenization(self, completion, completion_ids, span):
        if not isinstance(span, list) or len(span) != 2:
            raise ValueError("steer_decision_char_span must be [start, end].")
        start, end = int(span[0]), int(span[1])
        if start < 0 or end <= start or end > len(completion):
            raise ValueError(
                f"Invalid steer_decision_char_span={span} for {len(completion)} characters."
            )
        try:
            encoded = self.tokenizer(
                completion,
                add_special_tokens=False,
                return_offsets_mapping=True,
            )
            token_ids = list(encoded["input_ids"])
            offsets = [tuple(value) for value in encoded["offset_mapping"]]
        except (TypeError, NotImplementedError, KeyError):
            # Unit-test and slow-tokenizer fallback.  It is accepted only when
            # prefix/full tokenization gives an unambiguous contiguous suffix.
            token_ids = list(self.tokenizer.encode(completion, add_special_tokens=False))
            prefix_ids = list(self.tokenizer.encode(completion[:start], add_special_tokens=False))
            through_ids = list(self.tokenizer.encode(completion[:end], add_special_tokens=False))
            offsets = None
        if token_ids != completion_ids:
            raise ValueError(
                "Steer decision masking requires exact completion token identity; "
                "the stored completion differs from tokenizer encoding."
            )
        if offsets is not None:
            mask = [token_end > start and token_start < end for token_start, token_end in offsets]
        else:
            if token_ids[:len(prefix_ids)] != prefix_ids or token_ids[:len(through_ids)] != through_ids:
                raise ValueError("Slow tokenizer cannot align the Steer decision span exactly.")
            mask = [len(prefix_ids) <= index < len(through_ids) for index in range(len(token_ids))]
        if not any(mask):
            raise ValueError("Steer decision span maps to zero completion tokens.")
        return token_ids, mask

    def _split_around_marker(self, rendered_prompt, marker):
        start = rendered_prompt.find(marker)
        if start < 0 or rendered_prompt.find(marker, start + 1) >= 0:
            raise ValueError("Steer marker must occur exactly once in skill_prompt.")
        end = start + len(marker)
        try:
            encoded = self.tokenizer(
                rendered_prompt,
                add_special_tokens=False,
                return_offsets_mapping=True,
            )
            ids = list(encoded["input_ids"])
            offsets = [tuple(value) for value in encoded["offset_mapping"]]
        except (TypeError, NotImplementedError, KeyError) as error:
            raise ValueError(
                "Steer-preserving truncation requires tokenizer offset mappings."
            ) from error
        before, marker_ids, after = [], [], []
        for token, (token_start, token_end) in zip(ids, offsets):
            if token_end <= start:
                before.append(token)
            elif token_start >= end:
                after.append(token)
            else:
                marker_ids.append(token)
        if not marker_ids:
            raise ValueError("Steer marker maps to zero prompt tokens.")
        return before, marker_ids, after

    def _steer_decision_mask(
        self, completion, completion_ids, span, failed_completion, failed_span
    ):
        """Select the localized action while excluding hidden reasoning.

        The action-bearing spans prevent differences in hidden reasoning or
        formatting outside the submitted decision from becoming targets.  A
        failed/reference comparison additionally proves that this is a real
        behavioral bifurcation, then all submitted decision tokens implement
        the token average in the Steer forward-KL objective.
        """
        target_ids, target_span_mask = self._span_tokenization(
            completion, completion_ids, span
        )
        failed_ids = list(self.tokenizer.encode(failed_completion, add_special_tokens=False))
        failed_ids, failed_span_mask = self._span_tokenization(
            failed_completion, failed_ids, failed_span
        )
        target_indices = [i for i, active in enumerate(target_span_mask) if active]
        failed_indices = [i for i, active in enumerate(failed_span_mask) if active]
        target_action = [target_ids[i] for i in target_indices]
        failed_action = [failed_ids[i] for i in failed_indices]
        common = 0
        while (
            common < len(target_action)
            and common < len(failed_action)
            and target_action[common] == failed_action[common]
        ):
            common += 1
        if common == len(target_action) and common == len(failed_action):
            raise ValueError("Steer target and failed action have no token-level bifurcation.")
        return target_span_mask

    def _native_completion_ids(self, prompt, completion, tool_calls):
        """Render native tool calls with the model chat template.

        Rollout rows normally carry exact sampled token IDs. This fallback is
        for valid rows without them; serializing ``tool_calls`` with ``str``
        would train on a Python representation instead of the model format.
        """
        if not isinstance(prompt, list):
            raise ValueError(
                "Native tool-call records require a structured prompt when "
                "completion_token_ids are absent."
            )
        history = _normalize_chat_tool_arguments(prompt)
        assistant = _normalize_chat_tool_arguments([{
            "role": "assistant",
            "content": completion if completion else None,
            "tool_calls": copy.deepcopy(tool_calls),
        }])[0]
        prompt_text = self.tokenizer.apply_chat_template(
            history, tokenize=False, add_generation_prompt=True
        )
        full_text = self.tokenizer.apply_chat_template(
            history + [assistant], tokenize=False, add_generation_prompt=False
        )
        prompt_ids = self.tokenizer.encode(prompt_text, add_special_tokens=False)
        full_ids = self.tokenizer.encode(full_text, add_special_tokens=False)
        if full_ids[:len(prompt_ids)] != prompt_ids:
            raise ValueError(
                "The tokenizer chat template cannot isolate the native tool-call "
                "completion from its prompt."
            )
        completion_ids = full_ids[len(prompt_ids):]
        if not completion_ids:
            raise ValueError("Native tool-call chat template produced no completion tokens.")
        return completion_ids

    def _encode(self, instance):
        prompt = instance["prompt"]
        structured_prompt = prompt
        completion = instance["completion"]
        if not str(completion or "").strip() and not (
            instance.get("completion_tool_calls") or instance.get("completion_token_ids")
        ):
            raise ValueError("Empty/whitespace completion is not a training trajectory")
        prompt_ids = list(instance.get("prompt_token_ids", []))
        if not prompt_ids:
            if isinstance(prompt, list):
                prompt = self.tokenizer.apply_chat_template(
                    _normalize_chat_tool_arguments(prompt),
                    tokenize=False,
                    add_generation_prompt=True,
                )
            prompt_ids = self.tokenizer.encode(prompt, add_special_tokens=False)
        prompt_suffix_ids = list(instance.get("prompt_suffix_token_ids", []))
        if prompt_suffix_ids:
            prompt_ids.extend(prompt_suffix_ids)
        # Offline teacher generation records exact token ids. Using them avoids
        # decode/re-encode drift around Qwen3 tool-call and control tokens.
        completion_ids = list(instance.get("completion_token_ids", []))
        if not completion_ids:
            tool_calls = instance.get("completion_tool_calls")
            if tool_calls:
                completion_ids = self._native_completion_ids(
                    structured_prompt, completion, tool_calls
                )
            else:
                completion_ids = self.tokenizer.encode(completion, add_special_tokens=False)
        steer_decision_mask = None
        if "steer_decision_char_span" in instance:
            if instance.get("distill_mode") != "steer_forward":
                raise ValueError("Steer decision spans are valid only for steer_forward rows.")
            steer_decision_mask = self._steer_decision_mask(
                completion,
                completion_ids,
                instance["steer_decision_char_span"],
                str(instance.get("failed_completion", "")),
                instance.get("failed_decision_char_span"),
            )
        eos_id = self.tokenizer.eos_token_id
        add_eos = bool(instance.get("add_eos", True))
        decision_mask = None
        if "decision_token_mask" in instance:
            decision_mask = [bool(value) for value in instance["decision_token_mask"]]
            if len(decision_mask) != len(completion_ids):
                raise ValueError(
                    "Q-Guard decision_token_mask must match completion_token_ids: "
                    f"mask={len(decision_mask)}, completion={len(completion_ids)}"
                )
        if add_eos and eos_id is not None and (not completion_ids or completion_ids[-1] != eos_id):
            completion_ids.append(eos_id)
            if decision_mask is not None:
                decision_mask.append(True)
            if steer_decision_mask is not None:
                # The explicit end of the submitted assistant action is part
                # of the localized action objective.
                steer_decision_mask.append(True)

        max_length = self.tokenizer.model_max_length
        if (instance.get("distill_mode") in {"ordinary_opd", "skill_recovery"}
                and len(prompt_ids) + len(completion_ids) > max_length):
            raise ValueError(
                "SteerDistill requires the complete retained context and response; "
                f"tokens={len(prompt_ids) + len(completion_ids)} exceed max_length={max_length}."
            )
        if decision_mask is not None and len(completion_ids) >= max_length:
            raise ValueError(
                "Q-Guard completion exceeds the learner window; structural "
                f"quarantine must run first: completion={len(completion_ids)}, "
                f"max_length={max_length}."
            )
        skill_prompt_ids = None
        skill_marker = instance.get("skill_marker")
        if skill_marker is not None:
            if steer_decision_mask is None:
                raise ValueError("skill_marker is reserved for direct Steer targets.")
            skill_prompt = instance["skill_prompt"]
            if isinstance(skill_prompt, list):
                skill_prompt = self.tokenizer.apply_chat_template(
                    _normalize_chat_tool_arguments(skill_prompt),
                    tokenize=False,
                    add_generation_prompt=True,
                )
            skill_before, marker_ids, skill_after = self._split_around_marker(
                str(skill_prompt), str(skill_marker)
            )
            if len(completion_ids) + len(marker_ids) >= max_length:
                raise ValueError("Steer plus completion exceeds the learner window.")
            base_budget = max_length - len(completion_ids) - len(marker_ids)
            full_prompt_ids = prompt_ids
            if len(full_prompt_ids) <= base_budget:
                prompt_ids = full_prompt_ids
                skill_prompt_ids = skill_before + marker_ids + skill_after
            else:
                head_target = min(1024, max(1, base_budget // 4))
                head_count = min(head_target, len(skill_before))
                tail_count = min(base_budget - head_count, len(skill_after))
                unused = base_budget - head_count - tail_count
                if unused:
                    extra_head = min(unused, len(skill_before) - head_count)
                    head_count += extra_head
                    unused -= extra_head
                if unused:
                    tail_count += min(unused, len(skill_after) - tail_count)
                prompt_ids = full_prompt_ids[:head_count]
                if tail_count:
                    prompt_ids += full_prompt_ids[-tail_count:]
                skill_prompt_ids = skill_before[:head_count] + marker_ids
                if tail_count:
                    skill_prompt_ids += skill_after[-tail_count:]
            if len(skill_prompt_ids) + len(completion_ids) > max_length:
                raise ValueError("Steer-preserving prompt construction exceeds learner window.")
        elif len(completion_ids) >= max_length:
            raise ValueError(
                "SteerDistill retains the complete assistant response; refusing to "
                f"silently truncate completion={len(completion_ids)} at "
                f"max_length={max_length}. Increase MODEL_MAX_LENGTH or quarantine "
                "this record before training."
            )
        elif skill_prompt_ids is None:
            prompt_budget = max_length - len(completion_ids)
            if len(prompt_ids) > prompt_budget:
                # tool-use environment prompts put the MCP system prompt and user task at the
                # head, and the list_tools response at the tail. Retain both.
                full_prompt_ids = prompt_ids
                head_budget = min(1024, max(1, prompt_budget // 4))
                tail_budget = prompt_budget - head_budget
                prompt_ids = full_prompt_ids[:head_budget]
                if tail_budget:
                    prompt_ids += full_prompt_ids[-tail_budget:]

        input_ids = torch.tensor(prompt_ids + completion_ids, dtype=torch.long)
        active_completion = completion_ids
        if steer_decision_mask is not None:
            active_completion = [
                token if active else IGNORE_INDEX
                for token, active in zip(completion_ids, steer_decision_mask)
            ]
        labels = torch.tensor(
            [IGNORE_INDEX] * len(prompt_ids) + active_completion, dtype=torch.long
        )
        encoded = {"input_ids": input_ids, "labels": labels, "prompt_length": len(prompt_ids)}
        if "skill_prompt" in instance:
            if skill_prompt_ids is None:
                skill_prompt = instance["skill_prompt"]
                if isinstance(skill_prompt, list):
                    # Ordinary OPD uses the same unassisted context on both
                    # branches; avoid rendering and tokenizing it twice.
                    if skill_prompt == instance["prompt"]:
                        skill_prompt_ids = list(prompt_ids)
                    else:
                        skill_prompt = self.tokenizer.apply_chat_template(
                            _normalize_chat_tool_arguments(skill_prompt),
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                        skill_prompt_ids = self.tokenizer.encode(
                            skill_prompt, add_special_tokens=False
                        )
                else:
                    skill_prompt_ids = self.tokenizer.encode(
                        str(skill_prompt), add_special_tokens=False
                    )
                skill_budget = max_length - len(completion_ids)
                if len(skill_prompt_ids) > skill_budget:
                    raise ValueError(
                        "SteerDistill steering context plus complete response exceeds "
                        f"max_length={max_length}; increase MODEL_MAX_LENGTH or "
                        "quarantine this record before training."
                    )
            encoded["skill_input_ids"] = torch.tensor(
                skill_prompt_ids + completion_ids, dtype=torch.long
            )
            encoded["skill_labels"] = torch.tensor(
                [IGNORE_INDEX] * len(skill_prompt_ids) + active_completion, dtype=torch.long
            )
            modes = {
                "ordinary_opd": 0,
                "skill_recovery": 1,
                "teacher_rescue": 2,
                "steer_forward": 3,
            }
            mode = str(instance.get("distill_mode", "ordinary_opd"))
            if mode not in modes:
                raise ValueError(f"Unknown distill_mode={mode!r}")
            encoded["skill_distill_mode"] = modes[mode]
        if decision_mask is not None:
            encoded["decision_token_mask"] = torch.tensor(
                decision_mask, dtype=torch.bool
            )
            weight = float(instance.get("turn_reliability_weight", 1.0))
            if not 0.0 < weight <= 10.0:
                raise ValueError(
                    f"Invalid Q-Guard turn_reliability_weight={weight}; expected (0, 10]."
                )
            encoded["turn_reliability_weight"] = weight
        if "distill_role" in instance:
            role = str(instance["distill_role"])
            role_ids = {
                "student": 0,
                "student_corrected": 0,
                "teacher": 1,
                "teacher_critique": 1,
            }
            if role not in role_ids:
                raise ValueError(
                    f"Unknown distill_role={role!r}; expected student, "
                    "student_corrected, teacher, or teacher_critique."
                )
            encoded["distill_role"] = role_ids[role]
        if "old_logprobs" in instance:
            old_logprobs = instance["old_logprobs"]
            if len(old_logprobs) != len(completion_ids):
                raise ValueError(
                    "RLVR old_logprobs must match completion_token_ids including EOS: "
                    f"logprobs={len(old_logprobs)}, completion={len(completion_ids)}"
                )
            encoded["old_logprobs"] = torch.tensor(old_logprobs, dtype=torch.float32)
            if "rollout_logprobs" in instance:
                rollout_logprobs = instance["rollout_logprobs"]
                if len(rollout_logprobs) != len(completion_ids):
                    raise ValueError(
                        "RLVR rollout_logprobs must match completion_token_ids: "
                        f"logprobs={len(rollout_logprobs)}, completion={len(completion_ids)}"
                    )
                encoded["rollout_logprobs"] = torch.tensor(rollout_logprobs, dtype=torch.float32)
            encoded["advantage"] = float(instance["advantage"])
            encoded["trajectory_weight"] = float(instance.get("trajectory_weight", 1.0))
        has_soft_labels = "teacher_topk_ids" in instance or "teacher_topk_logprobs" in instance
        if has_soft_labels:
            if "teacher_topk_ids" not in instance or "teacher_topk_logprobs" not in instance:
                raise ValueError("Offline soft labels require both teacher_topk_ids and teacher_topk_logprobs.")
            topk_ids = instance["teacher_topk_ids"][:len(completion_ids)]
            topk_logprobs = instance["teacher_topk_logprobs"][:len(completion_ids)]
            if len(topk_ids) != len(completion_ids) or len(topk_logprobs) != len(completion_ids):
                raise ValueError(
                    "Offline soft-label length must match completion tokens including EOS: "
                    f"labels={len(completion_ids)}, ids={len(topk_ids)}, logprobs={len(topk_logprobs)}"
                )
            encoded["teacher_topk_ids"] = torch.tensor(topk_ids, dtype=torch.long)
            encoded["teacher_topk_logprobs"] = torch.tensor(topk_logprobs, dtype=torch.float32)
        return encoded

    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        encoded = [self._encode(item) for item in instances]
        input_ids = torch.nn.utils.rnn.pad_sequence(
            [item["input_ids"] for item in encoded], batch_first=True,
            padding_value=self.tokenizer.pad_token_id
        )
        labels = torch.nn.utils.rnn.pad_sequence(
            [item["labels"] for item in encoded], batch_first=True, padding_value=IGNORE_INDEX
        )
        batch = {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": input_ids.ne(self.tokenizer.pad_token_id),
        }
        if any("skill_input_ids" in item for item in encoded):
            if not all("skill_input_ids" in item for item in encoded):
                raise ValueError("Skill OPD batches require skill_prompt on every record.")
            skill_input_ids = torch.nn.utils.rnn.pad_sequence(
                [item["skill_input_ids"] for item in encoded], batch_first=True,
                padding_value=self.tokenizer.pad_token_id,
            )
            skill_labels = torch.nn.utils.rnn.pad_sequence(
                [item["skill_labels"] for item in encoded], batch_first=True,
                padding_value=IGNORE_INDEX,
            )
            batch["skill_input_ids"] = skill_input_ids
            batch["skill_attention_mask"] = skill_input_ids.ne(self.tokenizer.pad_token_id)
            batch["skill_labels"] = skill_labels
            batch["skill_distill_modes"] = torch.tensor(
                [item["skill_distill_mode"] for item in encoded], dtype=torch.long
            )
        if any("distill_role" in item for item in encoded):
            if not all("distill_role" in item for item in encoded):
                raise ValueError("Do not mix records with and without distill_role.")
            batch["distill_roles"] = torch.tensor(
                [item["distill_role"] for item in encoded], dtype=torch.long
            )
        if any("decision_token_mask" in item for item in encoded):
            if not all("decision_token_mask" in item for item in encoded):
                raise ValueError("Do not mix Q-Guard and ordinary OPD records in one batch.")
            batch_decisions = torch.zeros(input_ids.shape, dtype=torch.bool)
            for row, item in enumerate(encoded):
                start = item["prompt_length"]
                count = item["decision_token_mask"].shape[0]
                batch_decisions[row, start:start + count] = item["decision_token_mask"]
            batch["qguard_decision_mask"] = batch_decisions
            batch["qguard_turn_weights"] = torch.tensor(
                [item["turn_reliability_weight"] for item in encoded],
                dtype=torch.float32,
            )
        if any("old_logprobs" in item for item in encoded):
            if not all("old_logprobs" in item for item in encoded):
                raise ValueError("Do not mix RLVR and non-RLVR records in one batch.")
            batch_old = torch.zeros(input_ids.shape, dtype=torch.float32)
            batch_mask = torch.zeros(input_ids.shape, dtype=torch.bool)
            for row, item in enumerate(encoded):
                start = item["prompt_length"]
                count = item["old_logprobs"].shape[0]
                batch_old[row, start:start + count] = item["old_logprobs"]
                batch_mask[row, start:start + count] = True
            batch["old_logprobs"] = batch_old
            batch["rlvr_mask"] = batch_mask
            batch["advantages"] = torch.tensor(
                [item["advantage"] for item in encoded], dtype=torch.float32
            )
            batch["trajectory_weights"] = torch.tensor(
                [item["trajectory_weight"] for item in encoded], dtype=torch.float32
            )
            if any("rollout_logprobs" in item for item in encoded):
                if not all("rollout_logprobs" in item for item in encoded):
                    raise ValueError("Do not mix RLVR records with and without rollout logprobs.")
                batch_rollout = torch.zeros(input_ids.shape, dtype=torch.float32)
                for row, item in enumerate(encoded):
                    start = item["prompt_length"]
                    count = item["rollout_logprobs"].shape[0]
                    batch_rollout[row, start:start + count] = item["rollout_logprobs"]
                batch["rollout_logprobs"] = batch_rollout
        if any("teacher_topk_ids" in item for item in encoded):
            if not all("teacher_topk_ids" in item for item in encoded):
                raise ValueError("Do not mix records with and without offline soft labels in one batch.")
            top_k = encoded[0]["teacher_topk_ids"].shape[-1]
            if any(item["teacher_topk_ids"].shape[-1] != top_k for item in encoded):
                raise ValueError("All offline soft-label records in a batch must use the same top-k.")
            batch_ids = torch.zeros((*input_ids.shape, top_k), dtype=torch.long)
            # Finite padding is intentional: the loss masks these positions,
            # while -inf would create NaNs before masking (0 * NaN is NaN).
            batch_logprobs = torch.zeros((*input_ids.shape, top_k), dtype=torch.float32)
            batch_mask = torch.zeros(input_ids.shape, dtype=torch.bool)
            for row, item in enumerate(encoded):
                start = item["prompt_length"]
                count = item["teacher_topk_ids"].shape[0]
                batch_ids[row, start:start + count] = item["teacher_topk_ids"]
                batch_logprobs[row, start:start + count] = item["teacher_topk_logprobs"]
                batch_mask[row, start:start + count] = True
            batch["teacher_topk_ids"] = batch_ids
            batch["teacher_topk_logprobs"] = batch_logprobs
            batch["teacher_soft_mask"] = batch_mask
        return batch


def make_supervised_data_module(tokenizer: transformers.PreTrainedTokenizer, data_args) -> Dict:
    dataset = IndexedJsonlDataset(data_args.data_path, tokenizer)
    if data_args.max_train_samples is not None and data_args.max_train_samples < len(dataset):
        if data_args.max_train_samples < 1:
            raise ValueError("max_train_samples must be positive")
        dataset = Subset(dataset, random.sample(range(len(dataset)), data_args.max_train_samples))
    if int(os.environ.get("LOCAL_RANK", "0")) == 0:
        logger.info("Using all %d selected training records", len(dataset))

    return {
        "train_dataset": dataset,
        "eval_dataset": None,
        "data_collator": DataCollatorForSupervisedDataset(tokenizer=tokenizer),
    }
