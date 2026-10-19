from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from steerdistill.common import (
    canonical_decision,
    causal_action_delta,
    causal_transition_match,
    first_divergence,
    inject_skill,
    local_transition_match,
    prompt_fingerprint,
)
from steerdistill.materialize import rows_from_run
from steerdistill.counterfactuals import task_texts
from steerdistill.analysis import (
    analysis_violations,
    assert_pair_binding,
    bind_teacher_analysis,
    merge_steer_step,
    recovery_lineage,
    render_integrated_steer,
    required_relation,
    same_recovery_lineage,
)
from steerdistill.store import SkillStore
from steerdistill.skill_proxy import ProxyState
from steerdistill.training.data_loading import DataCollatorForSupervisedDataset
from steerdistill.training.mytrainer import SkillKDTrainer
from steerdistill.training.convert_hf_to_awq_runtime import pack_awq
from steerdistill.runtime_validation import unpack_awq
from scripts.validate.validate_skills import transition_with_steps


class TinyTokenizer:
    pad_token_id = 0
    eos_token_id = 2
    model_max_length = 64

    def encode(self, text, add_special_tokens=False):
        return [3 + (ord(char) % 23) for char in str(text)]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        rendered = "|".join(f"{m['role']}:{m.get('content', '')}" for m in messages)
        return rendered + ("|assistant:" if add_generation_prompt else "")


class TinyLM(torch.nn.Module):
    def __init__(self, seed):
        super().__init__()
        generator = torch.Generator().manual_seed(seed)
        self.embedding = torch.nn.Embedding(32, 8)
        self.projection = torch.nn.Linear(8, 32, bias=False)
        with torch.no_grad():
            self.embedding.weight.copy_(torch.randn(32, 8, generator=generator))
            self.projection.weight.copy_(torch.randn(32, 8, generator=generator))

    def forward(self, input_ids, attention_mask=None, logits_to_keep=None):
        logits = self.projection(self.embedding(input_ids))
        if logits_to_keep is not None:
            logits = logits.index_select(1, logits_to_keep)
        return SimpleNamespace(logits=logits)


