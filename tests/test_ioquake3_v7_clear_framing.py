import unittest
from pathlib import Path
from gameframe.ioquake3_v4_production import load_production,run_production

class ClearFramingTests(unittest.TestCase):
    def test_selected_visible_direction_and_safe_fixed_position(self):
        source=Path(__file__).resolve().parents[1]/"docs/examples/quake_v7_clear_framing.json"
        film=load_production(source)
        self.assertEqual(len(film.shots),2)
        for shot in film.shots:
            self.assertTrue(all(p.position==(212.,2360.,56.) for p in shot.keyframes))
            self.assertTrue(all(270<=p.yaw<=330 for p in shot.keyframes))
        self.assertEqual(film.shots[0].keyframes[0].yaw,315)
        manifest=run_production(film)
        self.assertEqual(manifest["status"],"completed")
        self.assertEqual(sum(s["camera"]["sample_count"] for s in manifest["shots"]),82)
