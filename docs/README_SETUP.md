# AMD ROCm Setup Guide for AI Legal Tender Hackathon

## 🎯 Goal
Get Llama 3 running on AMD MI300X via vLLM + Set up OCR for document processing

## 📋 Prerequisites
- Access to AMD Developer Cloud with MI300X
- SSH access to the server
- Hugging Face account (for downloading Llama 3)

---

## 🚀 Quick Start (15 minutes)

### Step 1: Initial Setup
```bash
# Make setup script executable
chmod +x amd_setup_guide.sh

# Run initial setup
./amd_setup_guide.sh
```

**What this does:**
- ✅ Verifies ROCm and MI300X GPU
- ✅ Installs/checks Docker
- ✅ Pulls vLLM Docker image
- ✅ Creates project directory structure
- ✅ Sets up Hugging Face token

**Important:** Screenshot your `rocm-smi` output - you'll need GPU specs for your presentation!

---

### Step 2: Download Hugging Face Model
```bash
# Make script executable
chmod +x download_model.sh

# Run downloader
./download_model.sh
```

**Choose model:**
- **Option 1: Llama 3 8B** (RECOMMENDED) - 40GB, perfect balance for hackathon
- Option 2: Llama 3 70B - 140GB, impressive but slow download
- Option 3: Mistral 7B - 14GB, faster alternative
- Option 4: Phi-3 Mini - 7GB, lightweight

**Note:** For Llama 3, you need to:
1. Get token from: https://huggingface.co/settings/tokens
2. Accept license at: https://huggingface.co/meta-llama

**Download time:** 10-30 minutes depending on model size

---

### Step 3: Start vLLM Inference Server
```bash
# Make script executable
chmod +x start_vllm.sh

# Start vLLM container
./start_vllm.sh
```

**What this does:**
- Starts vLLM in Docker container with ROCm support
- Exposes OpenAI-compatible API on port 8000
- Loads your Hugging Face model
- Enables GPU acceleration via MI300X

**Check logs:**
```bash
docker logs -f vllm-rocm
```

Wait for: `"Uvicorn running on http://0.0.0.0:8000"` message (30-60 seconds)

---

### Step 4: Test vLLM API
```bash
# Make script executable
chmod +x test_vllm.sh

# Run tests
./test_vllm.sh
```

**Tests performed:**
1. ✅ Server health check
2. ✅ Model listing
3. ✅ Text completion test
4. ✅ Chat completion test (simulates agent interaction)

**Expected output:** JSON responses with generated text

---

### Step 5: Setup OCR for Document Processing
```bash
# Make script executable
chmod +x setup_ocr.sh

# Run OCR setup
./setup_ocr.sh
```

**Choose OCR backend:**
- **Option 1: PaddleOCR** (RECOMMENDED) - Best for legal docs, ROCm support
- Option 2: EasyOCR - Good alternative, ROCm compatible
- Option 3: Tesseract - CPU-based fallback

**Creates:**
- Test scripts in `~/ai-legal-tender/scripts/`
- Unified OCR interface: `ocr_interface.py`

---

## 📊 Verify Everything Works

### Check GPU Status
```bash
# See GPU utilization
rocm-smi

# Detailed GPU info
rocminfo | grep -E "Name|Memory"
```

### Check vLLM Performance
```bash
# View inference speed
docker logs vllm-rocm | grep 'tokens/s'

# Monitor GPU usage
watch -n 1 rocm-smi
```

### Test OCR
```bash
cd ~/ai-legal-tender/scripts

# Test your chosen OCR
python3 test_ocr_paddle.py  # or test_ocr_easy.py or test_ocr_tesseract.py
```

---

## 🔧 Troubleshooting

### vLLM Container Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check GPU access
ls -la /dev/kfd /dev/dri

# View detailed container logs
docker logs vllm-rocm --tail 100
```

### Model Download Fails
```bash
# For Llama 3: Make sure you accepted the license
# Visit: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct

# Check your token is set
echo $HUGGING_FACE_HUB_TOKEN

# Try manual download
huggingface-cli login
huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct
```

### OCR Installation Issues
```bash
# For PaddleOCR issues, try EasyOCR instead
pip uninstall paddleocr
pip install easyocr --break-system-packages

# For Tesseract, ensure apt is updated
sudo apt-get update
sudo apt-get install tesseract-ocr -y
```

### GPU Not Detected
```bash
# Verify ROCm installation
/opt/rocm/bin/rocminfo

# Check if GPU is visible
lspci | grep -i amd

# Restart ROCm services
sudo systemctl restart rocm-smi
```

---

## 📁 Project Structure

```
~/ai-legal-tender/
├── models/              # Downloaded Hugging Face models
│   └── llama-3-8b/     # Model files
├── data/               # Mock legal communications (you'll create this)
├── logs/               # System logs
└── scripts/            # Python scripts
    ├── test_ocr_paddle.py
    ├── test_ocr_easy.py
    ├── test_ocr_tesseract.py
    └── ocr_interface.py
