# Claw Agent — Windows Setup Script
# Run from the project root: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "`n=== Claw Agent Windows Setup ===" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "  Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Or run: winget install Python.Python.3.13" -ForegroundColor Red
    exit 1
}

# 2. Check Node.js
Write-Host "`n[2/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  Found: Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  Node.js not found. Install from https://nodejs.org/" -ForegroundColor Red
    Write-Host "  Or run: winget install OpenJS.NodeJS.LTS" -ForegroundColor Red
    exit 1
}

# 3. Create virtual environment
Write-Host "`n[3/6] Creating Python virtual environment..." -ForegroundColor Yellow
Push-Location $ProjectRoot
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "  Created .venv" -ForegroundColor Green
} else {
    Write-Host "  .venv already exists" -ForegroundColor Green
}

# 4. Install Python dependencies
Write-Host "`n[4/6] Installing Python dependencies..." -ForegroundColor Yellow
& ".venv\Scripts\pip.exe" install -r requirements.txt
& ".venv\Scripts\pip.exe" install -r requirements-dev.txt
Write-Host "  Dependencies installed" -ForegroundColor Green

# 5. Set up .env
Write-Host "`n[5/6] Setting up .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Copied .env.example -> .env" -ForegroundColor Green
    Write-Host "  IMPORTANT: Edit .env with your API keys and tokens" -ForegroundColor Yellow
} else {
    Write-Host "  .env already exists" -ForegroundColor Green
}

# 6. Install frontend dependencies
Write-Host "`n[6/6] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location "frontend"
npm install
Pop-Location
Write-Host "  Frontend dependencies installed" -ForegroundColor Green

Pop-Location

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:"
Write-Host "  1. Edit .env with your API keys"
Write-Host "  2. (Optional) Install PostgreSQL: winget install PostgreSQL.PostgreSQL"
Write-Host "  3. Run: .\scripts\start.ps1"
Write-Host "  4. Run tests: .\scripts\test.ps1"
Write-Host ""
