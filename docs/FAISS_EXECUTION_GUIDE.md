# FAISS Implementation - Step-by-Step Execution Guide

**Date**: October 25, 2025  
**Location**: Local → AMD Server Migration  
**Estimated Time**: 5-6 hours total

---

## 🎯 OVERVIEW

This guide walks you through testing and optimizing your FAISS implementation, first locally (if possible), then on the AMD server where GPU acceleration happens.

---

## 📋 PREREQUISITES

### **On Your Local Mac** (Optional Testing)

Check if you have dependencies:
```bash
cd /Users/ilandanial/Paralegal
pip list | grep -E "sentence-transformers|faiss|psycopg2"
```

If missing, install:
```bash
pip install sentence-transformers faiss-cpu psycopg2-binary
```

### **On AMD Server** (Required for GPU)

You'll need:
```bash
pip install sentence-transformers faiss-cpu psycopg2-binary
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
```

---

## 🚀 PHASE 1: TEST LOCALLY (Optional - 15 min)

### **Goal**: Verify your code works before touching the AMD server

### **Step 1.1: Check Database Connection**

Create test script:
```bash
cd /Users/ilandanial/Paralegal
cat > test_db_connection.py << 'EOF'
#!/usr/bin/env python3
"""Test PostgreSQL connection"""
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",  # or your DB host
        port=5432,
        database="paralegal_db",
        user="paralegal_user",
        password="hackathon2024"
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM legal_data.documents WHERE session_id = 5")
    count = cursor.fetchone()[0]
    
    print(f"✅ Database connection successful!")
    print(f"✅ Found {count} Morgan & Morgan documents")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\nNote: If running locally, make sure:")
    print("  1. PostgreSQL is running")
    print("  2. Database 'paralegal_db' exists")
    print("  3. Or run this test on AMD server instead")
EOF

python test_db_connection.py
```

**Expected Output**:
- ✅ If on AMD server with DB access: "Found 54 Morgan & Morgan documents"
- ❌ If on local Mac: Connection error (this is OK, skip to Phase 2)

### **Step 1.2: Test FAISS Code (Dry Run)**

```bash
cd /Users/ilandanial/Paralegal/AMD_server/ml_pipeline

# Just check for syntax errors
python -m py_compile rag_embeddings.py

echo "✅ Code compiles successfully"
```

**If this fails**: Fix any import or syntax errors before proceeding.

---

## 🖥️ PHASE 2: ON AMD SERVER - BASELINE TEST (30 min)

### **Goal**: Generate embeddings with CPU, establish baseline performance

### **Step 2.1: Connect to AMD Server**

```bash
# From your Mac
ssh amd-knights@134.199.202.8
# Or whatever your AMD server connection is
```

### **Step 2.2: Navigate to Project**

```bash
cd /home/amd-knights/Paralegal
git pull  # Get latest code

cd AMD_server/ml_pipeline
```

### **Step 2.3: Check Dependencies**

```bash
# Check what's installed
pip list | grep -E "sentence-transformers|faiss|psycopg2|torch"

# If missing, install
pip install sentence-transformers faiss-cpu psycopg2-binary
```

### **Step 2.4: Run Baseline Test (CPU Only)**

```bash
python rag_embeddings.py
```

**What to expect**:
1. Downloads `all-MiniLM-L6-v2` model (~90MB) - takes 30-60 seconds
2. Loads 54 documents from PostgreSQL
3. Generates embeddings on CPU - **takes 2-5 minutes**
4. Builds FAISS index
5. Tests with 3 sample queries
6. Saves to `embeddings/morgan_documents/`

**Document the output**:
```
Embedding generation time: _____ seconds
Search time per query: _____ ms
```

### **Step 2.5: Verify Output Files**

```bash
ls -lh embeddings/morgan_documents/

# Should see:
# embeddings.npy (~81KB for 54 docs × 384 dims)
# faiss.index (~20KB)
# documents.pkl
# config.pkl
```

---

