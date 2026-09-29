@echo off
echo.
echo  ==========================================
echo   JARVIS (Mark LV) - Quick Start
echo  ==========================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found on PATH.
    echo         Install Python 3.11-3.13 from https://python.org
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Move to project root (one level up from this folder)
cd /d "%~dp0.."

:: Run setup if requirements haven't been installed yet
if not exist "config\api_keys.json" (
    echo [INFO] First run detected - running setup...
    python setup.py
    if errorlevel 1 (
        echo [ERROR] Setup failed. See error above.
        pause
        exit /b 1
    )
    echo.
)

echo [INFO] Starting JARVIS...
echo        Hold Ctrl+Space to speak.
echo        Say "Hey Jarvis" if wake word is enabled.
echo.
python main.py
pause
