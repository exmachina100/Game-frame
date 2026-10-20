"""Experimental V2 cinematic render-camera patch for a separate ioquake3 checkout.

Adds an opt-in cgame refdef override and client console queue commands.
Requires rebuilding BOTH ioquake3.exe and baseq3/cgame.dll (or QVM).
This affects rendered viewpoint only, not physics or player position.
"""
from pathlib import Path
import argparse
from .ioquake3_source_patch import MARKER as V1_MARKER

V2_CLIENT_MARKER="/* GAMEFRAME_V2_CLIENT */"
V2_CGAME_MARKER="/* GAMEFRAME_V2_CGAME */"

CLIENT_BRANCH=r'''
    /* GAMEFRAME_V2_CLIENT */
    {
        double a,b,c,p,y,r,f;
        char tail;
        if (sscanf(line, "gfview %lf %lf %lf %lf %lf %lf %lf %c",
                   &a,&b,&c,&p,&y,&r,&f,&tail)==7
            && isfinite(a)&&isfinite(b)&&isfinite(c)&&isfinite(p)
            && isfinite(y)&&isfinite(r)&&isfinite(f)
            && fabs(a)<100000 && fabs(b)<100000 && fabs(c)<100000
            && fabs(p)<=89 && fabs(y)<=36000 && fabs(r)<=180
            && f>=20 && f<=130) {
            char command[300];
            snprintf(command, sizeof(command),
              "set gf_cam_pose \"%.3f %.3f %.3f %.3f %.3f %.3f\"\nset gf_cam_enabled 1\nset cg_fov %.3f\n",
              a,b,c,p,y,r,f);
            Cbuf_AddText(command);
            fprintf(fp, "QUEUED\n");
            fclose(fp);
            return;
        }
        if (strcmp(line,"gfreset\n")==0 || strcmp(line,"gfreset")==0) {
            Cbuf_AddText("set gf_cam_enabled 0\n");
            fprintf(fp, "QUEUED\n");
            fclose(fp);
            return;
        }
    }
'''
# Use explicit C string escaping because branch is embedded in Python raw string.
CGAME_HOOK=r'''
/* GAMEFRAME_V2_CGAME */\n/* renderer-only detached viewpoint. */
static void GF_CinematicView(void) {
    char flag[16];
    char pose[256];
    float x,y,z,pitch,yaw,roll;
    char tail;
    trap_Cvar_VariableStringBuffer("gf_cam_enabled", flag, sizeof(flag));
    if (atoi(flag) != 1) return;
    trap_Cvar_VariableStringBuffer("gf_cam_pose", pose, sizeof(pose));
    if (sscanf(pose,"%f %f %f %f %f %f %c",
               &x,&y,&z,&pitch,&yaw,&roll,&tail) != 6) return;
    if (!isfinite(x)||!isfinite(y)||!isfinite(z)||
        !isfinite(pitch)||!isfinite(yaw)||!isfinite(roll)||
        fabs(x)>100000||fabs(y)>100000||fabs(z)>100000||
        fabs(pitch)>89||fabs(roll)>180) return;
    cg.refdef.vieworg[0]=x;
    cg.refdef.vieworg[1]=y;
    cg.refdef.vieworg[2]=z;
    cg.refdefViewAngles[PITCH]=pitch;
    cg.refdefViewAngles[YAW]=yaw;
    cg.refdefViewAngles[ROLL]=roll;
    AnglesToAxis(cg.refdefViewAngles, cg.refdef.viewaxis);
}
'''

def patch_client(source: str) -> str:
    if V2_CLIENT_MARKER in source:
        raise ValueError("V2 client already patched")
    if V1_MARKER not in source:
        raise ValueError("Apply existing GameFrame V1 source patch first")
    anchor='    if (sscanf(line, "setviewpos %lf %lf %lf %lf %c",'
    if source.count(anchor)!=1:
        raise ValueError("V1 client anchor changed")
    return source.replace(anchor,CLIENT_BRANCH+"\n"+anchor,1)

