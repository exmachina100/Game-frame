"""Stage 2 read-only entity snapshot readback. No actor mutation or inferred identity."""
from __future__ import annotations
import math
import os
from pathlib import Path
import time

def parse_scene(payload):
    lines=payload.strip().splitlines()
    if lines==["UNAVAILABLE"]:
        return {"available":False,"entities":[],"server_time_ms":None}
    if not lines:raise ValueError("Empty engine scene response")
    header=lines[0].split()
    if len(header)!=3 or header[0]!="SCENE":raise ValueError("Invalid snapshot header")
    try:
        time_ms,count=int(header[1]),int(header[2])
    except ValueError as exc:raise ValueError("Bad snapshot header numbers") from exc
    if time_ms<0 or count<0 or count>256 or len(lines)!=count+1:
        raise ValueError("Invalid snapshot entity count")
    entities=[]
    for line in lines[1:]:
        parts=line.split()
        if len(parts)!=9 or parts[0]!="E":raise ValueError("Malformed snapshot entity")
        try:
            eid,kind=int(parts[1]),int(parts[2])
            pos=[float(p) for p in parts[3:6]]
            legs,torso,frame=map(int,parts[6:])
        except ValueError as exc:raise ValueError("Invalid snapshot entity fields") from exc
        if not 0<=eid<2048 or not 0<=kind<1024 or any(not math.isfinite(p) or abs(p)>100000 for p in pos):
            raise ValueError("Snapshot entity outside bounds")
        entities.append({"number":eid,"etype":kind,"trajectory_base":pos,
                         "legs_animation":legs,"torso_animation":torso,"frame":frame})
    if len({x["number"] for x in entities})!=len(entities):
        raise ValueError("Duplicate entity indices")
    return {"available":True,"server_time_ms":time_ms,"entities":entities,
            "positions_are_trajectory_bases":True,
            "actors_identified":False,"actions_supported":False}

class SceneProbe:
    def __init__(self,directory,timeout=3):
        self.folder=Path(directory)
        self.timeout=timeout
        if not self.folder.is_dir() or not 0<timeout<=30:
            raise ValueError("Existing bridge directory and timeout required")
    def snapshot(self):
        req=self.folder/"camera_request.txt"
        tmp=self.folder/"camera_request.tmp"
        reply=self.folder/"camera_response.txt"
        if req.exists() or tmp.exists():
            raise RuntimeError("Camera bridge busy")
        # Windows can temporarily lock the engine reply file.
        deadline=time.monotonic()+self.timeout
        while True:
            try:
                reply.unlink(missing_ok=True)
                break
            except PermissionError:
                if time.monotonic()>=deadline:raise
                time.sleep(.025)
        try:
            with tmp.open("x",encoding="ascii") as f:f.write("gfscene\n")
            os.replace(tmp,req)
            while time.monotonic()<deadline:
                try:
                    if reply.exists():
                        payload=reply.read_text(encoding="ascii")
                        parsed=parse_scene(payload)
                        try:reply.unlink()
                        except PermissionError:pass
                        return parsed
                except (PermissionError,ValueError):
                    # Engine may still be writing this response on Windows.
                    pass
                time.sleep(.025)
            raise TimeoutError("No complete scene snapshot response; rebuild modified native client")
        finally:
            tmp.unlink(missing_ok=True)
