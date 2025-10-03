#!/bin/bash

# Script to stop locally running Onyx services

echo "🛑 Stopping Onyx services..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Try to kill by PID files first
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm "$PROJECT_ROOT/logs/backend.pid"
fi

if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm "$PROJECT_ROOT/logs/frontend.pid"
fi

# Fallback: kill by process name
echo "Cleaning up any remaining processes..."
pkill -f 'uvicorn onyx.main' 2>/dev/null || true
pkill -f 'next dev' 2>/dev/null || true

echo "✅ All services stopped"
