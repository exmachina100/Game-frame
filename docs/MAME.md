# MAME integration (experimental)

MAME exposes Lua scripting including session control and video capture. GameFrame's first native MAME connector is a **local file-queue bridge** supporting status, pause, resume, snapshot, record start and record stop. It does not yet manipulate sprites, read/write memory, inject input, or synchronize individual frames.

## Requirements
- An installed version of MAME with Lua and `lfs` and `json` modules accessible in its Lua runtime (availability varies by MAME build).
- A game/system you may legally run. GameFrame distributes no ROMs.
- A writable directory accessible to both MAME and the Python process.

## Windows PowerShell
```powershell
New-Item -ItemType Directory -Force C:\gameframe-bridge
$env:GAMEFRAME_BRIDGE_DIR="C:\gameframe-bridge"
mame <system> -autoboot_script C:\path\to\Game-frame\mame\gameframe_bridge.lua
```

## Python
```python
from pathlib import Path
from gameframe.mame_bridge import MameBridge
bridge = MameBridge(Path(r"C:\gameframe-bridge"), timeout=5)
print(bridge.request("status"))
print(bridge.request("snapshot"))
```

## Limitations
- This is a filesystem-based prototype, not a low-latency frame synchronous transport.
- MAME is not launched automatically, so the user's installed executable and game assets remain under their control.
- MAME's Lua scripting APIs are not guaranteed stable; verify the installed version before relying on this bridge.
- MAME's snapshot and recording outputs use its own configured folders.
- The Python side is tested using a simulated Lua responder; **an end-to-end MAME run has not yet been performed**.

See https://docs.mamedev.org/luascript/index.html and https://docs.mamedev.org/luascript/ref-core.html .
