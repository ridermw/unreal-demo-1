from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from profile_unreal import summarize


class ProfileTests(unittest.TestCase):
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
