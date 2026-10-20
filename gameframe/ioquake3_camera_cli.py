"""Manual camera command request for a custom-built GameFrame ioquake3 client."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .ioquake3_camera_bridge import IoQuake3CameraBridge

def main(argv=None):
    p=argparse.ArgumentParser(description="Send camera position to a *patched* ioquake3 client")
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--position",type=float,nargs=3,required=True,metavar=("X","Y","Z"))
    p.add_argument("--yaw",type=float,required=True)
    args=p.parse_args(argv)
    result=IoQuake3CameraBridge(args.dir).set_view(*args.position,args.yaw)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
