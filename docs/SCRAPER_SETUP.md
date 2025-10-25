# Scraper Setup and Usage Guide

This guide will help you set up and run the LexisNexis scraper on the AMD server.

## Quick Setup on AMD Server

### Step 1: SSH into AMD Server

```bash
ssh amd-knights@134.199.202.8
# Password: wasdGspot
```

### Step 2: Navigate to Project and Run Setup

```bash
cd ~/Paralegal/setup
chmod +x setup_scraper.sh
./setup_scraper.sh
```

**What this script does:**
- Installs PostgreSQL database
- Creates database `paralegal_db` and user `paralegal_user`
- Initializes database schema (7 tables)
- Installs Google Chrome and ChromeDriver for Selenium
- Installs Python dependencies (selenium, psycopg2, beautifulsoup4)
- Creates scraper configuration file with credentials

**This will take about 5-10 minutes to complete.**

---

## Step 3: Test Database Connection

After setup completes, verify everything works:

```bash
cd ~/Paralegal/scraper
python test_database.py
```

You should see:
```
✓ Connected to database successfully!
✓ Schema 'legal_data' exists
✓ Found X tables
✓ Test record inserted
✓ Test record deleted
✓ All database tests passed!
```

---

## Step 4: Run the Scraper

### Option A: Test Mode (Recommended First)

```bash
cd ~/Paralegal/scraper
python test_scraper.py
```

This runs a quick test to verify:
- LexisNexis authentication works
- Selenium ChromeDriver works
- Database insertion works

### Option B: Full Scraping

```bash
cd ~/Paralegal/scraper
python scrape.py
```

This will:
1. Authenticate with LexisNexis (credentials from config.ini)
2. Search for "law firm data compliance"
3. Scrape up to 100 results
4. Store everything in PostgreSQL database

---

## Configuration

The scraper configuration is in `scraper/config.ini`:

```ini
[lexisnexis]
username = Albert0898
password = Lexisme98!
search_query = law firm data compliance
max_results = 100

[database]
host = localhost
database = paralegal_db
username = paralegal_user
password = hackathon2024
```

**To change search query or credentials:**
```bash
nano ~/Paralegal/scraper/config.ini
```

---

## Database Information

### Connection Details
- **Host:** localhost
- **Port:** 5432
- **Database:** paralegal_db
- **Username:** paralegal_user
- **Password:** hackathon2024
- **Schema:** legal_data

### Tables Created

1. `search_sessions` - Tracks each scraping run
2. `documents` - Legal documents/cases scraped
3. `law_firms` - Law firms mentioned in documents
4. `document_law_firms` - Links documents to law firms
5. `compliance_topics` - Compliance topics/tags
6. `document_topics` - Links documents to topics
7. `documents_summary` (view) - Summary query for easy access

### Query the Database

Connect to PostgreSQL:
```bash
sudo -u postgres psql -d paralegal_db
```

Example queries:
```sql
-- See all scraping sessions
SELECT * FROM legal_data.search_sessions;

-- See all documents
SELECT * FROM legal_data.documents;

-- Get summary view
SELECT * FROM legal_data.documents_summary;

-- Count documents by type
SELECT document_type, COUNT(*) 
FROM legal_data.documents 
GROUP BY document_type;

-- Exit psql
\q
```

---

## Troubleshooting

### PostgreSQL not running
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### ChromeDriver errors
```bash
# Check Chrome version
google-chrome --version

# Check ChromeDriver version
chromedriver --version

# If mismatch, reinstall ChromeDriver
sudo apt-get update
sudo apt-get install --only-upgrade google-chrome-stable
```

### Connection refused
```bash
# Check if PostgreSQL is listening
sudo netstat -plnt | grep 5432

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Selenium/Chrome issues
```bash
# Run in headless mode (add to config.ini under [scraping])
headless = true

# Check if Chrome can run
google-chrome --headless --disable-gpu --dump-dom https://www.google.com
```

---

## Logs

The scraper creates a log file:
```bash
tail -f ~/Paralegal/scraper/scraper.log
```

---

## Integration with AI Agents

Once data is scraped, the Legal Researcher agent can query it:

```python
from backend.APIs.AMD.llm_client import LLMClient
from backend.agents.legal_researcher_agent import LegalResearcherAgent

# Initialize
llm = LLMClient()
researcher = LegalResearcherAgent(llm)

# Query with database context
case_info = "Personal injury case, car accident, Miami FL"
research = researcher.process(case_info)
print(research)
```

The agent will use scraped precedent cases to provide better legal guidance.

---

## Performance Tips

1. **Adjust delays** (config.ini):
   - `request_delay = 2.0` - Time between requests (increase if getting blocked)
   
2. **Batch processing**:
   - Run during off-peak hours
   - Use `max_results` to limit scraping

3. **Database optimization**:
   - Indexes are already created in schema
   - Run `VACUUM ANALYZE` periodically:
     ```bash
     sudo -u postgres psql -d paralegal_db -c "VACUUM ANALYZE;"
     ```

---

## Next Steps After Scraping

1. **Verify data quality:**
   ```bash
   python -c "from database import DatabaseManager; import configparser; config = configparser.ConfigParser(); config.read('config.ini'); db = DatabaseManager(dict(config['database'])); print('Database connected!')"
   ```

2. **Export data** (if needed):
   ```bash
   sudo -u postgres pg_dump -d paralegal_db -t legal_data.* > backup.sql
   ```

3. **Test with AI agents:**
   ```bash
   cd ~/Paralegal/backend
   python test_agents.py
   ```

---

## Quick Command Reference

```bash
# Setup
cd ~/Paralegal/setup && ./setup_scraper.sh

# Test database
cd ~/Paralegal/scraper && python test_database.py

# Test scraper
python test_scraper.py

# Run scraper
python scrape.py

# View logs
tail -f scraper.log

# Check database
sudo -u postgres psql -d paralegal_db

# Stop/Start PostgreSQL
sudo systemctl stop postgresql
sudo systemctl start postgresql
```

---

**Need help?** Check logs first:
- Scraper logs: `~/Paralegal/scraper/scraper.log`
- PostgreSQL logs: `/var/log/postgresql/postgresql-*-main.log`
- Chrome logs: Check terminal output when running test_scraper.py
