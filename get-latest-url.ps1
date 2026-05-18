# Get Latest Cloudflare Tunnel URL
# 自動從日誌檔案讀取最新的 Tunnel URL

$tunnelLog = "$env:TEMP\cloudflared-latest.log"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel URL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 檢查日誌檔案是否存在
if (-not (Test-Path $tunnelLog)) {
    Write-Host "`n❌ No tunnel log found!" -ForegroundColor Red
    Write-Host "   Start tunnel first with: powershell -ExecutionPolicy Bypass -File run-tunnel.ps1" -ForegroundColor Yellow
    Write-Host "`n"
    exit 1
}

# 讀取日誌檔案並尋找 URL
$urlPattern = "https://[a-z0-9-]+\.trycloudflare\.com"
$logContent = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue

# 尋找所有匹配的 URL，取最後（最新）的一個
$matches = [regex]::Matches($logContent, $urlPattern)

if ($matches.Count -gt 0) {
    $tunnelUrl = $matches[-1].Value
    $webhookUrl = "$tunnelUrl/webhook/line"
    
    Write-Host "`n✅ Found tunnel URL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Public URL:" -ForegroundColor White
    Write-Host "   $tunnelUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Webhook URL:" -ForegroundColor White
    Write-Host "   $webhookUrl" -ForegroundColor Yellow
    Write-Host ""
    
    # 複製到剪貼板
    $webhookUrl | Set-Clipboard
    Write-Host "   ✅ Webhook URL copied to clipboard!" -ForegroundColor Green
    
    Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Go to: https://developers.line.biz/" -ForegroundColor Gray
    Write-Host "   2. Update Webhook URL (already in clipboard)" -ForegroundColor Gray
    Write-Host "   3. Click 'Verify' button" -ForegroundColor Gray
    Write-Host "   4. Enable 'Use webhook'" -ForegroundColor Gray
} else {
    Write-Host "`n⚠️  Could not find tunnel URL in log" -ForegroundColor Yellow
    Write-Host "   Make sure tunnel is running (check tunnel window)" -ForegroundColor Gray
    Write-Host "`n"
    exit 1
}

Write-Host "`n"
