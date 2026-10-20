"""GameFrame V3: bounded renderer-only 6-axis shot planning and playback.

V3 uses gfview, *not* the V1 setviewpos player teleport. Wall-clock paced,
not frame-locked. Camera clearance and applied render state are unverified.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

from .ioquake3_render_camera import IoQuake3RenderCamera

@dataclass(frozen=True)
class Pose:
    time: float
    position: tuple[float, float, float]
    pitch: float
    yaw: float
    roll: float
    fov: float

@dataclass(frozen=True)
class Take:
    name: str
    keyframes: tuple[Pose, ...]

def load_take(path: str | Path) -> Take:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or set(data)!={"name","keyframes"}:
        raise ValueError("Take JSON must contain exactly name and keyframes")
    name=data["name"]
    if not isinstance(name,str) or not 1<=len(name)<=80 or not all(c.isalnum() or c in " _-" for c in name):
        raise ValueError("Take name must be a simple 1–80 character identifier")
    frames=data["keyframes"]
    if not isinstance(frames,list) or not 2<=len(frames)<=64:
        raise ValueError("Take needs 2–64 keyframes")
    poses=[]
    for frame in frames:
        if not isinstance(frame,dict) or set(frame)!={"time","position","pitch","yaw","roll","fov"}:
            raise ValueError("Each pose requires time, position, pitch, yaw, roll, fov")
        position=frame["position"]
        if not isinstance(position,list) or len(position)!=3:
            raise ValueError("position must have exactly three values")
        values=(frame["time"],*position,frame["pitch"],frame["yaw"],frame["roll"],frame["fov"])
        if any(type(x) not in (float,int) or not math.isfinite(x) for x in values):
            raise ValueError("Camera values must be finite numbers")
        t,x,y,z,pitch,yaw,roll,fov=map(float,values)
        if not 0<=t<=300 or any(abs(n)>=100000 for n in (x,y,z)) or abs(pitch)>89 or abs(yaw)>36000 or abs(roll)>180 or not 20<=fov<=130:
            raise ValueError("Pose outside V2 bridge limits")
        poses.append(Pose(t,(x,y,z),pitch,yaw,roll,fov))
    if poses[0].time!=0 or any(a.time>=b.time for a,b in zip(poses,poses[1:])):
        raise ValueError("Keyframe times must start at 0 and strictly increase")
    return Take(name,tuple(poses))

def _angle(a:float,b:float,t:float)->float:
    return a+((b-a+180)%360-180)*t

def interpolate(a:Pose,b:Pose,at:float,*,ease:bool=True)->Pose:
    t=max(0.,min(1.,(at-a.time)/(b.time-a.time)))
    if ease: t=t*t*(3-2*t)
    pos=tuple(x+(y-x)*t for x,y in zip(a.position,b.position))
    return Pose(at,pos,a.pitch+(b.pitch-a.pitch)*t,_angle(a.yaw,b.yaw,t),
                _angle(a.roll,b.roll,t),a.fov+(b.fov-a.fov)*t)

def sample(take:Take,at:float,*,ease:bool=True)->Pose:
    if at<=0: return take.keyframes[0]
    if at>=take.keyframes[-1].time: return take.keyframes[-1]
    for a,b in zip(take.keyframes,take.keyframes[1:]):
        if a.time<=at<=b.time: return interpolate(a,b,at,ease=ease)
    raise AssertionError("Time outside keyframes")

def run_take(take:Take,bridge:IoQuake3RenderCamera|None=None,*,rate:float=8,
             live:bool=False,allow_translation:bool=False,ease:bool=True,
             clock=time.monotonic,sleep=time.sleep)->dict:
    if type(rate) not in (int,float) or not math.isfinite(rate) or not 1<=rate<=15:
        raise ValueError("Rate must be between 1 and 15 Hz")
    if live and bridge is None:
        raise ValueError("Live playback requires a V2 render camera bridge")
    origin=take.keyframes[0].position
    if not allow_translation and any(p.position!=origin for p in take.keyframes):
        raise ValueError("Translation is not clearance-checked; require --allow-translation")
    duration=take.keyframes[-1].time
    samples=math.ceil(duration*rate)+1
    started=clock()
    records=[]
    try:
        for i in range(samples):
            at=min(i/rate,duration)
            pose=sample(take,at,ease=ease)
            if live:
                delay=started+at-clock()
                if delay>0: sleep(delay)
                result=bridge.set_pose(pose.position,pitch=pose.pitch,yaw=pose.yaw,roll=pose.roll,fov=pose.fov)
                queued=bool(result["queued"])
            else:
                queued=False
            records.append({"planned_seconds":round(at,4),"actual_elapsed_seconds":round(clock()-started,4) if live else None,
                            "position":list(pose.position),"pitch":pose.pitch,"yaw":pose.yaw,"roll":pose.roll,
                            "fov":pose.fov,"queued":queued})
        status="completed"
    except (Exception,KeyboardInterrupt):
        status="interrupted"
        raise
    finally:
        # Reset on interrupted playback as well as ordinary completion, but only
        # when this controller owns the active bridge and a live run was requested.
        if live and bridge is not None:
            try: bridge.reset()
            except Exception: pass
    return {"schema":"gameframe.v3.take_manifest.v1","name":take.name,"mode":"live" if live else "dry_run",
            "status":status,"rate_hz":rate,"planned_duration_seconds":duration,
            "sample_count":samples,"queued_count":sum(r["queued"] for r in records),
            "render_readback_verified":False,"frame_accurate":False,"samples":records}
