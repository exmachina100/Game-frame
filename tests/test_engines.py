import unittest
from gameframe.engines import Capabilities, ShotCommand, CinematicPlan, parse_plan, execute_plan
from gameframe.ioquake3 import IoQuake3Adapter

class FakeAdapter:
    def __init__(self):
        self.calls = []
    def capabilities(self):
        return Capabilities("fake3d",frozenset({"set_camera","capture_frame"}),True,True)
    def execute(self, operation, arguments):
        self.calls.append((operation,arguments))
        return {"acknowledged":True}

class EngineContractTests(unittest.TestCase):
    def setUp(self):
        self.plan = CinematicPlan("Alley scene",24,120,(
            ShotCommand(0,"set_camera",{"position":[0,1,3]}),
            ShotCommand(90,"capture_frame",{"name":"closeup"})))
    def test_round_trip(self):
        self.assertEqual(parse_plan(self.plan.serialize()),self.plan)
    def test_capability_negotiation(self):
        self.assertTrue(self.plan.validate_for(FakeAdapter().capabilities())["ready"])
        self.assertFalse(self.plan.validate_for(IoQuake3Adapter().capabilities())["ready"])
    def test_dry_run_is_nonexecuting(self):
        adapter=FakeAdapter()
        result=execute_plan(adapter,self.plan)
        self.assertFalse(result["executed"])
        self.assertEqual(adapter.calls,[])
    def test_explicit_execution(self):
        adapter=FakeAdapter()
        result=execute_plan(adapter,self.plan,dry_run=False)
        self.assertEqual(len(adapter.calls),2)
        self.assertTrue(result["executed"])
    def test_rejects_unsupported_capability(self):
        with self.assertRaisesRegex(ValueError,"does not support"):
            execute_plan(IoQuake3Adapter(),self.plan,dry_run=False)
    def test_rejects_invalid_timeline_and_nonfinite(self):
        with self.assertRaises(ValueError):
            CinematicPlan("a",24,10,(ShotCommand(10,"set_camera",{}),))
        with self.assertRaises(ValueError):
            ShotCommand(0,"set_camera",{"x":float("nan")})
        with self.assertRaises(ValueError):
            CinematicPlan("a",24,20,(ShotCommand(10,"set_camera",{}),ShotCommand(2,"capture_frame",{})))
    def test_executable_diagnostics(self):
        self.assertFalse(IoQuake3Adapter().diagnostics()["executable_found"])
        self.assertTrue(IoQuake3Adapter().capabilities().native_3d)
