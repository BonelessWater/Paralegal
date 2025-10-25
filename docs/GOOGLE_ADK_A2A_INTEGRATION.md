# Google ADK A2A Protocol Integration Guide
## Connecting Saul-7B on AMD vLLM with Google ADK Agent Protocol

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Google ADK A2A Protocol Layer                 │
│                  (Agent-to-Agent Communication)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│              Paralegal Specialist Agents (Local)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Client     │  │   Records    │  │    Legal     │          │
│  │Communication │  │  Wrangler    │  │  Researcher  │  +more   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ↓
                  ┌──────────────────────┐
                  │   AMDLLMClient API   │
                  │  (OpenAI-compatible) │
                  └──────────┬───────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              AMD MI300X Server (Remote Compute)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  vLLM Server (http://amd-server:8000)                    │  │
│  │  ┌────────────────────────────────────────────┐          │  │
│  │  │  Saul-7B-Instruct-v1                       │          │  │
│  │  │  (Legal-focused Llama 2 fine-tune)         │          │  │
│  │  │  - 7B parameters                            │          │  │
│  │  │  - ~14GB model size                         │          │  │
│  │  │  - Optimized for legal reasoning            │          │  │
│  │  └────────────────────────────────────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Component Breakdown

### 1. **Hugging Face Model: Saul-7B-Instruct-v1**

**Model Details:**
- **Repository:** https://huggingface.co/Equall/Saul-7B-Instruct-v1
- **Base:** Llama 2 7B fine-tuned on legal domain data
- **Size:** ~14GB (7 billion parameters)
- **Strengths:** 
  - Legal document understanding
  - Case law reasoning
  - Contract analysis
  - Compliance and regulatory text
- **License:** Check HuggingFace model card (typically Llama 2 Community License)

**Why Saul-7B for Legal Work:**
- Pre-trained on legal corpora (case law, statutes, contracts)
- Instruction-tuned for legal Q&A and analysis tasks
- Smaller than 70B variants (faster inference, lower memory)
- Better legal performance than general-purpose 7B models

### 2. **AMD MI300X Server + vLLM**

**Compute Infrastructure:**
- **Hardware:** AMD MI300X GPU(s) with ROCm
- **Software:** vLLM inference server (OpenAI-compatible API)
- **Endpoint:** `http://<amd-server-ip>:8000/v1/chat/completions`

**vLLM Benefits:**
- High-throughput batched inference
- PagedAttention for memory efficiency
- Continuous batching for low latency
- OpenAI API compatibility (easy integration)

**Configuration (in `.env`):**
```bash
VLLM_BASE_URL=http://<amd-server-ip-or-hostname>:8000
MODEL_NAME=Equall/Saul-7B-Instruct-v1
MODEL_FOLDER=saul-7b-instruct
MAX_MODEL_LEN=4096
TENSOR_PARALLEL_SIZE=1  # or 2+ for multi-GPU
```

### 3. **Local Paralegal Agents**

**Four Specialist Agents:**

1. **Client Communication Agent** (`client_communication_agent.py`)
   - Translates messy client messages into professional legal responses
   - System prompt: "You are a professional paralegal assistant..."

2. **Records Wrangler Agent** (`records_wrangler_agent.py`)
   - Organizes, categorizes, and indexes legal documents
   - System prompt: "You are a meticulous records management specialist..."

3. **Legal Researcher Agent** (`legal_researcher_agent.py`)
   - Searches case law, statutes, and legal precedents
   - System prompt: "You are an expert legal researcher..."

4. **Evidence Sorter Agent** (`evidence_sorter_agent.py`)
   - Analyzes and categorizes evidence for case preparation
   - System prompt: "You are an evidence analysis specialist..."

**All agents:**
- Use `AMDLLMClient` to call vLLM server
- Accept structured input (JSON or dict)
- Return structured output (JSON with agent metadata)
- Stateless (can run in parallel)

### 4. **Google ADK A2A Protocol**

**What is A2A (Agent-to-Agent Protocol)?**
- Standard for AI agents to communicate and collaborate
- Part of Google's Agent Development Kit (ADK)
- Enables:
  - Agent discovery
  - Task delegation
  - Result aggregation
  - Multi-agent workflows

**A2A Integration Points:**

```python
# Example ADK A2A wrapper for Paralegal agents

from google_adk import A2AAgent, A2AMessage
from backend.agents.client_communication_agent import ClientCommunicationAgent
from backend.APIs.AMD.llm_client import AMDLLMClient
from config.amd_config import AMDConfig

class ParalegalA2AAgent(A2AAgent):
    """A2A-compatible wrapper for Paralegal specialist agents"""
    
    def __init__(self, agent_type: str):
        super().__init__(name=f"paralegal-{agent_type}")
        
        # Initialize AMD LLM client
        self.llm_client = AMDLLMClient(
            base_url=AMDConfig.VLLM_BASE_URL,
            model=AMDConfig.MODEL_FOLDER
        )
        
        # Initialize specialist agent
        if agent_type == "client-communication":
            self.agent = ClientCommunicationAgent(self.llm_client)
        elif agent_type == "records-wrangler":
            self.agent = RecordsWranglerAgent(self.llm_client)
        # ... etc for other agents
        
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process incoming A2A message and return response"""
        
        # Extract input from A2A message
        input_data = message.payload
        
        # Call specialist agent
        result = self.agent.process(input_data)
        
        # Wrap result in A2A message format
        return A2AMessage(
            sender=self.name,
            recipient=message.sender,
            payload=result,
            metadata={
                "model": AMDConfig.MODEL_NAME,
                "agent_type": self.agent.__class__.__name__
            }
        )
```

---

## 🔧 Setup Instructions

### Step 1: Configure Saul-7B Model

**Edit `.env` file:**
```bash
# Model configuration (ALREADY UPDATED)
MODEL_NAME=Equall/Saul-7B-Instruct-v1
MODEL_FOLDER=saul-7b-instruct

# AMD server endpoint (UPDATE WITH YOUR SERVER IP/HOSTNAME)
VLLM_BASE_URL=http://<amd-server-ip>:8000

# Model parameters
MAX_MODEL_LEN=4096
TENSOR_PARALLEL_SIZE=1
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=500
```

**Note:** If AMD server is remote, replace `localhost` with server IP/hostname.

### Step 2: Download Saul-7B to AMD Server

**On AMD server (or local with remote mount):**

```bash
# Navigate to project
cd /path/to/Paralegal

# Run download script (interactive)
bash setup/download_model_enhanced.sh

# Choose option 1 (use .env) or option 2 (enter Equall/Saul-7B-Instruct-v1)
```

**Or non-interactive:**
```bash
export MODELS_PATH=/path/to/models
export MODEL_NAME=Equall/Saul-7B-Instruct-v1
export MODEL_FOLDER=saul-7b-instruct
huggingface-cli download $MODEL_NAME --local-dir $MODELS_PATH/$MODEL_FOLDER
```

**Download size:** ~14GB (may take 10-30 minutes depending on network)

### Step 3: Start vLLM Server on AMD Hardware

**On AMD MI300X server:**

```bash
# Start vLLM with Saul-7B
cd /path/to/Paralegal/setup
bash start_vllm.sh

# Or manually with Docker:
docker run -d \
  --name vllm-saul \
  --device=/dev/kfd --device=/dev/dri \
  --ipc=host --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
  -p 8000:8000 \
  -v /path/to/models:/models \
  rocm/pytorch:rocm6.0_ubuntu22.04_py3.10_pytorch_2.1.1 \
  python3 -m vllm.entrypoints.openai.api_server \
    --model /models/saul-7b-instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096 \
    --dtype float16
```

**Verify server is running:**
```bash
# Health check
curl http://<amd-server-ip>:8000/health

# List loaded models
curl http://<amd-server-ip>:8000/v1/models
```

### Step 4: Test AMD Connection from Local Machine

**Update VLLM_BASE_URL in `.env` if server is remote:**
```bash
VLLM_BASE_URL=http://192.168.1.100:8000  # Example IP
```

**Run connection test:**
```bash
cd /path/to/Paralegal/setup
bash test_model.sh
```

**Or test with Python:**
```python
from backend.APIs.AMD.llm_client import AMDLLMClient
from config.amd_config import AMDConfig

# Initialize client (reads from .env)
client = AMDLLMClient(
    base_url=AMDConfig.VLLM_BASE_URL,
    model=AMDConfig.MODEL_FOLDER
)

# Health check
if client.health_check():
    print("✅ Connected to AMD vLLM server")
else:
    print("❌ Cannot reach AMD server")

# Test prompt
response = client.simple_prompt(
    prompt="What is a tort in legal terms?",
    system_message="You are a legal expert assistant."
)
print(f"Response: {response}")
```

### Step 5: Test Specialist Agents

**Run agent test suite:**
```bash
cd /path/to/Paralegal/backend
python3 test_agents.py
```

**Expected output:**
```
Testing Client Communication Agent...
✅ Client Communication Agent works!

Testing Records Wrangler Agent...
✅ Records Wrangler Agent works!

Testing Legal Researcher Agent...
✅ Legal Researcher Agent works!

Testing Evidence Sorter Agent...
✅ Evidence Sorter Agent works!
```

### Step 6: Integrate with Google ADK A2A Protocol

**Install Google ADK (if not already):**
```bash
pip install google-adk  # or follow ADK installation docs
```

**Create A2A agent wrappers:**
```bash
# Create integration file
mkdir -p backend/integrations
touch backend/integrations/adk_a2a_agents.py
```

**Implement A2A wrapper (see example in "A2A Integration Points" section above)**

**Register agents with ADK:**
```python
from backend.integrations.adk_a2a_agents import ParalegalA2AAgent
from google_adk import A2ARegistry

# Register all specialist agents
registry = A2ARegistry()
registry.register(ParalegalA2AAgent("client-communication"))
registry.register(ParalegalA2AAgent("records-wrangler"))
registry.register(ParalegalA2AAgent("legal-researcher"))
registry.register(ParalegalA2AAgent("evidence-sorter"))

# Start A2A server
registry.serve(host="0.0.0.0", port=9000)
```

---

## 🔄 Data Flow Example

**Scenario:** Client sends unstructured request → ADK orchestrator → Specialist agents → Saul-7B

```
1. Client Input (via ADK):
   "I need help with my car accident case. Insurance won't pay."

2. ADK Orchestrator:
   - Analyzes request type
   - Routes to Client Communication Agent via A2A

3. Client Communication Agent:
   - Receives A2A message
   - Constructs prompt for Saul-7B:
     System: "You are a professional paralegal..."
     User: "Polish this client message: 'I need help...'"
   
4. AMD vLLM Server:
   - Saul-7B processes prompt
   - Returns: "Thank you for reaching out. I understand you're facing
     challenges with an insurance claim following a vehicle accident..."

5. Agent wraps response:
   {
     "original": "I need help...",
     "polished_response": "Thank you for reaching out...",
     "agent": "ClientCommunicationGuru",
     "model": "Equall/Saul-7B-Instruct-v1"
   }

6. ADK Orchestrator:
   - Receives A2A response
   - May route to other agents (Records, Researcher) for follow-up
   - Aggregates results
   - Returns to client
```

---

## 🚀 Performance & Optimization

### Expected Performance (AMD MI300X + Saul-7B)

| Metric | Value |
|--------|-------|
| Model size | ~14GB (7B params) |
| Inference latency | 50-200ms per token |
| Throughput | 20-50 tokens/sec (single GPU) |
| Max context | 4096 tokens |
| Concurrent requests | 5-10 (with batching) |

### Optimization Tips

1. **Enable Continuous Batching (vLLM default):**
   - Automatically batches concurrent requests
   - Reduces latency for multiple agents calling simultaneously

2. **Tune Temperature for Legal Work:**
   ```bash
   DEFAULT_TEMPERATURE=0.5  # Lower = more deterministic (good for legal)
   ```

3. **Multi-GPU Setup (if available):**
   ```bash
   TENSOR_PARALLEL_SIZE=2  # Split model across 2 GPUs
   ```

4. **Quantization (if memory constrained):**
   ```bash
   QUANTIZATION=awq  # 4-bit quantization (smaller, faster)
   ```

5. **A2A Async Processing:**
   - Use async/await in A2A handlers
   - Agents can run in parallel via ADK orchestrator

---

## 🔒 Security Considerations

### 1. Network Security
- If AMD server is remote, use VPN or SSH tunnel
- Restrict vLLM port (8000) to trusted IPs
- Consider HTTPS proxy (nginx/traefik) for production

### 2. Token Management
- Never commit `.env` with real tokens to git
- Use `.gitignore` to exclude `.env`
- For production, use secret management (AWS Secrets, Azure Key Vault)

### 3. Input Validation
- Agents should validate input before sending to LLM
- Implement rate limiting on A2A endpoints
- Sanitize client data (PII, confidential info)

---

## 🆘 Troubleshooting

### Issue: "Cannot connect to AMD server"

**Symptoms:**
- `health_check()` returns False
- Connection timeout errors

**Solutions:**
1. Verify server IP/hostname in `.env`
2. Check network connectivity: `ping <amd-server-ip>`
3. Verify vLLM is running: `docker ps` or `ps aux | grep vllm`
4. Check firewall allows port 8000

### Issue: "Model not found on server"

**Symptoms:**
- 404 errors from vLLM API
- Model name mismatch

**Solutions:**
1. Verify model downloaded: `ls -la ~/ai-legal-tender/models/saul-7b-instruct`
2. Check `MODEL_FOLDER` in `.env` matches vLLM `--model` path
3. Restart vLLM server after model download

### Issue: "Slow inference / timeouts"

**Symptoms:**
- Responses take >30 seconds
- Timeout errors

**Solutions:**
1. Reduce `MAX_MODEL_LEN` (less memory, faster)
2. Lower `DEFAULT_MAX_TOKENS` (shorter responses)
3. Check GPU utilization: `rocm-smi` (should be high during inference)
4. Enable quantization for smaller memory footprint

### Issue: "A2A messages not routing to agents"

**Symptoms:**
- ADK orchestrator can't find agents
- Registration errors

**Solutions:**
1. Verify A2A registry is running
2. Check agent names match ADK configuration
3. Ensure async handlers are properly awaited
4. Review ADK logs for routing errors

---

## 📚 Additional Resources

### Saul-7B Model
- **Model Card:** https://huggingface.co/Equall/Saul-7B-Instruct-v1
- **Paper:** [Insert paper link if available]
- **License:** Check model repository

### vLLM Documentation
- **Official Docs:** https://docs.vllm.ai/
- **AMD ROCm Support:** https://github.com/vllm-project/vllm/blob/main/docs/source/getting_started/amd-installation.rst

### Google ADK A2A Protocol
- **ADK Documentation:** [Insert Google ADK docs link]
- **A2A Specification:** [Insert A2A spec link]
- **Examples:** [Insert examples repo]

### AMD MI300X Resources
- **ROCm Documentation:** https://rocm.docs.amd.com/
- **Performance Tuning:** https://rocm.docs.amd.com/en/latest/conceptual/gpu-arch.html

---

## ✅ Quick Checklist

Before going live with Saul-7B + ADK A2A:

- [ ] `.env` configured with Saul-7B model name
- [ ] AMD server IP/hostname set in `VLLM_BASE_URL`
- [ ] Saul-7B downloaded to AMD server (~14GB)
- [ ] vLLM server running and accessible
- [ ] Health check passes from local machine
- [ ] All 4 specialist agents tested successfully
- [ ] Google ADK installed and A2A registry configured
- [ ] A2A wrapper agents registered with ADK
- [ ] Network security configured (VPN/firewall)
- [ ] Monitoring/logging enabled for production
- [ ] Backup AMD server configuration documented

---

## 🎉 Summary

You now have:
- ✅ **Saul-7B-Instruct** (legal-focused LLM from HuggingFace)
- ✅ **AMD MI300X compute** (high-performance GPU inference)
- ✅ **vLLM server** (OpenAI-compatible API)
- ✅ **4 Specialist Agents** (legal domain experts)
- ✅ **Google ADK A2A** (agent-to-agent communication protocol)

**Complete flow:**
```
Client → ADK Orchestrator → A2A Protocol → Paralegal Agents → 
vLLM API → Saul-7B on AMD → Legal Response → Client
```

**You're ready for production legal AI workflows! 🚀⚖️**
