#!/bin/bash
# Run this script on the AMD server to transcribe all audio files

cd /home/amd-knights/Paralegal

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Loaded .env file"
else
    echo "⚠️  Warning: .env file not found"
fi

cd AMD_server/ml_pipeline
source ../../venv/bin/activate

echo "Starting transcription..."
python audio/transcribe_local.py
