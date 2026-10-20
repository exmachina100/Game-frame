# ROM-free MAME 0.289 Lua probe via the built-in Pong hardware driver.
param(
  [string]$MameExe = "C:\MAME\mame.exe",
  [int]$TimeoutSeconds = 25,
  [string]$System = "pong"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $MameExe -PathType Leaf)) { throw "MAME not found: $MameExe" }
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lua = Join-Path $root "mame\probe.lua"
if (-not (Test-Path $lua -PathType Leaf)) { throw "Missing probe.lua; git pull origin main" }
$probe = Join-Path $env:TEMP ("gameframe_probe_" + [guid]::NewGuid().ToString("N") + ".txt")
$stdout = Join-Path $env:TEMP ("gameframe_mame_stdout_" + [guid]::NewGuid().ToString("N") + ".log")
$stderr = Join-Path $env:TEMP ("gameframe_mame_stderr_" + [guid]::NewGuid().ToString("N") + ".log")
$env:GAMEFRAME_PROBE_FILE = $probe
$proc = $null
try {
  Write-Host "GameFrame live probe - MAME $System (no external ROM required)" -ForegroundColor Cyan
  Write-Host "MAME: $MameExe"
  # A named running emulated machine is needed; MAME's system-selection frontend does
  # not trigger the post-machine-boot autoboot callback.
  $args = "$System -autoboot_script `"$lua`" -autoboot_delay 1 -window -verbose"
  $proc = Start-Process -FilePath $MameExe -ArgumentList $args -WorkingDirectory (Split-Path $MameExe) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if ((Test-Path $probe) -and ((Get-Item $probe).Length -gt 0)) {
      Write-Host "Probe completed:" -ForegroundColor Green
      Get-Content $probe
      return
    }
    $proc.Refresh()
    if ($proc.HasExited) { break }
    Start-Sleep -Milliseconds 250
  }
  Write-Warning "MAME did not produce the Lua report."
  $proc.Refresh()
  if ($proc.HasExited) { Write-Host "Exit code: $($proc.ExitCode)" }
  Write-Host "Diagnostics (last 35 lines of MAME output):" -ForegroundColor Yellow
  foreach ($p in @($stderr, $stdout)) {
    if (Test-Path $p) { Get-Content $p -Tail 35 }
  }
  throw "MAME Lua probe unsuccessful. Paste diagnostics shown above."
}
finally {
  if ($proc) {
    $proc.Refresh()
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  }
  Remove-Item Env:GAMEFRAME_PROBE_FILE -ErrorAction SilentlyContinue
  foreach ($p in @($probe, $stdout, $stderr)) {
    Remove-Item $p -Force -ErrorAction SilentlyContinue
  }
}
