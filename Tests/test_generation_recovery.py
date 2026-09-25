import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generation", ROOT / "Scripts/generate_textures.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class GenerationRecoveryTests(unittest.TestCase):
    def test_submitted_output_is_reconciled_and_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "brick.png"
            shutil.copy2(ROOT / "Art/Textures/brick.png", output)
            metadata = json.loads((ROOT / "Art/Textures/brick.png.metadata.json").read_text())
            metadata["account"] = "discard-me"
            receipt = output.with_suffix(".png.metadata.json")
            receipt.write_text(json.dumps(metadata))
            job = GEN.reconcile_output(output, {"status": "submitted"})
            self.assertEqual(job["status"], "completed")
            self.assertEqual(len(job["sha256"]), 64)
            self.assertNotIn("account", json.loads(receipt.read_text()))
            with self.assertRaises(ValueError):
                GEN.reconcile_output(output, {"sha256": "incorrect"})

    def test_missing_receipt_is_not_a_completed_job(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "brick.png"
            shutil.copy2(ROOT / "Art/Textures/brick.png", output)
            with self.assertRaises(RuntimeError):
                GEN.reconcile_output(output, {})
