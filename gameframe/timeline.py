"""Native-MAME real-time shot timeline for validated Pong paddle actions.

This is a measured playback timeline, not frame-perfect control.
Actual frame counts are recorded for every beat.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
from .realtime import run_until_frames


@dataclass(frozen=True)
class Beat:
    label: str
    frames: int
    paddle0: int
    paddle1: int

    def __post_init__(self):
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Beat label must be nonempty")
        if type(self.frames) is not int or not 1 <= self.frames <= 10000:
            raise ValueError("frames must be an integer in 1..10000")
        for value in (self.paddle0, self.paddle1):
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError("Paddle value must be an integer in 0..255")


def play_timeline(bridge: Any, beats: list[Beat], *,
                  record: bool = False, manifest: str | Path | None = None) -> dict:
    """Run non-frame-exact Pong action beats and optionally record an AVI.

    Recording uses the configured MAME AVI output directory. A manifest is
    written even on failure so partial tests are diagnosable.
    """
    if not beats or not all(isinstance(b, Beat) for b in beats):
        raise ValueError("beats must be a nonempty list of Beat")
    report: dict = {"engine": "mame", "mode": "measured_realtime",
                    "system": "pong", "frame_exact": False,
                    "record_requested": record, "beats": [], "complete": False}
    recording_started = False
    cleanup_errors: list[str] = []
    try:
        bridge.request("pause")
        state = bridge.request("status")["info"]
        if state.get("system") != "pong":
            raise RuntimeError("Pong timeline must run against MAME pong")
        if record:
            recording_started = True  # attempt cleanup even if start response is lost
            bridge.request("record_start")
            report["record_start_acknowledged"] = True
        for beat in beats:
            # Actions are applied while paused; then measured runtime begins.
            bridge.request("pause")
            a = bridge.request("set_paddle", paddle=0, value=beat.paddle0)["info"]
            b = bridge.request("set_paddle", paddle=1, value=beat.paddle1)["info"]
            if not a.get("applied") or not b.get("applied"):
                raise RuntimeError("Paddle command was not accepted")
            result = run_until_frames(bridge, beat.frames)
            report["beats"].append({
                **asdict(beat),
                "actual_frames": result.deltas,
                "target_reached": result.reached_target,
                "paused_after": result.paused,
            })
            if not result.reached_target or not result.paused:
                raise RuntimeError("Realtime beat did not complete as requested")
        report["complete"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        try:
            bridge.request("pause")
        finally:
            if recording_started:
                try:
                    bridge.request("record_stop")
                except Exception as exc:
                    report["record_stop_error"] = str(exc)
            if manifest is not None:
                destination = Path(manifest)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


DEMO_BEATS = [
    Beat("opening symmetry", 24, 128, 128),
    Beat("split composition", 30, 32, 224),
    Beat("inverse composition", 30, 224, 32),
    Beat("return to center", 24, 128, 128),
]
