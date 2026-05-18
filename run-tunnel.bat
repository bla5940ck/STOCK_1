@echo off
REM Cloudflare Tunnel Launcher with Output Logging
REM 啟動並記錄 Cloudflare Tunnel 輸出

setlocal enabledelayedexpansion

set TUNNEL_LOG=%TEMP%\cloudflared-latest.log
set CLOUDFLARED=%LOCALAPPDATA%\cloudflared.exe

REM 清除舊日誌
if exist "%TUNNEL_LOG%" del "%TUNNEL_LOG%"

REM 啟動 cloudflared 並將輸出同時寫入日誌和屏幕
echo Cloudflare Tunnel Starting...
echo.

"%CLOUDFLARED%" tunnel --url http://localhost:8000 | tee "%TUNNEL_LOG%"
