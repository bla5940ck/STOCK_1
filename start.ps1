# LINE Bot Quick Start

param(
    [switch]$Stop,
    [switch]$Clean
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ngrok = "$env:LOCALAPPDATA\ngrok\ngrok.exe"

if ($Stop) {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Push-Location $root
    docker-compose down 2>$null
    Pop-Location
    Stop-Process -Name ngrok -Force -ErrorAction SilentlyContinue
    Write-Host "Done!" -ForegroundColor Green
    exit 0
}

Write-Host "Starting LINE Bot..." -ForegroundColor Cyan

# Start Docker
Write-Host "1. Starting Docker..." -ForegroundColor Cyan
Push-Location $root
docker-compose up -d
Pop-Location

# Wait for app
Write-Host "2. Waiting for app..." -ForegroundColor Cyan
$count = 0
while ($count -lt 30) {
    try {
        $h = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($h.StatusCode -eq 200) {
            Write-Host "App ready!" -ForegroundColor Green
            break
        }
    }
    catch {}
    $count++
    Start-Sleep -Seconds 1
}

# Start ngrok
Write-Host "3. Starting ngrok..." -ForegroundColor Cyan
if (Test-Path $ngrok) {
    Start-Process -FilePath $ngrok -ArgumentList "http", "8000" -WindowStyle Minimized
    Start-Sleep -Seconds 3
    
    try {
        $api = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($api) {
            $data = $api.Content | ConvertFrom-Json
            $url = $data.tunnels[0].public_url
            Write-Host "ngrok ready!" -ForegroundColor Green
            Write-Host "" -ForegroundColor Gray
            Write-Host "Webhook URL: $url/webhook/line" -ForegroundColor Cyan
        }
    }
    catch {}
}

Write-Host "" -ForegroundColor Gray
Write-Host "Ready!" -ForegroundColor Green
Write-Host "Local: http://localhost:8000" -ForegroundColor Gray
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "" -ForegroundColor Gray
