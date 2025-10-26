# Email Processing Pipeline

Complete email classification and analysis system for legal practice automation.

## Overview

The Email Pipeline processes legal emails to:
- **Classify** emails by task type (client communication, records requests, etc.)
- **Extract** entities (people, organizations, case numbers, claim numbers)
- **Calculate** urgency scores for prioritization
- **Analyze** sentiment to detect client frustration
- **Route** emails to appropriate agents/workflows

## Features

### 1. Email Classification
Routes emails to the correct workflow based on content:
- `CLIENT_COMMUNICATION` - Direct client correspondence
- `RECORDS_REQUEST` - Medical/legal records requests
- `LEGAL_RESEARCH` - Research or case law questions
- `SETTLEMENT_DISCUSSION` - Settlement negotiations
- `COURT_FILING` - Court documents and filings
- `INTERNAL` - Internal team communication
- `OTHER` - Uncategorized

### 2. Entity Extraction
Identifies key information using NER + regex:
- **People** (PERSON) - Client names, attorneys, doctors
- **Organizations** (ORG) - Hospitals, insurance companies
- **Dates** (DATE) - Deadlines, appointment dates
- **Money** (MONEY) - Settlement amounts, medical costs
- **Locations** (GPE) - Cities, states, counties
- **Case Numbers** - Court case identifiers
- **Claim Numbers** - Insurance claim IDs
- **Phone Numbers** - Contact information
- **Email Addresses** - Correspondence trails

### 3. Urgency Scoring
Calculates 0.0-1.0 urgency score based on:
- **High urgency keywords**: "urgent", "ASAP", "immediately", "emergency"
- **Medium urgency keywords**: "soon", "quickly", "important"
- **Punctuation**: Exclamation marks (!!)
- **Formatting**: ALL CAPS words
- **Recency**: Recent emails = higher urgency
- **Sentiment**: Negative sentiment = higher urgency

### 4. Sentiment Analysis
Detects client emotion to identify escalations:
- `POSITIVE` - Satisfied, appreciative clients
- `NEGATIVE` - Frustrated, angry, disappointed
- `NEUTRAL` - Factual, information-seeking

## Architecture

```
email/
├── __init__.py              # Module exports
├── email_loader.py          # IMAP + database integration (310 lines)
├── email_classifier.py      # Task type classification (375 lines)
├── email_processor.py       # Entity extraction + urgency + sentiment (400 lines)
├── test_email.py            # Comprehensive test suite (330 lines)
└── README.md                # This file
```

### Data Flow

```
Gmail IMAP → EmailLoader → Database Storage
                              ↓
                     Email Classification
                      (TF-IDF + RandomForest)
                              ↓
                     Email Processing
           (spaCy NER + DistilBERT Sentiment)
                              ↓
              Structured Output → Agent Routing
```

## Installation

### Dependencies

```bash
# Core ML libraries
pip install scikit-learn numpy spacy transformers

# Email processing
pip install python-dotenv

# spaCy English model
python -m spacy download en_core_web_sm
```

### Environment Variables

Create `.env` file:

```env
# Gmail credentials (use App Password, not account password)
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_app_password

# Database (optional, for email storage)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legal_data
DB_USER=postgres
DB_PASS=your_password
```

**Note**: For Gmail, generate an App Password:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password under "Signing in to Google"

## Usage

### 1. Email Loading

```python
from ml_pipeline.email import EmailLoader

# Initialize loader
loader = EmailLoader()

# Fetch recent emails from Gmail
emails = loader.fetch_emails(
    mailbox="INBOX",
    limit=50,
    since_days=7
)

print(f"Fetched {len(emails)} emails")

# Save to database
loader.save_to_database(emails)

# Load from database
stored_emails = loader.load_from_database(limit=100)
```

### 2. Email Classification

