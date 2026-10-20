# Verify MAME screen frame delta and discover controls (no ROM required).
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=20)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_frames_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$proc=$null
try {
  $args="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $args -WorkingDirectory (Split-Path $MameExe) -PassThru
  @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
b=MameBridge(Path(sys.argv[1]),timeout=2)
deadline=time.monotonic()+int(sys.argv[2])
while True:
    try:
        baseline=b.request("pause")["info"]
        before=b.request("status")["info"]
        print("BEFORE:",before,flush=True)
        inputs=b.request("list_inputs")["info"]["ports"]
        print("INPUT PORTS:",inputs[:8],flush=True)
        b.request("step_once")
        time.sleep(.3)
        after=b.request("status")["info"]
        print("AFTER:",after,flush=True)
        bframes=before.get("screen_frames",{})
        aframes=after.get("screen_frames",{})
        delta={tag:aframes[tag]-v for tag,v in bframes.items() if tag in aframes}
        print("FRAME DELTA:",delta,flush=True)
        print("PAUSED AFTER:",after["paused"],flush=True)
        if delta and all(v==1 for v in delta.values()) and after["paused"]:
            print("PASS: observed one screen frame increment and paused state",flush=True)
        else:
            print("INCONCLUSIVE: step not verified as exactly one screen frame",flush=True)
        sys.exit(0)
    except TimeoutError:
        if time.monotonic()>=deadline: raise
        time.sleep(.2)
'@ | python - $dir $TimeoutSeconds
  if ($LASTEXITCODE -ne 0) { throw "Frame probe failed (Python exit $LASTEXITCODE)" }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
