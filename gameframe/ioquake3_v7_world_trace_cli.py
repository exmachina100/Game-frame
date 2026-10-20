"""V7: query static BSP world clearance before planning a camera move."""
import argparse
import json
from .ioquake3_v7_world_trace import IoQuake3WorldTrace,inspect_path
def main(argv=None):
    p=argparse.ArgumentParser(description="GameFrame V7 static-world collision preflight")
    p.add_argument("--dir",required=True)
    p.add_argument("--start",type=float,nargs=3,required=True)
    p.add_argument("--end",type=float,nargs=3,required=True)
    p.add_argument("--spacing",type=float,default=16)
    a=p.parse_args(argv)
    if not 1<=a.spacing<=128:p.error("--spacing must be 1-128")
    bridge=IoQuake3WorldTrace(a.dir)
    result=inspect_path(bridge,[a.start,a.end],max_spacing=a.spacing)
    print(json.dumps(result,indent=2))
    return 0 if result["static_world_clear"] else 2
if __name__=="__main__":
    raise SystemExit(main())
