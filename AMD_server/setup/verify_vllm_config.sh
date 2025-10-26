#!/bin/bash
# =========================
# verify_vllm_config.sh
# Verify vLLM is running with the expected configuration
# =========================

echo "======================================"
echo "Verifying vLLM Configuration"
echo "======================================"
echo ""

# Check if container is running
echo "1️⃣  Checking if vllm-optimized container is running..."
if ! docker ps | grep -q vllm-optimized; then
    echo "❌ Container 'vllm-optimized' is NOT running!"
    echo ""
    echo "Run this to start it:"
    echo "  bash AMD_server/setup/fix_vllm_CORRECT.sh"
    exit 1
fi
echo "✅ Container is running"
echo ""

# Check max_model_len in logs
echo "2️⃣  Checking max_model_len setting..."
MAX_LEN=$(docker logs vllm-optimized 2>&1 | grep -i "max_model_len" | tail -1)
if [ -z "$MAX_LEN" ]; then
    echo "⚠️  Could not find max_model_len in logs"
    echo "Searching for model configuration..."
    docker logs vllm-optimized 2>&1 | grep -i "max" | head -20
else
    echo "Found: $MAX_LEN"
    if echo "$MAX_LEN" | grep -q "8192"; then
        echo "✅ max_model_len is set to 8192"
    elif echo "$MAX_LEN" | grep -q "4096"; then
        echo "❌ max_model_len is still 4096 (not updated!)"
        echo ""
        echo "The vLLM restart did not apply the new configuration."
        echo "Try running fix_vllm_CORRECT.sh again."
    else
        echo "⚠️  Unexpected max_model_len value"
    fi
fi
echo ""

# Check if server is responding
echo "3️⃣  Testing vLLM server health..."
if curl -s http://localhost:8000/v1/models > /dev/null; then
    echo "✅ Server is responding on port 8000"
    MODEL_INFO=$(curl -s http://localhost:8000/v1/models)
    echo "Models available: $(echo $MODEL_INFO | jq -r '.data[].id' 2>/dev/null || echo $MODEL_INFO)"
else
    echo "❌ Server is not responding on port 8000"
fi
echo ""

# Test with a simple prompt
echo "4️⃣  Testing simple chat completion..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Equall/Saul-7B-Instruct-v1",
        "messages": [
            {"role": "system", "content": "You are a legal assistant."},
            {"role": "user", "content": "What is the rule of law? Answer in one sentence."}
        ],
        "max_tokens": 50,
        "temperature": 0.5
    }')

if echo "$RESPONSE" | grep -q "choices"; then
    echo "✅ Chat completion successful"
    ANSWER=$(echo "$RESPONSE" | jq -r '.choices[0].message.content' 2>/dev/null)
    echo "Response: $ANSWER"
elif echo "$RESPONSE" | grep -q "error"; then
    echo "❌ Chat completion failed with error:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
else
    echo "⚠️  Unexpected response:"
    echo "$RESPONSE"
fi
echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo "If max_model_len is still 4096, the vLLM container needs to be restarted."
echo "If chat completion fails, check the error message above for details."
echo ""
echo "Next steps:"
echo "  - If max_model_len = 4096: Run fix_vllm_CORRECT.sh again"
echo "  - If max_model_len = 8192 but still getting 400 errors: Check actual prompt size"
echo "  - Check full logs: docker logs vllm-optimized 2>&1 | tail -100"
