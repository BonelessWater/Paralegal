# 🚀 AMD Server Setup Instructions

## Quick Reference
- **Server IP**: 134.199.202.8
- **SSH User**: amd-knights
- **SSH Command**: `ssh amd-knights@134.199.202.8`
- **Password**: wasdGspot

---

## Step 1: SSH into AMD Server

```bash
ssh amd-knights@134.199.202.8
# Password: wasdGspot
```

---

## Step 2: Check if vLLM Server is Running

```bash
# Check if vLLM is already running
curl http://localhost:8000/v1/models

# If you get a response with model info, vLLM is running ✅
# If connection refused, continue to Step 3
```

---

## Step 3: Start vLLM Server (if not running)

### Option A: Use existing start script
```bash
cd ~/ai-legal-tender/setup
./start_vllm.sh
```

### Option B: Manual start (if script doesn't exist)
```bash
# Activate conda environment (if you have one)
# conda activate legal-ai  # or whatever your env is called

# Start vLLM with Saul-7B model
vllm serve Equall/Saul-7B-Instruct-v1 \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --dtype float16 \
  --max-model-len 4096

# This will run in foreground - keep this terminal open
# Or run with nohup to keep it running:
nohup vllm serve Equall/Saul-7B-Instruct-v1 \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --dtype float16 \
  --max-model-len 4096 > /tmp/vllm.log 2>&1 &
```

### Verify vLLM is running:
```bash
# Test the endpoint
curl http://localhost:8000/v1/models

# You should see JSON output with "Equall/Saul-7B-Instruct-v1"
```

---

## Step 4: Navigate to Project Directory

```bash
cd ~/Paralegal
# or wherever you have the project cloned

# If you don't have the project yet, clone it:
# git clone https://github.com/BonelessWater/Paralegal.git
# cd Paralegal
```

---

## Step 5: Install Backend Dependencies

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Should install:
# - fastapi
# - uvicorn
# - requests
# - aiohttp
# - pydantic
# - python-multipart
# - asyncio-compat
```

---

## Step 6: Start Backend API Server

```bash
# Make sure you're in the backend directory
cd ~/Paralegal/backend

# Start the API server
python api_server.py

# Server will start on http://0.0.0.0:8080
# You should see output like:
# INFO:     Started server process
# INFO:     Uvicorn running on http://0.0.0.0:8080
```

### To run in background (recommended for demo):
```bash
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Check it's running:
curl http://localhost:8080/health | jq

# View logs:
tail -f /tmp/api_server.log
```

---

## Step 7: Test the Backend API

```bash
# Test 1: Health check
curl http://localhost:8080/health | jq

# Should return:
# {
#   "status": "healthy",
#   "vllm_connected": true,
#   "model_info": {...}
# }

# Test 2: System stats
curl http://localhost:8080/stats | jq

# Should return:
# {
#   "total_tasks": 0,
#   "tasks_pending": 0,
#   "tasks_processing": 0,
#   ...
# }

# Test 3: Agents list
curl http://localhost:8080/agents | jq

# Should return array of 4 agents:
# - client_communication
# - records_wrangler
# - legal_researcher
# - evidence_sorter
```

---

## Step 8: Create a Test Legal Research Task

```bash
curl -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "content": "Find cases similar to slip and fall at grocery store with broken wrist in Florida. Need settlement range estimates.",
    "sender": "paralegal@firm.com",
    "priority": "high"
  }' | jq

# Save the task_id from the response
# Example: "task_001"
```

---

## Step 9: Watch Task Progress

```bash
# Replace TASK_ID with the ID from Step 8
TASK_ID="task_001"

# Watch the task status (run this multiple times)
curl http://localhost:8080/tasks/$TASK_ID | jq

# Status progression:
# "pending" → "processing" → "awaiting_approval"

# Or use watch to auto-refresh:
watch -n 2 "curl -s http://localhost:8080/tasks/$TASK_ID | jq '.status, .assigned_agent'"
```

---

## Step 10: Check Intelligent Scraper Metrics

```bash
# After task completes, check stats
curl http://localhost:8080/stats | jq

# Look for:
# - cases_scraped_today: Number of cases found
# - scraping_speed: Cases per second
# - scraping_sessions: Number of research sessions
# - tasks_completed: 1 (should be 1 after first task)
```

---

## 🎯 Quick Test Script (All-in-One)

Save this as `test_server.sh` on the AMD server:

```bash
#!/bin/bash

