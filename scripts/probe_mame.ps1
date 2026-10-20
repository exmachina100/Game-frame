# End-to-end Lua environment probe for Windows MAME 0.289.
# Runs MAME using its built-in no-ROM launcher; never sends gameplay commands.
param(
  [string]$MameExe = "C:\MAME\mame.exe",
  [int]$TimeoutSeconds = 18
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $MameExe -PathType Leaf)) { throw "MAME not found: $MameExe" }
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua = Join-Path $root "mame\probe.lua"
if (-not (Test-Path $lua)) { throw "Missing mame\probe.lua. Run git pull origin main." }
$probe = Join-Path $env:TEMP ("gameframe_probe_" + [guid]::NewGuid().ToString("N") + ".txt")
$env:GAMEFRAME_PROBE_FILE = $probe
Write-Host "Starting MAME Lua probe (no ROM required)..." -ForegroundColor Cyan
# MAME starts with its internal empty driver when no system is provided.
$proc = Start-Process -FilePath $MameExe -ArgumentList @("-autoboot_script", ('"' + $lua + '"'), "-autoboot_delay", "0") -PassThru
try {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path $probe) {
      Write-Host "Lua probe successful:" -ForegroundColor Green
      Get-Content $probe
      exit 0
    }
    $proc.Refresh()
    if ($proc.HasExited) { Write-Warning "MAME exited before writing the probe. Exit code: $($proc.ExitCode)"; break }
    Start-Sleep -Milliseconds 200
  }
  Write-Warning "Probe did not return. Try selecting a runnable machine in MAME and then rerun."
  exit 1
} finally {
  if ($proc) {
    $proc.Refresh()
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  }
  Remove-Item Env:GAMEFRAME_PROBE_FILE -ErrorAction SilentlyContinue
  Remove-Item $probe -ErrorAction SilentlyContinue
}