```python
from ml_pipeline.email import EmailClassifier

# Initialize classifier
classifier = EmailClassifier()

# Generate training data (keyword-based or Llama-based)
emails = [
    "I need my medical records from Dr. Smith for case 2024-CV-1234",
    "Settlement offer of $50,000 received from insurance company",
    "Researching precedent for slip and fall cases in shopping malls"
]

labels = classifier.generate_training_labels(emails, use_llama=False)

# Train classifier
metrics = classifier.train(emails, labels, test_size=0.2)
print(f"Accuracy: {metrics['accuracy']:.2%}")

# Classify new email
new_email = "Please send authorization for medical records"
task_type = classifier.predict(new_email)
print(f"Task type: {task_type}")

# Get probabilities
proba = classifier.predict_proba(new_email)
for task, prob in list(proba.items())[:3]:
    print(f"{task}: {prob:.1%}")
```

### 3. Email Processing

```python
from ml_pipeline.email import EmailProcessor
from datetime import datetime

# Initialize processor
processor = EmailProcessor()

# Process single email
email_text = """
Hi,

This is URGENT! I need my medical records ASAP for court.
Case number is 2024-CV-1234.

Please call me at 555-123-4567.

Very frustrated with the delay!
"""

result = processor.process_email(
    email_text,
    subject="URGENT: Medical Records Request",
    sender="client@example.com",
    sent_date=datetime.now()
)

print(f"Urgency: {result['urgency_score']:.2f}")
print(f"Sentiment: {result['sentiment']}")
print(f"Entities: {result['entities']}")
```

### 4. MLInference API (Production)

```python
from ml_pipeline.ml_inference import MLInference

# Initialize with all pipelines
ml = MLInference(load_email=True)

# Classify email
task_type = ml.classify_email("Please send medical records")
print(f"Task: {task_type}")

# Full analysis
analysis = ml.analyze_email(
    "URGENT! Need records for case 2024-CV-1234 ASAP!",
    subject="Medical Records Request",
    sender="client@example.com"
)

print(f"Task Type: {analysis['task_type']}")
print(f"Urgency: {analysis['urgency_score']:.2f}")
print(f"Sentiment: {analysis['sentiment']}")
print(f"Entities: {len(analysis['entities'])} types")

# Batch processing
emails = [
    {"body": "...", "subject": "...", "from": "..."},
    {"body": "...", "subject": "...", "from": "..."}
]
results = ml.process_email_batch(emails)
```

## Models

### Email Classifier
- **Algorithm**: TF-IDF + RandomForest
- **Features**: Unigrams + bigrams (5,000 max features)
- **Training**: Scikit-learn pipeline
- **Performance**: ~85-95% accuracy (depends on training data)
- **Model File**: `trained_models/email_classifier.pkl`

### NER (Named Entity Recognition)
- **Model**: spaCy `en_core_web_sm`
- **Entities**: PERSON, ORG, DATE, MONEY, GPE
- **Legal Entities**: Custom regex for case/claim numbers

### Sentiment Analyzer
- **Model**: DistilBERT fine-tuned on SST-2
- **Fallback**: Keyword-based sentiment (if transformers unavailable)
- **Labels**: POSITIVE, NEGATIVE, NEUTRAL

## Database Schema

Emails stored in `legal_data.communications`:

