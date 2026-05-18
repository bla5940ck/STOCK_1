@echo off
REM LINE Bot - One-Click Startup
REM All services in Docker Compose

cd /d "%~dp0"

echo.
echo ==========================================
echo   LINE Bot - Starting Services
echo ==========================================
echo.

REM Run the PowerShell startup script
powershell -ExecutionPolicy Bypass -File "%~dp0start-all-docker.ps1"

REM Keep window open
pause
