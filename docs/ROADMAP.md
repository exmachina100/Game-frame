# GameFrame development roadmap

## Milestone 0: deterministic director foundation
- [x] Minimal MCP stdio tool server
- [x] Frame-exact actor movement and static cameras
- [x] Procedural 2D demo renderer, with no commercial game assets
- [x] Shot frame export in PPM
- [x] Unit tests
- [ ] Validate CI on GitHub

## Milestone 1: real arcade/retro games
- [ ] Capability-based adapter protocol for emulator bridges
- [ ] MAME Lua: frame step, controller, safe scene state, capture
- [ ] BizHawk: Lua and TAS/movie replay
- [ ] Licensed homebrew test titles

## Milestone 2: engine-native 3D
- [ ] ioquake3 camera / actor bridge
- [ ] Scriptable cinematography and multishot editing
- [ ] Repeatability and capture verification

## Milestone 3: narrative director
- [ ] Narrative -> constrained shot plans
- [ ] Actor, camera, animation capability feedback
- [ ] Story filler generation, retakes, continuity checks

## Milestone 4: classic installed games
- [ ] MAX-FX / Max Payne 2 feasibility spike
- [ ] Hitman Glacier tooling reconnaissance
- [ ] Local license-aware asset discovery, never redistribute commercial assets

Current program is a **simulated 2D environment**, not yet an adapter for an installed commercial game.
