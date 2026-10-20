"""Client-side local file transport for a *custom-compiled* ioquake3 camera bridge.

Transport acknowledgement QUEUED means accepted by the command buffer, not
that the camera visibly moved. Requires a separate opt-in compiled engine build.
"""
from __future__ import annotations
from pathlib import Path
import math
import os
import time

class IoQuake3CameraBridge:
    def __init__(self, directory: str | Path, timeout: float = 3.0):
        self.directory = Path(directory).resolve()
        self.timeout = float(timeout)
        if not self.directory.is_dir() or self.timeout <= 0:
            raise ValueError("Bridge directory must exist and timeout be positive")

    def set_view(self, x: float, y: float, z: float, yaw: float) -> dict:
        nums = (x, y, z, yaw)
        if any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 100000 for n in nums):
            raise ValueError("Camera coordinates must be finite bounded numbers")
        request = self.directory / "camera_request.txt"
        response = self.directory / "camera_response.txt"
        if request.exists():
            raise RuntimeError("Previous camera command is pending")
        response.unlink(missing_ok=True)
        temporary = self.directory / "camera_request.tmp"
        try:
            with temporary.open("x", encoding="ascii") as file:
                file.write("setviewpos " + " ".join(f"{float(n):.3f}" for n in nums) + "\n")
            os.replace(temporary, request)
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                if response.exists():
                    state = response.read_text(encoding="ascii").strip()
                    response.unlink(missing_ok=True)
                    if state != "QUEUED":
                        raise RuntimeError(f"Camera command rejected by engine: {state}")
                    return {"queued": True, "view": list(nums), "verified": False}
                time.sleep(.02)
            raise TimeoutError("No native ioquake3 bridge reply. Use a custom-compiled executable with the GameFrame patch.")
        finally:
            temporary.unlink(missing_ok=True)
            # Do NOT remove request on timeout: the engine might still process it.
