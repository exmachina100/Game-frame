import unittest
from gameframe.stage2_scene_brief import validate_scene,capability_report

SCENE={"title":"Arena Arrival","map":"q3dm1","duration":8,
"beats":[{"start":0,"end":4,"intent":"establishing",
"subject":"environment","action":"Show arena"},
{"start":4,"end":8,"intent":"reveal",
"subject":"hero","action":"Walk to statue"}]}

class Stage2SceneTests(unittest.TestCase):
    def test_valid_scene_and_capabilities(self):
        self.assertEqual(validate_scene(SCENE)["map"],"q3dm1")
        report=capability_report(SCENE)
        self.assertFalse(report["executable"])
        self.assertFalse(report["actor_actions_executed"])
        self.assertEqual(len(report["unsupported_actions"]),1)
    def test_reject_overlap(self):
        bad={**SCENE,"beats":[SCENE["beats"][0],{**SCENE["beats"][1],"start":3}]}
        with self.assertRaisesRegex(ValueError,"non-overlapping"):validate_scene(bad)
    def test_reject_unsupported_intent(self):
        bad={**SCENE,"beats":[{**SCENE["beats"][0],"intent":"teleport"},SCENE["beats"][1]]}
        with self.assertRaises(ValueError):validate_scene(bad)
    def test_reject_nonfinite_timing(self):
        with self.assertRaises(ValueError):validate_scene({**SCENE,"duration":float("nan")})
