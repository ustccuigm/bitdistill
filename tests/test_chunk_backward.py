"""Compare production head chunking against direct full-logit gradients."""
import copy
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from steerdistill.training.mytrainer import SkillKDTrainer
from steerdistill.training.data_loading import DataCollatorForSupervisedDataset
from test_pipeline import TinyTokenizer


class HeadModel(torch.nn.Module):
    def __init__(self, seed, tied=False):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            self.embedding = torch.nn.Embedding(32, 8)
            self.lm_head = torch.nn.Linear(8, 32, bias=False)
        if tied:
            self.lm_head.weight = self.embedding.weight

    def forward(self, input_ids, attention_mask=None, logits_to_keep=None):
        hidden = self.embedding(input_ids)
        if logits_to_keep is not None:
            hidden = hidden.index_select(1, logits_to_keep)
        return SimpleNamespace(logits=self.lm_head(hidden))


class ChunkBackwardTest(unittest.TestCase):
    def test_retained_context_is_not_silently_truncated(self):
        tokenizer = TinyTokenizer()
        tokenizer.model_max_length = 8
        collator = DataCollatorForSupervisedDataset(tokenizer)
        for mode in ("ordinary_opd", "skill_recovery"):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "complete retained context"):
                collator([dict(prompt="long original context", skill_prompt="steered context",
                               completion="abc", add_eos=False, distill_mode=mode)])

    def test_gemma_softcapped_gradient_equivalence(self):
        from transformers import Gemma4UnifiedTextConfig, Gemma4UnifiedForCausalLM

        def create(seed, tied=False):
            config = Gemma4UnifiedTextConfig(
                vocab_size=32, hidden_size=32, intermediate_size=64,
                num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=2,
                head_dim=16, max_position_embeddings=128, use_cache=False,
                tie_word_embeddings=tied, attention_dropout=0,
                layer_types=["sliding_attention", "full_attention"],
                sliding_window=32, final_logit_softcapping=2.0,
                per_layer_config={}, hidden_size_per_layer_input=0)
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(seed)
                return Gemma4UnifiedForCausalLM(config).eval()

        with patch(__name__ + ".HeadModel", create):
            self.test_full_logit_gradient_equivalence()

    def test_qwen_model_architectures(self):
        from transformers import (Qwen3Config, Qwen3ForCausalLM,
                                  Qwen3_5Config, Qwen3_5ForConditionalGeneration)

        for family in ("qwen3", "qwen3_5"):
            def create(seed, tied=False):
                text_config = dict(vocab_size=32, hidden_size=32, intermediate_size=64,
                    num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=2,
                    head_dim=16, max_position_embeddings=128, use_cache=False,
                    tie_word_embeddings=tied, attention_dropout=0)
                with torch.random.fork_rng(devices=[]):
                    torch.manual_seed(seed)
                    if family == "qwen3":
                        return Qwen3ForCausalLM(Qwen3Config(**text_config)).eval()
                    text_config.update(linear_key_head_dim=16, linear_value_head_dim=16,
                        linear_num_key_heads=2, linear_num_value_heads=2,
                        layer_types=["linear_attention", "full_attention"])
                    config = Qwen3_5Config(text_config=text_config,
                        vision_config=dict(depth=1, hidden_size=32, intermediate_size=64,
                            num_heads=2, out_hidden_size=32, num_position_embeddings=16),
                        tie_word_embeddings=tied)
                    model = Qwen3_5ForConditionalGeneration(config).eval()
                    model.model.visual.requires_grad_(False)
                    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": True})
                    model.train()
                    return model
            with self.subTest(family=family), patch(__name__ + ".HeadModel", create):
                self.test_full_logit_gradient_equivalence()

    def test_full_logit_gradient_equivalence(self):
        rows = [dict(prompt="base" + "x" * index, skill_prompt="a longer steer prefix" + "y" * (3-index),
                     completion="abcde"[:index+2], add_eos=False, distill_mode=mode)
                for index, mode in enumerate(("ordinary_opd", "skill_recovery", "teacher_rescue", "steer_forward"))]
        batch = DataCollatorForSupervisedDataset(TinyTokenizer())(rows)
        for tied in (False, True):
            for chunk_size in (1, 3, 128):
                with self.subTest(tied=tied, chunk=chunk_size):
                    student = HeadModel(1, tied)
                    actual = copy.deepcopy(student)
                    teacher = HeadModel(2, tied).requires_grad_(False)
                    reference = HeadModel(3, tied).requires_grad_(False)
                    terms, count = [], 0
                    for row, mode in enumerate(batch["skill_distill_modes"].tolist()):
                        skill = mode in (1, 3)
                        ids = batch["skill_input_ids" if skill else "input_ids"][row:row+1]
                        labels = batch["skill_labels" if skill else "labels"][row:row+1, 1:]
                        mask = labels.ne(-100)
                        learner_ids = batch["input_ids"][row:row+1]
                        learner_mask = batch["labels"][row:row+1, 1:].ne(-100)
                        s = student(learner_ids).logits[:, :-1][learner_mask].float()
                        t = (reference if skill else teacher)(ids).logits[:, :-1][mask].float()
                        sl, tl = F.log_softmax(s, -1), F.log_softmax(t, -1)
                        terms.append(((sl.exp() * (sl-tl)) if mode == 0 else
                                      (tl.exp() * (tl-sl))).sum())
                        count += int(mask.sum())
                    expected_loss = sum(terms) / count
                    expected_loss.backward()
                    trainer = object.__new__(SkillKDTrainer)
                    trainer.teacher_model = teacher
                    trainer.skill_reference_model = reference
                    trainer.accelerator = SimpleNamespace(backward=lambda loss, **kwargs: loss.backward(**kwargs))
                    inputs = dict(batch, online_row_mask=torch.ones(len(rows), dtype=torch.bool))
                    with patch.dict(os.environ, STEER_BACKWARD_CHUNKS="1", STEER_LOGITS_CHUNK_SIZE=str(chunk_size)):
                        loss = trainer.compute_loss(actual, inputs, num_items_in_batch=count)
                        loss.backward()
                    torch.testing.assert_close(loss, expected_loss)
                    for got, expected in zip(actual.parameters(), student.parameters()):
                        torch.testing.assert_close(got.grad, expected.grad, atol=2e-6, rtol=2e-5)
                    self.assertTrue(all(p.grad is None for p in teacher.parameters()))
                    self.assertTrue(all(p.grad is None for p in reference.parameters()))


if __name__ == "__main__":
    unittest.main()
