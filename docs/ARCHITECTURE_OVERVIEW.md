# 📊 System Architecture Overview
## AI Legal Tender - Model-Agnostic Infrastructure

```
╔══════════════════════════════════════════════════════════════════════╗
║                    TEAMMATE CONFIGURATION LAYER                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   .env File (Single source of truth)                                 ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ MODEL_NAME=your-team/chosen-legal-model                     │   ║
║   │ MODEL_FOLDER=legal-model                                    │   ║
║   │ HUGGING_FACE_HUB_TOKEN=hf_xxx...                            │   ║
║   │ VLLM_BASE_URL=http://localhost:8000                         │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                                  ↓
╔══════════════════════════════════════════════════════════════════════╗
║                      MODEL DOWNLOAD & SETUP                           ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   AMD_server/setup/download_model_enhanced.sh                        ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ ✓ Reads MODEL_NAME from .env                                │   ║
║   │ ✓ Downloads from Hugging Face Hub                           │   ║
║   │ ✓ Saves to ~/ai-legal-tender/models/MODEL_FOLDER/           │   ║
║   │ ✓ Works with ANY HuggingFace model                          │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                                  ↓
╔══════════════════════════════════════════════════════════════════════╗
║                    AMD MI300X + vLLM SERVER                           ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   AMD_server/setup/start_vllm.sh                                     ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ Docker Container: vllm-rocm                                  │   ║
║   │ ├─ Loads model from MODEL_FOLDER                            │   ║
║   │ ├─ ROCm GPU acceleration                                    │   ║
║   │ ├─ OpenAI-compatible API                                    │   ║
║   │ └─ Endpoint: http://localhost:8000                          │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                                  ↓
╔══════════════════════════════════════════════════════════════════════╗
║                    CONFIGURATION & CLIENT LAYER                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   config/amd_config.py → backend/APIs/AMD/llm_client.py              ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ AMDConfig.validate()                                         │   ║
║   │ AMDLLMClient(base_url, model)                                │   ║
║   │ ├─ chat_completion()                                         │   ║
║   │ ├─ simple_prompt()                                           │   ║
║   │ ├─ health_check()                                            │   ║
║   │ └─ list_models()                                             │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                                  ↓
╔══════════════════════════════════════════════════════════════════════╗
║                      SPECIALIST AGENTS LAYER                          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   AMD_server/agents/                                                 ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ 1. ClientCommunicationAgent                                  │   ║
║   │    ├─ Input: Messy client messages                           │   ║
║   │    └─ Output: Polished professional responses                │   ║
║   │                                                               │   ║
║   │ 2. RecordsWranglerAgent                                      │   ║
║   │    ├─ Input: Case descriptions                               │   ║
║   │    └─ Output: Medical records requests                       │   ║
║   │                                                               │   ║
║   │ 3. LegalResearcherAgent                                      │   ║
║   │    ├─ Input: Injury type + jurisdiction                      │   ║
║   │    └─ Output: Research memos + settlement guidance           │   ║
║   │                                                               │   ║
║   │ 4. EvidenceSorterAgent                                       │   ║
║   │    ├─ Input: Document files (with OCR)                       │   ║
║   │    └─ Output: Classified documents                           │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
                                  ↓
╔══════════════════════════════════════════════════════════════════════╗
║                  GOOGLE ADK ORCHESTRATOR (Your teammate)              ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Imports and uses specialist agents                                 ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │ from backend.agents import *                                 │   ║
║   │                                                               │   ║
║   │ orchestrator.route_to_agent(task_type, input_data)           │   ║
║   │ └─> Calls appropriate specialist agent                       │   ║
║   │     └─> Gets response from YOUR model                        │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🔄 Data Flow Example

```
User Input: "hey i got hurt at work and idk what to do???"
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ Google ADK Orchestrator                                       │
│ ├─ Classifies as: CLIENT_COMMUNICATION                        │
│ └─ Routes to: ClientCommunicationAgent                        │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ ClientCommunicationAgent                                      │
│ ├─ Builds prompt with system message                          │
│ └─ Calls: llm_client.simple_prompt(...)                       │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ AMDLLMClient                                                   │
│ ├─ Formats request for OpenAI-compatible API                  │
│ └─ POST to: http://localhost:8000/v1/chat/completions         │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ vLLM Server (Your teammate's chosen model)                    │
│ ├─ Runs inference on AMD MI300X                               │
│ ├─ Generates professional legal response                      │
│ └─ Returns JSON response                                      │
└───────────────────────────────────────────────────────────────┘
                              ↓
