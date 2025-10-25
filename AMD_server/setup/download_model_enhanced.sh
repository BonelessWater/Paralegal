#!/bin/bash
# Enhanced Hugging Face Model Downloader
# Supports ANY model from Hugging Face Hub
# Your teammates can use this to download their chosen legal model

echo "========================================="
echo "Hugging Face Model Downloader"
echo "Enhanced for Custom Model Support"
echo "========================================="

# Load environment variables if .env exists
if [ -f "../.env" ]; then
    echo "📝 Loading configuration from .env file..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Ensure we're in the right directory
MODEL_DIR="${MODELS_PATH:-$HOME/ai-legal-tender/models}"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

# Check for HF token
if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
    echo ""
    echo "⚠️  Warning: HUGGING_FACE_HUB_TOKEN not set"
    echo "   Some models may require authentication"
    echo "   Get your token from: https://huggingface.co/settings/tokens"
    echo ""
    read -p "Enter your Hugging Face token (or press Enter to continue): " HF_TOKEN
    if [ ! -z "$HF_TOKEN" ]; then
        export HUGGING_FACE_HUB_TOKEN=$HF_TOKEN
    fi
fi

echo ""
echo "========================================="
echo "Model Selection"
echo "========================================="
echo ""
echo "Choose an option:"
echo ""
echo "1. Use model from .env file (MODEL_NAME=${MODEL_NAME:-not set})"
echo "2. Enter custom Hugging Face model path"
echo "3. Select from recommended legal models"
echo "4. Select from general-purpose models (Llama, Mistral, etc.)"
echo ""
read -p "Enter choice (1-4): " CHOICE

case $CHOICE in
    1)
        if [ -z "$MODEL_NAME" ]; then
            echo "❌ MODEL_NAME not set in .env file"
            echo "   Please set MODEL_NAME in your .env file first"
            exit 1
        fi
        MODEL_PATH="$MODEL_NAME"
        FOLDER_NAME="${MODEL_FOLDER:-${MODEL_NAME##*/}}"
        echo "Using model from .env: $MODEL_PATH"
        ;;
    
    2)
        echo ""
        echo "Enter the Hugging Face model path"
        echo "Examples:"
        echo "  - law-ai/InLegalBERT"
        echo "  - nlpaueb/legal-bert-base-uncased"
        echo "  - saul-good-man/legal-llama-7b"
        echo "  - meta-llama/Meta-Llama-3-8B-Instruct"
        echo ""
        read -p "Model path: " CUSTOM_MODEL
        
        if [ -z "$CUSTOM_MODEL" ]; then
            echo "❌ No model path entered. Exiting."
            exit 1
        fi
        
        MODEL_PATH="$CUSTOM_MODEL"
        
        # Generate folder name from model path
        DEFAULT_FOLDER=$(echo "$CUSTOM_MODEL" | sed 's/\//-/g' | tr '[:upper:]' '[:lower:]')
        read -p "Local folder name [$DEFAULT_FOLDER]: " CUSTOM_FOLDER
        FOLDER_NAME="${CUSTOM_FOLDER:-$DEFAULT_FOLDER}"
        
        echo ""
        echo "✓ Will download: $MODEL_PATH"
        echo "✓ To folder: $FOLDER_NAME"
        ;;
    
    3)
        echo ""
        echo "Recommended Legal-Focused Models:"
        echo "1. nlpaueb/legal-bert-base-uncased (Legal BERT - 110M params)"
        echo "2. law-ai/InLegalBERT (Legal domain BERT - 110M params)"
        echo "3. pile-of-law/legalbert-large-1.7M-1 (Large Legal BERT)"
        echo "4. zlucia/legalbert (Another legal BERT variant)"
        echo ""
        read -p "Select legal model (1-4): " LEGAL_CHOICE
        
        case $LEGAL_CHOICE in
            1)
                MODEL_PATH="nlpaueb/legal-bert-base-uncased"
                FOLDER_NAME="legal-bert-base"
                ;;
            2)
                MODEL_PATH="law-ai/InLegalBERT"
                FOLDER_NAME="in-legal-bert"
                ;;
            3)
                MODEL_PATH="pile-of-law/legalbert-large-1.7M-1"
                FOLDER_NAME="legal-bert-large"
                ;;
            4)
                MODEL_PATH="zlucia/legalbert"
                FOLDER_NAME="legal-bert-zlucia"
                ;;
            *)
                echo "Invalid choice. Exiting."
                exit 1
                ;;
        esac
        ;;
    
    4)
        echo ""
        echo "General-Purpose Models (Strong Baseline):"
        echo "1. Llama 3 8B (40GB - RECOMMENDED for hackathon)"
        echo "2. Llama 3 70B (140GB - impressive but slow download)"
        echo "3. Mistral 7B (14GB - faster alternative)"
        echo "4. Phi-3 Mini (7GB - lightweight option)"
        echo ""
        read -p "Select model (1-4): " MODEL_CHOICE
        
        case $MODEL_CHOICE in
            1)
                MODEL_PATH="meta-llama/Meta-Llama-3-8B-Instruct"
                FOLDER_NAME="llama-3-8b"
                ;;
            2)
                MODEL_PATH="meta-llama/Meta-Llama-3-70B-Instruct"
                FOLDER_NAME="llama-3-70b"
                ;;
            3)
                MODEL_PATH="mistralai/Mistral-7B-Instruct-v0.2"
                FOLDER_NAME="mistral-7b"
                ;;
            4)
                MODEL_PATH="microsoft/Phi-3-mini-4k-instruct"
                FOLDER_NAME="phi-3-mini"
                ;;
            *)
                echo "Invalid choice. Exiting."
                exit 1
                ;;
        esac
        ;;
    
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Install huggingface-cli if not present
if ! command -v huggingface-cli &> /dev/null; then
    echo ""
    echo "Installing Hugging Face CLI..."
    pip install huggingface-hub[cli] --break-system-packages
