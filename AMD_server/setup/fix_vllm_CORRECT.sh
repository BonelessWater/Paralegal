#!/bin/bash
# Increase vLLM max-model-len from 4096 to 8192 tokens
# Uses the SAME configuration as optimize_vllm_gpu.sh

echo "🔍 Current vLLM containers:"
docker ps -a | grep vllm

echo ""
echo "🛑 Stopping vllm-optimized container..."
docker stop vllm-optimized 2>/dev/null
sleep 2

# Force remove if still exists (the container has --rm flag but sometimes lingers)
docker rm -f vllm-optimized 2>/dev/null
sleep 2

echo ""
echo "🚀 Starting vLLM with SAME config but max-model-len 8192..."
echo "   Optimizations:"
echo "   ├─ GPU Memory: 60%"
echo "   ├─ KV Cache: FP8 quantization"
echo "   ├─ Flash Attention: Enabled (ROCm)"
echo "   ├─ Shared Memory: 8GB"
echo "   └─ Max Model Length: 8192 (was 4096)"
echo ""

# Start vLLM with exact same config as optimize_vllm_gpu.sh, but max-model-len 8192
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
    --max-model-len 8192 \
    --port 8000

echo ""
echo "⏳ Waiting for vLLM to start (30-60 seconds)..."
sleep 10

echo ""
echo "📊 Container status:"
docker ps | grep vllm

echo ""
echo "📋 Tailing logs (Ctrl+C when you see 'Uvicorn running')..."
docker logs -f vllm-optimized
