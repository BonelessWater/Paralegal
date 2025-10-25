# 🚀 AMD ROCm Setup Package - Ready to Deploy!

I've created a complete setup package to get your AMD MI300X + vLLM + OCR infrastructure running for the AI Legal Tender hackathon. Here's what you have:

---

## 📦 What's Included

### 🔧 Setup Scripts (Make Executable with `chmod +x *.sh`)

1. **amd_setup_guide.sh** - Main setup script
   - Verifies ROCm and MI300X GPU
   - Installs Docker if needed
   - Pulls vLLM Docker image
   - Creates project structure
   - Sets up Hugging Face token

2. **download_model.sh** - Model downloader
   - Interactive menu for choosing models
   - Supports Llama 3 8B/70B, Mistral 7B, Phi-3 Mini
   - Handles Hugging Face authentication
   - Downloads to proper directory

3. **start_vllm.sh** - vLLM container launcher
   - Starts vLLM with ROCm GPU support
   - Exposes OpenAI-compatible API on port 8000
   - Configures optimal settings for MI300X
   - Easy to restart/modify

4. **test_vllm.sh** - API testing suite
   - Tests server health
   - Lists available models
   - Tests completions and chat
   - Validates full pipeline

5. **setup_ocr.sh** - OCR installation
   - Interactive menu for OCR backend
   - PaddleOCR (recommended), EasyOCR, or Tesseract
   - Creates test scripts
   - Builds unified OCR interface

### 📚 Documentation

6. **README_SETUP.md** - Complete setup guide
   - Step-by-step instructions
   - Troubleshooting section
   - Integration examples
   - Demo talking points
   - Time estimates

7. **QUICK_REFERENCE.txt** - Command cheat sheet
   - All common commands in one place
   - GPU monitoring commands
   - Docker operations
   - Troubleshooting quick fixes
   - Performance metrics commands
   - Demo prep checklist

### 💻 Python Code

8. **example_integration.py** - Working examples
   - Complete AMD LLM client class
   - All 4 specialist agents implemented:
     * Client Communication Guru
     * Records Wrangler
     * Legal Researcher
     * Evidence Sorter (with OCR)
   - Ready-to-run demonstration
   - Copy/paste into your project

---

## 🎯 How to Use This Package

### Step 1: Upload to Your AMD Server
```bash
# From your local machine, upload all files:
scp *.sh *.py *.md *.txt your-username@amd-server:~

# Or if already on the server, they're ready to go!
```

### Step 2: Run Initial Setup (15 minutes)
```bash
chmod +x *.sh
./amd_setup_guide.sh
```

### Step 3: Download Model (10-30 minutes)
```bash
./download_model.sh
# Choose option 1 (Llama 3 8B) - perfect balance for hackathon
```

### Step 4: Start vLLM (5 minutes)
```bash
./start_vllm.sh
# Wait 60 seconds for model to load
```

### Step 5: Test Everything (5 minutes)
```bash
./test_vllm.sh
```

### Step 6: Setup OCR (10 minutes)
```bash
./setup_ocr.sh
# Choose option 1 (PaddleOCR)
```

### Step 7: Test Integration (5 minutes)
```bash
python3 example_integration.py
```

**Total Time: 45-65 minutes** ✅

---

## 🏗️ Project Structure After Setup

```
~/
├── amd_setup_guide.sh
├── download_model.sh
├── start_vllm.sh
├── test_vllm.sh
├── setup_ocr.sh
├── example_integration.py
├── README_SETUP.md
├── QUICK_REFERENCE.txt
└── ai-legal-tender/
    ├── models/
    │   └── llama-3-8b/        # Your downloaded model
    ├── data/                   # For mock legal communications
    ├── logs/                   # System logs
    └── scripts/
        ├── test_ocr_paddle.py
        ├── test_ocr_easy.py
        ├── test_ocr_tesseract.py
        └── ocr_interface.py    # Use this in your agents!
```

---

## 🎓 Integration with Your Hackathon Project

Once setup is complete, you'll have:

✅ **vLLM API** running on `http://localhost:8000`
   - Use in your specialist agents
   - OpenAI-compatible endpoints
   - See `example_integration.py` for code

