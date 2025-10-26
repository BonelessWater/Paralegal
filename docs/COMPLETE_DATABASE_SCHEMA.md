# Complete Database Schema Documentation

**Last Updated**: October 25, 2025  
**Database**: paralegal_db  
**PostgreSQL Version**: 16+

---

## Table of Contents

1. [Overview](#overview)
2. [Schema: case_management](#schema-case_management) ⭐ NEW
3. [Schema: legal_data](#schema-legal_data)
4. [Schema: client_comms](#schema-client_comms)
5. [Schema: datasets](#schema-datasets)
6. [Setup Instructions](#setup-instructions)
7. [Common Queries](#common-queries)

---

## Overview

The Paralegal AI database uses **four main schemas**:

| Schema | Purpose | Tables |
|--------|---------|--------|
| `case_management` ⭐ | **Clients, cases, injuries, insurance, tasks** | **14 tables** |
| `legal_data` | Legal research documents, cases, compliance | 7 tables |
| `client_comms` | Client communications (calls, SMS, emails) | 10 tables |
| `datasets` | Kaggle dataset metadata | 2 tables |

---

## Schema: case_management ⭐ NEW

**Purpose**: Core business entities - clients, cases, injuries, medical records, insurance, tasks, and notes.

### Key Tables

#### 1. `clients`
Client personal information and contact details.

**Key Columns**:
- `client_id` (VARCHAR UNIQUE) - External client ID
- `first_name`, `last_name`, `middle_name`
- `email`, `phone_primary`, `phone_secondary`, `phone_mobile`
- `address_*` - Full address fields
- `date_of_birth`, `ssn_encrypted`
- `client_status` ('active', 'inactive', 'potential', 'former')
- `client_source` ('referral', 'advertisement', 'website')
- `intake_date`, `preferred_language`, `preferred_contact_method`

#### 2. `cases` ⭐ CORE TABLE
Legal cases with complete details.

**Key Columns**:
- `case_id` (VARCHAR UNIQUE) - Case number
- `client_id` → References `clients(client_id)`
- `case_name`, `case_type`, `case_subtype`, `case_status`
- **Dates**: `incident_date`, `filing_date`, `case_opened_date`, `settlement_date`, `trial_date`
- **Parties**: `opposing_party_name`, `opposing_counsel_name`
- **Financial**: `damages_claimed`, `settlement_amount`, `attorney_fees`, `contingency_percentage`
- **Assignments**: `primary_attorney`, `assigned_paralegal`, `case_manager`
- **Details**: `incident_description`, `injuries_description`, `liability_assessment`, `settlement_recommendation`
- **Workflow**: `case_phase`, `next_action`, `next_deadline`

#### 3. `injuries`
Injuries sustained by clients.

**Columns**: injury_type, injury_location, injury_severity, icd10_code, requires_surgery, permanent_disability, etc.

#### 4. `medical_providers`
Medical treatment providers and records.

**Columns**: provider_type, provider_name, total_visits, total_billed, records_requested, records_received, etc.

#### 5. `insurance_claims`
Insurance claims related to cases.

**Columns**: claim_number, insurance_company_name, policy_number, claim_amount, settlement_offer, policy_limits, etc.

#### 6. `case_events`
Timeline of case events.

**Columns**: event_type, event_date, event_description, attendees, event_status, is_deadline, etc.

#### 7. `case_tasks`
Tasks and deadlines for case management.

**Columns**: task_name, assigned_to, due_date, task_status, priority, is_critical_deadline, etc.

#### 8. `case_notes`
Notes and journal entries.

**Columns**: note_type, note_content, author, is_confidential, is_privileged, etc.

#### 9. `attorneys`
Law firm attorneys and staff.

**Columns**: attorney_id, bar_number, role, department, practice_areas, employment_status, etc.

### Views

- `active_cases_summary` - Active cases with client info
- `case_financials` - Financial summary per case
- `attorney_workload` - Case count and workload per attorney

---

## Schema: legal_data

**Purpose**: Stores legal documents scraped from LexisNexis and imported case files (Morgan & Morgan).

### Tables

#### 1. `search_sessions`
Tracks scraping/import sessions.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `search_query` (TEXT) - Search terms or import description
- `search_url` (TEXT) - Source URL
- `total_results` (INTEGER) - Number of documents
- `scraped_at` (TIMESTAMP) - When session occurred
- `status` (VARCHAR(50)) - 'completed', 'failed', 'in_progress'
- `notes` (TEXT)

#### 2. `documents`
**Main table** for all legal documents.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `session_id` (INTEGER) → References `search_sessions(id)`
- `document_id` (VARCHAR(255) UNIQUE) - External identifier
- `title` (TEXT) - Document title/case name
- `document_type` (VARCHAR(100)) - 'Police Report', 'Settlement Offer', 'Case Law', 'PIP Document', 'Audio Recording', etc.
- `jurisdiction` (VARCHAR(255)) - 'Federal', 'State: Florida', etc.
- `court` (VARCHAR(255)) - Court name
- `decision_date` (DATE) - Date of ruling/document
- `citation` (TEXT) - Legal citation
- `url` (TEXT) - Source URL or file path
- `summary` (TEXT) - Document summary
- `full_text` (TEXT) - **Complete document text** (used for embeddings)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Important**: The `full_text` column is what gets embedded for RAG search!

#### 3. `law_firms`
Master table of law firms.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `firm_name` (VARCHAR(500) UNIQUE)
- `address`, `city`, `state`, `country` (TEXT/VARCHAR)
- `website` (VARCHAR(255))
- `created_at` (TIMESTAMP)

#### 4. `document_law_firms`
Junction table linking documents to law firms.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `document_id` (INTEGER) → References `documents(id)`
- `law_firm_id` (INTEGER) → References `law_firms(id)`
- `role` (VARCHAR(100)) - 'plaintiff', 'defendant', 'counsel'

#### 5. `compliance_topics`
Master table of compliance/legal topics.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `topic_name` (VARCHAR(255) UNIQUE)
- `description` (TEXT)
- `category` (VARCHAR(100))

#### 6. `document_topics`
Junction table linking documents to topics.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `document_id` (INTEGER) → References `documents(id)`
- `topic_id` (INTEGER) → References `compliance_topics(id)`
- `relevance_score` (DECIMAL(3,2)) - 0.00 to 1.00

#### 7. `documents_summary` (VIEW)
Pre-joined view for easy querying.

---

## Schema: client_comms

**Purpose**: Stores all client communications with AI-powered analysis.

### Tables

#### 1. `call_recordings`
Metadata for client call recordings.

**Key Columns**:
- `id` (SERIAL PRIMARY KEY)
- `call_id` (VARCHAR(255) UNIQUE)
- `client_id` (VARCHAR(255)) - Links to client
- `case_id` (VARCHAR(255)) - Links to legal case
- `phone_number` (VARCHAR(50))
- `call_direction` ('inbound'/'outbound')
- `call_duration_seconds` (INTEGER)
- `call_date` (TIMESTAMP)
- `recording_file_path` (TEXT) - Path to audio file
- `recording_url` (TEXT)
- `audio_format` (VARCHAR(20)) - 'mp3', 'm4a', 'wav'
- `caller_name`, `agent_name` (VARCHAR(255))
- `department` (VARCHAR(100)) - 'intake', 'case_management', etc.
- `priority` ('low', 'medium', 'high', 'urgent')
- `tags` (TEXT[]) - Array of tags
- `metadata` (JSONB) - Flexible additional data

#### 2. `call_transcripts`
AI-generated transcripts of calls.

**Key Columns**:
- `id` (SERIAL PRIMARY KEY)
- `call_id` (VARCHAR(255)) → References `call_recordings(call_id)`
- `transcript_text` (TEXT) - **Full transcript** (used for embeddings)
- `transcription_service` ('whisper', 'openai', 'aws')
- `transcription_model` ('whisper-large-v3', etc.)
- `confidence_score` (DECIMAL(3,2))
- `language` (VARCHAR(10))
- `speaker_diarization` (BOOLEAN) - True if speakers identified
- `num_speakers` (INTEGER)
- `transcript_segments` (JSONB) - Detailed segments with timestamps

#### 3. `transcript_speakers`
Speaker segments (when diarization enabled).

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `transcript_id` (INTEGER) → References `call_transcripts(id)`
- `speaker_label` ('Speaker 1', 'Client', 'Agent')
- `speaker_role` ('client', 'attorney', 'paralegal')
- `start_time`, `end_time` (DECIMAL) - Seconds from start
- `text` (TEXT) - Speaker's words
- `confidence` (DECIMAL(3,2))

#### 4. `sms_messages`
SMS/text messages.

**Key Columns**:
- `id` (SERIAL PRIMARY KEY)
- `message_id` (VARCHAR(255) UNIQUE)
- `client_id`, `case_id` (VARCHAR(255))
- `from_phone`, `to_phone` (VARCHAR(50))
- `message_direction` ('inbound'/'outbound')
- `message_text` (TEXT) - **Message content** (used for embeddings)
- `message_date` (TIMESTAMP)
- `message_status` ('sent', 'delivered', 'read', 'failed')
- `platform` ('twilio', 'vonage', etc.)
- `has_media` (BOOLEAN)
- `media_urls` (TEXT[])
- `sentiment_score` (DECIMAL(3,2)) - -1.00 to 1.00
- `sentiment_label` ('positive', 'neutral', 'negative', 'urgent')
- `automated_response` (BOOLEAN)
- `thread_id` (VARCHAR(255)) - Groups related messages

#### 5. `emails`
Email communications.

**Key Columns**:
- `id` (SERIAL PRIMARY KEY)
- `email_id` (VARCHAR(255) UNIQUE)
- `client_id`, `case_id` (VARCHAR(255))
- `from_email` (VARCHAR(255))
- `to_emails`, `cc_emails`, `bcc_emails` (TEXT[]) - Arrays
- `subject` (TEXT)
- `body_text` (TEXT) - **Plain text body** (used for embeddings)
- `body_html` (TEXT) - HTML version
- `email_direction` ('inbound'/'outbound')
- `email_date` (TIMESTAMP)
- `has_attachments` (BOOLEAN)
- `attachment_count` (INTEGER)
- `category` ('new_inquiry', 'case_update', 'billing', etc.)
- `sentiment_score`, `sentiment_label` (same as SMS)
- `thread_id` (VARCHAR(255))
- `in_reply_to` (VARCHAR(255)) - Parent email ID

#### 6. `email_attachments`
Email attachments with OCR/extraction.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `email_id` (VARCHAR(255)) → References `emails(email_id)`
- `attachment_name` (VARCHAR(500))
- `file_path`, `file_url` (TEXT)
- `file_size_bytes` (BIGINT)
- `mime_type` (VARCHAR(100))
- `extracted_text` (TEXT) - **OCR/PDF extraction** (used for embeddings)
- `document_type` (VARCHAR(100)) - Classification result

#### 7. `ai_analysis`
AI-powered analysis of all communications.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `communication_type` ('call', 'sms', 'email')
- `communication_id` (VARCHAR(255)) - ID from respective table
- `analysis_type` ('summary', 'sentiment', 'action_items', 'classification')
- `analysis_result` (JSONB) - Structured analysis
- `confidence_score` (DECIMAL(3,2))
- `model_used` ('gpt-4', 'claude-3', 'llama-70b')
- `processing_time_seconds` (DECIMAL)
- `created_by` (VARCHAR(100))

#### 8. `action_items`
Extracted action items from communications.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `communication_type`, `communication_id` (VARCHAR)
- `action_description` (TEXT)
- `assigned_to` (VARCHAR(255)) - Attorney/staff
- `due_date` (DATE)
- `priority` ('low', 'medium', 'high', 'urgent')
- `status` ('pending', 'in_progress', 'completed', 'cancelled')
- `completed_at` (TIMESTAMP)

### Views

#### `all_communications`
Union of all communication types in chronological order.

**Columns**: type, id, client_id, case_id, date, from_name, to_name, subject, content, status, priority, tags

#### `case_communication_summary`
Aggregate statistics by case.

**Columns**: case_id, total_calls, total_sms, total_emails, total_communications, last_communication_date, first_communication_date

---

## Schema: datasets

**Purpose**: Metadata for Kaggle training datasets.

### Tables

#### 1. `kaggle_datasets`
Dataset metadata.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `dataset_name` (VARCHAR(255))
- `dataset_url` (TEXT)
- `description` (TEXT)
- `file_count` (INTEGER)
- `total_size_gb` (DECIMAL(10,2))
- `download_date` (TIMESTAMP)
- `local_path` (TEXT)

#### 2. `kaggle_dataset_files`
Individual files within datasets.

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `dataset_id` (INTEGER) → References `kaggle_datasets(id)`
- `file_name` (VARCHAR(500))
- `file_path` (TEXT)
- `file_size_bytes` (BIGINT)
- `file_type` (VARCHAR(50))
- `loaded_to_db` (BOOLEAN)

---

## Setup Instructions

### 1. Create All Schemas

```bash
# On AMD server
cd /home/amd-knights/Paralegal/AMD_server/scraper

# Create case_management schema (clients, cases, tasks)
psql -h localhost -U paralegal_user -d paralegal_db -f case_management_schema.sql

# Create legal_data schema (documents, law firms)
psql -h localhost -U paralegal_user -d paralegal_db -f database_schema.sql

# Create client_comms schema (calls, SMS, emails)
psql -h localhost -U paralegal_user -d paralegal_db -f client_communications_schema.sql
```

### 2. Verify Schema Creation

```bash
python3 ../ml_pipeline/inspect_database.py
```

Should show:
- `case_management` schema with 14 tables ⭐ NEW
- `legal_data` schema with 7 tables
- `client_comms` schema with 10 tables
- `datasets` schema with 2 tables

---

## Common Queries

### Legal Data Queries

#### Get all Morgan & Morgan documents
```sql
SELECT id, document_id, title, document_type, full_text
FROM legal_data.documents
WHERE session_id = 5
AND full_text IS NOT NULL;
```

#### Count documents by type
```sql
SELECT document_type, COUNT(*) as count
FROM legal_data.documents
WHERE session_id = 5
GROUP BY document_type
ORDER BY count DESC;
```

### Client Communications Queries

#### Get all communications for a case
```sql
SELECT * FROM client_comms.all_communications
WHERE case_id = 'CASE-12345'
ORDER BY date DESC;
```

#### Find urgent messages
```sql
SELECT * FROM client_comms.sms_messages
WHERE sentiment_label = 'urgent'
OR priority = 'urgent'
ORDER BY message_date DESC;
```

#### Get call transcripts with high confidence
```sql
SELECT 
    cr.call_id,
    cr.caller_name,
    cr.call_date,
    ct.transcript_text,
    ct.confidence_score
FROM client_comms.call_recordings cr
JOIN client_comms.call_transcripts ct ON cr.call_id = ct.call_id
WHERE ct.confidence_score >= 0.85
ORDER BY cr.call_date DESC;
```

### RAG Embedding Queries

#### Get all text sources for embeddings
```sql
-- Legal documents
SELECT 
    'legal_doc' as source_type,
    document_id as source_id,
    title,
    document_type,
    full_text as text_content
FROM legal_data.documents
WHERE full_text IS NOT NULL

UNION ALL

-- Call transcripts
SELECT 
    'call_transcript' as source_type,
    call_id as source_id,
    cr.caller_name as title,
    'Call Transcript' as document_type,
    ct.transcript_text as text_content
FROM client_comms.call_transcripts ct
JOIN client_comms.call_recordings cr ON ct.call_id = cr.call_id

UNION ALL

-- SMS messages
SELECT 
    'sms' as source_type,
    message_id as source_id,
    sender_name as title,
    'SMS Message' as document_type,
    message_text as text_content
FROM client_comms.sms_messages

UNION ALL

-- Emails
SELECT 
    'email' as source_type,
    email_id as source_id,
    subject as title,
    'Email' as document_type,
    body_text as text_content
FROM client_comms.emails
WHERE body_text IS NOT NULL;
```

---

## Data Sources for RAG

**Text columns that should be embedded**:

1. **legal_data.documents.full_text** ✅ Currently implemented
2. **client_comms.call_transcripts.transcript_text** 🔜 Add next
3. **client_comms.sms_messages.message_text** 🔜 Add next
4. **client_comms.emails.body_text** 🔜 Add next
5. **client_comms.email_attachments.extracted_text** 🔜 OCR content

---

## Maintenance

### Vacuum & Analyze
```sql
VACUUM ANALYZE legal_data.documents;
VACUUM ANALYZE client_comms.call_transcripts;
VACUUM ANALYZE client_comms.sms_messages;
VACUUM ANALYZE client_comms.emails;
```

### Reindex Full Text Search
```sql
REINDEX INDEX idx_transcript_text;
REINDEX INDEX idx_sms_text;
REINDEX INDEX idx_emails_subject;
REINDEX INDEX idx_emails_body;
```

---

**For questions or schema changes, see**: /AMD_server/scraper/database_schema.sql and client_communications_schema.sql
