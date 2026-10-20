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
