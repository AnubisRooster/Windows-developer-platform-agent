# Claw Agent — Run Tests on Windows
# Run from the project root: .\scripts\test.ps1 [-Unit] [-Integration] [-Deployment] [-Coverage]

param(
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Deployment,
    [switch]$Coverage,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "`n=== Claw Agent — Test Runner ===" -ForegroundColor Cyan

# Activate venv
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "  .venv not found. Using system Python." -ForegroundColor Yellow
    $VenvPython = "python"
}

Push-Location $ProjectRoot

$pytestArgs = @()

if ($Verbose) {
    $pytestArgs += "-v"
}

if ($Coverage) {
    $pytestArgs += "--cov=."
    $pytestArgs += "--cov-report=html"
    $pytestArgs += "--cov-report=term-missing"
}

if ($Unit) {
    Write-Host "`n  Running UNIT tests..." -ForegroundColor Yellow
    & $VenvPython -m pytest tests/unit $pytestArgs -m "not slow"
} elseif ($Integration) {
    Write-Host "`n  Running INTEGRATION tests..." -ForegroundColor Yellow
    & $VenvPython -m pytest tests/integration $pytestArgs
} elseif ($Deployment) {
    Write-Host "`n  Running DEPLOYMENT tests..." -ForegroundColor Yellow
    & $VenvPython -m pytest tests/deployment $pytestArgs -m "deployment"
} else {
    Write-Host "`n  Running ALL tests..." -ForegroundColor Yellow
    & $VenvPython -m pytest tests/ $pytestArgs
}

$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -eq 0) {
    Write-Host "`n=== All Tests Passed ===" -ForegroundColor Green
} else {
    Write-Host "`n=== Some Tests Failed (exit code: $exitCode) ===" -ForegroundColor Red
}

exit $exitCode
