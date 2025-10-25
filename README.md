# 🎯 QUICK START: Model-Agnostic Setup
## For Your Teammates Working on Model Selection and ADK Framework

---

## 📌 What's Been Done For You

I've created a **completely flexible, plug-and-play infrastructure** that works with **ANY Hugging Face model** your team chooses. No hardcoded dependencies on specific models!

### ✅ Ready-to-Use Components

```
```
Paralegal/
├── .env.example          # Template - teammates just copy and edit
├── config/
│   └── amd_config.py     # Reads everything from .env automatically
├── AMD_server/           # All AMD server code organized here
│   ├── setup/
│   │   ├── download_model_enhanced.sh   # Downloads ANY HF model
│   │   ├── start_vllm.sh                # Starts server with chosen model
│   │   ├── test_model.sh                # Validates model works
│   │   └── [setup scripts...]
│   ├── scraper/
│   │   ├── load_kaggle_datasets.py      # Kaggle dataset downloader
│   │   ├── load_morgan_files.py         # Morgan & Morgan loader
│   │   ├── database.py                  # Database utilities
│   │   └── [scraper tools...]
│   └── Morgan&Morgan/    # Real case files
├── backend/
│   ├── APIs/AMD/
│   │   └── llm_client.py            # Generic client for any model
│   ├── agents/
│   │   ├── client_communication_agent.py
│   │   ├── records_wrangler_agent.py
│   │   ├── legal_researcher_agent.py
│   │   └── evidence_sorter_agent.py
│   └── test_agents.py               # Tests all agents with chosen model
```
└── docs/
    └── MODEL_SETUP_GUIDE.md         # Step-by-step for teammates
```

---

## 🚀 For Your Teammates: 3-Minute Setup

### Step 1: Configure Their Model (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit with their chosen model
nano .env  # or code .env
```

They just need to set 2 lines:

```bash
MODEL_NAME=their-org/their-legal-model
MODEL_FOLDER=their-model-folder
```

**That's it!** Everything else auto-configures.

### Step 2: Download Model (1 minute active time)

```bash
cd setup
./download_model_enhanced.sh
```

Options:
1. Use model from `.env` ← **Easiest** (just press 1)
2. Enter custom HF path
3. Choose from legal models
4. Choose from general models

### Step 3: Test It Works (1 minute)

```bash
./start_vllm.sh    # Start server
./test_model.sh    # Validate everything works
```

---

## 🎓 For ADK Framework Team

The specialist agents are **already integrated** and ready to use with Google ADK:

### Agent Architecture

```python
# All agents follow the same pattern:

from backend.APIs.AMD.llm_client import AMDLLMClient

# Initialize (uses model from .env automatically)
llm_client = AMDLLMClient()  

# Use in agents
agent = ClientCommunicationAgent(llm_client)
result = agent.process(input_data)
```

### Integration Points for ADK Orchestrator

1. **Import the agents:**
   ```python
   from backend.agents.client_communication_agent import ClientCommunicationAgent
   from backend.agents.records_wrangler_agent import RecordsWranglerAgent
   from backend.agents.legal_researcher_agent import LegalResearcherAgent
   from backend.agents.evidence_sorter_agent import EvidenceSorterAgent
   ```

2. **Initialize with LLM client:**
   ```python
   from backend.APIs.AMD.llm_client import AMDLLMClient
   from config.amd_config import AMDConfig
   
   llm = AMDLLMClient(
       base_url=AMDConfig.VLLM_BASE_URL,
       model=AMDConfig.MODEL_FOLDER
   )
   
   # Create agents
   client_guru = ClientCommunicationAgent(llm)
   records_agent = RecordsWranglerAgent(llm)
   researcher = LegalResearcherAgent(llm)
   sorter = EvidenceSorterAgent(llm)
   ```

3. **Call from ADK orchestrator:**
   ```python
   # Example: Route to client communication agent
   result = client_guru.process(messy_client_message)
   
   # Returns:
   # {
   #     "original": "...",
   #     "polished_response": "...",
   #     "agent": "ClientCommunicationGuru"
   # }
   ```

---

## 🔧 Configuration Reference

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_NAME` | HuggingFace model path | `nlpaueb/legal-bert-base-uncased` |
| `MODEL_FOLDER` | Local folder name | `legal-bert-base` |
| `HUGGING_FACE_HUB_TOKEN` | HF access token | `hf_xxx...` |
| `VLLM_BASE_URL` | Server URL | `http://localhost:8000` |
| `MAX_MODEL_LEN` | Max sequence length | `4096` |
| `DEFAULT_TEMPERATURE` | Generation temperature | `0.7` |
| `DEFAULT_MAX_TOKENS` | Max tokens per response | `500` |

