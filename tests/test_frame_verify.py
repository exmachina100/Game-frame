import unittest
from gameframe.frame_verify import verify_step


class FakeBridge:
    def __init__(self, statuses):
        self.statuses = iter(statuses)
        self.actions = []

    def request(self, action):
        self.actions.append(action)
        if action == "status":
            return {"info": next(self.statuses)}
        return {"info": {}}


class FrameVerifyTests(unittest.TestCase):
    def test_exact_increment(self):
        b = FakeBridge([
            {"paused": True, "screen_frames": {":screen": 65}},
            {"paused": True, "screen_frames": {":screen": 66}, "completed_frames": 20},
        ])
        result = verify_step(b, timeout=.1)
        self.assertTrue(result.confirmed)
        self.assertEqual(result.screen_deltas, {":screen": 1})

    def test_multiple_frames_not_confirmed(self):
        b = FakeBridge([
            {"paused": True, "screen_frames": {":screen": 65}},
            {"paused": True, "screen_frames": {":screen": 67}},
        ])
        result = verify_step(b, timeout=.1)
        self.assertFalse(result.confirmed)
        self.assertEqual(result.screen_deltas[":screen"], 2)

    def test_empty_counter_never_confirmed(self):
        b = FakeBridge([{"paused": True, "screen_frames": []}] * 8)
        result = verify_step(b, timeout=.03, poll_seconds=.01)
        self.assertFalse(result.confirmed)


if __name__ == "__main__":
    unittest.main()
