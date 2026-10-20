# GameFrame end-to-end read/status/snapshot/recording command test.
param([string]$MameExe="C:\MAME\mame.exe",[string]$System="pong",[int]$TimeoutSeconds=20)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
if (!(Test-Path $MameExe)) { throw "MAME not found: $MameExe" }
$bridge=Join-Path $env:TEMP ("gameframe_bridge_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $bridge | Out-Null
$out=Join-Path $bridge "stdout.log"; $err=Join-Path $bridge "stderr.log"
$env:GAMEFRAME_BRIDGE_DIR=$bridge
$proc=$null
try {
  $arguments="$System -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  Write-Host "Starting MAME $System with GameFrame bridge..." -ForegroundColor Cyan
  $proc=Start-Process -FilePath $MameExe -ArgumentList $arguments -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
bridge=MameBridge(Path(sys.argv[1]),timeout=2)
end=time.monotonic()+int(sys.argv[2])
while time.monotonic()<end:
    try:
        print("STATUS",bridge.request("status"),flush=True)
        print("SNAPSHOT",bridge.request("snapshot"),flush=True)
        print("RECORD_START",bridge.request("record_start"),flush=True)
        time.sleep(1)
        print("RECORD_STOP",bridge.request("record_stop"),flush=True)
        print("PASS: Live MAME bridge command exchange succeeded",flush=True)
        sys.exit(0)
    except TimeoutError:
        time.sleep(.3)
    except Exception as exc:
        print("Bridge failed:",repr(exc),flush=True)
        sys.exit(2)
print("Bridge timed out without a reply.",flush=True)
sys.exit(3)
'@ | python - $bridge $TimeoutSeconds
  if ($LASTEXITCODE -ne 0) {
    Write-Host "MAME stdout:" -ForegroundColor Yellow
    if (Test-Path $out) { Get-Content $out -Tail 35 }
    Write-Host "MAME stderr:" -ForegroundColor Yellow
    if (Test-Path $err) { Get-Content $err -Tail 35 }
    throw "Live bridge test failed; share output above"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $bridge -Recurse -Force -ErrorAction SilentlyContinue
}
