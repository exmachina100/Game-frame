# Stage 2A — Read-only ioquake3 scene snapshot probe

Source feature implemented; **not yet compiled or run on the user's Windows machine**.

Source review: `ioquake/ioq3` uses `CL_GetSnapshot` and `cl.snap`, plus a bounded `cl.parseEntities` circular buffer. The opt-in patch reads only the current valid client snapshot after `CA_ACTIVE`, emits its server time and at most `MAX_ENTITIES_IN_SNAPSHOT` entities as lines with entity number, numeric eType, `pos.trBase`, legsAnim, torsoAnim and frame. This is **not** a current interpolated rendered transform, and no actor identities, animation names, visibility or actions are inferred.

## Windows build, only once
Close Quake III first.

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
python -m gameframe.stage2_scene_probe_patch "D:\AI\Game Frame\ioq3-gameframe-source"
python -m gameframe.stage2_scene_probe_patch "D:\AI\Game Frame\ioq3-gameframe-source" --apply
cd "D:\AI\Game Frame\ioq3-gameframe-source"
cmake --build build-gameframe --config Release --parallel 4
```

Launch the rebuilt ioquake3 executable with the *same* bridge environment variable, filesystem settings, `sv_pure 0`, `vm_cgame 0`, `q3dm1` and existing native camera DLL as in V7. Keep the game running and console closed.

## Read-only snapshot
In a second PowerShell window:
```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.stage2_scene_probe_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --output "output\stage2_snapshot_01.json"
```

The output contains `available`, `server_time_ms`, `entities`, `positions_are_trajectory_bases`, `actors_identified:false`, and `actions_supported:false`.

If build fails, share the **first compiler error**. The source bridge and response parser have Python tests but the native patch remains **unverified** until Windows compilation and live inspection. Avoid running this probe simultaneously with filming because the underlying bridge uses one request/reply pair.

Next: compare multiple snapshots and identify actual player/actor `eType` semantics, then expose actor trajectories and animation states with provenance before authorizing scripted actions.
