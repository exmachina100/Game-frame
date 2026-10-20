# GameFrame — Stage 2: AI-native scene directing

## Gate decision (2026-10-21)

**Move forward now.** V7.5 has an accepted MP4 workflow: two visually approved camera motions (dolly and crane), static-world point collision preflight, 64 captured JPEG frames, and an eight-second H.264 film. V8 engine frame-synchronization remains open and should be developed in parallel; it is NOT a requirement for the first Stage 2 prototype.

Only **two further camera validations** are planned: (1) recording quality/time-base integration smoke test when a frame-stepped backend actually exists; (2) one scene-to-MP4 acceptance test. No more standalone dolly/crane demos. No invented guarantee that frame-accurate capture is available.

## Stage 2 objective

Create a director that converts a creative brief into a sequence of **scene beats**, **actor actions**, **shot intents**, **camera choices**, and **recording directives**. The engine must report capabilities rather than hallucinate actor control.

### Stage 2A — machine-readable production contract (next)

Inputs:
- scene concept, narrative objective, duration, location/map, mood
- actor roles and *desired* actions (not presumed supported)
- ordered beats with subject, action, start/end times
- shot intent (establishing, follow, reveal, reaction, insert)
- camera constraints: target subject or surveyed XYZ; shot types; clearance mode
- output profile: fps, resolution, soundtrack policy

Outputs:
- validated `ProductionBrief` and `ShotPlan`
- separate `supported`, `unsupported`, `requires_user_input` capability report
- camera-only fallback if actor choreography is not available
- executable adapter plan only for features actually supported
- reproducible manifest and review notes

Safety & provenance:
- never infer arbitrary game-world subject coordinates
- require explicit consent for engine actions
- validate numbers, scene duration, asset paths, and bounded actor commands
- protect the existing GitHub V6/V7 camera execution path; feature-gate new adapters

### Stage 2B — actors and scene state

Inspect ioquake3 game module and supported NPC/player controls. Build a read-only scene probe first: map, entities, actor transforms and animation states with timestamps. Then add controlled actor action playback in an isolated test map. Distinguish a scripted test actor from a live opponent or uncontrolled simulation.

### Stage 2C — timeline/director

A timeline where narrative beats bind to actors, movement, cameras, light and audio tracks. Allow retiming, re-framing, reviewing and exporting. Introduce a composition preview with tracked targets, but do not promise automated visibility before occlusion queries are integrated.

### Stage 2D — AI planning

Use model output as a proposal, not an executable command. Validate and normalize the JSON scene plan through a deterministic layer; reject unsupported tools and dangerous state changes. Record prompts, edits, approvals and generated shot manifests.

### Stage 2E — video pipeline

Keep V7.5 capture available while developing deterministic 24/30 fps in an opt-in engine branch. Test simulation time, event ordering, raster capture and output duration; replace the V6 sequential screenshot path only after acceptance tests pass.

## Minimum Stage 2 demo

**Arena: Arrival and Reveal** — 12–20 second three-beat sequence. One establishing view, one *declared* actor entrance (or clearly marked placeholder if actor APIs are unavailable), one reveal/reaction shot. No arbitrary orbit target. Output: shot plan JSON, capability report, preview, MP4, and a review manifest. The camera-only fallback must be usable immediately.

## Acceptance criteria

1. A user describes a scene and receives valid ordered beats and constraints.
2. Engine probes report real capabilities; no fictitious actor movement.
3. Camera shot locations pass available static BSP preflight before motion playback.
4. A preview records planned vs actual shot timings and unresolved features.
5. Camera-only fallback exports a video using V7.5.
6. Any unsupported actor action is visible in the report, never silently treated as executed.
7. Only two camera validation rounds remain before Stage 2 acceptance (recording improvement and integrated film test); further camera tests require evidence of a newly found defect.
