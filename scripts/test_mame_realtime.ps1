# Verify bounded real-time frame progression in ROM-free MAME Pong.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_realtime_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "mame_stdout.log"
$stderr=Join-Path $dir "mame_stderr.log"
$proc=$null
try {
  $args="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $args -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
from gameframe.realtime import run_until_frames
b=MameBridge(Path(sys.argv[1]),timeout=2.5)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY:",b.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.25)
else:
    raise RuntimeError("MAME did not respond")
for target in (10,20,30):
    result=run_until_frames(b,target,timeout=8)
    print(f"TARGET={target} ACTUAL={result.deltas} REACHED={result.reached_target} PAUSED={result.paused}",flush=True)
    if not result.reached_target or not result.paused:
        sys.exit(2)
print("PASS: three bounded real-time runs completed; overshoot is expected, frame-perfect replay is not claimed",flush=True)
'@ | python - $dir $TimeoutSeconds
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 30 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 30 }
    throw "Real-time test failed (Python $code)"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
