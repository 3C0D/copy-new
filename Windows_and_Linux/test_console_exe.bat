@echo off
echo ===== Testing Console Mode Executable =====
echo.
echo This will launch the Writing Tools executable built with console mode.
echo The console will stay open to show logs in real-time.
echo.
echo Press Ctrl+C to stop the application and close this window.
echo.
echo Press any key to launch the executable...
pause >nul

echo.
echo Launching Writing Tools with console mode...
echo ============================================
echo.

cd /d "%~dp0"

REM Launch the exe and keep console open
start /wait "Writing Tools Console" "dist\dev\Writing Tools.exe"

echo.
echo ============================================
echo Application has closed.
echo Press any key to exit...
pause >nul
