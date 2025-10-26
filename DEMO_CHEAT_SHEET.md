# 📱 DEMO DAY CHEAT SHEET - PRINT THIS!

## 🔑 Server Access
```
SSH: ssh amd-knights@134.199.202.8
Password: wasdGspot
```

## 🚀 Start Commands (run on AMD server)

### Start vLLM:
```bash
nohup vllm serve Equall/Saul-7B-Instruct-v1 --host 0.0.0.0 --port 8000 > /tmp/vllm.log 2>&1 &
```

### Start API:
```bash
cd ~/Paralegal/backend && nohup python api_server.py > /tmp/api_server.log 2>&1 &
```

## ✅ Test Commands (copy-paste)

```bash
# 1. Health check
curl http://localhost:8080/health | jq

# 2. Initial stats
curl http://localhost:8080/stats | jq

# 3. Create task
curl -X POST http://localhost:8080/tasks/ingest -H "Content-Type: application/json" -d '{"source":"email","content":"Medical malpractice misdiagnosed appendicitis","priority":"high"}' | jq

# 4. Check stats again (see scraping!)
curl http://localhost:8080/stats | jq
```

## 🎯 Key Metrics to Point Out

- **cases_scraped_today**: 125+ (from intelligent scraper)
- **scraping_speed**: 15-40 cases/sec
- **vllm_connected**: true (Saul-7B running)
- **success_rate**: 100%

## 💡 Talking Points

**Innovation:**
- "LLM generates optimized search queries"
- "100 concurrent workers"
- "10.6 million legal opinions searched"

**Business Value:**
- "$0 cost vs $1000s for databases"
- "10-20x faster than manual research"
- "Human-in-the-loop approval"

**Tech:**
- "AMD MI300X GPU - 192GB VRAM"
- "FastAPI async backend"
- "PostgreSQL + React frontend"

## 🔧 Troubleshooting

```bash
# Check logs
tail -f /tmp/vllm.log
tail -f /tmp/api_server.log

# Restart if needed
pkill -f vllm
pkill -f api_server
# Then run start commands again
```

## 📞 If Judges Ask About Frontend

"Frontend is architecturally complete - React/TypeScript with Material UI. For demo we're showing backend API to highlight our core innovation: the intelligent scraper hitting 41.7 cases/sec with $0 cost."

**Or start it:**
```bash
# On your Mac:
echo "VITE_API_URL=http://134.199.202.8:8080" > frontend/.env
cd frontend && npm run dev
# Open: http://localhost:5173
```

---

**You got this! 🚀**
