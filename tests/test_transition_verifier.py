import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from steerdistill.common import first_divergence, local_transition_match
from steerdistill.transition_verifier import check_boundary, compare_transition


class TransitionVerifierTest(unittest.TestCase):
    def test_equivalent_action_is_retained_and_audited_as_student_target(self):
        from steerdistill.common import canonical_decision, prompt_fingerprint
        from steerdistill.store import SkillStore
        from scripts.validate.validate_skills import main as validate
        from steerdistill.materialize import rows_from_run
        from scripts.data.audit_training_data import main as audit
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            teacher_dir, candidate_dir = root / "teacher", root / "runs/candidate"
            for directory in (teacher_dir, candidate_dir):
                self.snapshot(directory / "snapshots", 0, "pending")
                self.snapshot(directory / "snapshots", 1, "confirmed")
            reference = dict(self.trajectory(teacher_dir / "snapshots", "confirm", "ok"), scenario="s", task_id=1)
            candidate = dict(self.trajectory(candidate_dir / "snapshots", "set_status", "done"), scenario="s", task_id=1)
            for directory, trajectory in ((teacher_dir, reference), (candidate_dir, candidate)):
                (directory / "trajectory.json").write_text(json.dumps(trajectory))
                (directory / "verify.code.json").write_text(json.dumps({
                    "reward_type": "complete" if directory == teacher_dir else "incomplete",
                    "verify_result": {"execution_status": "success"}}))
            (candidate_dir / "local_gate.json").write_text(json.dumps({"assistant_turn": 0,
                "reference_turn": 0, "reference_run": str(teacher_dir), "accepted": True,
                "checked_before_continuation": True}))
            store = SkillStore(root / "store.jsonl")
            expected = canonical_decision(reference["messages"][1])
            step = {"index": 1, "step_id": "step", "assistant_turn": 0, "status": "proposed",
                    "expected_decision": expected, "causal_signature": "state", "failure_mechanism": "Order not confirmed",
                    "integrated_steer": "Confirm the order", "steer": "Confirm the order"}
            store.append({"skill_id": "skill", "task_key": "s:1", "step": 1, "version": 1,
                "status": "proposed", "skill": "Confirm the order", "analysis_schema": "causal-steer-v2",
                "corrected_run_dir": str(teacher_dir), "steer_steps": [step],
                "causal_divergence": {"assistant_turn": 0, "corrected_assistant_turn": 0}})
            (root / "proxy-1.jsonl").write_text(json.dumps({"injected": True, "skill_id": "skill",
                "skill_version": 1, "prefix_fingerprint": prompt_fingerprint(candidate["messages"][:1])}) + "\n")
            with patch.object(sys, "argv", ["validate", "--runs", str(root / "runs"), "--store", str(store.path),
                    "--step", "1", "--policy", "student", "--role-log-root", str(root)]):
                validate()
            record = store.latest_by_id()["skill"]
            self.assertEqual(record["status"], "locally_verified")
            accepted = record["steer_steps"][0]
            self.assertNotEqual(accepted["expected_decision"], expected)
            rows = rows_from_run({"run_dir": str(candidate_dir), "trajectory": candidate, "success": False},
                "revised", record, {0: "Confirm the order"}, {0: "skill_recovery"}, {0: accepted})
            data = root / "rows.jsonl"
            data.write_text("".join(json.dumps(row) + "\n" for row in rows))
            with patch.object(sys, "argv", ["audit", "--data", str(data), "--store", str(store.path)]):
                audit()

    def test_repair_preserves_prefix_snapshots_without_aliasing_anchor(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from steerdistill.teacher.generate_verified import preserve_snapshot_prefix
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root / "source", root / "output"
            output.mkdir()
            for index in (0, 1):
                self.snapshot(source, index, "pending")
                manifest = source / f"turn_{index:04d}/manifest.json"
                data = json.loads(manifest.read_text())
                manifest.write_text(json.dumps(dict(data, iteration=index)))
            preserve_snapshot_prefix(source / "turn_0001", output)
            self.assertEqual((output / "snapshots/turn_0000").resolve(), (source / "turn_0000").resolve())
            self.assertFalse((output / "snapshots/turn_0001").exists())
            self.snapshot(output / "snapshots", 1, "changed")
            self.assertNotEqual((output / "snapshots/turn_0001/state.db").read_bytes(),
                                (source / "turn_0001/state.db").read_bytes())

    def test_search_effect_ignores_query_wording_but_not_retrieved_information(self):
        from steerdistill.benchmarks.sdar_environment import Environment
        environment = object.__new__(Environment)
        environment.benchmark = "search_qa"
        environment.success = False
        environment.env = SimpleNamespace(done=False, turns=1, chat_history=[
            {"role": "assistant", "content": "<search>Paris capital</search>"},
            {"role": "user", "content": "Doc 1: Paris is the capital of France."}])
        expected = environment.transition_state()
        environment.env.turns = 9
        environment.env.chat_history[0]["content"] = "<search>capital of France</search>"
        self.assertEqual(environment.transition_state(), expected)
        environment.env.chat_history[1]["content"] = "Doc 1: An unrelated document."
        self.assertNotEqual(environment.transition_state(), expected)

    def test_webshop_effect_excludes_action_counters_not_product_selection(self):
        from steerdistill.benchmarks.sdar_environment import Environment
        environment = object.__new__(Environment)
        environment.benchmark = "webshop"
        environment.description = "Buy the requested item"
        environment.observation = "Product A"
        session = {"asin": "A", "options": {"size": "M"}, "actions": {"search": 1}}
        environment.env = SimpleNamespace(session="s", server=SimpleNamespace(user_sessions={"s": session}))
        expected = json.loads(json.dumps(environment.transition_state()))
        session["actions"]["search"] = 5
        self.assertEqual(environment.transition_state(), expected)
        session["options"]["size"] = "L"
        self.assertNotEqual(environment.transition_state(), expected)

    def test_alignment_skips_only_state_preserving_extra_reads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            teacher, student = root / "teacher", root / "student"
            for index, value in enumerate(("pending", "confirmed")):
                self.snapshot(teacher, index, value)
            for index, value in enumerate(("pending", "pending", "confirmed")):
                self.snapshot(student, index, value)
            reference = self.trajectory(teacher, "confirm", "ok")
            candidate = self.trajectory(student, "inspect", "pending")
            candidate["messages"].extend(self.trajectory(student, "set_status", "done")["messages"][1:])
            self.assertEqual(first_divergence(candidate, reference)["mismatch_kind"], "none")
            candidate["messages"][2]["content"] = "Error: wrong request"
            self.assertEqual(first_divergence(candidate, reference)["assistant_turn"], 0)

    def snapshot(self, root, turn, value):
        directory = root / f"turn_{turn:04d}"
        directory.mkdir(parents=True)
        db = directory / "state.db"
        with sqlite3.connect(db) as connection:
            connection.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT)")
            connection.execute("INSERT INTO orders VALUES (1, ?)", (value,))
        (directory / "manifest.json").write_text(json.dumps({"db": "state.db",
            "db_sha256": hashlib.sha256(db.read_bytes()).hexdigest()}))

    def trajectory(self, root, action, result):
        return {"snapshot_root": str(root), "messages": [
            {"role": "user", "content": "Confirm order"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "transport", "function": {"name": action, "arguments": "{}"}}]},
            {"role": "tool", "content": result}]}

    def test_different_actions_same_effect_and_identical_text_wrong_effect(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            teacher, candidate, wrong = [root / name for name in ("teacher", "candidate", "wrong")]
            for directory in (teacher, candidate, wrong):
                self.snapshot(directory, 0, "pending")
                self.snapshot(directory, 1, "cancelled" if directory == wrong else "confirmed")
            reference = self.trajectory(teacher, "confirm", "confirmed")
            equivalent = self.trajectory(candidate, "set_status", "done")
            bad = self.trajectory(wrong, "confirm", "confirmed")
            self.assertEqual(local_transition_match(equivalent, reference, 0), (True, "verified_state_transition"))
            self.assertEqual(local_transition_match(equivalent, reference, 0, expected_decision="unbound"),
                             (False, "reference_expected_mismatch"))
            self.assertEqual(first_divergence(equivalent, reference)["mismatch_kind"], "none")
            self.assertEqual(local_transition_match(bad, reference, 0), (False, "postcondition_state_mismatch"))
            self.assertEqual(first_divergence(bad, reference)["assistant_turn"], 0)

    def test_read_actions_require_evidence_and_unchanged_database(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("teacher", "candidate"):
                for turn in (0, 1):
                    self.snapshot(root / name, turn, "pending")
            reference = self.trajectory(root / "teacher", "lookup", '{"price":10,"id":1}')
            candidate = self.trajectory(root / "candidate", "search", '{"id":1,"price":10}')
            self.assertTrue(local_transition_match(candidate, reference, 0)[0])
            candidate["messages"][-1]["content"] = '{"id":1,"price":20}'
            self.assertFalse(local_transition_match(candidate, reference, 0)[0])

    def test_boundary_records_failure_and_missing_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reference_dir = root / "reference"
            candidate_dir = root / "candidate"
            for directory in (reference_dir, candidate_dir):
                self.snapshot(directory / "snapshots", 0, "pending")
                self.snapshot(directory / "snapshots", 1, "confirmed" if directory == reference_dir else "pending")
            reference = self.trajectory(reference_dir / "snapshots", "confirm", "ok")
            (reference_dir / "trajectory.json").write_text(json.dumps(reference))
            spec = root / "gate.json"
            spec.write_text(json.dumps({"reference_run": str(reference_dir), "assistant_turn": 0, "reference_turn": 0}))
            with patch.dict(os.environ, STEER_LOCAL_GATE=str(spec)):
                self.assertFalse(check_boundary(candidate_dir / "snapshots", 1, reference["messages"], candidate_dir))
            receipt = json.loads((candidate_dir / "local_gate.json").read_text())
            self.assertTrue(receipt["checked_before_continuation"])
            self.assertFalse(receipt["accepted"])
            (candidate_dir / "snapshots/turn_0001/state.db").unlink()
            with self.assertRaises(FileNotFoundError):
                compare_transition(candidate_dir / "snapshots", reference_dir / "snapshots", 0, 0, [], [])


if __name__ == "__main__":
    unittest.main()
