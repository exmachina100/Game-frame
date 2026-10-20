import json
import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v4_production import load_production,run_production
from gameframe.ioquake3_v4_source_patch import patch_source
from gameframe.ioquake3_source_patch import patch_source as patch_v1

class FakeBridge:
    def __init__(self):
        self.poses=[]
        self.captures=[]
        self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append((position,pitch,yaw,roll,fov))
        return {"queued":True}
    def capture(self,name):
        self.captures.append((name,len(self.poses)))
        return {"queued":True}
    def reset(self):
        self.resets+=1
        return {"queued":True}

class V4Tests(unittest.TestCase):
    def test_shipped_example(self):
        root=Path(__file__).resolve().parents[1]
        production=load_production(root/"docs/examples/quake_v4_film.json")
        self.assertEqual(len(production.shots),3)
        result=run_production(production)
        self.assertEqual(result["status"],"completed")
        self.assertEqual(len(result["shots"]),3)
        self.assertEqual(sum(s["camera"]["sample_count"] for s in result["shots"]),195)

    def test_live_capture_timing(self):
        root=Path(__file__).resolve().parents[1]
        production=load_production(root/"docs/examples/quake_v4_film.json")
        bridge=FakeBridge()
        result=run_production(production,bridge,live=True,capture=True,
                              rate=1,clock=lambda:0,sleep=lambda _:None)
        self.assertEqual(len(bridge.captures),3)
        self.assertEqual(bridge.resets,1)
        self.assertEqual([n for n,_ in bridge.captures],
                         ["arena_film_24s_"+s.name for s in production.shots])
        self.assertTrue(all(s["captures"][0]["file_verified"] is False for s in result["shots"]))

    def test_capture_requires_live(self):
        root=Path(__file__).resolve().parents[1]
        production=load_production(root/"docs/examples/quake_v4_film.json")
        with self.assertRaises(ValueError):
            run_production(production,capture=True)

    def test_source_patch(self):
        source=patch_v1("void CL_Frame ( int msec ) {}")
        upgraded=patch_source(source)
        self.assertIn("gfcapture",upgraded)
        with self.assertRaises(ValueError):
            patch_source(upgraded)
