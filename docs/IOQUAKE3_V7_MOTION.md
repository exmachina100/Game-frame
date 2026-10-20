# GameFrame V7.3 — motion presets with static BSP preflight

V7 already has a visually tested camera pan at yaw 270–330, a 20-unit dolly at origin `212 2360 56` through `212 2380 56`, and static-world point/segment traces at these two endpoints. V7.3 converts the proof into reusable **dolly**, **crane**, and **orbit** keyframe generators and a **preflight-before-playback** tool. It uses the previously compiled V7 native collision bridge, without further C rebuild.

## Architecture

- `gameframe/ioquake3_v7_motion.py`: `create_motion(kind,...)` yields a V3-compatible cinematic take for dolly, crane, or orbit. `preflight_motion` samples the *actual eased path* and calls native `gftrace` for each camera location and each path segment. `run_checked_motion` rejects blocked paths **before sending any camera pose**.
- `gameframe/ioquake3_v7_motion_cli.py`: invokes the native static trace bridge for both preview preflight and optional `--run` live movement.
- `tests/test_ioquake3_v7_motion.py`: motion generator and blocked-movement tests.

**Guarantees and limits:** This preflight uses **point traces against static BSP world geometry only**. Dynamic actors/doors, decorated render meshes, visual composition and camera-volume radius are NOT included. `static_world_clear:true` does not mean a production-safe dolly. A longer motion uses more trace requests and could take considerable wall-clock time. The camera itself uses the existing V3 wall-clock transport, not deterministic engine frame time. The commands do not record video yet.

## First test — use only the previously verified 20-unit dolly

Keep the V7-patched Quake III running with `q3dm1` loaded and the native V2 camera DLL. Use a second PowerShell window:

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
```

First run collision preflight *without moving the camera*:

```powershell
python -m gameframe.ioquake3_v7_motion_cli dolly `
  --dir "D:\AI\Game Frame\ioq3-camera-bridge" `
  --origin 212 2360 56 `
  --end 212 2380 56 `
  --yaw 315 `
  --duration 4
```

If `static_world_clear:true`, run the exact shot:

```powershell
python -m gameframe.ioquake3_v7_motion_cli dolly `
  --dir "D:\AI\Game Frame\ioq3-camera-bridge" `
  --origin 212 2360 56 `
  --end 212 2380 56 `
  --yaw 315 `
  --duration 4 `
  --run
```

For other moves, **do not use guessed crane/orbit coordinates without a geometry test and visual review**. Example syntax (dry-run only): `python -m gameframe.ioquake3_v7_motion_cli crane --dir "<bridge-folder>" --origin X Y Z --end X Y Z2` or `... orbit --origin X Y Z --target TX TY TZ --degrees 30`.

## Next

- Camera hull-based traces with collision radius, render-geometry visibility, dynamic mover checks.
- A path preview/timeline with approval before capture.
- Extend capture to shot presets only after the local motion/trace integration is verified.
- Deterministic frame-timed capture remains pending.
