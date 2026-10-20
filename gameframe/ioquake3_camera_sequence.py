"""Time-based camera-take sequencer for the verified ioquake3 local bridge.

Wall-clock stepping; no engine frame lock or camera pose readback. Safe default
holds xyz stationary and animates yaw only. A planned shot is not a verified
rendered frame or collision-tested camera.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

from .ioquake3_camera_bridge import IoQuake3CameraBridge

@dataclass(frozen=True)
class CameraKey:
    time: float
    position: tuple[float, float, float]
    yaw: float

def load_sequence(path: str | Path) -> tuple[CameraKey, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"keyframes"}:
        raise ValueError("Expected JSON object with keyframes only")
    frames = data["keyframes"]
    if not isinstance(frames, list) or not 2 <= len(frames) <= 64:
        raise ValueError("Provide between 2 and 64 camera keyframes")
    keys = []
    for row in frames:
        if not isinstance(row, dict) or set(row) != {"time", "position", "yaw"}:
            raise ValueError("Each keyframe requires exactly time, position, yaw")
        values = (row["time"], row["yaw"])
        pos = row["position"]
        if not isinstance(pos, list) or len(pos) != 3:
            raise ValueError("position must contain exactly three coordinates")
        numbers = (*values, *pos)
        if any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 100000 for n in numbers):
            raise ValueError("All camera numbers must be finite and bounded")
        if not 0 <= row["time"] <= 300:
            raise ValueError("Keyframe time outside 0–300 seconds")
        keys.append(CameraKey(float(row["time"]), tuple(map(float, pos)), float(row["yaw"])))
    if keys[0].time != 0 or any(a.time >= b.time for a, b in zip(keys, keys[1:])):
        raise ValueError("Keyframes must start at time 0 and increase strictly")
    return tuple(keys)

def interpolate(a: CameraKey, b: CameraKey, at: float, *, ease: bool = True) -> CameraKey:
    t = max(0.0, min(1.0, (at - a.time) / (b.time - a.time)))
    if ease:
        t = t * t * (3 - 2 * t)
    xyz = tuple(x + (y - x) * t for x, y in zip(a.position, b.position))
    # Smallest signed angular difference; avoid unintended full revolutions.
    delta = (b.yaw - a.yaw + 180) % 360 - 180
    return CameraKey(at, xyz, (a.yaw + delta * t) % 360)

def sample(keys: tuple[CameraKey, ...], seconds: float, *, ease: bool = True) -> CameraKey:
    if seconds <= 0:
        return keys[0]
    if seconds >= keys[-1].time:
        return keys[-1]
    for a, b in zip(keys, keys[1:]):
        if a.time <= seconds <= b.time:
            return interpolate(a, b, seconds, ease=ease)
    raise AssertionError("Unreachable timeline")

def run_sequence(
    keys: tuple[CameraKey, ...],
    bridge: IoQuake3CameraBridge,
    *,
    rate: float = 8,
    allow_translation: bool = False,
    dry_run: bool = True,
    ease: bool = True,
    sleep=time.sleep,
    clock=time.monotonic,
) -> list[dict]:
    if type(rate) not in (int, float) or not math.isfinite(rate) or not 1 <= rate <= 15:
        raise ValueError("Rate must be between 1 and 15 Hz (engine polls ~20 Hz)")
    origin = keys[0].position
    if not allow_translation and any(k.position != origin for k in keys):
        raise ValueError("Camera moves through the map; translation requires explicit --allow-translation and can clip geometry")
    # Cap to 300 s * 15 Hz = 4500 positions; avoid unbounded loops.
    tick_count = math.ceil(keys[-1].time * rate)
    start = clock()
    results = []
    for i in range(tick_count + 1):
        intended = min(i / rate, keys[-1].time)
        position = sample(keys, intended, ease=ease)
        if not dry_run:
            delay = start + intended - clock()
            if delay > 0:
                sleep(delay)
            result = bridge.set_view(*position.position, position.yaw)
            acknowledged = result["queued"]
        else:
            acknowledged = False
        results.append({"planned_seconds": round(intended, 4), "position": list(position.position),
                        "yaw": round(position.yaw, 4), "queued": acknowledged,
                        "visually_verified": False})
    return results
