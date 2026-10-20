# GameFrame ioquake3 native camera bridge — source integration prototype

**Status: source patch and Python transport committed, NOT compiled or validated in the running Windows game.**

The standard ioquake3 executable does not accept GameFrame commands. The native player-client console command `setviewpos` works manually in the user's local `devmap q3dm1` game, but server RCON does not operate the client viewpoint. We therefore need a specially built ioquake3 **client**.

## What the experimental bridge does

- Only when `GAMEFRAME_IOQ3_BRIDGE_DIR` is explicitly set, the patched `CL_Frame` polls `camera_request.txt` roughly every 50 ms.
- Accepts only bounded, numeric `setviewpos X Y Z YAW` requests.
- Inserts the command into the normal Quake III client command buffer.
- Returns `QUEUED` or `REJECTED` in `camera_response.txt`.
- Python provides `IoQuake3CameraBridge.set_view` and a simple CLI.

**QUEUED is not proof that cheats were enabled or that camera movement occurred.** No position readback, interpolation, pitch/roll, arbitrary engine console commands, network port or detached camera exists yet. Commands are *not* frame synchronous.

## Source checkout and Windows build

The patcher edits only a **separate checkout** of the GPL-licensed [ioquake/ioq3](https://github.com/ioquake/ioq3) source; do not patch or overwrite the working game executable.

```powershell
cd "D:\AI\Game Frame"
git clone https://github.com/ioquake/ioq3.git ioq3-gameframe-source
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_source_patch "D:\AI\Game Frame\ioq3-gameframe-source"
python -m gameframe.ioquake3_source_patch "D:\AI\Game Frame\ioq3-gameframe-source" --apply
python -m unittest discover -s tests -v
```

To build the patched client on Windows, install Visual Studio 2022 Community with C++ desktop tools and CMake. Upstream documents the following commands:

```powershell
cd "D:\\AI\\Game Frame\\ioq3-gameframe-source"
cmake -S . -B build-gameframe -G "Visual Studio 17 2022"
cmake --build build-gameframe --config Release
Get-ChildItem ".\\build-gameframe" -Recurse -Filter "ioquake3*.exe" | Select-Object FullName
```

The built executable may need renderer libraries and other runtime files from the same build directory. Run it from its compiled output tree, keeping your original game binary intact. The GameFrame source patch has NOT yet been compiled or locally tested. Do **not** overwrite `D:\AI\Game Frame\ioquake3\ioquake3.x86_64.exe` until the new build works independently.

## First smoke test (only after successful custom compilation)

Create a dedicated local, private command directory:

```powershell
New-Item -ItemType Directory -Force "D:\AI\Game Frame\ioq3-camera-bridge"
$env:GAMEFRAME_IOQ3_BRIDGE_DIR = "D:\AI\Game Frame\ioq3-camera-bridge"
```

Launch the **new patched client** from the same PowerShell environment using the known game-data options:

```powershell
& "PATH_TO_NEW_PATCHED_IOQUAKE3_EXE" +set fs_basepath "D:\AI\Quake 3 Arena" +set fs_homepath "D:\AI\Game Frame\ioquake3" +set r_fullscreen 0
```

Open its console, enter `/devmap q3dm1`, and use `/where` to read a safe current position. In another PowerShell terminal:

```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_camera_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --position 212 2360 56 --yaw 90
```

Those coordinates were observed in an earlier run; refresh using your **current map position** rather than assuming they're still safe. If the command returns `queued: true`, verify the viewpoint visibly rotates. This is the first actual live-bridge verification, and is **not yet completed**.

The bridge directory must be accessible only to trusted local users. The prototype is a basic file queue; don't expose it over a shared directory or network. Do not start two simultaneous Python clients. If the engine crashes with a request pending, stop it before cleaning up stale `camera_request.txt` or `camera_response.txt`.

## Further engineering work

1. Compile/test the patched client on Windows; fix build issues.
2. Introduce bounded request IDs, atomic response publication and proper camera-state readback.
3. Negotiate `set_camera` capability only after live engine verification.
4. Implement a genuine detached camera and measured / frame-accurate motion paths.
5. Add capture, actor staging and MCP execution after their own validation.