fi

# Download the model
echo ""
echo "========================================="
echo "Starting Download"
echo "========================================="
echo ""
echo "Model:       $MODEL_PATH"
echo "Destination: $MODEL_DIR/$FOLDER_NAME"
echo ""
echo "⏳ This may take 5-60 minutes depending on model size..."
echo ""

# Check if folder already exists
if [ -d "$FOLDER_NAME" ]; then
    echo "⚠️  Folder $FOLDER_NAME already exists!"
    read -p "Overwrite? (y/N): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Cancelled. Exiting."
        exit 0
    fi
    rm -rf "$FOLDER_NAME"
fi

huggingface-cli download "$MODEL_PATH" \
    --local-dir "$FOLDER_NAME" \
    --local-dir-use-symlinks False

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Model Downloaded Successfully!"
    echo "========================================="
    echo ""
    echo "Model location: $MODEL_DIR/$FOLDER_NAME"
    echo ""
    echo "📝 NEXT STEPS FOR YOUR TEAMMATES:"
    echo ""
    echo "1. Update your .env file with:"
    echo "   MODEL_NAME=$MODEL_PATH"
    echo "   MODEL_FOLDER=$FOLDER_NAME"
    echo ""
    echo "2. Start vLLM server:"
    echo "   cd ../setup"
    echo "   ./start_vllm.sh"
    echo ""
    echo "3. Test the model:"
    echo "   ./test_vllm.sh"
    echo ""
    
    # Offer to update start_vllm.sh automatically
    echo ""
    read -p "Auto-update start_vllm.sh with this model? (Y/n): " UPDATE_SCRIPT
    if [ "$UPDATE_SCRIPT" != "n" ] && [ "$UPDATE_SCRIPT" != "N" ]; then
        if [ -f "./start_vllm.sh" ]; then
            sed -i.bak "s|--model /models/.*|--model /models/$FOLDER_NAME \\\\|" ./start_vllm.sh
            echo "✅ start_vllm.sh updated!"
        fi
    fi
    
else
    echo ""
    echo "========================================="
    echo "❌ Download Failed"
    echo "========================================="
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Gated/Private Model Access:"
    echo "   - Visit: https://huggingface.co/$MODEL_PATH"
    echo "   - Click 'Accept' on the model license/terms"
    echo "   - Wait a few minutes for access approval"
    echo ""
    echo "2. Authentication Required:"
    echo "   - Get token from: https://huggingface.co/settings/tokens"
    echo "   - Set in .env: HUGGING_FACE_HUB_TOKEN=your_token"
    echo "   Or run: huggingface-cli login"
    echo ""
    echo "3. Network Issues:"
    echo "   - Check internet connection"
    echo "   - Try again in a few minutes"
    echo ""
    echo "4. Model Not Found:"
    echo "   - Double-check model path at: https://huggingface.co/models"
    echo "   - Ensure spelling is correct"
    echo ""
fi
