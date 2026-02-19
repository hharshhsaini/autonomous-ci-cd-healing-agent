#!/bin/bash

# Development startup script
# Usage: ./start-dev.sh

echo "🚀 Starting RIFT Healing Agent in Development Mode..."
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found!"
    echo "Creating from .env.example..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your API keys"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running!"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✓ Docker is running"
echo "✓ Environment files found"
echo ""

# Ask user which mode
echo "Choose startup mode:"
echo "1) Docker Compose (recommended)"
echo "2) Manual (backend + frontend separately)"
read -p "Enter choice [1-2]: " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🐳 Starting with Docker Compose..."
    docker-compose up --build
elif [ "$choice" = "2" ]; then
    echo ""
    echo "📦 Starting backend..."
    cd backend
    
    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Start backend in background
    uvicorn main:app --reload &
    BACKEND_PID=$!
    
    cd ..
    
    echo "✓ Backend started (PID: $BACKEND_PID)"
    echo ""
    echo "📦 Starting frontend..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Start frontend
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    echo "✓ Frontend started (PID: $FRONTEND_PID)"
    echo ""
    echo "🎉 Development servers running!"
    echo ""
    echo "📍 URLs:"
    echo "  - Frontend: http://localhost:5173"
    echo "  - Backend:  http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
else
    echo "Invalid choice"
    exit 1
fi
