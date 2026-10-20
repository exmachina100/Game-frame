# GameFrame V7 Phase 2A — Native static-world collision preflight

**Source committed, not yet compiled or live validated.** This opt-in patch queries ioquake3's native BSP collision model through `CM_BoxTrace`. It reports fraction/startsolid/allsolid, and the Python tool divides a camera segment into shorter checked segments.

It checks static world collision **only**. It does not guarantee render visibility, dynamic entity clearance, actor tracking, volumetric clearance, safety margins or fully raycast-aware orbit movement. A point-sized trace through BSP cannot clear a full-size camera rig, and may miss decorative render surfaces.

## Files

- `gameframe/ioquake3_v7_world_trace_patch.py`: adds `gftrace sx sy sz ex ey ez` to V4-patched client `cl_main.c`; replies with `TRACE fraction startsolid allsolid`.
- `gameframe/ioquake3_v7_world_trace.py`: bounded request/readback, `inspect_path` collision checking.
- `gameframe/ioquake3_v7_world_trace_cli.py`: opt-in preflight command; exit 0 if clear, 2 if blocked.
- `tests/test_ioquake3_v7_world_trace.py`: source patch and fake-bridge tests.

## Step 1: tests

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
python -m unittest discover -s tests -v
```

## Step 2: patch and rebuild the modified client

Close Quake III first. This patch must be applied **once** to your already V4-patched standalone source checkout; it does not change the `cgame.dll`.

```powershell
python -m gameframe.ioquake3_v7_world_trace_patch "D:\AI\Game Frame\ioq3-gameframe-source"
python -m gameframe.ioquake3_v7_world_trace_patch "D:\AI\Game Frame\ioq3-gameframe-source" --apply
cd "D:\AI\Game Frame\ioq3-gameframe-source"
cmake --build build-gameframe --config Release --parallel 4
```

If build fails, send the compiler diagnostics **before** trying any runtime trace. Revert only the local patch if necessary; your GitHub camera source is unaffected.

## Step 3: launch

Same V4/V7 working engine with bridge env and native `cgame.dll`, `sv_pure 0`, `vm_cgame 0`, `cg_draw2D 0`, `cg_drawGun 0` and `con_notifytime 0`. Load `/devmap q3dm1`, leave console closed.

## Step 4: preflight one known fixed position

Use a separate PowerShell:

```powershell
cd "D:\AI\Game Frame\Game-frame"
python -m gameframe.ioquake3_v7_world_trace_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --start 212 2360 56 --end 212 2360 56
```

This tests static point contents at that camera position. If it reports blocked, stop: the point could be inside a BSP brush, and the render camera may still appear to show the arena because it is not subject to player collision. If clear, test a *small nearby segment*, rather than an uninspected full dolly:

```powershell
python -m gameframe.ioquake3_v7_world_trace_cli --dir "D:\AI\Game Frame\ioq3-camera-bridge" --start 212 2360 56 --end 212 2380 56
```

Do **not** run unverified camera translation just because a single point trace clears. The report excludes dynamic collision and visual occlusion and cannot promise a cinematographically usable shot.

## Next

Native visibility/solid-volume queries, camera frustum and collision padding; link this preflight to V3/V4/V6 translation guardrails; then implement deterministic frame-time renderer capture. The latter remains entirely pending.
