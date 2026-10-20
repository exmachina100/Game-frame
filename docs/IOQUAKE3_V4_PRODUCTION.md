# GameFrame V4 — multi-shot film production

**Implementation committed; not yet live-verified on the user's Windows machine.** V3 independent cinematic camera take was verified live at 12 seconds and 97 queued samples. V4 adds multiple named shots and optional JPEG capture requests.

## What's implemented

- A production JSON file with 1–16 named shots; each shot has independently timed pitch/yaw/roll/FOV/XYZ keyframes.
- Wall-clock playback through the **V2 renderer-only camera**, at the selected 1–15 Hz command rate.
- Hard cuts between sequential takes (no fades/compositing).
- Sample manifests with camera command acknowledgements and capture-request acknowledgements.
- A small client-source addition for `gfcapture <safe-name>` => ioquake3 `screenshotJPEG <safe-name>` console command.
- Resets camera once after the production, rather than between capture and the shot.
- XYZ translation is blocked unless explicitly allowed; camera clearance is not available.

**Not yet available:** native video recording, automatic output-file readback, movie assembly, actor choreography, exact-frame capture sync, engine camera pose readback. `QUEUED` is not a guarantee that the requested JPEG exists on disk.

## First test: camera-only 24-second, 3-shot sequence (no C++ rebuild)

Use your existing successfully tested V2 build, with `sv_pure 0`, `vm_cgame 0`, modified `cgame.dll` loaded, and bridge environment variable set **before** starting game. `/devmap q3dm1` and close console for visual check.

Sample XYZ is fixed at `212 2360 56`, previously used in successful V2 camera tests. If that location is obstructed, change all keyframes to a known clear point.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.ioquake3_v4_production_cli docs/examples/quake_v4_film.json
python -m gameframe.ioquake3_v4_production_cli docs/examples/quake_v4_film.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run
```

Expect 3 shots, 195 total camera requests at 8 Hz and planned 24-second playback (per-shot endpoints included).

## Add screenshot requests (requires updating ioquake3.exe only)

Close Quake III fully. On your **already V1/V2-patched** local source checkout:

```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_v4_source_patch "D:\AI\Game Frame\ioq3-gameframe-source" --apply
cd "D:\AI\Game Frame\ioq3-gameframe-source"
$env:Path = "C:\Program Files\CMake\bin;$env:Path"
cmake --build build-gameframe --config Release --parallel 4
```

**Apply only once.** This source patch only changes client `cl_main.c`; no new cgame source patch is necessary. Keep your working original ioquake3 installation intact.

Restart patched Quake III using the known V2 launch flags and `GAMEFRAME_IOQ3_BRIDGE_DIR` set. To avoid pure-server forcing QVM, include `+set sv_pure 0 +set vm_cgame 0`. Run from GameFrame:

```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_v4_production_cli docs/examples/quake_v4_film.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run --capture --manifest "takes/v4_film_capture.json"
```

Output JPG files may appear inside the engine home directory's `baseq3/screenshots` or according to the engine's screenshot naming rules. Check the Quake console for screenshot messages; then locate files with:

```powershell
Get-ChildItem "D:\AI\Game Frame\ioq3-v2-home" -Recurse -Filter "*.jpg" | Select-Object FullName,Length,LastWriteTime
```

Capture is issued at each shot's final pose, before camera reset. It does not produce video. The manifest records `file_verified:false` until media checking is implemented.

## Next engineering priorities

1. Screenshot filename confirmation, request IDs, and receipt verification.
2. Frame/capture synchronization and native video or ordered-frame export.
3. Map geometry raycast or safe camera corridor checks.
4. Multi-shot timeline editing, retake selection, media browser.
5. Camera target tracking, actor staging and engine-neutral MCP director integration.
