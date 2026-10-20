import tempfile
import threading
import time
import unittest
from pathlib import Path
from gameframe.ioquake3_source_patch import patch_source, MARKER
from gameframe.ioquake3_camera_bridge import IoQuake3CameraBridge

class CameraBridgeTests(unittest.TestCase):
    def test_source_patch_once(self):
        base="start\nvoid CL_Frame ( int msec ) {\nreturn;\n}\n"
        updated=patch_source(base)
        self.assertIn(MARKER,updated)
        self.assertIn("GF_CameraPoll();",updated)
        with self.assertRaises(ValueError):
            patch_source(updated)

    def test_roundtrip_simulated_patched_engine(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            def consumer():
                request=folder/"camera_request.txt"
                limit=time.monotonic()+2
                while not request.exists() and time.monotonic()<limit:
                    time.sleep(.01)
                if request.exists():
                    self.assertEqual(request.read_text().strip(),"setviewpos 212.000 2360.000 56.000 90.000")
                    request.unlink()
                    (folder/"camera_response.txt").write_text("QUEUED\n")
            thread=threading.Thread(target=consumer)
            thread.start()
            try:
                result=IoQuake3CameraBridge(folder,2).set_view(212,2360,56,90)
                self.assertTrue(result["queued"])
                self.assertFalse(result["verified"])
            finally:
                thread.join(timeout=2)

    def test_rejects_invalid_camera_request(self):
        with tempfile.TemporaryDirectory() as folder:
            b=IoQuake3CameraBridge(folder)
            for bad in (float("nan"),float("inf"),100001,"0;quit",True):
                with self.subTest(value=bad):
                    with self.assertRaises(ValueError):
                        b.set_view(bad,0,0,90)

    def test_unpatched_engine_times_out(self):
        with tempfile.TemporaryDirectory() as folder:
            b=IoQuake3CameraBridge(folder,.04)
            with self.assertRaises(TimeoutError):
                b.set_view(0,0,0,0)
            with self.assertRaisesRegex(RuntimeError,"pending"):
                b.set_view(0,0,0,0)
