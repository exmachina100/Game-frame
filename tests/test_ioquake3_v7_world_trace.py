import unittest
from gameframe.ioquake3_v7_world_trace import inspect_path
from gameframe.ioquake3_v7_world_trace_patch import patch_source
from gameframe.ioquake3_source_patch import patch_source as v1patch
from gameframe.ioquake3_v4_source_patch import patch_source as v4patch

class FakeTrace:
    def __init__(self,blocked=False):
        self.calls=0;self.blocked=blocked
    def trace(self,a,b):
        self.calls+=1
        bad=self.blocked and self.calls==2
        return {"clear":not bad,"fraction":0.4 if bad else 1,
                "startsolid":False,"allsolid":False,"world_static_only":True}

class WorldTraceTests(unittest.TestCase):
    def test_split_segments(self):
        fake=FakeTrace()
        result=inspect_path(fake,[(0,0,0),(40,0,0)],max_spacing=16)
        self.assertTrue(result["static_world_clear"])
        self.assertEqual(result["checked_segments"],3)
        self.assertFalse(result["dynamic_entities_checked"])

    def test_blocks_early(self):
        fake=FakeTrace(blocked=True)
        result=inspect_path(fake,[(0,0,0),(40,0,0)])
        self.assertFalse(result["static_world_clear"])
        self.assertEqual(fake.calls,2)

    def test_v7_patch_requires_v4_and_rejects_duplicates(self):
        source=v4patch(v1patch("void CL_Frame ( int msec ) {}"))
        patched=patch_source(source)
        self.assertIn("CM_BoxTrace",patched)
        with self.assertRaises(ValueError):patch_source(patched)