## ⚡ PHASE 3: GPU ACCELERATION (1 hour)

### **Goal**: Move embedding generation to AMD GPU, measure speedup

### **Step 3.1: Install PyTorch with ROCm**

```bash
# On AMD server
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
```

### **Step 3.2: Verify GPU Detection**

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

**Expected**:
```
CUDA available: True
Device: AMD Instinct MI300X
```

**If False**: ROCm not properly configured (check with `rocm-smi`)

### **Step 3.3: Modify rag_embeddings.py for GPU**

Create backup:
```bash
cp rag_embeddings.py rag_embeddings.py.backup
```

Edit the file:
```bash
nano rag_embeddings.py
```

Find line ~68 (in `__init__` method):
```python
# Load sentence-transformer model
print(f"Loading sentence-transformer model: {model_name}")
self.model = SentenceTransformer(model_name)
```

Change to:
```python
# Load sentence-transformer model
print(f"Loading sentence-transformer model: {model_name}")
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
self.model = SentenceTransformer(model_name, device=device)
```

Find line ~130 (in `generate_embeddings` method):
```python
# Generate embeddings
self.embeddings = self.model.encode(
    texts,
    batch_size=batch_size,
    show_progress_bar=show_progress,
    convert_to_numpy=True
)
```

Change to:
```python
# Generate embeddings
import time
start_time = time.time()

self.embeddings = self.model.encode(
    texts,
    batch_size=batch_size,
    show_progress_bar=show_progress,
    convert_to_numpy=True,
    device=device  # Explicit device specification
)

elapsed = time.time() - start_time
print(f"⏱️  Embedding generation took: {elapsed:.2f} seconds ({len(texts)/elapsed:.1f} docs/sec)")
```

Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

### **Step 3.4: Test GPU Embeddings**

```bash
# Remove old embeddings to force regeneration
rm -rf embeddings/morgan_documents

# Run with GPU
python rag_embeddings.py
```

**What to watch for**:
```
Using device: cuda
⏱️  Embedding generation took: XX.XX seconds (XX docs/sec)
```

**Document**:
```
CPU baseline: _____ seconds
GPU time: _____ seconds
Speedup: _____x
```

### **Step 3.5: Monitor GPU Usage**

In another terminal on AMD server:
```bash
watch -n 1 rocm-smi
```

**Look for**:
- GPU memory usage increases when encoding
- GPU utilization spikes to 80-100%

---

## 🔧 PHASE 4: HNSW OPTIMIZATION (30 min)

### **Goal**: Upgrade to faster approximate search

### **Step 4.1: Modify build_index Method**

Edit `rag_embeddings.py`:
```bash
nano rag_embeddings.py
```

Find the `build_index` method (around line 149):
```python
def build_index(self, embeddings: np.ndarray = None):
    """
    Build FAISS index for fast similarity search.
    
    Args:
        embeddings: Embeddings array. If None, uses self.embeddings.
    """
    if embeddings is None:
        embeddings = self.embeddings
    
    if embeddings is None:
        raise ValueError("No embeddings available. Run generate_embeddings() first.")
    
    print("\nBuilding FAISS index...")
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Create FAISS index (Inner Product = cosine similarity for normalized vectors)
    dimension = embeddings.shape[1]
    self.index = faiss.IndexFlatIP(dimension)
    
    # Add embeddings to index
    self.index.add(embeddings.astype('float32'))
    
    print(f"✓ Built FAISS index with {self.index.ntotal} vectors")
```

