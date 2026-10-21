"""Read-only Quake III client entity snapshot; never executes actions."""
import argparse
import json
from pathlib import Path
from .stage2_scene_probe import SceneProbe
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args(argv)
    data=SceneProbe(a.dir).snapshot()
    encoded=json.dumps(data,indent=2)+"\n"
    if a.output:
        if a.output.exists():raise FileExistsError(a.output)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(encoded,encoding="utf-8")
    print(encoded)
if __name__=="__main__":main()
