# Claw Agent — Stop Services on Windows
# Run from the project root: .\scripts\stop.ps1
# Stops IronClaw (3000), Backend (8080), Frontend (3001)

Write-Host "`n=== Claw Agent — Stopping Services ===" -ForegroundColor Cyan

$ports = @(3000, 8080, 3001)
$stopped = 0
foreach ($port in $ports) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($conn -and $conn.OwningProcess) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped process on port $port (PID $($conn.OwningProcess))" -ForegroundColor Green
            $stopped++
        }
    } catch { }
}
if ($stopped -eq 0) {
    Write-Host "  No Claw Agent processes found on ports 3000, 8080, 3001." -ForegroundColor Yellow
}

# Also stop any jobs in current session (if stop was run from same window as start)
Get-Job | Stop-Job -PassThru -ErrorAction SilentlyContinue | Remove-Job -ErrorAction SilentlyContinue

Write-Host "`n=== Done ===" -ForegroundColor Cyan
