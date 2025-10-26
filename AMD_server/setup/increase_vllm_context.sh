#!/bin/bash
# Increase vLLM context window from 4096 to 8192 tokens
# This gives more headroom for multi-agent prompts

echo "🔧 Increasing vLLM context window..."
echo ""
echo "Current: --max-model-len 4096 (default)"
echo "New:     --max-model-len 8192"
echo ""

# Stop existing vLLM container
echo "Stopping existing vLLM container..."
docker stop vllm-rocm 2>/dev/null
docker rm vllm-rocm 2>/dev/null

# Container configuration
CONTAINER_NAME="vllm-rocm"
MODEL_PATH="/models"
HOST_MODEL_PATH="$HOME/ai-legal-tender/models"
VLLM_PORT=8000

echo "Starting vLLM with increased context window..."

# Start vLLM with 8192 max context length
docker run -d \
  --name $CONTAINER_NAME \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_PTRACE \
  -p $VLLM_PORT:8000 \
  -v $HOST_MODEL_PATH:/models \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  rocm/vllm:latest \
  --host 0.0.0.0 \
  --port 8000 \
  --model /models/Equall--Saul-7B-Instruct-v1 \
  --dtype float16 \
  --max-model-len 8192 \
  --tensor-parallel-size 1

echo ""
echo "✅ vLLM restarted with 8192 token context window!"
echo ""
echo "Benefits:"
echo "  - 2x more context for agent prompts"
echo "  - Can handle larger opinion excerpts"
echo "  - Reduced 400 Bad Request errors"
echo ""
echo "⏳ Wait 30-60 seconds for model to load..."
echo ""
echo "To verify: docker logs -f vllm-rocm | grep 'max_model_len'"
