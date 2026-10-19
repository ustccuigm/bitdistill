"""Opt-in tests against installed benchmark environments and real assets."""
import os
from pathlib import Path
import pickle
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from steerdistill.benchmarks.sdar_environment import Environment


@unittest.skipUnless(os.getenv("STEER_TEST_ENVIRONMENTS") == "1", "requires external benchmark assets")
class EnvironmentRuntimeTest(unittest.TestCase):
    def compare_restore(self, env, response):
        prompt = env.prompt()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.pkl"
            env.save_snapshot(path)
            first = env.step(response)
            env.restore(pickle.loads(path.read_bytes()))
        self.assertEqual(env.prompt(), prompt)
        second = env.step(response)
        self.assertEqual(first, second)

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
