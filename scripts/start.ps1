# Claw Agent — Start Services on Windows
# Run from the project root: .\scripts\start.ps1
# Starts IronClaw first, then backend + frontend.

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$SkipIronClaw,
    [string]$BackendHost = "127.0.0.1",
    [int]$Port = 8080,
    [int]$FrontendPort = 3001
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "`n=== Claw Agent — Starting Services ===" -ForegroundColor Cyan

# Activate venv
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
    Write-Host "  Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  WARNING: .venv not found. Run .\scripts\setup.ps1 first." -ForegroundColor Yellow
}

# 1. Start IronClaw first (required for AI/chat)
$IronClawProcess = $null
if (-not $SkipIronClaw) {
    $IronClawExe = $null
    $ic = Get-Command ironclaw -ErrorAction SilentlyContinue
    if ($ic) {
        $IronClawExe = $ic.Source
    } elseif (Test-Path (Join-Path $ProjectRoot "dist\ironclaw.exe")) {
        $IronClawExe = (Join-Path $ProjectRoot "dist\ironclaw.exe")
    }
    if ($IronClawExe) {
        Write-Host "`n[IronClaw] Starting AI engine on port 3000..." -ForegroundColor Yellow
        $DataDir = Join-Path $ProjectRoot "data"
        if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir -Force | Out-Null }
        $LibSqlPath = Join-Path $DataDir "ironclaw.db"

        $env:DATABASE_BACKEND = "libsql"
        $env:LIBSQL_PATH = $LibSqlPath
        $proc = Start-Process -FilePath $IronClawExe -ArgumentList "run" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow
        $IronClawProcess = $proc
        Write-Host "  IronClaw started (PID: $($proc.Id))" -ForegroundColor Green

        # Wait for IronClaw to be ready (health check)
        Write-Host "  Waiting for IronClaw to be ready..." -ForegroundColor Gray
        $maxAttempts = 30
        $attempt = 0
        $ready = $false
        while ($attempt -lt $maxAttempts) {
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000/api/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
                if ($r.StatusCode -eq 200) { $ready = $true; break }
            } catch { }
            $attempt++
            Start-Sleep -Seconds 2
        }
        if ($ready) {
            Write-Host "  IronClaw is ready." -ForegroundColor Green
        } else {
            Write-Host "  WARNING: IronClaw may not be ready (timeout). Continuing anyway." -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n  WARNING: IronClaw not found. Install via: winget install IronClaw, or run build-exe.ps1. AI features may use OpenRouter fallback." -ForegroundColor Yellow
    }
}

# 2. Start backend
if (-not $FrontendOnly) {
    Write-Host "`n[Backend] Starting on ${BackendHost}:${Port}..." -ForegroundColor Yellow
    $backendJob = Start-Job -ScriptBlock {
        param($root, $h, $p)
        Set-Location $root
        & ".venv\Scripts\python.exe" -m uvicorn webhooks.server:app --host $h --port $p --env-file .env
    } -ArgumentList $ProjectRoot, $BackendHost, $Port
    Write-Host "  Backend started (Job ID: $($backendJob.Id))" -ForegroundColor Green
}

if (-not $BackendOnly) {
    Write-Host "`n[Frontend] Starting on port ${FrontendPort}..." -ForegroundColor Yellow
    $frontendJob = Start-Job -ScriptBlock {
        param($root, $p)
        Set-Location (Join-Path $root "frontend")
        npm run dev -- --port $p
    } -ArgumentList $ProjectRoot, $FrontendPort
    Write-Host "  Frontend started (Job ID: $($frontendJob.Id))" -ForegroundColor Green
}

Write-Host "`n=== Services Running ===" -ForegroundColor Cyan
if ($IronClawProcess) {
    Write-Host "  IronClaw: http://127.0.0.1:3000"
}
if (-not $FrontendOnly) {
    Write-Host "  Backend:  http://${BackendHost}:${Port}"
    Write-Host "  Health:   http://${BackendHost}:${Port}/health"
}
if (-not $BackendOnly) {
    Write-Host "  Dashboard: http://localhost:${FrontendPort}"
}
Write-Host "`nPress Ctrl+C or run .\scripts\stop.ps1 to stop services."
Write-Host "Use Get-Job to check status, Receive-Job <id> to see output.`n"

# Keep script running so jobs stay alive
try {
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Get-Job | Stop-Job -PassThru | Remove-Job
    if ($IronClawProcess -and -not $IronClawProcess.HasExited) {
        $IronClawProcess.Kill()
        Write-Host "  IronClaw stopped." -ForegroundColor Green
    }
    Write-Host "Services stopped." -ForegroundColor Green
}
