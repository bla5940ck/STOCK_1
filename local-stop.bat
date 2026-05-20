@echo off
REM LINE Bot - 本地停止批次檔
REM 簡化版: 停止 Docker 應用

REM 設置 UTF-8 編碼以修復亂碼
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ========================================
echo   LINE Bot 本地停止
echo ========================================
echo.

REM 檢查是否有參數
if "%1"=="clean" goto CLEAN

REM ============================================
REM 停止服務
REM ============================================
echo 🛑 停止服務中...
echo   • 停止容器...
docker-compose down

echo.
echo ✅ 服務已停止！
echo   • 容器已停止但保留
echo   • 卷已保留（數據不會丟失）
echo   • 下次可快速啟動
echo.
echo 💡 提示:
echo   • 重新啟動: local-start.bat
echo   • 完全清理: local-stop.bat clean
echo.
pause
exit /b 0

REM ============================================
REM 完全清理
REM ============================================
:CLEAN
echo 🛑 清理中...
echo   • 停止容器...
echo   • 刪除卷和鏡像...
docker-compose down -v --rmi all

echo.
echo ✅ 已完全清理！
echo   • 所有容器已刪除
echo   • 所有卷已刪除
echo   • 所有鏡像已刪除
echo.
echo 💡 提示:
echo   • 重新啟動: local-start.bat
echo.
pause
exit /b 0
