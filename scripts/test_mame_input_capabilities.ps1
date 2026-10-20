# Probe the available MAME input field APIs without changing any inputs.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_input_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "stdout.log"
$stderr=Join-Path $dir "stderr.log"
$proc=$null
try {
  $args="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $args -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  @'
import sys,time,json
from pathlib import Path
from gameframe.mame_bridge import MameBridge
bridge=MameBridge(Path(sys.argv[1]),timeout=2.5)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY:",bridge.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.2)
else:
    raise RuntimeError("MAME bridge was not ready")
ports=bridge.request("input_capabilities")["info"]["ports"]
matches=[{"tag":port["tag"],"fields":[f for f in port.get("fields",[]) if "Paddle" in f.get("name","")]} for port in ports]
print("PADDLE CAPABILITIES:",json.dumps([m for m in matches if m["fields"]],indent=2),flush=True)
print("READ ONLY: no input fields were changed",flush=True)
'@ | python - $dir $TimeoutSeconds
  $code=$LASTEXITCODE
  if ($code -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 25 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 25 }
    throw "Input capability probe failed (Python $code)"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
