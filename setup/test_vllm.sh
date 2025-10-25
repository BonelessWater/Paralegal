#!/bin/bash
# Test vLLM API endpoint

echo "Testing vLLM API on AMD MI300X..."
echo ""

VLLM_URL="http://localhost:8000"

# Test 1: Check if server is running
echo "[Test 1] Checking if vLLM server is accessible..."
if curl -s -o /dev/null -w "%{http_code}" $VLLM_URL/health | grep -q "200"; then
    echo "✅ Server is running"
else
    echo "❌ Server not responding. Is the container running?"
    echo "   Try: docker logs vllm-rocm"
    exit 1
fi

# Test 2: List available models
echo ""
echo "[Test 2] Listing available models..."
curl -s $VLLM_URL/v1/models | python3 -m json.tool

# Test 3: Simple completion test
echo ""
echo "[Test 3] Testing text completion..."
echo "Sending prompt: 'Explain what a personal injury lawyer does in one sentence.'"
echo ""

curl -s $VLLM_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-8b",
    "prompt": "Explain what a personal injury lawyer does in one sentence.",
    "max_tokens": 100,
    "temperature": 0.7
  }' | python3 -m json.tool

# Test 4: Chat completion test (for agent interactions)
echo ""
echo ""
echo "[Test 4] Testing chat completion (for specialist agents)..."
echo "Simulating Client Communication Guru agent..."
echo ""

curl -s $VLLM_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-8b",
    "messages": [
      {
        "role": "system",
        "content": "You are a compassionate legal assistant. Rewrite client messages as clear, empathetic responses."
      },
      {
        "role": "user",
        "content": "Client says: hey um i got hurt at work and idk what to do??? my boss said its my fault but the floor was wet and there was no sign"
      }
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }' | python3 -m json.tool

echo ""
echo ""
echo "========================================="
echo "✅ vLLM API Tests Complete!"
echo "========================================="
echo ""
echo "If all tests passed, your AMD setup is ready!"
echo ""
echo "Performance stats to document for demo:"
echo "  - Check inference speed: docker logs vllm-rocm | grep 'tokens/s'"
echo "  - GPU utilization: rocm-smi"
echo "  - Model memory usage: docker stats vllm-rocm"
