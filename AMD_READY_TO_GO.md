# 🚀 READY TO GO - AMD Server Commands

## ✅ vLLM Already Running!

Since vLLM is already running, you just need to:

---

## 1️⃣ SSH to AMD Server
```bash
ssh amd-knights@134.199.202.8
# Password: wasdGspot
```

---

## 2️⃣ Pull Latest Code
```bash
cd ~/Paralegal
git pull origin main
```

This will get:
- ✅ `backend/api_server.py` (FastAPI server)
- ✅ `backend/llm_client.py` (vLLM wrapper)
- ✅ `backend/requirements.txt` (dependencies)
- ✅ All the agent integrations
- ✅ Intelligent scraper integration

---

## 3️⃣ Install Backend Dependencies
```bash
cd ~/Paralegal/backend
pip install -r requirements.txt
```

This installs:
- fastapi
- uvicorn
- requests
- aiohttp
- pydantic
- python-multipart

---

## 4️⃣ Start Backend API Server
```bash
# Still in ~/Paralegal/backend directory
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Should see output like:
# [1] 12345  (process ID)
```

---

## 5️⃣ Verify Everything Works

### Test vLLM (already running):
```bash
curl http://localhost:8000/v1/models | jq
```

### Test API Server:
```bash
curl http://localhost:8080/health | jq
```

**Expected output:**
```json
{
  "status": "healthy",
  "vllm_connected": true,
  "model_info": {
    "model": "Equall/Saul-7B-Instruct-v1"
  }
}
```

### Check Initial Stats:
```bash
curl http://localhost:8080/stats | jq
```

---

## 6️⃣ Create Test Task (Demo This!)
```bash
curl -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "content": "Find medical malpractice cases where doctor misdiagnosed appendicitis leading to rupture. Need similar cases for settlement estimate.",
    "sender": "paralegal@firm.com",
    "priority": "high"
  }' | jq
```

**Save the `task_id` from response!**

---

## 7️⃣ Watch Task Progress
```bash
# Replace with your actual task_id
TASK_ID="task_001"

# Check status (run multiple times)
curl http://localhost:8080/tasks/$TASK_ID | jq '.status, .assigned_agent'

# Or watch automatically:
watch -n 2 "curl -s http://localhost:8080/tasks/$TASK_ID | jq '.status, .assigned_agent, .ai_response' | head -20"
```

**Status progression:**
1. `"pending"` - Just created
2. `"processing"` - AI agent working (intelligent scraper running!)
3. `"awaiting_approval"` - Complete! Ready for human review

---

## 8️⃣ Check Final Stats (Show This to Judges!)
```bash
curl http://localhost:8080/stats | jq
```

**Point out these metrics:**
- `cases_scraped_today`: e.g., 125 (from intelligent scraper)
- `scraping_speed`: e.g., 15.2 cases/sec
- `scraping_sessions`: 1
- `tasks_completed`: 1
- `success_rate`: 100.0

---

## 🎯 ONE-LINER TEST SEQUENCE

Copy-paste this entire block for quick testing:

```bash
echo "=== Testing Paralegal System ===" && \
echo -e "\n1. Health Check:" && \
curl -s http://localhost:8080/health | jq '.status, .vllm_connected' && \
echo -e "\n2. System Stats:" && \
curl -s http://localhost:8080/stats | jq '{total_tasks, tasks_pending, tasks_completed, cases_scraped_today}' && \
echo -e "\n3. Creating Test Task..." && \
curl -s -X POST http://localhost:8080/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"email","content":"Slip and fall at grocery store with wrist injury","priority":"high"}' | jq '.task_id, .status' && \
echo -e "\n4. Waiting 20 seconds for processing..." && \
sleep 20 && \
echo -e "\n5. Final Stats:" && \
curl -s http://localhost:8080/stats | jq
```

---

## 🔍 Troubleshooting

### Check if API server is running:
```bash
ps aux | grep api_server
```

### View API logs:
```bash
tail -f /tmp/api_server.log
```

### Restart API if needed:
```bash
pkill -f api_server
cd ~/Paralegal/backend
nohup python api_server.py > /tmp/api_server.log 2>&1 &
```

### Check vLLM is still running:
```bash
ps aux | grep vllm
curl http://localhost:8000/v1/models
```

---

## ✅ SUCCESS CHECKLIST

- [x] vLLM running (you confirmed this!)
- [ ] Git pulled latest code
- [ ] Backend dependencies installed
- [ ] API server started on port 8080
- [ ] Health check returns `vllm_connected: true`
- [ ] Can create a task
- [ ] Task processes to "awaiting_approval"
- [ ] Stats show scraping metrics

---

## 🎬 READY FOR DEMO!

Once all checkboxes are done, you can:
1. Show judges the backend API working
2. Create tasks live
3. Watch intelligent scraper metrics
4. Show 10.6M opinions searched at 15-40 cases/sec
5. Highlight $0 cost vs expensive databases

**You're all set! 🚀**
