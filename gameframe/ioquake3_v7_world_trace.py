"""Readback for V7 native static BSP collision trace.

This uses the same single-controller file queue as the V2 camera bridge,
but reads 'TRACE fraction startsolid allsolid' rather than 'QUEUED'.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import time
from .ioquake3_render_camera import IoQuake3RenderCamera

class IoQuake3WorldTrace(IoQuake3RenderCamera):
    def trace(self,start,end):
        if any(not isinstance(v,(tuple,list)) or len(v)!=3 for v in (start,end)):
            raise ValueError("Trace endpoints require three coordinates each")
        values=(*start,*end)
        if any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>=100000 for v in values):
            raise ValueError("Trace coordinates outside bounds")
        folder=self.directory
        request=folder/"camera_request.txt"
        tmp=folder/"camera_request.tmp"
        response=folder/"camera_response.txt"
        if request.exists() or tmp.exists():
            raise RuntimeError("Previous camera request pending")
        response.unlink(missing_ok=True)
        try:
            with tmp.open("x",encoding="ascii") as f:
                f.write("gftrace "+" ".join(f"{v:.3f}" for v in values)+"\n")
            os.replace(tmp,request)
            deadline=time.monotonic()+self.timeout
            while time.monotonic()<deadline:
                if response.exists():
                    line=response.read_text(encoding="ascii").strip()
                    response.unlink(missing_ok=True)
                    fields=line.split()
                    if len(fields)!=4 or fields[0]!="TRACE":
                        raise RuntimeError(f"World trace command unavailable: {line}")
                    fraction=float(fields[1])
                    if not math.isfinite(fraction) or not 0<=fraction<=1 or fields[2] not in ("0","1") or fields[3] not in ("0","1"):
                        raise RuntimeError("Malformed native collision readback")
                    return {"fraction":fraction,"startsolid":fields[2]=="1",
                            "allsolid":fields[3]=="1","world_static_only":True,
                            "clear":fraction>=0.999999 and fields[2]=="0" and fields[3]=="0"}
                time.sleep(.02)
            raise TimeoutError("No V7 native collision response; check rebuilt client")
        finally:
            tmp.unlink(missing_ok=True)

def inspect_path(bridge,points,*,max_spacing=16):
    if not 1<=len(points)<=128:raise ValueError("Need 1-128 waypoints")
    segments=[]
    for a,b in zip(points,points[1:]):
        dist=math.dist(a,b)
        count=max(1,math.ceil(dist/max_spacing))
        for i in range(count):
            start=tuple(x+(y-x)*i/count for x,y in zip(a,b))
            end=tuple(x+(y-x)*(i+1)/count for x,y in zip(a,b))
            segments.append(bridge.trace(start,end))
            if not segments[-1]["clear"]:
                return {"static_world_clear":False,"checked_segments":len(segments),
                        "first_blocked":segments[-1],"dynamic_entities_checked":False}
    if not segments:
        result=bridge.trace(points[0],points[0])
        segments.append(result)
    return {"static_world_clear":all(s["clear"] for s in segments),
            "checked_segments":len(segments),"dynamic_entities_checked":False}
