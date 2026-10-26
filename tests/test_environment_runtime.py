"""Opt-in tests against installed benchmark environments and real assets."""
import copy
import json
import os
from pathlib import Path
import pickle
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from steerdistill.benchmarks.sdar_environment import Environment, state_hash
from steerdistill.benchmarks.online_rollout import divergence
from steerdistill.common import first_divergence
from steerdistill.transition_verifier import compare_alignment_state, unchanged_state


@unittest.skipUnless(os.getenv("STEER_TEST_TOOL_RUN"), "requires a recorded tool run with snapshots")
class ToolSnapshotRuntimeTest(unittest.TestCase):
    def test_recorded_states_ignore_text_but_detect_database_changes(self):
        root = Path(os.environ["STEER_TEST_TOOL_RUN"])
        trajectory = json.loads((root / "trajectory.json").read_text())
        trajectory["snapshot_root"] = str(root / "snapshots")
        candidate = copy.deepcopy(trajectory)
        for message in candidate["messages"]:
            if message["role"] == "assistant":
                message["content"] = "Different wording"
            elif message["role"] == "tool":
                message["content"] = "Different returned text"
        self.assertEqual(first_divergence(candidate, trajectory)["mismatch_kind"], "none")
        snapshots = trajectory["snapshot_root"]
        count = len(list(Path(snapshots).glob("turn_*/manifest.json"))) - 1
        changed = [turn for turn in range(count) if not unchanged_state(snapshots, turn)]
        self.assertTrue(changed, "The recorded run must contain a real database mutation")
        self.assertTrue(compare_alignment_state(snapshots, snapshots, changed[0], changed[0]))
        self.assertGreater(count, 1, "The recorded run must include adjacent transitions")
        adjacent = changed[0] - 1 if changed[0] else 1
        self.assertFalse(compare_alignment_state(snapshots, snapshots, changed[0], adjacent))


@unittest.skipUnless(os.getenv("STEER_TEST_ENVIRONMENTS") == "1", "requires external benchmark assets")
class EnvironmentRuntimeTest(unittest.TestCase):
    def compare_restore(self, env, response):
        prompt = env.prompt()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.pkl"
            before = env.save_snapshot(path)
            first = env.step(response)
            self.assertEqual(first["alignment_state_hash"], state_hash(env.alignment_state()))
            observation = env.observation
            env.observation = "Alternate presentation of the same environment state."
            self.assertEqual(first["alignment_state_hash"], state_hash(env.alignment_state()))
            env.observation = observation
            env.restore(pickle.loads(path.read_bytes()))
            self.assertEqual(before["alignment_hash"], state_hash(env.alignment_state()))
        self.assertEqual(env.prompt(), prompt)
        second = env.step(response)
        self.assertEqual(first, second)
        left = dict(first, before_alignment_state_hash=before["alignment_hash"])
        right = dict(second, before_alignment_state_hash=before["alignment_hash"],
                     state_hash="different-rendering", observation="Different wording")
        self.assertIsNone(divergence({"transitions": [left]}, {"transitions": [right]}))

    def test_alfworld_multiple_states(self):
        games = sorted((Path(os.environ["ALFWORLD_DATA"]) / "json_2.1.1/train").rglob("game.tw-pddl"))
        self.assertGreater(len(games), 3)
        for index in (0, len(games) // 2, len(games) - 1):
            env = Environment("alfworld", {"task_id": index, "gamefile": str(games[index])})
            try:
                for turn in range(5):
                    actions = [a for a in env.base.state.admissible_commands if a not in {"look", "inventory", "help"}]
                    self.assertTrue(actions)
                    self.compare_restore(env, f"<think>Reasoning at turn {turn}.</think><action>{actions[turn % len(actions)]}</action>")
                self.assertIn("Reasoning at turn 0.", env.prompt())
                self.assertEqual(env.prompt().count("<think>Reasoning at turn"), 5)
            finally:
                env.close()

    def test_webshop_search_and_navigation(self):
        env = Environment("webshop", {"task_id": 500})
        try:
            self.compare_restore(env, "<think>Find products.</think><action>search[blue shirt]</action>")
            clickable = env.env.get_available_actions()["clickables"]
            self.assertTrue(clickable)
            self.compare_restore(env, f"<think>Inspect an option.</think><action>click[{clickable[-1]}]</action>")
        finally:
            env.close()

    def test_search_real_retrieval_and_answer(self):
        env = Environment("search_qa", {"task_id": 0, "question": "What is the capital of France?",
                          "ground_truth": {"target": ["Paris"]}, "data_source": "nq"})
        try:
            self.compare_restore(env, "<think>Check the capital.</think><search>capital of France</search>")
            self.assertIn("Doc 1:", env.observation)
            self.compare_restore(env, "<think>The capital is Paris.</think><answer>Paris</answer>")
            self.assertTrue(env.success)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
