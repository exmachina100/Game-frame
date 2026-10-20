"""Small experimental stdio MCP server, supporting core tools.

Production deployments should migrate transport to the official MCP SDK.
"""
import json
import math
import sys
from pathlib import Path
from .core import Camera, Director
from .stage import RetroStage
from .engines import parse_plan
from .ioquake3 import IoQuake3Adapter

director = Director(RetroStage())


def schema(name, description, fields=None, required=None):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": fields or {},
                            "required": required or [], "additionalProperties": False}}


num = {"type": "number"}
string = {"type": "string"}
integer = {"type": "integer"}
TOOLS = [
    schema("inspect_game", "Describe connected game runtime"),
    schema("inspect_engine_capabilities", "Report native engine capabilities without assuming unimplemented cinematic controls", {"engine": string}, ["engine"]),
    schema("validate_cinematic_plan", "Validate structured cinematic plan against native engine capabilities without execution", {"engine": string, "plan": {"type": "object"}}, ["engine", "plan"]),
    schema("list_scenes", "List available levels"),
    schema("list_actors", "List currently staged actors"),
    schema("load_scene", "Load a level and reset timeline", {"name": string}, ["name"]),
    schema("spawn_actor", "Add actor", {"name": string, "x": num, "y": num}, ["name", "x", "y"]),
    schema("direct_actor", "Move actor between frames", {"name": string, "start": integer, "end": integer, "x": num, "y": num}, ["name", "start", "end", "x", "y"]),
    schema("set_camera", "Place static stage camera", {"x": num, "y": num, "zoom": num}, ["x", "y", "zoom"]),
    schema("play_sequence", "Return validated sequence manifest", {"frames": integer}, ["frames"]),
    schema("capture_sequence", "Export PPM frame sequence", {"frames": integer, "folder": string}, ["frames", "folder"]),
]


def execute(name, args):
    if name in ("inspect_engine_capabilities", "validate_cinematic_plan"):
        if args["engine"] != "ioquake3":
            raise ValueError("Unsupported native engine")
        adapter = IoQuake3Adapter()
        if name == "inspect_engine_capabilities":
            return {"capabilities": adapter.capabilities().describe(), "diagnostics": adapter.diagnostics()}
        return parse_plan(args["plan"]).validate_for(adapter.capabilities())
    if name == "inspect_game":
        return director.adapter.info()
    if name == "list_scenes":
        return {"scenes": director.adapter.info()["scenes"]}
    if name == "list_actors":
        return {"actors": [vars(a) for a in director.actors.values()]}
    if name == "load_scene":
        return director.load_scene(args["name"])
    if name == "spawn_actor":
        return director.spawn_actor(args["name"], args["x"], args["y"])
    if name == "direct_actor":
        return director.direct_actor(args["name"], args["start"], args["end"], args["x"], args["y"])
    if name == "set_camera":
        values = (args["x"], args["y"], args["zoom"])
        if not all(map(math.isfinite, values)) or not 0.1 <= args["zoom"] <= 8:
            raise ValueError("Invalid camera values")
        director.camera = Camera(*values)
        return vars(director.camera)
    if name == "play_sequence":
        return director.manifest(args["frames"])
    if name == "capture_sequence":
        meta = director.manifest(args["frames"])
        folder = args["folder"]
        if not folder or folder in (".", "..") or "/" in folder or "\\" in folder:
            raise ValueError("Use a safe single directory name")
        out = Path("output") / folder
        out.mkdir(parents=True, exist_ok=True)
        for i in range(meta["frames"]):
            (out / f"shot_{i:04d}.ppm").write_bytes(director.render_frame(i))
        return {**meta, "output": str(out)}
    raise ValueError("Unknown tool")


def handle(message):
    if "id" not in message:
        return None
    ident = message["id"]
    method = message.get("method")
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05",
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "gameframe", "version": "0.1.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params") or {}
        try:
            payload = execute(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(payload)}]}
        except (KeyError, ValueError, TypeError) as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def main():
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
            if response is not None:
                print(json.dumps(response), flush=True)
        except (ValueError, TypeError):
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": "Parse error"}}), flush=True)


if __name__ == "__main__":
    main()
