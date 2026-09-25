from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from publish_rounds import validate_component_audit


class VisualAuditTests(unittest.TestCase):
    def setUp(self):
        self.checklist = {"groups": [{"components": ["train.buffer: inspect", "opposite.facade: inspect"]}]}
        self.entries = [{"id": name, "status": "wrong", "target_observation": "Target feature",
                         "actual_observation": "Incorrect implemented feature", "correction": "Rebuild"}
                        for name in ("train.buffer", "opposite.facade")]

    def test_complete_audit(self):
        validate_component_audit({"component_audit": self.entries}, self.checklist)

    def test_missing_background_cannot_publish(self):
        with self.assertRaises(ValueError):
            validate_component_audit({"component_audit": self.entries[:1]}, self.checklist)

    def test_duplicate_entry_cannot_replace_missing_feature(self):
        with self.assertRaises(ValueError):
            validate_component_audit({"component_audit": self.entries[:1] * 2}, self.checklist)
