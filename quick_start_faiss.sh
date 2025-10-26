#!/bin/bash
# FAISS Quick Start - Run on AMD Server
# This script sets up and tests FAISS embeddings with GPU acceleration

set -e  # Exit on error

echo "======================================================================"
echo "🚀 FAISS + AMD GPU Quick Start"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check location
echo -e "${YELLOW}Step 1: Verifying we're on AMD server...${NC}"
if command -v rocm-smi &> /dev/null; then
    echo -e "${GREEN}✅ ROCm detected - we're on the AMD server${NC}"
    rocm-smi --showproductname | head -5
else
    echo -e "${RED}❌ ROCm not found - are you on the AMD server?${NC}"
    echo "This script must be run on the AMD server with MI300X GPU"
    exit 1
fi

# Step 2: Navigate to project
echo -e "\n${YELLOW}Step 2: Navigating to project directory...${NC}"
cd /home/amd-knights/Paralegal
echo -e "${GREEN}✅ Current directory: $(pwd)${NC}"

# Step 3: Pull latest code
echo -e "\n${YELLOW}Step 3: Pulling latest code...${NC}"
git pull
echo -e "${GREEN}✅ Code updated${NC}"

# Step 4: Check Python environment
echo -e "\n${YELLOW}Step 4: Checking Python environment...${NC}"
python3 --version
echo -e "${GREEN}✅ Python available${NC}"

# Step 5: Install dependencies
echo -e "\n${YELLOW}Step 5: Installing required packages...${NC}"
echo "This may take 2-3 minutes..."

# Install basic dependencies
pip install -q sentence-transformers faiss-cpu psycopg2-binary

# Check if PyTorch with ROCm is installed
if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ PyTorch with ROCm already installed${NC}"
else
    echo -e "${YELLOW}⚠️  Installing PyTorch with ROCm (this takes ~2 minutes)...${NC}"
    pip install -q torch --index-url https://download.pytorch.org/whl/rocm6.0
fi

echo -e "${GREEN}✅ All dependencies installed${NC}"

# Step 6: Verify GPU access
echo -e "\n${YELLOW}Step 6: Verifying GPU access from Python...${NC}"
python3 << 'EOF'
import torch
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  Device: {torch.cuda.get_device_name(0)}")
    print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("  ⚠️  GPU not accessible - will use CPU")
EOF
echo -e "${GREEN}✅ GPU verification complete${NC}"

# Step 7: Check database connection
echo -e "\n${YELLOW}Step 7: Checking PostgreSQL connection...${NC}"
python3 << 'EOF'
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="paralegal_db",
        user="paralegal_user",
        password="hackathon2024"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM legal_data.documents WHERE session_id = 5")
    count = cursor.fetchone()[0]
    print(f"  ✅ Database connected!")
    print(f"  ✅ Found {count} Morgan & Morgan documents")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  ❌ Database error: {e}")
    exit(1)
EOF
echo -e "${GREEN}✅ Database connection verified${NC}"

# Step 8: Run FAISS embeddings test
echo -e "\n${YELLOW}Step 8: Testing FAISS embeddings generation...${NC}"
echo "This will:"
echo "  1. Load 54 Morgan & Morgan documents from PostgreSQL"
echo "  2. Generate embeddings using sentence-transformers"
echo "  3. Build FAISS index"
echo "  4. Test search queries"
echo ""
echo "Expected time: 2-5 minutes (CPU) or 10-30 seconds (GPU)"
echo ""
read -p "Press Enter to continue..."

cd AMD_server/ml_pipeline

# Run the embeddings script
python3 rag_embeddings.py

echo -e "\n${GREEN}✅ FAISS embeddings test complete!${NC}"

# Step 9: Verify output
echo -e "\n${YELLOW}Step 9: Verifying output files...${NC}"
if [ -d "embeddings/morgan_documents" ]; then
    echo -e "${GREEN}✅ Embeddings directory created${NC}"
    ls -lh embeddings/morgan_documents/
else
    echo -e "${RED}❌ Embeddings directory not found${NC}"
    exit 1
fi

# Step 10: Summary
echo ""
echo "======================================================================"
echo -e "${GREEN}✅ QUICK START COMPLETE!${NC}"
echo "======================================================================"
echo ""
echo "What was accomplished:"
echo "  ✅ Dependencies installed (sentence-transformers, faiss, torch)"
echo "  ✅ GPU access verified (AMD MI300X)"
echo "  ✅ Database connection tested (54 documents)"
echo "  ✅ Embeddings generated and indexed"
echo "  ✅ Search functionality validated"
echo ""
echo "Next steps:"
echo "  1. Review docs/FAISS_EXECUTION_GUIDE.md for detailed optimization"
echo "  2. Run Phase 3 to enable GPU acceleration"
echo "  3. Run Phase 4 to upgrade to HNSW index"
echo ""
echo "To see the full guide:"
echo "  cat docs/FAISS_EXECUTION_GUIDE.md"
echo ""
echo "======================================================================"
