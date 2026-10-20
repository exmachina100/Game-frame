# Diagnostic screen-frame and input discovery probe for MAME 0.289.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_frames_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "mame_stdout.log"
$stderr=Join-Path $dir "mame_stderr.log"
$proc=$null
try {
  Write-Host "GameFrame frame verification: starting ROM-free Pong..." -ForegroundColor Cyan
  $arguments="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $arguments -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
b=MameBridge(Path(sys.argv[1]),timeout=3)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        status=b.request("status")["info"]
        print("BRIDGE READY:",status,flush=True)
        break
    except TimeoutError:
        print("Waiting for MAME bridge startup...",flush=True)
else:
    print("FAILED: no status response after startup deadline",flush=True)
    sys.exit(2)
print("PAUSE:",b.request("pause")["info"],flush=True)
before=b.request("status")["info"]
print("BEFORE:",before,flush=True)
try:
    inputs=b.request("list_inputs")["info"]["ports"]
    print("INPUT PORTS:",inputs[:8],flush=True)
except Exception as exc:
    print("INPUT DISCOVERY ERROR:",repr(exc),flush=True)
try:
    print("STEP:",b.request("step_once")["info"],flush=True)
    time.sleep(.35)
    after=b.request("status")["info"]
    print("AFTER:",after,flush=True)
    initial=before.get("screen_frames",{})
    final=after.get("screen_frames",{})
    delta={key: final[key]-value for key,value in initial.items() if key in final}
    print("FRAME DELTA:",delta,flush=True)
    print("PAUSED AFTER:",after.get("paused"),flush=True)
    print("RESULT:", "CONFIRMED" if delta and all(x==1 for x in delta.values()) and after.get("paused") else "INCONCLUSIVE",flush=True)
except Exception as exc:
    print("FRAME INSPECTION ERROR:",repr(exc),flush=True)
    sys.exit(3)
'@ | python - $dir $TimeoutSeconds
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    Write-Host "MAME stdout (last 50 lines):" -ForegroundColor Yellow
    if (Test-Path $stdout) { Get-Content $stdout -Tail 50 }
    Write-Host "MAME stderr (last 50 lines):" -ForegroundColor Yellow
    if (Test-Path $stderr) { Get-Content $stderr -Tail 50 }
    throw "MAME frame diagnostic failed with Python exit $code"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
