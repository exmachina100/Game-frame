# Windows ioquake3 setup for GameFrame

GameFrame is an AI filmmaking director. ioquake3 is an experimental 3D engine target, not the product UI. **Its game-side cinematic bridge is not implemented yet.**

## Recommended folder

```text
D:\AI\Game Frame\
  Game-frame\          GameFrame source (git repository)
  ioquake3\            engine installation (outside git)
```

You can choose a different directory. No physical or geographic location is required.

## Install the engine

1. Get the official Windows build from https://ioquake3.org/get-it/ .
2. Extract or install it to `D:\AI\Game Frame\ioquake3` (or any directory you prefer). The installer may use its own directory structure; this is only a recommendation.
3. Game content is **not included** with the open-source engine. To run Quake III Arena, use your legally owned game data, notably `baseq3/pak0.pk3`, following https://ioquake3.org/help/players-guide/ . Do not add game assets to GameFrame's Git repository.
4. An alternative for independent experiments is a free standalone id Tech 3 game such as OpenArena, which uses a related engine/fork and separate game assets. It should be treated as its own adapter compatibility test; do not assume base OpenArena files work unmodified with every ioquake3 build.

## Run the read-only check

From PowerShell:

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
powershell -ExecutionPolicy Bypass -File .\scripts\check_ioquake3_setup.ps1
```

To check a custom location:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_ioquake3_setup.ps1 -InstallDir "D:\Games\ioquake3"
```

The script scans for a likely engine executable and reports nearby .pk3 archive counts. It **does not install, download, launch, modify or validate ownership** of any game data. If the executable isn't found it exits with status 2, which is expected before installation.

Engine inspection alone does not establish gameplay, camera movement, actor control, frame stepping or native capture. Those need a real ioquake3-side GameFrame bridge and subsequent local tests.

## Next filmmaking milestone

1. Verify executable + permitted map and player assets.
2. Implement a safe, explicit opt-in game-side command transport.
3. Prove 3D camera transform/readback first, then actor staging and native capture.
4. Record a repeatable 15–30-second scene, preserving per-engine capability flags.
