@echo off
chcp 65001 >nul
echo ========================================
echo Starting Blog-Python Server
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Virtual environment activated.
echo [INFO] Starting server...
echo [INFO] Access URL: http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server.
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause