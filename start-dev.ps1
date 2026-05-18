# LINE Bot US Stock - Quick Start Script
# 一鍵啟動: Docker + ngrok + 應用程式

param(
    [switch]$NoNgrok,      # 跳過 ngrok（如果已在運行）
    [switch]$StopOnly,     # 只停止服務
    [switch]$CleanUp       # 清理所有容器和 ngrok
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ngrokPath = "$env:LOCALAPPDATA\ngrok\ngrok.exe"
$dockerComposePath = "$projectRoot\docker-compose.yml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LINE Bot US Stock - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 檢查 Docker 是否運行
function Test-Docker {
    $dockerStatus = docker ps 2>$null
    return $?
}

# 提取 ngrok URL
function Get-NgrokUrl {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response) {
            $tunnels = $response.Content | ConvertFrom-Json
            if ($tunnels.tunnels -and $tunnels.tunnels.Count -gt 0) {
                return $tunnels.tunnels[0].public_url
            }
        }
    }
    catch {
        # 忽略錯誤
    }
    return $null
}

# ========== 停止服務 ==========
if ($StopOnly -or $CleanUp) {
    Write-Host "`n🛑 停止服務中..." -ForegroundColor Yellow
    
    # 停止 Docker
    Write-Host "  • 停止 Docker 容器..." -ForegroundColor Gray
    Push-Location $projectRoot
    docker-compose down 2>$null
    Pop-Location
    
    # 停止 ngrok
    Write-Host "  • 停止 ngrok..." -ForegroundColor Gray
    Stop-Process -Name ngrok -Force -ErrorAction SilentlyContinue
    
    if ($CleanUp) {
        Write-Host "  • 清理 Docker 鏡像..." -ForegroundColor Gray
        docker system prune -f 2>$null
    }
    
    Write-Host "✅ 服務已停止" -ForegroundColor Green
    exit 0
}

# ========== 啟動服務 ==========
Write-Host "`n📦 正在啟動服務..." -ForegroundColor Yellow

# 1. 檢查 Docker
Write-Host "`n1️⃣  檢查 Docker..." -ForegroundColor Cyan
if (-not (Test-Docker)) {
    Write-Host "❌ Docker 未運行！請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker 就緒" -ForegroundColor Green

# 2. 啟動 Docker 容器
Write-Host "`n2️⃣  啟動 Docker 容器..." -ForegroundColor Cyan
Push-Location $projectRoot
docker-compose up -d
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker 啟動失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker 容器已啟動" -ForegroundColor Green

# 等待應用程式就緒
Write-Host "   ⏳ 等待應用程式就緒..." -ForegroundColor Gray
$maxRetries = 30
$retries = 0
while ($retries -lt $maxRetries) {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($health -and $health.StatusCode -eq 200) {
        Write-Host "✅ 應用程式就緒（http://localhost:8000）" -ForegroundColor Green
        break
    }
    $retries++
    Start-Sleep -Seconds 1
}

if ($retries -eq $maxRetries) {
    Write-Host "⚠️  應用程式啟動超時，但容器仍在運行" -ForegroundColor Yellow
}

# 3. 啟動 ngrok（如果沒有跳過）
if (-not $NoNgrok) {
    Write-Host "`n3️⃣  啟動 ngrok 隧道..." -ForegroundColor Cyan
    
    # 檢查 ngrok 是否已運行
    $existingTunnel = Get-NgrokUrl
    if ($existingTunnel) {
        Write-Host "✅ ngrok 已在運行" -ForegroundColor Green
        Write-Host "   公開 URL: $existingTunnel" -ForegroundColor Green
    }
    else {
        # 啟動 ngrok
        if (Test-Path $ngrokPath) {
            # 在後台啟動 ngrok
            Start-Process -FilePath $ngrokPath -ArgumentList "http", "8000" -WindowStyle Minimized
            Write-Host "   ⏳ 等待 ngrok 連線..." -ForegroundColor Gray
            Start-Sleep -Seconds 3
            
            $ngrokUrl = Get-NgrokUrl
            if ($ngrokUrl) {
                Write-Host "✅ ngrok 隧道已建立" -ForegroundColor Green
                Write-Host "   公開 URL: $ngrokUrl" -ForegroundColor Green
            }
            else {
                Write-Host "❌ ngrok 啟動失敗" -ForegroundColor Red
                Write-Host "   請手動執行: &`"$ngrokPath`" http 8000" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "⚠️  ngrok 未找到，請先設置 authtoken" -ForegroundColor Yellow
        }
    }
}

# ========== 顯示摘要 ==========
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ✅ 所有服務已啟動！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

$ngrokUrl = Get-NgrokUrl
Write-Host "`n📍 本地開發：" -ForegroundColor Cyan
Write-Host "   • 應用程式: http://localhost:8000" -ForegroundColor White
Write-Host "   • API 文檔: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • ReDoc: http://localhost:8000/redoc" -ForegroundColor White

if ($ngrokUrl) {
    Write-Host "`n🌐 公開訪問：" -ForegroundColor Cyan
    Write-Host "   • Webhook URL: $ngrokUrl/webhook/line" -ForegroundColor White
    Write-Host "`n💡 設置 LINE Webhook:" -ForegroundColor Yellow
    Write-Host "   1. 進入: https://developers.line.biz/" -ForegroundColor Gray
    Write-Host "   2. 進入 Messaging API 設定" -ForegroundColor Gray
    Write-Host "   3. Webhook URL 設為: $ngrokUrl/webhook/line" -ForegroundColor Gray
    Write-Host "   4. 點擊「驗證」按鈕" -ForegroundColor Gray
}

Write-Host "`n🛑 停止服務：" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File start-dev.ps1 -StopOnly" -ForegroundColor Gray

Write-Host "`n🧹 清理所有服務：" -ForegroundColor Cyan
Write-Host "   powershell -ExecutionPolicy Bypass -File start-dev.ps1 -CleanUp" -ForegroundColor Gray

Write-Host "`n"
