# Test dynamic Taiwan stock lookup for "健策"
$secret = "966320d380a1845e004061caf51fe757"
$bodyPath = "test-dynamic-tw-stock.json"
$body = Get-Content $bodyPath -Raw

$secretBytes = [System.Text.Encoding]::UTF8.GetBytes($secret)
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = $secretBytes
$hash = $hmac.ComputeHash($bodyBytes)
$signature = [Convert]::ToBase64String($hash)

$headers = @{
    "X-Line-Signature" = $signature
}

Write-Host "Testing dynamic Taiwan stock lookup: 健策" -ForegroundColor Cyan
Write-Host "Signature: $signature" -ForegroundColor Gray
Write-Host ""

$response = Invoke-WebRequest -Uri 'http://localhost:8000/webhook/line' `
    -Method Post `
    -Body $body `
    -ContentType "application/json" `
    -Headers $headers `
    -UseBasicParsing

Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
