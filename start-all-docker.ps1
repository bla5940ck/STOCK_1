# LINE Bot - One-Click Startup (All in Docker)
# 一鍵啟動所有服務（Docker Compose）

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LINE Bot - One-Click Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. 檢查 Docker
Write-Host "`n1️⃣  Checking Docker..." -ForegroundColor Cyan
try {
    docker ps >$null 2>&1
    Write-Host "✅ Docker is ready" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running! Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# 2. 啟動所有服務（Docker + Cloudflare Tunnel）
Write-Host "`n2️⃣  Starting all services (Docker)..." -ForegroundColor Cyan
Push-Location $root
docker-compose down 2>$null | Out-Null
Start-Sleep -Seconds 2
docker-compose up -d
$dockerResult = $LASTEXITCODE
Pop-Location

if ($dockerResult -ne 0) {
    Write-Host "❌ Docker failed to start" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker services started" -ForegroundColor Green

# 3. 等待應用就緒
Write-Host "`n3️⃣  Waiting for services to be ready..." -ForegroundColor Cyan
Write-Host "   ⏳ Checking FastAPI..." -ForegroundColor Gray
$count = 0
$maxWait = 30
while ($count -lt $maxWait) {
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($health -and $health.StatusCode -eq 200) {
            Write-Host "   ✅ FastAPI is ready" -ForegroundColor Green
            break
        }
    }
    catch {}
    $count++
    Start-Sleep -Milliseconds 500
}

Write-Host "   ⏳ Waiting for Cloudflare Tunnel..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 4. 獲取 Cloudflare Tunnel URL
Write-Host "`n4️⃣  Getting Cloudflare Tunnel URL..." -ForegroundColor Cyan

$tunnelUrl = $null
$maxAttempts = 15
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        # Read all tunnel logs, join lines and look for the URL pattern
        $logs = (docker logs linebot-tunnel 2>&1) -join " "
        
        # Match the URL pattern (removing whitespace that may have been inserted)
        if ($logs -match "https://([a-z0-9-]+)\.trycloudflare") {
            $domain = $matches[1]
            $tunnelUrl = "https://$domain.trycloudflare.com"
            break
        }
    }
    catch {}
    
    $attempt++
    if ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 1
    }
}

# ========== 顯示結果 ==========
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ✅ All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n📍 LOCAL ACCESS:" -ForegroundColor Cyan
Write-Host "   App:  http://localhost:8000" -ForegroundColor White
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n🌐 CLOUDFLARE TUNNEL:" -ForegroundColor Cyan
if ($tunnelUrl) {
    Write-Host "   ✅ Public URL: $tunnelUrl" -ForegroundColor Green
    Write-Host "   ✅ Webhook URL: $($tunnelUrl)/webhook/line" -ForegroundColor Green
    
    # 複製到剪貼板
    "$($tunnelUrl)/webhook/line" | Set-Clipboard
    Write-Host "   ✅ Webhook URL copied to clipboard!" -ForegroundColor Green
} else {
    Write-Host "   ⏳ URL not captured (still starting)" -ForegroundColor Yellow
    Write-Host "   Use: powershell -ExecutionPolicy Bypass -File get-tunnel-url.ps1" -ForegroundColor Gray
}

Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "   1. Copy Webhook URL (should be in clipboard now)" -ForegroundColor Gray
Write-Host "   2. Go to: https://developers.line.biz/" -ForegroundColor Gray
Write-Host "   3. Update Webhook URL" -ForegroundColor Gray
Write-Host "   4. Click 'Verify' button" -ForegroundColor Gray
Write-Host "   5. Enable 'Use webhook'" -ForegroundColor Gray

Write-Host "`n🛑 TO STOP ALL SERVICES:" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File stop-all.ps1" -ForegroundColor Gray

Write-Host "`n📌 TIPS:" -ForegroundColor Yellow
Write-Host "   - URL changes every time you restart" -ForegroundColor Gray
Write-Host "   - View logs: docker logs linebot-us-stock" -ForegroundColor Gray
Write-Host "   - View tunnel logs: docker logs linebot-tunnel" -ForegroundColor Gray
Write-Host "`n"
