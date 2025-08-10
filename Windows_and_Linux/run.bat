@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Writing Tools - Task Runner
REM This script provides a central place to run development and build tasks.
REM
REM Usage:
REM   run.bat [command]
REM
REM Commands:
REM   dev         - Run the application in development mode.
REM   build-dev   - Create a development build (fast, for testing).
REM   build-final - Create a final release build (clean, for distribution).
REM   help        - Show this help message.
REM
REM If no command is provided, an interactive menu will be shown.
REM ============================================================================

REM --- Script Setup ---
REM Get the directory where this batch file is located and change to it.
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM --- Python Detection ---
set "PYTHON_CMD="
for %%p in (python py python3) do (
    where %%p >nul 2>&1
    if !errorlevel! equ 0 (
        %%p --version 2>&1 | findstr "Python 3" >nul
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=%%p"
            goto :found_python
        )
    )
)
echo [ERROR] Python 3 not found. Please install Python 3 and ensure it's in your PATH.
pause
exit /b 1

:found_python

REM --- Argument Handling ---
set "COMMAND=%1"

REM Capture all arguments after the first one
set "EXTRA_ARGS="
shift
:loop
if "%1"=="" goto :done
set "EXTRA_ARGS=%EXTRA_ARGS% %1"
shift
goto :loop
:done

if /i "%COMMAND%"=="dev"         goto :run_dev
if /i "%COMMAND%"=="build-dev"   goto :run_build_dev
if /i "%COMMAND%"=="build-final" goto :run_build_final
if /i "%COMMAND%"=="help"        goto :show_help
if /i "%COMMAND%"=="/?"          goto :show_help

if not "%COMMAND%"=="" (
    echo [ERROR] Unknown command: %COMMAND%
    goto :show_help
)

REM --- Interactive Menu ---
:menu
cls
echo =================================
echo  Writing Tools - Task Runner
echo =================================
echo.
echo   1. Run Development Mode
echo      (Launched as script)
echo.
echo   2. Create Development Build
echo      (Faster compilation on subsequent runs, keeps your settings)
echo.
echo   3. Create Final Release Build
echo      (exe and files for production)
echo.
echo   4. Exit
echo.
set /p "CHOICE=Enter your choice [1-4]: "

if "%CHOICE%"=="1" goto :run_dev
if "%CHOICE%"=="2" goto :run_build_dev
if "%CHOICE%"=="3" goto :run_build_final
if "%CHOICE%"=="4" goto :exit_script
echo [ERROR] Invalid choice. Please select 1-4.
pause
goto :menu

REM --- Task Definitions ---
:run_dev
echo.
echo [INFO] Starting application in Development Mode...
echo -------------------------------------------------
"%PYTHON_CMD%" "scripts/dev_script.py"%EXTRA_ARGS%
call :handle_task_completion "Development Mode"
goto :post_task_menu

:run_build_dev
echo.
echo [INFO] Starting Development Build...
echo -----------------------------------
"%PYTHON_CMD%" "scripts/dev_build.py"%EXTRA_ARGS%
call :handle_task_completion "Development Build"
goto :post_task_menu

:run_build_final
echo.
echo [INFO] Starting Final Release Build...
echo -----------------------------------
"%PYTHON_CMD%" "scripts/final_build.py"
call :handle_task_completion "Final Release Build"
goto :post_task_menu

:show_help
echo.
echo Usage: run.bat [command] [arguments...]
echo.
echo Commands:
echo   dev          - Run the application in development mode.
echo   build-dev    - Create a development build (fast, for testing).
echo   build-final  - Create a final release build (clean, for distribution).
echo   help         - Show this help message.
echo.
echo Arguments:
echo   --theme [light^|dark^|auto]  - Force a specific theme (default: auto)
echo   --debug                     - Enable debug logging
echo.
echo Examples:
echo   run.bat dev --theme dark --debug
echo   run.bat build-dev --theme light
echo.
echo If no command is provided, an interactive menu will be shown.
echo.
pause
REM Si appelé avec help, retour au menu
if /i "%COMMAND%"=="help" goto :menu
if /i "%COMMAND%"=="/?" goto :menu
goto :exit_script

REM --- Task Completion Handler ---
:handle_task_completion
set "TASK_NAME=%~1"
echo.
echo ========================================
if %errorlevel% neq 0 (
    echo [DONE] %TASK_NAME% finished with errors (Exit code: %errorlevel%)
) else (
    echo [DONE] %TASK_NAME% finished successfully
)
echo ========================================
exit /b

REM --- Post Task Menu ---
:post_task_menu
echo.
echo What would you like to do next?
echo   1. Return to main menu
echo   2. Run the same task again
echo   3. Exit
echo.
set /p "NEXT_CHOICE=Enter your choice [1-3]: "

if "%NEXT_CHOICE%"=="1" goto :menu
if "%NEXT_CHOICE%"=="2" (
    if /i "%COMMAND%"=="dev" goto :run_dev
    if /i "%COMMAND%"=="build-dev" goto :run_build_dev
    if /i "%COMMAND%"=="build-final" goto :run_build_final
)
if "%NEXT_CHOICE%"=="3" goto :exit_script

echo [ERROR] Invalid choice. Returning to main menu...
timeout /t 2 >nul
goto :menu

:exit_script
echo.
echo Goodbye!
timeout /t 1 >nul
endlocal
exit /b 0