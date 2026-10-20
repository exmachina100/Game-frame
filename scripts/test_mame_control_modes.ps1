# Diagnose emu.step versus resume/pause on MAME's built-in Pong system.
param([string]$MameExe="C:\MAME\mame.exe",[int]$TimeoutSeconds=35)
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua=Join-Path $root "mame\gameframe_bridge.lua"
$dir=Join-Path $env:TEMP ("gameframe_modes_"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$env:GAMEFRAME_BRIDGE_DIR=$dir
$stdout=Join-Path $dir "mame_stdout.log"
$stderr=Join-Path $dir "mame_stderr.log"
$proc=$null
try {
    $argline="pong -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
    $proc=Start-Process -FilePath $MameExe -ArgumentList $argline -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    @'
import sys,time
from pathlib import Path
from gameframe.mame_bridge import MameBridge
b=MameBridge(Path(sys.argv[1]),timeout=2.5)
deadline=time.monotonic()+int(sys.argv[2])
while time.monotonic()<deadline:
    try:
        print("READY",b.request("status")["info"]["system"],flush=True)
        break
    except TimeoutError:
        time.sleep(.2)
else:
    raise RuntimeError("Bridge did not start")
def status():
    return b.request("status")["info"]
def show(label,s):
    print(label,"frames=",s.get("screen_frames"),"paused=",s.get("paused"),"step_pending=",s.get("step_pending"),"flag=",s.get("single_step_flag"),flush=True)
b.request("pause")
time.sleep(.3)
before=status()
show("BASELINE",before)
# Do not issue another step after an incomplete step; test resume independently.
b.request("step_once")
time.sleep(.4)
after=status()
show("AFTER STEP",after)
b.request("reset_step_tracking")
b.request("resume")
time.sleep(.4)
running=status()
show("AFTER 400ms RESUME",running)
b.request("pause")
time.sleep(.2)
stopped=status()
show("AFTER PAUSE",stopped)
start=before.get("screen_frames") or {}
end=stopped.get("screen_frames") or {}
if isinstance(start,dict) and isinstance(end,dict):
    print("REALTIME FRAME DELTA",{k:end[k]-v for k,v in start.items() if k in end},flush=True)
print("DIAGNOSTIC COMPLETE: resume path measured; exact stepping remains unverified",flush=True)
'@ | python - $dir $TimeoutSeconds
    $code=$LASTEXITCODE
    if ($code -ne 0) {
        if (Test-Path $stdout) { Get-Content $stdout -Tail 45 }
        if (Test-Path $stderr) { Get-Content $stderr -Tail 45 }
        throw "Mode diagnostic failed (Python $code)"
    }
} finally {
    if ($proc) { $proc.Refresh(); if (!$proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } }
    Remove-Item Env:GAMEFRAME_BRIDGE_DIR -ErrorAction SilentlyContinue
    Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}
