import tempfile
import threading
import time
import unittest
from pathlib import Path
from gameframe.ioquake3_v2_source_patch import patch_client,patch_cgame,V2_CGAME_MARKER
from gameframe.ioquake3_source_patch import patch_source
from gameframe.ioquake3_render_camera import IoQuake3RenderCamera

class RenderCameraTests(unittest.TestCase):
    def test_patches_requires_v1(self):
        with self.assertRaises(ValueError):
            patch_client("void CL_Frame ( int msec ) {}")
        c=patch_client(patch_source("void CL_Frame ( int msec ) {}"))
        self.assertIn("gfview",c)
        with self.assertRaises(ValueError):
            patch_client(c)

    def test_cgame_render_hook(self):
        source="static int CG_CalcViewValues( void ) {return 0;}\n\tinwater = CG_CalcViewValues();"
        patched=patch_cgame(source)
        self.assertIn(V2_CGAME_MARKER,patched)
        self.assertIn("GF_CinematicView();",patched)
        with self.assertRaises(ValueError):
            patch_cgame(patched)

    def test_transport_roundtrip(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            def engine():
                rq=folder/"camera_request.txt"
                deadline=time.monotonic()+2
                while not rq.exists() and time.monotonic()<deadline:
                    time.sleep(.01)
                if rq.exists():
                    self.assertEqual(rq.read_text().strip(),"gfview 212.000 2360.000 56.000 15.000 90.000 5.000 80.000")
                    rq.unlink()
                    (folder/"camera_response.txt").write_text("QUEUED\n")
            thread=threading.Thread(target=engine)
            thread.start()
            try:
                result=IoQuake3RenderCamera(folder,2).set_pose([212,2360,56],pitch=15,yaw=90,roll=5,fov=80)
                self.assertTrue(result["queued"])
                self.assertFalse(result["render_verified"])
            finally:
                thread.join(timeout=2)

    def test_rejects_unsafe_values(self):
        with tempfile.TemporaryDirectory() as dir:
            camera=IoQuake3RenderCamera(dir)
            with self.assertRaises(ValueError):
                camera.set_pose([0,0,0],pitch=91)
            with self.assertRaises(ValueError):
                camera.set_pose([0,0,float("nan")])
            with self.assertRaises(ValueError):
                camera.set_pose([0,0,0],fov=10)
            with self.assertRaises(ValueError):
                camera.set_pose([0,0,0],roll=181)
