# Snowflake Integration for AI Legal Tender

## ⚡ Quick Setup (5 Minutes)

Complete Snowflake integration for your LexisNexis scraper and AI agents.

---

## Prerequisites

- ✅ Snowflake account created (you have: **GUWYXHN-OF53265**)
- ✅ Login credentials (username: **IMDANIAL**)
- ✅ Python 3.8+ installed
- ✅ Internet connection

---

## Step 1: Install Snowflake Connector (1 minute)

### On Your Local Mac:
```bash
cd /Users/ilandanial/Paralegal
pip install snowflake-connector-python snowflake-sqlalchemy
```

### On AMD Server:
```bash
ssh amd-knights@134.199.202.8
cd ~/Paralegal
pip install snowflake-connector-python snowflake-sqlalchemy
```

---

## Step 2: Create Snowflake Database Schema (2 minutes)

### Option A: Using Snowflake Web UI (Easiest)

1. **Go to:** https://app.snowflake.com/
2. **Log in** with your credentials
3. **Click** "Worksheets" in the left sidebar
4. **Click** "+ Worksheet" button
5. **Copy** the entire contents of `scraper/snowflake_schema.sql`
6. **Paste** into the worksheet
7. **Click** "Run All" button (or press Cmd+Enter)
8. **Wait** ~10 seconds for tables to be created
9. **Verify:** You should see success messages for each CREATE statement

### Option B: Using SnowSQL CLI (Advanced)

```bash
# Install SnowSQL (if not already installed)
brew install --cask snowflake-snowsql

# Run the schema file
snowsql -a GUWYXHN-OF53265 -u IMDANIAL -f scraper/snowflake_schema.sql
# Enter your password when prompted
```

---

## Step 3: Configure Environment Variables (1 minute)

### Create your .env file:

```bash
cd /Users/ilandanial/Paralegal

# Copy the example
cp .env.example .env

# Edit with your favorite editor
code .env  # or nano .env, or vim .env
```

### Add your Snowflake credentials:

Find these lines in `.env` and update:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=GUWYXHN-OF53265
SNOWFLAKE_USER=IMDANIAL
SNOWFLAKE_PASSWORD=your_actual_password_here    # ← CHANGE THIS!
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=PARALEGAL_DB
SNOWFLAKE_SCHEMA=LEGAL_DATA
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

**Save** the file.

---

## Step 4: Test the Connection (1 minute)

```bash
cd /Users/ilandanial/Paralegal

# Test Snowflake connectivity
python backend/APIs/db/snowflake_client.py
```

**Expected output:**
```
✓ Connected to Snowflake: PARALEGAL_DB.LEGAL_DATA
1. Creating search session...
Session ID: abc123...
✓ Created search session: abc123...
2. Inserting sample document...
✓ Inserted document: doc_...
3. Inserting sample law firm...
✓ Inserted law firm: firm_...
...
✅ All examples completed successfully!
✓ Disconnected from Snowflake
```

---

## Step 5: Integrate with Scraper (Optional)

To use Snowflake with your webscraper:

### Update `scraper/config.ini`:

```ini
[database]
# Set backend to 'snowflake' or 'both' (PostgreSQL + Snowflake)
backend = snowflake
```

### Or use environment variable:

In your `.env` file:
```bash
SCRAPER_DB_BACKEND=snowflake    # Options: postgres, snowflake, both
```

### Test scraper with Snowflake:

```bash
cd scraper
python snowflake_adapter.py
```

---

## Usage Examples

### Example 1: Query from AI Agent

```python
from backend.APIs.db.snowflake_client import get_client

# Get a connected client
client = get_client()

# Search for relevant legal documents
docs = client.search_documents(
    query_text="personal injury slip and fall",
    jurisdiction="Florida",
    limit=10
)

for doc in docs:
    print(f"- {doc['TITLE']}")
    print(f"  Citation: {doc['CITATION']}")
    print(f"  Court: {doc['COURT']}")

client.disconnect()
```

### Example 2: Bulk Insert from Scraper

```python
from scraper.snowflake_adapter import SnowflakeScraperAdapter

adapter = SnowflakeScraperAdapter()

# Start scraping session
session_id = adapter.start_search_session(
    search_query="Florida law firm compliance",
    total_results=100
)

# Insert documents as you scrape them
for doc in scraped_documents:
    adapter.insert_document(doc)

adapter.close()
```

### Example 3: Get Analytics

