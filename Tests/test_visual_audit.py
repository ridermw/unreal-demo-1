from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from publish_rounds import validate_component_audit, matching_runtime_evidence


class VisualAuditTests(unittest.TestCase):
    def test_unknown_or_mismatched_runtime_cannot_count_as_matching(self):
        capture={"status":"success","clean_editor_verified":True,
                 "view":"target","camera_label":"PN_TargetCamera",
                 "scene_identity":{"sha256":"same"},"resolution":[1536,864],"screen_percentage":100,
                 "frame_cap":32,"one_frame_thread_lag":False,"runtime_settings":{"t.MaxFPS":32}}
        performance=dict(capture,provenance_finalized=True)
        self.assertTrue(matching_runtime_evidence(capture,performance))
        for value in (None,0,40):
            self.assertFalse(matching_runtime_evidence(capture,dict(performance,frame_cap=value)))
        self.assertFalse(matching_runtime_evidence(capture,dict(performance,provenance_finalized=False)))
        self.assertFalse(matching_runtime_evidence(dict(capture,view="opposite"),performance))

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
