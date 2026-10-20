# GameFrame Cinematic Camera V2 — experimental renderer override

**Code committed; not yet compiled or visually verified on Windows.** The previously verified V1 camera controller remains intact.

## Architecture

V1 uses server-side `setviewpos x y z yaw`, moving the playable character. V2 adds a second command (`gfview x y z pitch yaw roll fov`) to the already-patched client queue. The client puts the numbers in local cvars; a new `cg_view.c` hook overrides the **rendered view origin and view axes** after the normal game view calculation. This can decouple the *visual* camera from the player's location. It does **not** move player physics, create an editable 3D scene, freeze actors, or give scene collision validation.

- `gfreset` disables the override (but does **not** restore the previous FOV automatically).
- GameFrame uses `cg_fov` for FOV; the engine's existing FOV behavior applies.
- Camera pitch limited to ±89°, roll ±180°, FOV 20–130°. Positions must be chosen from known playable map areas until scene-aware clearance is available.
- This is a client-side experimental local tool intended only for private/offline test maps. Reconnect to ordinary gameplay with `--reset`.

## Rebuild — Windows PowerShell

Close Quake III first. In the existing GameFrame project folder:

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v

# Your separate ioquake3 source checkout already has the V1 patch.
python -m gameframe.ioquake3_v2_source_patch "D:\AI\Game Frame\ioq3-gameframe-source"
python -m gameframe.ioquake3_v2_source_patch "D:\AI\Game Frame\ioq3-gameframe-source" --apply

cd "D:\AI\Game Frame\ioq3-gameframe-source"
$env:Path = "C:\Program Files\CMake\bin;$env:Path"
cmake --build build-gameframe --config Release --parallel 4
```

This rebuilds **ioquake3.exe and cgame.dll**, not just Python. Don't overwrite the known working original build in `D:\AI\Game Frame\ioquake3\`.

## Launch with the rebuilt cgame module

ioquake3 may load `baseq3/vm/cgame.qvm` from the proprietary game data instead of the patched `cgame.dll`. For the V2 renderer override to work, the native `cgame.dll` must be loaded. The build generates `build-gameframe/Release/baseq3/cgame.dll`.

Use a **separate test homepath** and copy the GPL-built cgame DLL there (do not copy game assets):

```powershell
$root = "D:\AI\Game Frame"
$gameframeHome = "$root\ioq3-v2-home"
$bridge = "$root\ioq3-camera-bridge"

New-Item -ItemType Directory -Force "$gameframeHome\baseq3", $bridge
Copy-Item "$root\ioq3-gameframe-source\build-gameframe\Release\baseq3\cgame.dll" "$gameframeHome\baseq3\cgame.dll" -Force
$env:GAMEFRAME_IOQ3_BRIDGE_DIR = $bridge

& "$root\ioq3-gameframe-source\build-gameframe\Release\ioquake3.exe" `
  +set fs_basepath "$root\..\Quake 3 Arena" `
  +set fs_homepath "$gameframeHome" `
  +set vm_cgame 0 `
  +set r_fullscreen 0
```

Confirm Quake III starts, open the console, load `/devmap q3dm1`, then `/where`. If the DLL fails to load, stop here and send the console output; confirm `vm_cgame 0` actually loaded `cgame.dll`. Some builds may require game-code dependencies from the build output. Do not alter the original game binaries.

**Correct the example path** if your Quake III assets do not reside at `D:\AI\Quake 3 Arena`. This launch command points to that known location.

## First V2 camera smoke test

In a **second PowerShell**:

```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_render_camera_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --position 212 2360 56 --pitch 15 --yaw 90 --roll 0 --fov 85
```

**Replace the example xyz with the current /where coordinates.** Check for visible pitch and yaw change independent of the player's position, while gameplay is unpaused.

Return to regular gameplay:

```powershell
python -m gameframe.ioquake3_render_camera_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --reset
```

Response `queued: true` is not camera state readback. If graphics distort, reset the view and return to a safe known player location; do not assume the camera path has collision clearance.

## Still to implement

Camera readback and request IDs; actor focus/target helpers; secure typed sequence controls using the V2 pose protocol; cinematic record/capture; true engine frame-locked timeline; offline camera track persistence; map visibility and collision handling.
