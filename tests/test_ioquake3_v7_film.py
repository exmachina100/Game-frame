import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from gameframe.ioquake3_v7_film import produce_checked_film

class Trace:
    def __init__(self,blocked=False):
        self.blocked=blocked
        self.count=0
    def trace(self,start,end):
        self.count+=1
        return {"clear":not(self.blocked and self.count==3),"fraction":1,
                "startsolid":False,"allsolid":False}

class FilmTests(unittest.TestCase):
    def test_blocked_preflight_never_enters_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"take"
            with patch("gameframe.ioquake3_v7_film.record_film") as recorder:
                with self.assertRaisesRegex(RuntimeError,"REJECTED"):
                    produce_checked_film(Trace(blocked=True),object(),
                        screenshots=folder,output_dir=out)
                recorder.assert_not_called()
                self.assertFalse(out.exists())

    def test_valid_preflight_passes_two_shots_to_v6(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/"take"
            def mock_record_film(*args, **kwargs):
                # The real V6 recorder creates its own fresh output directory.
                Path(kwargs["output_dir"]).mkdir()
                return {"status":"completed","frames":[],"shots":[],
                        "video":{"verified":True}}
            with patch("gameframe.ioquake3_v7_film.record_film",
                       side_effect=mock_record_film) as recorder:
                result=produce_checked_film(Trace(),object(),screenshots=folder,
                    output_dir=dest,encode=False)
                production=recorder.call_args.args[0]
                self.assertEqual(len(production.shots),2)
                self.assertTrue(recorder.call_args.kwargs["allow_translation"])
                self.assertEqual([s["duration_seconds"] for s in result["timeline"]],[4,4])
                self.assertTrue((dest/"manifest.json").is_file())

    def test_reject_existing_output_before_collision_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileExistsError):
                produce_checked_film(Trace(),object(),screenshots=folder,
                    output_dir=folder)
