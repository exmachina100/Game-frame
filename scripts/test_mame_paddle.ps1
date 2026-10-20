# Live Pong paddle movement test (native MAME set_value).
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_paddle_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "stdout.log"
$stderr=Join-Path $dir "stderr.log"
$proc=$null
try {
  $arguments="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $arguments -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
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
        time.sleep(.2)
else:
    raise RuntimeError("MAME did not start")
print("INITIAL READBACK:",b.request("read_paddles")["info"],flush=True)
for paddle,value in [(0,32),(1,224),(0,224),(1,32),(0,128),(1,128)]:
    result=b.request("set_paddle",paddle=paddle,value=value)
    print("PADDLE:",result["info"],flush=True)
    run=run_until_frames(b,10,timeout=8)
    print("  FRAMES:",run.deltas,"PAUSED:",run.paused,flush=True)
    print("  LIVE READBACK:",b.request("read_paddles")["info"],flush=True)
print("COMMANDS ACCEPTED: inspect MAME window for actual paddle movement",flush=True)
'@ | python - $dir $TimeoutSeconds
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 30 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 30 }
    throw "Paddle test failed (Python $code)"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
