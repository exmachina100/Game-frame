import json
import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_camera_sequence import CameraKey, interpolate, load_sequence, sample, run_sequence

class FakeBridge:
    def __init__(self):
        self.calls=[]
    def set_view(self,*args):
        self.calls.append(args)
        return {"queued":True}

class SequenceTests(unittest.TestCase):
    def setUp(self):
        self.keys=(CameraKey(0,(212,2360,56),350),CameraKey(2,(212,2360,56),10))

    def test_shortest_yaw_arc(self):
        self.assertAlmostEqual(interpolate(self.keys[0],self.keys[1],1).yaw,0)
        self.assertEqual(sample(self.keys,5).yaw,10)

    def test_dry_run_does_not_call_bridge(self):
        b=FakeBridge()
        result=run_sequence(self.keys,b,rate=2)
        self.assertEqual(len(result),5)
        self.assertEqual(b.calls,[])
        self.assertTrue(all(not r["queued"] for r in result))

    def test_live_sends_bounded_samples(self):
        b=FakeBridge()
        result=run_sequence(self.keys,b,rate=2,dry_run=False,clock=lambda:0,sleep=lambda _:None)
        self.assertEqual(len(b.calls),5)
        self.assertEqual(len(result),5)
        self.assertEqual(b.calls[0][:3],(212,2360,56))
        self.assertAlmostEqual(b.calls[2][-1],0)

    def test_requires_explicit_translation(self):
        keys=(self.keys[0],CameraKey(2,(400,2360,56),10))
        with self.assertRaisesRegex(ValueError,"translation"):
            run_sequence(keys,FakeBridge(),rate=2)

    def test_json_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"sequence.json"
            path.write_text(json.dumps({"keyframes":[{"time":0,"position":[212,2360,56],"yaw":350},
                         {"time":2,"position":[212,2360,56],"yaw":10}]}))
            self.assertEqual(load_sequence(path),self.keys)
            path.write_text(json.dumps({"keyframes":[{"time":0,"position":[212,2360,56],"yaw":0},
                         {"time":0,"position":[212,2360,56],"yaw":20}]}))
            with self.assertRaises(ValueError):
                load_sequence(path)
