# ROM-free live MAME control test. Reports step status without assuming exact frame accuracy.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=20)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_step_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "mame_stdout.log"
$stderr=Join-Path $dir "mame_stderr.log"
$proc=$null
try {
  Write-Host "Launching ROM-free Pong for GameFrame step test..." -ForegroundColor Cyan
  $arguments="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc=Start-Process -FilePath $MameExe -ArgumentList $arguments -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
b=MameBridge(Path(sys.argv[1]),timeout=1)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("STATUS BEFORE:",b.request("status"),flush=True)
        print("PAUSE:",b.request("pause"),flush=True)
        print("STEP ONCE:",b.request("step_once"),flush=True)
        time.sleep(.4)
        status=b.request("status")
        print("STATUS AFTER:",status,flush=True)
        if status["info"]["paused"]:
            print("PASS: Single-step request returned to paused state",flush=True)
            sys.exit(0)
        print("INCONCLUSIVE: Emulator did not return to paused state",flush=True)
        sys.exit(2)
    except TimeoutError:
        time.sleep(.2)
    except Exception as exc:
        print("FAILED:",repr(exc),flush=True)
        sys.exit(3)
print("No MAME response before timeout",flush=True)
sys.exit(4)
'@ | python - $dir $TimeoutSeconds
  if ($LASTEXITCODE -ne 0) {
    if (Test-Path $stdout) { Get-Content $stdout -Tail 20 }
    if (Test-Path $stderr) { Get-Content $stderr -Tail 20 }
    throw "Live step test did not pass; share output"
  }
} finally {
  if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
  Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
