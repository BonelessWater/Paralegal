# Local Whisper Setup Guide - AMD MI300X + ROCm

**FREE, GPU-accelerated audio transcription using Whisper on AMD hardware**

This guide will help you set up local Whisper transcription on your AMD MI300X server with ROCm GPU acceleration. This replaces the OpenAI API approach and provides:

- **$0 cost** (vs $0.006/min with OpenAI API)
- **Privacy** (legal calls stay on your server)
- **Speed** (GPU batch processing)
- **Offline capability** (no internet needed)
- **Unlimited usage** (no API rate limits)

---

## Quick Start (5 minutes)

```bash
# 1. SSH to AMD server
ssh user@your-amd-server

# 2. Navigate to project
cd /path/to/Paralegal

# 3. Run setup script
chmod +x AMD_server/setup/setup_whisper.sh
./AMD_server/setup/setup_whisper.sh

# 4. Test installation
python test_whisper.py

# 5. Transcribe your audio
cd AMD_server/ml_pipeline
python audio/transcribe_local.py
```

Done! Your 16 Morgan & Morgan calls will be transcribed for **FREE** in ~15-30 minutes.

---

## Detailed Setup

### Prerequisites

**Hardware:**
- AMD MI300X GPU (you have this ✓)
- ROCm 5.7+ installed (already configured ✓)
- 32GB+ VRAM (you have 192GB ✓)

**Software:**
- Python 3.8+
- PostgreSQL database with audio files
- `.env` file with database credentials

### Installation Steps

#### 1. Install Dependencies

**Option A: Automated (Recommended)**
```bash
cd /path/to/Paralegal
chmod +x AMD_server/setup/setup_whisper.sh
./AMD_server/setup/setup_whisper.sh
```

This script will:
- Check ROCm installation
- Install PyTorch with ROCm support
- Install HuggingFace Transformers
- Install audio processing libraries (librosa, soundfile)
- Optionally pre-download Whisper model weights
- Create test scripts
- Verify installation

**Option B: Manual**
```bash
# Install PyTorch for ROCm 6.0
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

# Install Whisper dependencies
pip install transformers>=4.30.0
pip install accelerate>=0.20.0
pip install librosa>=0.10.0
pip install soundfile>=0.12.0
pip install optimum>=1.12.0

# Install ML pipeline dependencies (if not already installed)
pip install psycopg2-binary pandas numpy python-dotenv
```

#### 2. Verify Installation

```bash
# Test PyTorch + ROCm
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"

# Expected output:
# CUDA: True, GPU: AMD Instinct MI300X

# Test Whisper
python test_whisper.py
```

#### 3. Configure Database

Make sure your `.env` file has database credentials:
```bash
DB_HOST=your_server_ip
DB_PORT=5432
DB_NAME=paralegal_db
DB_USER=paralegal_user
DB_PASSWORD=your_password
```

---

## Usage

### Check Transcription Status

```bash
cd AMD_server/ml_pipeline
python audio/transcribe_local.py --status
```

Output:
```
TRANSCRIPTION STATUS
======================================================================
Total audio files: 16
Transcribed: 0
Not transcribed: 16
Completion: 0.0%
```

### Dry Run (Preview)

```bash
python audio/transcribe_local.py --dry-run
```

This shows what will be transcribed **without** actually processing:
```
AUDIO TRANSCRIPTION PIPELINE
======================================================================
Mode: DRY RUN
Force re-transcription: False
Limit: None

📊 Summary:
  Total files: 16
  Already transcribed: 0
  Cost: FREE (local processing)
```

### Transcribe All Files

```bash
python audio/transcribe_local.py
```

This will:
1. Load 16 audio files from database
2. Transcribe each using GPU-accelerated Whisper
3. Save transcripts to database
4. Show progress for each file

**Expected output:**
```
AUDIO TRANSCRIPTION PIPELINE
======================================================================
Mode: LIVE
Force re-transcription: False
Limit: None

Loading audio files from database...
----------------------------------------------------------------------
✓ Found 16 audio files

📊 Summary:
  Total files: 16
  Already transcribed: 0
  Cost: FREE (local processing)

Proceed with transcription? (y/n): y

Transcribing audio files...
----------------------------------------------------------------------

[1/16] Morgan_Call_Recording_001.m4a
  ID: 55
  Path: /data/audio/Morgan_Call_Recording_001.m4a
  ✓ Transcribed in 12.3s
  Length: 1847 characters
  ✓ Saved to database

[2/16] Morgan_Call_Recording_002.m4a
  ID: 56
  Path: /data/audio/Morgan_Call_Recording_002.m4a
  ✓ Transcribed in 15.7s
  Length: 2134 characters
  ✓ Saved to database

... (14 more files)

======================================================================
TRANSCRIPTION COMPLETE
======================================================================
Total files: 16
Successful: 16
Failed: 0
Skipped: 0
Total time: 234.5s
Average time per file: 14.7s
Total cost: $0.00 (FREE!)
```

