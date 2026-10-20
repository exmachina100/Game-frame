import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep
import unittest
from gameframe.mame_bridge import MameBridge


class MameBridgeTests(unittest.TestCase):
    def test_rejects_unsafe_actions(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                MameBridge(Path(temp)).request("eval_lua")

    def test_round_trip(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            bridge = MameBridge(directory, timeout=2)
            def fake_mame():
                deadline = monotonic() + 1.5
                while monotonic() < deadline:
                    requests = list(directory.glob("request_*.json"))
                    if requests:
                        payload = json.loads(requests[0].read_text())
                        reply = {"id": payload["id"], "ok": True,
                                 "info": {"paused": True}}
                        (directory / f"response_{payload['id']}.json").write_text(json.dumps(reply))
                        return
                    sleep(.01)
                raise AssertionError("No request seen")
            t = Thread(target=fake_mame)
            t.start()
            response = bridge.request("pause")
            t.join()
            self.assertEqual(response["info"]["paused"], True)
            self.assertEqual(list(directory.glob("request_*.json")), [])

    def test_timeout(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(TimeoutError):
                MameBridge(Path(temp), timeout=.05).request("status")
