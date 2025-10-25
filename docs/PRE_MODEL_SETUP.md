# 🚀 Quick Start: Pre-Model Setup

## Run This NOW While Waiting for Model Selection

While your teammate works on choosing the perfect legal Hugging Face model, you can prepare the entire AMD infrastructure!

---

## What This Script Does

```bash
cd setup
./pre_model_setup.sh
```

### ✅ Automated Setup (15-20 minutes):

1. **Verifies ROCm & AMD GPU** ✓
   - Checks ROCm installation
   - Detects MI300X GPU
   - Documents GPU specs for demo

2. **Installs/Configures Docker** ✓
   - Installs Docker if needed
   - Starts Docker daemon
   - Adds you to docker group
   - Configures GPU access permissions

3. **Pulls vLLM Docker Image** ✓
   - Downloads rocm/vllm:latest (~10-15GB)
   - Pre-configured with ROCm
   - Saves 2-3 hours of manual setup

4. **Creates Project Structure** ✓
   - ~/ai-legal-tender/models/
   - ~/ai-legal-tender/data/
   - ~/ai-legal-tender/logs/
   - ~/ai-legal-tender/scripts/

5. **Sets Up Environment** ✓
   - Configures PATH
   - (Optional) Sets Hugging Face token
   - Prepares for model download

6. **Verifies Network** ✓
   - Tests Hugging Face connectivity
   - Tests Docker Hub connectivity

---

## How to Run

### On AMD Cloud Server:

```bash
# SSH into your AMD server
ssh your-username@amd-server

# Navigate to setup directory
cd ~/Paralegal/setup  # or wherever you cloned the repo

# Run the pre-model setup
./pre_model_setup.sh
```

The script is **interactive** - it will:
- Ask before installing Docker (if needed)
- Ask before pulling the large vLLM image
- Ask if you want to set Hugging Face token now (optional)
- Give you progress updates throughout

---

## What Happens Next

### ✅ After Pre-Model Setup Completes:

You'll have:
- ✅ ROCm verified and working
- ✅ Docker installed and configured
- ✅ vLLM image downloaded and ready
- ✅ Project directories created
- ✅ Environment configured

### 🎯 When Your Teammate Selects the Model:

They just need to:

```bash
# 1. Configure the model (2 minutes)
cp .env.example .env
nano .env  # Set MODEL_NAME and MODEL_FOLDER

# 2. Download it (5-30 minutes, automated)
cd setup
./download_model_enhanced.sh  # Choose option 1

# 3. Start vLLM (2 minutes)
./start_vllm.sh

# 4. Test (2 minutes)
./test_model.sh
```

**Total time after model selection: ~10-35 minutes**

---

## What YOU Can Do While Waiting

Since the infrastructure is ready, you can work on:

### 🔨 Google ADK Orchestrator
- Set up ADK framework
- Build routing logic
- The agents are already ready to import!

### 🎨 Approval Interface
- Build React/Flask UI
- Create approval workflow
- Design task queue display

### 📧 Outreach Automation
- Set up SendGrid/Twilio
- Configure ElevenLabs API
- Build email/SMS/voice sending logic

### 📊 Mock Data
- Create sample legal communications
- Generate test cases
- Prepare demo scenarios

### 🎯 Demo Prep
- Architecture diagrams
- Talking points
- Performance metrics plan

---

## Parallel Workflow

```
┌─────────────────────┐         ┌─────────────────────┐
│  YOU (Right Now)    │         │  Teammate (Parallel)│
├─────────────────────┤         ├─────────────────────┤
│                     │         │                     │
│ Run:                │         │ Research:           │
│ pre_model_setup.sh  │         │ - Legal models      │
│                     │         │ - Model comparison  │
│ ↓ (15-20 min)       │         │ - License check     │
│                     │         │                     │
│ Infrastructure      │         │ Choose:             │
│ Ready! ✅           │         │ - Best model        │
│                     │         │ - Configure .env    │
│ ↓                   │         │                     │
│                     │         │ ↓                   │
│ Work on:            │         │ Download:           │
│ - ADK orchestrator  │◄────────│ download_model.sh   │
│ - Approval UI       │  Model  │                     │
│ - Outreach setup    │  Ready  │ ↓                   │
│ - Mock data         │         │                     │
│ - Demo prep         │         │ Start & Test:       │
│                     │         │ - start_vllm.sh     │
│                     │         │ - test_model.sh     │
│                     │         │                     │
└─────────────────────┘         └─────────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         ↓
              Integration & Testing
                    ↓
                 Demo! 🎉
```

---

## Troubleshooting

### If ROCm Not Found:
```bash
# Install ROCm first
# Follow: https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html
```

### If Docker Installation Fails:
```bash
# Try manual installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### If vLLM Image Download is Slow:
- It's 10-15GB, be patient
- Use fast network connection
- Can take 5-30 minutes depending on bandwidth

### If You Need to Re-run:
```bash
# Script is idempotent - safe to run multiple times
./pre_model_setup.sh
```

---

## Expected Output

### Success Looks Like:

```
╔══════════════════════════════════════════════════════════════════╗
║                    ✅ SETUP COMPLETE!                             ║
╚══════════════════════════════════════════════════════════════════╝

✓ ROCm and GPU verified
✓ Docker installed and configured
✓ vLLM Docker image downloaded
✓ Project directory structure created
✓ Environment variables configured

Infrastructure is ready! 🚀
```

### Files Created:

- `~/ai-legal-tender/SETUP_INFO.txt` - Setup summary
- `~/.bashrc` - Updated with environment vars
- `~/ai-legal-tender/models/` - Ready for model download
- `~/ai-legal-tender/data/` - Ready for mock data
- `~/ai-legal-tender/logs/` - Ready for logs
- `~/ai-legal-tender/scripts/` - Ready for scripts

---

## Time Saved

**Without this script:** 
- Manual ROCm verification: 15 min
- Docker installation/config: 30 min
- vLLM image download: 10-15 min
- Directory setup: 5 min
- Environment config: 10 min
- **Total: ~70-75 minutes**

**With this script:**
- Automated: 15-20 minutes
- **Time saved: ~50-55 minutes!** ⏰

---

## Next Steps

After running this script:

1. ✅ **You're done with infrastructure!**
2. 📧 **Tell your teammate:** "Infrastructure ready, pick your model!"
3. 🔨 **Start building:** ADK orchestrator, UI, outreach
4. ⏰ **Save time:** ~50+ minutes freed up for other work

---

## Questions?

Check:
- `TEAMMATE_HANDOFF.md` - Overview for team
- `docs/MODEL_SETUP_GUIDE.md` - Model selection guide
- `docs/ARCHITECTURE_OVERVIEW.md` - System architecture

**You're ready to parallelize the work! 🚀**
