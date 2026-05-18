$secret = "966320d380a1845e004061caf51fe757"
$body = '{"destination":"xxxxxxxx","events":[{"message":{"text":"test","type":"text","id":"100001"},"timestamp":1462629479859,"source":{"type":"user","userId":"U206d25c2ea6bd87c17655609a0c62d33"},"replyToken":"nHuyWiB7yP5Xw52FIkcQT","type":"message"}]}'

$secretBytes = [System.Text.Encoding]::UTF8.GetBytes($secret)
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = $secretBytes
$hash = $hmac.ComputeHash($bodyBytes)
$signature = [Convert]::ToBase64String($hash)

$uri = "http://localhost:8000/webhook/line"
$headers = @{ "X-Line-Signature" = $signature }

Write-Host "Testing webhook endpoint..."
Write-Host "Signature: $signature"
Write-Host ""

Invoke-WebRequest -Uri $uri -Method Post -Body $body -ContentType "application/json" -Headers $headers -UseBasicParsing | Select-Object StatusCode, StatusDescription
