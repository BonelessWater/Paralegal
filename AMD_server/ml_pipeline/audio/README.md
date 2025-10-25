# Audio Transcription Pipeline

Fast, production-ready audio transcription using OpenAI's Whisper API for Morgan & Morgan call recordings.

## Overview

This pipeline transcribes legal phone call recordings (.m4a format) and stores transcripts in PostgreSQL database for:
- Multi-modal legal AI demos
- Client communication analysis
- Evidence documentation
- RAG semantic search integration

## Features

✅ **OpenAI Whisper API Integration**
- Fast cloud-based transcription (30 sec - 2 min per 15-min call)
- High accuracy for legal terminology
- Automatic language detection
- Error handling with exponential backoff

✅ **Database Integration**
- Loads audio metadata from PostgreSQL
- Saves transcripts to `legal_data.documents.full_text`
- Tracks transcription status
- Supports incremental updates

✅ **Production Ready**
- Retry logic for API failures
- Rate limit handling
- File size validation (25MB limit)
- Dry-run mode for testing
- Detailed progress reporting

## Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install openai psycopg2-binary

# Or install from requirements.txt
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
# Add to .env file (already configured)
OPENAI_API_KEY=sk-proj-...
```

### 3. Run Transcription

```bash
# Navigate to audio directory
cd AMD_server/ml_pipeline/audio

# Transcribe all untranscribed recordings
python transcribe_api.py

# Dry run (test without saving)
python transcribe_api.py --dry-run

# Transcribe specific recordings by ID
python transcribe_api.py --ids 1 2 3

# Force re-transcribe already transcribed files
python transcribe_api.py --force
```

## Components

### 1. AudioLoader (`audio_loader.py`)

Loads audio file metadata from PostgreSQL database.

```python
from audio.audio_loader import AudioLoader

loader = AudioLoader()

# Get summary statistics
summary = loader.get_summary()
print(f"Total recordings: {summary['total_recordings']}")
print(f"Transcribed: {summary['transcribed']}")
print(f"Untranscribed: {summary['untranscribed']}")

# Load all audio files
audio_files = loader.load_audio_recordings()

# Load only untranscribed files
untranscribed = loader.load_audio_recordings(only_untranscribed=True)

# Verify files exist on disk
stats = loader.verify_audio_files(audio_files)
```

**Key Methods:**
- `load_audio_recordings(limit=None, only_untranscribed=False)` - Load audio metadata
- `get_audio_file_path(audio_record)` - Get file path for audio file
- `verify_audio_files(audio_files)` - Check file existence
- `get_summary()` - Get transcription statistics

### 2. WhisperAPITranscriber (`whisper_api.py`)

Transcribes audio using OpenAI Whisper API.

```python
from audio.whisper_api import WhisperAPITranscriber

transcriber = WhisperAPITranscriber()

# Transcribe single file
result = transcriber.transcribe("path/to/audio.m4a")
print(result['text'])

# Transcribe batch
audio_paths = ["call1.m4a", "call2.m4a", "call3.m4a"]
results = transcriber.transcribe_batch(audio_paths, verbose=True)

# Estimate cost
cost = transcriber.estimate_cost(audio_duration_minutes=240)
print(f"Estimated cost: ${cost:.2f}")
```

**Key Methods:**
- `transcribe(audio_path, language='en', prompt=None)` - Transcribe single file
- `transcribe_batch(audio_paths, language='en')` - Transcribe multiple files
- `estimate_cost(audio_duration_minutes)` - Calculate API cost
- `get_supported_formats()` - List supported audio formats

**Supported Formats:** `.flac`, `.mp3`, `.mp4`, `.m4a`, `.mpeg`, `.mpga`, `.oga`, `.ogg`, `.wav`, `.webm`

### 3. TranscriptionPipeline (`transcribe_api.py`)

End-to-end pipeline orchestration.

```python
from audio.transcribe_api import TranscriptionPipeline

pipeline = TranscriptionPipeline()

# Transcribe all untranscribed files
results = pipeline.transcribe_all()

# Transcribe specific IDs
results = pipeline.transcribe_all(record_ids=[1, 2, 3])

# Dry run (test mode)
results = pipeline.transcribe_all(dry_run=True)

# Force re-transcribe
results = pipeline.transcribe_all(force=True)
```

**Pipeline Steps:**
1. Load audio files from database
2. Verify files exist on disk
3. Estimate cost and confirm
4. Transcribe each file via OpenAI API
5. Save transcripts to database
6. Generate summary report

## Database Schema

Transcripts are saved to `legal_data.documents` table:

```sql
-- Audio recordings stored with:
document_type = 'Audio Recording'
url = '/path/to/audio.m4a'  -- File path
full_text = 'Transcript text...'  -- Transcription
updated_at = CURRENT_TIMESTAMP  -- Last update
```

**Query Transcripts:**
```sql
-- Get all transcribed audio recordings
SELECT id, title, full_text 
FROM legal_data.documents 
WHERE document_type = 'Audio Recording' 
AND full_text IS NOT NULL;

