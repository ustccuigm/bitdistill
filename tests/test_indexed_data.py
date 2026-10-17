import json
from pathlib import Path
import pickle
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "train"))
from data_loading import make_supervised_data_module
from chat_templates import normalize_tool_arguments


class IndexedDataTest(unittest.TestCase):
    def test_null_tool_arguments_work_for_both_native_and_wrapped_calls(self):
        for raw in (None, "null", "{}", {}):
            for wrapped in (False, True):
                function = {"name": "list_tools", "arguments": raw}
                call = {"function": function} if wrapped else function
                messages = [{"role": "assistant", "tool_calls": [call]}]
                normalized = normalize_tool_arguments(messages)[0]["tool_calls"][0]
                self.assertEqual((normalized["function"] if wrapped else normalized)["arguments"], {})
                self.assertEqual(function["arguments"], raw)
        with self.assertRaises(ValueError):
            normalize_tool_arguments([{"tool_calls": [{"name": "bad", "arguments": "[]"}]}])

    def test_all_records_remain_trainable_after_worker_serialization(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.jsonl"
            rows = [{"prompt": f"question {index}", "completion": f"answer {index}"} for index in range(25)]
            path.write_text("\n" + "\n".join(json.dumps(row) for row in rows) + "\n")
            module = make_supervised_data_module(None, SimpleNamespace(data_path=path, max_train_samples=25))
            dataset = module["train_dataset"]
            self.assertEqual(len(dataset), 25)
            self.assertEqual(dataset[24], rows[24])
            self.assertEqual(dataset[0], rows[0])
            restored = pickle.loads(pickle.dumps(dataset))
            self.assertEqual(restored[17], rows[17])
            self.assertIsNone(module["eval_dataset"])

    def test_only_an_explicit_sample_limit_reduces_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.jsonl"
            path.write_text("\n".join(json.dumps({"prompt": str(i), "completion": str(i)}) for i in range(20)))
            module = make_supervised_data_module(None, SimpleNamespace(data_path=path, max_train_samples=7))
            self.assertEqual(len(module["train_dataset"]), 7)
            self.assertEqual(len({module["train_dataset"][i]["prompt"] for i in range(7)}), 7)


if __name__ == "__main__":
    unittest.main()
