import unittest
from gameframe.ioquake3_v7_director import MotionShot,reference_plan,preflight_plan,run_plan
from gameframe.ioquake3_v7_motion import create_motion

class FakeTrace:
    def __init__(self,blocked_after=None):
        self.count=0;self.blocked_after=blocked_after
    def trace(self,a,b):
        self.count+=1
        return {"clear":self.count!=self.blocked_after,"fraction":1,
                "startsolid":False,"allsolid":False}

class FakeCamera:
    def __init__(self):self.poses=[];self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append(position)
        return {"queued":True}
    def reset(self):
        self.resets+=1
        return {"queued":True}

class DirectorTests(unittest.TestCase):
    def test_reference_plan_is_only_verified_dolly(self):
        plan=reference_plan()
        self.assertEqual(len(plan),1)
        self.assertEqual(plan[0].kind,"dolly")
    def test_two_shots_clear_before_live(self):
        plan=reference_plan(include_crane=True)
        camera=FakeCamera()
        report=run_plan(plan,FakeTrace(),camera,rate=2,live=True)
        self.assertTrue(report["static_world_preflight_passed"])
        self.assertEqual(len(report["playback"]),2)
        self.assertEqual(len(camera.poses),18)
        self.assertEqual(camera.resets,1)
    def test_second_shot_block_prevents_any_commands(self):
        plan=reference_plan(include_crane=True)
        camera=FakeCamera()
        with self.assertRaisesRegex(RuntimeError,"no playback started"):
            run_plan(plan,FakeTrace(blocked_after=20),camera,rate=2,live=True)
        self.assertEqual(camera.poses,[])
        self.assertEqual(camera.resets,0)
    def test_orbit_must_be_explicit(self):
        self.assertEqual(len(reference_plan()),1)
        self.assertEqual(len(reference_plan(orbit_target=(100,2300,56))),2)
