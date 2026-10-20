# GameFrame

An experimental AI filmmaking director for retro, arcade, and classic 3D games. **The current implementation is a procedural 2D stage, not yet a real-game adapter.** It renders every frame deterministically; no AI image-to-video model is required.

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

Nine exposed MCP tools: `inspect_game`, `list_scenes`, `list_actors`, `load_scene`, `spawn_actor`, `direct_actor`, `set_camera`, `play_sequence`, and `capture_sequence`.

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
