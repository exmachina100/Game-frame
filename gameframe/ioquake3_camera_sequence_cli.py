"""Run or preview a timed camera move on the patched ioquake3 client."""
import argparse
import json
from pathlib import Path
from .ioquake3_camera_bridge import IoQuake3CameraBridge
from .ioquake3_camera_sequence import load_sequence, run_sequence

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame timed ioquake3 camera move")
    p.add_argument("sequence",type=Path,help="Camera keyframes JSON")
    p.add_argument("--dir",type=Path,help="Existing private native camera bridge directory")
    p.add_argument("--rate",type=float,default=8,help="Commands per second, 1–15 (default 8)")
    p.add_argument("--run",action="store_true",help="Actually send commands; otherwise preview only")
    p.add_argument("--allow-translation",action="store_true",help="Opt-in to potentially clipping through geometry")
    p.add_argument("--linear",action="store_true",help="Disable smoothstep easing")
    args=p.parse_args(argv)
    if args.run and args.dir is None:
        p.error("--run requires --dir")
    keys=load_sequence(args.sequence)
    if args.run:
        bridge=IoQuake3CameraBridge(args.dir)
    else:
        bridge=None
    result=run_sequence(keys,bridge,rate=args.rate,dry_run=not args.run,
                        allow_translation=args.allow_translation,ease=not args.linear)
    print(json.dumps({"mode":"live" if args.run else "dry_run","samples":len(result),
                      "first":result[0],"last":result[-1],
                      "queued":sum(1 for item in result if item["queued"]),
                      "readback_verified":False},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
