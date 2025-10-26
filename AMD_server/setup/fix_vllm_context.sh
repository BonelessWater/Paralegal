#!/bin/bash
# Fix vLLM context window - Simple version

echo "🔍 Checking current vLLM container..."
docker ps -a | grep vllm

echo ""
echo "🔍 Checking current vLLM logs for model and max_model_len..."
docker logs vllm-rocm 2>&1 | grep -E "model|max_model_len" | tail -20

echo ""
echo "❓ What model path should we use?"
echo "Options:"
echo "  1. /models/Equall--Saul-7B-Instruct-v1"
echo "  2. /models/llama-3-8b" 
echo "  3. Check what's in /models directory"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    MODEL_PATH="/models/Equall--Saul-7B-Instruct-v1"
    ;;
  2)
    MODEL_PATH="/models/llama-3-8b"
    ;;
  3)
    echo "Listing models..."
    docker run --rm -v $HOME/ai-legal-tender/models:/models rocm/vllm:latest ls -la /models
    read -p "Enter full model path: " MODEL_PATH
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "🛑 Stopping existing vLLM container..."
docker stop vllm-rocm 2>/dev/null
docker rm vllm-rocm 2>/dev/null

echo ""
echo "🚀 Starting vLLM with model: $MODEL_PATH and max-model-len 8192..."

docker run -d \
  --name vllm-rocm \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_PTRACE \
  -p 8000:8000 \
  -v $HOME/ai-legal-tender/models:/models \
  -e HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
  rocm/vllm:latest \
  --host 0.0.0.0 \
  --port 8000 \
  --model "$MODEL_PATH" \
  --dtype float16 \
  --max-model-len 8192 \
  --tensor-parallel-size 1

echo ""
echo "⏳ Waiting for vLLM to start..."
sleep 5

echo ""
echo "📊 Checking if container is running..."
docker ps | grep vllm-rocm

echo ""
echo "📋 Last 30 lines of logs:"
docker logs vllm-rocm 2>&1 | tail -30

echo ""
echo "✅ Setup complete!"
echo ""
echo "Monitor logs with: docker logs -f vllm-rocm"
echo "Check for 'max_model_len': docker logs vllm-rocm 2>&1 | grep max_model_len"
