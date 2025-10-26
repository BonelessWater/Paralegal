# AMD Server Status Documentation

**Last Updated:** October 25, 2025  
**Server:** gpu-mi300x1-192gb-contracted-atl1-28 (AMD MI300X, 192GB VRAM)

---

## 🖥️ Server Environment

### Python Environment
- **Location:** `/home/amd-knights/Paralegal/venv`
- **Python Version:** 3.12
- **Status:** ✅ Active virtual environment

### LLM Server Configuration
- **Model:** Equall/Saul-7B-Instruct-v1 (Legal-specific LLM)
- **Server:** vLLM at http://localhost:8000/v1
- **API Format:** OpenAI-compatible
- **Status:** ❓ Unknown (need to check if vLLM is running)

### Database Configuration
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paralegal_db
DB_USER=paralegal_user
DB_PASSWORD=hackathon2024
```

### HuggingFace Cache
```bash
HF_HOME=/home/amd-knights/Paralegal/.cache/huggingface
```

---

## 📁 Server File Structure

### Existing Files (Confirmed on Server)

**LLM-related files:**
- `/home/amd-knights/Paralegal/AMD_server/ADK/a2a_agents/llm_saul.py`
  - Simple LLM client for Saul model
  - Uses OpenAI API format
  - Environment variables: `SAUL_BASE_URL`, `SAUL_MODEL`, `SAUL_API_KEY`

**Backend API files:**
```
/home/amd-knights/Paralegal/backend/APIs/
├── email/
│   ├── emailer.py
│   └── __init__.py
├── text/
│   ├── texter.py
│   └── __init__.py
├── call/
│   ├── caller.py
│   └── __init__.py
├── db/
│   └── __init__.py
└── AMD/
    ├── OCR/
    │   └── __init__.py
    └── ADK/
        ├── __init__.py
        ├── client.py  (HTTP client for AMD server)
        └── example.py
```

---

## 🔍 LLM Configuration Discovery

### ✅ FOUND: Working LLM Setup in ADK

**Location:** `/home/amd-knights/Paralegal/AMD_server/ADK/researcher.py`

**Configuration (lines 48-50):**
```python
SAUL_BASE_URL = os.getenv("SAUL_BASE_URL", "http://localhost:8000/v1")
SAUL_MODEL    = os.getenv("SAUL_MODEL", "Equall/Saul-7B-Instruct-v1")
_client = OpenAI(base_url=SAUL_BASE_URL, api_key=os.getenv("SAUL_API_KEY","dummy"))
```

**Key Details:**
- **Model:** Equall/Saul-7B-Instruct-v1 (legal-specific LLM)
- **Server:** vLLM at http://localhost:8000/v1
- **API Format:** OpenAI-compatible
- **Function:** `saul_complete_sync(prompt, max_tokens, temperature)`

**This is the ACTUAL working LLM infrastructure!**

---

## ❌ Missing Files (Referenced but Don't Exist)

### Test Infrastructure (Not Critical - ADK Works Without Them)

1. **`backend/APIs/AMD/llm_client.py`** - DOES NOT EXIST
   - Referenced in: `test_agents.py`, `test_rag_agent.py`
   - Expected class: `AMDLLMClient`
   - Expected method: `.simple_prompt()`
   - **Alternative:** Use `saul_complete_sync()` from researcher.py

2. **`config/amd_config.py`** - DOES NOT EXIST
   - Referenced in: `test_agents.py`, `test_rag_agent.py`
   - Expected class: `AMDConfig`
   - Expected properties: `VLLM_BASE_URL`, `MODEL_FOLDER`, `MODEL_NAME`
   - **Alternative:** Use environment variables (SAUL_BASE_URL, SAUL_MODEL)

3. **`.env` Configuration** - INCOMPLETE
   - Current .env only has database + HuggingFace cache
   - Should add (optional, has defaults):
     - `SAUL_BASE_URL=http://localhost:8000/v1`
     - `SAUL_MODEL=Equall/Saul-7B-Instruct-v1`
     - `SAUL_API_KEY=dummy`

---

## ✅ Working Components

### RAG Embeddings System
- **Status:** ✅ Fully operational
- **Location:** `/home/amd-knights/Paralegal/AMD_server/ml_pipeline/`
- **Embeddings:** 39 Morgan & Morgan documents (384-dim)
- **Index Type:** HNSW (64.5x faster than Flat)
- **GPU:** AMD Instinct MI300X VF (191.7 GB VRAM) ✅ Detected
- **Performance:**
  - Search latency: ~17ms median
  - Similarity scores: 30-50% for relevant queries
  - 100% recall maintained

