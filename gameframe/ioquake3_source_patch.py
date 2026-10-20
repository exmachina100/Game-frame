"""Generate a minimal opt-in GameFrame camera command bridge for ioquake3 client source.

Patch a separate checkout of ioquake/ioq3; never alter a distributed executable.
Commands are strict numeric setviewpos only. Local file queue is explicitly
experimental, not frame-exact or a detached free camera.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "/* GAMEFRAME_CAMERA_BRIDGE_V1 */"
HOOK = "GF_CameraPoll();"
SOURCE = r"""
/* GAMEFRAME_CAMERA_BRIDGE_V1 */
/* Optional local developer-only bridge. GPL-compatible with ioquake3 source. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static void GF_CameraPoll(void) {
    static int lastPoll = 0;
    const char *root = getenv("GAMEFRAME_IOQ3_BRIDGE_DIR");
    char path[1024], reply[1024], line[256];
    FILE *fp;
    double x, y, z, yaw;
    char extra;
    int now = Sys_Milliseconds();
    if (!root || !root[0] || strlen(root) > 880) return;
    if (now - lastPoll < 50) return;
    lastPoll = now;
    if (snprintf(path, sizeof(path), "%s\\camera_request.txt", root) >= (int)sizeof(path)) return;
    fp = fopen(path, "r");
    if (!fp) return;
    line[0] = 0;
    if (!fgets(line, sizeof(line), fp)) { fclose(fp); remove(path); return; }
    fclose(fp);
    remove(path);
    if (snprintf(reply, sizeof(reply), "%s\\camera_response.txt", root) >= (int)sizeof(reply)) return;
    fp = fopen(reply, "w");
    if (!fp) return;
    if (sscanf(line, "setviewpos %lf %lf %lf %lf %c", &x, &y, &z, &yaw, &extra) == 4
        && isfinite(x) && isfinite(y) && isfinite(z) && isfinite(yaw)
        && fabs(x) <= 100000 && fabs(y) <= 100000
        && fabs(z) <= 100000 && fabs(yaw) <= 100000) {
        char command[180];
        snprintf(command, sizeof(command), "setviewpos %.3f %.3f %.3f %.3f\n", x, y, z, yaw);
        Cbuf_AddText(command);
        fprintf(fp, "QUEUED\n");
    } else {
        fprintf(fp, "REJECTED\n");
    }
    fclose(fp);
}
"""

def patch_source(contents: str) -> str:
    if MARKER in contents:
        raise ValueError("GameFrame bridge patch already present")
    anchor = "void CL_Frame ( int msec ) {"
    if contents.count(anchor) != 1:
        raise ValueError("Unsupported ioquake3 source: CL_Frame signature differs")
    return contents.replace(anchor, SOURCE + "\n" + anchor + "\n\t" + HOOK, 1)


def patch_checkout(root: Path) -> Path:
    target = Path(root) / "code" / "client" / "cl_main.c"
    if not target.is_file():
        raise FileNotFoundError(f"ioquake3 source not found: {target}")
    before = target.read_text(encoding="utf-8")
    after = patch_source(before)
    target.write_text(after, encoding="utf-8")
    return target


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Patch local ioquake3 source with camera bridge")
    p.add_argument("checkout", type=Path)
    p.add_argument("--apply", action="store_true", help="Opt-in source modification")
    args = p.parse_args(argv)
    path = args.checkout / "code" / "client" / "cl_main.c"
    if args.apply:
        print("Patched", patch_checkout(args.checkout))
    else:
        if not path.is_file():
            raise FileNotFoundError(path)
        patch_source(path.read_text(encoding="utf-8"))
        print("Patch compatible. Dry run only; add --apply to modify source.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
