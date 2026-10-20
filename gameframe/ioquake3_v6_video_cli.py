"""Record a real screenshot sequence from a GameFrame V4 patched ioquake3."""
import argparse
import json
from pathlib import Path
from .ioquake3_v4_bridge import IoQuake3ProductionBridge
from .ioquake3_v4_production import load_production
from .ioquake3_v6_video import record_film

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V6: verified frame sequence to MP4")
    p.add_argument("production",type=Path)
    p.add_argument("--dir",type=Path,required=True,help="Camera bridge folder")
    p.add_argument("--screenshot-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--fps",type=int,default=8)
    p.add_argument("--ffmpeg",default="ffmpeg")
    p.add_argument("--allow-translation",action="store_true")
    p.add_argument("--capture-timeout",type=float,default=3.0)
    p.add_argument("--frames-only",action="store_true",help="Capture frames but skip MP4 encoding")
    args=p.parse_args(argv)
    production=load_production(args.production)
    bridge=IoQuake3ProductionBridge(args.dir)
    result=record_film(production,bridge,screenshots=args.screenshot_dir,
                       output_dir=args.output_dir,fps=args.fps,
                       ffmpeg=args.ffmpeg,allow_translation=args.allow_translation,
                       capture_timeout=args.capture_timeout,encode=not args.frames_only)
    print(json.dumps({"name":result["production"],"status":result["status"],
                      "frames":len(result["frames"]),"shots":len(result["shots"]),
                      "video":result["video"],"manifest":str(args.output_dir/"manifest.json")},indent=2))

if __name__=="__main__":
    main()
