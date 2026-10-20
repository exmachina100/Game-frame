import tempfile
import unittest
from pathlib import Path
from gameframe.ioquake3_v3_takes import Pose,Take
from gameframe.ioquake3_v4_production import Production
from gameframe.ioquake3_v6_video import record_film,encode_mp4

class FakeBridge:
    def __init__(self,folder):
        self.folder=folder
        self.poses=[]
        self.reset_calls=0
    def set_pose(self,position,*,pitch,yaw,roll,fov):
        self.poses.append((position,pitch,yaw,roll,fov))
        return {"queued":True}
    def capture(self,name):
        (self.folder/(name+".jpg")).write_bytes(b"test-jpeg")
        return {"queued":True}
    def reset(self):
        self.reset_calls+=1
        return {"queued":True}

def sample_film():
    keys=(Pose(0,(212,2360,56),0,0,0,85),Pose(1,(212,2360,56),0,45,0,55))
    return Production("test_film",(Take("shot_a",keys),Take("shot_b",keys)))

class V6Tests(unittest.TestCase):
    def test_frames_are_sequential_across_cuts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); screen=root/"screens";screen.mkdir()
            bridge=FakeBridge(screen)
            result=record_film(sample_film(),bridge,screenshots=screen,
                    output_dir=root/"take",fps=2,encode=False,
                    clock=lambda:0,sleep=lambda _:None,capture_timeout=0)
            self.assertEqual(result["status"],"frames_captured")
            self.assertEqual(len(result["frames"]),4)
            self.assertEqual(len(bridge.poses),4)
            self.assertEqual(bridge.reset_calls,1)
            self.assertEqual([p.name for p in (root/"take/frames").iterdir()],
                    ["frame_000000.jpg","frame_000001.jpg","frame_000002.jpg","frame_000003.jpg"])
            self.assertTrue((root/"take/manifest.json").exists())
            with self.assertRaises(FileExistsError):
                record_film(sample_film(),bridge,screenshots=screen,
                    output_dir=root/"take",fps=2,encode=False)

    def test_encoder_rejects_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"frame_000000.jpg").write_bytes(b"abc")
            (folder/"frame_000002.jpg").write_bytes(b"abc")
            with self.assertRaises(ValueError):
                encode_mp4(folder,folder/"film.mp4",8)

    def test_encoding_uses_explicit_frame_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"frame_000000.jpg").write_bytes(b"abc")
            def runner(command,check):
                self.assertIn("libx264",command)
                self.assertEqual(command[command.index("-framerate")+1],"8")
                Path(command[-1]).write_bytes(b"mp4")
            video=encode_mp4(folder,folder/"film.mp4",8,runner=runner)
            self.assertTrue(video["verified"])

    def test_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); screen=root/"screens";screen.mkdir()
            with self.assertRaises(ValueError):
                record_film(sample_film(),FakeBridge(screen),screenshots=screen,
                            output_dir=root/"take",fps=30)
