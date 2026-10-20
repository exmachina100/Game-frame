"""Upgrade the existing local V2 client source with bounded screenshot command."""
from pathlib import Path
import argparse
MARKER="/* GAMEFRAME_V4_CAPTURE */"
BLOCK=r'''
    /* GAMEFRAME_V4_CAPTURE */
    {
        char shot[100], tail;
        int i, valid=1;
        if (sscanf(line,"gfcapture %99s %c",shot,&tail)==1 &&
            strncmp(line,"gfcapture ",10)==0) {
            for(i=0;shot[i];i++) {
                if (!((shot[i]>='a'&&shot[i]<='z')||
                      (shot[i]>='A'&&shot[i]<='Z')||
                      (shot[i]>='0'&&shot[i]<='9')||
                       shot[i]=='_'||shot[i]=='-')) valid=0;
            }
            if(valid && i>0 && i<=96) {
                char cmd[160];
                snprintf(cmd,sizeof(cmd),"screenshotJPEG %s\n",shot);
                Cbuf_AddText(cmd);
                fprintf(fp,"QUEUED\n");
            } else fprintf(fp,"REJECTED\n");
            fclose(fp);
            return;
        }
    }
'''
def patch_source(source):
    if MARKER in source: raise ValueError("V4 capture already applied")
    anchor='    if (sscanf(line, "setviewpos %lf %lf %lf %lf %c",'
    if source.count(anchor)!=1: raise ValueError("Existing GameFrame bridge not found")
    return source.replace(anchor,BLOCK+"\n"+anchor,1)
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args(argv)
    file=a.checkout/"code/client/cl_main.c"
    changed=patch_source(file.read_text(encoding="utf-8"))
    if a.apply:
        file.write_text(changed,encoding="utf-8")
        print("Patched",file)
    else: print("Compatible; dry run only")
if __name__=="__main__":main()
