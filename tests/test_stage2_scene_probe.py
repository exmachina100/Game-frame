import unittest
from gameframe.stage2_scene_probe import parse_scene
from gameframe.stage2_scene_probe_patch import patch_source
class ProbeTests(unittest.TestCase):
    def test_parse_scene(self):
        data=parse_scene("SCENE 1234 2\nE 1 1 12.000 34.000 56.000 2 3 4\nE 2 3 0 0 -1 0 0 1\n")
        self.assertEqual(data["server_time_ms"],1234)
        self.assertEqual(len(data["entities"]),2)
        self.assertFalse(data["actions_supported"])
    def test_unavailable(self):
        self.assertFalse(parse_scene("UNAVAILABLE\n")["available"])
    def test_reject_partial_and_duplicates(self):
        for response in ("SCENE 3 1\n", "SCENE 3 2\nE 1 1 0 0 0 1 1 1\nE 1 1 0 0 0 1 1 1\n"):
            with self.assertRaises(ValueError):parse_scene(response)
    def test_patch_once(self):
        source="    /* GAMEFRAME_V7_WORLD_TRACE */"
        result=patch_source(source)
        self.assertIn("cl.snap.serverTime",result)
        with self.assertRaises(ValueError):patch_source(result)
