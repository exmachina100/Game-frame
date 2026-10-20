import unittest
from gameframe.mcp_server import execute, TOOLS

class CinematicMcpTests(unittest.TestCase):
    def test_capability_discovery(self):
        result = execute("inspect_engine_capabilities",{"engine":"ioquake3"})
        self.assertTrue(result["capabilities"]["native_3d"])
        self.assertEqual(result["capabilities"]["operations"], [])
        self.assertEqual(result["diagnostics"]["connection"],"not_connected")

    def test_film_plan_reports_unavailable_camera(self):
        plan={"schema":"gameframe.cinematic.v1","title":"Short",
              "fps":24,"duration_frames":120,
              "commands":[{"frame":0,"operation":"set_camera",
                           "arguments":{"position":[0,2,3]}}]}
        status=execute("validate_cinematic_plan",{"engine":"ioquake3","plan":plan})
        self.assertFalse(status["ready"])
        self.assertEqual(status["unsupported"],["set_camera"])

    def test_tools_advertised(self):
        names={x["name"] for x in TOOLS}
        self.assertIn("inspect_engine_capabilities",names)
        self.assertIn("validate_cinematic_plan",names)

    def test_unknown_engine_rejected(self):
        with self.assertRaises(ValueError):
            execute("inspect_engine_capabilities",{"engine":"unspecified"})
