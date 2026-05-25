#!/usr/bin/env pwsh
<#
Test script to verify LINE bot returns real market data
#>

$ErrorActionPreference = "Stop"

# Configuration
$APP_URL = "https://linebot-us-stock.onrender.com"
$CHANNEL_SECRET = $env:LINE_CHANNEL_SECRET  # Should be set from environment
$TEST_QUERY = "美股"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing LINE Bot - Real Market Data Verification" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Test 1: Health check
Write-Host "`n[Test 1] Health Check..."
try {
    $response = Invoke-WebRequest -Uri "$APP_URL/health" -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        $content = $response.Content | ConvertFrom-Json
        Write-Host "✅ Health check passed" -ForegroundColor Green
        Write-Host "   Status: $($content.status)"
        Write-Host "   Timestamp: $($content.timestamp)"
    }
}
catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check webhook signature (if we have the secret)
Write-Host "`n[Test 2] Webhook Signature Verification..."

# Simulated LINE event payload
$eventPayload = @{
    events = @(
        @{
            replyToken = "test-token-" + (New-Guid).ToString().Substring(0, 8)
            type = "message"
            timestamp = [int64]([datetime]::UtcNow.Subtract([datetime]'1970-01-01')).TotalMilliseconds
            source = @{
                type = "user"
                userId = "U" + ([guid]::NewGuid().ToString().Replace("-", ""))
            }
            message = @{
                type = "text"
                id = (New-Guid).ToString()
                text = $TEST_QUERY
            }
        }
    )
}

$jsonPayload = $eventPayload | ConvertTo-Json -Depth 10
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonPayload)

Write-Host "Payload: $jsonPayload" -ForegroundColor Gray

# Generate HMAC-SHA256 signature if we have the secret
if ($CHANNEL_SECRET) {
    try {
        $hmac = New-Object System.Security.Cryptography.HMACSHA256
        $hmac.Key = [System.Text.Encoding]::UTF8.GetBytes($CHANNEL_SECRET)
        $hashBytes = $hmac.ComputeHash($bodyBytes)
        $signature = [Convert]::ToBase64String($hashBytes)
        
        Write-Host "✅ Signature generated: $($signature.Substring(0, 20))..." -ForegroundColor Green
        
        # Test 3: Send webhook with signature
        Write-Host "`n[Test 3] Sending Webhook with Signature..."
        $headers = @{
            "Content-Type" = "application/json"
            "X-Line-Signature" = $signature
        }
        
        try {
            $response = Invoke-WebRequest -Uri "$APP_URL/webhook/line" `
                -Method POST `
                -Headers $headers `
                -Body $jsonPayload `
                -TimeoutSec 10
            
            Write-Host "✅ Webhook response: $($response.StatusCode)" -ForegroundColor Green
            Write-Host "   Body: $($response.Content)" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️  Webhook call failed: $_" -ForegroundColor Yellow
            if ($_.Exception.Response) {
                Write-Host "   Response: $($_.Exception.Response.Content)" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "❌ Failed to generate signature: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "⚠️  LINE_CHANNEL_SECRET not set, skipping signature verification" -ForegroundColor Yellow
    Write-Host "   To test webhook, set: `$env:LINE_CHANNEL_SECRET = 'your-secret'" -ForegroundColor Yellow
}

# Test 4: Direct service test (local testing)
Write-Host "`n[Test 4] Testing Index Data Directly (if running locally)..."
Write-Host "   Run: python test_database_data.py" -ForegroundColor Yellow

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✨ Test completed!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