class PipelineTest(unittest.TestCase):
    def test_tool_call_ids_are_transport_metadata(self):
        from steerdistill.common import canonical_decision

        left = {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_A", "type": "function",
            "function": {"name": "lookup", "arguments": '{"b": 2, "a": 1}'},
        }]}
        right = {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_B", "type": "function",
            "function": {"name": "lookup", "arguments": '{"a": 1, "b": 2}'},
        }]}
        self.assertEqual(canonical_decision(left), canonical_decision(right))

    def test_canonical_tool_wrappers_ignore_transport_ids_but_keep_argument_ids(self):
        native = {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_A", "type": "function",
            "function": {"name": "lookup", "arguments": '{"id": "record-A", "b": 2, "a": 1}'},
        }]}
        wrapped = {
            "role": "assistant",
            "content": '<tool_call>{"name":"lookup","arguments":{"a":1,"b":2,"id":"record-A"}}</tool_call>',
        }
        self.assertEqual(canonical_decision(native), canonical_decision(wrapped))
        different_argument = dict(wrapped)
        different_argument["content"] = '<tool_call>{"name":"lookup","arguments":{"a":1,"b":2,"id":"record-B"}}</tool_call>'
        self.assertNotEqual(canonical_decision(native), canonical_decision(different_argument))

    def test_canonical_tool_calls_preserve_multi_call_order(self):
        left = {"role": "assistant", "content": None, "tool_calls": [
            {"id": "a", "function": {"name": "first", "arguments": '{"x":1}'}},
            {"id": "b", "function": {"name": "second", "arguments": '{"y":2}'}},
        ]}
        right = {
            "role": "assistant",
            "content": (
                '<tool_call>{"name":"first","arguments":{"x":1}}</tool_call>'
                '<tool_call>{"name":"second","arguments":{"y":2}}</tool_call>'
            ),
        }
        self.assertEqual(canonical_decision(left), canonical_decision(right))

    def test_divergence_aligns_nonmatching_assistant_turn_indices(self):
        failed = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"prepare"}</tool_call>'},
            {"role": "tool", "content": '{"ok":true}'},
            {"role": "assistant", "content": "extra explanation"},
            {"role": "assistant", "content": '<tool_call>{"name":"bad"}</tool_call>'},
            {"role": "tool", "content": '{"ok":false}'},
        ]}
        success = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"prepare"}</tool_call>'},
            {"role": "tool", "content": '{"ok":true}'},
            {"role": "assistant", "content": '<tool_call>{"name":"good"}</tool_call>'},
            {"role": "tool", "content": '{"ok":true}'},
        ]}
        divergence = first_divergence(failed, success)
        self.assertEqual(divergence["assistant_turn"], 2)
        self.assertEqual(divergence["corrected_assistant_turn"], 1)

    def test_empty_native_tool_call_is_materialized(self):
        from steerdistill.materialize import rows_from_run

        run = {"run_dir": "/native", "success": True, "trajectory": {
            "scenario": "s", "task_id": 2,
            "messages": [
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "", "tool_calls": [{
                    "id": "call_A", "type": "function",
                    "function": {"name": "lookup", "arguments": '{"x": 1}'},
                }]},
            ],
        }}
        rows = rows_from_run(run, "ordinary_opd")
        self.assertEqual(len(rows), 1)
        self.assertIn("lookup", rows[0]["completion"])
        self.assertIn("completion_tool_calls", rows[0])

    def test_native_tool_call_with_null_content_is_materialized(self):
        run = {"run_dir": "/native-null", "success": True, "trajectory": {
            "scenario": "s", "task_id": 4,
            "messages": [
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "call_native", "type": "function",
                    "function": {"name": "lookup", "arguments": '{"id": 7}'},
                }]},
            ],
        }}
        rows = rows_from_run(run, "ordinary_opd")
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["completion"], "None")
        self.assertIn("completion_tool_calls", rows[0])

    def test_native_tool_call_fallback_uses_chat_template(self):
        class NativeTokenizer(TinyTokenizer):
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
                rendered = []
                for message in messages:
                    if message.get("role") == "assistant" and message.get("tool_calls"):
                        rendered.append("assistant:" + json.dumps(message["tool_calls"], sort_keys=True))
                    else:
                        rendered.append(f"{message['role']}:{message.get('content') or ''}")
                result = "|".join(rendered)
                return result + ("|assistant:" if add_generation_prompt else "")

        tokenizer = NativeTokenizer()
        tokenizer.model_max_length = 256
        collator = DataCollatorForSupervisedDataset(tokenizer)
        encoded = collator._encode({
            "prompt": [{"role": "user", "content": "task"}],
            "completion": "",
            "completion_tool_calls": [{
                "id": "call_native", "type": "function",
                "function": {"name": "lookup", "arguments": '{"id": 7}'},
            }],
            "add_eos": False,
        })
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": "task"}],
            tokenize=False, add_generation_prompt=True,
        )
        expected = tokenizer.encode(
            json.dumps([{
                "id": "call_native", "type": "function",
                "function": {"name": "lookup", "arguments": {"id": 7}},
            }], sort_keys=True), add_special_tokens=False,
        )
        self.assertEqual(encoded["prompt_length"], len(tokenizer.encode(prompt, add_special_tokens=False)))
        self.assertEqual(encoded["input_ids"].tolist()[-len(expected):], expected)

    def test_teacher_takeover_row_has_forward_target_without_steer_prompt(self):
        run = {"run_dir": "/rescue", "success": True, "trajectory": {
            "scenario": "s", "task_id": 3,
            "messages": [
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "teacher action"},
            ],
        }}
        skill = {
            "skill_id": "skill_r", "version": 1, "skill": "unused steer",
            "causal_divergence": {"assistant_turn": 0},
        }
        rows = rows_from_run(
            run, "revised", skill, {}, {0: "teacher_rescue"}
        )
        self.assertEqual(rows[0]["distill_mode"], "teacher_rescue")
        self.assertEqual(rows[0]["distill_target"], "bf16_teacher_forward_kl")
        self.assertEqual(rows[0]["skill_prompt"], rows[0]["prompt"])

    def test_store_step_filter_prevents_cross_step_prompt_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SkillStore(Path(directory) / "events.jsonl")
            for step, skill in ((1, "old prompt"), (2, "current prompt")):
                store.append({
                    "skill_id": f"skill-{step}", "task_key": "s:1",
                    "version": step, "step": step, "status": "proposed",
                    "skill": skill,
                })
            self.assertEqual(store.latest_by_task(1)["s:1"]["skill"], "old prompt")
            self.assertEqual(store.latest_by_task(2)["s:1"]["skill"], "current prompt")
            self.assertEqual(store.latest_by_task(3), {})

    def test_awq_pack_order_round_trip(self):
        values = torch.arange(32, dtype=torch.int64).reshape(4, 8) % 16
        packed = pack_awq(values, bits=4)
        self.assertEqual(int(packed[0, 0].item()), 0x75316420)
        restored = unpack_awq(packed, bits=4)
        self.assertTrue(torch.equal(values, restored))

    def test_divergence_and_injection(self):
        failed = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"a"}</tool_call>'},
            {"role": "assistant", "content": '<tool_call>{"name":"bad"}</tool_call>'},
        ]}
        success = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"a"}</tool_call>'},
            {"role": "assistant", "content": '<tool_call>{"name":"good"}</tool_call>'},
        ]}
        self.assertEqual(first_divergence(failed, success)["assistant_turn"], 1)
        injected = inject_skill([{"role": "system", "content": "base"}], "remember")
        self.assertIn("remember", injected[0]["content"])
        self.assertEqual(len(injected), 1)

    def test_append_only_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            store = SkillStore(path)
            store.append({
                "skill_id": "skill_a", "task_key": "s:1", "version": 1,
                "status": "proposed", "skill": "check state",
            })
            store.transition("skill_a", "verified", validation_successes=1)
            self.assertEqual(len(store.events()), 2)
            self.assertEqual(store.latest_by_task()["s:1"]["status"], "verified")
            self.assertTrue(store.compact().is_file())

    def test_local_transition_does_not_require_episode_success(self):
        reference = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"correct","x":1}</tool_call>'},
            {"role": "tool", "content": '{"updated": true}'},
            {"role": "assistant", "content": "done"},
        ]}
        candidate = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"correct","x":1}</tool_call>'},
            {"role": "tool", "content": '{"updated": true}'},
            {"role": "assistant", "content": "later wrong action"},
        ]}
        matched, kind = local_transition_match(candidate, reference, 0)
        self.assertTrue(matched)
        self.assertEqual(kind, "verified_action_transition")

        candidate["messages"][0]["content"] = '<tool_call>{"name":"wrong","x":1}</tool_call>'
        matched, kind = local_transition_match(candidate, reference, 0)
        self.assertFalse(matched)
        self.assertEqual(kind, "decision_mismatch")

        candidate["messages"][0]["content"] = '<tool_call>{"name":"correct","x":1}</tool_call>'
        candidate["messages"][1]["content"] = '{"updated": false}'
        matched, kind = local_transition_match(candidate, reference, 0)
        self.assertFalse(matched)
        self.assertEqual(kind, "observation_mismatch")

    def test_local_transition_is_bound_to_expected_causal_action(self):
        reference = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"anchor"}</tool_call>'},
            {"role": "tool", "content": '{"ok": true}'},
            {"role": "assistant", "content": '<tool_call>{"name":"correct"}</tool_call>'},
        ]}
        candidate = {"messages": [
            {"role": "assistant", "content": '<tool_call>{"name":"anchor"}</tool_call>'},
            {"role": "tool", "content": '{"ok": true}'},
        ]}
        expected = first_divergence(
            {"messages": [{"role": "assistant", "content": "wrong"}]},
            {"messages": [{"role": "assistant", "content": '<tool_call>{"name":"correct"}</tool_call>'}]},
        )["corrected_decision"]
        matched, kind = local_transition_match(
            candidate, reference, 0, expected_decision=expected
        )
        self.assertFalse(matched)
        self.assertEqual(kind, "reference_expected_mismatch")

    def test_terminal_repair_uses_final_verifier_instead_of_observation(self):
        reference = {"messages": [
            {"role": "assistant", "content": "The task is complete."},
        ]}
        candidate = {"messages": [
            {"role": "assistant", "content": "Done successfully."},
        ]}
        matched, kind = causal_transition_match(
            candidate,
            reference,
            0,
            "The task is complete.",
            candidate_success=True,
        )
        self.assertTrue(matched)
        self.assertEqual(kind, "verified_terminal_success")
        matched, kind = causal_transition_match(
            candidate,
            reference,
            0,
            "The task is complete.",
            candidate_success=False,
        )
        self.assertFalse(matched)
        self.assertEqual(kind, "terminal_verifier_failed")

    def test_action_delta_separates_three_residual_failures(self):
        def action(tool, arguments):
            return json.dumps({
                "name": "call_tool",
                "arguments": {
                    "tool_name": tool,
                    "arguments": json.dumps(arguments),
                },
            }, sort_keys=True, separators=(",", ":"))

        wrong_date = causal_action_delta(
            action("auto_assign", {"scheduled_date": "2025-05-03", "region_id": 1}),
            action("auto_assign", {"scheduled_date": "2025-05-02", "region_id": 1}),
        )
        diagnose_empty = causal_action_delta(
            "No jobs were found.",
            action("list_jobs", {"status": "new", "region_id": 1}),
        )
        replan = causal_action_delta(
            "No assignments were made.",
            action("auto_assign", {"scheduled_date": "2025-07-11", "region_id": 1}),
        )
        self.assertEqual(wrong_date["failure_type"], "argument_grounding")
        self.assertEqual(wrong_date["changed_arguments"], ["scheduled_date"])
        self.assertEqual(diagnose_empty["failure_type"], "premature_termination")
        self.assertEqual(replan["failure_type"], "premature_termination")
        self.assertEqual(len({
            wrong_date["signature"], diagnose_empty["signature"], replan["signature"]
        }), 3)

        repeated_teacher_output = {
            "decision": "revise",
            "summary": "wrong date",
            "failure_mechanism": "Incorrect date parameter",
            "failure_type": "argument_grounding",
            "relation_to_prior": "revision",
            "causal_assistant_turn": 2,
            "steer": {
                "precondition": "job task active",
                "decision_rule": "use the correct date",
                "expected_transition": "jobs scheduled",
                "recovery_check": "inspect status",
            },
        }
        previous = None
        bound = []
        for turn, delta in enumerate((wrong_date, diagnose_empty, replan), 2):
            result = bind_teacher_analysis(
                repeated_teacher_output,
                focus=turn,
                action_delta=delta,
                previous=previous,
            )
            step = {
                "index": len(bound) + 1,
                "assistant_turn": turn,
                "status": "locally_verified",
                "causal_signature": delta["signature"],
                "failure_type": result["failure_type"],
                "failure_mechanism": result["failure_mechanism"],
                "steer": result["steer"],
            }
            bound.append(step)
            previous = {"status": "locally_verified", "steer_steps": list(bound)}
        # Binding metadata must not manufacture a new teacher explanation or
        # prepend a hand-written instruction. Repeated bad analyses are rejected
        # by analysis_violations, not disguised with generated explanations.
        self.assertEqual({step["failure_mechanism"] for step in bound}, {"Incorrect date parameter"})
        for step in bound:
            self.assertEqual(json.loads(step["steer"])["decision_rule"], "use the correct date")

    def test_analyzer_cannot_repeat_old_mechanism_for_new_delta(self):
        delta = {
            "signature": "causal_new",
            "failure_type": "premature_termination",
        }
        previous = {
            "status": "locally_verified",
            "steer_steps": [{
                "status": "locally_verified",
                "causal_signature": "causal_old",
                "failure_mechanism": "Incorrect date parameter",
                "steer": json.dumps({
                    "precondition": "date known",
                    "decision_rule": "use correct date",
                    "expected_transition": "jobs found",
                    "recovery_check": "inspect jobs",
                }, sort_keys=True),
            }],
        }
        analysis = {
            "causal_assistant_turn": 3,
            "failure_type": "premature_termination",
            "relation_to_prior": "new",
            "failure_mechanism": "Incorrect date parameter",
            "steer": {
                "precondition": "empty result observed",
                "decision_rule": "inspect jobs before terminating",
                "expected_transition": "job dates become visible",
                "recovery_check": "list_jobs returns records",
            },
        }
        violations = analysis_violations(
            analysis, focus=3, action_delta=delta, previous=previous
        )
        self.assertIn(
            "new causal signature repeated a previous failure_mechanism",
            violations,
        )

    def test_realignment_can_revisit_verified_anchor(self):
        previous = {
            "status": "locally_verified",
            "steer_steps": [{
                "status": "locally_verified",
                "assistant_turn": 3,
                "causal_signature": "causal_old",
                "failure_mechanism": "premature stop",
                "steer": "inspect state",
            }],
        }
        analysis = {
            "causal_assistant_turn": 3,
            "failure_type": "wrong_tool",
            "relation_to_prior": "new",
            "failure_mechanism": "wrong follow-up tool",
            "steer": {
                "precondition": "state observed",
                "decision_rule": "use next tool",
                "expected_transition": "state advances",
                "recovery_check": "inspect observation",
            },
        }
        violations = analysis_violations(
            analysis,
            focus=3,
            action_delta={"signature": "causal_new", "failure_type": "wrong_tool"},
            previous=previous,
        )
        self.assertFalse(any("strictly after" in item for item in violations))

    def test_independent_rollout_does_not_inherit_anchor_turn_order(self):
        previous = {
            "status": "locally_verified",
            "failed_run_dir": "/route/steps/step001/repairs/event-old/plain/runs/s/task_1/attempt_0",
            "steer_steps": [{
                "status": "locally_verified",
                "assistant_turn": 5,
                "causal_signature": "causal_old",
                "failure_mechanism": "wrong lookup",
                "steer": "lookup first",
            }],
        }
        current = "/route/steps/step002/repairs/event-new/plain/runs/s/task_1/attempt_0"
        self.assertFalse(same_recovery_lineage(previous, current))
        analysis = {
            "causal_assistant_turn": 1,
            "failure_type": "wrong_tool",
            "relation_to_prior": "new",
            "failure_mechanism": "wrong update tool",
            "steer": {
                "precondition": "record found",
                "decision_rule": "use update tool",
                "expected_transition": "record changes",
                "recovery_check": "inspect updated record",
            },
        }
        violations = analysis_violations(
            analysis,
            focus=1,
            action_delta={"signature": "causal_new", "failure_type": "wrong_tool"},
            previous=previous,
            same_lineage=False,
        )
        self.assertFalse(any("strictly after" in item for item in violations))

    def test_continuation_retains_anchor_turn_order(self):
        previous = {
            "failed_run_dir": "/route/steps/step002/repairs/event-a/plain/runs/s/task_1/attempt_0",
        }
        current = "/route/steps/step002/repairs/event-a/continuation-001/runs/s/task_1/attempt_0"
        self.assertTrue(same_recovery_lineage(previous, current))
        self.assertEqual(
            recovery_lineage(current),
            "/route/steps/step002/repairs/event-a",
        )

    def test_recurrence_refines_matching_step_without_duplication(self):
        previous = [{
            "index": 1,
            "step_id": "step-old",
            "status": "verified",
            "causal_signature": "causal_repeat",
            "steer": "old rule",
        }, {
            "index": 2,
            "step_id": "step-duplicate",
            "status": "verified",
            "causal_signature": "causal_repeat",
            "steer": "duplicate old rule",
        }]
        current = {
            "index": 2,
            "step_id": "step-new",
            "status": "proposed",
            "causal_signature": "causal_repeat",
            "steer": "refined rule",
        }
        self.assertEqual(
            required_relation(
                {"steer_steps": previous},
                {"signature": "causal_repeat"},
                same_lineage=False,
            ),
            "recurrence",
        )
        merged = merge_steer_step(previous, current, "recurrence")
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["index"], 1)
        self.assertEqual(merged[0]["step_id"], "step-old")
        self.assertEqual(merged[0]["steer"], "refined rule")

    def test_pair_binding_rejects_serialized_turn_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = root / "failed.json"
            corrected = root / "corrected.json"
            failed.write_text(json.dumps({"messages": [
                {"role": "assistant", "content": '<tool_call>{"name":"bad"}</tool_call>'}
            ]}))
            corrected.write_text(json.dumps({"messages": [
                {"role": "assistant", "content": '<tool_call>{"name":"good"}</tool_call>'}
            ]}))
            pair = {
                "failed_trajectory_path": str(failed),
                "corrected_trajectory_path": str(corrected),
                "divergence": {
                    "assistant_turn": 0,
                    "failed_decision": "wrong serialized action",
                    "corrected_decision": '<tool_call>{"name":"good"}</tool_call>',
                },
            }
            with self.assertRaisesRegex(ValueError, "serialized failed_decision"):
                assert_pair_binding(pair)

    def test_integrated_steer_is_one_teacher_prompt(self):
        prompt = render_integrated_steer("single rewritten rule")
        self.assertIn("single rewritten rule", prompt)
        self.assertIn("Verified causal steering instruction", prompt)
        self.assertNotIn("[Steer 1]", prompt)
        self.assertNotIn("[Steer 2]", prompt)

    def test_status_transition_preserves_integrated_steer(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SkillStore(Path(directory) / "events.jsonl")
            store.append({
                "skill_id": "skill_a",
                "task_key": "s:1",
                "version": 1,
                "status": "proposed",
                "skill": "stale failed rule",
            })
            steps = [{
                "index": 1,
                "step_id": "step-a",
                "status": "teacher_rescue",
                "failure_mechanism": "failed mechanism",
                "steer": "stale failed rule",
            }]
            transition_with_steps(
                store,
                store.latest_by_task()["s:1"],
                "teacher_rescue",
                steps,
            )
            latest = store.latest_by_task()["s:1"]
            self.assertNotIn("stale failed rule", latest["skill"])
            self.assertEqual(latest["steer_steps"][0]["status"], "teacher_rescue")

    def test_proxy_replays_verified_anchor_then_injects_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "failed"
            run.mkdir()
            trajectory = {
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "unique task text"},
                    {"role": "assistant", "content": '<tool_call>{"name":"list"}</tool_call>'},
                    {"role": "tool", "content": "tools"},
                    {"role": "assistant", "content": "wrong"},
                ],
                "trajectory": [
                    {
                        "role": "assistant",
                        "content": '<tool_call>{"name":"list"}</tool_call>',
                        "sampling": {"token_ids": [11, 12], "logprobs": [-0.1, -0.2]},
                    },
                    {
                        "role": "assistant",
                        "content": "wrong",
                        "sampling": {"token_ids": [13], "logprobs": [-0.3]},
                    },
                ],
            }
            (run / "trajectory.json").write_text(json.dumps(trajectory))
            store = SkillStore(root / "events.jsonl")
            store.append({
                "skill_id": "skill_a", "task_key": "s:1", "version": 1,
                "status": "proposed", "skill": "use the right action",
                "task_text": "unique task text", "failed_run_dir": str(run),
                "causal_divergence": {"assistant_turn": 1},
                "causal_prefix_decisions": ['{"name":"list"}'],
            })
            proxy = ProxyState("http://unused", store.path, root / "roles.jsonl", {"proposed"})
            prefix = trajectory["messages"][:2]
            row, mode, anchor = proxy.route(prefix)
            self.assertEqual(mode, "restore_required")
            self.assertIsNone(anchor)
            row, mode, anchor = proxy.route(trajectory["messages"][:4])
            self.assertEqual(mode, "skill_inject")
            self.assertIsNone(anchor)

    def test_proxy_replays_teacher_action_once_then_returns_to_w4(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = root / "failed"
            corrected = root / "corrected"
            failed.mkdir()
            corrected.mkdir()
            base = [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "unique rescue task"},
                {"role": "assistant", "content": '<tool_call>{"name":"list"}</tool_call>'},
                {"role": "tool", "content": "listed"},
            ]
            (failed / "trajectory.json").write_text(json.dumps({
                "messages": base + [{"role": "assistant", "content": "wrong"}],
                "trajectory": [
                    {"role": "assistant", "content": base[2]["content"], "sampling": {"token_ids": [1], "logprobs": [-.1]}},
                    {"role": "assistant", "content": "wrong", "sampling": {"token_ids": [2], "logprobs": [-.2]}},
                ],
            }))
            (corrected / "trajectory.json").write_text(json.dumps({
                "messages": base + [{"role": "assistant", "content": "teacher action"}],
                "trajectory": [
                    {"role": "assistant", "content": base[2]["content"], "sampling": {"token_ids": [1], "logprobs": [-.1]}},
                    {"role": "assistant", "content": "teacher action", "sampling": {"token_ids": [9], "logprobs": [-.05]}},
                ],
            }))
            store = SkillStore(root / "events.jsonl")
            store.append({
                "skill_id": "skill_r", "task_key": "s:2", "version": 1,
                "status": "unresolved", "skill": "failed steer",
                "task_text": "unique rescue task", "failed_run_dir": str(failed),
                "corrected_run_dir": str(corrected),
                "causal_divergence": {"assistant_turn": 1},
                "causal_prefix_decisions": ['{"name":"list"}'],
            })
            proxy = ProxyState(
                "http://unused", store.path, root / "roles.jsonl",
                {"unresolved"}, mode="teacher_rescue",
            )
            _, mode, replay = proxy.route(base[:2])
            self.assertEqual(mode, "restore_required")
            self.assertIsNone(replay)
            _, mode, replay = proxy.route(base)
            self.assertEqual(mode, "teacher_rescue_replay")
            self.assertEqual(replay["content"], "teacher action")

    def test_empty_tool_arguments_match_an_omitted_argument_field(self):
        omitted = canonical_decision({
            "tool_calls": [{"name": "list_tools", "arguments": None}],
        })
        empty = canonical_decision({
            "tool_calls": [{"name": "list_tools", "arguments": {}}],
        })
        self.assertEqual(omitted, '{"name":"list_tools"}')
        self.assertEqual(empty, omitted)

    def test_prompt_fingerprint_ignores_tool_call_transport_encoding(self):
        omitted = [{
            "role": "assistant", "content": "reasoning",
            "tool_calls": [{"id": "call_a", "name": "list_tools", "arguments": None}],
        }]
        empty = [{
            "role": "assistant", "content": "reasoning",
            "tool_calls": [{"id": "call_b", "name": "list_tools", "arguments": {}}],
        }]
        self.assertEqual(prompt_fingerprint(omitted), prompt_fingerprint(empty))

    def test_task_identity_uses_first_user_not_tool_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "prompts.jsonl"
            row = {
                "prompt": (
                    "<|im_start|>user\nreal task<|im_end|>"
                    "<|im_start|>assistant\ncall tools<|im_end|>"
                    "<|im_start|>user\n<tool_response>huge schema</tool_response><|im_end|>"
                ),
                "metadata": {"scenario": "s", "task_id": 1},
            }
            manifest.write_text(json.dumps(row) + "\n")
            self.assertEqual(task_texts(manifest)["s:1"], "real task")

    def test_materializer_separates_failed_candidate_and_verified_recovery(self):
        trajectory = {
            "scenario": "s", "task_id": 1,
            "messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "wrong action"},
            ],
            "trajectory": [{
                "role": "assistant", "iteration": 1,
                "sampling": {"token_ids": [7, 8], "logprobs": [-1.0, -2.0]},
            }],
        }
        failed = {"trajectory": trajectory, "run_dir": "/failed", "success": False}
        skill = {
            "skill_id": "skill_a", "version": 1,
            "skill": "verify before acting",
            "causal_divergence": {"assistant_turn": 0},
        }
        ordinary = rows_from_run(failed, "ordinary_opd")
        recovered_trajectory = dict(trajectory)
        recovered_trajectory["messages"] = trajectory["messages"][:-1] + [
            {"role": "assistant", "content": "recovered action"}
        ]
        recovered = {"trajectory": recovered_trajectory, "run_dir": "/recovered", "success": True}
        correction = rows_from_run(recovered, "skill_recovery", skill)
        self.assertEqual(ordinary[0]["completion"], "wrong action")
        self.assertEqual(ordinary[0]["distill_mode"], "ordinary_opd")
        self.assertEqual(correction[0]["completion"], "recovered action")
        self.assertEqual(correction[0]["distill_mode"], "skill_recovery")
        self.assertNotEqual(correction[0]["skill_prompt"], correction[0]["prompt"])

    def test_reverse_opd_and_forward_recovery_backward(self):
        tokenizer = TinyTokenizer()
        collator = DataCollatorForSupervisedDataset(tokenizer)
        batch = collator([
            {
                "prompt": "plain-a", "skill_prompt": "plain-a",
                "completion": "xy", "distill_mode": "ordinary_opd",
                "add_eos": False,
            },
            {
                "prompt": "plain-b", "skill_prompt": "memory-b",
                "completion": "xy", "distill_mode": "skill_recovery",
                "add_eos": False,
            },
        ])
        student = TinyLM(1)
        teacher = TinyLM(2).eval()
        skill_reference = TinyLM(3).eval()
        for model in (teacher, skill_reference):
            for parameter in model.parameters():
                parameter.requires_grad = False
        trainer = object.__new__(SkillKDTrainer)
        trainer.teacher_model = teacher
        trainer.skill_reference_model = skill_reference
        loss = SkillKDTrainer.compute_loss(trainer, student, dict(batch))
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(any(parameter.grad is not None for parameter in student.parameters()))
        self.assertTrue(all(parameter.grad is None for parameter in teacher.parameters()))
        self.assertTrue(all(parameter.grad is None for parameter in skill_reference.parameters()))


if __name__ == "__main__":
    unittest.main()
