# PostgreSQL Database Documentation

## Table of Contents
1. [Overview](#overview)
2. [Database Connection](#database-connection)
3. [Database Schemas](#database-schemas)
4. [Legal Data Schema](#legal-data-schema)
5. [Kaggle Datasets Schema](#kaggle-datasets-schema)
6. [Dataset Catalog](#dataset-catalog)
7. [Common Queries](#common-queries)
8. [Maintenance & Troubleshooting](#maintenance--troubleshooting)

---

## Overview

The **Paralegal AI** system uses PostgreSQL 16 to store legal research data, scraped documents, and training datasets for AI agents.

### Server Information
- **Host**: localhost (AMD MI300X Server: 134.199.202.8)
- **Port**: 5432
- **Database**: `paralegal_db`
- **User**: `paralegal_user`
- **Password**: `hackathon2024`

### Purpose
- Store scraped legal documents from LexisNexis
- Manage Kaggle training datasets metadata
- Track document relationships (law firms, attorneys, topics)
- Enable AI agents to query precedent data

---

## Database Connection

### Python Connection (psycopg2)
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="paralegal_db",
    user="paralegal_user",
    password="hackathon2024"
)
```

### Command Line (psql)
```bash
# As paralegal_user
psql -h localhost -U paralegal_user -d paralegal_db

# As postgres superuser (admin)
sudo -u postgres psql -d paralegal_db
```

### Configuration File (config.ini)
```ini
[database]
host = localhost
port = 5432
database = paralegal_db
username = paralegal_user
password = hackathon2024
schema = legal_data
```

---

## Database Schemas

The database uses **two main schemas** to organize tables:

| Schema | Purpose | Tables |
|--------|---------|--------|
| `legal_data` | LexisNexis scraped documents | 7 tables + 1 view |
| `datasets` | Kaggle dataset metadata | 2 tables |

---

## Legal Data Schema

### Overview
The `legal_data` schema stores documents scraped from LexisNexis Advance, including legal cases, articles, and compliance information.

### Tables

#### 1. `search_sessions`
Tracks scraping sessions and data import sessions for reproducibility.

```sql
CREATE TABLE legal_data.search_sessions (
    id SERIAL PRIMARY KEY,
    search_query TEXT,
    search_url TEXT,
    total_results INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    notes TEXT
);
```

**Fields:**
- `id`: Unique session identifier
- `search_query`: Search terms used (for LexisNexis scraping)
- `search_url`: URL of the search source
- `total_results`: Total matches found
- `scraped_at`: When scraping/import started
- `status`: 'completed', 'failed', 'in_progress', etc.
- `notes`: Additional session information

---

#### 2. `documents`
Core table storing legal documents, case files, and imported documents.

```sql
CREATE TABLE legal_data.documents (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES legal_data.search_sessions(id),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    document_type VARCHAR(100),
    jurisdiction VARCHAR(100),
    court VARCHAR(255),
    decision_date DATE,
    citation TEXT,
    url TEXT,
    summary TEXT,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique internal identifier (auto-incrementing)
- `session_id`: Links to search/import session
- `document_id`: Unique document identifier (e.g., case_number-hash for Morgan & Morgan files)
- `title`: Document title/case name
- `document_type`: 'Case Law', 'Police Report', 'Settlement Offer', 'PIP Document', 'Audio Recording', etc.
- `jurisdiction`: 'Federal', 'State: California', etc.
- `court`: Court name that issued decision
- `decision_date`: Date of ruling/publication
- `citation`: Legal citation (e.g., "123 F.3d 456")
- `url`: Source URL or file path
- `summary`: Document summary/headnotes
- `full_text`: Complete document text (extracted from PDFs)
- `created_at`: When document was created/imported
- `updated_at`: When document was last modified

**Indexes:**
```sql
CREATE INDEX idx_documents_session ON legal_data.documents(session_id);
CREATE INDEX idx_documents_type ON legal_data.documents(document_type);
CREATE INDEX idx_documents_date ON legal_data.documents(decision_date);
CREATE INDEX idx_documents_jurisdiction ON legal_data.documents(jurisdiction);
CREATE INDEX idx_documents_document_id ON legal_data.documents(document_id);
```

---

#### 3. `law_firms`
Master table of law firms.

```sql
CREATE TABLE legal_data.law_firms (
    id SERIAL PRIMARY KEY,
    firm_name VARCHAR(500) UNIQUE NOT NULL,
    address VARCHAR(500),
    city VARCHAR(255),
    state VARCHAR(100),
    country VARCHAR(100),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique firm identifier
- `firm_name`: Full law firm name (unique)
- `address`: Street address
- `city`: City location
- `state`: State/province
- `country`: Country
- `website`: Firm website URL
- `created_at`: When firm record was created

**Index:**
```sql
CREATE INDEX idx_law_firms_name ON legal_data.law_firms(firm_name);
```

---

#### 4. `document_law_firms`
Junction table linking documents to law firms.

```sql
CREATE TABLE legal_data.document_law_firms (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    law_firm_id INTEGER REFERENCES legal_data.law_firms(id) ON DELETE CASCADE,
    role VARCHAR(100),
    UNIQUE(document_id, law_firm_id, role)
);
```

**Fields:**
- `document_id`: Reference to document
- `law_firm_id`: Reference to law firm
- `role`: 'Plaintiff Counsel', 'Defendant Counsel', 'Amicus', etc.

**Indexes:**
```sql
CREATE INDEX idx_doc_firms_document ON legal_data.document_law_firms(document_id);
CREATE INDEX idx_doc_firms_firm ON legal_data.document_law_firms(law_firm_id);
```

---

#### 5. `attorneys`
Individual attorneys mentioned in documents.

```sql
CREATE TABLE legal_data.attorneys (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    firm_id INTEGER REFERENCES legal_data.law_firms(id),
    bar_number VARCHAR(50),
    specialization TEXT
);
```

**Fields:**
- `id`: Unique attorney identifier
- `full_name`: Attorney's full name
- `firm_id`: Associated law firm
- `bar_number`: State bar registration number
- `specialization`: Practice area specialty

---

#### 6. `document_attorneys`
Junction table linking documents to attorneys.

```sql
CREATE TABLE legal_data.document_attorneys (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    attorney_id INTEGER REFERENCES legal_data.attorneys(id) ON DELETE CASCADE,
    role VARCHAR(100),
    UNIQUE(document_id, attorney_id)
);
```

**Fields:**
- `document_id`: Reference to document
- `attorney_id`: Reference to attorney
- `role`: 'Lead Counsel', 'Associate', 'Judge', etc.

---

#### 7. `compliance_issues`
Tracks data compliance topics mentioned in documents.

```sql
CREATE TABLE legal_data.compliance_issues (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    issue_type VARCHAR(100),
    description TEXT,
    severity VARCHAR(50),
    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `document_id`: Reference to document
- `issue_type`: 'Privacy Violation', 'HIPAA', 'GDPR', etc.
- `description`: Details of compliance issue
- `severity`: 'Low', 'Medium', 'High', 'Critical'
- `identified_at`: When issue was detected

---

#### 8. `compliance_topics`
Master table of compliance categories.

```sql
CREATE TABLE legal_data.compliance_topics (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    regulatory_framework VARCHAR(100)
);
```

**Fields:**
- `topic_name`: Topic identifier (e.g., 'HIPAA', 'GDPR')
- `description`: Topic explanation
- `regulatory_framework`: Governing law/regulation

**Index:**
```sql
CREATE INDEX idx_compliance_topics_name ON legal_data.compliance_topics(topic_name);
```

---

#### 9. `document_topics`
Junction table linking documents to compliance topics.

```sql
CREATE TABLE legal_data.document_topics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES legal_data.compliance_topics(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2),
    UNIQUE(document_id, topic_id)
);
```

**Fields:**
- `document_id`: Reference to document
- `topic_id`: Reference to compliance topic
- `relevance_score`: 0.00 to 1.00 (how relevant topic is)

---

#### 10. `documents_summary` (VIEW)
Denormalized view for easy querying.

```sql
CREATE VIEW legal_data.documents_summary AS
SELECT 
    d.id,
    d.title,
    d.document_type,
    d.jurisdiction,
    d.decision_date,
    d.case_number,
    ARRAY_AGG(DISTINCT lf.firm_name) AS law_firms,
    ARRAY_AGG(DISTINCT ct.topic_name) AS topics,
    d.scraped_at
FROM legal_data.documents d
LEFT JOIN legal_data.document_law_firms dlf ON d.id = dlf.document_id
LEFT JOIN legal_data.law_firms lf ON dlf.firm_id = lf.id
LEFT JOIN legal_data.document_topics dt ON d.id = dt.document_id
LEFT JOIN legal_data.compliance_topics ct ON dt.topic_id = ct.id
GROUP BY d.id;
```

**Purpose**: Simplifies queries by pre-joining common relationships.

---

## Kaggle Datasets Schema

### Overview
The `datasets` schema stores metadata about downloaded Kaggle datasets used for AI training.

### Tables

#### 1. `kaggle_datasets`
Master table of Kaggle datasets.

```sql
CREATE TABLE datasets.kaggle_datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    kaggle_path VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_count INTEGER DEFAULT 0,
    total_size_mb DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT
);
```

**Fields:**
- `id`: Unique dataset identifier
- `name`: Human-readable dataset name
- `kaggle_path`: Kaggle API path (e.g., 'username/dataset-name')
- `category`: Dataset category ('healthcare', 'document_ocr', 'audio')
- `description`: Dataset purpose/contents
- `download_date`: When dataset was downloaded
- `file_count`: Number of files in dataset
- `total_size_mb`: Total size in megabytes
- `status**: 'pending', 'downloading', 'completed', 'failed'
- `error_message`: Error details if download failed

**Indexes:**
```sql
CREATE INDEX idx_kaggle_datasets_category ON datasets.kaggle_datasets(category);
CREATE INDEX idx_kaggle_datasets_status ON datasets.kaggle_datasets(status);
```

---

#### 2. `dataset_files`
Individual files within each Kaggle dataset.

```sql
CREATE TABLE datasets.dataset_files (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets.kaggle_datasets(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_mb DECIMAL(10,2),
    file_type VARCHAR(50),
    row_count INTEGER,
    column_count INTEGER,
    columns_info JSONB
);
```

**Fields:**
- `id`: Unique file identifier
- `dataset_id`: Reference to parent dataset
- `file_name`: Original filename
- `file_path`: Local storage path
- `file_size_mb`: File size in megabytes
- `file_type`: 'csv', 'json', 'parquet', 'image', etc.
- `row_count`: Number of rows (for tabular data)
- `column_count`: Number of columns (for tabular data)
- `columns_info`: JSON metadata about columns (names, types)

**Index:**
```sql
CREATE INDEX idx_dataset_files_dataset ON datasets.dataset_files(dataset_id);
```

---

## Dataset Catalog

### Healthcare & Veterans Datasets (4 datasets)

#### 1. VHA Hospitals Timely Care Data
- **Kaggle Path**: `thedevastator/vha-hospitals-timely-care-data`
- **Category**: Healthcare
- **Size**: ~5-10 MB
- **Description**: Performance on Clinical Measures and Processes of Care
- **Use Case**: Train Legal Researcher Agent on healthcare compliance cases
- **Key Fields**: Hospital metrics, care quality indicators, patient outcomes

#### 2. Veteran Employment Outcomes
- **Kaggle Path**: `mpwolke/cusersmarildownloadsvetcsv`
- **Category**: Veterans
- **Size**: ~1-5 MB
- **Description**: Veteran Employment Outcomes by age demographics
- **Use Case**: Legal cases involving veteran employment discrimination
- **Key Fields**: Age groups, employment status, demographic breakdowns

#### 3. Veterans Lung Cancer Clinical Trial
- **Kaggle Path**: `harivpatel/veterans-lung-cancer-clinical-trial-dataset`
- **Category**: Medical
- **Size**: ~1-2 MB
- **Description**: Survival data from Veterans Administration Lung Cancer Trial
- **Use Case**: Medical malpractice and VA healthcare litigation research
- **Key Fields**: Treatment groups, survival times, patient characteristics

#### 4. US Hospital Locations
- **Kaggle Path**: `andrewmvd/us-hospital-locations`
- **Category**: Healthcare
- **Size**: ~5-10 MB
- **Description**: Location and general data for 7,596 hospitals
- **Use Case**: Jurisdiction mapping for healthcare litigation
- **Key Fields**: Hospital coordinates, addresses, facility types

---

### Document OCR Datasets (6 datasets)

These datasets train the **Evidence Sorter Agent** on document classification and text extraction.

#### 5. RVLCDIP
- **Kaggle Path**: `abdellatifsassioui/rvlcdip`
- **Category**: Document OCR
- **Size**: ~400-800 MB
- **Description**: RVL-CDIP (Ryerson Vision Lab Complex Document Information Processing) - 400,000 grayscale document images in 16 classes
- **Use Case**: Train Evidence Sorter to classify legal document types
- **Classes**: Letter, form, email, handwritten, advertisement, scientific report, scientific publication, specification, file folder, news article, budget, invoice, presentation, questionnaire, resume, memo

#### 6. FUNSD
- **Kaggle Path**: `aravindram11/funsdform-understanding-noisy-scanned-documents`
- **Category**: Document OCR
- **Size**: ~30-50 MB
- **Description**: Form Understanding in Noisy Scanned Documents - 199 fully annotated forms
- **Use Case**: Extract structured data from legal forms (intake forms, court documents)
- **Key Features**: Entity recognition, form structure understanding, noisy document handling

#### 7. SROIE Dataset v2
- **Kaggle Path**: `urbikn/sroie-datasetv2`
- **Category**: Document OCR
- **Size**: ~100-200 MB
- **Description**: ICDAR 2019 SROIE (Scanned Receipts OCR and Information Extraction)
- **Use Case**: Extract key information from receipts/invoices in billing disputes
- **Tasks**: Text localization, OCR, key information extraction

#### 8. PubLayNet
- **Kaggle Path**: `captaintushar/publaynet-dataset`
- **Category**: Document OCR
- **Size**: ~9-12 GB (LARGEST dataset)
- **Description**: 360,000+ document images for layout detection
- **Use Case**: Understand document structure (headers, paragraphs, tables, figures)
- **Classes**: Text, title, list, table, figure
- **Note**: This is the largest dataset and will take longest to download

#### 9. ICDAR 2019 MLT OCR
- **Kaggle Path**: `zubairalibhutto/mlt-19-ocr-dataset`
- **Category**: Document OCR
- **Size**: ~500 MB - 1 GB
- **Description**: Multilingual Scene Text Dataset from ICDAR 2019
- **Use Case**: Handle multilingual legal documents (immigration cases)
- **Languages**: 10+ languages including English, Chinese, Arabic, Hindi

#### 10. Noisy and Rotated Scanned Documents
- **Kaggle Path**: `sthabile/noisy-and-rotated-scanned-documents`
- **Category**: Document OCR
- **Size**: ~50-100 MB
- **Description**: Predictive model for recognizing angles of scanned documents
- **Use Case**: Auto-rotate misaligned scanned documents before OCR
- **Task**: Rotation angle prediction, image alignment

---

### Audio Dataset (1 dataset)

#### 11. Common Voice
- **Kaggle Path**: `mozillaorg/common-voice`
- **Category**: Audio
- **Size**: ~3-5 GB
- **Description**: 500 hours of speech recordings with speaker demographics
- **Use Case**: Train audio transcription for call recordings (Client Communication Agent)
- **Languages**: Multiple languages
- **Metadata**: Age, gender, accent
- **Format**: MP3 audio files + transcripts

---

## Morgan & Morgan Case Files

### Overview
Real-world legal case files from Morgan & Morgan law firm, loaded into the database for AI agent training and demonstration.

### Statistics
- **Cases**: 4 active personal injury cases
- **Total Documents**: 54 files
- **PDFs Processed**: 34 (with text extraction)
- **Audio Recordings**: 16 client call recordings
- **Session ID**: 5

### Case Files

#### File 1: Case #12564888
- **Documents**: 4 files
- **Types**: Police Report, PIP payout, Settlement Offer, Property Damage
- **Key Content**: Crash report, insurance payouts, property damage estimates

#### File 2: Case #9232459
- **Documents**: 5 files
- **Types**: Police Reports, Property Damage, Total Loss Estimates
- **Key Content**: Crash documentation, vehicle total loss, property damage estimates

#### File 3: Case #11869964
- **Documents**: 36 files (largest case)
- **Types**: Settlement Offers (8), Audio Recordings (7), PIP Documents, Medical Liens, Insurance Policies, Property Damage
- **Key Content**:
  - Settlement negotiation sequence: $22k → $24k → $25k → $28k
  - Client call recordings (first call, follow-ups, demand discussions)
  - Medicare and Optum medical liens
  - Progressive and Geico insurance policies and declarations
  - PIP exhaustion letters
- **Audio Files**: First call, 2nd call, 3rd call, 4th call, call about demand, call about CRN, call about tender, 5 days after demand, call about offer

#### File 4: Case #9840025
- **Documents**: 9 files
- **Types**: Settlement Offers, Audio Recordings, Police Report, PIP Documents
- **Key Content**:
  - Settlement offer from Auto-Owners Insurance ($18k)
  - Client call recordings (first call through 4th call)
  - Police crash report
  - PIP payment logs
- **Audio Files**: First call, 2nd call, 3rd call, 4th call, call about demand, low offer lawsuit discussion

### Document Type Breakdown

| Document Type | Count | Use Case |
|---------------|-------|----------|
| Settlement Offer | 11 | Train negotiation pattern recognition |
| Audio Recording | 10 | Client communication transcription |
| Legal Document | 9 | General legal document classification |
| Medical Lien | 4 | Healthcare billing and liens |
| PIP Document | 4 | Personal Injury Protection claims |
| Police Report | 4 | Incident documentation |
| Other Document | 4 | Photos and miscellaneous |
| Property Damage | 3 | Vehicle damage assessment |
| Demand Letter | 3 | Legal demand documentation |
| Insurance Document | 1 | Policy information |
| Tender Document | 1 | Insurance tender offers |

### AI Training Applications

**Legal Researcher Agent:**
- Study settlement negotiation patterns
- Analyze PIP claim workflows
- Research medical lien handling

**Evidence Sorter Agent:**
- Document classification (police reports vs. settlement offers vs. liens)
- Text extraction from scanned PDFs
- File organization by case and document type

**Client Communication Agent:**
- Audio transcription of client calls (16 recordings)
- Timeline reconstruction (first call → follow-ups → demand → settlement)
- Communication pattern analysis

**Records Agent:**
- Track Morgan & Morgan firm involvement
- Link documents to specific cases
- Maintain case file organization

### Query Examples

```sql
-- Get all Morgan & Morgan documents
SELECT document_type, COUNT(*) 
FROM legal_data.documents 
WHERE session_id = 5 
GROUP BY document_type;

-- Find settlement offers with amounts
SELECT title, document_type, LEFT(full_text, 200)
FROM legal_data.documents
WHERE document_type = 'Settlement Offer' AND session_id = 5;

-- Get audio recordings for transcription
SELECT document_id, title, url
FROM legal_data.documents
WHERE document_type = 'Audio Recording' AND session_id = 5;
```

---

## Dataset Storage Summary

| Category | Datasets | Est. Total Size | Primary Agent |
|----------|----------|-----------------|---------------|
| Healthcare/Veterans | 4 | 20-30 MB | Legal Researcher |
| Document OCR | 6 | 10-14 GB | Evidence Sorter |
| Audio | 1 | 3-5 GB | Client Comm |
| **Morgan & Morgan** | **4 cases** | **46 MB (54 files)** | **All Agents** |
| **TOTAL** | **11 + 4 cases** | **~15-20 GB** | All Agents |

**Note**: Two datasets failed to download and were removed:
- ~~CMS Medicare Open Payments~~ (download error)
- ~~Denoising Dirty Documents~~ (not found on Kaggle)

**Download Time Estimates (Kaggle datasets only):**
- Sequential (1 worker): 30-60 minutes
- Parallel (8 workers): 5-10 minutes
- Parallel (16 workers): 3-7 minutes
- Parallel (32 workers): 2-5 minutes

**Storage Location**: `~/Paralegal/AMD_server/scraper/kaggle_datasets/`  
**Morgan & Morgan Files**: `~/Morgan&Morgan/` (uploaded to AMD server)

---

## Common Queries

### Legal Data Queries

#### Get all documents by jurisdiction
```sql
SELECT id, title, document_type, decision_date, court_name
FROM legal_data.documents
WHERE jurisdiction = 'Federal'
ORDER BY decision_date DESC;
```

#### Find documents by law firm
```sql
SELECT d.title, d.document_type, d.decision_date, dlf.role
FROM legal_data.documents d
JOIN legal_data.document_law_firms dlf ON d.id = dlf.document_id
JOIN legal_data.law_firms lf ON dlf.law_firm_id = lf.id
WHERE lf.firm_name LIKE '%Morgan & Morgan%';
```

#### Search documents by compliance topic
```sql
SELECT d.title, ct.topic_name, dt.relevance_score
FROM legal_data.documents d
JOIN legal_data.document_topics dt ON d.id = dt.document_id
JOIN legal_data.compliance_topics ct ON dt.topic_id = ct.id
WHERE ct.topic_name = 'HIPAA'
ORDER BY dt.relevance_score DESC;
```

#### Get document summary with all relationships
```sql
SELECT * FROM legal_data.documents_summary
WHERE document_type = 'Case Law'
ORDER BY decision_date DESC
LIMIT 10;
```

#### Get Morgan & Morgan case documents
```sql
SELECT d.document_id, d.title, d.document_type, d.created_at
FROM legal_data.documents d
WHERE d.session_id = 5
ORDER BY d.document_type, d.title;
```

#### Find settlement offers
```sql
SELECT title, LEFT(full_text, 200) as preview
FROM legal_data.documents
WHERE document_type = 'Settlement Offer'
ORDER BY created_at DESC;
```

#### Count documents by type
```sql
SELECT document_type, COUNT(*) as count
FROM legal_data.documents
GROUP BY document_type
ORDER BY count DESC;
```

---

### Kaggle Dataset Queries

#### List all downloaded datasets
```sql
SELECT id, name, category, file_count, total_size_mb, status
FROM datasets.kaggle_datasets
ORDER BY category, name;
```

#### Get datasets by category
```sql
SELECT name, description, total_size_mb, download_date
FROM datasets.kaggle_datasets
WHERE category = 'document_ocr'
ORDER BY total_size_mb DESC;
```

#### Find failed downloads
```sql
SELECT name, kaggle_path, error_message
FROM datasets.kaggle_datasets
WHERE status = 'failed';
```

#### Get file details for a specific dataset
```sql
SELECT df.file_name, df.file_size_mb, df.file_type, df.row_count
FROM datasets.dataset_files df
JOIN datasets.kaggle_datasets kd ON df.dataset_id = kd.id
WHERE kd.name = 'PubLayNet'
ORDER BY df.file_size_mb DESC;
```

#### Calculate total storage used
```sql
SELECT 
    category,
    COUNT(*) as dataset_count,
    SUM(file_count) as total_files,
    SUM(total_size_mb) as total_size_mb
FROM datasets.kaggle_datasets
WHERE status = 'completed'
GROUP BY category;
```

#### Get dataset download progress
```sql
SELECT 
    name,
    status,
    ROUND((file_count::DECIMAL / NULLIF(total_size_mb, 0)) * 100, 2) as completion_pct,
    download_date
FROM datasets.kaggle_datasets
ORDER BY download_date DESC;
```

---

## Maintenance & Troubleshooting

### Database Statistics

#### Check table sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('legal_data', 'datasets')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Count rows in all tables
```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname IN ('legal_data', 'datasets')
ORDER BY n_live_tup DESC;
```

---

### Vacuum and Analyze

#### Optimize database performance
```sql
-- Reclaim storage and update statistics
VACUUM ANALYZE legal_data.documents;
VACUUM ANALYZE datasets.kaggle_datasets;

-- Full vacuum (requires exclusive lock)
VACUUM FULL legal_data.documents;
```

---

### Backup and Restore

#### Backup entire database
```bash
# Backup to SQL file
pg_dump -h localhost -U paralegal_user -d paralegal_db > paralegal_db_backup.sql

# Backup to compressed format
pg_dump -h localhost -U paralegal_user -d paralegal_db -Fc > paralegal_db_backup.dump
```

#### Restore from backup
```bash
# Restore from SQL file
psql -h localhost -U paralegal_user -d paralegal_db < paralegal_db_backup.sql

# Restore from compressed format
pg_restore -h localhost -U paralegal_user -d paralegal_db paralegal_db_backup.dump
```

#### Backup specific schema
```bash
pg_dump -h localhost -U paralegal_user -d paralegal_db -n legal_data > legal_data_backup.sql
pg_dump -h localhost -U paralegal_user -d paralegal_db -n datasets > datasets_backup.sql
```

---

### Permissions Management

#### Grant read-only access to new user
```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'readonly_password';

-- Grant schema access
GRANT USAGE ON SCHEMA legal_data TO readonly_user;
GRANT USAGE ON SCHEMA datasets TO readonly_user;

-- Grant table access
GRANT SELECT ON ALL TABLES IN SCHEMA legal_data TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA datasets TO readonly_user;
```

#### Revoke permissions
```sql
REVOKE ALL ON SCHEMA legal_data FROM readonly_user;
DROP USER readonly_user;
```

---

### Common Issues

#### Connection Refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Enable auto-start
sudo systemctl enable postgresql
```

#### Permission Denied Errors
```sql
-- Grant schema usage
GRANT USAGE ON SCHEMA legal_data TO paralegal_user;

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA legal_data TO paralegal_user;

-- Grant sequence permissions (for auto-increment)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA legal_data TO paralegal_user;
```

#### Out of Disk Space
```bash
# Check disk usage
df -h

# Find large tables
sudo -u postgres psql -d paralegal_db -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"

# Clean up old data
DELETE FROM legal_data.documents WHERE scraped_at < NOW() - INTERVAL '30 days';
VACUUM FULL;
```

---

## Performance Optimization

### Create Indexes for Common Queries

```sql
-- Full-text search on document text
CREATE INDEX idx_documents_fulltext ON legal_data.documents 
USING gin(to_tsvector('english', full_text));

-- Search documents by text
SELECT title, document_type 
FROM legal_data.documents
WHERE to_tsvector('english', full_text) @@ to_tsquery('english', 'healthcare & compliance');
```

### Partitioning Large Tables

```sql
-- Partition documents by year (for very large datasets)
CREATE TABLE legal_data.documents_2024 PARTITION OF legal_data.documents
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE legal_data.documents_2025 PARTITION OF legal_data.documents
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## AI Agent Integration

### Legal Researcher Agent
- **Primary Tables**: `documents`, `compliance_topics`, `document_topics`
- **Datasets Used**: Healthcare datasets (CMS Medicare, VHA Hospitals)
- **Query Pattern**: Search by jurisdiction, topic, date range

### Evidence Sorter Agent
- **Primary Tables**: `dataset_files` (document OCR datasets)
- **Datasets Used**: RVLCDIP, FUNSD, PubLayNet
- **Task**: Document classification, text extraction

### Client Communication Agent
- **Primary Tables**: `documents` (for context), `dataset_files` (audio)
- **Datasets Used**: Common Voice
- **Task**: Audio transcription, email/text analysis

### Records Agent
- **Primary Tables**: `law_firms`, `attorneys`, `document_law_firms`
- **Query Pattern**: Find records by law firm, attorney, case number

---

## Appendix

### Schema Diagram

```
legal_data Schema:
┌─────────────────────┐
│  search_sessions    │
└──────────┬──────────┘
           │
           │ 1:N
           ▼
┌─────────────────────┐      ┌──────────────────┐
│     documents       │◄────►│   law_firms      │
└──────────┬──────────┘  N:M └──────┬───────────┘
           │                        │
           │ 1:N                    │ 1:N
           ▼                        ▼
┌─────────────────────┐      ┌──────────────────┐
│ compliance_issues   │      │    attorneys     │
└─────────────────────┘      └──────────────────┘
           │                        
           │ N:M                    
           ▼                        
┌─────────────────────┐      
│ compliance_topics   │      
└─────────────────────┘      

datasets Schema:
┌──────────────────────┐
│  kaggle_datasets     │
└───────────┬──────────┘
            │
            │ 1:N
            ▼
┌──────────────────────┐
│   dataset_files      │
└──────────────────────┘
```

### Contact & Support

- **Database Admin**: AMD Server (amd-knights@134.199.202.8)
- **Config File**: `~/Paralegal/AMD_server/scraper/config.ini`
- **Setup Script**: `~/Paralegal/AMD_server/setup/setup_scraper.sh`
- **Dataset Loader**: `~/Paralegal/AMD_server/scraper/load_kaggle_datasets.py`
- **Morgan & Morgan Loader**: `~/Paralegal/AMD_server/scraper/load_morgan_files.py`

### Version History

- **v2.0** (2025-10-25): Schema corrections and Morgan & Morgan integration
  - Fixed all table schemas to match actual database implementation
  - Corrected column names: document_id, url, court, law_firm_id, created_at, updated_at
  - Added Morgan & Morgan case files (54 documents, 4 cases)
  - Removed failed Kaggle datasets (CMS Medicare, Denoising Dirty Documents)
  - Updated to 11 successfully downloaded Kaggle datasets
  - Added comprehensive Morgan & Morgan documentation section
  
- **v1.0** (2025-10-25): Initial database setup
  - PostgreSQL 16 installation
  - Legal data schema (7 tables + 1 view)
  - Kaggle datasets schema (2 tables)
  - 13 Kaggle datasets attempted (11 successful)

---

**Last Updated**: October 25, 2025  
**Hackathon**: AI Legal Tender (Morgan & Morgan Challenge)  
**Team**: BonelessWater
