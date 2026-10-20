"""Stage 2: deterministic, non-executing scene brief validation.

The brief describes intent; it never claims the engine can move actors.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

SHOT_INTENTS=frozenset(("establishing","follow","reveal","reaction","insert"))
def validate_scene(data):
    if not isinstance(data,dict) or set(data)!={"title","map","duration","beats"}:
        raise ValueError("Scene requires title, map, duration, beats")
    if not isinstance(data["title"],str) or not 1<=len(data["title"])<=100 or not data["title"].strip():
        raise ValueError("Invalid scene title")
    if not isinstance(data["map"],str) or not 1<=len(data["map"])<=64 or not all(c.isalnum() or c in "_-" for c in data["map"]):
        raise ValueError("Invalid map")
    duration=data["duration"]
    if type(duration) not in (int,float) or not math.isfinite(duration) or not 1<=duration<=300:
        raise ValueError("Duration outside 1-300 seconds")
    beats=data["beats"]
    if not isinstance(beats,list) or not 1<=len(beats)<=24:
        raise ValueError("Scene needs 1-24 beats")
    last=0
    for i,beat in enumerate(beats):
        if not isinstance(beat,dict) or set(beat)!={"start","end","intent","subject","action"}:
            raise ValueError("Invalid beat schema")
        start,end=beat["start"],beat["end"]
        if (type(start) not in (int,float) or type(end) not in (int,float)
                or not math.isfinite(start) or not math.isfinite(end)
                or start<last or end<=start or end>duration):
            raise ValueError("Beats must be sorted, non-overlapping and inside duration")
        if i==0 and start!=0:raise ValueError("First beat must start at zero")
        if beat["intent"] not in SHOT_INTENTS:raise ValueError("Unsupported shot intent")
        if any(not isinstance(beat[k],str) or not 1<=len(beat[k].strip())<=200
               for k in ("subject","action")):
            raise ValueError("Subject and action required")
        last=end
    return data

def capability_report(scene,*,actor_actions_supported=False):
    validate_scene(scene)
    unsupported=[{"beat":i+1,"action":b["action"],"reason":"actor action execution unavailable"}
        for i,b in enumerate(scene["beats"])
        if b["subject"]!="environment" and not actor_actions_supported]
    return {"scene":scene["title"],"status":"camera_only_fallback" if unsupported else "planning_only",
            "actor_actions_executed":False,"unsupported_actions":unsupported,
            "world_targets_surveyed":False,"executable":False}

def load_scene(path):
    return validate_scene(json.loads(Path(path).read_text(encoding="utf-8")))
