# ============================================
# Docker 和 WSL 2 自動安裝腳本 (Windows 11)
# ============================================

# 檢查管理員權限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    Write-Host "❌ 此腳本需要管理員權限" -ForegroundColor Red
    Write-Host "✅ 解決方法：以管理員身份運行 PowerShell，然後執行：" -ForegroundColor Yellow
    Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    Write-Host "   .\install-docker.ps1" -ForegroundColor Cyan
    exit 1
}

Write-Host "🚀 開始安裝 Docker 和 WSL 2..." -ForegroundColor Green
Write-Host ""

# 步驟 1: 安裝 WSL 2
Write-Host "📦 步驟 1/3: 安裝 WSL 2..." -ForegroundColor Cyan
try {
    wsl --install -d Ubuntu --no-launch
    Write-Host "✅ WSL 2 安裝成功" -ForegroundColor Green
} catch {
    Write-Host "⚠️  WSL 2 安裝遇到問題（這不是致命錯誤）" -ForegroundColor Yellow
}

# 步驟 2: 啟用 Hyper-V 和虛擬化功能
Write-Host ""
Write-Host "📦 步驟 2/3: 啟用 Hyper-V..." -ForegroundColor Cyan
try {
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
    Write-Host "✅ Hyper-V 啟用成功" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Hyper-V 啟用遇到問題：$_" -ForegroundColor Yellow
}

# 步驟 3: 下載並安裝 Docker Desktop
Write-Host ""
Write-Host "📦 步驟 3/3: 下載 Docker Desktop..." -ForegroundColor Cyan
Write-Host "下載地址: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
Write-Host ""
Write-Host "👉 請執行以下步驟：" -ForegroundColor Green
Write-Host "   1. 打開上面的鏈接" -ForegroundColor Cyan
Write-Host "   2. 點擊 'Download for Windows'" -ForegroundColor Cyan
Write-Host "   3. 運行下載的 Docker Desktop Installer.exe" -ForegroundColor Cyan
Write-Host "   4. 完成安裝並重啟電腦" -ForegroundColor Cyan
Write-Host ""

# 嘗試自動下載（如果有 PowerShell 5.1+）
Write-Host "🤖 嘗試自動下載..." -ForegroundColor Yellow
$DownloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$InstallerPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    Write-Host "下載中... (約 500MB)" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $InstallerPath -UseBasicParsing
    
    if (Test-Path $InstallerPath) {
        Write-Host "✅ 下載完成" -ForegroundColor Green
        Write-Host "📍 路徑: $InstallerPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⏳ 開始安裝..." -ForegroundColor Yellow
        
        # 運行安裝程序
        & $InstallerPath
        
        Write-Host "✅ 安裝程序已啟動" -ForegroundColor Green
    } else {
        throw "下載失敗"
    }
} catch {
    Write-Host "⚠️  自動下載失敗：$_" -ForegroundColor Yellow
    Write-Host "💡 請手動下載：https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "═" * 60 -ForegroundColor Green
Write-Host "📝 安裝完成後的步驟：" -ForegroundColor Green
Write-Host "═" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "1️⃣  重啟電腦" -ForegroundColor Cyan
Write-Host "   ► 按鈕 > 電源 > 重新啟動" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  打開 Docker Desktop" -ForegroundColor Cyan
Write-Host "   ► 開始菜單搜索 'Docker Desktop'" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  驗證安裝" -ForegroundColor Cyan
Write-Host "   ► 打開 PowerShell 執行：" -ForegroundColor Gray
Write-Host "   ► docker --version" -ForegroundColor Gray
Write-Host "   ► 應該看到: Docker version XXX" -ForegroundColor Gray
Write-Host ""
Write-Host "4️⃣  啟動應用" -ForegroundColor Cyan
Write-Host "   ► cd C:\Users\bla59\OneDrive\Desktop\SDD\US_STOCK" -ForegroundColor Gray
Write-Host "   ► docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "═" * 60 -ForegroundColor Green
