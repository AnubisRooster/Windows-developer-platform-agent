# Claw Agent - Build executable and portable package
# Run from project root: .\scripts\build-exe.ps1

param(
    [switch]$SkipFrontend,
    [switch]$SkipIronClaw,
    [string]$IronClawVersion = "v0.18.0"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "`n=== Claw Agent Build ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

# 1. Build frontend
if (-not $SkipFrontend) {
    Write-Host "`n[1/4] Building frontend (Next.js static export)..." -ForegroundColor Yellow
    Push-Location (Join-Path $ProjectRoot "frontend")
    try {
        npm run build
        if (-not (Test-Path "out")) {
            throw "Frontend build did not produce 'out' directory"
        }
        Write-Host "  Frontend built successfully" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "`n[1/4] Skipping frontend build" -ForegroundColor Gray
}

# 2. Download IronClaw
$DistDir = Join-Path $ProjectRoot "dist"
$IronClawExe = Join-Path $DistDir "ironclaw.exe"
if (-not $SkipIronClaw) {
    Write-Host "`n[2/4] Downloading IronClaw Windows binary..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
    $IronClawUrl = "https://github.com/nearai/ironclaw/releases/download/$IronClawVersion/ironclaw-x86_64-pc-windows-msvc.tar.gz"
    $TarPath = Join-Path $DistDir "ironclaw.tar.gz"
    try {
        Invoke-WebRequest -Uri $IronClawUrl -OutFile $TarPath -UseBasicParsing
        # tar.gz on Windows - use tar if available (Windows 10+)
        $TarDir = Join-Path $DistDir "ironclaw_extract"
        New-Item -ItemType Directory -Force -Path $TarDir | Out-Null
        tar -xzf $TarPath -C $TarDir 2>$null
        $ExtractedExe = Get-ChildItem -Path $TarDir -Filter "ironclaw.exe" -Recurse | Select-Object -First 1
        if ($ExtractedExe) {
            Copy-Item $ExtractedExe.FullName -Destination $IronClawExe -Force
        }
        Remove-Item $TarPath -Force -ErrorAction SilentlyContinue
        Remove-Item $TarDir -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path $IronClawExe) {
            Write-Host "  IronClaw downloaded to dist/ironclaw.exe" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Could not extract ironclaw.exe from archive" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  WARNING: Could not download IronClaw: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[2/4] Skipping IronClaw download" -ForegroundColor Gray
}

# 3. Build Python executable
Write-Host "`n[3/4] Building Python executable with PyInstaller..." -ForegroundColor Yellow
Push-Location $ProjectRoot
try {
    if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
        pip install pyinstaller
    }
    python -m PyInstaller packaging/ClawAgent.spec --noconfirm --clean
    if (-not (Test-Path (Join-Path $ProjectRoot "dist" "ClawAgent.exe"))) {
        throw "PyInstaller did not produce ClawAgent.exe"
    }
    Write-Host "  ClawAgent.exe built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# 4. Assemble portable package
Write-Host "`n[4/4] Assembling portable package..." -ForegroundColor Yellow
$DistExe = Join-Path $ProjectRoot "dist" "ClawAgent.exe"
$PortableDir = Join-Path $ProjectRoot "dist" "ClawAgent-Portable"
New-Item -ItemType Directory -Force -Path $PortableDir | Out-Null
Copy-Item $DistExe -Destination (Join-Path $PortableDir "ClawAgent.exe") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $PortableDir "data") | Out-Null
if (Test-Path $IronClawExe) {
    Copy-Item $IronClawExe -Destination (Join-Path $PortableDir "ironclaw.exe") -Force
}
Copy-Item (Join-Path $ProjectRoot "packaging" "README.txt") -Destination (Join-Path $PortableDir "README.txt") -Force
Write-Host "  Portable package: dist/ClawAgent-Portable/" -ForegroundColor Green

Write-Host "`n=== Build Complete ===" -ForegroundColor Cyan
Write-Host "  Executable: dist/ClawAgent.exe"
Write-Host "  Portable:   dist/ClawAgent-Portable/"
Write-Host "`nRun ClawAgent.exe and open http://localhost:8080 in your browser."
Write-Host "For AI features, run ironclaw run in a separate terminal (see README.txt).`n"
