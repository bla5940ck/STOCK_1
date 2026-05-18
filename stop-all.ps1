# LINE Bot - Stop All Services
# 停止所有服務

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  Stopping All Services" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n1️⃣  Stopping Docker containers..." -ForegroundColor Cyan
Push-Location $root
docker-compose down 2>$null
Pop-Location
Write-Host "✅ Docker containers stopped" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ✅ All services stopped!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n"
Write-Host "`n"

Write-Host "`nTo start again:" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File start-all.ps1" -ForegroundColor Gray
Write-Host "`n"
