import unittest
from gameframe.core import Director
from gameframe.stage import RetroStage
from gameframe.mcp_server import handle


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.director = Director(RetroStage())

    def test_positions(self):
        d = self.director
        d.spawn_actor("actor", 0, 0)
        d.direct_actor("actor", 0, 10, 100, 0)
        self.assertEqual(d.actors_at(5)["actor"].x, 50)
        self.assertEqual(d.actors_at(10)["actor"].x, 100)

    def test_sequential_actions(self):
        d = self.director
        d.spawn_actor("actor", 0, 0)
        d.direct_actor("actor", 0, 10, 100, 0)
        d.direct_actor("actor", 10, 20, 100, 50)
        self.assertEqual(d.actors_at(15)["actor"].y, 25)

    def test_reject_overlap(self):
        d = self.director
        d.spawn_actor("actor", 0, 0)
        d.direct_actor("actor", 0, 10, 100, 0)
        with self.assertRaises(ValueError):
            d.direct_actor("actor", 5, 12, 10, 0)

    def test_frames_deterministic(self):
        d = self.director
        d.spawn_actor("actor", 3, 1)
        self.assertEqual(d.render_frame(3), d.render_frame(3))
        self.assertTrue(d.render_frame(3).startswith(b"P6\n320 180\n255\n"))

    def test_mcp_discovery(self):
        r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in r["result"]["tools"]}
        self.assertEqual(len(names), len(r["result"]["tools"]))
        self.assertTrue({"inspect_game", "list_scenes", "list_actors", "load_scene",
                         "spawn_actor", "direct_actor", "set_camera", "play_sequence",
                         "capture_sequence", "inspect_engine_capabilities",
                         "validate_cinematic_plan"} <= names)


if __name__ == "__main__":
    unittest.main()
