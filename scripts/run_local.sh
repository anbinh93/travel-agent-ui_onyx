#!/bin/bash

# Script to run Onyx Backend and Frontend locally (without Docker)
# This script sets up and runs both services on localhost

set -e  # Exit on error

echo "=================================================="
echo "🚀 Starting Onyx Backend + Frontend (Local Mode)"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "\n${YELLOW}Project Root: ${PROJECT_ROOT}${NC}\n"

###################
# 1. PREREQUISITES
###################
echo "=================================================="
echo "📋 Checking Prerequisites..."
echo "=================================================="

# Check Python
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}❌ Python 3.11 not found!${NC}"
    echo "Install Python 3.11: brew install python@3.11"
    exit 1
fi
echo -e "${GREEN}✅ Python 3.11 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found!${NC}"
    echo "Install Node.js: brew install node"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Check if services are available
check_service() {
    local service=$1
    local port=$2
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✅ $service is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service is NOT running on port $port${NC}"
        return 1
    fi
}

echo -e "\n${YELLOW}Checking required services...${NC}"
POSTGRES_OK=false
REDIS_OK=false
VESPA_OK=false
MINIO_OK=false

check_service "PostgreSQL" 5432 && POSTGRES_OK=true || true
check_service "Redis" 6379 && REDIS_OK=true || true
check_service "Vespa" 8081 && VESPA_OK=true || true
check_service "MinIO" 9000 && MINIO_OK=true || true

if [ "$POSTGRES_OK" = false ] || [ "$REDIS_OK" = false ] || [ "$VESPA_OK" = false ] || [ "$MINIO_OK" = false ]; then
    echo -e "\n${YELLOW}⚠️  Some services are not running.${NC}"
    echo -e "${YELLOW}You need to start Docker services first:${NC}"
    echo ""
    echo "  cd $PROJECT_ROOT/deployment/docker_compose"
    echo "  docker compose up -d relational_db cache index minio"
    echo ""
    read -p "Do you want to start these services now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT/deployment/docker_compose"
        docker compose up -d relational_db cache index minio
        echo -e "\n${GREEN}✅ Services started. Waiting 10 seconds for initialization...${NC}"
        sleep 10
    else
        echo -e "${RED}Cannot proceed without required services.${NC}"
        exit 1
    fi
fi

######################
# 2. SETUP BACKEND
######################
echo -e "\n=================================================="
echo "🐍 Setting up Backend..."
echo "=================================================="

cd "$PROJECT_ROOT/backend"

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv .venv
fi

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements/default.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from docker_compose/.env...${NC}"
    cp "$PROJECT_ROOT/deployment/docker_compose/.env" .env
    
    # Update for local development
    cat >> .env << 'EOF'

# Local Development Overrides
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
QDRANT_HOST=localhost
VESPA_HOST=localhost
VESPA_PORT=8081
REDIS_HOST=localhost
REDIS_PORT=6379
MINIO_HOST=localhost
MINIO_PORT=9000

# Disable auth for local dev
AUTH_TYPE=disabled

# API URLs
WEB_DOMAIN=http://localhost:3000
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

# Run Alembic migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
alembic upgrade head || {
    echo -e "${RED}❌ Migration failed. You may need to reset the database.${NC}"
    read -p "Reset database and retry? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Drop and recreate
        cd "$PROJECT_ROOT/deployment/docker_compose"
        docker compose down relational_db -v
        docker compose up -d relational_db
        sleep 5
        cd "$PROJECT_ROOT/backend"
        alembic upgrade head
    else
        exit 1
    fi
}

echo -e "${GREEN}✅ Backend setup complete${NC}"

######################
# 3. SETUP FRONTEND
######################
echo -e "\n=================================================="
echo "⚛️  Setting up Frontend..."
echo "=================================================="

cd "$PROJECT_ROOT/web"

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check .env.local
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local for frontend...${NC}"
    cat > .env.local << 'EOF'
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8080

# Disable auth for local dev
NEXT_PUBLIC_DISABLE_AUTH=true

# Other settings
NEXT_PUBLIC_NEW_CHAT_DIRECTS_TO_SAME_PERSONA=false
NEXT_PUBLIC_THEME=light
EOF
    echo -e "${GREEN}✅ Created .env.local${NC}"
fi

echo -e "${GREEN}✅ Frontend setup complete${NC}"

######################
# 4. START SERVICES
######################
echo -e "\n=================================================="
echo "🚀 Starting Services..."
echo "=================================================="

# Kill any existing processes on these ports
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

echo "Checking for processes on ports 8080 and 3000..."
kill_port 8080
kill_port 3000

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Start Backend
echo -e "\n${YELLOW}Starting Backend on http://localhost:8080${NC}"
cd "$PROJECT_ROOT/backend"
source .venv/bin/activate
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"

nohup python -m uvicorn onyx.main:app --host 0.0.0.0 --port 8080 --reload > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo "   Logs: tail -f $PROJECT_ROOT/logs/backend.log"

# Wait for backend to start
echo -n "Waiting for backend to be ready"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "\n${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Start Frontend
echo -e "\n${YELLOW}Starting Frontend on http://localhost:3000${NC}"
cd "$PROJECT_ROOT/web"

nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "   Logs: tail -f $PROJECT_ROOT/logs/frontend.log"

# Wait for frontend
echo -n "Waiting for frontend to be ready"
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "\n${GREEN}✅ Frontend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

######################
# 5. SUMMARY
######################
echo -e "\n=================================================="
echo "✨ All Services Running!"
echo "=================================================="
echo ""
echo -e "${GREEN}🌐 Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}🔧 Backend API:${NC} http://localhost:8080"
echo -e "${GREEN}📚 API Docs:${NC} http://localhost:8080/docs"
echo -e "${GREEN}❤️  Health Check:${NC} http://localhost:8080/health"
echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Log Files:${NC}"
echo "  Backend: tail -f $PROJECT_ROOT/logs/backend.log"
echo "  Frontend: tail -f $PROJECT_ROOT/logs/frontend.log"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  OR"
echo "  pkill -f 'uvicorn onyx.main'"
echo "  pkill -f 'next dev'"
echo ""
echo "=================================================="

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > "$PROJECT_ROOT/logs/backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/logs/frontend.pid"

echo -e "${GREEN}✅ Setup complete! Opening browser...${NC}"
sleep 2
open http://localhost:3000
