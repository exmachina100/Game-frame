"""V7.5: preflight every cinematic movement before any V6 frame is captured."""
from __future__ import annotations
import json
from pathlib import Path
from .ioquake3_v7_director import reference_plan,preflight_plan
from .ioquake3_v4_production import Production
from .ioquake3_v6_video import record_film

def produce_checked_film(trace_bridge,capture_bridge,*,screenshots,output_dir,
                         fps=8,ffmpeg="ffmpeg",capture_timeout=3.0,encode=True,
                         include_crane=True,spacing=8):
    if not include_crane:
        raise ValueError("V7.5 initial film requires the verified dolly and crane")
    if type(fps) is not int or not 1<=fps<=15:
        raise ValueError("FPS must be an integer from 1 to 15")
    dest=Path(output_dir)
    if dest.exists():
        raise FileExistsError("Use a new film output directory")
    shots=reference_plan(include_crane=True)
    preflight=preflight_plan(shots,trace_bridge,rate=fps,spacing=spacing)
    # Only enter V6 capture if every scene has passed collision checks.
    production=Production("v75_dolly_crane",tuple(s.take for s in shots))
    result=record_film(production,capture_bridge,screenshots=screenshots,
                       output_dir=dest,fps=fps,ffmpeg=ffmpeg,
                       allow_translation=True,capture_timeout=capture_timeout,
                       encode=encode)
    result["schema"]="gameframe.v7_5.checked_film.v1"
    result["static_world_preflight"]={"passed":True,"shots":preflight,
        "dynamic_entities_checked":False,"camera_volume_checked":False,
        "render_visibility_verified":False}
    result["timeline"]=[{"shot":s.take.name,"motion":s.kind,
        "start_seconds":sum(v.take.keyframes[-1].time for v in shots[:i]),
        "duration_seconds":s.take.keyframes[-1].time}
        for i,s in enumerate(shots)]
    (dest/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result
