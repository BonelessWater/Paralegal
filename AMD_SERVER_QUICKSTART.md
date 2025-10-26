# 🚀 AMD Server Quick Start - One Page

## 1️⃣ SSH to Server
```bash
ssh amd-knights@134.199.202.8
# Password: wasdGspot
```

## 2️⃣ Start vLLM Server
```bash
# Check if already running:
curl http://localhost:8000/v1/models

# If not running, start it:
nohup vllm serve Equall/Saul-7B-Instruct-v1 \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --dtype float16 \
  --max-model-len 4096 > /tmp/vllm.log 2>&1 &

# Verify:
curl http://localhost:8000/v1/models | jq
```

## 3️⃣ Start Backend API
```bash
cd ~/Paralegal/backend

# Install deps (first time only):
pip install -r requirements.txt

# Start server:
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Verify:
curl http://localhost:8080/health | jq
```

## 4️⃣ Test with Sample Task
```bash
curl -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "content": "Find slip and fall cases at grocery stores with wrist injuries",
    "priority": "high"
  }' | jq

# Get task_id from response, then watch:
curl http://localhost:8080/tasks/TASK_ID | jq
```

## 5️⃣ Check Stats
```bash
curl http://localhost:8080/stats | jq
```

## ✅ Success Checklist
- [ ] vLLM returns model info on port 8000
- [ ] API /health shows `"vllm_connected": true`
- [ ] Creating task returns `task_id`
- [ ] Task status changes: pending → processing → awaiting_approval
- [ ] Stats show `cases_scraped_today > 0`

## 🔧 Troubleshooting
```bash
# View vLLM logs
tail -f /tmp/vllm.log

# View API logs
tail -f /tmp/api_server.log

# Kill and restart
pkill -f vllm
pkill -f api_server
# Then start again
```

## 📊 Demo Commands (Copy-Paste)
```bash
# Full test sequence
curl http://localhost:8080/health | jq
curl http://localhost:8080/stats | jq
curl -X POST http://localhost:8080/tasks/ingest -H "Content-Type: application/json" -d '{"source":"email","content":"Medical malpractice misdiagnosed appendicitis","priority":"high"}' | jq
curl http://localhost:8080/stats | jq
```

**That's it! 🎉**
