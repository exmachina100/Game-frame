import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from gameframe.timeline import Beat, play_timeline


class FakeBridge:
    def __init__(self):
        self.calls = []
        self.frame = 0
        self.paused = True

    def request(self, action, **kwargs):
        self.calls.append((action, kwargs))
        if action == "pause":
            self.paused = True
        elif action == "resume":
            self.paused = False
        elif action == "status" and not self.paused:
            self.frame += 7
        info = {"system": "pong", "screen_frames": {":screen": self.frame},
                "paused": self.paused}
        if action == "set_paddle":
            info = {"applied": True}
        return {"info": info}


class TimelineTests(unittest.TestCase):
    def test_record_failure_writes_manifest_and_keeps_original_error(self):
        class BrokenRecorder(FakeBridge):
            def request(self, action, **kwargs):
                if action == "status" and not self.paused:
                    raise TimeoutError("simulated stalled recorder")
                if action == "pause" and not self.paused:
                    self.paused = True
                    raise TimeoutError("simulated cleanup failure")
                return super().request(action, **kwargs)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "failed.json"
            with self.assertRaisesRegex(TimeoutError, "stalled recorder"):
                play_timeline(BrokenRecorder(), [Beat("test", 10, 128, 128)], record=True, manifest=path)
            report = json.loads(path.read_text())
            self.assertFalse(report["complete"])
            self.assertIn("stalled recorder", report["error"])
            self.assertIn("stalled recorder", report["error"])
            # The inner emergency pause may fail once, then the outer
            # timeline cleanup can succeed. No cleanup_errors key is needed
            # when the final recovery commands completed successfully.
            self.assertIn(("record_stop", {}), bridge.calls)

    def test_validation(self):
        for value in (-1, 256, True, 1.5):
            with self.assertRaises(ValueError):
                Beat("invalid", 12, value, 128)

    def test_records_manifest_and_stops(self):
        bridge = FakeBridge()
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "manifest.json"
            result = play_timeline(bridge, [Beat("one", 10, 5, 250)], record=True, manifest=output)
            self.assertTrue(result["complete"])
            self.assertFalse(result["frame_exact"])
            self.assertEqual(result["beats"][0]["paddle0"], 5)
            self.assertEqual(result["beats"][0]["paddle1"], 250)
            self.assertTrue(json.loads(output.read_text())["complete"])
            self.assertIn(("record_start", {}), bridge.calls)
            self.assertIn(("record_stop", {}), bridge.calls)
            self.assertTrue(bridge.paused)
