import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from evaluate_tau2 import bind_output, selected_tasks


class Tau2InputsTest(unittest.TestCase):
    def test_validate_every_domain_before_starting_runtime(self):
        loader = lambda domain, split: [SimpleNamespace(id="0"), SimpleNamespace(id="1")]
        selected = {domain: ["0"] for domain in ("airline", "retail", "telecom")}
        self.assertEqual(selected_tasks(selected, loader), selected)
        for invalid in (["missing"], ["0", "0"], [], [0]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                selected_tasks({**selected, "telecom": invalid}, loader)
        self.assertEqual(selected_tasks(None, loader)["airline"], ["0", "1"])

    def test_output_cannot_reuse_different_model_or_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {"runtime": {"weights": "hash1"}, "tasks": {"airline": ["0"]}}
            bind_output(root, manifest)
            bind_output(root, manifest)
            for changed in ({**manifest, "runtime": {"weights": "hash2"}},
                            {**manifest, "tasks": {"airline": ["1"]}}):
                with self.assertRaisesRegex(ValueError, "inputs changed"):
                    bind_output(root, changed)
            (root / "manifest.json").unlink()
            (root / "airline.json").write_text(json.dumps({"simulations": []}))
            with self.assertRaisesRegex(ValueError, "no input manifest"):
                bind_output(root, manifest)
