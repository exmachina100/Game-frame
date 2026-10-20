# GameFrame V7.5 — collision-preflighted two-shot film

The dolly and crane at yaw 315 degrees were visually approved by the user in V7.4. This opt-in workflow uses the existing V6 capture implementation unchanged, after native static-world BSP preflight of **both** camera paths. It writes a verified set of JPEG frames and attempts ffmpeg MP4 assembly into a fresh output directory.

Camera poses and screenshot commands are sent sequentially at wall-clock pace. **This is not deterministic engine-frame-synchronized capture; playback FPS is an output-file rate.** Scene contents can evolve between captures. The director preserves hard shot cuts, no cross-fade or sound edit. `manifest.json` records shot boundaries, planned durations, native static BSP preflight, frame paths, and video verification. Camera-volume/dynamic-object checks, sightline certification and render-state readback remain absent.

## Windows run

Keep the already compiled V7 ioquake3 with native cgame DLL active, `q3dm1` loaded, HUD hidden, and console **closed**. Keep the bridge environment variable set in the window launching ioquake3.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
```

If tests pass, create a **new output folder** on every run:

```powershell
python -m gameframe.ioquake3_v7_film_cli `
  --dir "D:\AI\Game Frame\ioq3-camera-bridge" `
  --screenshot-dir "D:\AI\Game Frame\ioq3-v2-home\baseq3\screenshots" `
  --output-dir "output\v75_dolly_crane_01" `
  --fps 8
```

Expected planned shot timeline: 4-second dolly, 4-second crane, 8 seconds of output playback, **64 consecutive frames** at 8fps (32 per shot). Native static geometry is checked before V6 captures begin. Depending on screenshot/write latency, execution can take longer than eight seconds.

After successful completion:

```powershell
explorer "D:\AI\Game Frame\Game-frame\output\v75_dolly_crane_01"
```

Inspect `film.mp4` and `manifest.json`. A failed run leaves a manifest of captured frames for debugging; don't re-use the same output folder. `--frames-only` is available to skip ffmpeg encoding.

If the preflight reports a blocked segment, **no video capture begins**. Do not override it or run an unverified orbit.

For follow-up: native frame-locked capture, camera-volume traces, dynamic object handling, and transition editing are separate future steps.
