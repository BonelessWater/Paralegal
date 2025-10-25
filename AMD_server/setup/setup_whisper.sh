#!/bin/bash
#
# Setup Local Whisper on AMD MI300X with ROCm
#
# This script installs all dependencies needed for GPU-accelerated 
# audio transcription using Whisper on AMD hardware.
#
# Run this on your AMD server:
#   chmod +x setup_whisper.sh
#   ./setup_whisper.sh
#

set -e  # Exit on error

echo "============================================================="
echo "LOCAL WHISPER SETUP - AMD MI300X + ROCm"
echo "============================================================="

# Check if running on AMD server
echo ""
echo "Checking system..."
if command -v rocm-smi &> /dev/null; then
    echo "✓ ROCm detected"
    rocm-smi --showproductname || true
else
    echo "⚠️  ROCm not detected. This script is for AMD GPUs."
    echo "   Install ROCm first: https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html"
fi

# Check Python version
echo ""
echo "Checking Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment (optional but recommended)
echo ""
read -p "Create virtual environment? (recommended) [y/N]: " create_venv

if [[ "$create_venv" =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install ROCm-compatible PyTorch
echo ""
echo "============================================================="
echo "INSTALLING PYTORCH FOR ROCm"
echo "============================================================="
echo ""
echo "This will install PyTorch optimized for AMD GPUs..."
echo ""

# Check ROCm version
if command -v rocm-smi &> /dev/null; then
    rocm_version=$(cat /opt/rocm/.info/version 2>/dev/null || echo "unknown")
    echo "Detected ROCm version: $rocm_version"
fi

# Install PyTorch for ROCm
# Using ROCm 6.0 as it's most compatible with MI300X
echo ""
echo "Installing PyTorch with ROCm support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

# Verify PyTorch installation
echo ""
echo "Verifying PyTorch + ROCm..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU device: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('⚠️  GPU not detected. Check ROCm installation.')
"

# Install HuggingFace Transformers
echo ""
echo "============================================================="
echo "INSTALLING TRANSFORMERS + WHISPER DEPENDENCIES"
echo "============================================================="
echo ""

pip install transformers>=4.30.0
pip install accelerate>=0.20.0
pip install librosa
pip install soundfile
pip install datasets

# Install optional dependencies for faster inference
echo ""
echo "Installing optimizations..."
pip install optimum
pip install flash-attn --no-build-isolation 2>/dev/null || echo "⚠️  flash-attn failed (optional, skipping)"

# Install other ML pipeline dependencies
echo ""
echo "Installing ML pipeline dependencies..."
pip install psycopg2-binary
pip install pandas
pip install numpy
pip install python-dotenv
pip install sentence-transformers
pip install faiss-cpu

# Download Whisper model (optional - will download on first use)
echo ""
read -p "Pre-download Whisper model? (saves time later) [y/N]: " download_model

if [[ "$download_model" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Select model size:"
    echo "  1) tiny (39M params, ~1GB VRAM, fastest)"
    echo "  2) base (74M params, ~1.5GB VRAM, fast)"
    echo "  3) small (244M params, ~2GB VRAM, balanced)"
    echo "  4) medium (769M params, ~5GB VRAM, good)"
    echo "  5) large-v3 (1550M params, ~10GB VRAM, best) [RECOMMENDED]"
    echo ""
    read -p "Choice [5]: " model_choice
    model_choice=${model_choice:-5}
    
    case $model_choice in
        1) model_name="tiny" ;;
        2) model_name="base" ;;
        3) model_name="small" ;;
        4) model_name="medium" ;;
        5) model_name="large-v3" ;;
        *) model_name="large-v3" ;;
    esac
    
    echo ""
    echo "Downloading Whisper $model_name..."
    python3 -c "
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
model_id = 'openai/whisper-$model_name'
print(f'Downloading {model_id}...')
model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id)
processor = AutoProcessor.from_pretrained(model_id)
print('✓ Model downloaded successfully!')
"
fi

# Test Whisper installation
echo ""
echo "============================================================="
echo "TESTING WHISPER INSTALLATION"
echo "============================================================="
echo ""

# Update requirements.txt
echo ""
echo "Updating requirements.txt..."
cat >> requirements.txt << 'EOF'

# Local Whisper on AMD ROCm
torch>=2.0.0
transformers>=4.30.0
accelerate>=0.20.0
librosa>=0.10.0
soundfile>=0.12.0
optimum>=1.12.0
EOF

echo "✓ Added Whisper dependencies to requirements.txt"

# Create test script
echo ""
echo "Creating test script..."
cat > test_whisper.py << 'EOF'
#!/usr/bin/env python3
"""
Test Whisper installation on AMD GPU
"""

import torch
from transformers import pipeline

print("=" * 70)
print("WHISPER INSTALLATION TEST")
print("=" * 70)

# Check PyTorch
print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    device = "cuda"
else:
    print("⚠️  Running on CPU")
    device = "cpu"

# Test Whisper (will download model if not cached)
print("\n" + "=" * 70)
print("Testing Whisper...")
print("=" * 70)

try:
    # Use tiny model for quick test
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny",
        device=device
    )
    print("✓ Whisper loaded successfully!")
    print(f"  Model: whisper-tiny")
    print(f"  Device: {device}")
    
    if torch.cuda.is_available():
        print(f"  VRAM allocated: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nIf you see '✓ Whisper loaded successfully', you're ready!")
print("\nNext steps:")
print("  1. Test on real audio: python whisper_local.py your_audio.m4a")
print("  2. Run transcription: python transcribe_local.py")
EOF

chmod +x test_whisper.py

# Show summary
echo ""
echo "============================================================="
echo "SETUP COMPLETE!"
echo "============================================================="
echo ""
echo "✓ PyTorch + ROCm installed"
echo "✓ Transformers + Whisper dependencies installed"
echo "✓ ML pipeline dependencies installed"
echo ""
echo "Next steps:"
echo ""
echo "1. Test installation:"
echo "   python test_whisper.py"
echo ""
echo "2. Test on a real audio file:"
echo "   cd AMD_server/ml_pipeline"
echo "   python audio/whisper_local.py /path/to/audio.m4a"
echo ""
echo "3. Run full transcription pipeline:"
echo "   python audio/transcribe_local.py --status  # Check status"
echo "   python audio/transcribe_local.py --dry-run # Preview"
echo "   python audio/transcribe_local.py           # Transcribe all"
echo ""
echo "4. Choose different model sizes:"
echo "   python audio/transcribe_local.py --model-size tiny      # Fastest"
echo "   python audio/transcribe_local.py --model-size medium    # Balanced"
echo "   python audio/transcribe_local.py --model-size large-v3  # Best (default)"
echo ""
echo "============================================================="
echo ""

# Show GPU info if available
if command -v rocm-smi &> /dev/null; then
    echo "Current GPU status:"
    echo ""
    rocm-smi || true
fi
