"""ioquake3 feasibility adapter.

Reports only verified *planning* support until a native game-side bridge exists.
No fake free-camera or actor-control commands: these need engine integration.
"""
from __future__ import annotations
from pathlib import Path
from .engines import Capabilities

class IoQuake3Adapter:
    def __init__(self, executable: str | Path | None = None):
        self.executable = Path(executable) if executable is not None else None

    def capabilities(self) -> Capabilities:
        # All cinematic operations remain unavailable until implemented and
        # validated on the user's ioquake3 build and legitimate game assets.
        return Capabilities(engine="ioquake3", operations=frozenset(),
                            frame_exact=False, native_3d=True)

    def diagnostics(self) -> dict:
        exe = self.executable
        return {"engine": "ioquake3",
                "executable": str(exe) if exe else None,
                "executable_found": bool(exe and exe.is_file()),
                "connection": "not_connected",
                "native_bridge": "not_implemented",
                "next_step": "Verify local executable, permissibly available content, and develop game-side cinematic bridge"}

    def execute(self, operation: str, arguments: dict) -> dict:
        raise NotImplementedError("ioquake3 game-side cinematic bridge has not been implemented")
