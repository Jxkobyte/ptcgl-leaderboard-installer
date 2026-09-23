param(
    [string]$IsccPath = "",
    # Where the PtcglLeaderboard repo lives. The launcher and the plugin are both built from it.
    [string]$TrackerRepo = "..\..\source\repos\PtcglLeaderboard",
    # Skip rebuilding and just package whatever is already staged in src\.
    [switch]$NoRebuild
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# ---------------------------------------------------------------------------------------------
# Build the launcher and the plugin, then stage them.
#
# This is not a convenience. The installer packages whatever happens to be sitting in src\, so
# without this step an edit to Repair.cs or Core\*.cs compiles fine, the installer compiles fine,
# and you ship the PREVIOUS build with no error anywhere. Staging from a fresh build is the only
# thing that makes the output correspond to the source.
# ---------------------------------------------------------------------------------------------
if (-not $NoRebuild) {
    $repo = Join-Path $root $TrackerRepo
    if (-not (Test-Path (Join-Path $repo "PtcglLeaderboard.csproj"))) {
        Write-Host "PtcglLeaderboard repo not found at: $repo" -ForegroundColor Red
        Write-Host "Pass -TrackerRepo <path>, or -NoRebuild to package what is already staged." -ForegroundColor Yellow
        exit 1
    }

    # PTCGL holds BepInEx\core open while it runs, and the plugin build deploys into the game
    # folder, so a running client turns this into a confusing half-failure.
    if (Get-Process -Name "Pokemon TCG Live" -ErrorAction SilentlyContinue) {
        Write-Host "Pokemon TCG Live is running. Close it before building." -ForegroundColor Red
        exit 1
    }

    Write-Host "Building launcher..." -ForegroundColor Cyan
    & dotnet build (Join-Path $repo "Launcher\Launcher.csproj") -c Release -v quiet
    if ($LASTEXITCODE -ne 0) { Write-Host "Launcher build failed." -ForegroundColor Red; exit 1 }

    Write-Host "Building plugin..." -ForegroundColor Cyan
    & dotnet build (Join-Path $repo "PtcglLeaderboard.csproj") -c Release -v quiet
    if ($LASTEXITCODE -ne 0) { Write-Host "Plugin build failed." -ForegroundColor Red; exit 1 }

    New-Item -ItemType Directory -Force -Path (Join-Path $root "src\launcher") | Out-Null
    Copy-Item (Join-Path $repo "Launcher\bin\Release\PtcglLeaderboardLauncher.exe") `
              (Join-Path $root "src\launcher\") -Force
    Copy-Item (Join-Path $repo "bin\Release\PtcglLeaderboard.dll") `
              (Join-Path $root "src\files\BepInEx\plugins\") -Force

    # Fail loudly rather than packaging something that is not there.
    foreach ($f in @("src\launcher\PtcglLeaderboardLauncher.exe", "src\files\BepInEx\plugins\PtcglLeaderboard.dll")) {
        $p = Join-Path $root $f
        if (-not (Test-Path $p)) { Write-Host "Staging failed: $f missing" -ForegroundColor Red; exit 1 }
        Write-Host ("  staged {0}  ({1:N0} bytes, {2})" -f $f, (Get-Item $p).Length, (Get-Item $p).LastWriteTime) -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------------------------
# Compile the installer.
# ---------------------------------------------------------------------------------------------
$possiblePaths = @(
    $IsccPath,
    "iscc.exe",  # On PATH
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$ISCC = $null
foreach ($path in $possiblePaths) {
    if ($path -and (Test-Path $path -ErrorAction SilentlyContinue)) { $ISCC = $path; break }
    elseif ($path -eq "iscc.exe") {
        $cmd = Get-Command $path -ErrorAction SilentlyContinue
        if ($cmd) { $ISCC = $cmd.Source; break }
    }
}

if (-not $ISCC) {
    Write-Host "Inno Setup compiler 'iscc.exe' not found." -ForegroundColor Red
    Write-Host "Install Inno Setup 6: https://jrsoftware.org/isinfo.php" -ForegroundColor Yellow
    Write-Host "Or: .\build.ps1 -IsccPath 'C:\path\to\iscc.exe'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Compiling installer with: $ISCC" -ForegroundColor Cyan
& $ISCC (Join-Path $root "installer.iss")
if ($LASTEXITCODE -ne 0) { Write-Host "Installer compile failed." -ForegroundColor Red; exit 1 }

$out = Join-Path $root "build\output\ptcgl-leaderboard-setup.exe"
if (Test-Path $out) {
    Write-Host ("Done: {0}  ({1:N0} bytes)" -f $out, (Get-Item $out).Length) -ForegroundColor Green
}
