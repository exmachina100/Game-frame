# Repeat three screen-frame steps in ROM-free Pong and report every delta.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$folder=Join-Path $env:TEMP ("gameframe_repeat_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $folder | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$folder
$stdout=Join-Path $folder "stdout.log"
$stderr=Join-Path $folder "stderr.log"
$proc=$null
try {
    $args="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
    $proc=Start-Process -FilePath $MameExe -ArgumentList $args -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
from gameframe.frame_verify import verify_step
b=MameBridge(Path(sys.argv[1]),timeout=2)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY:",b.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.2)
else:
    raise RuntimeError("No response from MAME bridge")
good=0
for n in range(1,4):
    r=verify_step(b,timeout=4)
    print(f"STEP {n}: delta={r.screen_deltas}, paused={r.paused}, confirmed={r.confirmed}",flush=True)
    good += int(r.confirmed)
print(f"REPEAT RESULT: {good}/3 verified single-screen-frame steps",flush=True)
if good!=3:
    sys.exit(2)
'@ | python - $folder $TimeoutSeconds
    $code=$LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "MAME stdout:" -ForegroundColor Yellow
        if (Test-Path $stdout) { Get-Content $stdout -Tail 30 }
        Write-Host "MAME stderr:" -ForegroundColor Yellow
        if (Test-Path $stderr) { Get-Content $stderr -Tail 30 }
        throw "Repeat-step test failed: $code"
    }
} finally {
    if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
    Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
    Remove-Item $folder -Recurse -Force -ErrorAction SilentlyContinue
}
