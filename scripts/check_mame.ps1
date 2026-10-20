# GameFrame Windows MAME diagnostics
# Run from a PowerShell terminal in the cloned Game-frame repository:
#   powershell -ExecutionPolicy Bypass -File .\scripts\check_mame.ps1
# Does not download ROMs, change installation, or start a game.
param([string]$MamePath = "")
$ErrorActionPreference = "Stop"
function Find-Mame {
  param([string]$ExplicitPath)
  if ($ExplicitPath) {
    if (Test-Path $ExplicitPath -PathType Container) { $ExplicitPath = Join-Path $ExplicitPath "mame.exe" }
    if (Test-Path $ExplicitPath -PathType Leaf) { return (Resolve-Path $ExplicitPath).Path }
    throw "No mame.exe found at: $ExplicitPath"
  }
  $inPath = Get-Command mame.exe -ErrorAction SilentlyContinue
  if ($inPath) { return $inPath.Source }
  $candidates = @(
    "C:\MAME\mame.exe",
    "C:\mame\mame.exe",
    "D:\MAME\mame.exe",
    "D:\Games\MAME\mame.exe",
    "$env:USERPROFILE\Downloads\mame\mame.exe",
    "$env:USERPROFILE\Desktop\MAME\mame.exe"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate -PathType Leaf) { return (Resolve-Path $candidate).Path }
  }
  return $null
}
Write-Host "GameFrame MAME diagnostic" -ForegroundColor Cyan
$exe = Find-Mame -ExplicitPath $MamePath
if (-not $exe) {
  Write-Host "MAME not found in standard locations or PATH." -ForegroundColor Yellow
  Write-Host "Rerun with: powershell -ExecutionPolicy Bypass -File .\scripts\check_mame.ps1 -MamePath 'D:\path\to\mame.exe'"
  exit 2
}
Write-Host "MAME executable: $exe"
$versionOutput = & $exe -version 2>&1
$version = ($versionOutput | Select-Object -First 1 | Out-String).Trim()
Write-Host "MAME version: $version"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua = Join-Path $repo "mame\gameframe_bridge.lua"
Write-Host "Bridge Lua exists: $(Test-Path $lua)"
$python = Get-Command python -ErrorAction SilentlyContinue
Write-Host "Python available: $([bool]$python)"
if ($python) {
  & python -m unittest discover -s tests -v
  if ($LASTEXITCODE -ne 0) { throw "GameFrame tests failed" }
}
Write-Host ""
Write-Host "Diagnostic complete. Send the MAME executable path and version printed above." -ForegroundColor Green
Write-Host "NOTE: No live bridge command was sent; MAME Lua compatibility is not verified."
