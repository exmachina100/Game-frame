"""Send one detached rendering camera pose through the experimental V2 client."""
import argparse
import json
from pathlib import Path
from .ioquake3_render_camera import IoQuake3RenderCamera

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V2: independent renderer pose")
    p.add_argument("--dir",required=True,type=Path)
    p.add_argument("--position",nargs=3,type=float,metavar=("X","Y","Z"))
    p.add_argument("--pitch",type=float,default=0)
    p.add_argument("--yaw",type=float,default=0)
    p.add_argument("--roll",type=float,default=0)
    p.add_argument("--fov",type=float,default=85)
    p.add_argument("--reset",action="store_true",help="Restore standard gameplay camera")
    args=p.parse_args(argv)
    if not args.reset and args.position is None:
        p.error("--position required unless --reset")
    client=IoQuake3RenderCamera(args.dir)
    result=client.reset() if args.reset else client.set_pose(args.position,pitch=args.pitch,
             yaw=args.yaw,roll=args.roll,fov=args.fov)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
