"""Generate safe, inspectable Quake III console scripts for filmmaking smoke tests.

This is an offline console-script workflow, NOT native GameFrame camera RPC.
Commands run only after the user explicitly executes the generated cfg inside
a locally installed ioquake3. Never sends arbitrary console input to a process.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")
_SAFE_MAP = re.compile(r"^[a-zA-Z0-9_]{1,40}$")

def camera_test_script(*, map_name: str = "q3dm1", prefix: str = "gameframe_test") -> str:
    if not _SAFE_MAP.fullmatch(map_name) or not _SAFE_NAME.fullmatch(prefix):
        raise ValueError("Map and capture prefix must be alphanumeric without paths")
    return (
        "// GameFrame camera and native-capture smoke test — user-operated\n"
        "// Execute in ioquake3 console with: /exec gameframe_camera_test.cfg\n"
        "// Uses devmap (local cheats); does NOT provide remote camera control.\n"
        f"devmap {map_name}\n"
        "seta cg_draw2D 0\n"
        "seta cg_drawGun 0\n"
        "seta cg_fov 85\n"
        "bind F6 \"noclip\"\n"
        f"bind F7 \"screenshotJPEG {prefix}\"\n"
        f"bind F8 \"record {prefix}\"\n"
        "bind F9 \"stoprecord\"\n"
        "echo GAMEFRAME: local map loaded; F6 noclip, F7 screenshot, F8 record, F9 stop.\n"
        "echo GAMEFRAME: camera is still manually driven with keyboard/mouse.\n"
    )

def save_script(root: Path, content: str) -> Path:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    output = root / "gameframe_camera_test.cfg"
    output.write_text(content, encoding="utf-8", newline="\n")
    return output

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate manual ioquake3 cinematic camera smoke-test cfg")
    p.add_argument("--baseq3", type=Path, default=Path(r"D:\AI\Game Frame\ioquake3\baseq3"))
    p.add_argument("--map", default="q3dm1")
    p.add_argument("--prefix", default="gameframe_test")
    p.add_argument("--write", action="store_true", help="Write cfg to specified baseq3 folder")
    args = p.parse_args(argv)
    script = camera_test_script(map_name=args.map, prefix=args.prefix)
    if args.write:
        print("Wrote", save_script(args.baseq3, script))
    else:
        print(script)
        print("Dry run only. Use --write to save cfg explicitly.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
