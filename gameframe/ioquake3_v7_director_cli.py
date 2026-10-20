"""V7.4 multi-shot director; all static BSP collision checks before playback."""
import argparse
import json
from pathlib import Path
from .ioquake3_render_camera import IoQuake3RenderCamera
from .ioquake3_v7_world_trace import IoQuake3WorldTrace
from .ioquake3_v7_director import reference_plan,run_plan

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame all-shot-preflighted director")
    p.add_argument("--dir",required=True)
    p.add_argument("--include-crane",action="store_true",
                   help="Experimental crane; static trace passed earlier but framing not visually confirmed")
    p.add_argument("--orbit-target",nargs=3,type=float,
                   help="Explicit surveyed world-coordinate target; NEVER inferred automatically")
    p.add_argument("--orbit-degrees",type=float,default=15)
    p.add_argument("--rate",type=int,default=8)
    p.add_argument("--spacing",type=float,default=8)
    p.add_argument("--run",action="store_true")
    p.add_argument("--report",type=Path)
    args=p.parse_args(argv)
    shots=reference_plan(include_crane=args.include_crane,
                         orbit_target=args.orbit_target,orbit_degrees=args.orbit_degrees)
    trace=IoQuake3WorldTrace(args.dir)
    camera=IoQuake3RenderCamera(args.dir) if args.run else None
    report=run_plan(shots,trace,camera,rate=args.rate,spacing=args.spacing,live=args.run)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    main()
