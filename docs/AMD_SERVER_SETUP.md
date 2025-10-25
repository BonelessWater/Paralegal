# 🔐 AMD Server Connection & Setup Guide

## Server Credentials

```
Host: 134.199.202.8
Username: amd-knights
Password: wasdGspot
```

---

## 🚀 Quick Start - Run This on Your Local Mac

### Step 1: Connect to AMD Server

Open a terminal on your Mac and run:

```bash
ssh amd-knights@134.199.202.8
# When prompted, enter password: wasdGspot
```

### Step 2: Clone the Repository (on AMD server)

Once connected to the AMD server:

```bash
# Clone the repo
git clone https://github.com/BonelessWater/Paralegal.git

# Navigate to the project
cd Paralegal
```

### Step 3: Run Pre-Model Setup

```bash
# Navigate to setup directory
cd setup

# Make script executable (if needed)
chmod +x pre_model_setup.sh

# Run the setup
./pre_model_setup.sh
```

The script will:
- ✅ Verify ROCm and AMD GPU (MI300X)
- ✅ Install/configure Docker
- ✅ Pull vLLM Docker image (~10-15GB)
- ✅ Create project directories
- ✅ Set up environment

**Time: 15-20 minutes**

---

## 🔄 Alternative: One-Command Setup from Your Mac

If you prefer to run everything from your local Mac in one go:

```bash
ssh amd-knights@134.199.202.8 << 'ENDSSH'
  # Clone repo
  git clone https://github.com/BonelessWater/Paralegal.git
  
  # Navigate and run setup
  cd Paralegal/setup
  chmod +x pre_model_setup.sh
  ./pre_model_setup.sh
ENDSSH
```

**Note:** This will ask for password once, but you won't see interactive prompts. Better to SSH in manually.

---

## 📝 Detailed Step-by-Step

### On Your Local Mac Terminal:

```bash
# 1. SSH into AMD server
ssh amd-knights@134.199.202.8
# Password: wasdGspot

# 2. You should now see the AMD server prompt
# Something like: amd-knights@hostname:~$

# 3. Clone the repository
git clone https://github.com/BonelessWater/Paralegal.git

# 4. Navigate to the project
cd Paralegal/setup

# 5. Run the pre-model setup
./pre_model_setup.sh
```

### What the Script Will Do:

**Step 1:** Check ROCm installation
```
[1/7] Verifying AMD GPU and ROCm Installation
✓ ROCm tools found (rocm-smi)
GPU Status:
[Shows MI300X information]
```

**Step 2:** Check/Install Docker
```
[2/7] Checking Docker Installation
✓ Docker is already installed
Docker version 24.x.x
```

**Step 3:** Verify GPU Access
```
[3/7] Verifying Docker GPU Access
✓ GPU device files exist (/dev/kfd, /dev/dri)
```

**Step 4:** Pull vLLM Image (this takes 5-15 min)
```
[4/7] Pulling AMD vLLM Docker Image
Pull vLLM Docker image now? [Y/n]: y
[Shows download progress]
✓ vLLM Docker image downloaded successfully
```

**Step 5:** Create Directories
```
[5/7] Creating Project Directory Structure
✓ Created directory structure at ~/ai-legal-tender
```

**Step 6:** Environment Setup
```
[6/7] Setting Up Environment Variables
Do you have your Hugging Face token now? [y/N]: 
[You can skip this - teammate will set it later]
```

**Step 7:** Network Check
```
[7/7] Verifying Network Connectivity
✓ Can reach Hugging Face Hub
```

---

## ✅ After Setup Completes

You'll see:

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

---

## 🎯 What's Ready After This

On the AMD server, you'll have:

```
~/ai-legal-tender/
├── models/          # Ready for model download
├── data/            # Ready for mock legal data
├── logs/            # Ready for logs
└── scripts/         # Ready for OCR/scripts

~/Paralegal/
├── .env.example     # Template for configuration
├── setup/           # All setup scripts
├── backend/         # Pre-built agents
└── docs/            # Documentation
```

---

## 📋 Next Steps After Pre-Model Setup

### For Your Teammate (Model Selection):

```bash
# 1. SSH to AMD server
ssh amd-knights@134.199.202.8

# 2. Navigate to project
cd Paralegal

# 3. Configure model
cp .env.example .env
nano .env
# Set MODEL_NAME and MODEL_FOLDER

# 4. Download model
cd setup
./download_model_enhanced.sh
# Choose option 1 (uses .env)

# 5. Start vLLM
./start_vllm.sh

# 6. Test
./test_model.sh
```

### For You (While Waiting):

Work on your local machine:
- 🔨 Google ADK orchestrator
- 🎨 Approval interface
- 📧 Outreach automation
- 📊 Mock data generation
- 🎯 Demo preparation

---

## 🔧 Troubleshooting

### Cannot Connect to Server

```bash
# Test connection
ping 134.199.202.8

# If ping works but SSH doesn't, check firewall
# Try with verbose mode:
ssh -v amd-knights@134.199.202.8
```

### "Permission Denied" When Running Script

```bash
# Make script executable
chmod +x pre_model_setup.sh

# Then run
./pre_model_setup.sh
```

### Script Fails Mid-Way

```bash
# Script is idempotent - safe to re-run
./pre_model_setup.sh

# Check what went wrong:
cat ~/ai-legal-tender/SETUP_INFO.txt
```

### Docker Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker amd-knights

# Log out and back in
exit
ssh amd-knights@134.199.202.8

# Or activate group in current session
newgrp docker
```

---

## 💡 Pro Tips

### Keep Connection Open

Use `screen` or `tmux` to keep session alive:

```bash
# Start screen session
screen -S hackathon

# Run your setup
./pre_model_setup.sh

# Detach: Ctrl+A, then D
# Reattach later: screen -r hackathon
```

### Monitor Progress Remotely

```bash
# In one terminal: Run setup
ssh amd-knights@134.199.202.8
./pre_model_setup.sh

# In another terminal: Monitor
ssh amd-knights@134.199.202.8
watch -n 2 'docker images; echo "---"; df -h ~'
```

### Save Setup Log

```bash
# Run with logging
./pre_model_setup.sh 2>&1 | tee setup.log

# Later, review the log
less setup.log
```

---

## 📞 Quick Commands Reference

```bash
# Connect to server
ssh amd-knights@134.199.202.8

# Check if setup is complete
ls ~/ai-legal-tender/
cat ~/ai-legal-tender/SETUP_INFO.txt

# Check Docker
docker images | grep vllm

# Check ROCm
rocm-smi

# View GPU specs
rocminfo | grep -E "Name|Memory"
```

---

## ⏱️ Expected Timeline

```
00:00 - SSH into server
00:01 - Clone repository
00:02 - Start pre_model_setup.sh
00:05 - Docker verified/installed
00:10 - vLLM image download starts
00:20 - vLLM image download complete
00:22 - Directories created
00:23 - Environment configured
00:25 - Setup complete! ✅
```

**Total: ~20-25 minutes**

---

## 🎉 You're Ready!

Once the script completes:
- ✅ Infrastructure is prepared
- ✅ Teammate can download model anytime
- ✅ You can work on other components in parallel

**Happy Hacking! 🚀**
