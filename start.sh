#!/bin/bash

# Start both Frontend and Backend servers for Evaluation Coach

echo "🎯 Starting Evaluation Coach Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   Stopped backend (PID: $BACKEND_PID)"
    fi
    
    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   Stopped frontend (PID: $FRONTEND_PID)"
    fi
    
    echo "✅ All servers stopped"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup INT TERM

# Activate virtual environment
source venv/bin/activate

# Initialize database if needed
echo "📦 Checking database..."
python backend/database.py
echo ""

# Start Backend Server
echo "🚀 Starting Backend API on port 8850..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8850 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "   Backend PID: $BACKEND_PID (logs: backend.log)"
echo ""

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! curl -s http://localhost:8850/api/health > /dev/null 2>&1; then
    echo "⚠️  Backend may still be starting up..."
else
    echo "✅ Backend is responding"
fi
echo ""

# Start Frontend Server
echo "🎨 Starting Frontend on port 8800..."
cd frontend
python3 -m http.server 8800 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID (logs: frontend.log)"
echo ""

# Display access information
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Evaluation Coach is running!"
echo ""
echo "📱 Frontend:  http://localhost:8800"
echo "🔌 Backend:   http://localhost:8850"
echo "📚 API Docs:  http://localhost:8850/docs"
echo ""
echo "📊 View logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for user to press Ctrl+C
wait
