"""Bounded real-time MAME runs measured by native screen frame counters.

This is observation, not deterministic frame stepping: elapsed frames can
overshoot a target because IPC polling and pause commands have latency.
"""
from dataclasses import dataclass
import time


def _frames(info):
    value = info.get("screen_frames")
    return value if isinstance(value, dict) else {}


@dataclass(frozen=True)
class RunResult:
    before: dict
    after: dict
    deltas: dict
    reached_target: bool
    paused: bool


def run_until_frames(bridge, target_frames: int, *, timeout: float = 8.0,
                     poll_seconds: float = 0.03) -> RunResult:
    if not isinstance(target_frames, int) or isinstance(target_frames, bool) or target_frames <= 0:
        raise ValueError("target_frames must be a positive integer")
    if timeout <= 0 or poll_seconds <= 0:
        raise ValueError("timeout and poll_seconds must be positive")
    bridge.request("pause")
    start = bridge.request("status")["info"]
    base = _frames(start)
    if not base:
        raise RuntimeError("No numeric screen frame counter available")
    if start.get("step_pending"):
        bridge.request("reset_step_tracking")
    latest = start
    bridge.request("resume")
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            latest = bridge.request("status")["info"]
            current = _frames(latest)
            deltas = {key: current[key] - value for key, value in base.items()
                      if key in current and isinstance(current[key], (float, int))}
            if deltas and all(delta >= target_frames for delta in deltas.values()):
                break
            time.sleep(poll_seconds)
    finally:
        # Never leave MAME running when polling errors or times out.
        bridge.request("pause")
    latest = bridge.request("status")["info"]
    current = _frames(latest)
    deltas = {key: current[key] - value for key, value in base.items()
              if key in current and isinstance(current[key], (float, int))}
    return RunResult(start, latest, deltas,
                     bool(deltas) and all(value >= target_frames for value in deltas.values()),
                     bool(latest.get("paused")))