```

---

## 🎯 Integration with Your Agents

### Using vLLM API in Your Specialist Agents

```python
import requests

def call_amd_llm(prompt, system_message=""):
    """Call AMD-hosted LLM via vLLM"""
    
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "llama-3-8b",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]

# Example: Client Communication Guru Agent
def client_communication_agent(messy_client_message):
    system_prompt = """You are a compassionate legal assistant. 
    Rewrite client messages as clear, empathetic responses. 
    Maintain professional but warm tone."""
    
    response = call_amd_llm(messy_client_message, system_prompt)
    return response
```

### Using OCR in Evidence Sorter Agent

```python
from scripts.ocr_interface import extract_text_from_image, extract_text_from_pdf

def evidence_sorter_agent(file_path):
    """Extract and classify legal documents"""
    
    # Extract text using OCR
    if file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path, ocr_type='paddle')
    else:
        text = extract_text_from_image(file_path, ocr_type='paddle')
    
    # Send to AMD LLM for classification
    classification_prompt = f"""Categorize this legal document:
    
    {text}
    
    Categories: Medical Bill, Police Report, Insurance Correspondence, 
                Court Document, Other
    
    Return only the category name."""
    
    category = call_amd_llm(classification_prompt)
    
    return {
        "file": file_path,
        "extracted_text": text,
        "category": category.strip()
    }
```

---

## 🏆 Demo Talking Points

When presenting your AMD setup:

### Hardware
- "Running on AMD MI300X with 128GB HBM memory"
- "Self-hosted for data privacy - client data never leaves our secure environment"

### Software Stack
- "Production deployment using vLLM - not just basic inference"
- "Full ROCm stack: HIP for portability, MIGraphX for optimization"
- "OpenAI-compatible API for easy integration"

### Performance Metrics
```bash
# Get these numbers before your demo:
docker logs vllm-rocm | grep 'tokens/s'  # Inference speed
rocm-smi  # GPU utilization
docker stats vllm-rocm  # Memory usage
```

Say something like:
- "Achieving [X] tokens/second on MI300X"
- "Running 8B parameter model with sub-second response times"
- "Multi-GPU scaling ready via tensor parallelism"

---

## 🔄 Restarting/Managing Services

### Stop vLLM
```bash
docker stop vllm-rocm
```

### Restart vLLM
```bash
docker restart vllm-rocm
```

### Change Model
```bash
# Stop current container
docker stop vllm-rocm

# Edit start_vllm.sh and change the --model path
nano start_vllm.sh

# Start with new model
./start_vllm.sh
```

### Clean Up
```bash
# Remove container
docker stop vllm-rocm
docker rm vllm-rocm

# Remove models (careful! Large downloads)
rm -rf ~/ai-legal-tender/models/*

# Remove all setup
rm -rf ~/ai-legal-tender
```

---

## ⏱️ Time Estimates

Based on your execution plan:

- **Setup & Verification (Step 1):** 15 minutes
- **Model Download (Step 2):** 10-30 minutes
- **vLLM Container Start (Step 3):** 5 minutes
- **Testing (Step 4):** 5 minutes
- **OCR Setup (Step 5):** 10 minutes

**Total:** 45-65 minutes to have everything running

---

## 🆘 Quick Reference Commands

```bash
# Check GPU
rocm-smi

# View vLLM logs
docker logs -f vllm-rocm

# Test API
curl http://localhost:8000/v1/models

# Monitor GPU usage
watch -n 1 rocm-smi

# Restart everything
docker restart vllm-rocm
```

---

## 📞 Next Steps

After completing this setup:

1. ✅ **Phase 1 Complete:** AMD infrastructure running
2. ➡️ **Move to Phase 2:** Data ingestion (mock legal communications)
3. ➡️ **Move to Phase 3:** Build Google ADK orchestrator
4. ➡️ **Move to Phase 4:** Create specialist agents

**You now have:**
- ✅ Llama 3 running on AMD MI300X via vLLM
- ✅ OpenAI-compatible API endpoint for your agents
- ✅ OCR capability for document processing
- ✅ Full ROCm software stack deployed

---

## 💡 Pro Tips

1. **Start model download IMMEDIATELY** - it's the longest wait time
2. **Screenshot everything** - GPU specs, logs, performance metrics
3. **Test early** - don't wait until hour 4 to verify vLLM works
4. **Have fallback** - if vLLM fails, keep PyTorch + Transformers option ready
5. **Document performance** - judges love concrete numbers (tokens/s, latency)

---

Good luck with your hackathon! 🚀

**Questions?** Check logs first:
- vLLM: `docker logs vllm-rocm`
- ROCm: `dmesg | grep -i rocm`
- GPU: `rocm-smi --showproductname`
