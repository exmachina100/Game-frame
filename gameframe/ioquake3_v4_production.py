"""V4 multi-shot production timeline for the GameFrame V2 native camera.

Keeps capture evidence explicit: queued screenshot requests are not confirmed files.
Requires V4 source extension/rebuild for automated capture; otherwise run
--capture none and V3 camera commands work with the existing V2 build.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import re
from .ioquake3_v3_takes import Take,Pose,run_take

SAFE_NAME=re.compile(r"^[A-Za-z0-9_-]{1,48}$")

@dataclass(frozen=True)
class Production:
    name: str
    shots: tuple[Take,...]

def load_production(path):
    raw=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw,dict) or set(raw)!={"name","shots"} or not isinstance(raw["name"],str) or not SAFE_NAME.fullmatch(raw["name"]):
        raise ValueError("Production requires a safe name and shots")
    shots=raw["shots"]
    if not isinstance(shots,list) or not 1<=len(shots)<=16:
        raise ValueError("Use 1–16 shots")
    result=[]
    for row in shots:
        if not isinstance(row,dict) or set(row)!={"name","keyframes"} or not SAFE_NAME.fullmatch(str(row["name"])):
            raise ValueError("Shot name must be a safe identifier")
        frames=row["keyframes"]
        if not isinstance(frames,list) or not 2<=len(frames)<=64:
            raise ValueError("Each shot needs 2–64 keyframes")
        poses=[]
        for frame in frames:
            if not isinstance(frame,dict) or set(frame)!={"time","position","pitch","yaw","roll","fov"}:
                raise ValueError("Invalid camera keyframe")
            # Reuse V3's exact validation on one short, two-frame take.
            from .ioquake3_v3_takes import load_take
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                f=Path(tmp)/"frame.json"
                frame2={**frame,"time":frame["time"]+1}
                f.write_text(json.dumps({"name":"check","keyframes":[{**frame,"time":0}, {**frame2,"time":1}]}))
                checked=load_take(f)
            pose=checked.keyframes[0]
            poses.append(Pose(float(frame["time"]),pose.position,pose.pitch,pose.yaw,pose.roll,pose.fov))
        if poses[0].time!=0 or any(a.time>=b.time for a,b in zip(poses,poses[1:])) or poses[-1].time>300:
            raise ValueError("Shot timings must begin at zero and increase")
        result.append(Take(row["name"],tuple(poses)))
    if len({s.name for s in result})!=len(result):
        raise ValueError("Shot names must be unique")
    return Production(raw["name"],tuple(result))

def run_production(production,bridge=None,*,live=False,rate=8,allow_translation=False,capture=False,clock=None,sleep=None):
    if live and bridge is None: raise ValueError("Live mode requires bridge")
    if capture and (not live or not hasattr(bridge,"capture")):
        raise ValueError("Automated capture requires V4 patched bridge in live mode")
    # Validate all movements before the first live command.
    for shot in production.shots:
        if not allow_translation and any(k.position!=shot.keyframes[0].position for k in shot.keyframes):
            raise ValueError("Shot translation requires explicit opt-in")
    manifests=[]
    status="completed"
    try:
        for shot in production.shots:
            kw={"rate":rate,"live":live,"allow_translation":allow_translation}
            if clock is not None: kw["clock"]=clock
            if sleep is not None: kw["sleep"]=sleep
            manifest=run_take(shot,bridge,**kw)
            entry={"name":shot.name,"camera":manifest,"captures":[]}
            if capture:
                ack=bridge.capture(production.name+"_"+shot.name)
                entry["captures"].append({"requested_name":production.name+"_"+shot.name,
                    "queued":ack["queued"],"file_verified":False})
            manifests.append(entry)
    except BaseException:
        status="failed_or_interrupted"
        raise
    return {"schema":"gameframe.v4.production.v1","name":production.name,"status":status,
            "mode":"live" if live else "dry_run","shots":manifests,
            "frame_accurate":False,"capture_files_verified":False}
