"""Experimental V2 6DOF render camera transport; does not move player physics."""
from __future__ import annotations
import math
import os
from pathlib import Path
import time

class IoQuake3RenderCamera:
    def __init__(self,directory: str | Path,timeout:float=3.0):
        self.directory=Path(directory).resolve()
        self.timeout=timeout
        if not self.directory.is_dir() or not 0 < timeout <= 30:
            raise ValueError("Existing directory and 0-30 s timeout required")

    def _send(self,command:str)->dict:
        request=self.directory/"camera_request.txt"
        reply=self.directory/"camera_response.txt"
        tmp=self.directory/"camera_request.tmp"
        if request.exists() or tmp.exists():
            raise RuntimeError("Previous camera request pending; do not run multiple controllers")
        reply.unlink(missing_ok=True)
        try:
            with tmp.open("x",encoding="ascii") as f:
                f.write(command+"\n")
            os.replace(tmp,request)
            stop=time.monotonic()+self.timeout
            while time.monotonic()<stop:
                if reply.exists():
                    status=reply.read_text(encoding="ascii").strip()
                    reply.unlink(missing_ok=True)
                    if status!="QUEUED":
                        raise RuntimeError(f"Native camera request not accepted: {status}")
                    return {"queued":True,"render_verified":False}
                time.sleep(.02)
            raise TimeoutError("V2 engine did not acknowledge command; verify new binary and active cgame DLL")
        finally:
            tmp.unlink(missing_ok=True)

    def set_pose(self,position,*,pitch=0.0,yaw=0.0,roll=0.0,fov=85.0)->dict:
        if not isinstance(position,(tuple,list)) or len(position)!=3:
            raise ValueError("position requires 3 coordinates")
        values=(*position,pitch,yaw,roll,fov)
        if any(type(n) not in (float,int) or not math.isfinite(n) for n in values):
            raise ValueError("All pose values must be finite numbers")
        x,y,z,p,ya,r,f=map(float,values)
        if any(abs(a)>=100000 for a in (x,y,z)) or abs(p)>89 or abs(ya)>36000 or abs(r)>180 or not 20<=f<=130:
            raise ValueError("Camera pose outside conservative bounds")
        ack=self._send("gfview "+" ".join(f"{v:.3f}" for v in values))
        return {**ack,"position":[x,y,z],"pitch":p,"yaw":ya,"roll":r,"fov":f}

    def reset(self)->dict:
        return self._send("gfreset")
