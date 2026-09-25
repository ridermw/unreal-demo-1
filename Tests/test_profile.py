from pathlib import Path
import sys
import unittest
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from profile_unreal import summarize, captured_pacing, finalized_identity


class ProfileTests(unittest.TestCase):
    def test_capture_conditions_come_from_log(self):
        self.assertEqual(captured_pacing('t.MaxFPS = "40"\nr.OneFrameThreadLag = "0"'),(40,False))
        self.assertEqual(captured_pacing('t.MaxFPS = "0"\nr.OneFrameThreadLag = "1"'),(0,True))

    def test_readbacks_override_command_requests(self):
        text='Cmd: t.MaxFPS 32\nCmd: r.OneFrameThreadLag 0\nt.MaxFPS = "0"\nr.OneFrameThreadLag = "1"'
        self.assertEqual(captured_pacing(text),(0,True))
        self.assertEqual(captured_pacing("Cmd: t.MaxFPS 32\nCmd: r.OneFrameThreadLag 0"),(None,None))

    def test_pending_or_tampered_profile_cannot_be_replayed(self):
        provenance={"status":"success","scene_identity":{"sha256":"scene"},
                    "log_sha256":hashlib.sha256(b"log").hexdigest(),
                    "csv_sha256":hashlib.sha256(b"csv").hexdigest()}
        self.assertEqual(finalized_identity(provenance,b"log",b"csv"),{"sha256":"scene"})
        with self.assertRaises(RuntimeError):
            finalized_identity(provenance,b"log",b"tampered")
        for status in ("pending","failed"):
            with self.assertRaises(RuntimeError):
                finalized_identity(dict(provenance,status=status),b"log",b"csv")

    def test_missing_capture_settings_remain_unknown(self):
        self.assertEqual(captured_pacing("No recorded console settings"),(None,None))

    def test_expanding_columns_and_warmup(self):
        rows = [["EVENTS", "FrameTime"]]
        rows += [["", "200"] for _ in range(360)]
        rows += [["", "20", "10"] for _ in range(360)]
        rows += [["EVENTS", "FrameTime", "NewStat"], ["[HasHeaderRowAtEnd]", "1"]]
        metrics, _, samples = summarize(rows)
        self.assertEqual(len(samples), 360)
        self.assertEqual(metrics["median_fps"], 50)
        self.assertTrue(metrics["meets_target"])

    def test_incomplete_capture_fails(self):
        with self.assertRaises(RuntimeError):
            summarize([["FrameTime"], ["20"], ["[metadata]"]])

    def test_footer_does_not_count_as_frame(self):
        rows = [["EVENTS", "FrameTime"]] + [["", "20"] for _ in range(719)]
        rows += [["EVENTS", "FrameTime"], ["[HasHeaderRowAtEnd]", "1"]]
        with self.assertRaises(RuntimeError):
            summarize(rows)
