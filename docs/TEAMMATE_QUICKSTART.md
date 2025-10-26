# Quick Start Guide for Teammates

**Last Updated:** October 25, 2025  
**Server:** gpu-mi300x1-192gb-contracted-atl1-28 (AMD MI300X)

---

## 🔐 Access the Server

```bash
ssh amd-knights@134.199.202.8
# Password: [provided separately]
```

---

## 📍 File Locations

### Main Project Directory
```bash
/home/amd-knights/Paralegal
```

### Key Test Scripts
```bash
# Complete RAG + LLM pipeline test
/home/amd-knights/Paralegal/AMD_server/test_complete_system.py

# Simple RAG test (no LLM)
/home/amd-knights/Paralegal/AMD_server/test_rag_simple.py

# FAISS performance benchmark
/home/amd-knights/Paralegal/AMD_server/ml_pipeline/benchmark_faiss.py
```

### RAG System Components
```bash
# RAG embeddings module
/home/amd-knights/Paralegal/AMD_server/ml_pipeline/rag_embeddings.py

# Embeddings data
/home/amd-knights/Paralegal/AMD_server/ml_pipeline/embeddings/morgan_documents/
  ├── embeddings.npy        # 39 × 384 embedding vectors
  ├── faiss.index           # HNSW search index
  ├── documents.pkl         # Document metadata
  └── config.pkl            # Configuration
```

### Legal Researcher Agent
```bash
# RAG-enhanced legal researcher agent
/home/amd-knights/Paralegal/AMD_server/agents/legal_researcher_agent.py

# Agent test suite
/home/amd-knights/Paralegal/AMD_server/test_agents.py
```

---

## 🚀 Quick Start Commands

### 1. Activate Python Environment
```bash
cd ~/Paralegal
source venv/bin/activate
```

### 2. Test the Complete RAG + LLM Pipeline
```bash
cd ~/Paralegal/AMD_server
python test_complete_system.py
```

**Expected output:**
- ✅ RAG finds 3 similar cases
- ✅ LLM generates analysis based on those cases
- ✅ ~10-15 seconds total runtime

### 3. Test RAG Only (No LLM)
```bash
cd ~/Paralegal/AMD_server
python test_rag_simple.py
```

### 4. Benchmark FAISS Performance
```bash
cd ~/Paralegal/AMD_server/ml_pipeline
python benchmark_faiss.py
```

---

## 🔧 System Status Check

### Check if vLLM Server is Running
```bash
curl http://localhost:8000/v1/models
```

**Expected response:**
```json
{"object":"list","data":[{"id":"Equall/Saul-7B-Instruct-v1",...}]}
```

### Check Docker Containers
```bash
docker ps | grep vllm
```

**Expected:**
```
vllm-optimized ... Up ... 0.0.0.0:8000->8000/tcp
```

### Check Database
```bash
psql -U paralegal_user -d paralegal_db -c "SELECT COUNT(*) FROM legal_documents;"
```

**Expected:** 39 rows

---

## 📝 Using the RAG System in Your Code

### Python Example
```python
import sys
sys.path.append('/home/amd-knights/Paralegal/AMD_server/ml_pipeline')
from rag_embeddings import RAGEmbeddings

# Initialize RAG
rag = RAGEmbeddings()
rag.load('morgan_documents')

# Search for similar cases
results = rag.search('car accident back injury', top_k=5)

# Use results
for r in results:
    print(f"Similarity: {r['similarity']:.1%}")
    print(f"Title: {r['document']['title']}")
    print(f"Text: {r['document']['full_text'][:200]}...")
```

### With LLM Integration
```python
from openai import OpenAI

# Initialize LLM client
client = OpenAI(
    base_url='http://localhost:8000/v1',
    api_key='dummy'
)

# Build context from RAG results
context = "\n\n".join([r['document']['full_text'][:500] for r in results])

# Get LLM analysis
response = client.completions.create(
    model='Equall/Saul-7B-Instruct-v1',
    prompt=f"Based on these cases:\n{context}\n\nQuestion: Your legal question here?",
    max_tokens=300,
    temperature=0.3
)

print(response.choices[0].text)
```

---

## 🗂️ Database Access

### Connection Details (from .env)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paralegal_db
DB_USER=paralegal_user
DB_PASSWORD=hackathon2024
```

### Connect via psql
```bash
psql -U paralegal_user -d paralegal_db
```

### Python Connection
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="paralegal_db",
    user="paralegal_user",
    password="hackathon2024"
)
```

