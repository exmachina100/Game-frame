"""Add an opt-in read-only current snapshot probe to V7 patched ioquake3."""
from pathlib import Path
import argparse
MARKER="/* GAMEFRAME_STAGE2_SCENE_PROBE */"
BLOCK=r'''
    /* GAMEFRAME_STAGE2_SCENE_PROBE */
    if (strcmp(line,"gfscene\n")==0 || strcmp(line,"gfscene")==0 ||
        strcmp(line,"gfscene\r\n")==0) {
        int j,n;
        if (clc.state!=CA_ACTIVE || !cl.snap.valid ||
            cl.parseEntitiesNum-cl.snap.parseEntitiesNum>=MAX_PARSE_ENTITIES) {
            fprintf(fp,"UNAVAILABLE\n");
        } else {
            n=cl.snap.numEntities;
            if (n<0) n=0;
            if (n>MAX_ENTITIES_IN_SNAPSHOT) n=MAX_ENTITIES_IN_SNAPSHOT;
            fprintf(fp,"SCENE %d %d\n",cl.snap.serverTime,n);
            for(j=0;j<n;j++) {
                entityState_t *e=&cl.parseEntities[
                  (cl.snap.parseEntitiesNum+j)&(MAX_PARSE_ENTITIES-1)];
                fprintf(fp,"E %d %d %.3f %.3f %.3f %d %d %d\n",
                    e->number,e->eType,
                    e->pos.trBase[0],e->pos.trBase[1],e->pos.trBase[2],
                    e->legsAnim,e->torsoAnim,e->frame);
            }
        }
        fclose(fp);
        return;
    }
'''
def patch_source(source):
    if MARKER in source:raise ValueError("Stage2 probe already installed")
    anchor='    /* GAMEFRAME_V7_WORLD_TRACE */'
    if source.count(anchor)!=1:raise ValueError("Requires V7 world trace source patch")
    return source.replace(anchor,BLOCK+"\n"+anchor,1)
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args(argv)
    f=a.checkout/"code/client/cl_main.c"
    updated=patch_source(f.read_text(encoding="utf-8"))
    if a.apply:
        f.write_text(updated,encoding="utf-8")
        print("Patched",f)
    else:print("Compatible (dry-run)")
if __name__=="__main__":main()
