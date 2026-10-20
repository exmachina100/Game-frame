import unittest
from gameframe.realtime import run_until_frames


class FakeBridge:
    def __init__(self):
        self.calls = []
        self.value = 0
        self.paused = True

    def request(self, action):
        self.calls.append(action)
        if action == "pause":
            self.paused = True
        if action == "resume":
            self.paused = False
        if action == "status" and not self.paused:
            self.value += 3
        return {"info": {"paused": self.paused, "screen_frames": {":screen": self.value}}}


class RealtimeTests(unittest.TestCase):
    def test_reaches_target_and_pauses(self):
        b = FakeBridge()
        result = run_until_frames(b, 5, timeout=.3, poll_seconds=.001)
        self.assertTrue(result.reached_target)
        self.assertTrue(result.paused)
        self.assertGreaterEqual(result.deltas[":screen"], 5)
        self.assertEqual(b.calls[-2:], ["pause", "status"])

    def test_rejects_bad_target(self):
        with self.assertRaises(ValueError):
            run_until_frames(FakeBridge(), 0)


if __name__ == "__main__":
    unittest.main()
