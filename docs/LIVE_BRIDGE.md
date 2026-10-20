# Live bridge integration test (MAME 0.289)

Your ROM-free Pong probe confirmed Lua startup, periodic callbacks, JSON, LuaFileSystem and video methods. The next test runs MAME with the full bridge and calls status, snapshot, record start, and record stop from Python.

Run in PowerShell:
```powershell
cd "D:\AI\Game Frame\Game-frame"
git pull origin main
powershell -ExecutionPolicy Bypass -File .\scripts\test_mame_bridge.ps1
```

This starts a disposable MAME Pong process and stops only that process after the test. Snapshots/recordings use the standard MAME output folders under `C:\MAME\snap` (configuration can vary). The local command directory is deleted afterward. No arcade ROM required.

A successful test prints `PASS: Live MAME bridge command exchange succeeded`. On error, paste the stdout/stderr report.

**Still not supported:** arbitrary sprite staging, emulator input injection, memory editing, deterministic per-frame replay, or automatic narrative scripting. Those need separate game-aware adapters.
