# GameFrame V6 — moving camera footage to MP4 (experimental)

V5 was user-verified on Windows: 72 passing tests, 195 queued camera instructions, three fresh captured JPEG files and a verified manifest. V6 extends the proven V4 native `gfcapture` bridge to **capture numbered JPEGs during the camera timeline**, not just one still at each shot end.

## What is implemented

- `gameframe/ioquake3_v6_video.py`: sample each shot at selected integer 1–15 fps, queue V2 render-only camera pose, request native engine JPEG, wait for a fresh expected screenshot, copy to `frames/frame_000000.jpg` etc., update a per-frame manifest, reset camera on completion/failure.
- `encode_mp4`: invoke FFmpeg with explicit image sequence input framerate, libx264, yuv420p and even-dimension scale; require a nonempty output MP4. No audio yet.
- `gameframe/ioquake3_v6_video_cli.py`: CLI wrapper for one full production. Output directory is intentionally new for every attempt; previous takes are immutable.
- `tests/test_ioquake3_v6_video.py`: short fake-engine sequence, duplicate output refusal, encode arguments, invalid sequences and bounds.

## Requirements

Use the **V4-patched ioquake3.exe** and the previously verified **V2 native cgame.dll**, launched with `sv_pure 0`, `vm_cgame 0` and bridge environment variable. Load `/devmap q3dm1`. No additional engine rebuild should be required.

Install **FFmpeg** separately and check:

```powershell
ffmpeg -version
```

## Test commands in a second PowerShell window

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.ioquake3_v6_video_cli docs/examples/quake_v4_film.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --screenshot-dir "D:\AI\Game Frame\ioq3-v2-home\baseq3\screenshots" --output-dir "output\arena_v6_take01" --fps 8
```

Expected if every capture is successful: 3 shots x 8 seconds x 8 fps = **192 verified JPEGs**, plus `film.mp4`, `manifest.json`. Note V4's 195 commands included **one extra endpoint sample per shot**. V6 omits that duplicate shot-boundary image and therefore captures 192 frames at 8 fps.

To verify files:

```powershell
(Get-ChildItem "output\arena_v6_take01\frames" -Filter "frame_*.jpg").Count
Get-Item "output\arena_v6_take01\film.mp4"
```

## Important limitations

**V6 is not yet live verified.** Each frame requires a camera bridge acknowledgement and an engine JPEG write/read. This sequential method is limited by disk/engine latency and may run slower than real time. The MP4 will play at the requested encoded FPS, so its nominal duration equals total sampled duration, but camera/world animations **are not frame-locked** to the video. It is a proof-of-output recorder, not yet professional sync or deterministic in-game rendering.

There is no engine playback clock, native continuous video capture, synchronized actors/audio, collision test, or automatic visual quality analysis. If an expected image is missing or FFmpeg fails, V6 raises an error and preserves the already captured frames and failure manifest rather than claiming completion. Every run needs a **new output directory**.

## Next after validation

- Benchmark realistic capture speed and image dimensions, then optimize.
- Native renderer frame callback and deterministic video capture without screenshot command overhead.
- Audio recording/synchronization; metadata and shots/takes browser.
- Camera/actor choreography and scene direction.
