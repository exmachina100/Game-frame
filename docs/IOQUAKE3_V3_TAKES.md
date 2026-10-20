# GameFrame V3 — six-axis cinematic take runner

**Source code and tests committed, but V3 playback has not yet been exercised on the user's machine.** V2's independent render camera, pitch/yaw/roll and FOV were visually confirmed by the user. The earlier timed sequence was the **V1 setviewpos** path; this V3 runner is the first timed path using the independent V2 **gfview** interface.

## Supported now
- JSON takes with name and 2–64 absolute time keyframes (0–300 seconds).
- Render-camera position, pitch, yaw, roll, and FOV interpolation, eased or linear.
- Shortest-arc yaw/roll interpolations.
- Wall-clock pacing 1–15 Hz; each command uses the already verified local bridge.
- CLI dry-run and live modes, with opt-in JSON take manifest.
- Automatically queues `gfreset` after live playback, including interruptions.
- Translation is refused unless explicitly enabled, since map geometry clearance is **not** implemented.

## First test — same safe position, 12 seconds

Launch the *patched client with native cgame.dll loaded*, `sv_pure 0` and the existing `GAMEFRAME_IOQ3_BRIDGE_DIR` environment variable. Load `/devmap q3dm1`. Do not launch multiple camera controllers at the same time.

The sample take is deliberately **stationary at** `212,2360,56` to avoid map traversal. This was a previous known camera test point but does not guarantee clearance across sessions. If the view clips geometry, reset and update *all* sample keyframes to a known unobstructed position.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v

# Read-only preview
python -m gameframe.ioquake3_v3_takes_cli docs/examples/quake_v3_opening.json

# Execute using the native render-camera bridge and write planned/queued poses
python -m gameframe.ioquake3_v3_takes_cli docs/examples/quake_v3_opening.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run --manifest "takes/arena_opening.json"
```

Expected live output: `mode: live`, `sample_count: 97`, `queued_count: 97` at 8 Hz, if every camera command is accepted. Successful queue acknowledgements are **not readback of rendered frames**. Inspect the game window for motion and zoom.

## Dolly / crane / translation experiments

Update some keyframes' XYZ to different points, and run the CLI with `--allow-translation`. **This can move the renderer into walls, invisible volumes or voids.** Only test near inspected safe regions. The camera does not change the physics actor/player location. `--rate 5` reduces commands per second.

## Limitations and next milestones

This is a **camera-take prototype**, not a complete video production engine. There is no capture trigger, rendered-frame count, deterministic engine timeline, true camera-state feedback, actor direction, or viewport/UI yet. The manifest logs planned positions, command times and queue acknowledgements; it is not an exported movie. On interrupt, the program attempts reset but cannot guarantee recovery if the engine bridge itself is down. Manual recovery: `python -m gameframe.ioquake3_render_camera_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --reset`.

Next: map-aware clearance; request ID and applied-state readback; bounded cinematic dolly/crane helpers; reliable frame capture/video synchronization; named take management and actor performance.
