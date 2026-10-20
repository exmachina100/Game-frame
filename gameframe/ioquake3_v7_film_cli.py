"""V7.5: verified dolly + crane film using V6 per-frame capture and ffmpeg."""
import argparse
import json
from pathlib import Path
from .ioquake3_v4_bridge import IoQuake3ProductionBridge
from .ioquake3_v7_world_trace import IoQuake3WorldTrace
from .ioquake3_v7_film import produce_checked_film

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V7.5: collision-preflighted two-shot MP4")
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--screenshot-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--fps",type=int,default=8)
    p.add_argument("--ffmpeg",default="ffmpeg")
    p.add_argument("--capture-timeout",type=float,default=3)
    p.add_argument("--frames-only",action="store_true")
    a=p.parse_args(argv)
    trace=IoQuake3WorldTrace(a.dir)
    camera=IoQuake3ProductionBridge(a.dir)
    film=produce_checked_film(trace,camera,screenshots=a.screenshot_dir,
        output_dir=a.output_dir,fps=a.fps,ffmpeg=a.ffmpeg,
        capture_timeout=a.capture_timeout,encode=not a.frames_only)
    print(json.dumps({"status":film["status"],"shots":film["timeline"],
        "frame_count":len(film["frames"]),"video":film["video"],
        "manifest":str(a.output_dir/"manifest.json"),
        "preflight_passed":film["static_world_preflight"]["passed"]},indent=2))

if __name__=="__main__":main()