---

## 🔍 Useful Debugging Commands

### Check GPU Status
```bash
rocm-smi
```

### Check Python Packages
```bash
pip list | grep -E "faiss|sentence-transformers|openai|torch"
```

### View Recent Logs
```bash
docker logs vllm-optimized --tail 50
```

### Check Disk Space
```bash
df -h
```

### Check Memory Usage
```bash
free -h
```

---

## 📚 Documentation

### Key Documentation Files
```bash
# Server status and configuration
/home/amd-knights/Paralegal/docs/SERVER_STATUS.md

# Complete achievement summary
/home/amd-knights/Paralegal/docs/RAG_INTEGRATION_SUMMARY.md

# Repository analysis
/home/amd-knights/Paralegal/docs/REPO_ANALYSIS_AND_STATUS.md

# Database schema documentation
/home/amd-knights/Paralegal/docs/COMPLETE_DATABASE_SCHEMA.md
```

### View Documentation
```bash
cd ~/Paralegal/docs
cat SERVER_STATUS.md
```

---

## ⚠️ Important Notes

### Environment Variables
The following are already set in `.env`:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `HF_HOME=/home/amd-knights/Paralegal/.cache/huggingface`

Optional (have defaults):
- `SAUL_BASE_URL=http://localhost:8000/v1`
- `SAUL_MODEL=Equall/Saul-7B-Instruct-v1`
- `SAUL_API_KEY=dummy`

### GPU Access
The AMD MI300X GPU is shared. Monitor usage with:
```bash
watch -n 1 rocm-smi
```

### vLLM Server
- **Running in Docker** (container: vllm-optimized)
- **Port:** 8000
- **Model:** Saul-7B (legal-specific)
- **Auto-restarts** if container fails

If you need to restart:
```bash
docker restart vllm-optimized
```

---

## 🎯 Common Tasks

### Add New Documents to RAG
```python
# 1. Add documents to database (PostgreSQL)
# 2. Regenerate embeddings:
from ml_pipeline.rag_embeddings import RAGEmbeddings
rag = RAGEmbeddings()
rag.generate_embeddings_pipeline()  # Uses localhost DB
```

### Test Different Search Queries
```python
queries = [
    "car accident settlement",
    "slip and fall liability", 
    "medical malpractice",
    "workers compensation"
]

for q in queries:
    results = rag.search(q, top_k=3)
    print(f"\nQuery: {q}")
    for r in results:
        print(f"  {r['similarity']:.1%}: {r['document']['title']}")
```

### Adjust LLM Temperature
```python
# Lower = more focused, higher = more creative
response = client.completions.create(
    model='Equall/Saul-7B-Instruct-v1',
    prompt=prompt,
    temperature=0.1,  # Very focused (legal analysis)
    # temperature=0.5,  # Balanced
    # temperature=0.9,  # Creative
    max_tokens=300
)
```

---

## 🆘 Troubleshooting

### Issue: "Module not found: rag_embeddings"
**Solution:**
```bash
cd ~/Paralegal/AMD_server
python  # Then in Python:
import sys
sys.path.append('ml_pipeline')
from rag_embeddings import RAGEmbeddings
```

### Issue: "Connection refused to localhost:8000"
**Solution:**
```bash
# Check if vLLM is running
docker ps | grep vllm

# If not, restart it
docker restart vllm-optimized

# Wait 30 seconds, then test
curl http://localhost:8000/v1/models
```

### Issue: "Database connection failed"
**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U paralegal_user -d paralegal_db -c "SELECT 1;"
```

### Issue: "CUDA out of memory"
**Solution:**
```bash
# Check GPU memory
rocm-smi

# The vLLM server uses 60% of GPU memory (configured)
# RAG embeddings use the remaining 40%
# If issues persist, restart the Python process
```

---

## 📞 Need Help?

1. **Check documentation:** `~/Paralegal/docs/`
2. **View recent commits:** `git log --oneline -10`
3. **Check system status:** Run the test scripts
4. **Server issues:** Check Docker logs: `docker logs vllm-optimized`

---

## ✨ Quick Reference Card

```bash
# Navigate to project
cd ~/Paralegal/AMD_server

# Activate environment
source ../venv/bin/activate

# Test complete system
python test_complete_system.py

# Test RAG only
python test_rag_simple.py

# Check vLLM
curl http://localhost:8000/v1/models

# Check database
psql -U paralegal_user -d paralegal_db
```

**That's it! You're ready to use the RAG + LLM system! 🚀**
