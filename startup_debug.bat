@echo off
REM Script batch pour lancer le debug de démarrage de Writing Tools
REM Ce script peut être ajouté au démarrage de Windows pour capturer les logs

echo ========================================
echo Writing Tools - Startup Debug Launcher
echo ========================================
echo.

REM Obtenir le répertoire du script
set SCRIPT_DIR=%~dp0
echo Script directory: %SCRIPT_DIR%

REM Changer vers le répertoire du script
cd /d "%SCRIPT_DIR%"
echo Changed to: %CD%

REM Créer le dossier de logs s'il n'existe pas
if not exist "startup_logs" mkdir startup_logs

REM Log de démarrage du script batch
echo %DATE% %TIME% - Startup debug batch started >> startup_logs\batch_debug.log

REM Chercher le bon Python (environnement virtuel du projet)
set PYTHON_EXE=python
set VENV_PYTHON=%SCRIPT_DIR%Windows_and_Linux\myvenv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    echo Found virtual environment Python: %VENV_PYTHON%
    echo %DATE% %TIME% - Using venv Python: %VENV_PYTHON% >> startup_logs\batch_debug.log
    set PYTHON_EXE=%VENV_PYTHON%
) else (
    echo Virtual environment not found, using system Python
    echo %DATE% %TIME% - Using system Python >> startup_logs\batch_debug.log

    REM Vérifier si Python système est disponible
    python --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Python not found in PATH
        echo %DATE% %TIME% - ERROR: Python not found >> startup_logs\batch_debug.log
        pause
        exit /b 1
    )
)

echo Launching startup debug script with: %PYTHON_EXE%
echo %DATE% %TIME% - Launching Python script with: %PYTHON_EXE% >> startup_logs\batch_debug.log

REM Lancer le script Python de debug
"%PYTHON_EXE%" startup_debug.py

REM Log du résultat
if %ERRORLEVEL% equ 0 (
    echo %DATE% %TIME% - Python script completed successfully >> startup_logs\batch_debug.log
) else (
    echo %DATE% %TIME% - Python script failed with error %ERRORLEVEL% >> startup_logs\batch_debug.log
)

echo.
echo Debug session completed. Check startup_logs folder for detailed logs.
echo Press any key to exit...
pause >nul
