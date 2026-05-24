@echo off
chcp 65001 >nul
echo ========================================
echo Blog-Python Project Environment Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

echo.
echo [2/4] Creating virtual environment...
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists. Skipping creation.
)

echo.
echo [3/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [4/4] Upgrading pip and installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Environment setup completed!
echo ========================================
echo.
echo To start the server, run: start.bat
echo.
pause