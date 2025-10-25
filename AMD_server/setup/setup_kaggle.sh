#!/bin/bash

# =============================================================================
# Quick Setup for Kaggle Dataset Download on AMD Server
# =============================================================================

echo "🚀 Setting up Kaggle Dataset Downloader"
echo ""

# Install dependencies
echo "[1/3] Installing Python dependencies..."
pip install kaggle pandas psycopg2-binary

# Setup Kaggle credentials
echo ""
echo "[2/3] Setting up Kaggle API credentials..."
echo ""
echo "Please follow these steps:"
echo "  1. Go to https://www.kaggle.com/settings"
echo "  2. Scroll to 'API' section"
echo "  3. Click 'Create New API Token'"
echo "  4. Download kaggle.json"
echo "  5. Upload it to this server:"
echo ""
echo "     From your local machine, run:"
echo "     scp ~/Downloads/kaggle.json amd-knights@134.199.202.8:~/.kaggle/"
echo ""
read -p "Press Enter once you've uploaded kaggle.json..."

# Create kaggle directory and set permissions
mkdir -p ~/.kaggle
if [ -f ~/.kaggle/kaggle.json ]; then
    chmod 600 ~/.kaggle/kaggle.json
    echo "✓ Kaggle credentials configured"
else
    echo "⚠ Warning: kaggle.json not found at ~/.kaggle/kaggle.json"
    echo "  You'll need to upload it before running the download script"
fi

# Test database connection
echo ""
echo "[3/3] Testing database connection..."
cd ~/Paralegal/AMD_server/scraper
python test_database.py

echo ""
echo "============================================"
echo "✓ Setup Complete!"
echo "============================================"
echo ""
echo "To download all 13 Kaggle datasets, run:"
echo "  cd ~/Paralegal/AMD_server/scraper"
echo "  python load_kaggle_datasets.py"
echo ""
echo "For faster downloads on supercomputer (16 parallel workers):"
echo "  KAGGLE_WORKERS=16 python load_kaggle_datasets.py"
echo ""
echo "This will download ~15-25 GB of data."
echo "Estimated time with 8 workers: 5-10 minutes"
echo "Estimated time with 16 workers: 3-7 minutes"
echo ""
