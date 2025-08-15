@echo off
echo 🚀 Starting Frontend Server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Start the frontend server
echo 🌐 Starting frontend on http://localhost:3000
echo 📋 Make sure backend is running on http://localhost:8000
echo.
python serve.py

pause
