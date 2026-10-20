import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_launcher import launch_arguments

class Ioquake3LaunchTests(unittest.TestCase):
    def test_installed_engine_and_game_content(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            exe=base/"engine"/"ioquake3.x86_64.exe"
            exe.parent.mkdir()
            exe.touch()
            (base/"game"/"baseq3").mkdir(parents=True)
            (base/"game"/"baseq3"/"pak0.pk3").touch()
            argv=launch_arguments(exe,base/"game",exe.parent)
            self.assertEqual(argv[0],str(exe))
            self.assertIn("fs_basepath",argv)
            self.assertIn("fs_homepath",argv)
            self.assertEqual(argv[-1],"0")
    def test_missing_game_data_stops_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            exe=base/"ioquake3.exe"
            exe.touch()
            with self.assertRaises(FileNotFoundError):
                launch_arguments(exe,base,base)
    def test_reject_non_executable_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            exe=base/"engine.txt"
            exe.touch()
            (base/"baseq3").mkdir()
            (base/"baseq3"/"pak0.pk3").touch()
            with self.assertRaises(ValueError):
                launch_arguments(exe,base,base)
