#!/bin/bash

echo "🛑 Stopping Evaluation Coach Application..."

# Stop backend (port 8850)
BACKEND_PIDS=$(lsof -ti:8850 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    echo "   Stopping backend (port 8850)..."
    kill -15 $BACKEND_PIDS 2>/dev/null
    sleep 2
    # Force kill if still running
    if lsof -ti:8850 >/dev/null 2>&1; then
        kill -9 $BACKEND_PIDS 2>/dev/null
    fi
    echo "   ✅ Backend stopped"
else
    echo "   ℹ️  Backend not running"
fi

# Stop frontend (port 8800)
FRONTEND_PIDS=$(lsof -ti:8800 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "   Stopping frontend (port 8800)..."
    kill -15 $FRONTEND_PIDS 2>/dev/null
    sleep 2
    # Force kill if still running
    if lsof -ti:8800 >/dev/null 2>&1; then
        kill -9 $FRONTEND_PIDS 2>/dev/null
    fi
    echo "   ✅ Frontend stopped"
else
    echo "   ℹ️  Frontend not running"
fi

echo ""
echo "✅ All servers stopped"
