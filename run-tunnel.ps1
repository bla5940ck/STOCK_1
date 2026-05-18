# Cloudflare Tunnel Launcher with URL Capture
# 啟動 Cloudflare Tunnel 並自動抓取 URL

$cloudflared = "$env:LOCALAPPDATA\cloudflared.exe"
$tunnelLog = "$env:TEMP\cloudflared-latest.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $cloudflared)) {
    Write-Host "❌ cloudflared not found!" -ForegroundColor Red
    exit 1
}

# 清除舊日誌
Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue

Write-Host "`n🔗 Starting tunnel and waiting for URL..." -ForegroundColor Yellow
Write-Host ""

# 啟動 cloudflared 並同時記錄到文件
& $cloudflared tunnel --url http://localhost:8000 2>&1 | Tee-Object -FilePath $tunnelLog -Append

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Tunnel stopped" -ForegroundColor Yellow
Write-Host "========================================"
