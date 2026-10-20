"""V7 cinematography utilities: Quake 3 target framing and clean-HUD setup.

Geometry visibility cannot be established from camera coordinates alone.
Quake pitch: positive points down, negative points up.
"""
from __future__ import annotations
from dataclasses import replace
import math
from pathlib import Path
import json
from .ioquake3_v3_takes import Pose,Take
from .ioquake3_v4_production import Production,load_production

def aim_at(position,target):
    if len(position)!=3 or len(target)!=3:
        raise ValueError("Position and target need three coordinates")
    numbers=(*position,*target)
    if any(type(n) not in (float,int) or not math.isfinite(n) for n in numbers):
        raise ValueError("Target and position must be finite")
    dx,dy,dz=(b-a for a,b in zip(position,target))
    flat=math.hypot(dx,dy)
    if flat<0.000001 and abs(dz)<0.000001:
        raise ValueError("Camera coincides with target")
    pitch=-math.degrees(math.atan2(dz,flat))
    if abs(pitch)>89:
        raise ValueError("Near-vertical target exceeds V2 camera limit")
    yaw=math.degrees(math.atan2(dy,dx))%360
    return pitch,yaw

def target_track(production,target,*,fov=None):
    """Re-aim every existing keyframe at a world-space target; retain XYZ.

    Does not raycast walls or automatically determine a visible subject.
    """
    result=[]
    for shot in production.shots:
        keys=[]
        for p in shot.keyframes:
            pitch,yaw=aim_at(p.position,target)
            keys.append(replace(p,pitch=pitch,yaw=yaw,
                                fov=p.fov if fov is None else fov))
        result.append(Take(shot.name,tuple(keys)))
    if fov is not None and not (20<=fov<=130):
        raise ValueError("FOV must be 20–130")
    return Production(production.name+"_tracked",tuple(result))

def export_production(production,path):
    data={"name":production.name,"shots":[{"name":shot.name,"keyframes":[
        {"time":k.time,"position":list(k.position),"pitch":k.pitch,
         "yaw":k.yaw,"roll":k.roll,"fov":k.fov} for k in shot.keyframes]}
        for shot in production.shots]}
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return path

# Launch-only cvars. No arbitrary engine console injection via camera bridge.
CINEMATIC_CVARS={
    "cg_draw2D":"0",           # suppress HUD (may also hide overlays)
    "cg_drawGun":"0",          # first-person weapon
    "cg_drawCrosshair":"0",
    "con_notifytime":"0",      # transient console text
}
def launch_arguments():
    result=[]
    for name,value in CINEMATIC_CVARS.items():
        result.extend(("+set",name,value))
    return result
