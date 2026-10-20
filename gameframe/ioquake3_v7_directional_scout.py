"""Directional V7 scout: eight camera yaw directions from one fixed origin.

Requires patched V4 gfcapture bridge. This produces visual evidence, not
raycast-backed proof of an unobstructed path. Keep Quake console closed.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import shutil
import uuid
from .ioquake3_v4_bridge import IoQuake3ProductionBridge
from .ioquake3_capture_verify import snapshot_screenshot_dir,wait_for_capture

def directions(step=45):
    if type(step) is not int or step not in (30,45,60,90):
        raise ValueError("Angular step must be 30, 45, 60 or 90 degrees")
    return tuple(range(0,360,step))

def directional_scout(bridge,*,screenshots,output_dir,origin,pitch=0,fov=85,step=45,timeout=3):
    if len(origin)!=3 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>=100000 for v in origin):
        raise ValueError("Origin must be three finite bounded coordinates")
    if type(pitch) not in (float,int) or not math.isfinite(pitch) or abs(pitch)>89:
        raise ValueError("Pitch outside -89 to 89")
    if type(fov) not in (float,int) or not math.isfinite(fov) or not 20<=fov<=130:
        raise ValueError("FOV outside 20 to 130")
    folder=Path(screenshots)
    if not folder.is_dir():raise ValueError("Screenshot directory does not exist")
    out=Path(output_dir)
    if out.exists():raise FileExistsError("Use a new scout output directory")
    yaws=directions(step)
    out.mkdir(parents=True)
    results=[]
    nonce=uuid.uuid4().hex[:10]
    try:
        for index,yaw in enumerate(yaws,1):
            ack=bridge.set_pose(origin,pitch=pitch,yaw=yaw,roll=0,fov=fov)
            if not ack["queued"]:raise RuntimeError("Camera pose not queued")
            token=f"gfdir_{nonce}_{index:02d}"
            before=snapshot_screenshot_dir(folder)
            captured=bridge.capture(token)
            if not captured["queued"]:raise RuntimeError("Screenshot not queued")
            source=wait_for_capture(folder,before,token,timeout=timeout)
            if source is None:raise TimeoutError(f"Missing screenshot at yaw {yaw}")
            dst=out/f"{index:02d}_yaw_{yaw:03d}.jpg"
            shutil.copyfile(source,dst)
            if dst.stat().st_size==0:raise ValueError("Screenshot is empty")
            results.append({"index":index,"yaw":yaw,"position":list(origin),"pitch":pitch,
                            "fov":fov,"file":str(dst),"file_verified":True,
                            "occlusion_verified":False})
    finally:
        try:bridge.reset()
        except Exception:pass
        (out/"directions.json").write_text(json.dumps({
            "schema":"gameframe.v7.directional_scout.v1",
            "origin":list(origin),"step_degrees":step,
            "human_review_required":True,"occlusion_verified":False,
            "directions":results},indent=2)+"\n",encoding="utf-8")
    return results

def main(argv=None):
    p=argparse.ArgumentParser(description="Capture a 360-degree directional camera scout")
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--screenshot-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--origin",nargs=3,type=float,required=True)
    p.add_argument("--pitch",type=float,default=0)
    p.add_argument("--fov",type=float,default=85)
    p.add_argument("--step",type=int,default=45)
    args=p.parse_args(argv)
    result=directional_scout(IoQuake3ProductionBridge(args.dir),
        screenshots=args.screenshot_dir,output_dir=args.output_dir,origin=args.origin,
        pitch=args.pitch,fov=args.fov,step=args.step)
    print(json.dumps({"images":len(result),"yaws":[v["yaw"] for v in result],
       "output_dir":str(args.output_dir),"occlusion_verified":False},indent=2))

if __name__=="__main__":
    main()
