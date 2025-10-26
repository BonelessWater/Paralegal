#!/bin/bash
# Optimize running vLLM Docker container for GPU sharing with Whisper
# This script restarts vLLM with reduced memory footprint while maintaining performance

set -e

echo "========================================================================"
echo "vLLM GPU OPTIMIZATION FOR WHISPER COMPATIBILITY"
echo "========================================================================"
echo ""

# Check for Docker container
CONTAINER_ID=$(docker ps -q -f "ancestor=rocm/vllm:latest" 2>/dev/null || echo "")

if [ -z "$CONTAINER_ID" ]; then
    echo "⚠️  vLLM Docker container is not currently running"
    echo "   To start vLLM with optimizations, see AMD_server/setup/start_vllm.sh"
    exit 1
fi

echo "📊 Current vLLM Container Status:"
echo "   Container ID: $CONTAINER_ID"
docker ps --filter "id=$CONTAINER_ID" --format "table {{.Image}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Get current configuration from docker inspect
CURRENT_CMD=$(docker inspect $CONTAINER_ID --format '{{.Config.Cmd}}' 2>/dev/null)
echo "Current command: $CURRENT_CMD"
echo ""

# Check GPU usage
echo "📈 Current GPU Memory Usage:"
rocm-smi | grep -A 2 "VRAM%"
echo ""

read -p "🔄 Restart vLLM container with optimized settings? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🛑 Stopping current vLLM container..."
docker stop $CONTAINER_ID
sleep 3

echo "✓ Container stopped"
echo ""

# Record baseline GPU stats
echo "📊 GPU Memory After Stop:"
rocm-smi | grep -A 2 "VRAM%"
echo ""

echo "🚀 Starting vLLM with optimized configuration..."
echo "   Optimizations:"
echo "   ├─ GPU Memory: 60% (was 95%)"
echo "   ├─ KV Cache: FP8 quantization"
echo "   ├─ Flash Attention: Enabled (ROCm)"
echo "   └─ Shared Memory: 8GB"
echo ""

# Start optimized vLLM container
docker run -d \
  --name vllm-optimized \
  --rm \
  --device /dev/kfd \
  --device /dev/dri \
  --shm-size 8g \
  --ipc=host \
  -p 8000:8000 \
  -v /home/amd-knights/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_USE_ROCM_FLASH_ATTN=1 \
  -e PYTORCH_HIP_ALLOC_CONF=expandable_segments:True \
  rocm/vllm:latest \
  vllm serve Equall/Saul-7B-Instruct-v1 \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.6 \
    --kv-cache-dtype fp8 \
    --max-model-len 4096 \
    --port 8000

NEW_CONTAINER_ID=$(docker ps -q -f "name=vllm-optimized")

if [ -n "$NEW_CONTAINER_ID" ]; then
    echo "✓ Container started: $NEW_CONTAINER_ID"
    echo ""
    
    echo "⏳ Waiting for vLLM to initialize (30 seconds)..."
    sleep 30
    
    echo "📊 Optimized GPU Memory Usage:"
    rocm-smi | grep -A 2 "VRAM%"
    echo ""
    
    echo "========================================================================"
    echo "OPTIMIZATION COMPLETE"
    echo "========================================================================"
    echo ""
    echo "Memory Savings:"
    echo "   Before: ~182 GB (95% of 192 GB)"
    echo "   After:  ~115 GB (60% of 192 GB)"
    echo "   Freed:  ~67 GB for Whisper transcription"
    echo ""
    echo "vLLM API: http://localhost:8000"
    echo "Container logs: docker logs -f vllm-optimized"
    echo ""
    echo "✅ You can now run Whisper transcription:"
    echo "   cd /home/amd-knights/Paralegal"
    echo "   bash run_transcription.sh"
    echo ""
else
    echo "❌ Container failed to start"
    echo "   Check logs: docker logs vllm-optimized"
    exit 1
fi
