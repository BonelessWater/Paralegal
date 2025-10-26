#!/bin/bash
# Quick health check for vLLM server

echo "======================================"
echo "vLLM Server Health Check"
echo "======================================"
echo ""

echo "1. Checking if vLLM process is running..."
ps aux | grep -i "vllm" | grep -v grep || echo "❌ No vLLM process found"
echo ""

echo "2. Checking port 8000..."
lsof -i :8000 || echo "❌ Nothing listening on port 8000"
echo ""

echo "3. Testing vLLM /v1/models endpoint..."
curl -s http://localhost:8000/v1/models | jq '.' || echo "❌ vLLM server not responding"
echo ""

echo "4. Testing quick completion (15s timeout)..."
curl -s --max-time 15 http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Equall/Saul-7B-Instruct-v1",
    "prompt": "Legal research involves",
    "max_tokens": 10,
    "temperature": 0.7
  }' | jq '.choices[0].text' || echo "❌ Completion test failed or timed out"
echo ""

echo "======================================"
echo "Health check complete"
echo "======================================"
