@echo off
title Pinedit - Starting...
echo.
echo   ============================
echo     Pinedit - Photo Editor
echo   ============================
echo.

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment found.
)

:: Activate venv and install dependencies
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Launch the app
echo [3/3] Starting Pinedit...
echo.
echo   App running at: http://localhost:5000
echo   Press Ctrl+C to stop.
echo.

:: Open browser after a short delay
start "" http://localhost:5000

:: Run Flask
python app.py