```python
from backend.APIs.db.snowflake_client import get_client

client = get_client()

# Get overall statistics
stats = client.get_total_stats()
print(f"Total Documents: {stats['total_documents']}")
print(f"Total Compliance Issues: {stats['total_compliance_issues']}")

# Get firm statistics
firm_stats = client.get_firm_statistics()
for firm in firm_stats[:10]:  # Top 10 firms
    print(f"{firm['FIRM_NAME']}: {firm['TOTAL_CASES']} cases")

client.disconnect()
```

---

## Troubleshooting

### Error: "Import snowflake.connector could not be resolved"

**Solution:** Install the package
```bash
pip install snowflake-connector-python
```

### Error: "250001: Could not connect to Snowflake backend"

**Possible causes:**
1. Wrong account identifier → Check: `GUWYXHN-OF53265`
2. Wrong username → Check: `IMDANIAL`
3. Wrong password → Verify in `.env`
4. Network/firewall blocking connection → Try from different network

### Error: "Object 'PARALEGAL_DB.LEGAL_DATA' does not exist"

**Solution:** Run the schema SQL file (Step 2)

### Error: "Warehouse 'COMPUTE_WH' does not exist"

**Solution:** Either:
1. Use the warehouse that exists in your account (check Snowflake UI)
2. Or create `COMPUTE_WH`:
```sql
CREATE WAREHOUSE COMPUTE_WH;
```

---

## Snowflake Web UI Cheat Sheet

### View Your Data:

1. Go to: https://app.snowflake.com/
2. Click "Data" → "Databases"
3. Expand: `PARALEGAL_DB` → `LEGAL_DATA` → `Tables`
4. Click on any table to browse data

### Run Queries:

1. Click "Worksheets"
2. Create new worksheet
3. Select context:
   - Warehouse: `COMPUTE_WH`
   - Database: `PARALEGAL_DB`
   - Schema: `LEGAL_DATA`
4. Write SQL and run

**Example queries:**

```sql
-- Count total documents
SELECT COUNT(*) FROM DOCUMENTS;

-- View recent compliance violations
SELECT * FROM VW_RECENT_VIOLATIONS LIMIT 10;

-- Search for specific case
SELECT * FROM DOCUMENTS 
WHERE TITLE ILIKE '%slip and fall%' 
LIMIT 5;

-- Get firm activity summary
SELECT * FROM VW_FIRM_ACTIVITY 
ORDER BY TOTAL_CASES DESC;
```

---

## Cost Management

### Your Snowflake Trial Includes:

- 💰 **$400 free credits** (lasts months for this project)
- ⏰ **Auto-suspend after 5 minutes** (saves money)
- 📊 **SMALL warehouse** ($2/hour, only when running)

### Expected Costs for Hackathon:

- **Scraping 1,000 documents:** ~$0.10-0.50
- **AI agent queries (100/day):** ~$0.05-0.10
- **Total for 24-hour hackathon:** ~$1-3

**Your $400 credit covers this 100x over!**

### Monitor Usage:

1. Snowflake UI → "Admin" → "Usage"
2. View credit consumption in real-time

---

## Next Steps

1. ✅ **Integrate with AI Agents** 
   - Update `backend/agents/legal_researcher_agent.py` to query Snowflake
   - See: `docs/AGENT_SNOWFLAKE_INTEGRATION.md` (coming next)

2. ✅ **Build Demo Dashboard**
   - Use `VW_FIRM_ACTIVITY` and `VW_RECENT_VIOLATIONS` views
   - Create Streamlit or Flask UI showing analytics

3. ✅ **Configure Scraper**
   - Update `scraper/config.ini` with LexisNexis credentials
   - Set `backend=snowflake` to use Snowflake storage

---

## Quick Reference

**Your Snowflake Info:**
- Account: `GUWYXHN-OF53265`
- URL: `https://GUWYXHN-OF53265.snowflakecomputing.com`
- User: `IMDANIAL`
- Region: GCP US-East-4 (N. Virginia)
- Edition: Enterprise

**Key Files:**
- Schema: `scraper/snowflake_schema.sql`
- Client: `backend/APIs/db/snowflake_client.py`
- Adapter: `scraper/snowflake_adapter.py`
- Config: `.env`

**Support:**
- Snowflake Docs: https://docs.snowflake.com/
- Python Connector: https://docs.snowflake.com/en/user-guide/python-connector

---

## 🎉 You're Done!

Snowflake is now fully integrated with your AI Legal Tender project. Your scraper can write data to Snowflake, and your AI agents can query it for fast case lookups and analytics.

**Architecture:**
```
LexisNexis → Scraper → Snowflake → AI Agents → Responses
                             ↓
                        Analytics Dashboard
```

Ready to scrape some legal data! 🚀