### Advanced Options

**Choose Model Size:**
```bash
# Tiny - Fastest, 39M params, ~1GB VRAM
python audio/transcribe_local.py --model-size tiny

# Base - Fast, 74M params, ~1.5GB VRAM
python audio/transcribe_local.py --model-size base

# Small - Balanced, 244M params, ~2GB VRAM
python audio/transcribe_local.py --model-size small

# Medium - Good, 769M params, ~5GB VRAM
python audio/transcribe_local.py --model-size medium

# Large-v3 - Best accuracy, 1550M params, ~10GB VRAM (DEFAULT)
python audio/transcribe_local.py --model-size large-v3
```

**Limit Number of Files:**
```bash
# Test on first 3 files
python audio/transcribe_local.py --limit 3
```

**Force Re-transcription:**
```bash
# Re-transcribe files that were already processed
python audio/transcribe_local.py --force
```

**Specify Language:**
```bash
# For Spanish audio
python audio/transcribe_local.py --language es
```

---

## Model Comparison

| Model | Params | VRAM | Speed | Accuracy | Use Case |
|-------|--------|------|-------|----------|----------|
| tiny | 39M | ~1GB | 5x | ★★☆☆☆ | Quick drafts |
| base | 74M | ~1.5GB | 3x | ★★★☆☆ | Fast preview |
| small | 244M | ~2GB | 2x | ★★★★☆ | Balanced |
| medium | 769M | ~5GB | 1.5x | ★★★★★ | Production |
| **large-v3** | 1550M | ~10GB | 1x | ★★★★★ | **Best (recommended)** |

**Recommendation for your setup:**
- Use **large-v3** for production (best accuracy)
- Use **medium** for faster iteration during development
- You have 192GB VRAM, so even large-v3 is tiny for you!

---

## Performance Benchmarks

**Expected performance on AMD MI300X:**

| Model | Time per minute of audio | 16 calls (~2.5 hours audio) |
|-------|--------------------------|------------------------------|
| tiny | ~0.5s | ~5 minutes total |
| base | ~1s | ~10 minutes total |
| small | ~2s | ~15 minutes total |
| medium | ~3s | ~20 minutes total |
| **large-v3** | **~5s** | **~25-30 minutes total** |

**Cost comparison:**

| Method | 16 calls (2.5 hours) | 100 calls | 1000 calls |
|--------|---------------------|-----------|------------|
| **Local Whisper** | **$0** | **$0** | **$0** |
| OpenAI API | $0.90 | $5.60 | $56.00 |

---

## Programmatic Usage

### Basic Transcription

```python
from audio.whisper_local import WhisperLocalTranscriber

# Initialize
transcriber = WhisperLocalTranscriber(model_size="large-v3")

# Transcribe single file
result = transcriber.transcribe("audio.m4a")
print(result['text'])

# Get transcript + metadata
print(f"Language: {result['language']}")
print(f"Duration: {result['duration_seconds']:.2f}s")
print(f"File: {result['file_path']}")
```

### Batch Processing

```python
# Transcribe multiple files
audio_files = [
    "/path/to/call1.m4a",
    "/path/to/call2.m4a",
    "/path/to/call3.m4a"
]

results = transcriber.transcribe_batch(audio_files)

for result in results:
    if result['success']:
        print(f"✓ {result['file_path']}: {len(result['text'])} chars")
    else:
        print(f"✗ {result['file_path']}: {result['error']}")
```

### With Timestamps

```python
# Get word-level timestamps
result = transcriber.transcribe(
    "audio.m4a",
    return_timestamps=True
)

for chunk in result['chunks']:
    print(f"[{chunk['timestamp']}] {chunk['text']}")
```

### Full Pipeline

```python
from audio.transcribe_local import LocalTranscriptionPipeline

# Initialize pipeline
pipeline = LocalTranscriptionPipeline(model_size="large-v3")

# Transcribe all from database
results = pipeline.transcribe_all(
    dry_run=False,      # Set to True for preview
    force=False,        # Set to True to re-transcribe
    limit=None,         # Set to N to process N files
    language="en"       # Audio language
)

print(f"Transcribed {results['successful']} files in {results['total_duration']:.2f}s")
```

---

## Integration with Agents

Once transcribed, use the ML inference API to process audio:

