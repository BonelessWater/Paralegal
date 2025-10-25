# Audio Transcription Instructions for Teammate

## Overview
We've built a complete audio transcription pipeline using OpenAI Whisper API. This will transcribe all 16 Morgan & Morgan call recordings and save them to the PostgreSQL database.

**Cost**: ~$1.44 total ($0.09 per call)  
**Time**: ~15 minutes for all 16 calls  
**Result**: Transcripts saved to database for RAG search & agent integration

---

## Setup (5 minutes)

### 1. Pull Latest Code
```bash
cd ~/Paralegal  # Or wherever your repo is
git pull
```

### 2. Install Python Dependencies
```bash
# Install OpenAI package
pip install openai

# Or install all requirements
pip install -r requirements.txt
```

### 3. Verify .env File Has OpenAI Key
```bash
# Check if key exists
grep OPENAI_API_KEY .env

# Should show:
# OPENAI_API_KEY=sk-proj-...
```

**If key is missing**: The key is already in our actual `.env` file (which is gitignored for security). Contact Dom if you need it.

---

## Run Transcription (15 minutes)

### Step 1: Navigate to Audio Pipeline
```bash
cd AMD_server/ml_pipeline/audio
```

### Step 2: Test with Dry Run (No Cost, No Database Changes)
```bash
python transcribe_api.py --dry-run
```

**Expected Output:**
```
======================================================================
MORGAN & MORGAN CALL TRANSCRIPTION PIPELINE
======================================================================

📁 Loading audio files from database...
   Found 16 audio recordings

🔍 Verifying audio files...
   Total: 16
   Found on disk: 16
   Missing: 0
   Already transcribed: 0
   Need transcription: 16

💰 Cost Estimation:
   Files to transcribe: 16
   Estimated duration: 240 minutes (~15 min/call)
   Estimated cost: $1.44

⚠️  DRY RUN MODE - Will not save to database

Continue with transcription? [y/N]:
```

**Action**: Type `y` and press Enter to test. This will transcribe without saving to database (no cost if you cancel early).

### Step 3: Run Actual Transcription
```bash
python transcribe_api.py
```

**What happens**:
1. Loads 16 audio files from PostgreSQL
2. Verifies files exist on disk
3. Shows cost estimate ($1.44)
4. Asks for confirmation
5. Transcribes each file via OpenAI API (~1 min each)
6. Saves transcript to `legal_data.documents.full_text`
7. Shows summary report

**Expected Runtime**: 10-20 minutes total

**Sample Progress Output**:
```
🎙️  Starting transcription...
======================================================================

[1/16] Morgan & Morgan - Initial Consultation - Case #MM001
   ID: 1
   ✓ Transcribed in 45.3s
   Transcript length: 12847 characters
   File size: 8.42 MB
   ✓ Saved to database

[2/16] Morgan & Morgan - Follow-up Call - Case #MM002
   ID: 2
   ✓ Transcribed in 38.7s
   Transcript length: 9234 characters
   File size: 6.15 MB
   ✓ Saved to database

...

======================================================================
TRANSCRIPTION SUMMARY
======================================================================

Total files: 16
✓ Successful: 16
✗ Failed: 0
⊘ Skipped: 0

⏱️  Total time: 892.45 seconds (14.87 minutes)
💰 Estimated cost: $1.44

✓ 16 transcripts saved to database!
```

---

## Verify Results

### Check Database for Transcripts
```bash
# Connect to PostgreSQL (credentials from .env)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Query transcripts
SELECT id, title, LENGTH(full_text) as transcript_length
FROM legal_data.documents
WHERE document_type = 'Audio Recording'
AND full_text IS NOT NULL;

# Should show 16 records with transcript_length > 0
```

### Quick Python Test
```python
from audio.audio_loader import AudioLoader

loader = AudioLoader()
summary = loader.get_summary()

print(f"Total recordings: {summary['total_recordings']}")
print(f"Transcribed: {summary['transcribed']}")  # Should be 16
print(f"Untranscribed: {summary['untranscribed']}")  # Should be 0
```

---

## Troubleshooting

### Issue: "OpenAI API key not found"
**Solution**:
```bash
# Check .env file exists
ls -la .env

# Check key is set
grep OPENAI_API_KEY .env

# If missing, contact Dom for the key
```

### Issue: "Audio file not found"
**Solution**:
```bash
# Check if you're on AMD server (files are there)
hostname  # Should show AMD server name

# If not on AMD server, SSH in first (credentials in .env)
ssh $AMD_SSH_USER@$AMD_SSH_HOST
cd ~/Paralegal
```

### Issue: "ModuleNotFoundError: No module named 'openai'"
**Solution**:
```bash
pip install openai
```

### Issue: Rate limit errors
**Don't worry** - The script automatically retries with exponential backoff. Just let it run.

---

## Advanced Options

### Transcribe Specific Files Only
```bash
# Transcribe only IDs 1, 5, and 10
python transcribe_api.py --ids 1 5 10
```

### Force Re-transcribe Already Transcribed Files
```bash
python transcribe_api.py --force
```

### Specify Language (Slight Speed Boost)
```bash
python transcribe_api.py --language en
```

---

## What to Do After Transcription

Once transcription completes:

### 1. Verify in Database
```sql
-- Check all transcripts exist
SELECT COUNT(*) FROM legal_data.documents 
WHERE document_type = 'Audio Recording' AND full_text IS NOT NULL;
-- Should return: 16

-- Check average transcript length
SELECT AVG(LENGTH(full_text)) FROM legal_data.documents 
WHERE document_type = 'Audio Recording';
-- Should be ~10,000-15,000 characters per call
```

### 2. Test with Agents
The transcripts are now available to all our agents:
- **Client Communication Agent** can search call transcripts
- **Legal Researcher Agent** can find relevant call details
- **Evidence Sorter Agent** can classify call content

### 3. Build RAG Embeddings (Next Step)
Once transcription is done, we can generate semantic search embeddings for all documents including audio transcripts.

---

## Files Created

All files are in `AMD_server/ml_pipeline/audio/`:

- **`audio_loader.py`** - Loads audio metadata from PostgreSQL
- **`whisper_api.py`** - OpenAI Whisper API client
- **`transcribe_api.py`** - Main transcription script (this is what you run)
- **`README.md`** - Full technical documentation

---

## Summary

**Quick Start:**
```bash
cd ~/Paralegal
git pull
pip install openai
cd AMD_server/ml_pipeline/audio
python transcribe_api.py --dry-run  # Test first
python transcribe_api.py             # Run actual transcription
```

**Expected Results:**
- ✅ 16 call transcripts in database
- ✅ ~$1.44 API cost
- ✅ ~15 minutes runtime
- ✅ Ready for RAG search & agent integration

---

## Questions?

- **Script location**: `AMD_server/ml_pipeline/audio/transcribe_api.py`
- **Full docs**: `AMD_server/ml_pipeline/audio/README.md`
- **Database schema**: `docs/DATABASE_DOCUMENTATION.md`
- **Contact**: Dom (if issues with API key or database access)

---

## Alternative: Local Whisper (If You Want to Build It Later)

If you want to avoid API costs and run Whisper locally on our AMD GPU:
1. We'd need to build a local Whisper implementation (~2-3 hours setup)
2. Uses HuggingFace transformers + ROCm GPU acceleration
3. Free but slower (2-4 hours to transcribe all 16 calls)
4. Better for privacy and offline use

**For now, stick with API** - it's fast, cheap, and we need results quickly for the hackathon!
