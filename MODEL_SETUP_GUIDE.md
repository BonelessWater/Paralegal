# 🚀 Quick Start Guide for Your Teammates
## Adding ANY Hugging Face Model to the AI Legal Tender System

---

## 📋 TL;DR - 3 Steps to Add Your Model

```bash
# 1. Configure your model
cp .env.example .env
# Edit .env and set MODEL_NAME and MODEL_FOLDER

# 2. Download the model
cd setup
./download_model_enhanced.sh

# 3. Test it works
./test_model.sh
```

**That's it!** The system is designed to work with ANY Hugging Face model you choose.

---

## 🎯 Step-by-Step Instructions

### Step 1: Choose Your Legal Model

Browse Hugging Face for legal-focused models:
- 🔍 Search: https://huggingface.co/models?search=legal
- 📊 Popular legal models:
  - `nlpaueb/legal-bert-base-uncased` - Legal BERT
  - `law-ai/InLegalBERT` - InLegal BERT
  - `pile-of-law/legalbert-large-1.7M-1` - Large Legal BERT
  - Or ANY custom model your team builds/finds!

### Step 2: Configure Your Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env
# OR
code .env
```

**Update these two critical lines:**

```bash
# Your Hugging Face token (get from https://huggingface.co/settings/tokens)
HUGGING_FACE_HUB_TOKEN=hf_YourActualTokenHere

# Your chosen model (format: "organization/model-name")
MODEL_NAME=nlpaueb/legal-bert-base-uncased

# Local folder name (will be created automatically)
MODEL_FOLDER=legal-bert-base
```

### Step 3: Download Your Model

```bash
cd setup
./download_model_enhanced.sh
```

**The script offers 4 options:**
1. **Use model from .env** (recommended - just hit "1" and Enter)
2. **Enter custom model path** (for any HF model not in the list)
3. **Select from legal models** (curated list of legal-focused models)
4. **Select from general models** (Llama, Mistral, etc.)

💡 **Tip:** If you configured `.env`, just choose option 1!

### Step 4: Start vLLM Server

The download script can auto-update `start_vllm.sh` with your model, or you can do it manually:

```bash
# Option A: Let the download script update it (recommended)
# It asks at the end of download: "Auto-update start_vllm.sh?"

# Option B: Manual update
nano start_vllm.sh
# Change the --model line to: --model /models/YOUR_MODEL_FOLDER
```

Then start the server:

```bash
./start_vllm.sh
```

Wait 30-60 seconds for the model to load.

### Step 5: Test Your Model

```bash
./test_model.sh
```

This will:
- ✅ Check server health
- ✅ List loaded models  
- ✅ Send test prompt
- ✅ Verify responses are generated

---

## 🔧 Advanced Configuration

### Model-Specific Settings

Some models need special settings. Edit `.env`:

```bash
# For larger models, increase max length
MAX_MODEL_LEN=8192

# For models with custom code
TRUST_REMOTE_CODE=true

# For quantized models
QUANTIZATION=awq  # or gptq, squeezellm

# For multi-GPU setups
TENSOR_PARALLEL_SIZE=2
```

### Testing Different Models Quickly

Want to try multiple models? It's easy:

```bash
# Download model 1
./download_model_enhanced.sh
# Choose your first model

# Download model 2
./download_model_enhanced.sh
# Choose your second model

# Switch between them by editing .env:
MODEL_FOLDER=legal-bert-base  # Use model 1
# OR
MODEL_FOLDER=llama-3-8b       # Use model 2

