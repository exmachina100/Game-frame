import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_capture_verify import (
    snapshot_screenshot_dir,find_new_files,match_capture_files,
    stage_verified_capture,wait_for_capture,
)
from gameframe.ioquake3_v4_production import Production,run_production
from gameframe.ioquake3_v3_takes import Pose,Take

class FakeBridge:
    def __init__(self,screen,skip=()):
        self.screen=screen
        self.skip=set(skip)
        self.resets=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        return {"queued":True}
    def capture(self,name):
        if name not in self.skip:
            (self.screen/(name+".jpg")).write_bytes(b"jpeg-data-"+name.encode())
        return {"queued":True}
    def reset(self):
        self.resets+=1
        return {"queued":True}

def film():
    keys=(Pose(0,(212,2360,56),0,0,0,85),Pose(1,(212,2360,56),0,20,0,85))
    return Production("capture_test",(Take("shot_a",keys),Take("shot_b",keys)))

class CaptureVerificationTests(unittest.TestCase):
    def test_new_file_detection_and_no_unrelated_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"old.jpg").write_bytes(b"before")
            before=snapshot_screenshot_dir(folder)
            (folder/"capture_test_shot_a.jpg").write_bytes(b"new")
            (folder/"unrelated.jpg").write_bytes(b"junk")
            new=find_new_files(before,folder)
            self.assertEqual(len(new),2)
            matches=match_capture_files(["capture_test_shot_a","capture_test_shot_b"],new)
            self.assertEqual(matches["capture_test_shot_a"].name,"capture_test_shot_a.jpg")
            self.assertIsNone(matches["capture_test_shot_b"])

    def test_staging_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); shot=folder/"camera.jpg";shot.write_bytes(b"jpeg")
            out=folder/"output"
            staged=stage_verified_capture(shot,out,1,"shot_a")
            self.assertEqual(staged.read_bytes(),b"jpeg")
            with self.assertRaises(FileExistsError):
                stage_verified_capture(shot,out,1,"shot_a")

    def test_capture_full_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);screen=root/"screens";screen.mkdir()
            bridge=FakeBridge(screen)
            result=run_production(film(),bridge,live=True,rate=1,capture=True,
                screenshot_dir=screen,output_dir=root/"production",
                clock=lambda:0,sleep=lambda _:None,capture_timeout=0)
            self.assertTrue(result["capture_files_verified"])
            self.assertEqual(bridge.resets,1)
            self.assertEqual(result["schema"],"gameframe.v5.production_manifest.v1")
            self.assertTrue((root/"production/01_shot_a.jpg").is_file())
            self.assertTrue((root/"production/02_shot_b.jpg").is_file())

    def test_partial_missing_does_not_fake_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);screen=root/"screens";screen.mkdir()
            bridge=FakeBridge(screen,skip={"capture_test_shot_b"})
            result=run_production(film(),bridge,live=True,rate=1,capture=True,
                screenshot_dir=screen,output_dir=root/"production",
                clock=lambda:0,sleep=lambda _:None,capture_timeout=0)
            self.assertFalse(result["capture_files_verified"])
            self.assertTrue(result["shots"][0]["captures"][0]["file_verified"])
            self.assertFalse(result["shots"][1]["captures"][0]["file_verified"])
            self.assertIsNone(result["shots"][1]["captures"][0]["output_file"])

    def test_no_accepting_stale_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); screen=root/"screens";screen.mkdir()
            (screen/"capture_test_shot_b.jpg").write_bytes(b"stale")
            before=snapshot_screenshot_dir(screen)
            self.assertIsNone(wait_for_capture(screen,before,"capture_test_shot_b",timeout=0))
