import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v7_scout import candidate_positions,scout

class FakeBridge:
    def __init__(self,folder):
        self.folder=folder
        self.reset_count=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        return {"queued":True}
    def capture(self,name):
        (self.folder/(name+".jpg")).write_bytes(b"jpeg")
        return {"queued":True}
    def reset(self):
        self.reset_count+=1

class ScoutTests(unittest.TestCase):
    def test_positions(self):
        positions=candidate_positions((212,2360,56),32)
        self.assertEqual(len(positions),6)
        self.assertEqual(positions[1][1],(212,2328,56))
    def test_record_scout(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);screen=root/"screens";screen.mkdir()
            bridge=FakeBridge(screen)
            result=scout(bridge,screenshots=screen,output_dir=root/"scout",
                origin=(212,2360,56),target=(300,2400,60),offset=32,timeout=0)
            self.assertEqual(len(result),6)
            self.assertEqual(bridge.reset_count,1)
            self.assertTrue((root/"scout/scout.json").is_file())
            self.assertTrue(all(x["file_verified"] and not x["occlusion_verified"] for x in result))
    def test_existing_directory_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);screen=root/"screens";screen.mkdir()
            with self.assertRaises(FileExistsError):
                scout(FakeBridge(screen),screenshots=screen,output_dir=root,
                      origin=(212,2360,56),target=(300,2400,60))
