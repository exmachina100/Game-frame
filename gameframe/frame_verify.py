"""Read-only MAME frame-step verification and sequencing helpers."""
from dataclasses import dataclass
import time


@dataclass
class StepResult:
    before: dict
    after: dict
    screen_deltas: dict[str, int]
    paused: bool

    @property
    def confirmed(self) -> bool:
        return bool(self.screen_deltas) and all(n == 1 for n in self.screen_deltas.values()) and self.paused


def _screens(payload: dict) -> dict[str, int]:
    raw = payload.get("screen_frames") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if isinstance(v, int) and not isinstance(v, bool)}


def verify_step(bridge, timeout: float = 3.0, poll_seconds: float = 0.02) -> StepResult:
    """Request a step and verify a single increment per exposed screen.

    Does not claim deterministic emulation if there are no readable screen frames.
    Never uses callback count as a proxy for a screen-frame number.
    """
    if timeout <= 0 or poll_seconds <= 0:
        raise ValueError("timeout and poll_seconds must be positive")
    bridge.request("pause")
    before = bridge.request("status")["info"]
    start = _screens(before)
    bridge.request("step_once")
    deadline = time.monotonic() + timeout
    last = before
    while time.monotonic() < deadline:
        last = bridge.request("status")["info"]
        current = _screens(last)
        deltas = {k: current[k] - v for k, v in start.items() if k in current}
        if last.get("paused") and start and any(d != 0 for d in deltas.values()) and not last.get("step_pending", False):
            return StepResult(before, last, deltas, True)
        time.sleep(poll_seconds)
    current = _screens(last)
    deltas = {k: current[k] - v for k, v in start.items() if k in current}
    return StepResult(before, last, deltas, bool(last.get("paused")))
