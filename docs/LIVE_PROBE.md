# Live Lua verification on Windows

After cloning / pulling the GameFrame repository, launch the read-only probe:

```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
powershell -ExecutionPolicy Bypass -File .\scripts\probe_mame.ps1
```

It starts `C:\MAME\mame.exe` without loading a game ROM, passes `mame/probe.lua` via `-autoboot_script`, and checks that MAME executes Lua. It reports API and optional module availability, then shuts down only the MAME process the script started.

Expected report begins with `gameframe_probe=1`. If no file appears, MAME may not run autoboot scripts in its empty-driver frontend. We can instead test after selecting a user-owned system.

This test intentionally does not send gameplay commands, access game assets or save videos. Lua and Python adapters should only be connected after an actual successful probe. The original experimental bridge presently assumes `json` and `lfs` modules are available; the probe explicitly tests those assumptions and helps choose a compatible transport.
