# GameFrame

An experimental AI filmmaking director for retro, arcade, and classic 3D games. **The project includes a procedural stage and an experimental live MAME bridge; a native 3D filmmaking adapter remains a development priority.** It renders every frame deterministically; no AI image-to-video model is required.

## Installed features
- Python 3.11+ core director with frame-indexed actor movement and static camera
- Experimental JSON-RPC stdio MCP server with nine tools
- Native procedural 320x180 PPM rendering
- A twelve-second sample with two actors
- Unit tests, GitHub Actions CI, and a staged integration roadmap

## Quick start
```bash
git clone https://github.com/exmachina100/Game-frame.git
cd Game-frame
python -m unittest discover -s tests -v
python -m gameframe.demo
```

The demo creates 144 frames in `output/demo/`. Convert frames to MP4 with FFmpeg:
```bash
ffmpeg -framerate 12 -i output/demo/shot_%04d.ppm -c:v libx264 -pix_fmt yuv420p output/demo.mp4
```

Launch MCP over standard input/output:
```bash
python -m gameframe.mcp_server
```

Example MCP client config, with absolute path substituted:
```json
{
  "mcpServers": {
    "gameframe": {
      "command": "python",
      "args": ["-m", "gameframe.mcp_server"],
      "cwd": "/absolute/path/to/Game-frame"
    }
  }
}
```

The procedural director exposes nine legacy MCP tools, alongside `inspect_engine_capabilities` and `validate_cinematic_plan` for engine-neutral cinematic planning. Existing legacy tools: `inspect_game`, `list_scenes`, `list_actors`, `load_scene`, `spawn_actor`, `direct_actor`, `set_camera`, `play_sequence`, and `capture_sequence`.

## Architecture
```
AI narrative planner (planned)
    -> MCP tools
    -> Deterministic Director
    -> Runtime adapter
         -> Procedural RetroStage (implemented)
         -> MAME / BizHawk (planned)
         -> ioquake3 (planned)
         -> MAX-FX feasibility study (planned)
    -> Native render frames -> FFmpeg
```

The MCP server is a deliberately small experimental implementation. Production use should move to the official Python MCP SDK, stronger schema validation, and engine-specific capability negotiation.

See [development roadmap](docs/ROADMAP.md).

## IP / safety
The demo uses procedurally created shapes only. Do not commit proprietary installed game files, ROMs or extracted commercial assets. Game integrations should operate against legitimate local installations with applicable permissions and licensing.

## Experimental MAME control bridge

The Lua/Python bridge has been exercised against a user-run MAME 0.289 Pong installation, including input-port readback, screenshots, AVI recording, and measured frame advancement. Native paddle input values match commands but visual paddle movement was not observed in uploaded screenshots. Frame-exact native advancement is unresolved. See [MAME setup](docs/MAME.md). MAME is a research adapter, not the product UI.


## Engine-neutral cinema planning (new)

GameFrame now has a typed capability contract and cinematic shot-plan schema. These components are **planning and validation infrastructure**, not a working ioquake3 game bridge.

```powershell
python -m gameframe.engine_cli inspect ioquake3
python -m gameframe.engine_cli validate docs/examples/alley_scene.json ioquake3
```

Validation of the sample alley sequence intentionally reports unsupported operations and exits with code 2: the ioquake3 engine-side camera/actor bridge has not been implemented. The capability inspection and shot-plan checks are also available as MCP tools.

See the [updated filmmaking roadmap](docs/ROADMAP.md). The next integration milestone is a legally installed ioquake3 environment with validated 3D camera control, then actors, scene capture and cinematic timeline.
