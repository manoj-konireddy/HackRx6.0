@echo off
echo 🔧 Starting Backend with Proper Environment...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Verify packages
echo 📦 Testing critical packages...
python -c "import fastapi, numpy, pinecone; print('✅ All packages available')" || (
    echo ❌ Missing packages, installing...
    pip install numpy faiss-cpu --timeout 60
)

REM Change to backend directory
cd backend

REM Start the server
echo 🚀 Starting server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
