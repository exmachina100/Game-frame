import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v7_directional_scout import directions,directional_scout

class Bridge:
    def __init__(self,folder):
        self.folder=folder
        self.poses=[]
        self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append((tuple(position),yaw))
        return {"queued":True}
    def capture(self,name):
        (self.folder/(name+".jpg")).write_bytes(b"jpeg-test")
        return {"queued":True}
    def reset(self):
        self.resets+=1

class DirectionalTests(unittest.TestCase):
    def test_eight_yaw_angles(self):
        self.assertEqual(directions(),(0,45,90,135,180,225,270,315))
        with self.assertRaises(ValueError):directions(50)

    def test_scout_full_circle(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);shots=root/"screens";shots.mkdir()
            bridge=Bridge(shots)
            records=directional_scout(bridge,screenshots=shots,
                 output_dir=root/"scan",origin=(212,2360,56),timeout=0)
            self.assertEqual(len(records),8)
            self.assertEqual([yaw for _,yaw in bridge.poses],list(directions()))
            self.assertEqual(bridge.resets,1)
            self.assertTrue((root/"scan/directions.json").exists())
            self.assertTrue((root/"scan/08_yaw_315.jpg").exists())

    def test_invalid_origin_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);shots=root/"screens";shots.mkdir()
            with self.assertRaises(ValueError):
                directional_scout(Bridge(shots),screenshots=shots,
                    output_dir=root/"scan",origin=(float("nan"),0,0))
            self.assertFalse((root/"scan").exists())
