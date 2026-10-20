# GameFrame — AI-native game-engine filmmaking roadmap

## Product direction
GameFrame directs cinematic scenes through native game engines, using an engine-independent shot plan, capability negotiation, actors, cameras, takes, retakes and capture. Pong is a **diagnostic adapter**, not the product's primary interface. Never imply a game adapter has control capabilities that have not been verified.

## Milestone 0 — Director foundation (implemented prototype)
- [x] Procedural 2D director, actor motion, static camera, frame render and PPM export
- [x] Experimental JSON-RPC MCP server for procedural stage
- [x] Engine-neutral `Capabilities`, `ShotCommand`, `CinematicPlan`, validation and dry-run
- [x] Unit tests for protocol, planning and legacy director
- [ ] Confirm GitHub CI results

## Milestone 1 — Native emulation feasibility (partially demonstrated)
- [x] MAME Pong Lua/Python command queue; native screenshot and AVI capture
- [x] Measured frame progress, pause/resume, input-port value readback
- [x] Early dedicated Pong shot editor and script runner (test tooling only)
- [ ] Resolve mismatch between analog input port readback and *visible* paddle movement
- [ ] Implement native engine capability registration against the generic contract
- [ ] Investigate frame-exact MAME method and/or BizHawk movie playback
- [ ] Homebrew test scene with distributable assets

## Milestone 2 — ioquake3 3D production pilot (active priority)
- [x] ioquake3 planning/diagnostics adapter with **zero claimed executable operations**
- [x] Capability-aware example cinematic plan; fails validation until controls exist
- [ ] Identify valid executable and legal local engine/data installation
- [x] Add manual Quake III native console camera-placement and capture smoke-test generators (not RPC)
- [ ] Verify `setviewpos` and native screenshot/demo capture on the user's running engine
- [ ] Build and verify game-side camera bridge and scene state inspection
- [ ] Add stage/actor transform controls with documented limitations
- [ ] Implement repeatable multi-shot timeline and native frame/video capture
- [ ] Produce and visually verify a 15–30 second directed 3D scene

## Milestone 3 — Director workspace and AI narrative
- [ ] Engine-neutral viewport with live engine preview where adapter supports it
- [ ] Character staging, camera rigs, gizmos, per-shot controls, timeline, takes and media bin
- [ ] MCP integration with capability-backed engine actions
- [ ] Narrative -> constrained shot plan, tool-feedback repair, retakes and continuity validation

## Milestone 4 — Classic installed games
- [ ] Max Payne 2 / MAX-FX feasibility
- [ ] Hitman Glacier feasibility
- [ ] License-aware local assets and game-specific adapter design
- [ ] No redistribution of proprietary game assets

## Engineering constraints
- Frame-exact is a capability **per engine**, not a default product promise.
- ioquake3 bridge is **not implemented**: engine_cli only diagnoses, it does not launch or control a game.
- No game executable, ROM or proprietary asset is bundled.
- Cinematic plans should fail early when adapters lack requested operations.
- Prefer thin engine adapters and reusable director/shot semantics over game-specific main UI.

## Camera pilot
See [ioquake3 camera pilot](IOQUAKE3_CAMERA_PILOT.md). The console cfg exporter does not imply native camera RPC or frame-accurate automation.

## Developer commands
```powershell
python -m unittest discover -s tests -v
python -m gameframe.engine_cli inspect ioquake3
python -m gameframe.engine_cli inspect ioquake3 --exe "C:\\path\\to\\ioquake3.exe"
python -m gameframe.engine_cli validate docs/examples/alley_scene.json ioquake3
```
The final validation command is **expected to exit with code 2** while the actual ioquake3 bridge is unavailable. This is intentional truthful capability reporting.
