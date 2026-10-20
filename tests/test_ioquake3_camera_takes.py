import tempfile
import unittest
from pathlib import Path
from gameframe.engines import CinematicPlan, ShotCommand
from gameframe.ioquake3_camera_takes import camera_takes, export_takes

class CameraTakeTests(unittest.TestCase):
    def plan(self, commands):
        return CinematicPlan("test", 24, 240, tuple(commands))

    def test_camera_commands(self):
        plan = self.plan([ShotCommand(0,"set_camera",{"position":[100,200,40],"yaw":90}),
                          ShotCommand(72,"set_camera",{"position":[120,230,55],"yaw":180})])
        takes=camera_takes(plan)
        self.assertEqual(takes[0],(0,"setviewpos 100.000 200.000 40.000 90.000"))
        self.assertEqual(takes[1][0],72)
        with tempfile.TemporaryDirectory() as tmp:
            files=export_takes(plan,Path(tmp))
            self.assertEqual(len(files),2)
            self.assertIn("setviewpos",files[0].read_text())
            self.assertIn("NOT scheduled",files[1].read_text())

    def test_rejects_non_camera_control(self):
        plan=self.plan([ShotCommand(0,"spawn_actor",{"name":"x"})])
        with self.assertRaisesRegex(ValueError,"only set_camera"):
            camera_takes(plan)

    def test_rejects_extra_args_and_invalid_vectors(self):
        for args in ({"position":[0,1,2],"yaw":90,"command":"quit"},
                     {"position":[0,1],"yaw":90},
                     {"position":[0,1,float("inf")],"yaw":90},
                     {"position":[0,1,2],"yaw":"90;quit"}):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    camera_takes(self.plan([ShotCommand(0,"set_camera",args)]))
