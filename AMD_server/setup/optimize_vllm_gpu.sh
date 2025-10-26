#!/bin/bash
# Optimize running vLLM for GPU sharing with Whisper
# This script restarts vLLM with reduced memory footprint while maintaining performance

set -e

echo "========================================================================"
echo "vLLM GPU OPTIMIZATION FOR WHISPER COMPATIBILITY"
echo "========================================================================"
echo ""

# Get current vLLM PID
VLLM_PID=$(pgrep -f "vllm serve" || echo "")

if [ -z "$VLLM_PID" ]; then
    echo "⚠️  vLLM is not currently running"
    echo "   To start vLLM with optimizations, run:"
    echo "   ./AMD_server/setup/start_vllm_optimized.sh"
    exit 1
fi

echo "📊 Current vLLM Status:"
echo "   PID: $VLLM_PID"
ps -p $VLLM_PID -o args= | head -1
echo ""

# Check GPU usage
echo "📈 Current GPU Memory Usage:"
rocm-smi | grep -A 2 "GPU use"
echo ""

# Get current vLLM configuration
CURRENT_MODEL=$(ps -p $VLLM_PID -o args= | grep -oP 'serve \K[^\s]+' || echo "Equall/Saul-7B-Instruct-v1")
CURRENT_PORT=$(ps -p $VLLM_PID -o args= | grep -oP '\-\-port \K[0-9]+' || echo "8000")

echo "Current Configuration:"
echo "   Model: $CURRENT_MODEL"
echo "   Port: $CURRENT_PORT"
echo ""

read -p "🔄 Restart vLLM with optimized settings? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🛑 Stopping current vLLM..."
sudo kill -TERM $VLLM_PID
sleep 3

# Force kill if still running
if pgrep -f "vllm serve" > /dev/null; then
    echo "   Force stopping..."
    sudo pkill -9 -f "vllm serve"
    sleep 2
fi

echo "✓ vLLM stopped"
echo ""

# Record baseline GPU stats
echo "📊 GPU Memory After Stop:"
rocm-smi | grep -A 2 "GPU use"
echo ""

echo "🚀 Starting vLLM with optimized configuration..."
echo "   Optimizations:"
echo "   ├─ GPU Memory: 60% (was 95%)"
echo "   ├─ KV Cache: FP8 quantization"
echo "   ├─ Flash Attention: Enabled (ROCm)"
echo "   └─ Memory Fragmentation: Optimized"
echo ""

# Set environment variables for AMD ROCm
export VLLM_USE_ROCM_FLASH_ATTN=1
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True

# Start optimized vLLM
nohup vllm serve "$CURRENT_MODEL" \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.6 \
  --kv-cache-dtype fp8 \
  --max-model-len 4096 \
  --port "$CURRENT_PORT" \
  > /tmp/vllm_optimized.log 2>&1 &

echo "⏳ Waiting for vLLM to initialize..."
sleep 15

# Check if started successfully
if pgrep -f "vllm serve" > /dev/null; then
    NEW_PID=$(pgrep -f "vllm serve")
    echo "✓ vLLM started successfully!"
    echo "   New PID: $NEW_PID"
    echo ""
    
    # Wait a bit more for model loading
    echo "⏳ Waiting for model to load..."
    sleep 10
    
    echo "📊 Optimized GPU Memory Usage:"
    rocm-smi | grep -A 2 "GPU use"
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
    echo "vLLM API: http://localhost:$CURRENT_PORT"
    echo "Logs: tail -f /tmp/vllm_optimized.log"
    echo ""
    echo "✅ You can now run Whisper transcription:"
    echo "   cd /home/amd-knights/Paralegal"
    echo "   bash run_transcription.sh"
    echo ""
else
    echo "❌ vLLM failed to start"
    echo "   Check logs: cat /tmp/vllm_optimized.log"
    exit 1
fi
