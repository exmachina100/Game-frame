import unittest
from gameframe.ioquake3_v7_motion import create_motion,preflight_motion,run_checked_motion

class FakeTrace:
    def __init__(self,blocked=False):
        self.count=0;self.blocked=blocked
    def trace(self,a,b):
        self.count+=1
        return {"clear":not (self.blocked and self.count==2),"fraction":1,
                "startsolid":False,"allsolid":False}

class FakeCamera:
    def __init__(self):self.poses=[];self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append(position)
        return {"queued":True}
    def reset(self):
        self.resets+=1
        return {"queued":True}

class MotionTests(unittest.TestCase):
    def test_dolly(self):
        t=create_motion("dolly",origin=(212,2360,56),end=(212,2380,56),steps=8)
        self.assertEqual(t.keyframes[-1].position,(212.,2380.,56.))
        self.assertEqual(t.keyframes[0].yaw,315)
    def test_crane(self):
        t=create_motion("crane",origin=(212,2360,56),end=(212,2360,76))
        self.assertEqual(t.keyframes[-1].position[2],76)
    def test_orbit_looks_at_target(self):
        t=create_motion("orbit",origin=(100,0,10),target=(0,0,0),degrees=90)
        self.assertAlmostEqual(t.keyframes[-1].position[1],100)
        self.assertAlmostEqual(t.keyframes[-1].yaw,270)
    def test_blocked_prevents_camera_movement(self):
        t=create_motion("dolly",origin=(212,2360,56),end=(212,2380,56))
        camera=FakeCamera()
        with self.assertRaisesRegex(RuntimeError,"REJECTED"):
            run_checked_motion(t,FakeTrace(blocked=True),camera,rate=2,live=True)
        self.assertEqual(camera.poses,[])
    def test_valid_preflight_then_live(self):
        t=create_motion("dolly",origin=(212,2360,56),end=(212,2380,56),duration=1)
        camera=FakeCamera()
        result=run_checked_motion(t,FakeTrace(),camera,rate=2,live=True)
        self.assertTrue(result["preflight"]["static_world_clear"])
        self.assertEqual(len(camera.poses),3)
        self.assertEqual(camera.resets,1)
