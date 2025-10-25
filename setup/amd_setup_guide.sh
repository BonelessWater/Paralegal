#!/bin/bash
# AMD MI300X Setup Script for AI Legal Tender Hackathon
# This script sets up ROCm, vLLM for Hugging Face models, and OCR

echo "========================================="
echo "AMD MI300X Setup - AI Legal Tender"
echo "========================================="

# STEP 1: Verify ROCm and GPU
echo -e "\n[Step 1] Verifying AMD GPU and ROCm installation..."
echo "Running rocm-smi to check GPU status:"
rocm-smi

echo -e "\nRunning rocminfo to get detailed GPU info:"
rocminfo | grep -E "Name|Memory"

# Document these specs for your presentation!
echo -e "\n💡 TIP: Screenshot the above output for your demo deck!"

# STEP 2: Check Docker installation
echo -e "\n[Step 2] Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    docker --version
else
    echo "❌ Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️  Log out and back in for Docker permissions to take effect"
fi

# STEP 3: Pull vLLM Docker Image for ROCm
echo -e "\n[Step 3] Pulling AMD vLLM Docker image..."
echo "This is pre-configured with ROCm - saves 2-3 hours!"
docker pull rocm/vllm:latest

# STEP 4: Create directory structure
echo -e "\n[Step 4] Creating project directories..."
mkdir -p ~/ai-legal-tender/{models,data,logs,scripts}
cd ~/ai-legal-tender

echo "✅ Directory structure created"
echo "   - models/  : For storing downloaded Hugging Face models"
echo "   - data/    : For mock legal communications"
echo "   - logs/    : For system logs"
echo "   - scripts/ : For Python scripts"

# STEP 5: Create Hugging Face token file
echo -e "\n[Step 5] Hugging Face Setup"
echo "You'll need a Hugging Face token to download models like Llama 3"
echo "Get your token from: https://huggingface.co/settings/tokens"
echo ""
read -p "Enter your Hugging Face token (or press Enter to skip): " HF_TOKEN

if [ ! -z "$HF_TOKEN" ]; then
    echo "export HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" >> ~/.bashrc
    echo "✅ Token saved to ~/.bashrc"
else
    echo "⚠️  Skipped - you can set this later"
fi

echo -e "\n========================================="
echo "✅ Basic setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Run the vLLM container: ./start_vllm.sh"
echo "2. Set up OCR model: ./setup_ocr.sh"
echo "3. Download Hugging Face model: ./download_model.sh"
