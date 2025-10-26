# 🎯 QUICK START: Local Whisper Transcription

**Get your 16 audio calls transcribed for FREE in ~30 minutes**

---

## Prerequisites ✅

- [ ] AMD MI300X server access
- [ ] PostgreSQL database with 16 audio recordings
- [ ] `.env` file with `DB_HOST`, `DB_USER`, `DB_PASSWORD`
- [ ] ROCm already installed (you have this!)

---

## Step-by-Step Setup (15 minutes)

### 1️⃣ SSH to AMD Server

```bash
ssh user@134.199.202.8  # Your AMD server
cd /path/to/Paralegal
```

### 2️⃣ Run Setup Script

```bash
# Make executable
chmod +x AMD_server/setup/setup_whisper.sh

# Run installation (takes ~10-15 minutes)
./AMD_server/setup/setup_whisper.sh
```

**What it does:**
- ✅ Installs PyTorch with ROCm support
- ✅ Installs HuggingFace Transformers + Whisper
- ✅ Installs audio processing libraries
- ✅ Downloads Whisper model (optional, ~6GB)
- ✅ Creates test scripts

**During installation, when asked:**
- Create virtual environment? → `y` (recommended)
- Pre-download Whisper model? → `y`
- Model size? → `5` (large-v3 for best accuracy)

### 3️⃣ Test Installation

```bash
# Quick test
python test_whisper.py
```

**Expected output:**
```
✓ Whisper loaded successfully!
  Model: whisper-tiny
  Device: cuda
  VRAM allocated: 0.xx GB
```

### 4️⃣ Test on One Audio File

```bash
cd AMD_server/ml_pipeline

# Test on single file
python audio/whisper_local.py /data/audio/Morgan_Call_Recording_001.m4a
```

**Expected output:**
```
✓ Whisper large-v3 loaded successfully!
Transcribing: Morgan_Call_Recording_001.m4a
✓ Transcribed in 12.3s (1847 chars)

Transcript:
----------------------------------------------------------------------
[Full transcript text here]
----------------------------------------------------------------------
```

---

## Step-by-Step Transcription (15 minutes)

### 5️⃣ Check Status

```bash
cd AMD_server/ml_pipeline
python audio/transcribe_local.py --status
```

**Output:**
```
Total audio files: 16
Transcribed: 0
Not transcribed: 16
Completion: 0.0%
```

### 6️⃣ Dry Run (Preview)

```bash
python audio/transcribe_local.py --dry-run
```

This shows what will happen **without** actually transcribing.

### 7️⃣ Transcribe First 3 Files (Test)

```bash
python audio/transcribe_local.py --limit 3
```

**What happens:**
- Loads 3 audio files from database
- Transcribes each using GPU
- Saves to database
- Takes ~30-45 seconds total

### 8️⃣ Transcribe All 16 Files

```bash
python audio/transcribe_local.py
```

**What happens:**
- Loads all 16 audio files
- Shows summary and cost estimate (FREE!)
- Asks for confirmation
- Transcribes each file (~10-15s each)
- Saves to database after each file
- Takes ~15-25 minutes total

**Expected output:**
```
TRANSCRIPTION COMPLETE
======================================================================
Total files: 16
Successful: 16
Failed: 0
Total time: 234.5s
Average time per file: 14.7s
Total cost: $0.00 (FREE!)
```

---

## Troubleshooting 🔧

### GPU Not Detected?

```bash
# Check GPU
rocm-smi

# If not working, set environment variable
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Retry
python test_whisper.py
```

### "Module not found" Error?

```bash
# Re-run setup
./AMD_server/setup/setup_whisper.sh

# Or install manually
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
pip install transformers accelerate librosa soundfile
```

### Database Connection Error?

```bash
# Check .env file
cat .env | grep DB_

# Should see:
# DB_HOST=134.199.202.8
# DB_USER=paralegal_user
# DB_PASSWORD=hackathon2024
# DB_NAME=paralegal_db

# If missing, add them to .env
```

### Too Slow?

```bash
# Use faster model (less accurate)
python audio/transcribe_local.py --model-size medium
```

---

## Model Size Comparison

| Model | Speed | Accuracy | Time for 16 calls |
|-------|-------|----------|-------------------|
| tiny | 5x faster | ★★☆☆☆ | ~5 min |
| base | 3x faster | ★★★☆☆ | ~10 min |
| small | 2x faster | ★★★★☆ | ~15 min |
| medium | 1.5x faster | ★★★★★ | ~20 min |
| **large-v3** | **1x (baseline)** | **★★★★★** | **~25 min** |

**Recommendation:** Use `large-v3` (default) for production quality.

---

## After Transcription

Once all 16 calls are transcribed:

### 1. Verify in Database

```bash
# Check transcripts
psql -h 134.199.202.8 -U paralegal_user -d paralegal_db -c "
SELECT id, filename, LENGTH(extracted_text) as text_length 
FROM legal_data.documents 
WHERE document_type = 'Audio Recording'
LIMIT 5;
"
```

### 2. Train ML Models

```bash
# Train document classifier
cd AMD_server/ml_pipeline
python train.py

# Generate RAG embeddings
python rag_embeddings.py
```

### 3. Test Unified API

```python
from ml_inference import MLInference

ml = MLInference()

# Process audio call (transcribe + analyze + find similar cases)
result = ml.process_audio_call("/path/to/call.m4a")

print(f"Transcript: {result['transcript'][:200]}...")
print(f"Type: {result['classification']['predicted_type']}")
print(f"Similar cases: {len(result['similar_cases'])}")
```

---

## Cost Comparison

| Method | 16 calls | Your savings |
|--------|----------|--------------|
| **Local Whisper** | **$0.00** | - |
| OpenAI API | $0.90 | **Saved $0.90** |

**Scale to 1000 calls:**
- Local: $0
- OpenAI: $56
- **Your savings: $56/month** 🎉

---

## Quick Commands Reference

```bash
# Setup
./AMD_server/setup/setup_whisper.sh

# Test
python test_whisper.py

# Check status
python audio/transcribe_local.py --status

# Dry run
python audio/transcribe_local.py --dry-run

# Test on 3 files
python audio/transcribe_local.py --limit 3

# Transcribe all
python audio/transcribe_local.py

# Use faster model
python audio/transcribe_local.py --model-size medium

# Force re-transcribe
python audio/transcribe_local.py --force
```

---

## Need Help?

1. **Check logs:** Read error messages in terminal
2. **GPU status:** Run `rocm-smi`
3. **Test installation:** Run `python test_whisper.py`
4. **Full guide:** See `docs/LOCAL_WHISPER_SETUP.md`

---

## Summary

**Time investment:** ~30 minutes total
- Setup: 15 minutes
- Transcription: 15-25 minutes

**Cost:** $0 (vs $0.90 with OpenAI)

**Result:** 16 transcribed calls in your database, ready for ML training

**Next steps:** Train models, generate embeddings, integrate with agents

---

🚀 **Ready? Start with step 1!**
