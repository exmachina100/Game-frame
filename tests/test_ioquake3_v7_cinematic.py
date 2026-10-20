import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v7_cinematic import aim_at,target_track,export_production,launch_arguments
from gameframe.ioquake3_v4_production import load_production

class V7Tests(unittest.TestCase):
    def test_quake_axis_angles(self):
        self.assertEqual(aim_at((0,0,0),(100,0,0)),(0,0))
        self.assertAlmostEqual(aim_at((0,0,0),(0,100,0))[1],90)
        self.assertLess(aim_at((0,0,0),(100,0,10))[0],0)
        self.assertGreater(aim_at((0,0,0),(100,0,-10))[0],0)

    def test_invalid_aim(self):
        with self.assertRaises(ValueError):aim_at((0,0,0),(0,0,0))
        with self.assertRaises(ValueError):aim_at((0,0,0),(0,0,10))

    def test_export_target_track(self):
        root=Path(__file__).resolve().parents[1]
        base=load_production(root/"docs/examples/quake_v4_film.json")
        target=(300,2400,60)
        tracked=target_track(base,target)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"tracked.json"
            export_production(tracked,path)
            restored=load_production(path)
            self.assertEqual(restored,tracked)
            with self.assertRaises(FileExistsError):export_production(tracked,path)

    def test_clean_flag_profile(self):
        flags=launch_arguments()
        self.assertIn("cg_draw2D",flags)
        self.assertIn("con_notifytime",flags)
