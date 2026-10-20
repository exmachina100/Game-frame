"""Patch V4 ioquake3 client for developer-only static BSP world collision traces.

Uses CM_BoxTrace against world model 0. Static world brushes only: not dynamic
entities, movers, rendered meshes or guarantees of a camera-safe shot.
"""
from pathlib import Path
import argparse

MARKER="/* GAMEFRAME_V7_WORLD_TRACE */"
BLOCK=r'''
    /* GAMEFRAME_V7_WORLD_TRACE */
    {
        double a,b,c,d,e,g;
        char tail;
        if (strncmp(line,"gftrace ",8)==0) {
            if (sscanf(line,"gftrace %lf %lf %lf %lf %lf %lf %c",
                       &a,&b,&c,&d,&e,&g,&tail)==6 &&
                isfinite(a)&&isfinite(b)&&isfinite(c)&&
                isfinite(d)&&isfinite(e)&&isfinite(g)&&
                fabs(a)<100000&&fabs(b)<100000&&fabs(c)<100000&&
                fabs(d)<100000&&fabs(e)<100000&&fabs(g)<100000 &&
                clc.state>=CA_LOADING) {
                vec3_t start,end,zero={0,0,0};
                trace_t tr;
                start[0]=(float)a;start[1]=(float)b;start[2]=(float)c;
                end[0]=(float)d;end[1]=(float)e;end[2]=(float)g;
                CM_BoxTrace(&tr,start,end,zero,zero,0,CONTENTS_SOLID,0);
                fprintf(fp,"TRACE %.7f %d %d\n",tr.fraction,
                        tr.startsolid?1:0,tr.allsolid?1:0);
            } else {
                fprintf(fp,"REJECTED\n");
            }
            fclose(fp);
            return;
        }
    }
'''
def patch_source(source):
    if MARKER in source:raise ValueError("V7 world trace already installed")
    anchor='    /* GAMEFRAME_V4_CAPTURE */'
    if source.count(anchor)!=1:raise ValueError("Requires V4-patched ioquake3 client source")
    return source.replace(anchor,BLOCK+"\n"+anchor,1)
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args(argv)
    target=a.checkout/"code/client/cl_main.c"
    updated=patch_source(target.read_text(encoding="utf-8"))
    if a.apply:
        target.write_text(updated,encoding="utf-8")
        print("Patched",target)
    else:print("V7 static trace patch compatible; use --apply after closing engine")
if __name__=="__main__":main()
