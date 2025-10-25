#!/bin/bash
# Run this script on the AMD server to transcribe all audio files

cd /home/amd-knights/Paralegal/AMD_server/ml_pipeline
source ../../venv/bin/activate
export HF_HOME=/home/amd-knights/Paralegal/.cache/huggingface

echo "Starting transcription..."
python audio/transcribe_local.py