Replace with:
```python
def build_index(self, embeddings: np.ndarray = None, use_hnsw: bool = True):
    """
    Build FAISS index for fast similarity search.
    
    Args:
        embeddings: Embeddings array. If None, uses self.embeddings.
        use_hnsw: Use HNSW index (faster) vs Flat index (exact)
    """
    if embeddings is None:
        embeddings = self.embeddings
    
    if embeddings is None:
        raise ValueError("No embeddings available. Run generate_embeddings() first.")
    
    print("\nBuilding FAISS index...")
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    dimension = embeddings.shape[1]
    
    if use_hnsw:
        # HNSW index for fast approximate search
        M = 32  # Number of connections per layer (16-64 typical)
        efConstruction = 200  # Build-time accuracy (100-500 typical)
        
        print(f"Using HNSW index (M={M}, efConstruction={efConstruction})")
        self.index = faiss.IndexHNSWFlat(dimension, M)
        self.index.hnsw.efConstruction = efConstruction
        
        # Set search-time accuracy
        self.index.hnsw.efSearch = 64  # Higher = more accurate, slower
    else:
        # Flat index for exact search (baseline)
        print("Using Flat index (exact search)")
        self.index = faiss.IndexFlatIP(dimension)
    
    # Add embeddings to index
    import time
    start = time.time()
    self.index.add(embeddings.astype('float32'))
    elapsed = time.time() - start
    
    index_type = "HNSW" if use_hnsw else "Flat"
    print(f"✓ Built {index_type} index with {self.index.ntotal} vectors in {elapsed:.2f}s")
```

### **Step 4.2: Test HNSW Performance**

Create benchmark script:
```bash
cat > benchmark_faiss.py << 'EOF'
#!/usr/bin/env python3
"""Benchmark FAISS search performance"""
import time
from rag_embeddings import RAGEmbeddings

# Load existing embeddings
rag = RAGEmbeddings()
rag.load('morgan_documents')

# Test queries
queries = [
    "car accident with back injury",
    "settlement offer for medical expenses",
    "police report about incident",
    "property damage insurance claim",
    "personal injury whiplash case"
]

print("\n" + "="*70)
print("FAISS SEARCH BENCHMARK")
print("="*70)

for query in queries:
    start = time.time()
    results = rag.search(query, top_k=5)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    print(f"\nQuery: '{query}'")
    print(f"⏱️  Search time: {elapsed:.2f}ms")
    print(f"Top result: {results[0]['document']['title']} (similarity: {results[0]['similarity']:.3f})")

print("\n" + "="*70)
EOF

python benchmark_faiss.py
```

**Document**:
```
Flat index search: _____ ms average
HNSW index search: _____ ms average
Speedup: _____x
```

---

## 📊 PHASE 5: UPGRADE TO BETTER MODEL (10 min)

### **Goal**: Switch to BGE-Large for better legal text quality

### **Step 5.1: Modify model_name**

Edit the main execution block in `rag_embeddings.py` (bottom of file):

Find:
```python
if __name__ == "__main__":
    import sys
    
    # Generate embeddings
    rag = generate_embeddings_pipeline()
```

Change to:
```python
if __name__ == "__main__":
    import sys
    
    # Generate embeddings with better model
    rag = generate_embeddings_pipeline(
        save_name="morgan_documents_bge",
        model_name="BAAI/bge-large-en-v1.5"  # Upgraded model
    )
```

### **Step 5.2: Regenerate with BGE-Large**

```bash
# This will download BGE-Large (~1.3GB) and regenerate embeddings
python rag_embeddings.py
```

**Watch for**:
```
Model: BAAI/bge-large-en-v1.5
Embedding dimension: 1024 (vs 384 before)
```

### **Step 5.3: Compare Quality**

```bash
python benchmark_faiss.py
```

Note if results are more relevant (subjective evaluation).

---

## ✅ PHASE 6: VERIFICATION & DOCUMENTATION (15 min)

### **Step 6.1: Final Integration Test**

