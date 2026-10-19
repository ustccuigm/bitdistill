import json
from pathlib import Path
import tempfile
import unittest

from steerdistill.runtime_validation import behavioral_metadata


class RuntimeMetadataTest(unittest.TestCase):
    def test_writer_version_is_not_a_generation_setting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generation_config.json"
            config = {"transformers_version": "5.10.0", "eos_token_id": [1, 50],
                      "suppress_tokens": [123], "temperature": 1.0}
            path.write_text(json.dumps(config))
            expected = behavioral_metadata(path)
            config["transformers_version"] = "5.16.1"
            path.write_text(json.dumps(config))
            self.assertEqual(behavioral_metadata(path), expected)
            for key, value in (("eos_token_id", [1]), ("suppress_tokens", []), ("temperature", 0.5)):
                path.write_text(json.dumps({**config, key: value}))
                self.assertNotEqual(behavioral_metadata(path), expected)


if __name__ == "__main__":
    unittest.main()