-- Get untranscribed recordings
SELECT id, title, url 
FROM legal_data.documents 
WHERE document_type = 'Audio Recording' 
AND (full_text IS NULL OR full_text = '');
```

## Pricing & Performance

### OpenAI Whisper API Pricing
- **Cost:** $0.006 per minute
- **Example:** 16 calls × 15 minutes = 240 minutes = **$1.44 total**

### Expected Performance
- **Speed:** 30 seconds - 2 minutes per 15-minute call
- **Accuracy:** 95%+ for clear audio with legal terminology
- **File Size Limit:** 25MB per file (API restriction)

### Cost Comparison

| Approach | Cost | Setup Time | Transcription Time |
|----------|------|------------|-------------------|
| **OpenAI API** | $1.44 | 5 min | 30 min |
| Local Whisper (GPU) | $0 | 2-3 hours | 2-4 hours |

## Usage Examples

### Example 1: Transcribe All Untranscribed Calls

```bash
cd AMD_server/ml_pipeline/audio
python transcribe_api.py
```

**Output:**
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

Continue with transcription? [y/N]: y

🎙️  Starting transcription...
======================================================================

[1/16] Morgan & Morgan - Initial Consultation - Case #MM001
   ID: 1
   ✓ Transcribed in 45.3s
   Transcript length: 12847 characters
   File size: 8.42 MB
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

### Example 2: Test with Dry Run

```bash
python transcribe_api.py --dry-run
```

Tests transcription without saving to database.

### Example 3: Transcribe Specific Recordings

```bash
python transcribe_api.py --ids 1 5 10
```

Only transcribes recordings with IDs 1, 5, and 10.

### Example 4: Re-transcribe All Files

```bash
python transcribe_api.py --force
```

Re-transcribes even if transcripts already exist.

## Integration with Other Components

### 1. ML Pipeline Integration

```python
# Use transcripts in document classifier
from ml_pipeline.data_loader import DataLoader

loader = DataLoader()
audio_transcripts = loader.load_morgan_documents(
    document_types=['Audio Recording']
)

# Train model on audio transcripts
X = [doc['full_text'] for doc in audio_transcripts]
y = [doc['document_type'] for doc in audio_transcripts]
```

### 2. RAG Integration

```python
# Add audio transcripts to semantic search index
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings for audio transcripts
embeddings = model.encode(audio_transcripts)
```

### 3. Agent Integration

```python
# Client Communication Agent can now access call transcripts
from AMD_server.agents.client_communication_agent import ClientCommunicationAgent

agent = ClientCommunicationAgent()

# Query: "What did the client say about their injury?"
response = agent.search_call_transcripts(query="injury details")
```

## Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Should show:
OPENAI_API_KEY=sk-proj-...
```

### Issue: "Audio file not found"

**Solution:**
```python
# Verify file paths in database
from audio.audio_loader import AudioLoader

loader = AudioLoader()
audio_files = loader.load_audio_recordings()

for audio in audio_files:
    path = loader.get_audio_file_path(audio)
    print(f"{audio['id']}: {path} - Exists: {path.exists() if path else False}")
```

### Issue: "File too large (>25MB)"

**Solution:**
```bash
# Compress audio file
ffmpeg -i input.m4a -ac 1 -ar 16000 -b:a 64k output.m4a
```

### Issue: Rate limit errors

**Solution:** The transcriber automatically handles rate limits with exponential backoff. If persistent:

```python
# Increase max retries
transcriber = WhisperAPITranscriber(max_retries=5)
```

## Testing

### Unit Tests

```bash
# Test AudioLoader
cd AMD_server/ml_pipeline/audio
python audio_loader.py

# Test WhisperAPI
python whisper_api.py
```

### Integration Test

```bash
# Dry run on all files (no cost, no database changes)
python transcribe_api.py --dry-run

# Test on single file
python transcribe_api.py --ids 1 --dry-run
```

## Next Steps

After transcription completes:

1. **Generate RAG Embeddings** - Create semantic search index
2. **Train Document Classifier** - Include audio in ML model
3. **Agent Integration** - Enable agents to query call transcripts
4. **Demo Preparation** - Showcase multi-modal capabilities

## API Reference

### Command Line Arguments

```bash
python transcribe_api.py [OPTIONS]

Options:
  --force           Re-transcribe already transcribed files
  --dry-run         Test mode - don't save to database
  --ids ID [ID...]  Specific record IDs to transcribe
  --language CODE   Audio language code (default: en)
  --api-key KEY     OpenAI API key (default: from env)
  -h, --help        Show help message
```

## Performance Tips

1. **Batch Processing:** Transcribe during off-peak hours for faster API response
2. **File Size:** Compress large files to reduce upload time
3. **Language Code:** Specify language (`--language en`) for 10-20% speed boost
4. **Prompting:** Use legal context in prompt for better accuracy

## Support

For issues or questions:
- Check database connection: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`
- Verify API key: `echo $OPENAI_API_KEY`
- Review logs: Detailed error messages printed to console
