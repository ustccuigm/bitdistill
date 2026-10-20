"""CPU-only checks for the organized experiment data."""
import csv
import json
import math
import os
from pathlib import Path
import unittest


PAGES = Path(os.environ["STEER_PAGES_ROOT"]) if os.environ.get("STEER_PAGES_ROOT") else None
ROOT = PAGES / "experiments" if PAGES else None
METHODS = {"BF16", "Ours", "GPTQ", "EfficientQAT", "BitDistiller", "On-Policy QAD", "QeRL"}


def rows(name):
    with (ROOT / "data" / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


@unittest.skipUnless(PAGES is not None, "Set STEER_PAGES_ROOT to a gh-pages checkout to test published data")
class ExperimentDataTest(unittest.TestCase):
    def test_manifest_dimensions_and_finite_values(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for name, specification in {**manifest["tables"], **manifest["figures"]}.items():
            data = rows(name)
            self.assertEqual(len(data), specification["rows"], name)
            for row in data:
                self.assertNotIn(None, row)
                for value in row.values():
                    try:
                        number = float(value)
                    except ValueError:
                        continue
                    self.assertTrue(math.isfinite(number), name)

    def test_benchmark_coverage_and_averages(self):
        data = rows("benchmark_results.csv")
        keys = {(r["model"], r["precision"], r["method"]) for r in data}
        self.assertEqual(len(keys), 33)
        for model in ("Qwen3-8B", "Qwen3.5-4B", "Gemma 4 12B-it"):
            self.assertEqual({r["method"] for r in data if r["model"] == model and r["precision"] in ("BF16", "W4A16")}, METHODS)
        for row in data:
            values = [float(row[k]) for k in ("bfcl_v4", "tau2_bench", "webshop", "alfworld", "search_qa")]
            self.assertTrue(all(0 <= value <= 100 for value in values))
            self.assertLessEqual(abs(sum(values)/5 - float(row["average"])), .0051)

    def test_training_curves_and_bands(self):
        data = rows("training_efficiency.csv")
        for method in ("On-Policy QAD", "QeRL", "Ours"):
            selected = [r for r in data if r["method"] == method]
            hours = [int(r["gpu_hours"]) for r in selected]
            self.assertEqual(hours, [0, 8, 16, 24, 32, 40, 48, 64, 80, 96, 112])
            for row in selected:
                self.assertLessEqual(float(row["lower"]), float(row["mean"]))
                self.assertLessEqual(float(row["mean"]), float(row["upper"]))
                self.assertAlmostEqual(float(row["lower"])+float(row["upper"]), 2*float(row["mean"]), places=3)

    def test_scatter_and_matrix_dimensions(self):
        scatter = rows("inference_efficiency.csv")
        for precision in ("W4A16", "W2A16", "W4A8"):
            selected = [r for r in scatter if r["precision"] == precision]
            self.assertEqual({r["method"] for r in selected}, METHODS)
            self.assertEqual(len(selected), 7)
            self.assertTrue(all(float(r["output_tokens"]) > 0 and 0 <= float(r["pass_at_1"]) <= 100 for r in selected))
        matrix = rows("reasoning_prefix.csv")
        labels = list(matrix[0])[2:]
        self.assertEqual(len(labels), 7)
        for case in ("door_locking", "file_ordering"):
            selected = [r for r in matrix if r["case"] == case]
            self.assertEqual({r["weights_label"] for r in selected}, set(labels))
            self.assertTrue(all(0 <= float(r[label]) <= 1 for r in selected for label in labels))

    def test_case_collection_contract(self):
        index = json.loads((PAGES / "data/case_index.json").read_text())
        self.assertEqual(len(index), 40)
        self.assertEqual(len({row["task_id"] for row in index}), 40)
        for row in index:
            case = PAGES / "data" / row["path"]
            for name in ("task.json", "ground_truth.json", "analysis.json"):
                json.loads((case / name).read_text())
            self.assertTrue((case / "summary.md").is_file())
            for method in METHODS:
                score = json.loads((case / method / "score.json").read_text())
                self.assertEqual(score["passed"], method in ("BF16", "Ours"))
                self.assertFalse(score["length_limited"])
                for name in ("trajectory.json", "actions.json", "request_metadata.json"):
                    json.loads((case / method / name).read_text())
                self.assertTrue((case / method / "cot_and_actions.txt").is_file())


if __name__ == "__main__":
    unittest.main()
