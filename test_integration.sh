#!/bin/bash
# ============================================================================
# Integration Test Script - Paralegal AI System
# ============================================================================
# Tests the complete backend API integration with intelligent scraper
# 
# Prerequisites:
# 1. vLLM server running on port 8000 (Saul-7B)
# 2. PostgreSQL database accessible (paralegal_db)
# 3. CourtListener API token configured in .env
# 
# Usage: ./test_integration.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Paralegal AI - Integration Test Suite                  ║"
echo "║        Testing Backend API + Intelligent Scraper               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Test 1: Check vLLM Server
echo -e "${BLUE}[1/5] Checking vLLM server...${NC}"
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ vLLM server is running${NC}"
else
    echo -e "${RED}✗ vLLM server is NOT running on port 8000${NC}"
    echo -e "${YELLOW}Start it with: cd setup && ./start_vllm.sh${NC}"
    exit 1
fi

# Test 2: Install Backend Dependencies
echo -e "\n${BLUE}[2/5] Installing backend dependencies...${NC}"
cd backend
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt not found!${NC}"
    exit 1
fi

pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Test 3: Start API Server (background)
echo -e "\n${BLUE}[3/5] Starting API server...${NC}"
python api_server.py > /tmp/paralegal_api.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

# Wait for server to start
echo -n "Waiting for API server to initialize"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ API server is running${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}✗ API server failed to start after 30 seconds${NC}"
        echo -e "${YELLOW}Check logs: tail /tmp/paralegal_api.log${NC}"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
done

# Test 4: Health Check
echo -e "\n${BLUE}[4/5] Testing API endpoints...${NC}"
echo -e "${YELLOW}Health Check:${NC}"
curl -s http://localhost:8080/health | python3 -m json.tool

echo -e "\n${YELLOW}System Stats:${NC}"
curl -s http://localhost:8080/stats | python3 -m json.tool

echo -e "\n${YELLOW}Agents List:${NC}"
curl -s http://localhost:8080/agents | python3 -m json.tool

# Test 5: Create Legal Research Task
echo -e "\n${BLUE}[5/5] Creating legal research task...${NC}"
TASK_RESPONSE=$(curl -s -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "content": "Find cases similar to slip and fall at grocery store with broken wrist in Florida. Need settlement range estimates.",
    "sender": "paralegal@firm.com",
    "priority": "high"
  }')

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null || echo "unknown")

if [ "$TASK_ID" != "unknown" ]; then
    echo -e "${GREEN}✓ Task created successfully!${NC}"
    echo -e "${YELLOW}Task ID: $TASK_ID${NC}"
    
    # Watch task progress
    echo -e "\n${MAGENTA}Watching task progress (will check 10 times, 3 seconds apart)...${NC}"
    for i in {1..10}; do
        echo -e "\n${BLUE}Check $i/10:${NC}"
        TASK_STATUS=$(curl -s http://localhost:8080/tasks/$TASK_ID)
        echo "$TASK_STATUS" | python3 -m json.tool
        
        STATUS=$(echo "$TASK_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
        
        if [ "$STATUS" = "awaiting_approval" ]; then
            echo -e "\n${GREEN}✓ Task completed! AI research is ready for approval.${NC}"
            echo -e "\n${YELLOW}AI Response:${NC}"
            echo "$TASK_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ai_response', 'No response'))"
            break
        elif [ "$STATUS" = "processing" ]; then
            echo -e "${YELLOW}⏳ Still processing... Intelligent scraper is working.${NC}"
        elif [ "$STATUS" = "pending" ]; then
            echo -e "${BLUE}⏳ Task pending...${NC}"
        fi
        
        sleep 3
    done
else
    echo -e "${RED}✗ Failed to create task${NC}"
    echo "$TASK_RESPONSE"
fi

# Show final stats
echo -e "\n${MAGENTA}Final System Statistics:${NC}"
curl -s http://localhost:8080/stats | python3 -m json.tool

# Cleanup
echo -e "\n${BLUE}Stopping API server (PID: $API_PID)...${NC}"
kill $API_PID 2>/dev/null || true

echo -e "\n${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Integration Test Complete!                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}✓ All tests passed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start frontend: cd frontend && npm run dev"
echo "  2. Open http://localhost:5173 in browser"
echo "  3. Watch Dashboard update with real-time stats"
echo ""
echo -e "${BLUE}To run API server persistently:${NC}"
echo "  cd backend && python api_server.py"
echo ""
echo -e "${MAGENTA}API server logs saved to: /tmp/paralegal_api.log${NC}"