def patch_cgame(source: str) -> str:
    if V2_CGAME_MARKER in source or "/* GAMEFRAME_V2_CGAME: renderer-only detached viewpoint. */" in source:
        raise ValueError("V2 cgame already patched")
    anchor='static int CG_CalcViewValues( void ) {'
    target='\tinwater = CG_CalcViewValues();'
    if source.count(anchor)!=1 or source.count(target)!=1:
        raise ValueError("Unsupported cg_view.c anchors")
    # cg_local.h includes math library through Q_shared headers; add standard headers explicitly.
    prefix='#ifndef Q3_VM\n#include <stdio.h>\n#include <stdlib.h>\n#include <math.h>\n'
    source=source.replace(anchor,prefix+CGAME_HOOK.replace("*/\\n/*", "*/\n/*")+"\n#endif /* !Q3_VM */\n"+anchor,1)
    return source.replace(target,target+"\n#ifndef Q3_VM\n\tGF_CinematicView();\n#endif",1)

def repair_checkout(root: Path) -> Path:
    """Guard existing V2 native-only camera override from the QVM compiler."""
    file = root / "code/cgame/cg_view.c"
    source = file.read_text(encoding="utf-8")
    if "GF_CinematicView" not in source:
        raise ValueError("V2 cgame override is not installed")
    if "#ifndef Q3_VM\n#include <stdio.h>" in source:
        print("V2 cgame QVM guard already installed")
        return file
    needle = "#include <stdio.h>\n#include <stdlib.h>\n#include <math.h>\n"
    if source.count(needle) != 1:
        raise ValueError("Expected exactly one V2 standard-header block")
    source = source.replace(needle, "#ifndef Q3_VM\n"+needle,1)
    # V2 previously inserted a literal backslash-n between marker comments.
    source = source.replace("/* GAMEFRAME_V2_CGAME */\\n/*", "/* GAMEFRAME_V2_CGAME */\n/*",1)
    anchor = "\nstatic int CG_CalcViewValues( void ) {"
    if source.count(anchor) != 1:
        raise ValueError("Unsupported cgame view anchor")
    source=source.replace(anchor,"\n#endif /* !Q3_VM */"+anchor,1)
    call="\n\tGF_CinematicView();"
    if source.count(call) != 1:
        raise ValueError("V2 camera call not found exactly once")
    source=source.replace(call,"\n#ifndef Q3_VM"+call+"\n#endif",1)
    file.write_text(source,encoding="utf-8")
    return file


def patch_checkout(root: Path) -> tuple[Path,Path]:
    client=root/"code/client/cl_main.c"
    cgame=root/"code/cgame/cg_view.c"
    if not client.is_file() or not cgame.is_file():
        raise FileNotFoundError("Expected ioquake3 source checkout")
    before1=client.read_text(encoding="utf-8")
    before2=cgame.read_text(encoding="utf-8")
    after1=patch_client(before1)
    after2=patch_cgame(before2)
    # Validate BOTH before any writing.
    client.write_text(after1,encoding="utf-8")
    cgame.write_text(after2,encoding="utf-8")
    return client,cgame

def main(argv=None):
    p=argparse.ArgumentParser(description="Apply experimental V2 render-camera patch")
    p.add_argument("checkout",type=Path)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--repair-qvm",action="store_true",help="Repair already-patched V2 cgame for QVM builds")
    args=p.parse_args(argv)
    if args.repair_qvm:
        print("Repaired:",repair_checkout(args.checkout))
    elif args.apply:
        print("Patched:",*[str(p) for p in patch_checkout(args.checkout)],sep="\n")
    else:
        root=args.checkout
        patch_client((root/"code/client/cl_main.c").read_text(encoding="utf-8"))
        patch_cgame((root/"code/cgame/cg_view.c").read_text(encoding="utf-8"))
        print("Compatible checkout; dry run only")
if __name__=="__main__":
    main()
