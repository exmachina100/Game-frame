"""V7.4 director: preflight every shot before any camera commands are queued.

Static BSP point traces only. Multi-shot plans are not camera-volume or
render-visibility verified. Orbit requires an explicit surveyed target.
"""
from __future__ import annotations
from dataclasses import dataclass
from .ioquake3_v7_motion import create_motion,preflight_motion
from .ioquake3_v3_takes import run_take

@dataclass(frozen=True)
class MotionShot:
    take: object
    kind: str

def reference_plan(*,include_crane=False,orbit_target=None,orbit_degrees=15):
    origin=(212,2360,56)
    shots=[
        MotionShot(create_motion("dolly",name="verified_dolly",origin=origin,
            end=(212,2380,56),duration=4,yaw=315),"dolly")
    ]
    if include_crane:
        shots.append(MotionShot(create_motion("crane",name="experimental_crane",
            origin=origin,end=(212,2360,76),duration=4,yaw=315),"crane"))
    if orbit_target is not None:
        shots.append(MotionShot(create_motion("orbit",name="experimental_orbit",
            origin=origin,target=orbit_target,degrees=orbit_degrees,duration=4),"orbit"))
    return tuple(shots)

def preflight_plan(shots,trace_bridge,*,rate=8,spacing=8):
    if not 1<=len(shots)<=8:raise ValueError("Plan must have 1-8 shots")
    results=[]
    for index,shot in enumerate(shots):
        verification=preflight_motion(shot.take,trace_bridge,rate=rate,spacing=spacing)
        results.append({"shot":shot.take.name,"kind":shot.kind,"preflight":verification})
        if not verification["static_world_clear"]:
            raise RuntimeError("Director REJECTED at shot %d (%s): static BSP path blocked; no playback started"%
                               (index+1,shot.take.name))
    return results

def run_plan(shots,trace_bridge,camera_bridge=None,*,rate=8,spacing=8,live=False):
    # ALL shots are cleared BEFORE the first camera command. Fail closed.
    checked=preflight_plan(shots,trace_bridge,rate=rate,spacing=spacing)
    if live and camera_bridge is None:raise ValueError("Live mode requires camera bridge")
    playback=[]
    try:
        for shot in shots:
            result=run_take(shot.take,camera_bridge,rate=rate,live=live,
                            allow_translation=True,reset_after=False)
            playback.append({"shot":shot.take.name,"queued":result["queued_count"],
                "samples":result["sample_count"]})
    finally:
        if live:
            try:camera_bridge.reset()
            except Exception:pass
    return {"static_world_preflight_passed":True,"mode":"live" if live else "dry_run",
            "shots":checked,"playback":playback,"render_readback_verified":False,
            "camera_volume_checked":False,"dynamic_entities_checked":False}