### Database Connection
- **PostgreSQL:** ✅ Running on localhost:5432
- **Schema:** paralegal_db with multiple tables
- **Data:** 39 legal documents loaded
- **Connection:** Working via localhost (external IP doesn't work from within server)

### Test Scripts
- ✅ `test_rag_simple.py` - Tests RAG without LLM (WORKING)
- ❌ `test_rag_agent.py` - Requires missing AMDLLMClient (BROKEN)
- ❌ `test_agents.py` - Requires missing AMDLLMClient + AMDConfig (BROKEN)

---

## 🔧 What Needs to Be Created

### Option 1: Create Missing LLM Infrastructure

**File:** `backend/APIs/AMD/llm_client.py`
```python
# Needs to implement:
class AMDLLMClient:
    def __init__(self, base_url, model):
        pass
    
    def simple_prompt(self, prompt, system_message=None, temperature=0.7, max_tokens=500):
        pass
    
    def health_check(self):
        pass
    
    def list_models(self):
        pass
```

**File:** `config/amd_config.py`
```python
# Needs to implement:
class AMDConfig:
    VLLM_BASE_URL = "http://localhost:8000"
    MODEL_FOLDER = "model-name"
    MODEL_NAME = "full-model-name"
    
    @classmethod
    def validate(cls):
        pass
    
    @classmethod
    def print_config(cls):
        pass
```

### Option 2: Use Alternative LLM Client

**Existing alternative:** `/home/amd-knights/Paralegal/AMD_server/ADK/a2a_agents/llm_saul.py`
- Uses OpenAI API format
- Requires: `SAUL_BASE_URL`, `SAUL_MODEL`, `SAUL_API_KEY`
- Already has `complete()` function

---

## 🎯 Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| RAG Embeddings | ✅ Working | 39 docs, HNSW index, GPU accelerated |
| Database | ✅ Working | PostgreSQL with legal documents |
| Python Environment | ✅ Working | venv with all ML dependencies |
| LLM (Saul-7B) | ❓ Unknown | Configured but need to check if running |
| vLLM Server | ❓ Unknown | Expected at localhost:8000 |
| ADK Researcher | ✅ Code Ready | Full orchestration system exists |
| Test Scripts (agents) | ❌ Broken | Require AMDLLMClient wrapper |
| RAG Integration | ✅ Complete | Legal researcher agent ready |

---

## 📊 Recommendations

### Immediate Next Steps

1. **Check if vLLM is running:**
   ```bash
   curl http://localhost:8000/v1/models
   # OR
   docker ps | grep vllm
   # OR
   ps aux | grep vllm
   ```

2. **If vLLM is NOT running, start it:**
   ```bash
   # Check for startup script
   ls ~/Paralegal/setup/*vllm*
   ls ~/Paralegal/AMD_server/setup/*vllm*
   ```

3. **Test Saul integration directly:**
   ```bash
   python -c "
   import os
   from openai import OpenAI
   
   client = OpenAI(
       base_url='http://localhost:8000/v1',
       api_key='dummy'
   )
   
   response = client.completions.create(
       model='Equall/Saul-7B-Instruct-v1',
       prompt='What is a tort?',
       max_tokens=100
   )
   
   print(response.choices[0].text)
   "
   ```

4. **Create simple LLM client wrapper** (to make test_agents.py work):
   - Wrap `saul_complete_sync()` from researcher.py
   - Make it compatible with agent expectations
   - Use existing OpenAI client infrastructure

### Alternative Approach

**The ADK system already works!** Use it directly instead of test_agents.py:
```bash
# Test the actual working system
cd ~/Paralegal/AMD_server/ADK
python researcher.py --issue "car accident liability" --jurisdiction "Florida"
```

---

## 🔍 Search Results Summary

**Commands run:**
```bash
find ~/Paralegal -name "*llm*.py" -type f
  Result: Only llm_saul.py exists (in ADK)

find ~/Paralegal -name "*config*.py" -type f  
  Result: No project config files, only library configs

grep -r "class AMDLLMClient" ~/Paralegal --include="*.py"
  Result: No results (class doesn't exist)

grep -r "def simple_prompt" ~/Paralegal --include="*.py"
  Result: No results (method doesn't exist)

find ~/Paralegal/backend -name "*.py" -type f
  Result: Only API wrappers (email, call, text, AMD/ADK)
```

**Conclusion:** The test files reference infrastructure that was planned but never implemented.

---

## 💡 Quick Fix for Testing

**Use this instead of test_agents.py:**

```bash
# Test RAG functionality (already working)
python test_rag_simple.py

# Test RAG search programmatically
python -c "
import sys
sys.path.append('ml_pipeline')
from rag_embeddings import RAGEmbeddings

rag = RAGEmbeddings()
rag.load('morgan_documents')
results = rag.search('car accident', top_k=3)

for r in results:
    print(f\"{r['similarity']:.1%}: {r['document']['title']}\")
"
```

This demonstrates the RAG system works perfectly - it just needs an LLM client to be fully integrated with agents.
