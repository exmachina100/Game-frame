"""Preview or run a V4 multi-shot production and save its evidence manifest."""
import argparse
import json
from pathlib import Path
from .ioquake3_v4_bridge import IoQuake3ProductionBridge
from .ioquake3_v4_production import load_production,run_production

def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V4 multi-shot director")
    p.add_argument("production",type=Path)
    p.add_argument("--dir",type=Path)
    p.add_argument("--run",action="store_true")
    p.add_argument("--capture",action="store_true",help="Request engine JPEG for every shot; requires V4 rebuild")
    p.add_argument("--allow-translation",action="store_true")
    p.add_argument("--rate",type=float,default=8)
    p.add_argument("--manifest",type=Path,default=Path("takes/v4_production.json"))
    p.add_argument("--screenshot-dir",type=Path,help="Existing ioquake3 screenshots folder for V5 verification")
    p.add_argument("--output-dir",type=Path,help="Dedicated folder for verified JPEGs")
    p.add_argument("--capture-timeout",type=float,default=3.0)
    args=p.parse_args(argv)
    if (args.screenshot_dir is None)!=(args.output_dir is None):
        p.error("--screenshot-dir and --output-dir must be used together")
    if args.output_dir and not (args.run and args.capture):
        p.error("V5 output verification requires --run --capture")
    if args.run and args.dir is None: p.error("--run requires --dir")
    if args.capture and not args.run: p.error("--capture requires --run")
    production=load_production(args.production)
    bridge=IoQuake3ProductionBridge(args.dir) if args.run else None
    result=run_production(production,bridge,live=args.run,rate=args.rate,
                          allow_translation=args.allow_translation,capture=args.capture,
                          screenshot_dir=args.screenshot_dir,output_dir=args.output_dir,
                          capture_timeout=args.capture_timeout)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"name":result["name"],"mode":result["mode"],
                      "status":result["status"],"shots":len(result["shots"]),
                      "queued":sum(x["camera"]["queued_count"] for x in result["shots"]),
                      "capture_requests":sum(len(x["captures"]) for x in result["shots"]),
                      "capture_files_verified":result["capture_files_verified"],"manifest":str(args.manifest),
                      "output_dir":result["output_dir"]},indent=2))

if __name__=="__main__":main()
