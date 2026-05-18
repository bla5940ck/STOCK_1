# LINE Bot - Quick Start (Cloudflare Tunnel)
# 一鍵啟動所有服務

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cloudflared = "$env:LOCALAPPDATA\cloudflared.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LINE Bot - One-Click Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 檢查 Docker
Write-Host "`nChecking Docker..." -ForegroundColor Cyan
try {
    docker ps >$null 2>&1
    Write-Host "✅ Docker is ready" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running! Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# 2. 啟動 Docker 容器
Write-Host "`n2️⃣  Starting Docker containers..." -ForegroundColor Cyan
Push-Location $root
docker-compose down 2>$null
Start-Sleep -Seconds 2
docker-compose up -d
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker failed to start" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker containers started" -ForegroundColor Green

# 等待應用程式就緒
Write-Host "   ⏳ Waiting for app..." -ForegroundColor Gray
$count = 0
$maxWait = 30
while ($count -lt $maxWait) {
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($health -and $health.StatusCode -eq 200) {
            Write-Host "✅ App ready (http://localhost:8000)" -ForegroundColor Green
            break
        }
    }
    catch {}
    $count++
    Start-Sleep -Milliseconds 500
}

if ($count -ge $maxWait) {
    Write-Host "⚠️  App startup is taking longer..." -ForegroundColor Yellow
}

# 3. 啟動 Cloudflare Tunnel
Write-Host "`n3️⃣  Starting Cloudflare Tunnel..." -ForegroundColor Cyan

if (-not (Test-Path $cloudflared)) {
    Write-Host "   Installing cloudflared..." -ForegroundColor Gray
    $ProgressPreference = 'SilentlyContinue'
    try {
        Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/download/2024.5.0/cloudflared-windows-amd64.exe" -OutFile "$env:TEMP\cloudflared.exe" -TimeoutSec 30 -ErrorAction Stop
        Copy-Item "$env:TEMP\cloudflared.exe" "$env:LOCALAPPDATA\cloudflared.exe" -Force
        Write-Host "✅ cloudflared installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install cloudflared: $_" -ForegroundColor Red
        exit 1
    }
}

# 檢查是否已有 cloudflared 在運行
$existingProcess = Get-Process cloudflared -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "   Stopping old tunnel..." -ForegroundColor Gray
    Stop-Process -Name cloudflared -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 啟動 cloudflared 並捕獲 URL
Write-Host "   Starting cloudflared..." -ForegroundColor Gray

# 臨時文件用於捕獲輸出
$tempLog = "$env:TEMP\cloudflared-url.txt"
Remove-Item $tempLog -Force -ErrorAction SilentlyContinue

# 建立臨時檔案來儲存輸出
$tunnelProcess = Start-Process -FilePath $cloudflared `
    -ArgumentList "tunnel", "--url", "http://localhost:8000" `
    -PassThru `
    -WindowStyle Normal `
    -NoNewWindow:$false

Write-Host "✅ Cloudflare Tunnel starting..." -ForegroundColor Green

# 等待並捕獲 URL（檢查 cloudflared 窗口或日誌）
$tunnelUrl = $null
$waitCount = 0
$maxWait = 30  # 15 seconds with 500ms intervals

Write-Host "   ⏳ Waiting for tunnel URL..." -ForegroundColor Gray

# 嘗試從進程名稱和系統來猜測 URL 或等待用戶手動輸入
Start-Sleep -Seconds 5

# 嘗試從 Windows 事件日誌或其他地方尋找 URL
# 因為 cloudflared 會在自己的窗口中顯示，所以用戶可以看到
# 我們也可以讀取臨時文件（如果 cloudflared 支援）

# 簡單方法：提醒用戶從窗口複製 URL
Write-Host "✅ Tunnel window opened" -ForegroundColor Green

# ========== 顯示摘要 ==========
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ✅ All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n📍 LOCAL ACCESS:" -ForegroundColor Cyan
Write-Host "   App: http://localhost:8000" -ForegroundColor White
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n🌐 CLOUDFLARE TUNNEL:" -ForegroundColor Cyan

if ($tunnelUrl) {
    Write-Host "   ✅ Public URL: $tunnelUrl" -ForegroundColor Green
    Write-Host "   ✅ Webhook URL: $($tunnelUrl)/webhook/line" -ForegroundColor Green
} else {
    Write-Host "   ⬆️  Check the Cloudflare Tunnel window (should be open now)" -ForegroundColor White
    Write-Host "   📌 Copy the URL that looks like: https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor White
}

Write-Host "`n📋 SETUP STEPS:" -ForegroundColor Yellow
Write-Host "   1. Copy Webhook URL from above" -ForegroundColor Gray
Write-Host "   2. Go to: https://developers.line.biz/" -ForegroundColor Gray
Write-Host "   3. Update Webhook URL with your URL" -ForegroundColor Gray
Write-Host "   4. Click 'Verify' button" -ForegroundColor Gray
Write-Host "   5. Enable 'Use webhook'" -ForegroundColor Gray

Write-Host "`n⏰ IMPORTANT:" -ForegroundColor Yellow
Write-Host "   The tunnel URL changes every time you restart" -ForegroundColor Gray
Write-Host "   Always update LINE Developer Console with the new URL" -ForegroundColor Gray

Write-Host "`n🛑 TO STOP:" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File stop-all.ps1" -ForegroundColor Gray
Write-Host "`n"
