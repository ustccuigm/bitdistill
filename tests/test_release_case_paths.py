"""Reviewed benchmark paths do not weaken the source release checks."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE = "experiments/cases/033_multi_turn_miss_param_26/BitDistiller/trajectory.json"


class ReleaseCasePathsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("scripts/_bootstrap.sh", "scripts/validate/check_release.sh", CASE):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def check(self):
        return subprocess.run(["bash", str(self.root / "scripts/validate/check_release.sh")],
                              env={"PATH": os.environ["PATH"]}, capture_output=True, text=True)

    def test_exact_reviewed_transcript_is_allowed(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_changed_transcript_loses_exception(self):
        path = self.root / CASE
        path.write_text(path.read_text() + "\n")
        self.assertEqual(self.check().returncode, 2)

    def test_new_home_path_is_rejected(self):
        (self.root / "note.txt").write_text("/" + "home" + "/person/project")
        self.assertEqual(self.check().returncode, 2)

    def test_credentials_are_still_rejected(self):
        (self.root / "note.txt").write_text("sk-" + "x" * 40)
        result = self.check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("forbidden_metadata", result.stderr)


if __name__ == "__main__":
    unittest.main()
