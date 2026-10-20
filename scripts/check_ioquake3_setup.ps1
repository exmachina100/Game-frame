# GameFrame Windows ioquake3 installation readiness check.
# Does not download, install, launch, or copy proprietary game assets.
param([string]$InstallDir="D:\AI\Game Frame\ioquake3")
$ErrorActionPreference="Stop"
$dir=[IO.Path]::GetFullPath($InstallDir)
Write-Host "GameFrame / ioquake3 readiness" -ForegroundColor Cyan
Write-Host "Installation directory: $dir"
if (!(Test-Path -LiteralPath $dir -PathType Container)) {
    Write-Host "STATUS: NOT INSTALLED — directory absent." -ForegroundColor Yellow
    Write-Host "Download the Windows build from https://ioquake3.org/get-it/"
    Write-Host "Extract/install into $dir (or pass -InstallDir with your location)."
    exit 2
}
$exe=Get-ChildItem -LiteralPath $dir -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(ioquake3|ioq3).*\.exe$' } |
    Select-Object -First 1
if (!$exe) {
    Write-Host "STATUS: No ioquake3 executable found in installation directory." -ForegroundColor Yellow
    Write-Host "Install the official Windows engine build before continuing."
    exit 2
}
Write-Host "Executable: $($exe.FullName)" -ForegroundColor Green
Write-Host "Game data are separate from the GPL engine; Quake III retail files are not included."
$gameDirs=@("baseq3","baseoa")
foreach($game in $gameDirs) {
    $gameDir=Join-Path $exe.DirectoryName $game
    $count=0
    if(Test-Path -LiteralPath $gameDir -PathType Container) {
        $count=@(Get-ChildItem -LiteralPath $gameDir -Filter "*.pk3" -File -ErrorAction SilentlyContinue).Count
    }
    Write-Host "$game data archives: $count"
}
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $root
try {
    python -m gameframe.engine_cli inspect ioquake3 --exe "$($exe.FullName)"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
Write-Host "NOTE: Executable discovery is not an engine connection or camera-control test." -ForegroundColor Yellow