**All components read from this single file!**

---

## 🧪 Testing Workflow

### Test 1: Server-Level Test
```bash
cd setup
./test_model.sh
```

Validates:
- ✅ Server health
- ✅ Model loaded
- ✅ Completions work
- ✅ Chat works
- ✅ Response time
- ✅ GPU utilization

### Test 2: Agent-Level Test
```bash
cd backend
python3 test_agents.py
```

Tests all 4 agents:
- ✅ Client Communication Guru
- ✅ Records Wrangler
- ✅ Legal Researcher
- ✅ Evidence Sorter

---

## 💡 Model Flexibility Examples

### Example 1: Legal BERT

```bash
# In .env:
MODEL_NAME=nlpaueb/legal-bert-base-uncased
MODEL_FOLDER=legal-bert-base
MAX_MODEL_LEN=512
```

### Example 2: Fine-tuned Llama for Legal

```bash
# In .env:
MODEL_NAME=your-team/llama-3-legal-8b
MODEL_FOLDER=llama-3-legal
MAX_MODEL_LEN=4096
TRUST_REMOTE_CODE=false
```

### Example 3: Custom Legal Model

```bash
# In .env:
MODEL_NAME=your-team/custom-legal-instruct
MODEL_FOLDER=custom-legal-model
MAX_MODEL_LEN=2048
TRUST_REMOTE_CODE=true
```

**Switch models anytime by editing .env and restarting vLLM!**

---

## 🎯 What Makes This Flexible

### 1. **No Hardcoded Models**
- All model references use `AMDConfig.MODEL_NAME`
- Change `.env`, everything updates automatically

### 2. **Extensible Agent System**
- Agents work with ANY text generation model
- System prompts tuned for legal domain
- Easy to add new agents

### 3. **Configuration-Driven**
- Single `.env` file controls everything
- Teammates don't touch code to change models
- Validation ensures config is correct

### 4. **Comprehensive Testing**
- `test_model.sh` validates server setup
- `test_agents.py` validates agent integration
- Catch issues before demo time

---

## 📚 Documentation for Teammates

Send them to:
- **`docs/MODEL_SETUP_GUIDE.md`** - Complete guide with examples
- **`docs/README.md`** - Documentation index
- **`.env.example`** - Annotated configuration template
- **`AMD_server/setup/download_model_enhanced.sh`** - Self-documenting download script

---

## 🆘 Common Issues & Solutions

### "I want to use a different model"

```bash
# Edit .env
nano .env

# Change MODEL_NAME and MODEL_FOLDER
# Restart server
docker restart vllm-rocm
```

### "Model downloads but won't load"

Check model type compatibility:
- Some BERT models need different inference code
- vLLM works best with: Llama, Mistral, GPT-style models
- For BERT models, may need alternative serving method

### "Responses are bad quality"

Try tuning in `.env`:
```bash
DEFAULT_TEMPERATURE=0.5  # Lower = more deterministic
DEFAULT_MAX_TOKENS=300   # Shorter responses
```

Or update agent system prompts in `/backend/agents/`

---

## ✅ Ready for Hackathon

Your teammates can:
- ✅ Use ANY HuggingFace model
- ✅ Switch models anytime
- ✅ Test multiple models easily
- ✅ Integrate with ADK immediately
- ✅ Focus on their part (model selection, ADK)

**You've eliminated infrastructure friction!**

---

## 🤝 Division of Labor

| Team Member | Focus Area | What They Use |
|-------------|-----------|---------------|
| **Model Selection** | Choose/fine-tune legal model | `download_model_enhanced.sh`, `.env` |
| **ADK Framework** | Build orchestrator | Import from `backend/agents/` |
| **You** | Infrastructure (done!) | All setup scripts |

Everyone can work in parallel! 🎉

---

## 📞 Quick Commands Reference

```bash
# Setup model
cp .env.example .env
nano .env  # Configure
cd setup && ./download_model_enhanced.sh

# Start server
./start_vllm.sh

# Test
./test_model.sh
cd ../backend && python3 test_agents.py

# Monitor
docker logs -f vllm-rocm
rocm-smi  # On AMD hardware

# Switch models
nano ../.env  # Change MODEL_FOLDER
docker restart vllm-rocm
```

---

**Bottom line:** Your infrastructure is model-agnostic and ready. Teammates can plug in their model and go! 🚀