✅ **OCR Module** ready in `~/ai-legal-tender/scripts/ocr_interface.py`
   - Import and use for Evidence Sorter agent
   - Supports images and PDFs
   - AMD GPU-accelerated

✅ **Performance Metrics** ready to collect
   - Run commands from QUICK_REFERENCE.txt
   - Document for your demo

### Quick Integration Example
```python
# In your orchestrator/agent code:
import requests
import sys
sys.path.append('/home/claude/ai-legal-tender/scripts')
from ocr_interface import extract_text_from_image

# Call AMD LLM
response = requests.post("http://localhost:8000/v1/chat/completions",
    json={
        "model": "llama-3-8b",
        "messages": [
            {"role": "system", "content": "You are a legal assistant"},
            {"role": "user", "content": "Draft a response to this client"}
        ]
    })

# Use OCR
text = extract_text_from_image("medical_bill.jpg", ocr_type='paddle')
```

---

## 🔥 Key AMD Talking Points

When presenting to judges, emphasize:

### Hardware Excellence
- "Running on AMD MI300X with 128GB HBM memory"
- "Self-hosted deployment for data privacy - client data never leaves our secure environment"

### Software Stack Sophistication
- "Deployed vLLM for production-grade inference, not just basic PyTorch"
- "Full ROCm ecosystem: HIP for portability, MIGraphX for optimization"
- "OpenAI-compatible API for seamless integration"

### Performance (Get real numbers!)
```bash
# Run these and record the output:
docker logs vllm-rocm | grep 'tokens/s'    # "Achieving X tokens/second"
rocm-smi                                    # "Y% GPU utilization"
```

### Enterprise Architecture
- "Hybrid deployment: Google ADK for orchestration, AMD for compute"
- "Scalable via tensor parallelism for multi-GPU"
- "Production-ready with proper human oversight workflows"

---

## ⚠️ Critical Reminders

1. **Start model download IMMEDIATELY** - it's the longest wait (10-30 min)

2. **Keep QUICK_REFERENCE.txt open** - all commands in one place

3. **Screenshot everything** - GPU specs, performance metrics, working demos

4. **Test early and often** - don't wait until hour 4 to verify vLLM works

5. **Have fallbacks ready**:
   - Pre-record working demo video
   - If vLLM fails, use Transformers library directly
   - If AMD cloud down, run locally with Ollama

---

## 📞 Support During Hackathon

### Something Not Working?

1. **Check logs first:**
   ```bash
   docker logs vllm-rocm          # vLLM issues
   rocm-smi                       # GPU issues
   dmesg | grep -i rocm          # ROCm issues
   ```

2. **Consult QUICK_REFERENCE.txt** - common issues & solutions

3. **Read README_SETUP.md** - detailed troubleshooting section

### Common Quick Fixes

- **vLLM won't start:** `docker restart vllm-rocm`
- **API not responding:** Wait 60 seconds after start
- **Out of memory:** Use Llama 3 8B instead of 70B
- **Model download fails:** Accept license at huggingface.co/meta-llama

---

## 🏆 Success Criteria

### Minimum Viable Demo (Hours 0-4)
✅ LLM responding via API  
✅ One agent working end-to-end  
✅ Can explain architecture  

### Winning Demo (Full 24 Hours)
🏆 vLLM on MI300X (not basic PyTorch)  
🏆 Multiple specialist agents  
🏆 OCR + LLM integration  
🏆 Clean approval interface  
🏆 Performance metrics documented  

---

## 🎉 You're Ready!

Everything you need is in this package:
- ✅ Complete setup automation
- ✅ Working code examples
- ✅ Comprehensive documentation
- ✅ Quick reference commands
- ✅ Integration templates

**Next Steps:**
1. Upload these files to your AMD server
2. Run `./amd_setup_guide.sh`
3. Follow the prompts
4. Within 45-65 minutes, you'll have Phase 1 complete! 🚀

**Then move to Phase 2:** Data ingestion and mock legal communications

---

Good luck with your hackathon! The AMD infrastructure foundation is solid - now build amazing agents on top of it! 💪

Questions? Check:
- `README_SETUP.md` for detailed guide
- `QUICK_REFERENCE.txt` for quick commands
- `example_integration.py` for working code

---

**Created for AI Legal Tender Hackathon**  
**AMD MI300X + vLLM + ROCm Stack**  
**Ready to Deploy Package**
