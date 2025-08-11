@echo off
echo ===== Writing Tools - Console Mode Test =====
echo.

cd /d "%~dp0"

REM Check if console build exists
if not exist "dist\dev\Writing Tools.exe" (
    echo ERROR: Console build not found!
    echo.
    echo Please run first:
    echo   python scripts\dev_build.py --console
    echo.
    pause
    exit /b 1
)

echo Launching Writing Tools in console mode...
echo You should see logs directly in this window.
echo.
echo Press Ctrl+C to stop the application.
echo ==========================================
echo.

REM Run the executable directly in this console (no start command)
"dist\dev\Writing Tools.exe"

echo.
echo ==========================================
echo Application has exited.
pause