```python
from ml_inference import MLInference

# Initialize
ml = MLInference()

# Process audio call (transcribe + analyze)
result = ml.process_audio_call("/path/to/call.m4a")

print(f"Transcript: {result['transcript']}")
print(f"Document type: {result['classification']['predicted_type']}")
print(f"Related cases: {len(result['similar_cases'])} found")

for case in result['similar_cases']:
    print(f"  - {case['filename']} (similarity: {case['score']:.2f})")
```

---

## Troubleshooting

### GPU Not Detected

**Issue:** `CUDA available: False` or running on CPU

**Solutions:**
```bash
# 1. Check ROCm installation
rocm-smi

# 2. Check PyTorch sees GPU
python -c "import torch; print(torch.cuda.is_available())"

# 3. Reinstall PyTorch with ROCm
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0

# 4. Set environment variables
export HSA_OVERRIDE_GFX_VERSION=11.0.0  # For MI300X
export ROCM_HOME=/opt/rocm
```

### Out of Memory

**Issue:** `CUDA out of memory` error

**Solutions:**
```bash
# Use smaller model
python audio/transcribe_local.py --model-size medium

# Or use lower precision (automatic with float16, but can force)
# Edit whisper_local.py: torch_dtype="float16"

# Your MI300X has 192GB VRAM, so this is unlikely!
```

### Slow Transcription

**Issue:** Transcription taking too long

**Solutions:**
```bash
# 1. Use smaller model
python audio/transcribe_local.py --model-size medium

# 2. Enable flash attention (already enabled by default)
# 3. Check GPU utilization
rocm-smi -d 0 --showuse

# 4. Ensure GPU is being used
python -c "import torch; print(torch.cuda.is_available())"
```

### Model Download Fails

**Issue:** Cannot download Whisper weights from HuggingFace

**Solutions:**
```bash
# 1. Set HuggingFace token (if needed for private models)
export HUGGING_FACE_HUB_TOKEN="your_token"

# 2. Download manually
python -c "
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
model = AutoModelForSpeechSeq2Seq.from_pretrained('openai/whisper-large-v3')
processor = AutoProcessor.from_pretrained('openai/whisper-large-v3')
"

# 3. Use different model
python audio/transcribe_local.py --model-size medium
```

### Database Connection Error

**Issue:** Cannot connect to PostgreSQL

**Solutions:**
```bash
# 1. Check .env file
cat .env | grep DB_

# 2. Test connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# 3. Verify credentials
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'Host: {os.getenv(\"DB_HOST\")}')
print(f'User: {os.getenv(\"DB_USER\")}')
print(f'DB: {os.getenv(\"DB_NAME\")}')
"
```

---

## Next Steps

After transcribing your audio:

1. **Train document classifier:**
   ```bash
   cd AMD_server/ml_pipeline
   python train.py
   ```

2. **Generate RAG embeddings:**
   ```bash
   python rag_embeddings.py
   ```

3. **Test unified inference API:**
   ```python
   from ml_inference import MLInference
   ml = MLInference()
   
   # Classify document
   result = ml.classify_document("Contract text here...")
   
   # Search similar cases
   cases = ml.search_similar_cases("personal injury case")
   
   # Process audio call
   result = ml.process_audio_call("/path/to/call.m4a")
   ```

4. **Integrate with agents:**
   - See `docs/AGENT_TRAINING_OPTIMIZATION.md`
   - See `ML_PIPELINE_GUIDE.md`

---

## Cost Savings

**Your savings by using local Whisper:**

| Scenario | OpenAI API Cost | Local Cost | Savings |
|----------|----------------|------------|---------|
| 16 demo calls | $0.90 | $0 | $0.90 |
| 100 client calls | $5.60 | $0 | $5.60 |
| 1,000 calls/month | $56 | $0 | $56/month |
| **10,000 calls/year** | **$560** | **$0** | **$560/year** |

Plus:
- ✓ **Privacy:** Legal calls never leave your server
- ✓ **Speed:** GPU batch processing potentially faster than API
- ✓ **Offline:** No internet dependency
- ✓ **Demo factor:** Shows technical sophistication

---

## Support

If you run into issues:

1. Check this guide's troubleshooting section
2. Run: `python test_whisper.py`
3. Check GPU: `rocm-smi`
4. Check logs: Look for error messages in terminal output

**Common issues are almost always:**
- ROCm not seeing GPU → Set `HSA_OVERRIDE_GFX_VERSION=11.0.0`
- Wrong PyTorch version → Use ROCm-specific install
- Missing dependencies → Run `setup_whisper.sh` again
