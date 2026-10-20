# Produce a measured native-MAME Pong directing test and manifest.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35,[switch]$Record)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_timeline_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "stdout.log"
$stderr=Join-Path $dir "stderr.log"
$proc=$null
$manifest=Join-Path $root "output\pong_timeline_manifest.json"
try {
  $arguments="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $arguments -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  $recordFlag=if ($Record) { "1" } else { "0" }
  @'
import sys,time,json
from pathlib import Path
from gameframe.mame_bridge import MameBridge
from gameframe.timeline import play_timeline,DEMO_BEATS
bridge=MameBridge(Path(sys.argv[1]),timeout=2.5)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY:",bridge.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.25)
else:
    raise RuntimeError("MAME startup timeout")
result=play_timeline(bridge,DEMO_BEATS,record=(sys.argv[4]=="1"),manifest=Path(sys.argv[3]))
for beat in result["beats"]:
    print("BEAT:",beat["label"],"TARGET:",beat["frames"],"ACTUAL:",beat["actual_frames"],flush=True)
print("COMPLETE:",result["complete"],"FRAME_EXACT:",result["frame_exact"],flush=True)
print("MANIFEST:",sys.argv[3],flush=True)
if sys.argv[4]=="1":
    print("MAME AVI recording was requested; check its configured video output directory",flush=True)
'@ | python - $dir $TimeoutSeconds $manifest $recordFlag
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 30 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 30 }
    throw "Pong timeline failed (Python $code)"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
