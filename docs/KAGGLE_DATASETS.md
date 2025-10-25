# Kaggle Dataset Loading Guide

This guide shows you how to download the 13 Kaggle datasets and load them into your PostgreSQL database.

## Prerequisites

### 1. Install Kaggle API

```bash
pip install kaggle pandas
```

### 2. Get Kaggle API Credentials

1. Go to https://www.kaggle.com/settings
2. Scroll to "API" section
3. Click "Create New API Token"
4. This downloads `kaggle.json`

### 3. Set Up Kaggle Credentials

**On your local machine:**
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

**On AMD server:**
```bash
ssh amd-knights@134.199.202.8
mkdir -p ~/.kaggle
exit

# Upload from local machine:
scp ~/.kaggle/kaggle.json amd-knights@134.199.202.8:~/.kaggle/
```

---

## Datasets to Download

The script will download **13 datasets**:

### Healthcare & Veterans (5 datasets)
1. **VHA Hospitals Timely Care Data** - Clinical measures and processes
2. **CMS Medicare** - 7,596 hospitals registered with Medicare
3. **Veteran Employment Outcomes** - Employment data by age
4. **Veterans' Lung Cancer Clinical Trial** - Survival data from VA trial
5. **US Hospital Locations** - Location and general data for hospitals

### Document OCR & Processing (7 datasets)
6. **RVLCDIP** - Document image classification
7. **FUNSD** - Form Understanding Noisy Scanned Documents
8. **SROIE Dataset v2** - Scanned receipts OCR (ICDAR 2019)
9. **PubLayNet** - Document layout generation
10. **ICDAR 2019 MLT OCR** - Multilingual scene text
11. **Denoising Dirty Documents** - Noise removal from printed text
12. **Noisy and Rotated Scanned Documents** - Angle recognition

### Audio (1 dataset)
13. **Common Voice** - 500 hours of speech recordings

---

## Running the Download Script

### On AMD Server

```bash
ssh amd-knights@134.199.202.8
cd ~/Paralegal/scraper

# Install dependencies
pip install kaggle pandas psycopg2-binary

# Make sure database is set up
python test_database.py

# Download all datasets
python load_kaggle_datasets.py
```

**This will:**
- Create `datasets` schema in PostgreSQL
- Create `kaggle_datasets` and `dataset_files` tables
- Download all 13 datasets to `~/Paralegal/scraper/kaggle_datasets/`
- Insert metadata into database
- Print download summary

---

## Expected Output

```
============================================================
Kaggle Dataset Downloader
============================================================
✓ Dataset tables created

[1/13] Processing: VHA Hospitals Timely Care Data
Category: healthcare
Description: Performance on Clinical Measures and Processes of Care
Downloading: VHA Hospitals Timely Care Data...
✓ Downloaded: VHA Hospitals Timely Care Data
✓ Metadata saved for: VHA Hospitals Timely Care Data

[2/13] Processing: CMS Medicare
...

============================================================
✓ All datasets processed!
============================================================

Download Summary:
------------------------------------------------------------
  DOWNLOADED: 13 datasets, 150 files, 2500.00 MB
```

---

## Database Schema

The script creates two tables:

### `datasets.kaggle_datasets`
Stores dataset metadata:
- `id` - Primary key
- `name` - Dataset name
- `kaggle_path` - Kaggle identifier
- `category` - healthcare, document_ocr, audio, etc.
- `description` - Dataset description
- `download_path` - Local file path
- `downloaded_at` - Timestamp
- `file_count` - Number of files
- `total_size_mb` - Total size
- `status` - downloaded, failed, pending

### `datasets.dataset_files`
Stores individual file information:
- `id` - Primary key
- `dataset_id` - Foreign key to kaggle_datasets
- `file_name` - File name
- `file_path` - Full file path
- `file_type` - Extension (.csv, .json, .png, etc.)
- `size_mb` - File size
- `rows_count` - Rows (for CSV/tabular data)
- `columns_count` - Columns (for CSV/tabular data)
- `loaded_to_table` - Target table name if loaded

---

## Query the Downloaded Datasets

```bash
sudo -u postgres psql -d paralegal_db
```

```sql
-- View all datasets
SELECT name, category, file_count, total_size_mb, status 
FROM datasets.kaggle_datasets;

-- View healthcare datasets only
SELECT name, description, file_count 
FROM datasets.kaggle_datasets 
WHERE category = 'healthcare';

-- View all CSV files
SELECT d.name, f.file_name, f.size_mb
FROM datasets.kaggle_datasets d
JOIN datasets.dataset_files f ON d.id = f.dataset_id
WHERE f.file_type = '.csv';

-- Total downloaded size
SELECT 
    COUNT(*) as total_datasets,
    SUM(file_count) as total_files,
    SUM(total_size_mb) as total_size_mb
FROM datasets.kaggle_datasets
WHERE status = 'downloaded';
```

---

## Storage Requirements

**Estimated sizes:**
- Healthcare datasets: ~500 MB
- OCR/Document datasets: ~5-10 GB (includes images)
- Audio dataset (Common Voice): ~10-15 GB

**Total:** ~15-25 GB disk space required

Make sure the AMD server has enough space:
```bash
df -h ~
```

---

## Troubleshooting

### Kaggle API not authenticated
```
OSError: Could not find kaggle.json
```
**Solution:** Follow step 2-3 above to set up credentials

### Rate limiting
```
403 Forbidden
```
**Solution:** Kaggle limits downloads. Wait a few minutes and retry.

### Out of disk space
```
No space left on device
```
**Solution:** 
```bash
# Check space
df -h ~

# Delete old datasets if needed
rm -rf ~/Paralegal/scraper/kaggle_datasets/
```

### Database connection error
```
could not connect to server
```
**Solution:** Make sure PostgreSQL is running:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

## Next Steps

After downloading, you can:

1. **Process CSV files** - Load tabular data into database tables
2. **Train OCR models** - Use document datasets for evidence sorting agent
3. **Build search** - Index hospital/medicare data for legal research
4. **Create embeddings** - Use datasets for AI agent training

---

## Manual Download (Alternative)

If the script fails, you can download datasets manually:

1. Go to each Kaggle URL
2. Click "Download"
3. Upload to server via SCP:
```bash
scp ~/Downloads/dataset.zip amd-knights@134.199.202.8:~/Paralegal/scraper/kaggle_datasets/
```

---

## Integration with AI Agents

These datasets can enhance your AI agents:

- **Legal Researcher Agent**: Search Medicare/hospital data for medical malpractice cases
- **Evidence Sorter Agent**: Train on OCR datasets to classify scanned documents
- **Records Wrangler Agent**: Use hospital locations to generate records requests

The datasets are now in your database and ready to use! 🎯
