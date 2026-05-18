# ============================================================
# Auto-update LINE Webhook URL via Cloudflare API
# ============================================================

# 配置
$LINE_CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"  # 需要你的 LINE Access Token
$DOCKER_CONTAINER = "linebot-us-stock"

Write-Host "📱 LINE Webhook URL 自動更新工具" -ForegroundColor Cyan
Write-Host "=" * 50

# 步驟 1：等待 Tunnel 啟動
Write-Host "⏳ 等待 Cloudflare Tunnel 啟動..." -ForegroundColor Yellow
Start-Sleep 5

# 步驟 2：提取 Tunnel URL
$maxAttempts = 20
$attempt = 0
$tunnelUrl = $null

while ($attempt -lt $maxAttempts -and -not $tunnelUrl) {
    $logs = docker logs $DOCKER_CONTAINER 2>$null | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -All
    
    if ($logs) {
        # 提取最後一個 URL（最新的）
        $matches = [regex]::Matches($logs.Line, 'https://([a-z0-9-]+)\.trycloudflare\.com')
        if ($matches.Count -gt 0) {
            $tunnelUrl = $matches[-1].Value
            Write-Host "✅ 找到 Tunnel URL: $tunnelUrl" -ForegroundColor Green
        }
    }
    
    if (-not $tunnelUrl) {
        Write-Host "⏳ 嘗試 $($attempt + 1)/$maxAttempts..." -ForegroundColor Gray
        Start-Sleep 2
        $attempt++
    }
}

if ($tunnelUrl) {
    $webhookUrl = "$tunnelUrl/webhook/line"
    Write-Host "🔗 Webhook URL: $webhookUrl" -ForegroundColor Green
    
    # 複製到剪貼板
    $webhookUrl | Set-Clipboard
    Write-Host "✅ URL 已複製到剪貼板！" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "📋 下一步："
    Write-Host "1. 去 https://developers.line.biz/"
    Write-Host "2. 在 'Webhook URL' 欄位貼上上面的 URL"
    Write-Host "3. 點 'Verify' 按鈕"
    Write-Host "4. 勾選 'Use webhook'"
} else {
    Write-Host "❌ 無法提取 Tunnel URL，請檢查 Docker 日誌" -ForegroundColor Red
}
