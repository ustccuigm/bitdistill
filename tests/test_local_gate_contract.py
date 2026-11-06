"""Training promotion requires a real, candidate-bound precontinuation gate."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.validate.validate_skills import main as validate
from steerdistill.common import canonical_decision, causal_transition_match, local_transition_match, prompt_fingerprint
from steerdistill.store import SkillStore
from steerdistill.transition_verifier import check_boundary, validate_gate_receipt


class LocalGateContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reference_dir = self.root / "reference"
        self.candidate_dir = self.root / "runs/candidate"
        for directory in (self.reference_dir, self.candidate_dir):
            for turn, value in enumerate(("pending", "confirmed")):
                snapshot = directory / "snapshots" / f"turn_{turn:04d}"
                snapshot.mkdir(parents=True)
                database = snapshot / "state.db"
                with sqlite3.connect(database) as connection:
                    connection.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT)")
                    connection.execute("INSERT INTO orders VALUES (1, ?)", (value,))
                (snapshot / "manifest.json").write_text(json.dumps({
                    "db": "state.db", "db_sha256": hashlib.sha256(database.read_bytes()).hexdigest()}))
        self.reference = self.trajectory(self.reference_dir, "confirm")
        self.candidate = self.trajectory(self.candidate_dir, "set_status")
        self.spec = {"reference_run": str(self.reference_dir), "assistant_turn": 0,
                     "reference_turn": 0, "task_key": "bank:1", "skill_id": "skill", "skill_version": 1}
        self.spec_path = self.root / "gate_input.json"
        self.spec_path.write_text(json.dumps(self.spec))
        self.save()
        self.store = SkillStore(self.root / "store.jsonl")
        self.store.append({"skill_id": "skill", "task_key": "bank:1", "step": 1,
            "version": 1, "status": "proposed", "skill": "Confirm order",
            "corrected_run_dir": str(self.reference_dir),
            "causal_divergence": {"assistant_turn": 0, "corrected_assistant_turn": 0},
            "steer_steps": [{"index": 1, "step_id": "step", "assistant_turn": 0,
                "expected_decision": canonical_decision(self.reference["messages"][1]), "status": "proposed"}]})
        (self.root / "proxy-1.jsonl").write_text(json.dumps({"injected": True,
            "teacher_rescued": True, "skill_id": "skill", "skill_version": 1,
            "prefix_fingerprint": prompt_fingerprint(self.candidate["messages"][:1])}) + "\n")

    def trajectory(self, directory, action):
        return {"scenario": "bank", "task_id": 1, "snapshot_root": str(directory / "snapshots"),
                "messages": [{"role": "user", "content": "Confirm order"},
                    {"role": "assistant", "content": "", "tool_calls": [
                        {"id": "call-1", "function": {"name": action, "arguments": "{}"}}]},
                    {"role": "tool", "tool_call_id": "call-1", "content": "ok"}]}

    def save(self):
        for directory, trajectory in ((self.reference_dir, self.reference), (self.candidate_dir, self.candidate)):
            (directory / "trajectory.json").write_text(json.dumps(trajectory))
            (directory / "verify.code.json").write_text(json.dumps({"reward_type": "complete",
                "verify_result": {"execution_status": "success"}}))

    def gate(self, iteration=1, messages=None):
        with patch.dict(os.environ, STEER_LOCAL_GATE=str(self.spec_path)):
            return check_boundary(self.candidate["snapshot_root"], iteration,
                                  self.candidate["messages"] if messages is None else messages, self.candidate_dir)

    def receipt(self):
        return json.loads((self.candidate_dir / "local_gate.json").read_text())

    def validate_receipt(self, receipt=None, spec=None, output=None, candidate=None):
        candidate = self.candidate if candidate is None else candidate
        validate_gate_receipt(self.receipt() if receipt is None else receipt,
            self.spec if spec is None else spec, candidate["snapshot_root"], candidate["messages"],
            self.candidate_dir if output is None else output, self.reference, True, "verified_state_transition")

    def promote(self, rescue=False):
        with patch.object(sys, "argv", ["validate", "--runs", str(self.root / "runs"),
                "--store", str(self.store.path), "--step", "1", "--policy", "student",
                "--role-log-root", str(self.root)] + (["--rescue"] if rescue else [])):
            validate()
        return self.store.latest_by_id()["skill"]

    def test_real_gate_promotes_equivalent_action_and_preserves_free_suffix(self):
        self.assertTrue(self.gate())
        self.candidate["messages"].append({"role": "assistant", "content": "Done"})
        self.save()
        self.validate_receipt()
        self.assertTrue(self.gate(iteration=2))
        self.assertEqual(self.promote()["status"], "verified")

    def test_local_success_can_promote_without_episode_success(self):
        self.assertTrue(self.gate())
        (self.candidate_dir / "verify.code.json").unlink()
        self.assertEqual(self.promote()["status"], "locally_verified")

    def test_no_snapshot_legacy_match_cannot_promote_or_rescue(self):
        self.candidate = copy.deepcopy(self.reference)
        for trajectory in (self.candidate, self.reference):
            trajectory.pop("snapshot_root")
        self.save()
        self.assertTrue(local_transition_match(self.candidate, self.reference, 0)[0])
        self.assertEqual(self.promote()["status"], "unresolved")
        # Rescue logs must authenticate the new current skill version as well.
        record = self.store.latest_by_id()["skill"]
        (self.root / "proxy-1.jsonl").write_text(json.dumps({"teacher_rescued": True,
            "skill_id": "skill", "skill_version": record["version"],
            "prefix_fingerprint": prompt_fingerprint(self.candidate["messages"][:1])}) + "\n")
        self.assertEqual(self.promote(rescue=True)["status"], "rescue_failed")

    def test_missing_gate_cannot_promote(self):
        with self.assertRaisesRegex(ValueError, "before continuation"):
            self.promote()
        self.assertEqual(self.store.latest_by_id()["skill"]["status"], "proposed")

    def test_legacy_boolean_receipt_cannot_promote(self):
        (self.candidate_dir / "local_gate.json").write_text(json.dumps(dict(
            self.spec, accepted=True, checked_before_continuation=True)))
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_one_missing_snapshot_root_cannot_promote(self):
        self.gate()
        self.candidate.pop("snapshot_root")
        self.save()
        self.assertEqual(self.promote()["status"], "unresolved")

    def test_receipt_identity_and_flags_are_bound(self):
        self.gate()
        for key, value in {"candidate_run": "/elsewhere", "reference_run": "/elsewhere",
                "task_key": "bank:2", "skill_id": "other", "skill_version": 2,
                "assistant_turn": 1, "reference_turn": 1, "format": 1,
                "checked_before_continuation": False, "accepted": False,
                "candidate_boundary_sha256": "fake", "reason": "legacy"}.items():
            with self.subTest(key=key):
                receipt = dict(self.receipt(), **{key: value})
                with self.assertRaisesRegex(ValueError, "evidence mismatch"):
                    self.validate_receipt(receipt=receipt)
        stale = dict(self.spec, skill_version=2)
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.validate_receipt(spec=stale)

    def test_candidate_boundary_tamper_cannot_promote_despite_same_effect(self):
        self.gate()
        self.candidate["messages"][1]["tool_calls"][0]["function"]["name"] = "another_equivalent_tool"
        self.save()
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_reference_boundary_tamper_invalidates_receipt(self):
        self.gate()
        self.reference["messages"][2]["content"] = "different response"
        self.save()
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_copied_candidate_and_source_path_swap_invalidate_receipt(self):
        self.gate()
        clone = self.root / "runs/clone"
        shutil.copytree(self.candidate_dir, clone)
        copied = dict(self.candidate, snapshot_root=str(clone / "snapshots"))
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.validate_receipt(candidate=copied, output=clone)
        swapped = dict(self.candidate, snapshot_root=str(self.reference_dir / "snapshots"))
        with self.assertRaisesRegex(ValueError, "belong to the candidate"):
            self.validate_receipt(candidate=swapped)
        (clone / "trajectory.json").write_text(json.dumps(copied))
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_reference_source_path_is_bound_even_for_identical_copy(self):
        self.gate()
        clone = self.root / "reference-copy"
        shutil.copytree(self.reference_dir, clone)
        self.reference["snapshot_root"] = str(clone / "snapshots")
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.validate_receipt(spec=dict(self.spec, reference_run=str(clone)))

    def test_snapshot_symlink_source_swap_invalidates_receipt(self):
        self.gate()
        snapshot = self.candidate_dir / "snapshots/turn_0000"
        moved = self.root / "copied-snapshot"
        snapshot.rename(moved)
        snapshot.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_mutated_valid_snapshot_manifest_invalidates_receipt(self):
        self.gate()
        path = self.candidate_dir / "snapshots/turn_0001/manifest.json"
        manifest = json.loads(path.read_text())
        path.write_text(json.dumps(dict(manifest, generation="changed")))
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_database_tamper_fails_checksum(self):
        self.gate()
        path = self.candidate_dir / "snapshots/turn_0001/state.db"
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE orders SET status='cancelled'")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.promote()

    def test_rehashed_matching_database_changes_still_invalidate_receipt(self):
        self.gate()
        for directory in (self.candidate_dir, self.reference_dir):
            path = directory / "snapshots/turn_0001/state.db"
            with sqlite3.connect(path) as connection:
                connection.execute("UPDATE orders SET status='cancelled'")
            manifest_path = path.parent / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["db_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
        self.assertTrue(local_transition_match(self.candidate, self.reference, 0)[0])
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.promote()

    def test_late_gate_cannot_create_precontinuation_receipt(self):
        self.candidate["messages"].append({"role": "assistant", "content": "Done"})
        with self.assertRaisesRegex(ValueError, "after continuation"):
            self.gate()
        with self.assertRaises(FileNotFoundError):
            self.gate(iteration=2)
        self.assertFalse((self.candidate_dir / "local_gate.json").exists())

    def test_reference_must_be_an_action_even_with_snapshots(self):
        self.reference["messages"][1] = {"role": "assistant", "content": "Done"}
        self.assertEqual(local_transition_match(self.candidate, self.reference, 0),
                         (False, "reference_not_action"))

    def test_nonterminal_or_truncated_prose_cannot_promote_final_success(self):
        self.reference["messages"] = self.reference["messages"][:1] + [
            {"role": "assistant", "content": "Complete"}]
        self.candidate["messages"] = self.candidate["messages"][:1] + [
            {"role": "assistant", "content": "Done"}]
        record = self.store.latest_by_id()["skill"]
        record["steer_steps"][0]["expected_decision"] = "Complete"
        for mutation in ({"truncated": True}, {"messages": self.candidate["messages"] + [
                {"role": "assistant", "content": "Only now complete"}]}):
            with self.subTest(mutation=mutation):
                self.store.path.write_text(json.dumps(record) + "\n")
                candidate = self.candidate
                self.candidate = dict(candidate, **mutation)
                self.save()
                self.assertEqual(self.promote()["status"], "unresolved")
                self.candidate = candidate

    def test_terminal_requires_actual_end_and_no_truncation(self):
        reference = {"messages": [{"role": "assistant", "content": "Complete"}]}
        candidate = {"messages": [{"role": "assistant", "content": "Done"}]}
        def check(left, right):
            return causal_transition_match(left, right, 0, "Complete", candidate_success=True)
        self.assertEqual(check(candidate, reference), (True, "verified_terminal_success"))
        mutations = [
            {"messages": candidate["messages"] + [{"role": "assistant", "content": "Later"}]},
            {"messages": candidate["messages"] + [{"role": "tool", "content": "Later"}]},
            {"truncated": True}, {"truncation_info": {"finish_reason": "length"}},
            {"termination_reason": "max_iterations"}, {"termination_reason": "context_length"},
            {"termination_reason": "generation_length"},
            {"trajectory": [{"role": "assistant", "sampling": {"finish_reason": "length"}}]},
            {"messages": [{"role": "assistant", "content": "Done", "is_final": False}]},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertFalse(check(dict(candidate, **mutation), reference)[0])
                self.assertFalse(check(candidate, dict(reference, **mutation))[0])
        self.assertEqual(causal_transition_match(candidate, reference, -1, "Complete", candidate_success=True),
                         (False, "turn_missing"))


if __name__ == "__main__":
    unittest.main()
