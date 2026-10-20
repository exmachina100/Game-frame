"""Engine-independent cinematic capability negotiation and shot validation.

This layer never assumes a game exposes free camera, actor control or deterministic
frame stepping. Drivers explicitly advertise operations before any commands run.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol, Any
import math

OPERATIONS = frozenset({
    "load_scene", "spawn_actor", "move_actor", "set_camera",
    "capture_frame", "record_start", "record_stop", "advance_frames",
    "inspect_scene", "play_animation", "set_lighting",
})


@dataclass(frozen=True)
class Capabilities:
    engine: str
    operations: frozenset[str]
    frame_exact: bool = False
    native_3d: bool = False

    def __post_init__(self):
        if not self.engine or not isinstance(self.engine, str):
            raise ValueError("engine must be a nonempty string")
        if not isinstance(self.operations, frozenset) or not self.operations <= OPERATIONS:
            raise ValueError("Unsupported capability")
        if not isinstance(self.frame_exact, bool) or not isinstance(self.native_3d, bool):
            raise ValueError("Invalid capability flag")

    def describe(self) -> dict:
        return {**asdict(self), "operations": sorted(self.operations)}


class EngineAdapter(Protocol):
    def capabilities(self) -> Capabilities: ...
    def execute(self, operation: str, arguments: dict[str, Any]) -> dict: ...


@dataclass(frozen=True)
class ShotCommand:
    frame: int
    operation: str
    arguments: dict[str, Any]

    def __post_init__(self):
        if type(self.frame) is not int or self.frame < 0 or self.frame > 360000:
            raise ValueError("Frame must be a nonnegative integer within 360000")
        if self.operation not in OPERATIONS:
            raise ValueError("Unknown cinematic operation")
        if not isinstance(self.arguments, dict):
            raise ValueError("Arguments must be an object")
        for item in self.arguments.values():
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("Nonfinite shot parameter")


@dataclass(frozen=True)
class CinematicPlan:
    title: str
    fps: int
    duration_frames: int
    commands: tuple[ShotCommand, ...]

    def __post_init__(self):
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Title required")
        if type(self.fps) is not int or not 1 <= self.fps <= 240:
            raise ValueError("fps out of range")
        if type(self.duration_frames) is not int or not 1 <= self.duration_frames <= 360000:
            raise ValueError("Invalid duration")
        if not isinstance(self.commands, tuple):
            raise ValueError("commands must be a tuple")
        if any(not isinstance(c, ShotCommand) or c.frame >= self.duration_frames for c in self.commands):
            raise ValueError("Command outside timeline")
        if any(a.frame > b.frame for a,b in zip(self.commands,self.commands[1:])):
            raise ValueError("Commands must be ordered by frame")

    def validate_for(self, capability: Capabilities) -> dict:
        unsupported = sorted({cmd.operation for cmd in self.commands} - capability.operations)
        return {
            "engine": capability.engine,
            "ready": not unsupported,
            "unsupported": unsupported,
            "frame_exact": capability.frame_exact,
            "native_3d": capability.native_3d,
            "shots": len(self.commands),
        }

    def serialize(self) -> dict:
        return {"schema": "gameframe.cinematic.v1", "title": self.title, "fps": self.fps,
                "duration_frames": self.duration_frames,
                "commands": [asdict(c) for c in self.commands]}


def parse_plan(data: dict) -> CinematicPlan:
    if not isinstance(data, dict) or data.get("schema") != "gameframe.cinematic.v1":
        raise ValueError("Unrecognized cinematic plan schema")
    rows = data.get("commands")
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError("commands must contain at most 10000 entries")
    return CinematicPlan(
        title=data["title"], fps=data["fps"], duration_frames=data["duration_frames"],
        commands=tuple(ShotCommand(**row) for row in rows),
    )


def execute_plan(adapter: EngineAdapter, plan: CinematicPlan, *, dry_run: bool = True) -> dict:
    report = plan.validate_for(adapter.capabilities())
    if not report["ready"]:
        raise ValueError("Engine does not support: " + ", ".join(report["unsupported"]))
    if dry_run:
        return {**report, "executed": False, "planned": plan.serialize()}
    results = []
    for command in plan.commands:
        results.append({"frame": command.frame, "operation": command.operation,
                        "result": adapter.execute(command.operation, command.arguments)})
    return {**report, "executed": True, "results": results}
