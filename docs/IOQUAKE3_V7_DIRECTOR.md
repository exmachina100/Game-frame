# GameFrame V7.4 — all-shot-preflight director

Committed code, **not yet run against your local Windows Quake III installation**.

The default reference sequence contains only the **visually validated dolly** from `(212,2360,56)` to `(212,2380,56)`, yaw 315°, four seconds. The previously static-collision-cleared crane to Z 76 requires an explicit `--include-crane` flag because its visual framing was not confirmed in the conversation. Orbit requires an explicit measured target through `--orbit-target X Y Z`. The director does not guess a world-space subject coordinate.

The director checks the sampled camera positions and line segments for **every shot** before playback. If any static BSP point trace detects collision, the entire sequence is rejected before the first pose is queued. This is a static point-trace check, NOT camera rig volume clearance, dynamic collision, occlusion or cinematographic quality assurance. Runtime transport is not frame-accurate.

## Pull and test
```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
```

Keep your existing V7-modified Quake III running with `q3dm1`, native cgame DLL, HUD hidden and console closed. No engine rebuild is necessary.

## Default: verified dolly only; preflight dry-run
```powershell
python -m gameframe.ioquake3_v7_director_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge"
```

## Opt-in crane: preflight two shots, no playback
```powershell
python -m gameframe.ioquake3_v7_director_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --include-crane
```

If both pass, optionally run the two-shot sequence:
```powershell
python -m gameframe.ioquake3_v7_director_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --include-crane --run
```

Observe the **crane shot** visually and report any wall intrusion. Do not add orbit until the arena subject target is determined and surveyed. When known, add `--orbit-target X Y Z` and run dry preflight first.

The previous V6 video recorder is unchanged. This new director does not export an MP4.
