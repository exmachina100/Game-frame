"""V5 capture verification: match actual fresh JPEGs to exact requested shot names.

Only accepted filenames are <capture>.jpg or <capture>-<digits>.jpg.
No unrelated newest-file fallback; a missing screenshot remains unverified.
"""
from __future__ import annotations
from pathlib import Path
import os
import re
import shutil
import time

def snapshot_screenshot_dir(folder):
    folder=Path(folder)
    if not folder.is_dir():
        return {}
    return {p.name.lower():(p.stat().st_mtime_ns,p.stat().st_size)
            for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".jpg",".jpeg")}

def find_new_files(before,folder):
    folder=Path(folder)
    if not folder.is_dir(): return []
    after=snapshot_screenshot_dir(folder)
    return sorted((folder/name for name,state in after.items() if before.get(name)!=state),
                  key=lambda p:p.name)

def match_capture_files(names,files):
    """Return request-name -> distinct JPEG path or None, without loose fallbacks."""
    matches={}
    remaining=list(files)
    for name in names:
        regex=re.compile(r"^"+re.escape(name)+r"(?:[-_][0-9]+)?\.(?:jpg|jpeg)$",re.I)
        candidates=[p for p in remaining if regex.fullmatch(p.name)]
        exact=[p for p in candidates if p.stem.lower()==name.lower()]
        choice=(exact or sorted(candidates,key=lambda p:p.stat().st_mtime_ns,reverse=True))
        matches[name]=choice[0] if choice else None
        if choice: remaining.remove(choice[0])
    return matches

def wait_for_capture(folder,before,name,*,timeout=3.0,poll=0.05,clock=time.monotonic,sleep=time.sleep):
    if timeout<0: raise ValueError("timeout cannot be negative")
    end=clock()+timeout
    while True:
        matches=match_capture_files([name],find_new_files(before,folder))
        if matches[name] is not None: return matches[name]
        if clock()>=end: return None
        sleep(min(poll,max(0,end-clock())))

def stage_verified_capture(source,output_dir,index,shot_name):
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    target=out/f"{index:02d}_{shot_name}.jpg"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite previous capture: {target}")
    temp=out/(target.name+".part")
    try:
        if temp.exists(): raise FileExistsError(f"Previous staging file exists: {temp}")
        with Path(source).open("rb") as src, temp.open("xb") as dest:
            shutil.copyfileobj(src,dest)
        if temp.stat().st_size==0: raise ValueError("Empty screenshot")
        os.replace(temp,target)
    finally:
        temp.unlink(missing_ok=True)
    return target
