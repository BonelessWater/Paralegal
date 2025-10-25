#!/bin/bash
#
# Quick Whisper Setup - Install only what's needed
#

set -e

echo "============================================================="
echo "QUICK WHISPER SETUP - Install Dependencies Only"
echo "============================================================="

cd /home/amd-knights/Paralegal

# Install Python packages
echo ""
echo "Installing Python packages..."
pip install --user transformers>=4.30.0
pip install --user accelerate>=0.20.0
pip install --user librosa>=0.10.0
pip install --user soundfile>=0.12.0
pip install --user optimum>=1.12.0
pip install --user python-dotenv

echo ""
echo "✓ Dependencies installed!"
echo ""
echo "Testing installation..."

# Quick test
python3 -c "
try:
    from transformers import pipeline
    print('✓ Transformers installed')
except ImportError as e:
    print(f'✗ Error: {e}')

try:
    import librosa
    print('✓ Librosa installed')
except ImportError as e:
    print(f'✗ Error: {e}')

try:
    import soundfile
    print('✓ Soundfile installed')
except ImportError as e:
    print(f'✗ Error: {e}')
"

echo ""
echo "============================================================="
echo "SETUP COMPLETE!"
echo "============================================================="
echo ""
echo "Next steps:"
echo "1. Test: python3 AMD_server/ml_pipeline/audio/whisper_local.py"
echo "2. Transcribe: cd AMD_server/ml_pipeline && python3 audio/transcribe_local.py"
