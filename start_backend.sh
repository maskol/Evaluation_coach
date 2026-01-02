#!/bin/bash

# Initialize and start Evaluation Coach backend

echo "🎯 Initializing Evaluation Coach Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Initialize database
echo "📦 Initializing SQLite database..."
python backend/database.py

# Start FastAPI server
echo "🚀 Starting FastAPI server on port 8850..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8850
