# LINE Bot - 本地啟動腳本
# 簡化版: 僅啟動 Docker，無需 ngrok

param(
    [switch]$Stop,     # 停止服務
    [switch]$Clean,    # 完全清理（刪除容器和鏡像）
    [switch]$Rebuild   # 重新構建鏡像
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerComposePath = "$projectRoot\docker-compose.yml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LINE Bot 本地啟動腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================
# 停止服務
# ============================================
if ($Stop -or $Clean -or $Rebuild) {
    Write-Host "`n🛑 停止服務中..." -ForegroundColor Yellow
    
    Push-Location $projectRoot
    
    if ($Clean) {
        Write-Host "  • 清理容器和鏡像..." -ForegroundColor Gray
        docker-compose down -v --rmi all 2>$null
    } elseif ($Rebuild) {
        Write-Host "  • 停止容器..." -ForegroundColor Gray
        docker-compose down 2>$null
    } else {
        Write-Host "  • 停止容器..." -ForegroundColor Gray
        docker-compose down 2>$null
    }
    
    Pop-Location
    
    if ($Stop -and -not $Rebuild) {
        Write-Host "✅ 服務已停止`n" -ForegroundColor Green
        exit 0
    }
    
    Write-Host "✅ 已停止`n" -ForegroundColor Green
}

# ============================================
# 檢查 Docker
# ============================================
Write-Host "`n🐳 檢查 Docker..." -ForegroundColor Cyan
$dockerStatus = docker ps 2>$null
if (-not $?) {
    Write-Host "❌ Docker 未運行，請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker 已運行" -ForegroundColor Green

# ============================================
# 啟動服務
# ============================================
Write-Host "`n▶️  啟動應用..." -ForegroundColor Cyan
Push-Location $projectRoot

if ($Rebuild) {
    Write-Host "  • 重新構建鏡像..." -ForegroundColor Gray
    docker-compose build --no-cache
    if (-not $?) {
        Write-Host "❌ 構建失敗" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

Write-Host "  • 啟動容器..." -ForegroundColor Gray
docker-compose up -d
if (-not $?) {
    Write-Host "❌ 啟動失敗" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# ============================================
# 等待應用就緒
# ============================================
Write-Host "`n⏳ 等待應用啟動..." -ForegroundColor Cyan
$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest `
            -Uri "http://localhost:8000/health" `
            -UseBasicParsing `
            -ErrorAction SilentlyContinue
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ 應用已就緒！" -ForegroundColor Green
            break
        }
    }
    catch {
        # 應用還未就緒
    }
    
    $retryCount++
    Start-Sleep -Seconds 1
    
    if ($retryCount % 5 -eq 0) {
        Write-Host "  • 等待中... ($retryCount/$maxRetries)" -ForegroundColor Gray
    }
}

if ($retryCount -ge $maxRetries) {
    Write-Host "⚠️  應用啟動超時，但容器應該正在運行" -ForegroundColor Yellow
}

# ============================================
# 顯示信息
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ✅ 啟動完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "📍 本地地址" -ForegroundColor Cyan
Write-Host "  • API: http://localhost:8000" -ForegroundColor Gray
Write-Host "  • 文檔: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  • 健康檢查: http://localhost:8000/health" -ForegroundColor Gray

Write-Host ""
Write-Host "🐳 Docker 容器" -ForegroundColor Cyan
docker-compose ps | Select-Object -Skip 1 | ForEach-Object {
    Write-Host "  $PSItem" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📚 常用命令" -ForegroundColor Cyan
Write-Host "  • 查看日誌: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • 停止服務: powershell -ExecutionPolicy Bypass -File local-start.ps1 -Stop" -ForegroundColor Gray
Write-Host "  • 完全清理: powershell -ExecutionPolicy Bypass -File local-start.ps1 -Clean" -ForegroundColor Gray
Write-Host "  • 重新構建: powershell -ExecutionPolicy Bypass -File local-start.ps1 -Rebuild" -ForegroundColor Gray

Write-Host ""
Write-Host "💡 提示: 需要 ngrok 嗎？使用 start-dev.ps1 代替此腳本" -ForegroundColor Cyan
Write-Host ""
