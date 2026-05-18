@echo off
REM LINE Bot - Stop All Services (停止所有服務)
REM ============================================

cd /d "%~dp0"

echo.
echo ==========================================
echo   LINE Bot - Stopping Services
echo ==========================================
echo.

REM 執行 PowerShell 停止腳本
powershell -ExecutionPolicy Bypass -File "%~dp0stop-all.ps1"

REM 保持窗口開啟讓用戶看到輸出
pause
