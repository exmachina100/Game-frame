"""Inspect supported game engines and validate cinematic shot plans.

Example:
  python -m gameframe.engine_cli inspect ioquake3
  python -m gameframe.engine_cli validate docs/examples/alley_scene.json ioquake3
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .engines import parse_plan
from .ioquake3 import IoQuake3Adapter

def main(argv=None):
    p = argparse.ArgumentParser(description="GameFrame cinematic engine diagnostics")
    sub = p.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("engine", choices=["ioquake3"])
    inspect.add_argument("--exe", default=None)
    validate = sub.add_parser("validate")
    validate.add_argument("plan", type=Path)
    validate.add_argument("engine", choices=["ioquake3"])
    validate.add_argument("--exe", default=None)
    args = p.parse_args(argv)
    adapter = IoQuake3Adapter(args.exe)
    if args.command == "inspect":
        report = {**adapter.diagnostics(), "capabilities": adapter.capabilities().describe()}
        code = 0
    else:
        plan = parse_plan(json.loads(args.plan.read_text(encoding="utf-8")))
        report = plan.validate_for(adapter.capabilities())
        code = 0 if report["ready"] else 2
    print(json.dumps(report, indent=2))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
