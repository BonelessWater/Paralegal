# 🚀 Paralegal AI - Quick Start Guide

**Complete deployment guide for the Multi-Agent Legal Research System**

---

## � System Requirements

### AMD Server (Production)
- **GPU**: AMD MI300X (192GB VRAM)
- **OS**: Ubuntu with ROCm 6.0
- **Docker**: For vLLM container
- **Python**: 3.11+
- **Node.js**: 18+

### Local Development
- **SSH Access**: To AMD server (134.199.202.8)
- **Local Ports**: 3000 (frontend), 9081 (backend tunnel)
- **Browser**: Chrome/Firefox for dashboard

---

## ⚙️ Quick Setup (5 Minutes)

### 1. Start vLLM Server (AMD Server)

```bash
# SSH into AMD server
ssh amd-knights@134.199.202.8

# Navigate to project
cd ~/Paralegal

# Start vLLM Docker container
./AMD_server/setup/optimize_vllm_gpu.sh

# Verify vLLM is running
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Check model is loaded
curl http://localhost:8000/v1/models
# Expected: Saul-7B-Instruct-v1
```

**vLLM Configuration:**
- Model: `Saul-7B-Instruct-v1`
- Max context: 4096 tokens
- GPU memory: 60% (115GB)
- Precision: bfloat16 with FP8 KV cache
- Port: 8000

---

### 2. Start Backend API (AMD Server)

```bash
# In another SSH terminal
cd ~/Paralegal/backend

# Activate Python environment
pyenv shell 3.11.8

# Install dependencies (first time only)
pip install -r requirements.txt

# Start FastAPI server
python api_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8081
✅ Multi-agent research system loaded
✅ RAG embeddings loaded successfully
```

**Backend Configuration:**
- Port: 8081 (internal)
- vLLM endpoint: http://localhost:8000
- Database: PostgreSQL (paralegal_db)
- Features: Multi-agent research, RAG search, 4-stage synthesis

---

### 3. SSH Tunnel (Local Machine)

```bash
# From your local machine, create SSH tunnel
ssh -L 9081:localhost:8081 amd-knights@134.199.202.8

# Keep this terminal open
# Backend API now accessible at http://localhost:9081
```

**Test tunnel:**
```bash
# From local machine
curl http://localhost:9081/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

---

### 4. Start Frontend (Local Machine)

```bash
# From your local machine
cd ~/Paralegal/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected output:**
```
VITE v5.x.x ready in XXX ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

**Frontend Features:**
- Real-time synthesis progress stepper (4 stages)
- Material UI dashboard
- Legal research interface
- Live status updates

---

## 🧪 Test End-to-End System

### Option 1: Web UI (Recommended)

1. Open browser: http://localhost:3000
2. Navigate to "Legal Research" tab
3. Enter query: "What is the liability standard for slip and fall cases at grocery stores?"
4. Click "Search"
5. Watch 4-stage synthesis progress:
   - **Stage 1**: Organizing findings (0-30s)
   - **Stage 2**: Writing sections (30-45s)
   - **Stage 3**: Integration (45-75s)
   - **Stage 4**: Quality check (75-90s)
6. Review comprehensive memo (~5,700 chars)

**Expected sections:**
- Executive Summary
- Legal Framework
- Case Analysis (6 relevant cases)
- Practical Guidance

---

### Option 2: API Testing

```bash
# Test health
curl http://localhost:9081/health | jq

# Create research task
curl -X POST http://localhost:9081/tasks/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "manual",
    "content": "What is the liability standard for slip and fall cases at grocery stores?",
    "priority": "high"
  }' | jq

# Get task status (use task_id from response)
curl http://localhost:9081/tasks/{task_id} | jq

# Watch for completion (status: "completed")
watch -n 2 "curl -s http://localhost:9081/tasks/{task_id} | jq '.status'"
```

**Performance Expectations:**
- Query time: 150-200 seconds
- Cases analyzed: 6 relevant cases
- Memo length: 5,000-6,000 characters
- Quality score: 7-8/10

---
---

## 🔧 Troubleshooting

### vLLM Server Not Running

**Symptom**: `curl http://localhost:8000/health` fails

**Solution**:
```bash
# Check Docker container
docker ps | grep vllm

# If not running, start it
./AMD_server/setup/optimize_vllm_gpu.sh

# Check logs
docker logs $(docker ps -q --filter ancestor=rocm/vllm:latest)
```

---

### Backend API Errors

**Symptom**: Backend crashes or returns 500 errors

**Check**:
```bash
# Verify vLLM is accessible
curl http://localhost:8000/v1/models

# Check Python environment
pyenv shell 3.11.8
python --version

# Verify dependencies
pip install -r requirements.txt

# Check logs
tail -f backend/logs/*.log
```

---

### SSH Tunnel Issues

**Symptom**: `curl http://localhost:9081/health` fails from local machine

**Solution**:
```bash
# Kill existing tunnel
pkill -f "ssh.*9081:localhost:8081"

# Restart tunnel
ssh -L 9081:localhost:8081 amd-knights@134.199.202.8

# Verify in another terminal
curl http://localhost:9081/health
```

