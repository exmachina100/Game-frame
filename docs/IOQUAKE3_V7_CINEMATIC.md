# GameFrame V7 — clean cinematic output and target framing (phase 1)

V6 produced an actual 856x480, 8-fps, 24-second 192-frame MP4, verified by FFprobe. Reviewing the submitted contact sheet exposed first-person HUD, close-up wall obstructions and shots without a clear visual subject. **This phase does not yet implement renderer frame-locking or collision/occlusion detection.**

## Implemented and committed

1. `gameframe/ioquake3_v7_cinematic.py` — target-aware framing. Compute Quake pitch/yaw for the vector between camera and specified world-space target, preserving existing keyframe XYZ/roll and optionally changing FOV. Refuse impossible vertical target angles. Outputs remain subject to map collision and occlusion.
2. `gameframe/ioquake3_v7_cinematic_cli.py` — output a new V4/V6-compatible film JSON, and display recommended cinematic launch cvars.
3. `tests/test_ioquake3_v7_cinematic.py` — Quake angle sign and cardinal axes, invalid targets, JSON round trip, launch flags.

## Clean HUD and console notifications

**Close the existing ioquake3 executable and relaunch** the same V4-patched `ioquake3.exe` with the V2 native `cgame.dll` in its isolated homepath. Pass extra console variables on launch:

```powershell
$env:GAMEFRAME_IOQ3_BRIDGE_DIR = "D:\AI\Game Frame\ioq3-camera-bridge"
& "D:\AI\Game Frame\ioq3-gameframe-source\build-gameframe\Release\ioquake3.exe" `
  +set fs_basepath "D:\AI\Quake 3 Arena" `
  +set fs_homepath "D:\AI\Game Frame\ioq3-v2-home" `
  +set sv_pure 0 `
  +set vm_cgame 0 `
  +set r_fullscreen 0 `
  +set cg_draw2D 0 `
  +set cg_drawGun 0 `
  +set cg_drawCrosshair 0 `
  +set con_notifytime 0
```

Then use `/devmap q3dm1`, **close the console**, and verify the arena is visible without health/ammo overlays. These are existing game cvars; no native rebuild is needed.

## Target-aware framing: do not guess the subject point

The coordinates **300 2400 60 below are an example**, not a verified visible subject in q3dm1. You should use a real target position identified by in-game inspection. Output only writes a shot plan; it doesn't move, spawn or identify game actors.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.ioquake3_v7_cinematic_cli docs/examples/quake_v4_film.json --target 300 2400 60 --out docs/examples/quake_v7_targeted_local.json --launch-flags
```

Camera-only test with your existing native bridge, substituting verified clear target coordinates. Note: if your three shot cameras share the same position and target, all three shots share the same pitch/yaw. To create actual pans around a subject, author different positions and explicitly opt in to translation only after visually validating clearance. Avoid using the placeholder `--target` coordinates in a full 192-frame video unless the framing looks correct in a brief test.

```powershell
python -m gameframe.ioquake3_v4_production_cli docs/examples/quake_v7_targeted_local.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run
```

**Avoid re-recording 192 images until visual composition looks correct.** For a separate V6 film output, use a new `--output-dir` and the reviewed production JSON.

## Phase 1b: six-frame visual scout after wall obstruction was confirmed

User visually confirmed **HUD hidden, camera looking into a wall** for placeholder target `300 2400 60` from `212 2360 56`. The placeholder target is not a verified visible subject. Don't record another 192-frame movie using it.

Use a live, V4-patched ioquake3 engine with the native V2 cgame module, bridge and cinematic launch flags from above. Scout **six camera origins** around the previous test position and aim each at the test target; inspect the saved JPEGs manually. Positions may intersect map geometry; **the scout does not guarantee clearance**.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.ioquake3_v7_scout --dir "D:\AI\Game Frame\ioq3-camera-bridge" --screenshot-dir "D:\AI\Game Frame\ioq3-v2-home\baseq3\screenshots" --output-dir "output\v7_scout_01" --origin 212 2360 56 --target 300 2400 60 --offset 32
Get-ChildItem "output\v7_scout_01"
```

This generates `01_origin.jpg`, `02_left.jpg`, `03_right.jpg`, `04_back.jpg`, `05_forward.jpg`, `06_up.jpg` and `scout.json`. Choose the best visibly clear image, or report if all are blocked. Use a new output directory per attempt. The next engineering step is **real scene geometry raycasting**, not treating a visually selected sample as proof of collision-free camera travel.

## Phase 2 planned

- Engine-coupled render-time camera timeline and direct framebuffer capture, replacing per-frame screenshots.
- Camera raycasts and geometry-aware avoidance, with chosen subject visibility checked.
- Resolution independent from window size, scene actor choreography, synchronization and codec selection.
- Per-frame timing diagnostics and movie cadence analysis.
