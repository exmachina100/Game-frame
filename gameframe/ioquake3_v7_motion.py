"""V7.3 camera motion: reusable dolly/crane/orbit and mandatory static BSP preflight.

Point traces check static world only. No volume, dynamic entity, or visibility guarantees.
Run through the existing V2 render camera AFTER the entire timeline is preflighted.
"""
from __future__ import annotations
import math
from .ioquake3_v3_takes import Pose,Take,sample,run_take
from .ioquake3_v7_world_trace import inspect_path
from .ioquake3_v7_cinematic import aim_at

def _xyz(v):
    if len(v)!=3 or any(type(n) not in (int,float) or not math.isfinite(n) or abs(n)>=100000 for n in v):
        raise ValueError("Coordinates must contain three finite bounded numbers")
    return tuple(float(x) for x in v)

def create_motion(kind,*,origin,end=None,target=None,radius=None,degrees=45,
                  duration=4,fov=85,yaw=315,pitch=0,steps=16,name=None):
    if kind not in ("dolly","crane","orbit"):raise ValueError("Unknown motion type")
    origin=_xyz(origin)
    if type(duration) not in (int,float) or not math.isfinite(duration) or not 0<duration<=30:
        raise ValueError("Duration must be within 0-30 seconds")
    if type(steps) is not int or not 2<=steps<=64:
        raise ValueError("Keyframe steps must be 2-64")
    if not 20<=fov<=130:raise ValueError("FOV must be 20-130")
    if kind in ("dolly","crane"):
        if end is None:raise ValueError("Dolly and crane require end XYZ")
        end=_xyz(end)
        if math.dist(origin,end)>256:raise ValueError("Maximum camera travel is 256 units")
        if kind=="crane" and end[2]==origin[2]:
            raise ValueError("Crane requires Z change")
    else:
        if target is None:raise ValueError("Orbit requires target XYZ")
        target=_xyz(target)
        if radius is None:radius=math.dist(origin[:2],target[:2])
        if not (8<=radius<=256) or not math.isfinite(radius):
            raise ValueError("Orbit radius must be 8-256")
        if not type(degrees) in (float,int) or not math.isfinite(degrees) or abs(degrees)>180:
            raise ValueError("Orbit arc must be <=180 degrees")
        angle=math.atan2(origin[1]-target[1],origin[0]-target[0])
    keys=[]
    for i in range(steps+1):
        t=i/steps
        if kind=="orbit":
            a=angle+math.radians(degrees)*t
            pos=(target[0]+radius*math.cos(a),target[1]+radius*math.sin(a),origin[2])
            p,y=aim_at(pos,target)
        else:
            pos=tuple(a+(b-a)*t for a,b in zip(origin,end))
            if target is not None:p,y=aim_at(pos,_xyz(target))
            else:p,y=pitch,yaw
        if abs(p)>89:raise ValueError("Pitch out of bounds")
        keys.append(Pose(duration*t,pos,p,y,0,float(fov)))
    return Take(name or kind+"_shot",tuple(keys))

def preflight_motion(take,trace_bridge,*,rate=8,spacing=8):
    """Sample actual playback path and require each location plus intervening line clear."""
    if not 1<=rate<=15 or not 1<=spacing<=32:raise ValueError("Rate/spacing out of bounds")
    n=math.ceil(take.keyframes[-1].time*rate)
    positions=[sample(take,min(i/rate,take.keyframes[-1].time)).position for i in range(n+1)]
    # Explicit point traces also check starts/ends. Motion paths can have
    # clear line segments yet start inside a world brush.
    checks=0
    for i,pos in enumerate(positions):
        result=trace_bridge.trace(pos,pos)
        checks+=1
        if not result["clear"]:
            return {"static_world_clear":False,"checks":checks,"failed_sample":i,
                    "dynamic_entities_checked":False,"camera_volume_checked":False}
    # inspect_path supports at most 128 points, so preflight separately per
    # adjacent sample pair rather than silently skipping long takes.
    for i,(a,b) in enumerate(zip(positions,positions[1:])):
        result=inspect_path(trace_bridge,[a,b],max_spacing=spacing)
        checks+=result["checked_segments"]
        if not result["static_world_clear"]:
            return {"static_world_clear":False,"checks":checks,"failed_segment":i,
                    "dynamic_entities_checked":False,"camera_volume_checked":False}
    return {"static_world_clear":True,"checks":checks,"samples":len(positions),
            "dynamic_entities_checked":False,"camera_volume_checked":False}

def run_checked_motion(take,trace_bridge,camera_bridge,*,rate=8,spacing=8,live=False):
    verification=preflight_motion(take,trace_bridge,rate=rate,spacing=spacing)
    if not verification["static_world_clear"]:
        raise RuntimeError("Camera motion REJECTED: static BSP collision preflight failed")
    playback=run_take(take,camera_bridge,rate=rate,live=live,allow_translation=True)
    return {"preflight":verification,"playback":playback}
