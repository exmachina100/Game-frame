"""Compile camera-only GameFrame cinematic plans into manual ioquake3 cfg takes.

Experimental native Quake III 'setviewpos x y z yaw' console command. The
engine runs the cfg only after a person uses /exec in a local devmap session.
This does not supply timed execution, camera pitch/roll or RPC readback.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import math
from .engines import parse_plan


def camera_takes(plan) -> list[tuple[int, str]]:
    result = []
    for cmd in plan.commands:
        if cmd.operation != "set_camera":
            raise ValueError("Console pilot supports only set_camera; no scene or actor control yet")
        args = cmd.arguments
        if set(args) != {"position", "yaw"}:
            raise ValueError("set_camera requires exactly position:[x,y,z] and yaw:degrees")
        position = args["position"]
        yaw = args["yaw"]
        if not isinstance(position, list) or len(position) != 3:
            raise ValueError("position must have exactly 3 numbers")
        values = [*position, yaw]
        if any(type(value) not in (float, int) or not math.isfinite(value) or abs(value) > 100000 for value in values):
            raise ValueError("camera position/yaw must be finite bounded numbers")
        line = "setviewpos " + " ".join(f"{float(value):.3f}" for value in values)
        result.append((cmd.frame, line))
    if not result:
        raise ValueError("Plan has no camera takes")
    return result


def export_takes(plan, baseq3: Path, *, stem: str = "gameframe_take") -> list[Path]:
    if stem != "gameframe_take":
        raise ValueError("Only fixed output stem is permitted")
    takes = camera_takes(plan)
    destination = Path(baseq3).resolve()
    if not destination.is_dir():
        raise FileNotFoundError(f"Create ioquake3 home baseq3 directory first: {destination}")
    paths = []
    for i, (frame, command) in enumerate(takes, start=1):
        path = destination / f"{stem}_{i:02d}.cfg"
        path.write_text(
            "// Manually execute in an ioquake3 /devmap session; testing only.\n"
            f"// GameFrame planned frame {frame} (NOT scheduled in engine).\n"
            "// Requires server cheat permission. Not a free camera.\n"
            + command + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Export manual Quake III camera take commands")
    p.add_argument("plan", type=Path)
    p.add_argument("--baseq3", type=Path, default=Path(r"D:\AI\Game Frame\ioquake3\baseq3"))
    p.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    plan = parse_plan(json.loads(args.plan.read_text(encoding="utf-8")))
    takes = camera_takes(plan)
    for number, (frame, command) in enumerate(takes, start=1):
        print(f"Take {number} / planned frame {frame}: {command}")
    if args.write:
        for path in export_takes(plan, args.baseq3):
            print("Wrote", path)
    else:
        print("Preview only; use --write to export cfg takes")
    print("WARNING: Timing, pitch, roll and readback require native engine bridge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
