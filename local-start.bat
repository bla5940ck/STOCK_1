@echo off
REM LINE Bot - 本地啟動批次檔
REM 簡化版: 啟動 Docker 應用

REM 設置 UTF-8 編碼以修復亂碼
chcp 65001 >nul

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ========================================
echo   LINE Bot 本地啟動
echo ========================================
echo.

REM 檢查是否有參數
if "%1"=="stop" goto STOP
if "%1"=="clean" goto CLEAN
if "%1"=="rebuild" goto REBUILD

REM ============================================
REM 檢查 Docker
REM ============================================
echo [1/3] 檢查 Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Docker 未運行，請先啟動 Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker 已運行
echo.

REM ============================================
REM 啟動應用
REM ============================================
echo [2/3] 啟動應用...
docker-compose up -d
if errorlevel 1 (
    echo.
    echo ❌ 啟動失敗
    pause
    exit /b 1
)
echo ✅ 容器啟動中...
echo.

REM ============================================
REM 等待應用就緒
REM ============================================
echo [3/3] 等待應用啟動...
setlocal enabledelayedexpansion
set "maxRetries=30"
set "retryCount=0"

:WAIT_LOOP
if !retryCount! geq !maxRetries! goto WAIT_TIMEOUT

timeout /t 1 /nobreak >nul

REM 嘗試連接 health 端點
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -ErrorAction SilentlyContinue; if ($r.StatusCode -eq 200) { exit 0 } } catch {} exit 1" >nul 2>&1

if %ERRORLEVEL% equ 0 goto WAIT_SUCCESS

set /a retryCount=!retryCount! + 1

if %errorlevel% equ 5 goto WAIT_SUCCESS
if !retryCount! lss !maxRetries! goto WAIT_LOOP

:WAIT_TIMEOUT
echo ⚠️  應用啟動超時，但容器應該正在運行
goto SHOW_INFO

:WAIT_SUCCESS
echo ✅ 應用已就緒！
goto SHOW_INFO

REM ============================================
REM 顯示信息
REM ============================================
:SHOW_INFO
echo.
echo ========================================
echo   ✅ 啟動完成！
echo ========================================
echo.
echo 📍 本地地址:
echo   • API: http://localhost:8000
echo   • 文檔: http://localhost:8000/docs
echo   • 健康檢查: http://localhost:8000/health
echo.
echo 📚 常用命令:
echo   • 查看日誌: docker-compose logs -f
echo   • 停止服務: local-stop.bat
echo   • 完全清理: local-start.bat clean
echo   • 重新構建: local-start.bat rebuild
echo.
echo 💡 提示: 需要 ngrok 嗎？使用 start-dev.ps1 代替
echo.
pause
exit /b 0

REM ============================================
REM 停止服務
REM ============================================
:STOP
echo.
echo 🛑 停止服務中...
docker-compose down
echo ✅ 服務已停止
echo.
pause
exit /b 0

REM ============================================
REM 清理服務
REM ============================================
:CLEAN
echo.
echo 🛑 清理中...
echo   • 停止容器...
echo   • 刪除卷和鏡像...
docker-compose down -v --rmi all
echo ✅ 已完全清理！
echo   • 所有容器已刪除
echo   • 所有卷已刪除
echo   • 所有鏡像已刪除
echo.
pause
exit /b 0

REM ============================================
REM 重新構建
REM ============================================
:REBUILD
echo.
echo 🔨 重新構建中...
echo   • 停止容器...
docker-compose down
echo   • 重新構建鏡像...
docker-compose build --no-cache
if errorlevel 1 (
    echo.
    echo ❌ 構建失敗
    pause
    exit /b 1
)
echo   • 啟動容器...
docker-compose up -d
echo ✅ 重新構建完成！
echo.
pause
exit /b 0
