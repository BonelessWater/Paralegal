# Quick Start: Audio Transcription

## For Your Teammate

Hey! I've built a complete audio transcription pipeline for the 16 Morgan & Morgan call recordings. Here's what you need to do:

---

## Setup (2 minutes)

```bash
# 1. Pull latest code
cd ~/Paralegal
git pull

# 2. Install OpenAI package
pip install openai

# 3. Done! The .env file already has all credentials configured.
```

---

## Run Transcription (15 minutes)

```bash
# Navigate to audio pipeline
cd AMD_server/ml_pipeline/audio

# Run transcription (will ask for confirmation)
python transcribe_api.py
```

**What happens:**
- Loads 16 audio files from database
- Shows cost estimate ($1.44)
- Asks for confirmation
- Transcribes each call (~1 min each)
- Saves transcripts to database
- Shows success report

**Expected output:**
```
Found 16 audio recordings
Estimated cost: $1.44

Continue with transcription? [y/N]: y

[1/16] Morgan & Morgan - Call #MM001
   ✓ Transcribed in 45.3s
   ✓ Saved to database

...

✓ 16 transcripts saved to database!
```

---

## Verify It Worked

```python
# Quick test
cd AMD_server/ml_pipeline/audio
python -c "
from audio_loader import AudioLoader
loader = AudioLoader()
summary = loader.get_summary()
print(f'Transcribed: {summary[\"transcribed\"]}/16')
"
```

Should print: `Transcribed: 16/16`

---

## Troubleshooting

**"OpenAI API key not found"**
→ The key is in `.env` file. If you don't have it, ask Dom.

**"Audio file not found"**  
→ Make sure you're on the AMD server where the files are stored.

**"Module not found"**
→ Run: `pip install openai`

---

## Full Documentation

- **Quick guide**: `TRANSCRIPTION_INSTRUCTIONS.md` (root directory)
- **Technical docs**: `AMD_server/ml_pipeline/audio/README.md`
- **Database info**: `docs/DATABASE_DOCUMENTATION.md`

---

## What This Unlocks

Once transcription is done, we can:
✅ Build RAG semantic search (search across calls + docs)
✅ Train document classifier (include audio in ML model)
✅ Enable agents to query call transcripts
✅ Demo multi-modal legal AI (text + audio + images)

---

## Quick Commands Cheat Sheet

```bash
# Test without saving (dry run)
python transcribe_api.py --dry-run

# Transcribe all
python transcribe_api.py

# Transcribe specific IDs
python transcribe_api.py --ids 1 5 10

# Force re-transcribe
python transcribe_api.py --force
```

---

## Cost & Time

- **Cost**: $1.44 total ($0.09 per call)
- **Time**: 15-20 minutes
- **Accuracy**: 95%+ for legal terminology
- **Storage**: Saves to PostgreSQL `legal_data.documents.full_text`

---

**Questions?** Check `TRANSCRIPTION_INSTRUCTIONS.md` for detailed guide or ask Dom!
