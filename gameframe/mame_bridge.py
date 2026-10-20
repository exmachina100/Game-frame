"""Local file-queue transport for a separately running MAME Lua script.

The bridge is deliberately opt-in: it never launches MAME, finds ROMs, or
writes emulated memory. Communicates through a private directory containing
one request and one response per command, with atomic file replacement.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
import json
import os
import re
import time
import uuid

_ALLOWED = {"status", "pause", "resume", "step_once", "reset_step_tracking", "list_inputs", "input_capabilities", "set_paddle", "snapshot", "record_start", "record_stop"}
_SAFE_ID = re.compile(r"^[a-f0-9]{32}$")


@dataclass
class MameBridge:
    directory: Path
    timeout: float = 5.0

    def __post_init__(self) -> None:
        self.directory = Path(self.directory).expanduser().resolve()
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    def request(self, action: str, **params) -> dict:
        if action == "set_paddle":
            if type(params.get("paddle")) is not int or params["paddle"] not in (0, 1):
                raise ValueError("paddle must be 0 or 1")
            if type(params.get("value")) is not int or not 0 <= params["value"] <= 255:
                raise ValueError("value must be an integer from 0 to 255")
        elif params:
            raise ValueError("This action accepts no parameters")
        if action not in _ALLOWED:
            raise ValueError(f"Unsupported MAME action: {action}")
        if not self.directory.is_dir():
            raise FileNotFoundError(f"MAME bridge directory missing: {self.directory}")
        request_id = uuid.uuid4().hex
        assert _SAFE_ID.fullmatch(request_id)
        command = {"id": request_id, "action": action, **params}
        request_path = self.directory / f"request_{request_id}.json"
        response_path = self.directory / f"response_{request_id}.json"
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.directory,
                                prefix=".pending_", delete=False) as f:
            temporary = Path(f.name)
            json.dump(command, f)
            f.write("\n")
        os.replace(temporary, request_path)
        deadline = time.monotonic() + self.timeout
        try:
            while time.monotonic() < deadline:
                if response_path.exists():
                    try:
                        response = json.loads(response_path.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, PermissionError, OSError):
                        # Older bridge versions can expose a file before writing completes.
                        time.sleep(0.02)
                        continue
                    if response.get("id") != request_id:
                        raise ValueError("Bridge response ID mismatch")
                    if not response.get("ok", False):
                        raise RuntimeError(response.get("error", "MAME command failed"))
                    return response
                time.sleep(0.02)
            raise TimeoutError("MAME did not respond; verify -autoboot_script and bridge directory")
        finally:
            for path in (request_path, response_path):
                try:
                    path.unlink(missing_ok=True)
                except PermissionError:
                    # Windows can still hold a handle briefly after Lua closes it.
                    pass
