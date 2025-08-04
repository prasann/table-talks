@echo off
REM TableTalk Setup Script for Windows
REM This is a wrapper around the Python-based setup

echo 🗣️  TableTalk Setup
echo ===================
echo.
echo ℹ️  Cross-platform Python setup for Windows
echo.
echo 🚀 Running Python setup script...
echo.

REM Check if Python 3 is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not found.
    echo    Please install Python 3.11+ from: https://python.org
    pause
    exit /b 1
)

REM Run the Python setup script
python "%~dp0setup.py" %*

echo.
echo 💡 For future setups, you can run directly:
echo    python scripts\setup.py

pause
