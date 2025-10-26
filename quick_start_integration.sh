#!/bin/bash
# Quick Start Script - Frontend-Backend Integration
# Automates setup and testing of the integrated system

set -e  # Exit on error

echo "🚀 Paralegal AI - Frontend-Backend Integration Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "INTEGRATION_GUIDE.md" ]; then
    echo -e "${RED}❌ Error: Must run from Paralegal project root${NC}"
    exit 1
fi

# Step 1: Install Backend Dependencies
echo -e "${YELLOW}Step 1: Installing backend dependencies...${NC}"
cd backend
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo ""

# Step 2: Check vLLM Server
echo -e "${YELLOW}Step 2: Checking vLLM server...${NC}"
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✅ vLLM server is running${NC}"
else
    echo -e "${RED}❌ vLLM server not responding at localhost:8000${NC}"
    echo -e "${YELLOW}Please start vLLM on AMD server:${NC}"
    echo "   ssh amd-knights@134.199.202.8"
    echo "   cd ~/Paralegal/AMD_server/setup"
    echo "   ./start_vllm.sh"
    exit 1
fi
echo ""

# Step 3: Test LLM Client
echo -e "${YELLOW}Step 3: Testing LLM client connection...${NC}"
cd ..
if python backend/llm_client.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ LLM client can connect to vLLM${NC}"
else
    echo -e "${YELLOW}⚠️  LLM client test had issues (non-critical)${NC}"
fi
echo ""

# Step 4: Setup Frontend
echo -e "${YELLOW}Step 4: Setting up frontend...${NC}"
cd frontend

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env from .env.example${NC}"
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies (this may take a minute)...${NC}"
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

cd ..
echo ""

# Step 5: Instructions
echo -e "${GREEN}=================================================="
echo "🎉 Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "To start the system, open 2 terminals:"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend API Server:${NC}"
echo "   cd backend"
echo "   python api_server.py"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend Dev Server:${NC}"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "Then open your browser to: ${GREEN}http://localhost:5173${NC}"
echo ""
echo "To test the API:"
echo "   curl http://localhost:8080/health"
echo ""
echo "For complete guide, see: ${GREEN}INTEGRATION_GUIDE.md${NC}"
echo ""

# Option to start servers now
read -p "Start servers now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Starting backend server...${NC}"
    echo "Backend will run in background. Check backend_server.log for output."
    cd backend
    nohup python api_server.py > ../backend_server.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    
    sleep 3
    
    # Test backend
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is responding${NC}"
    else
        echo -e "${RED}❌ Backend failed to start. Check backend_server.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    
    cd ../frontend
    echo -e "${YELLOW}Starting frontend server...${NC}"
    echo "Frontend will open in your browser automatically."
    npm run dev
else
    echo "Run the commands above manually to start the servers."
fi
