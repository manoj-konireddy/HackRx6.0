#!/bin/bash

# Intelligent Query Retrieval System Setup Script

set -e

echo "🚀 Setting up Intelligent Query Retrieval System..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running the application"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads logs

# Check if PostgreSQL is running
if command -v psql >/dev/null 2>&1; then
    echo "🐘 PostgreSQL found. Checking connection..."
    if psql -h localhost -U postgres -c '\q' 2>/dev/null; then
        echo "✅ PostgreSQL connection successful"
        
        # Create database if it doesn't exist
        echo "🗄️ Creating database if it doesn't exist..."
        psql -h localhost -U postgres -c "CREATE DATABASE intelligent_query_db;" 2>/dev/null || echo "Database already exists or creation failed"
    else
        echo "⚠️ PostgreSQL is not running or connection failed"
        echo "Please start PostgreSQL and ensure it's accessible"
    fi
else
    echo "⚠️ PostgreSQL not found. Please install and configure PostgreSQL"
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v || echo "⚠️ Some tests failed. Check the output above."

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Ensure PostgreSQL is running and accessible"
echo "3. Run the application: python -m uvicorn app.main:app --reload"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For production deployment, see README.md"
