# MAME Pong native-input visual verification.
# Captures a screenshot after each sustained extreme paddle pose.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_visual_"+[guid]::NewGuid().ToString("N"))
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
b=MameBridge(Path(sys.argv[1]),timeout=3)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY:",b.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.25)
else:
    raise RuntimeError("MAME Pong did not respond")
poses=[("TOP",0,0),("BOTTOM",255,255),("SPLIT",0,255),("INVERSE",255,0),("CENTER",128,128)]
for label,left,right in poses:
    b.request("pause")
    b.request("set_paddle",paddle=0,value=left)
    b.request("set_paddle",paddle=1,value=right)
    result=run_until_frames(b,90,timeout=10)
    readback=b.request("read_paddles")["info"]["paddles"]
    actual={int(x["paddle"]):x.get("port_read") for x in readback}
    if actual!={0:left,1:right}:
        raise RuntimeError(f"{label} readback mismatch: {actual}")
    screenshot=b.request("snapshot")["info"]
    print(f"POSE={label} EXPECTED=({left},{right}) INPUT_READBACK={actual} FRAME_ADVANCE={result.deltas} SCREENSHOT={screenshot}",flush=True)
print("DONE: screenshots saved in MAME configured snap directory. Compare paddle pixels between images.",flush=True)
'@ | python - $dir $TimeoutSeconds
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 40 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 40 }
    throw "Pong visual probe failed (Python $code)"
  }
  Write-Host "Newest MAME PNG screenshots:" -ForegroundColor Cyan
  $snap=Join-Path (Split-Path $MameExe) "snap\pong"
  if (Test-Path $snap) {
    Get-ChildItem $snap -Filter *.png | Sort-Object LastWriteTime -Descending |
      Select-Object -First 8 FullName,Length,LastWriteTime | Format-Table -AutoSize
  } else { Write-Host "MAME snap folder not found at $snap" }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
