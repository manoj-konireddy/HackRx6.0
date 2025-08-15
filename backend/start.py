#!/usr/bin/env python3
"""
Startup script for the Intelligent Query Retrieval System backend.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    try:
        import fastapi
        import sqlalchemy
        import pinecone
        import openai
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ Environment file found")
        return True
    else:
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure your settings")
        return False

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Intelligent Query Retrieval System Backend...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main startup function."""
    print("🔧 Intelligent Query Retrieval System - Backend Startup")
    print("=" * 60)
    
    # Change to backend directory if not already there
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
