@echo off
setlocal enabledelayedexpansion

echo ===== Writing Tools - Console Log Viewer =====
echo.
echo This script will:
echo 1. Launch Writing Tools executable
echo 2. Show real-time logs in this console window
echo 3. Keep the console open until you press Ctrl+C
echo.

cd /d "%~dp0"

REM Check if executable exists
if not exist "dist\dev\Writing Tools.exe" (
    echo ERROR: Writing Tools.exe not found in dist\dev\
    echo Please run: python scripts\dev_build.py --console
    echo.
    pause
    exit /b 1
)

REM Create log file if it doesn't exist
if not exist "dist\dev\build_dev_debug.log" (
    echo. > "dist\dev\build_dev_debug.log"
)

echo Launching Writing Tools...
echo.

REM Launch the executable in background
start "" "dist\dev\Writing Tools.exe"

REM Wait a moment for the app to start
timeout /t 2 /nobreak >nul

echo ============================================
echo Real-time logs (Press Ctrl+C to stop):
echo ============================================
echo.

REM Monitor the log file in real-time using PowerShell
powershell -Command "& {Get-Content 'dist\dev\build_dev_debug.log' -Wait -Tail 10}"

echo.
echo Log monitoring stopped.
pause
