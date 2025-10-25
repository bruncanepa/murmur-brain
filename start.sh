#!/bin/bash

# Local Brain - Start Script
# Runs both Python FastAPI server and Electron app

set -e

echo "🚀 Starting Local Brain..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://127.0.0.1:11434/api/tags &> /dev/null; then
    echo -e "${RED}⚠️  Warning: Ollama is not running${NC}"
    echo "   Please start Ollama: ollama serve"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Shutting down...${NC}"

    # Kill tail process
    if [ ! -z "$TAIL_PID" ]; then
        kill $TAIL_PID 2>/dev/null || true
    fi

    # Kill Python server
    if [ ! -z "$PYTHON_PID" ]; then
        echo "Stopping Python server (PID: $PYTHON_PID)..."
        kill $PYTHON_PID 2>/dev/null || true
    fi

    # Kill Electron app
    if [ ! -z "$ELECTRON_PID" ]; then
        echo "Stopping Electron app (PID: $ELECTRON_PID)..."
        kill $ELECTRON_PID 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start Python server in background
echo -e "${BLUE}📦 Starting Python FastAPI server...${NC}"
cd server
python3 main.py > ../logs/python-server.log 2>&1 &
PYTHON_PID=$!
cd ..

echo -e "${GREEN}✓ Python server started (PID: $PYTHON_PID)${NC}"
echo "  Log: logs/python-server.log"
echo ""

# Wait for Python server to write port file
echo "⏳ Waiting for Python server to assign port..."
for i in {1..30}; do
    if [ -f .api-port ]; then
        API_PORT=$(cat .api-port)
        echo -e "${GREEN}✓ Python server assigned port: $API_PORT${NC}"
        break
    fi

    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Python server failed to start${NC}"
        echo "Check logs/python-server.log for details"
        exit 1
    fi

    sleep 1
done

# Verify server is responding
echo "⏳ Checking server health..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:$API_PORT/api/health &> /dev/null; then
        echo -e "${GREEN}✓ Python server is ready${NC}"
        break
    fi

    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Python server not responding${NC}"
        echo "Check logs/python-server.log for details"
        exit 1
    fi

    sleep 1
done

echo ""

# Start Electron app
echo -e "${BLUE}🖥️  Starting Electron app...${NC}"
NODE_OPTIONS="--max-old-space-size=8192 --expose-gc" npm start > logs/electron.log 2>&1 &
ELECTRON_PID=$!

echo -e "${GREEN}✓ Electron app started (PID: $ELECTRON_PID)${NC}"
echo ""

echo -e "${GREEN}✅ Local Brain is running!${NC}"
echo ""
echo "Python API: http://127.0.0.1:$API_PORT"
echo "API Docs:   http://127.0.0.1:$API_PORT/docs"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Streaming logs (Press Ctrl+C to stop all services)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Stream both log files with labels
tail -f logs/python-server.log logs/electron.log 2>/dev/null &
TAIL_PID=$!

# Wait for tail process
wait $TAIL_PID