```sql
CREATE TABLE legal_data.communications (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    body TEXT,
    sent_date TIMESTAMP,
    has_attachments BOOLEAN,
    email_type TEXT,
    urgency_score FLOAT,
    sentiment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Reference

### EmailLoader

#### `fetch_emails(mailbox, limit, since_days)`
Fetch emails from Gmail IMAP.

**Parameters:**
- `mailbox` (str): Gmail folder (default: "INBOX")
- `limit` (int): Max emails to fetch (default: 100)
- `since_days` (int): Only fetch last N days (optional)

**Returns:** List of parsed email dicts

#### `save_to_database(emails)`
Save emails to PostgreSQL.

**Returns:** Number of emails saved

#### `load_from_database(limit, email_type)`
Load emails from database.

**Parameters:**
- `limit` (int): Max to load
- `email_type` (str): Filter by task type

**Returns:** List of email records

### EmailClassifier

#### `train(emails, labels, test_size=0.2)`
Train classification model.

**Returns:** Dict with metrics (accuracy, precision, recall, f1)

#### `predict(email_text)`
Predict task type for single email.

**Returns:** Task type string (e.g., "RECORDS_REQUEST")

#### `predict_proba(email_text)`
Get probability distribution over task types.

**Returns:** Dict mapping task type → probability

#### `predict_batch(emails)`
Classify multiple emails at once.

**Returns:** List of predicted task types

### EmailProcessor

#### `extract_entities(text)`
Extract named entities.

**Returns:** Dict mapping entity type → list of entities

#### `calculate_urgency(email_text, subject, sent_date)`
Calculate urgency score.

**Returns:** Float (0.0 = not urgent, 1.0 = very urgent)

#### `analyze_sentiment(text)`
Analyze email sentiment.

**Returns:** "POSITIVE", "NEGATIVE", or "NEUTRAL"

#### `process_email(email_text, subject, sender, sent_date)`
Complete email analysis.

**Returns:** Dict with entities, urgency, sentiment, action_required

## Performance

### Classification Speed
- **Single email**: ~5-10ms
- **Batch (100 emails)**: ~0.5-1s
- **Training (200 samples)**: ~2-5s

### Entity Extraction
- **spaCy NER**: ~10-20ms per email
- **Regex patterns**: <1ms per email

### Sentiment Analysis
- **DistilBERT**: ~50-100ms per email (CPU)
- **Keyword fallback**: <1ms per email

### End-to-End
- **Full analysis (classify + NER + urgency + sentiment)**: ~100-150ms per email

## Testing

Run comprehensive test suite:

```bash
cd AMD_server/ml_pipeline/email
python test_email.py
```

Tests cover:
- Email loader initialization and IMAP connectivity
- Email classification training and prediction
- Entity extraction (standard + legal entities)
- Urgency scoring with different email types
- Sentiment analysis
- End-to-end email processing

## Integration with Agents

### Evidence Sorter Agent

```python
from agents.evidence_sorter_agent import EvidenceSorterAgent
from ml_pipeline.ml_inference import MLInference

ml = MLInference()
agent = EvidenceSorterAgent(ml_inference=ml)

# Process incoming email
email = {
    "subject": "Medical Records Request",
    "body": "Please send records for John Doe...",
    "sender": "lawyer@firm.com"
}

analysis = ml.analyze_email(email['body'], subject=email['subject'])

if analysis['task_type'] == 'RECORDS_REQUEST':
    # Route to records request workflow
    agent.handle_records_request(analysis)
elif analysis['urgency_score'] > 0.7:
    # High urgency - escalate
    agent.escalate_urgent_email(analysis)
```

### Client Communication Agent

```python
# Analyze client email for routing
analysis = ml.analyze_email(client_email_text)

if analysis['sentiment'] == 'NEGATIVE' and analysis['urgency_score'] > 0.6:
    # Frustrated client with urgent issue
    priority = 'HIGH'
    assign_to_senior_paralegal()
elif analysis['action_required']:
    # Client needs response
    priority = 'MEDIUM'
    add_to_task_queue()
```

## Troubleshooting

### Gmail Authentication Fails

**Error**: "Username and Password not accepted"

**Solution**: Use App Password, not account password:
1. Enable 2FA on Google Account
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use 16-character app password in `.env`

### spaCy Model Not Found

**Error**: "Can't find model 'en_core_web_sm'"

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Low Classification Accuracy

**Causes:**
- Insufficient training data (<50 examples)
- Imbalanced classes (one type dominates)
- Generic email content (hard to classify)

**Solutions:**
1. Add more labeled examples (aim for 100-200)
2. Balance classes (20+ examples per type)
3. Use Llama-based labeling instead of keywords
4. Add domain-specific keywords to classifier

## Future Enhancements

- [ ] Email threading (group related emails)
- [ ] Attachment analysis (extract text from PDFs)
- [ ] Duplicate detection (same email forwarded multiple times)
- [ ] Auto-reply generation for common questions
- [ ] Email summarization for long threads
- [ ] Calendar event extraction (parse meeting times)
- [ ] Contact extraction (build contact database)

## License

MIT License - See main project LICENSE file.
