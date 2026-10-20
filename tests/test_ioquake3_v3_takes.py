import json
import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v3_takes import Pose,Take,load_take,sample,run_take

class FakeRenderer:
    def __init__(self):
        self.poses=[]
        self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append((position,pitch,yaw,roll,fov))
        return {"queued":True}
    def reset(self):
        self.resets+=1
        return {"queued":True}

class V3TakesTests(unittest.TestCase):
    def setUp(self):
        self.take=Take("Test shot",(
            Pose(0,(212,2360,56),0,350,0,85),
            Pose(2,(212,2360,56),10,10,25,55)))

    def test_interpolates_six_axis_pose(self):
        mid=sample(self.take,1)
        self.assertEqual(mid.position,(212.,2360.,56.))
        self.assertAlmostEqual(mid.pitch,5)
        self.assertAlmostEqual(mid.yaw,360)
        self.assertAlmostEqual(mid.roll,12.5)
        self.assertAlmostEqual(mid.fov,70)

    def test_dry_run_has_no_calls(self):
        bridge=FakeRenderer()
        manifest=run_take(self.take,bridge,rate=2)
        self.assertEqual(bridge.poses,[])
        self.assertEqual(manifest["sample_count"],5)
        self.assertEqual(manifest["queued_count"],0)

    def test_live_uses_renderer_and_resets(self):
        bridge=FakeRenderer()
        manifest=run_take(self.take,bridge,rate=2,live=True,clock=lambda:0,sleep=lambda _:None)
        self.assertEqual(manifest["queued_count"],5)
        self.assertEqual(len(bridge.poses),5)
        self.assertEqual(bridge.resets,1)

    def test_translation_requires_opt_in(self):
        other=Take("move",(self.take.keyframes[0],Pose(2,(222,2360,56),0,0,0,85)))
        with self.assertRaisesRegex(ValueError,"Translation"):
            run_take(other)

    def test_json_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"take.json"
            data={"name":"Test shot","keyframes":[{"time":p.time,"position":list(p.position),
                 "pitch":p.pitch,"yaw":p.yaw,"roll":p.roll,"fov":p.fov} for p in self.take.keyframes]}
            path.write_text(json.dumps(data))
            self.assertEqual(load_take(path),self.take)
            data["keyframes"][1]["fov"]=200
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_take(path)
