@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ========================================
echo   Export Copilot Chat Records
echo ========================================
echo.
python scripts\export_chat.py --latest %*
echo.
pause
