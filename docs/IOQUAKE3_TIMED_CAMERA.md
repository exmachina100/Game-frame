# GameFrame — Timed ioquake3 Camera Takes

**Status:** GameFrame's Python camera command was visibly verified by the user on the compiled ioquake3 client. This sequencer is newly implemented, but its live timed playback has not yet been tested on that user's machine.

## Current scope

The sequencer calls the existing Python-to-client camera bridge at a selected wall-clock sample rate (1–15 commands/sec, default 8). It interpolates between keyframes using smoothstep easing and shortest-arc yaw rotation. This controls the **player viewpoint**, not a detached camera.

The first sample is sent at time 0; commands are scheduled against a monotonic clock. Individual bridge waits and engine polling can delay samples. A QUEUED result confirms command admission, not applied pose, exact frames, or render/capture completion.

**No collision clearance, pitch/roll, frame stepping, synchronized shots or movie export is present.** Preserve the same validated xyz across all keyframes until safe path planning is implemented.

## First live test

Make sure the *patched* ioquake3 executable is running and has `GAMEFRAME_IOQ3_BRIDGE_DIR` set. Load `/devmap q3dm1` and use `/where`. Edit the JSON below to use the live `/where` xyz, not arbitrary scene coordinates. The included sample position `212 2360 56` comes from an earlier run and may not fit the current spawn/map.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main

# Preview first. No command is sent.
python -m gameframe.ioquake3_camera_sequence_cli docs/examples/quake_camera_orbit_safe.json

# Then, only if the patched game is running on a valid devmap.
python -m gameframe.ioquake3_camera_sequence_cli docs/examples/quake_camera_orbit_safe.json --dir "D:\AI\Game Frame\ioq3-camera-bridge" --run
```

Exit sequence playback by pressing Ctrl+C in the terminal. Do not run several simultaneous camera controllers; the experimental local bridge has only one request slot and no request IDs. If a previous invocation timed out, inspect and clear stale request/response files with the game stopped.

### JSON example

```json
{
  "keyframes": [
    {
      "time": 0,
      "position": [
        212,
        2360,
        56
      ],
      "yaw": 0
    },
    {
      "time": 2,
      "position": [
        212,
        2360,
        56
      ],
      "yaw": 90
    },
    {
      "time": 4,
      "position": [
        212,
        2360,
        56
      ],
      "yaw": 180
    }
  ]
}
```

`--rate 5` can reduce load; `--linear` changes ease; `--allow-translation` allows position interpolation but is **unsafe in map geometry**. Do not opt in for the first test.

### Testing

```powershell
python -m unittest discover -s tests -v
```

The tests use a fake bridge; they do not prove visual smoothness on a running game.

## Next engineering work

Add readback and acknowledgement IDs, use game-engine simulation timing rather than wall clock, introduce real 6-DOF free camera and map-aware path clearance, and synchronize native frame capture and actor directing.
