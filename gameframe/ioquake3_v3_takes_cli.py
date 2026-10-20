"""Preview or perform a V3 cinematic renderer take and save a JSON manifest."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .ioquake3_render_camera import IoQuake3RenderCamera
from .ioquake3_v3_takes import load_take,run_take

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V3: cinematic render-only six-axis take")
    p.add_argument("take",type=Path)
    p.add_argument("--dir",type=Path)
    p.add_argument("--run",action="store_true",help="Send commands to active V2 engine")
    p.add_argument("--allow-translation",action="store_true",help="Opt in to unverified motion through map geometry")
    p.add_argument("--rate",type=float,default=8)
    p.add_argument("--linear",action="store_true")
    p.add_argument("--manifest",type=Path,help="Save execution plan/results as JSON")
    args=p.parse_args(argv)
    if args.run and args.dir is None: p.error("--run requires --dir")
    take=load_take(args.take)
    bridge=IoQuake3RenderCamera(args.dir) if args.run else None
    manifest=run_take(take,bridge,rate=args.rate,live=args.run,allow_translation=args.allow_translation,ease=not args.linear)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True,exist_ok=True)
        args.manifest.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in manifest.items() if k!="samples"},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
