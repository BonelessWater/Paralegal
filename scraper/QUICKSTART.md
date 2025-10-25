# Quick Start Guide - LexisNexis Scraper

## Prerequisites Checklist
- [ ] Python 3.8+ installed
- [ ] PostgreSQL 12+ installed and running
- [ ] Chrome browser installed
- [ ] Valid LexisNexis Advance subscription
- [ ] LexisNexis credentials ready

## 5-Minute Setup

### Step 1: Install Dependencies (2 minutes)

```powershell
# Navigate to project directory
cd "C:\Users\johnp\Desktop\knighthaxs\Paralegal"

# Install Python packages
pip install -r requirements.txt

# Install ChromeDriver (if not already installed)
choco install chromedriver
```

### Step 2: Configure Credentials (1 minute)

```powershell
cd scraper

# Copy example config
cp config.ini.example config.ini

# Edit config.ini with your favorite editor
notepad config.ini
```

**Update these sections:**
```ini
[lexisnexis]
username = YOUR_LEXISNEXIS_USERNAME
password = YOUR_LEXISNEXIS_PASSWORD

[database]
password = YOUR_POSTGRES_PASSWORD
```

### Step 3: Setup Database (1 minute)

```powershell
# Create database
psql -U postgres -c "CREATE DATABASE paralegal_db;"

# Initialize schema
psql -U postgres -d paralegal_db -f database_schema.sql
```

**Or use the setup script:**
```powershell
.\setup.ps1
```

### Step 4: Test Installation (30 seconds)

```powershell
python test_scraper.py
```

All tests should pass ✓

### Step 5: Run Your First Scrape (30 seconds)

```powershell
# Small test run (10 results)
python scrape.py --query "law firm data compliance" --max-results 10
```

## Common Commands

### Run with default settings
```powershell
python scrape.py
```

### Custom search query
```powershell
python scrape.py --query "GDPR violations" --max-results 50
```

### Re-initialize database
```powershell
python scrape.py --init-db
```

## Verify Results

```powershell
# Connect to database
psql -U postgres -d paralegal_db
```

```sql
-- Check scraped documents
SELECT COUNT(*) FROM legal_data.documents;

-- View recent documents
SELECT title, decision_date, jurisdiction 
FROM legal_data.documents 
ORDER BY created_at DESC 
LIMIT 10;

-- Exit
\q
```

## Troubleshooting

### Import errors
```powershell
pip install --upgrade -r requirements.txt
```

### ChromeDriver issues
```powershell
# Check Chrome version
chrome --version

# Download matching ChromeDriver from:
# https://chromedriver.chromium.org/downloads
```

### Authentication fails
- Verify credentials in config.ini
- Try logging in manually at https://advance.lexis.com
- Check for 2FA or CAPTCHA requirements

### Database connection fails
```powershell
# Check if PostgreSQL is running
Get-Service postgresql*

# Start if stopped
Start-Service postgresql-x64-14  # adjust version
```

## What Gets Scraped?

✅ Document titles  
✅ Citations  
✅ Jurisdictions  
✅ Courts  
✅ Decision dates  
✅ Document URLs  
✅ Summaries  
✅ Search metadata  

## Output Location

- **Database**: PostgreSQL `paralegal_db`
- **Logs**: `scraper/scraper.log`
- **Schema**: `legal_data` schema

## Next Steps

1. Review scraped data in database
2. Customize search queries in config.ini
3. Adjust scraping delays if needed
4. Export data for analysis
5. Set up scheduled scraping (optional)

## Important Notes

⚠️ **Rate Limiting**: Default 2-second delay between requests  
⚠️ **Authentication**: Requires valid LexisNexis credentials  
⚠️ **Terms of Service**: Ensure compliance with LexisNexis ToS  
⚠️ **Data Volume**: Start with small `--max-results` for testing  

## Support

- Check `README.md` for detailed documentation
- Review `scraper.log` for error details
- Run `test_scraper.py` to diagnose issues

---

Ready to go! 🚀
