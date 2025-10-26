# Quick Fix for vLLM 400 Errors

## Problem
Multi-agent getting 400 Bad Request errors even with per-case processing.

## Root Cause  
vLLM's default `max-model-len 4096` tokens (~16KB) is too small for:
- Agent prompt (~500 chars)
- Case text (1500 chars)
- Question (~200 chars)
- System message
- **Total: ~2500-3000 chars per request**

Even though individual prompts look small, with JSON encoding and overhead, they exceed 4096 tokens.

## Solution
Increase vLLM context window to **8192 tokens** (2x current limit).

## Steps on AMD Server

### Option 1: Interactive Script (Recommended)
```bash
cd ~/Paralegal/AMD_server/setup
./fix_vllm_context.sh
```

This will:
1. Show current vLLM setup
2. Let you verify/choose the model path
3. Restart with 8192 token limit
4. Show logs to confirm

### Option 2: Manual Docker Command

First, find the correct model path:
```bash
docker logs vllm-rocm 2>&1 | grep "model" | head -5
```

Then restart vLLM:
```bash
# Stop existing
docker stop vllm-rocm
docker rm vllm-rocm

# Start with 8192 context (replace MODEL_PATH with actual path)
docker run -d \
  --name vllm-rocm \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_PTRACE \
  -p 8000:8000 \
  -v $HOME/ai-legal-tender/models:/models \
  rocm/vllm:latest \
  --host 0.0.0.0 \
  --port 8000 \
  --model /models/Equall--Saul-7B-Instruct-v1 \
  --dtype float16 \
  --max-model-len 8192 \
  --tensor-parallel-size 1
```

### Verify It Worked

```bash
# Check container is running
docker ps | grep vllm-rocm

# Verify max_model_len is 8192
docker logs vllm-rocm 2>&1 | grep max_model_len

# Should show something like:
# INFO: max_model_len=8192
```

### After vLLM Restarts

Wait 1-2 minutes for model to load, then:

```bash
# Test vLLM is responding
curl http://localhost:8000/v1/models

# Restart API server to reconnect
cd ~/Paralegal/backend
pkill -f api_server.py
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Monitor for multi-agent success
tail -f /tmp/api_server.log | grep -E "Cycle|findings|ERROR"
```

## Expected Results

**BEFORE (4096 tokens):**
```
ERROR:llm_client:Chat completion failed: 400 Client Error
ERROR:llm_client:Chat completion failed: 400 Client Error
ERROR:llm_client:Chat completion failed: 400 Client Error
```

**AFTER (8192 tokens):**
```
INFO:agents.multi_agent_researcher:Cycle 1: Generated 15 findings from 5 cases
INFO:agents.multi_agent_researcher:Cycle 2: Generated 15 findings from 5 cases  
INFO:agents.multi_agent_researcher:Cycle 3: Generated 15 findings from 5 cases
✅ NO 400 ERRORS!
```

## Troubleshooting

### If container won't start:

Check logs:
```bash
docker logs vllm-rocm
```

Common issues:
- **Model path wrong**: Check with `docker run --rm -v $HOME/ai-legal-tender/models:/models rocm/vllm:latest ls /models`
- **GPU busy**: Another process using GPU - check `rocm-smi`
- **Out of memory**: 8192 context needs ~2GB more VRAM (should be fine with 192GB)

### If still getting 400 errors after increasing context:

1. Verify vLLM actually restarted:
   ```bash
   docker logs vllm-rocm 2>&1 | grep "max_model_len"
   ```

2. Check API server reconnected:
   ```bash
   grep "vLLM server connected" /tmp/api_server.log
   ```

3. Check actual prompt sizes being sent:
   ```bash
   grep "Prompt length" /tmp/api_server.log
   ```

## Alternative: Reduce Context Even More

If 8192 still causes issues (unlikely), we can further reduce:

In `AMD_server/agents/multi_agent_researcher.py`:
- Line 366: Change `case_text[:1500]` to `case_text[:1000]`
- Line 428: Change `case_text[:1500]` to `case_text[:1000]`
- Line 476: Change `case_text[:1500]` to `case_text[:1000]`

This reduces each prompt by ~500 chars (~125 tokens).

---

**Bottom line**: With 8192 token limit, the multi-agent system should work perfectly! 🚀
