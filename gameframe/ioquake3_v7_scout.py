"""V7 visual scout: short, human-reviewed stills around a candidate camera.

Does not claim geometric clearance. Candidate camera points may be inside walls.
Requires live V4 patched ioquake3 screenshot bridge.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import shutil
import time
import uuid
from .ioquake3_v4_bridge import IoQuake3ProductionBridge
from .ioquake3_capture_verify import snapshot_screenshot_dir,wait_for_capture
from .ioquake3_v7_cinematic import aim_at

def candidate_positions(origin,offset):
    x,y,z=origin
    # Keep small, user-controlled offsets, not arbitrary map-wide jumps.
    return [("origin",(x,y,z)),("left",(x,y-offset,z)),
            ("right",(x,y+offset,z)),("back",(x-offset,y,z)),
            ("forward",(x+offset,y,z)),("up",(x,y,z+offset))]

def scout(bridge,*,screenshots,output_dir,origin,target,offset=32,fov=85,timeout=3):
    if type(offset) not in (int,float) or not math.isfinite(offset) or not 1<=offset<=128:
        raise ValueError("offset must be 1-128 map units")
    if not 20<=fov<=130:raise ValueError("fov must be 20-130")
    folder=Path(screenshots)
    if not folder.is_dir():raise ValueError("Screenshots directory does not exist")
    out=Path(output_dir)
    if out.exists():raise FileExistsError("Use a new scout output directory")
    candidates=candidate_positions(origin,offset)
    # Validate all candidate camera poses before sending commands.
    checked=[]
    for name,pos in candidates:
        pitch,yaw=aim_at(pos,target)
        if any(abs(a)>=100000 for a in pos):raise ValueError("Candidate outside safe command limits")
        checked.append((name,pos,pitch,yaw))
    out.mkdir(parents=True)
    results=[]
    nonce=uuid.uuid4().hex[:10]
    try:
        for i,(name,pos,pitch,yaw) in enumerate(checked,1):
            ack=bridge.set_pose(pos,pitch=pitch,yaw=yaw,roll=0,fov=fov)
            if not ack["queued"]:raise RuntimeError("Camera command not queued")
            token=f"gfsc_{nonce}_{i:02d}"
            before=snapshot_screenshot_dir(folder)
            capture=bridge.capture(token)
            if not capture["queued"]:raise RuntimeError("Screenshot command not queued")
            source=wait_for_capture(folder,before,token,timeout=timeout)
            if source is None:raise TimeoutError(f"Missing screenshot for {name}")
            filename=out/f"{i:02d}_{name}.jpg"
            shutil.copyfile(source,filename)
            if filename.stat().st_size==0:raise ValueError("Empty JPEG")
            results.append({"index":i,"name":name,"position":list(pos),
                            "pitch":pitch,"yaw":yaw,"file":str(filename),
                            "file_verified":True,"occlusion_verified":False})
    finally:
        try:bridge.reset()
        except Exception:pass
        (out/"scout.json").write_text(json.dumps({
            "schema":"gameframe.v7.scout.v1","origin":list(origin),"target":list(target),
            "offset":offset,"human_review_required":True,"candidates":results
        },indent=2)+"\n",encoding="utf-8")
    return results

def main(argv=None):
    p=argparse.ArgumentParser(description="Scout a 3D camera location using six short stills")
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--screenshot-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--origin",type=float,nargs=3,required=True)
    p.add_argument("--target",type=float,nargs=3,required=True)
    p.add_argument("--offset",type=float,default=32)
    p.add_argument("--fov",type=float,default=85)
    a=p.parse_args(argv)
    result=scout(IoQuake3ProductionBridge(a.dir),screenshots=a.screenshot_dir,
                 output_dir=a.output_dir,origin=a.origin,target=a.target,
                 offset=a.offset,fov=a.fov)
    print(json.dumps({"images":len(result),"output_dir":str(a.output_dir),
                      "occlusion_verified":False,"next":"Visually inspect six JPEGs before recording"},indent=2))

if __name__=="__main__":
    main()
