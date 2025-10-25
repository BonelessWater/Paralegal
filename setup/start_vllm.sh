#!/bin/bash
# Start vLLM inference server on AMD MI300X

echo "Starting vLLM container with ROCm support..."

# Container configuration
CONTAINER_NAME="vllm-rocm"
MODEL_PATH="/models"  # Path inside container
HOST_MODEL_PATH="$HOME/ai-legal-tender/models"  # Path on host
VLLM_PORT=8000

# Stop existing container if running
docker stop $CONTAINER_NAME 2>/dev/null
docker rm $CONTAINER_NAME 2>/dev/null

# Start vLLM container with GPU access
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
  --model /models/llama-3-8b \
  --dtype float16 \
  --max-model-len 4096 \
  --tensor-parallel-size 1

echo ""
echo "✅ vLLM container started!"
echo ""
echo "Container name: $CONTAINER_NAME"
echo "API endpoint: http://localhost:$VLLM_PORT"
echo ""
echo "To check logs: docker logs -f $CONTAINER_NAME"
echo "To test API: curl http://localhost:$VLLM_PORT/v1/models"
echo ""
echo "⏳ Wait 30-60 seconds for model to load, then test with:"
echo "   ./test_vllm.sh"
