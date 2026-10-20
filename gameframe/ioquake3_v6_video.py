"""V6: recorded frame sequence and truthful MP4 assembly for ioquake3.

Captures one screenshot per sampled camera pose; each frame must exist before
encoding. This is sequential wall-clock-controlled capture, NOT frame-exact
engine synchronization. Requested fps sets output playback rate.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from .ioquake3_capture_verify import snapshot_screenshot_dir,wait_for_capture
from .ioquake3_v3_takes import sample
from .ioquake3_v4_production import load_production

def encode_mp4(frames_dir,output,fps,*,ffmpeg="ffmpeg",runner=subprocess.run):
    """Encode verified numbered JPEG frames only; fail on missing ffmpeg/frames."""
    frames_dir=Path(frames_dir)
    paths=sorted(frames_dir.glob("frame_*.jpg"))
    if not paths or any(p.name!=f"frame_{i:06d}.jpg" or p.stat().st_size==0 for i,p in enumerate(paths)):
        raise ValueError("Frames must form a nonempty, contiguous, nonzero sequence")
    output=Path(output)
    if output.exists(): raise FileExistsError(f"Refusing to overwrite video: {output}")
    output.parent.mkdir(parents=True,exist_ok=True)
    command=[str(ffmpeg),"-hide_banner","-loglevel","error","-nostdin","-n",
             "-framerate",str(fps),"-start_number","0",
             "-i",str(frames_dir/"frame_%06d.jpg"),
             "-vf","scale=trunc(iw/2)*2:trunc(ih/2)*2",
             "-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    result=runner(command,check=True)
    if not output.is_file() or output.stat().st_size==0:
        raise RuntimeError("FFmpeg exited but nonempty MP4 was not found")
    return {"path":str(output),"verified":True,"frame_count":len(paths),"playback_fps":fps,"command":command}

def record_film(production,bridge,*,screenshots,output_dir,fps=8,ffmpeg="ffmpeg",
                allow_translation=False,capture_timeout=3.0,encode=True,
                clock=time.monotonic,sleep=time.sleep):
    if type(fps) is not int or not 1<=fps<=15:
        raise ValueError("FPS must be an integer from 1 to 15")
    if not 0<=capture_timeout<=30:
        raise ValueError("Capture timeout must be 0-30 seconds")
    screenshots=Path(screenshots)
    if not screenshots.is_dir(): raise ValueError("Screenshots folder must exist")
    output_dir=Path(output_dir)
    if output_dir.exists(): raise FileExistsError("Choose a new V6 output directory (previous takes are immutable)")
    for shot in production.shots:
        if not allow_translation and any(k.position!=shot.keyframes[0].position for k in shot.keyframes):
            raise ValueError("Translation requires explicit opt-in")
    output_dir.mkdir(parents=True)
    frames_dir=output_dir/"frames"
    frames_dir.mkdir()
    # Unique per execution: prevents older engine screenshots from being reused.
    run_id=uuid.uuid4().hex[:10]
    manifest={"schema":"gameframe.v6.film.v1","production":production.name,"status":"recording",
              "run_id":run_id,"fps":fps,"frame_accurate":False,
              "render_pose_readback_verified":False,"shots":[],"frames":[],
              "video":{"verified":False},"output_dir":str(output_dir)}
    manifest_path=output_dir/"manifest.json"
    def persist():
        manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    persist()
    frame_index=0
    try:
        for shot_number,shot in enumerate(production.shots,1):
            duration=shot.keyframes[-1].time
            # Frame intervals [0,duration) avoid duplicate boundary frames.
            count=math.ceil(duration*fps)
            entry={"name":shot.name,"index":shot_number,"planned_seconds":duration,
                   "expected_frames":count,"captured_frames":0}
            manifest["shots"].append(entry)
            start=clock()
            for i in range(count):
                at=i/fps
                pose=sample(shot,at)
                delay=start+at-clock()
                if delay>0:sleep(delay)
                ack=bridge.set_pose(pose.position,pitch=pose.pitch,yaw=pose.yaw,roll=pose.roll,fov=pose.fov)
                if not ack["queued"]: raise RuntimeError("Camera pose was not queued")
                token=f"gf6_{run_id}_{frame_index:06d}"
                before=snapshot_screenshot_dir(screenshots)
                captured=bridge.capture(token)
                if not captured["queued"]: raise RuntimeError(f"Capture command not queued: {token}")
                source=wait_for_capture(screenshots,before,token,timeout=capture_timeout)
                if source is None:raise TimeoutError(f"Screenshot missing: {token}")
                dest=frames_dir/f"frame_{frame_index:06d}.jpg"
                if dest.exists():raise FileExistsError(dest)
                shutil.copyfile(source,dest)
                if dest.stat().st_size==0:raise RuntimeError(f"Empty frame: {dest}")
                manifest["frames"].append({"index":frame_index,"shot":shot.name,"planned_time":round(at,4),
                                           "actual_elapsed":round(clock()-start,4),"pose_queued":True,
                                           "capture_queued":True,"file_verified":True,"source":str(source),"file":str(dest)})
                entry["captured_frames"]+=1
                frame_index+=1
                persist()
        manifest["status"]="frames_captured"
        persist()
        if encode:
            manifest["video"]=encode_mp4(frames_dir,output_dir/"film.mp4",fps,ffmpeg=ffmpeg)
            manifest["status"]="completed"
        persist()
    except BaseException as exc:
        manifest["status"]="interrupted_or_failed"
        manifest["error"]=f"{type(exc).__name__}: {exc}"
        persist()
        raise
    finally:
        try:bridge.reset()
        except Exception:pass
    return manifest
