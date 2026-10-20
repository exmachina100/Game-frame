import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_camera_test import camera_test_script, save_script


class IoQuake3CameraSmokeTests(unittest.TestCase):
    def test_cfg_contains_manual_camera_and_capture_commands(self):
        script = camera_test_script(map_name="q3dm2", prefix="take_01")
        self.assertIn("devmap q3dm2", script)
        self.assertIn("noclip", script)
        self.assertIn("screenshotJPEG take_01", script)
        self.assertIn("record take_01", script)
        self.assertIn("stoprecord", script)

    def test_disallows_console_or_path_injection(self):
        for bad in ("q3dm1;quit", "../../secret", "one two", "map\nquit"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    camera_test_script(map_name=bad)
                with self.assertRaises(ValueError):
                    camera_test_script(prefix=bad)

    def test_writes_to_requested_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = save_script(Path(tmp) / "baseq3", camera_test_script())
            self.assertEqual(target.name, "gameframe_camera_test.cfg")
            self.assertTrue(target.is_file())
            self.assertIn("devmap q3dm1", target.read_text(encoding="utf-8"))
