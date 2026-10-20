"""V7 camera-target planning and clean-game launch diagnostics."""
import argparse
import json
from pathlib import Path
from .ioquake3_v4_production import load_production
from .ioquake3_v7_cinematic import target_track,export_production,launch_arguments

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V7 shot framing")
    p.add_argument("production",type=Path)
    p.add_argument("--target",nargs=3,metavar=("X","Y","Z"),type=float,
                   help="Aim camera shots at this world-space subject point")
    p.add_argument("--fov",type=float)
    p.add_argument("--out",type=Path,help="Output JSON shot plan (no overwrite)")
    p.add_argument("--launch-flags",action="store_true",help="Print clean cinematic mode engine flags")
    args=p.parse_args(argv)
    if args.out is not None and args.target is None:
        p.error("--out requires --target")
    film=load_production(args.production)
    if args.target is not None:
        film=target_track(film,args.target,fov=args.fov)
    output=str(export_production(film,args.out)) if args.out else None
    print(json.dumps({"name":film.name,"shots":len(film.shots),
                      "frame_target":args.target,"generated":output,
                      "occlusion_verified":False,
                      "launch_flags":launch_arguments() if args.launch_flags else None},indent=2))

if __name__=="__main__":
    main()
