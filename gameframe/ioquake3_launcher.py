"""Safe launcher for a local, user-owned ioquake3 Windows installation.

The engine's own console script can stage a test map and capture a screenshot.
This is not an API for moving a free camera; that requires engine-side code.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess

DEFAULT_EXE = Path(r"D:\AI\Game Frame\ioquake3\ioquake3.x86_64.exe")
DEFAULT_BASE = Path(r"D:\AI\Quake 3 Arena")
DEFAULT_HOME = Path(r"D:\AI\Game Frame\ioquake3")

def launch_arguments(executable: Path, basepath: Path, homepath: Path,
                     *, fullscreen: bool = False) -> list[str]:
    for path, label in ((executable, "engine executable"), (basepath, "game data directory")):
        if not path.exists():
            raise FileNotFoundError(f"Missing {label}: {path}")
    if executable.suffix.lower() != ".exe":
        raise ValueError("Expected Windows executable")
    if not (basepath / "baseq3" / "pak0.pk3").is_file():
        raise FileNotFoundError("No baseq3/pak0.pk3 in game data directory")
    if not homepath.is_dir():
        raise FileNotFoundError("ioquake3 home directory does not exist")
    return [str(executable), "+set", "fs_basepath", str(basepath),
            "+set", "fs_homepath", str(homepath), "+set", "r_fullscreen",
            "1" if fullscreen else "0"]

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="Inspect and launch ioquake3 from GameFrame")
    parser.add_argument("--exe",type=Path,default=DEFAULT_EXE)
    parser.add_argument("--basepath",type=Path,default=DEFAULT_BASE)
    parser.add_argument("--homepath",type=Path,default=DEFAULT_HOME)
    parser.add_argument("--launch",action="store_true",help="Actually launch engine (otherwise dry run)")
    parser.add_argument("--fullscreen",action="store_true")
    args=parser.parse_args(argv)
    command=launch_arguments(args.exe,args.basepath,args.homepath,fullscreen=args.fullscreen)
    print(json.dumps({"executable":str(args.exe),"game_assets_found":True,
                      "command":command,"launch":args.launch,
                      "cinematic_bridge":"not_implemented"},indent=2))
    if args.launch:
        subprocess.Popen(command, cwd=args.exe.parent)
        print("Engine process launched; this is not a verified GameFrame runtime connection.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