---

### Frontend Not Connecting

**Symptom**: Frontend shows "Failed to connect to backend"

**Check**:
1. SSH tunnel is running: `lsof -i :9081`
2. Backend is running on server: `curl http://localhost:9081/health`
3. Frontend .env file has correct API URL:
   ```
   VITE_API_URL=http://localhost:9081
   ```

---

### Slow Query Performance

**Symptom**: Queries taking >300 seconds

**Diagnostics**:
```bash
# Check GPU usage on AMD server
rocm-smi

# Check vLLM load
curl http://localhost:8000/health

# Check backend logs for timeout errors
tail -f backend/logs/*.log | grep "timeout"
```

**Solutions**:
- Reduce max_cycles in `multi_agent_researcher.py` (currently 2)
- Increase timeout values if network is slow
- Check GPU isn't being used by other processes

---

### Database Connection Issues

**Symptom**: "Failed to connect to database" errors

**Solution**:
```bash
# Test database connection
psql -h localhost -U paralegal_user -d paralegal_db

# Password: hackathon2024

# Verify RAG embeddings table
\dt opinions_embeddings

# Check opinion count
SELECT COUNT(*) FROM opinions;
# Expected: 10.6M+
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AMD Server (134.199.202.8)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  vLLM Docker     │         │  Backend API (FastAPI)  │  │
│  │  Port: 8000      │◄────────│  Port: 8081             │  │
│  │  Saul-7B Model   │         │  - Multi-agent research │  │
│  │  GPU: 115GB      │         │  - RAG search           │  │
│  └──────────────────┘         │  - 4-stage synthesis    │  │
│                               └──────────┬──────────────┘  │
│                                          │                  │
│  ┌──────────────────┐                   │                  │
│  │  PostgreSQL DB   │◄──────────────────┘                  │
│  │  10.6M+ opinions │                                      │
│  │  RAG embeddings  │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
                                ▲
                                │ SSH Tunnel (9081→8081)
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Local Machine                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Browser         │◄────────│  Frontend (React/TS)    │  │
│  │  localhost:3000  │         │  Port: 3000             │  │
│  │                  │         │  - Material UI          │  │
│  │                  │         │  - Synthesis stepper    │  │
│  └──────────────────┘         │  - Real-time updates    │  │
│                               └─────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Performance Metrics

### Multi-Agent Research Pipeline

```
Query → RAG Search (10-15s)
  ↓
Relevance Filter (1-2s)
  ↓
Cycle 1: 3 agents × 3 cases = 9 analyses (30-40s)
  ↓
Cycle 2: 3 agents × 3 cases = 9 analyses (30-40s)
  ↓
Stage 1: Organize findings (15-20s)
  ↓
Stage 2: Write sections in parallel (20-30s)
  ↓
Stage 3: Integration (20-30s)
  ↓
Stage 4: Quality check (15-20s)
  ↓
Total: ~179 seconds
```

### Resource Usage

| Component | CPU | Memory | GPU | Network |
|-----------|-----|--------|-----|---------|
| vLLM | 10-20% | 8GB | 115GB (60%) | Low |
| Backend | 5-10% | 2GB | - | Medium |
| Frontend | 1-2% | 500MB | - | Low |
| Database | 2-5% | 4GB | - | Low |

---

## 🎯 Next Steps

1. **Review Quality Improvements**: [RESEARCH_QUALITY_IMPROVEMENTS.md](RESEARCH_QUALITY_IMPROVEMENTS.md)
2. **Understand Performance**: [RESEARCH_PERFORMANCE_OPTIMIZATION.md](RESEARCH_PERFORMANCE_OPTIMIZATION.md)
3. **Explore Architecture**: [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
4. **Database Operations**: [docs/DATABASE_DOCUMENTATION.md](docs/DATABASE_DOCUMENTATION.md)
5. **GPU Optimization**: [docs/GPU_OPTIMIZATION_GUIDE.md](docs/GPU_OPTIMIZATION_GUIDE.md)

---

## 📝 Configuration Files

### Backend (.env)
```bash
# AMD_server/.env
VLLM_BASE_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paralegal_db
DB_USER=paralegal_user
DB_PASSWORD=hackathon2024
```

### Frontend (.env)
```bash
# frontend/.env
VITE_API_URL=http://localhost:9081
```

### vLLM Docker
```bash
# Configured in: AMD_server/setup/optimize_vllm_gpu.sh
# Model: Saul-7B-Instruct-v1
# GPU memory: 60% (--gpu-memory-utilization 0.6)
# Max context: 4096 (--max-model-len 4096)
# Precision: bfloat16 (--dtype bfloat16)
# KV cache: FP8 (--kv-cache-dtype fp8)
```

---

## 🆘 Getting Help

- **Documentation**: See [README.md](README.md) for full documentation index
- **Issues**: Create GitHub issue with logs and error messages
- **Logs**: Check `backend/logs/` for detailed error traces
- **Health Checks**: Use `/health` endpoints on all services

---

**System Status**: ✅ Production Ready (v4.0 - October 26, 2025)