echo "=== Testing Paralegal Backend API ==="

echo -e "\n1. Health Check:"
curl -s http://localhost:8080/health | jq '.status, .vllm_connected'

echo -e "\n2. Initial Stats:"
curl -s http://localhost:8080/stats | jq '{total_tasks, tasks_pending, tasks_completed}'

echo -e "\n3. Creating Legal Research Task..."
RESPONSE=$(curl -s -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "content": "Medical malpractice - misdiagnosed appendicitis leading to rupture. Need similar cases.",
    "priority": "high"
  }')

TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')
echo "Task ID: $TASK_ID"

echo -e "\n4. Waiting for task to process (30 seconds)..."
for i in {1..10}; do
    echo "Check $i/10..."
    STATUS=$(curl -s http://localhost:8080/tasks/$TASK_ID | jq -r '.status')
    echo "  Status: $STATUS"
    
    if [ "$STATUS" = "awaiting_approval" ]; then
        echo "✅ Task completed!"
        break
    fi
    sleep 3
done

echo -e "\n5. Final Stats:"
curl -s http://localhost:8080/stats | jq

echo -e "\n6. Task Details:"
curl -s http://localhost:8080/tasks/$TASK_ID | jq '{status, assigned_agent, ai_response}' | head -30

echo -e "\n=== Test Complete ==="
```

Run it:
```bash
chmod +x test_server.sh
./test_server.sh
```

---

## 📊 Expected Demo Output

When everything is working, you should see:

### Health Check:
```json
{
  "status": "healthy",
  "vllm_connected": true,
  "model_info": {
    "model": "Equall/Saul-7B-Instruct-v1",
    "served_model": "Equall/Saul-7B-Instruct-v1"
  }
}
```

### After Creating Task:
```json
{
  "task_id": "task_001",
  "status": "processing",
  "assigned_agent": "legal_researcher",
  "ai_response": "Searching for relevant cases..."
}
```

### Final Stats (with scraper active):
```json
{
  "total_tasks": 1,
  "tasks_completed": 1,
  "cases_scraped_today": 125,
  "scraping_speed": 15.2,
  "scraping_sessions": 1,
  "success_rate": 100.0
}
```

---

## 🚨 Troubleshooting

### vLLM won't start:
```bash
# Check GPU availability
rocm-smi

# Check if port 8000 is already in use
lsof -i :8000

# Kill existing vLLM process
pkill -f vllm

# Try starting again
```

### API server won't start:
```bash
# Check if port 8080 is in use
lsof -i :8080

# Check Python version
python --version  # Should be 3.10+

# View detailed error logs
python api_server.py
```

### "Connection refused" errors:
```bash
# Make sure you're on the server, not your local machine
hostname  # Should show AMD server hostname

# Check firewall (if needed)
sudo ufw status
```

---

## 🎬 Once Both Servers are Running

### On AMD Server:
- ✅ vLLM running on port 8000
- ✅ Backend API running on port 8080

### From Your Local Machine:
```bash
# Test from your Mac (replace with actual server IP)
curl http://134.199.202.8:8080/health | jq

# If this works, you can:
# 1. Update frontend .env to point to server: VITE_API_URL=http://134.199.202.8:8080
# 2. Start frontend locally: cd frontend && npm run dev
# 3. Open browser: http://localhost:5173
```

---

## 📝 Quick Commands Summary

```bash
# SSH to server
ssh amd-knights@134.199.202.8

# Start vLLM (background)
nohup vllm serve Equall/Saul-7B-Instruct-v1 --host 0.0.0.0 --port 8000 > /tmp/vllm.log 2>&1 &

# Start API server (background)
cd ~/Paralegal/backend
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Test endpoints
curl http://localhost:8080/health | jq
curl http://localhost:8080/stats | jq

# Create test task
curl -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"email","content":"Find slip and fall cases","priority":"high"}' | jq

# Watch logs
tail -f /tmp/vllm.log
tail -f /tmp/api_server.log
```

---

## ✅ You're Ready When You See:

1. vLLM health check returns model info
2. API /health returns `"vllm_connected": true`
3. Creating a task returns a task_id
4. Task status changes from "pending" → "processing" → "awaiting_approval"
5. Stats show `cases_scraped_today > 0` and `scraping_speed > 0`

**Then you're demo-ready! 🚀**