# Restart vLLM
docker restart vllm-rocm
```

---

## 📖 Examples for Common Legal Models

### Example 1: Legal BERT

```bash
# In .env:
MODEL_NAME=nlpaueb/legal-bert-base-uncased
MODEL_FOLDER=legal-bert-base
MAX_MODEL_LEN=512  # BERT models typically use 512
```

### Example 2: Llama 3 (Fine-tuned for Legal)

```bash
# In .env:
MODEL_NAME=your-org/llama-3-legal-8b
MODEL_FOLDER=llama-3-legal
MAX_MODEL_LEN=4096
TRUST_REMOTE_CODE=false
```

### Example 3: Custom Legal Model

```bash
# In .env:
MODEL_NAME=your-team/custom-legal-model
MODEL_FOLDER=custom-legal-model
MAX_MODEL_LEN=2048
TRUST_REMOTE_CODE=true  # If you have custom model code
```

---

## 🆘 Troubleshooting

### "Model not found" Error

**Problem:** Model doesn't exist or wrong path

**Solutions:**
1. Verify model path at https://huggingface.co/models
2. Check for typos in `MODEL_NAME`
3. Some models are gated - accept the license on HF first

### "Authentication Required" Error

**Problem:** Need Hugging Face token

**Solutions:**
1. Get token: https://huggingface.co/settings/tokens
2. Add to `.env`: `HUGGING_FACE_HUB_TOKEN=hf_...`
3. Or run: `huggingface-cli login`

### "Out of Memory" Error

**Problem:** Model too large for GPU

**Solutions:**
1. Use smaller model
2. Enable quantization in `.env`: `QUANTIZATION=awq`
3. Reduce `MAX_MODEL_LEN` in `.env`

### "Model loads but gives bad responses"

**Problem:** Model may not be instruction-tuned

**Solutions:**
1. Try an "Instruct" variant: `meta-llama/Meta-Llama-3-8B-Instruct`
2. Adjust temperature: `DEFAULT_TEMPERATURE=0.5` (lower = more deterministic)
3. Change the system prompts in `/AMD_server/agents/` files

---

## 🧪 Testing Your Model with the Agents

Once your model is running, test it with the specialist agents:

```bash
cd ..
python3 AMD_server/test_agents.py
```

This will run all 4 specialist agents with your model:
1. ✅ Client Communication Guru
2. ✅ Records Wrangler
3. ✅ Legal Researcher
4. ✅ Evidence Sorter

---

## 💡 Pro Tips

### Tip 1: Keep Multiple Models

Download multiple models to compare:

```bash
~/ai-legal-tender/models/
├── legal-bert-base/     # Legal-focused BERT
├── llama-3-8b/          # General Llama
└── custom-legal-model/  # Your custom model
```

Switch between them by changing `MODEL_FOLDER` in `.env`

### Tip 2: Model Naming Convention

Use descriptive folder names:

```bash
# Good
MODEL_FOLDER=legal-bert-contracts
MODEL_FOLDER=llama-3-8b-injury-law

# Bad
MODEL_FOLDER=model1
MODEL_FOLDER=test
```

### Tip 3: Document Your Model Choice

Add a comment in `.env`:

```bash
# Using Legal BERT - best for document classification
# Tested on 100 sample legal docs - 94% accuracy
MODEL_NAME=nlpaueb/legal-bert-base-uncased
MODEL_FOLDER=legal-bert-base
```

---

## 🎓 Understanding the File Structure

```
Paralegal/
├── .env                    # ← YOUR CONFIG HERE
├── .env.example           # Template
├── config/
│   └── amd_config.py      # Reads from .env
├── AMD_server/
│   ├── setup/
│   │   ├── download_model_enhanced.sh  # ← DOWNLOAD YOUR MODEL
│   │   ├── start_vllm.sh               # ← START SERVER
│   │   └── test_model.sh               # ← TEST IT WORKS
│   ├── agents/
│   │   ├── client_communication_agent.py
│   │   ├── records_wrangler_agent.py
│   │   ├── legal_researcher_agent.py
│   │   └── evidence_sorter_agent.py
│   └── test_agents.py
└── backend/
    └── APIs/AMD/
        └── llm_client.py   # Uses your model automatically
        ├── legal_researcher_agent.py
        └── evidence_sorter_agent.py
```

**Key Point:** Once you set up `.env`, ALL parts of the system automatically use your chosen model!

---

## ✅ Checklist for Your Teammates

Before the hackathon demo:

- [ ] `.env` file created and configured
- [ ] `HUGGING_FACE_HUB_TOKEN` set correctly
- [ ] `MODEL_NAME` points to your legal model
- [ ] Model downloaded successfully
- [ ] vLLM server starts without errors
- [ ] Test script passes all checks
- [ ] Agents produce coherent legal responses
- [ ] Response time is acceptable (< 5 seconds)
- [ ] GPU utilization is good (check with `rocm-smi`)

---

## 🚀 Ready to Go!

Your infrastructure is **completely model-agnostic**. You can:

✅ Use ANY Hugging Face model  
✅ Switch models anytime  
✅ Test multiple models  
✅ Use custom fine-tuned models  
✅ Use general-purpose or legal-specific models  

**The system adapts automatically!**

Questions? Check the troubleshooting section or examine the example configurations above.

Good luck with the hackathon! 🎉
