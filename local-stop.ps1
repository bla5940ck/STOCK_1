# LINE Bot - 本地停止腳本
# 簡化版: 僅停止 Docker 容器

param(
    [switch]$Clean      # 完全清理（刪除容器和鏡像）
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LINE Bot 本地停止腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n🛑 停止服務中..." -ForegroundColor Yellow

Push-Location $projectRoot

if ($Clean) {
    Write-Host "  • 清理容器、卷和鏡像..." -ForegroundColor Gray
    Write-Host "    (使用 -Clean 參數)" -ForegroundColor DarkGray
    docker-compose down -v --rmi all 2>$null
    
    Write-Host "`n✅ 已完全清理！" -ForegroundColor Green
    Write-Host "  • 所有容器已刪除" -ForegroundColor Gray
    Write-Host "  • 所有卷已刪除" -ForegroundColor Gray
    Write-Host "  • 所有鏡像已刪除" -ForegroundColor Gray
} else {
    Write-Host "  • 停止容器..." -ForegroundColor Gray
    docker-compose down 2>$null
    
    Write-Host "`n✅ 服務已停止！" -ForegroundColor Green
    Write-Host "  • 容器已停止但保留" -ForegroundColor Gray
    Write-Host "  • 卷已保留（數據不會丟失）" -ForegroundColor Gray
    Write-Host "  • 下次可快速啟動" -ForegroundColor Gray
}

Pop-Location

Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "  • 重新啟動: powershell -ExecutionPolicy Bypass -File local-start.ps1" -ForegroundColor Gray
Write-Host "  • 完全清理: powershell -ExecutionPolicy Bypass -File local-stop.ps1 -Clean" -ForegroundColor Gray
Write-Host ""
