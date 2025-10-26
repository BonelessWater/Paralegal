# SSH Tunnel Setup Guide for Teammates

## Quick Access to Paralegal AI System

This guide will help you access the Paralegal AI system running on the AMD MI300X server from your local machine.

---

## 🎯 What You'll Access

- **Backend API**: Running on AMD server port 8081
- **Frontend UI**: Running locally on port 3000
- **vLLM Server**: Running on AMD server port 8000 (optional)

---

## 📋 Prerequisites

You need:
1. **SSH access** to the AMD server
   - Host: `134.199.202.8`
   - Username: `amd-knights`
   - Password: (get from Ilan)

2. **Git** installed locally
3. **Node.js** (v18+) and **npm** installed locally

---

## 🚀 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
cd ~
git clone https://github.com/BonelessWater/Paralegal.git
cd Paralegal
```

### Step 2: Create SSH Tunnel to Backend

Open a **new terminal window** and run:

```bash
ssh -L 9081:localhost:8081 amd-knights@134.199.202.8
```

**What this does:**
- Forwards your local port `9081` → AMD server port `8081` (backend API)
- Keep this terminal window open while working

**Verification:**
```bash
# In a new terminal, test the tunnel:
curl http://localhost:9081/health
```

Expected response:
```json
{"status":"healthy","agents":["client_communication","records_wrangler","legal_researcher","evidence_sorter"],"version":"1.0.0"}
```

### Step 3: (Optional) Tunnel to vLLM Server

If you want to test LLM directly:

```bash
ssh -L 8000:localhost:8000 amd-knights@134.199.202.8
```

This allows you to send requests to the LLM at `http://localhost:8000/v1/chat/completions`

---

## 🖥️ Frontend Setup

### Step 1: Install Dependencies

```bash
cd ~/Paralegal/frontend
npm install
```

### Step 2: Start Frontend Dev Server

```bash
npm run dev
```

Expected output:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

### Step 3: Open Browser

Navigate to: **http://localhost:3000**

You should see the Paralegal AI interface!

---

## 📡 Architecture Overview

```
┌─────────────────────┐
│  Your Local Machine │
│                     │
│  Browser            │
│  localhost:3000     │ ← Frontend (Vite dev server)
│         ↓           │
│  localhost:9081     │ ← SSH Tunnel
└──────────┬──────────┘
           │ SSH Tunnel
           │
┌──────────┴──────────────────────────────────┐
│  AMD MI300X Server (134.199.202.8)         │
│                                             │
│  Backend API (FastAPI)                      │
│  localhost:8081                             │
│         ↓                                   │
│  vLLM Server (Saul-7B-Instruct)            │
│  localhost:8000                             │
│         ↓                                   │
│  RAG Database (FAISS + Embeddings)         │
│  CourtListener API (10.6M cases)           │
└─────────────────────────────────────────────┘
```

---

## 🎨 Using the System

### Legal Research (Main Feature)

1. Click **"Legal Research"** in the sidebar
2. Enter a legal question, e.g.:
   ```
   Research premises liability cases involving slip and fall with inadequate warning signs
   ```
3. Click **"Submit Research Request"**
4. Watch the progress bar - it will:
   - Generate search queries
   - Search CourtListener (live)
   - Analyze 80+ real cases
   - Generate legal memo with citations
5. View the research memo with actual case citations!

### Other Features

- **Dashboard**: System stats and recent tasks
- **Client Communication**: Email/message handling
- **Records Management**: Document processing
- **Evidence Analysis**: Evidence sorting

---

## 🔧 Troubleshooting

### Issue: "Connection Refused" on localhost:9081

**Solution:**
- Check if SSH tunnel is still running
- Restart the tunnel:
  ```bash
  ssh -L 9081:localhost:8081 amd-knights@134.199.202.8
  ```

### Issue: Frontend shows "Network Error"

**Solution:**
- Verify tunnel is working: `curl http://localhost:9081/health`
- Check frontend API URL in browser console
- The frontend automatically uses `http://localhost:9081` (tunneled port)

