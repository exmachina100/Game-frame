"""V7.3 camera motion generator with native static-world clearance gating."""
import argparse
import json
from pathlib import Path
from .ioquake3_render_camera import IoQuake3RenderCamera
from .ioquake3_v7_world_trace import IoQuake3WorldTrace
from .ioquake3_v7_motion import create_motion,run_checked_motion

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V7.3 collision-preflighted camera motions")
    p.add_argument("kind",choices=("dolly","crane","orbit"))
    p.add_argument("--dir",required=True,help="Active native V7 collision bridge folder")
    p.add_argument("--origin",nargs=3,type=float,required=True)
    p.add_argument("--end",nargs=3,type=float)
    p.add_argument("--target",nargs=3,type=float)
    p.add_argument("--radius",type=float)
    p.add_argument("--degrees",type=float,default=45)
    p.add_argument("--duration",type=float,default=4)
    p.add_argument("--yaw",type=float,default=315)
    p.add_argument("--pitch",type=float,default=0)
    p.add_argument("--fov",type=float,default=85)
    p.add_argument("--rate",type=int,default=8)
    p.add_argument("--spacing",type=float,default=8)
    p.add_argument("--run",action="store_true",help="Execute only after every static-world check passes")
    p.add_argument("--report",type=Path)
    a=p.parse_args(argv)
    shot=create_motion(a.kind,origin=a.origin,end=a.end,target=a.target,
        radius=a.radius,degrees=a.degrees,duration=a.duration,
        yaw=a.yaw,pitch=a.pitch,fov=a.fov)
    trace=IoQuake3WorldTrace(a.dir)
    camera=IoQuake3RenderCamera(a.dir) if a.run else None
    result=run_checked_motion(shot,trace,camera,rate=a.rate,spacing=a.spacing,live=a.run)
    output={"shot":shot.name,"motion":a.kind,"live":a.run,"preflight":result["preflight"],
            "queued":result["playback"]["queued_count"],
            "samples":result["playback"]["sample_count"],"pose_readback_verified":False}
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output,indent=2))

if __name__=="__main__":
    main()
