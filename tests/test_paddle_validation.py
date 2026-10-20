import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from gameframe.mame_bridge import MameBridge


class PaddleValidationTests(unittest.TestCase):
    def test_invalid_paddle_and_range(self):
        with TemporaryDirectory() as temp:
            bridge = MameBridge(Path(temp))
            for args in ({"paddle": -1, "value": 100},
                         {"paddle": 2, "value": 100},
                         {"paddle": 0, "value": 256},
                         {"paddle": 1, "value": -1},
                         {"paddle": 0, "value": True},
                         {"paddle": "0", "value": 42}):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    bridge.request("set_paddle", **args)

    def test_no_unexpected_params(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                MameBridge(Path(temp)).request("status", value=2)
