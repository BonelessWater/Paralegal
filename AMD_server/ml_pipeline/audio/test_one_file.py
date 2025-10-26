#!/usr/bin/env python3
"""
Debug script to test transcription of a single file
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print(f"✓ Loaded environment from {env_path}")
    print(f"  HF_HOME: {os.getenv('HF_HOME')}")
    print()

# Test transcribing one file
test_file = "/home/amd-knights/Morgan&Morgan/File 4-9840025/File 4- 2nd call.m4a"

print("=" * 70)
print("SINGLE FILE TRANSCRIPTION TEST")
print("=" * 70)
print(f"\nFile: {test_file}")
print(f"Exists: {Path(test_file).exists()}")
print()

# Test 1: Load with librosa
print("TEST 1: Loading audio with librosa...")
try:
    import librosa
    audio, sr = librosa.load(test_file, sr=16000, mono=True)
    print(f"✓ Loaded: {len(audio)} samples, {len(audio)/sr:.2f} seconds")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Initialize Whisper
print("\nTEST 2: Loading Whisper model...")
try:
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from audio.whisper_local import WhisperLocalTranscriber
    transcriber = WhisperLocalTranscriber(model_size="large-v3")
    print("✓ Model loaded")
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Transcribe
print("\nTEST 3: Transcribing...")
try:
    result = transcriber.transcribe(test_file, language="en")
    print(f"✓ Transcribed!")
    print(f"\nTranscript ({len(result['text'])} chars):")
    print("-" * 70)
    print(result['text'][:500])  # First 500 chars
    print("-" * 70)
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")