### Issue: Frontend won't start

**Solution:**
```bash
cd ~/Paralegal/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: "EADDRINUSE: Port 3000 already in use"

**Solution:**
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9
# Or use a different port
npm run dev -- --port 3001
```

---

## 🔒 Security Notes

1. **SSH Tunnel**: Keep the SSH terminal window open while working
2. **Passwords**: Don't commit passwords to Git
3. **API Keys**: CourtListener API key is in server `.env` file (not in repo)
4. **Network**: Only accessible via SSH tunnel (not exposed publicly)

---

## 📊 System Status

### Check if Backend is Running

```bash
# Test health endpoint
curl http://localhost:9081/health

# Get system stats
curl http://localhost:9081/stats

# List all tasks
curl http://localhost:9081/tasks
```

### Check if vLLM is Running

```bash
# Test LLM endpoint (if tunnel is open)
curl http://localhost:8000/v1/models
```

---

## 🚨 If Backend is Down

Contact Ilan or restart the backend on the AMD server:

```bash
# SSH into AMD server
ssh amd-knights@134.199.202.8

# Navigate to project
cd ~/Paralegal/backend

# Activate virtual environment
source ~/Paralegal/venv/bin/activate

# Kill old process
pkill -f api_server.py

# Start fresh
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# Check logs
tail -f /tmp/api_server.log
```

---

## 📝 Quick Reference

### Essential Commands

```bash
# Start SSH tunnel (keep open)
ssh -L 9081:localhost:8081 amd-knights@134.199.202.8

# Start frontend (in project directory)
cd ~/Paralegal/frontend && npm run dev

# Test backend health
curl http://localhost:9081/health

# View backend logs (on AMD server)
tail -f /tmp/api_server.log
```

### Important URLs

- **Frontend**: http://localhost:3000
- **Backend API** (tunneled): http://localhost:9081
- **API Docs** (tunneled): http://localhost:9081/docs
- **Health Check**: http://localhost:9081/health

---

## 💡 Pro Tips

1. **Keep SSH tunnel open**: Use `screen` or `tmux` to keep tunnel running
   ```bash
   screen -S tunnel
   ssh -L 9081:localhost:8081 amd-knights@134.199.202.8
   # Press Ctrl+A, then D to detach
   # Reconnect: screen -r tunnel
   ```

2. **Multiple tunnels**: Use different local ports
   ```bash
   ssh -L 9081:localhost:8081 -L 9000:localhost:8000 amd-knights@134.199.202.8
   ```

3. **Background tunnel**: Use `-f -N` flags
   ```bash
   ssh -f -N -L 9081:localhost:8081 amd-knights@134.199.202.8
   # Kill later: pkill -f "ssh.*9081"
   ```

4. **Auto-reconnect**: Use `autossh` for persistent tunnels
   ```bash
   brew install autossh  # macOS
   autossh -M 0 -L 9081:localhost:8081 amd-knights@134.199.202.8
   ```

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Vite Docs**: https://vitejs.dev/
- **React Docs**: https://react.dev/
- **Material-UI**: https://mui.com/
- **CourtListener API**: https://www.courtlistener.com/api/rest-info/

---

## 📞 Get Help

- **Issues**: Post in GitHub Issues
- **Questions**: Slack/Discord (team channel)
- **Bugs**: Create detailed bug report with logs

---

## ✅ Success Checklist

- [ ] SSH tunnel connected to port 9081
- [ ] Backend health check returns 200 OK
- [ ] Frontend running on port 3000
- [ ] Browser shows Paralegal AI interface
- [ ] Can submit legal research query
- [ ] Research returns 80+ cases from CourtListener
- [ ] Legal memo generated with real citations

**You're all set! Happy researching! 🎉**

---

*Last Updated: October 26, 2025*  
*System Version: 1.0.0*  
*AMD MI300X Server: 134.199.202.8*
