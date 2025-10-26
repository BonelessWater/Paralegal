#!/bin/bash
# Fix vLLM context - Use the CORRECT vLLM serve syntax

echo "🔍 Current vLLM containers:"
docker ps -a | grep vllm

echo ""
echo "🛑 Stopping ALL vLLM containers..."
docker stop vllm-rocm vllm-optimized 2>/dev/null
docker rm vllm-rocm vllm-optimized 2>/dev/null

echo ""
echo "🚀 Starting vLLM with CORRECT syntax and 8192 token context..."

# Use vllm serve command (new syntax) instead of passing args to docker run
docker run -d \
  --name vllm-optimized \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_PTRACE \
  -p 8000:8000 \
  -v $HOME/ai-legal-tender/models:/root/.cache/huggingface \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  rocm/vllm:latest \
  vllm serve Equall/Saul-7B-Instruct-v1 \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype float16 \
  --max-model-len 8192 \
  --tensor-parallel-size 1

echo ""
echo "⏳ Waiting for vLLM to start (this takes 30-60 seconds)..."
sleep 10

echo ""
echo "📊 Container status:"
docker ps | grep vllm

echo ""
echo "📋 Checking logs for max_model_len..."
sleep 5
docker logs vllm-optimized 2>&1 | grep -i "max"

echo ""
echo "✅ vLLM should now be running with 8192 token context!"
echo ""
echo "Monitor startup: docker logs -f vllm-optimized"
echo "When you see 'Uvicorn running', vLLM is ready"
echo ""
echo "Then restart API server:"
echo "  cd ~/Paralegal/backend"
echo "  pkill -f api_server.py"
echo "  nohup python api_server.py > /tmp/api_server.log 2>&1 &"