Response: "Thank you for reaching out. I understand you were 
injured at work, and I want to help. Based on what you've 
described, this may be a workplace injury case..."
                              ↓
                    [Approval Interface]
                              ↓
                    [Outreach Automation]
```

---

## 🎯 Key Flexibility Points

### 1. **Model Independence**
```
ANY HuggingFace Model
├─> Configure in .env
├─> Download with enhanced script
├─> Load in vLLM
└─> All agents work automatically
```

### 2. **Configuration Hierarchy**
```
.env
 ├─> config/amd_config.py (reads .env)
 ├─> backend/APIs/AMD/llm_client.py (uses config)
 └─> AMD_server/agents/*.py (uses client)
```

### 3. **Testing Layers**
```
AMD_server/setup/test_model.sh
 ├─ Server health ✓
 ├─ Model loaded ✓
 ├─ API responses ✓
 └─ Performance metrics ✓

AMD_server/test_agents.py
 ├─ Agent 1 ✓
 ├─ Agent 2 ✓
 ├─ Agent 3 ✓
 └─ Agent 4 ✓
```

---

## 📦 File Responsibilities

| File | Purpose | Who Uses |
|------|---------|----------|
| `.env` | Configuration | **Model team** edits this |
| `download_model_enhanced.sh` | Get model | **Model team** runs this |
| `start_vllm.sh` | Start server | **Everyone** uses this |
| `test_model.sh` | Validate setup | **Model team** tests with this |
| `llm_client.py` | API wrapper | **ADK team** imports this |
| `agents/*.py` | Specialist agents | **ADK team** imports these |
| `test_agents.py` | E2E test | **Everyone** validates with this |

---

## 🚀 Quick Start Flow

```bash
# Model Team Setup (5 minutes)
cp .env.example .env              # Configure
nano .env                         # Edit MODEL_NAME
cd setup
./download_model_enhanced.sh      # Download
./start_vllm.sh                   # Start server
./test_model.sh                   # Validate

# ADK Team Integration (already done!)
from backend.agents import *      # Import agents
# Use in orchestrator
```

---

## ✅ What's Complete

- [x] Model-agnostic configuration system
- [x] Flexible model download script
- [x] Generic LLM client (works with any model)
- [x] 4 specialist agents (pre-built)
- [x] Comprehensive testing tools
- [x] Clear documentation for teammates
- [x] Ready for ADK integration

---

## 🤝 Team Collaboration

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Model Team    │     │   ADK Team      │     │   Your Work     │
│                 │     │                 │     │                 │
│ Choose model    │     │ Build           │     │ Infrastructure  │
│ Configure .env  │────▶│ orchestrator    │────▶│ (COMPLETE!)     │
│ Test model      │     │ Integrate       │     │                 │
│                 │     │ agents          │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                         │
        └───────────────────────┴─────────────────────────┘
                    All work in parallel! 🎉
```

---

## 🎉 Bottom Line

Your infrastructure is **completely model-agnostic** and **ready for the hackathon**!

- ✅ Model team can plug in ANY Hugging Face model
- ✅ ADK team can import and use pre-built agents
- ✅ Everyone can work independently
- ✅ No blocking dependencies!

**Time saved: Hours of integration headaches avoided! 🚀**
