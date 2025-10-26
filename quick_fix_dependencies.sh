#!/bin/bash
# Quick fix for missing dependencies and model configuration

echo "========================================================================"
echo "QUICK FIX: Installing missing dependencies and checking vLLM model"
echo "========================================================================"
echo ""

cd /home/amd-knights/Paralegal || exit 1
source venv/bin/activate

# Install missing dependencies
echo "✅ Installing webdriver_manager..."
pip install -q webdriver-manager selenium

# Install aiohttp if not already installed
echo "✅ Installing aiohttp for async scraping..."
pip install -q aiohttp

# Check what model is actually running in vLLM
echo ""
echo "========================================================================"
echo "Checking vLLM server model..."
echo "========================================================================"
curl -s http://localhost:8000/v1/models | python3 -m json.tool

echo ""
echo "========================================================================"
echo "✅ Dependencies installed!"
echo "========================================================================"
echo ""
echo "Now run: ./test_complete_system.sh"