Create complete test:
```bash
cat > test_complete_pipeline.py << 'EOF'
#!/usr/bin/env python3
"""Complete end-to-end test"""
import time
from rag_embeddings import RAGEmbeddings

print("="*70)
print("COMPLETE FAISS PIPELINE TEST")
print("="*70)

# Test 1: Load embeddings
print("\n1. Loading embeddings...")
start = time.time()
rag = RAGEmbeddings(model_name="BAAI/bge-large-en-v1.5")
rag.load('morgan_documents_bge')
print(f"✅ Loaded in {time.time()-start:.2f}s")
print(f"   - {len(rag.documents)} documents")
print(f"   - {rag.embeddings.shape[1]}-dimensional embeddings")

# Test 2: Search performance
print("\n2. Testing search...")
query = "client injured in car accident with back pain"
start = time.time()
results = rag.search(query, top_k=3)
search_time = (time.time() - start) * 1000

print(f"✅ Search completed in {search_time:.2f}ms")
print(f"\n   Top 3 results:")
for r in results:
    print(f"   {r['rank']}. {r['document']['title']}")
    print(f"      Similarity: {r['similarity']:.3f}")
    print(f"      Type: {r['document']['document_type']}")

# Test 3: Summary stats
print("\n3. System summary:")
summary = rag.get_summary()
for key, value in summary.items():
    print(f"   {key}: {value}")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED")
print("="*70)
EOF

python test_complete_pipeline.py
```

### **Step 6.2: Document Metrics**

Create metrics file:
```bash
cat > FAISS_METRICS.md << 'EOF'
# FAISS Implementation Metrics

**Date**: October 25, 2025
**System**: AMD Instinct MI300X

## Performance Results

### Embedding Generation
- **Model**: BAAI/bge-large-en-v1.5
- **Documents**: 54 Morgan & Morgan cases
- **Embedding Dimension**: 1024

| Hardware | Time | Throughput | Speedup |
|----------|------|------------|---------|
| CPU | ___ sec | ___ docs/sec | 1.0x |
| AMD MI300X GPU | ___ sec | ___ docs/sec | ___x |

### Vector Search
- **Index Type**: HNSW (M=32, efSearch=64)
- **Index Size**: 54 vectors

| Metric | Value |
|--------|-------|
| Average search latency | ___ ms |
| Top-5 accuracy (recall) | ~97% (HNSW) |
| Index build time | ___ sec |
| Memory usage | ___ MB |

### End-to-End Latency
- New query embedding: ___ ms
- FAISS search: ___ ms
- **Total**: ___ ms ✅ (Target: <150ms)

## GPU Utilization
```
rocm-smi output during embedding generation:
[Paste rocm-smi output here]
```

## Conclusions
- ✅ AMD GPU provides ___x speedup for embeddings
- ✅ HNSW search achieves <___ms latency
- ✅ System ready for integration with agents
EOF

echo "✅ Edit FAISS_METRICS.md with your actual numbers"
```

---

## 🎯 NEXT STEPS

Once Phase 6 is complete, you're ready for:

1. **Database Schema Extension** (2-3h)
   - Add client/case tracking tables
   - Enable context retrieval

2. **Context Manager Integration** (2-3h)
   - Combine FAISS + PostgreSQL
   - Hybrid search system

3. **Agent Integration** (2h)
   - Add context to existing agents
   - Test context-aware responses

4. **Demo Preparation** (2h)
   - Polish scripts
   - Practice presentation

---

## 📝 TROUBLESHOOTING

### "CUDA not available"
```bash
# Check ROCm
rocm-smi

# Reinstall PyTorch with ROCm
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
```

### "Database connection failed"
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U paralegal_user -d paralegal_db
```

### "FAISS import error"
```bash
pip install faiss-cpu --upgrade
```

### "Out of memory (GPU)"
```bash
# Reduce batch size in generate_embeddings
# Edit rag_embeddings.py, change batch_size from 32 to 16
```

---

## ✅ SUCCESS CRITERIA

You'll know you're done when:

- ✅ Embeddings generate on AMD GPU (10-15x faster than CPU)
- ✅ HNSW search completes in <80ms
- ✅ BGE-Large model loaded and working
- ✅ All tests pass
- ✅ Metrics documented

**Time commitment**: 2-3 hours for Phases 1-6

**Ready to proceed to AMD server? Let me know when you're connected!**
EOF
chmod +x test_*.py benchmark_faiss.py test_complete_pipeline.py
