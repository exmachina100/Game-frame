import json
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from gameframe.shot_plan import load_shot_plan


class ShotPlanTests(unittest.TestCase):
    def test_loads_valid_plan(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "shots.json"
            path.write_text(json.dumps({"schema": "gameframe.pong.shots.v1", "system": "pong",
              "beats": [{"label": "shot", "frames": 12, "paddle0": 42, "paddle1": 200}]}))
            beats = load_shot_plan(path)
            self.assertEqual(beats[0].paddle1, 200)

    def test_rejects_out_of_range_controls(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "shots.json"
            path.write_text(json.dumps({"schema": "gameframe.pong.shots.v1", "system": "pong",
              "beats": [{"label": "shot", "frames": 12, "paddle0": 999, "paddle1": 200}]}))
            with self.assertRaises(ValueError):
                load_shot_plan(path)
