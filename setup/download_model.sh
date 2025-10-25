#!/bin/bash
# Download Hugging Face models for AMD deployment

echo "========================================="
echo "Hugging Face Model Downloader"
echo "========================================="

# Ensure we're in the right directory
cd ~/ai-legal-tender/models

# Check for HF token
if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
    echo "⚠️  Warning: HUGGING_FACE_HUB_TOKEN not set"
    echo "Some models may require authentication"
    echo ""
    read -p "Enter your Hugging Face token (or press Enter to continue): " HF_TOKEN
    if [ ! -z "$HF_TOKEN" ]; then
        export HUGGING_FACE_HUB_TOKEN=$HF_TOKEN
    fi
fi

echo ""
echo "Select model to download:"
echo "1. Llama 3 8B (40GB - RECOMMENDED for hackathon)"
echo "2. Llama 3 70B (140GB - impressive but slow download)"
echo "3. Mistral 7B (14GB - faster alternative)"
echo "4. Phi-3 Mini (7GB - lightweight option)"
echo ""
read -p "Enter choice (1-4): " MODEL_CHOICE

case $MODEL_CHOICE in
    1)
        MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
        FOLDER_NAME="llama-3-8b"
        echo "Downloading Llama 3 8B..."
        ;;
    2)
        MODEL_NAME="meta-llama/Meta-Llama-3-70B-Instruct"
        FOLDER_NAME="llama-3-70b"
        echo "Downloading Llama 3 70B (this will take a while)..."
        ;;
    3)
        MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2"
        FOLDER_NAME="mistral-7b"
        echo "Downloading Mistral 7B..."
        ;;
    4)
        MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"
        FOLDER_NAME="phi-3-mini"
        echo "Downloading Phi-3 Mini..."
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Install huggingface-cli if not present
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing Hugging Face CLI..."
    pip install huggingface-hub[cli] --break-system-packages
fi

# Download the model
echo ""
echo "Starting download to: ~/ai-legal-tender/models/$FOLDER_NAME"
echo "This may take 5-30 minutes depending on model size and network..."
echo ""

huggingface-cli download $MODEL_NAME \
    --local-dir $FOLDER_NAME \
    --local-dir-use-symlinks False

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Model downloaded successfully!"
    echo ""
    echo "Model location: ~/ai-legal-tender/models/$FOLDER_NAME"
    echo ""
    echo "Next step: Start vLLM with this model"
    echo "   Edit start_vllm.sh and set: --model /models/$FOLDER_NAME"
    echo "   Then run: ./start_vllm.sh"
else
    echo ""
    echo "❌ Download failed. Common issues:"
    echo "   1. Need Hugging Face token for Llama models (get from huggingface.co/settings/tokens)"
    echo "   2. Need to accept Llama license at: https://huggingface.co/meta-llama"
    echo "   3. Network issues - try again"
fi
