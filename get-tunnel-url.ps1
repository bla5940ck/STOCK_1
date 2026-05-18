# LINE Bot - Get Tunnel URL
# 查看當前的 Cloudflare Tunnel URL

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel URL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n🔍 Looking for active tunnel..." -ForegroundColor Yellow

# 檢查 cloudflared 是否運行
$process = Get-Process cloudflared -ErrorAction SilentlyContinue
if (-not $process) {
    Write-Host "`n❌ Cloudflare Tunnel is not running!" -ForegroundColor Red
    Write-Host "`nStart it with:" -ForegroundColor Yellow
    Write-Host "   powershell -ExecutionPolicy Bypass -File start-all.ps1" -ForegroundColor Gray
    Write-Host "`n"
    exit 1
}

Write-Host "✅ Cloudflare Tunnel is running (PID: $($process.Id))" -ForegroundColor Green

Write-Host "`n📌 IMPORTANT:" -ForegroundColor Yellow
Write-Host "   Each time cloudflared starts, it creates a NEW URL" -ForegroundColor Gray
Write-Host "   The URL appears in the cloudflared window when it starts" -ForegroundColor Gray

Write-Host "`n🔎 HOW TO FIND YOUR TUNNEL URL:" -ForegroundColor Cyan
Write-Host "   1. Look for the cloudflared window (or check recent terminal output)" -ForegroundColor White
Write-Host "   2. Find this line:" -ForegroundColor White
Write-Host "      'Your quick Tunnel has been created! Visit it at:'" -ForegroundColor Gray
Write-Host "   3. The URL looks like:" -ForegroundColor White
Write-Host "      https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor Yellow

Write-Host "`n🔗 YOUR WEBHOOK URL:" -ForegroundColor Cyan
Write-Host "   https://xxxx-xxxx-xxxx.trycloudflare.com/webhook/line" -ForegroundColor Yellow
Write-Host "   (Replace xxxx-xxxx-xxxx with your actual URL)" -ForegroundColor Gray

Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "   1. Find your Tunnel URL from the cloudflared window output" -ForegroundColor White
Write-Host "   2. Go to: https://developers.line.biz/" -ForegroundColor White
Write-Host "   3. Update Webhook URL with your new URL" -ForegroundColor White
Write-Host "   4. Click 'Verify' button" -ForegroundColor White

Write-Host "`n⏰ NOTE: URL changes every time cloudflared restarts" -ForegroundColor Yellow
Write-Host "`n"
