#!/bin/bash
# Test script to validate your Hugging Face model is working
# Run this after starting vLLM to ensure everything is configured correctly

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          Model Validation Test Suite                            ║"
echo "║          For AI Legal Tender Hackathon                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Load environment variables if .env exists
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | grep -v '^$' | xargs)
fi

VLLM_URL="${VLLM_BASE_URL:-http://localhost:8000}"
MODEL_NAME="${MODEL_FOLDER:-llama-3-8b}"

echo "Configuration:"
echo "  Server: $VLLM_URL"
echo "  Model:  $MODEL_NAME"
echo ""

PASSED=0
FAILED=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

pass_test() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail_test() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn_test() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================================
# Test 1: Server Health Check
# ============================================================================
echo "[Test 1/6] Checking vLLM server health..."
if curl -s -o /dev/null -w "%{http_code}" $VLLM_URL/health | grep -q "200"; then
    pass_test "Server is running and healthy"
else
    fail_test "Server not responding at $VLLM_URL"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Start the server: cd setup && ./start_vllm.sh"
    echo "  2. Check Docker: docker ps | grep vllm"
    echo "  3. Check logs: docker logs vllm-rocm"
    exit 1
fi
echo ""

# ============================================================================
# Test 2: Model Listing
# ============================================================================
echo "[Test 2/6] Checking if model is loaded..."
MODEL_RESPONSE=$(curl -s $VLLM_URL/v1/models)

if echo "$MODEL_RESPONSE" | grep -q "data"; then
    LOADED_MODEL=$(echo "$MODEL_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data'][0]['id'] if data.get('data') else 'none')" 2>/dev/null)
    
    if [ ! -z "$LOADED_MODEL" ] && [ "$LOADED_MODEL" != "none" ]; then
        pass_test "Model loaded: $LOADED_MODEL"
    else
        fail_test "No model loaded"
    fi
else
    fail_test "Could not retrieve model information"
fi
echo ""

# ============================================================================
# Test 3: Simple Completion Test
# ============================================================================
echo "[Test 3/6] Testing text completion capability..."
echo -e "${BLUE}Prompt:${NC} 'Explain what a personal injury lawyer does in one sentence.'"

COMPLETION_RESPONSE=$(curl -s $VLLM_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$LOADED_MODEL\",
    \"prompt\": \"Explain what a personal injury lawyer does in one sentence.\",
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }" 2>/dev/null)

if echo "$COMPLETION_RESPONSE" | grep -q "choices"; then
    COMPLETION_TEXT=$(echo "$COMPLETION_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['text'].strip() if 'choices' in data else '')" 2>/dev/null)
    
    if [ ! -z "$COMPLETION_TEXT" ] && [ ${#COMPLETION_TEXT} -gt 20 ]; then
        pass_test "Completion works - generated ${#COMPLETION_TEXT} characters"
        echo -e "${BLUE}Response:${NC} $COMPLETION_TEXT"
    else
        fail_test "Completion response too short or empty"
        echo "Response: $COMPLETION_TEXT"
    fi
else
    fail_test "Completion API failed"
    echo "Error response: $COMPLETION_RESPONSE"
fi
echo ""

# ============================================================================
# Test 4: Chat Completion Test (Agent Simulation)
# ============================================================================
echo "[Test 4/6] Testing chat completion (simulating agent behavior)..."
echo -e "${BLUE}Simulating Client Communication Agent...${NC}"

CHAT_RESPONSE=$(curl -s $VLLM_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$LOADED_MODEL\",
    \"messages\": [
      {
        \"role\": \"system\",
        \"content\": \"You are a compassionate legal assistant. Rewrite client messages as clear, professional responses.\"
      },
      {
        \"role\": \"user\",
        \"content\": \"Client says: hey i got hurt at work and idk what to do???\"
      }
    ],
    \"max_tokens\": 150,
    \"temperature\": 0.7
  }" 2>/dev/null)

if echo "$CHAT_RESPONSE" | grep -q "choices"; then
    CHAT_TEXT=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'].strip() if 'choices' in data else '')" 2>/dev/null)
    
    if [ ! -z "$CHAT_TEXT" ] && [ ${#CHAT_TEXT} -gt 30 ]; then
        pass_test "Chat completion works - generated ${#CHAT_TEXT} characters"
        echo -e "${BLUE}Agent Response:${NC}"
        echo "$CHAT_TEXT" | fold -s -w 70
    else
        fail_test "Chat response too short or empty"
    fi
else
    fail_test "Chat API failed"
    echo "Error response: $CHAT_RESPONSE"
fi
echo ""

# ============================================================================
# Test 5: Response Time Check
# ============================================================================
echo "[Test 5/6] Measuring response time..."

START_TIME=$(date +%s%N)
curl -s $VLLM_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$LOADED_MODEL\",
    \"prompt\": \"Test\",
    \"max_tokens\": 10
  }" > /dev/null 2>&1
END_TIME=$(date +%s%N)

ELAPSED_MS=$(( ($END_TIME - $START_TIME) / 1000000 ))
ELAPSED_SEC=$(echo "scale=2; $ELAPSED_MS / 1000" | bc)

if [ $ELAPSED_MS -lt 5000 ]; then
    pass_test "Response time: ${ELAPSED_SEC}s (excellent)"
elif [ $ELAPSED_MS -lt 10000 ]; then
    pass_test "Response time: ${ELAPSED_SEC}s (good)"
    warn_test "Could be faster - check GPU utilization"
else
    warn_test "Response time: ${ELAPSED_SEC}s (slow)"
    echo "  Consider:"
    echo "    - Using a smaller model"
    echo "    - Checking GPU utilization (rocm-smi)"
    echo "    - Reducing MAX_MODEL_LEN in .env"
fi
echo ""

# ============================================================================
# Test 6: GPU Utilization (if rocm-smi available)
# ============================================================================
echo "[Test 6/6] Checking GPU utilization..."

if command -v rocm-smi &> /dev/null; then
    GPU_USAGE=$(rocm-smi | grep "GPU use" | awk '{print $4}' | head -1)
    
    if [ ! -z "$GPU_USAGE" ]; then
        pass_test "GPU available - Usage: $GPU_USAGE"
        
        if [ "$GPU_USAGE" -lt "10" ]; then
            warn_test "GPU utilization is low - model may not be using GPU"
            echo "  Check Docker GPU access: docker logs vllm-rocm | grep -i gpu"
        fi
    else
        warn_test "Could not read GPU utilization"
    fi
else
    warn_test "rocm-smi not available (normal if not on AMD server)"
    echo "  This test is only relevant on AMD hardware"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "════════════════════════════════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}✓${NC} Passed: $PASSED tests"
echo -e "  ${RED}✗${NC} Failed: $FAILED tests"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your model is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test with specialist agents: cd .. && python3 backend/test_agents.py"
    echo "  2. Integrate with Google ADK orchestrator"
    echo "  3. Build approval interface"
    echo ""
    echo "Performance metrics for your demo:"
    echo "  - Model: $LOADED_MODEL"
    echo "  - Response time: ${ELAPSED_SEC}s"
    echo "  - Server: $VLLM_URL"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Restart vLLM: docker restart vllm-rocm"
    echo "  2. Check logs: docker logs vllm-rocm"
    echo "  3. Verify .env configuration"
    echo "  4. Ensure model downloaded: ls ~/ai-legal-tender/models/"
    echo ""
    exit 1
fi
