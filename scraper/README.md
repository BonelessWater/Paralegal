# LexisNexis Advance Scraper

A comprehensive web scraper for extracting law firm compliance data from LexisNexis Advance and storing it in a PostgreSQL database.

## ⚠️ Important Notice

**LexisNexis Advance requires authentication and a valid subscription.** This scraper:
- Requires valid LexisNexis credentials
- Is intended for authorized users only
- Should comply with LexisNexis Terms of Service
- May require adjustment based on website structure changes

## Features

- ✅ Automated authentication with LexisNexis Advance
- ✅ Configurable search queries
- ✅ Pagination support for large result sets
- ✅ PostgreSQL database integration with normalized schema
- ✅ Comprehensive error handling and logging
- ✅ Retry logic for network failures
- ✅ Selenium-based scraping for JavaScript-heavy pages

## Project Structure

```
scraper/
├── scrape.py              # Main scraper module
├── database.py            # PostgreSQL database manager
├── database_schema.sql    # Database schema definition
├── config.ini.example     # Example configuration file
├── scraper.log           # Log file (auto-generated)
└── README.md             # This file
```

## Prerequisites

1. **Python 3.8+**
2. **PostgreSQL 12+**
3. **Chrome/Chromium browser**
4. **ChromeDriver** (for Selenium)
5. **Valid LexisNexis Advance subscription**

## Installation

### 1. Install Python Dependencies

```powershell
cd "C:\Users\johnp\Desktop\knighthaxs\Paralegal"
pip install -r requirements.txt
```

### 2. Install ChromeDriver

**Windows:**
```powershell
# Download ChromeDriver matching your Chrome version from:
# https://chromedriver.chromium.org/downloads

# Add ChromeDriver to your PATH or place in the project directory
```

**Alternative - Install via Chocolatey:**
```powershell
choco install chromedriver
```

### 3. Set Up PostgreSQL Database

```powershell
# Create database
psql -U postgres
```

```sql
CREATE DATABASE paralegal_db;
\q
```

```powershell
# Initialize schema
cd scraper
psql -U postgres -d paralegal_db -f database_schema.sql
```

### 4. Configure the Scraper

```powershell
# Copy example config
cd scraper
cp config.ini.example config.ini
```

Edit `config.ini` with your credentials:

```ini
[lexisnexis]
username = your_lexisnexis_username
password = your_lexisnexis_password

[database]
host = localhost
port = 5432
database = paralegal_db
username = postgres
password = your_db_password
```

## Usage

### Basic Usage

```powershell
cd scraper
python scrape.py
```

This will use the search query defined in `config.ini`.

### Advanced Usage

```powershell
# Custom search query
python scrape.py --query "data privacy compliance"

# Limit results
python scrape.py --query "GDPR violations" --max-results 50

# Initialize database schema
python scrape.py --init-db

# Use custom config file
python scrape.py --config custom_config.ini
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to configuration file | `config.ini` |
| `--query` | Search query (overrides config) | From config |
| `--max-results` | Maximum results to scrape | `100` |
| `--init-db` | Initialize database schema | `False` |

## Database Schema

The scraper creates the following tables:

### Main Tables

- **`search_sessions`** - Tracks each scraping session
- **`documents`** - Stores legal documents and cases
- **`law_firms`** - Master table of law firms
- **`compliance_topics`** - Categorized compliance topics

### Junction Tables

- **`document_law_firms`** - Links documents to law firms
- **`document_topics`** - Links documents to compliance topics

### Example Queries

```sql
-- Get all documents from a specific search
SELECT * FROM legal_data.documents_summary 
WHERE search_query = 'law firm data compliance';

-- Find documents by law firm
SELECT d.* 
FROM legal_data.documents d
JOIN legal_data.document_law_firms dlf ON d.id = dlf.document_id
JOIN legal_data.law_firms lf ON dlf.law_firm_id = lf.id
WHERE lf.firm_name ILIKE '%firm name%';

-- Get compliance topics by document
SELECT d.title, ct.topic_name, dt.relevance_score
FROM legal_data.documents d
JOIN legal_data.document_topics dt ON d.id = dt.document_id
JOIN legal_data.compliance_topics ct ON dt.topic_id = ct.id
ORDER BY dt.relevance_score DESC;
```

## Configuration Options

### Scraping Settings

```ini
[scraping]
request_delay = 2.0        # Delay between requests (seconds)
max_retries = 3            # Maximum retry attempts
timeout = 30               # Request timeout (seconds)
```

### Logging

Logs are written to both console and `scraper.log` file:
- **INFO** - Progress updates
- **WARNING** - Recoverable errors
- **ERROR** - Critical failures

## Troubleshooting

### Authentication Fails

**Problem:** `Authentication failed - still on sign-in page`

**Solutions:**
1. Verify credentials in `config.ini`
2. Check if LexisNexis account is active
3. Try logging in manually to verify account status
4. Check for CAPTCHA or 2FA requirements

### ChromeDriver Not Found

**Problem:** `Failed to initialize WebDriver`

**Solutions:**
```powershell
# Install ChromeDriver
choco install chromedriver

# Or download manually and add to PATH
# https://chromedriver.chromium.org/downloads
```

### Database Connection Error

**Problem:** `Failed to create connection pool`

**Solutions:**
1. Verify PostgreSQL is running:
   ```powershell
   Get-Service postgresql*
   ```

2. Check connection details in `config.ini`

3. Test connection manually:
   ```powershell
   psql -U postgres -d paralegal_db
   ```

### No Results Found

**Problem:** `Could not find any results on this page`

**Solutions:**
1. LexisNexis HTML structure may have changed
2. Run with logging to inspect page source
3. Update CSS selectors in `_extract_document_data()` method
4. Check if search query is valid

### Import Errors

**Problem:** `Import "psycopg2" could not be resolved`

**Solutions:**
```powershell
# Install all dependencies
pip install -r requirements.txt

# If psycopg2 fails, try binary version
pip install psycopg2-binary
```

## Customization

### Modifying Search Selectors

LexisNexis may update their HTML structure. To update selectors:

1. Open `scrape.py`
2. Locate `_extract_document_data()` method
3. Update CSS selectors based on current HTML structure
4. Test with small `--max-results` value

### Adding Custom Fields

To capture additional data:

1. Update `database_schema.sql` with new columns
2. Modify `_extract_document_data()` to extract new fields
3. Update `insert_document()` in `database.py`
4. Reinitialize database:
   ```powershell
   python scrape.py --init-db
   ```

## Code Structure

### Main Classes

**`LexisNexisScraper`**
- `authenticate()` - Handle login
- `search()` - Execute search query
- `scrape_search_results()` - Scrape result pages
- `_extract_document_data()` - Parse individual results

**`DatabaseManager`**
- `create_search_session()` - Track scraping session
- `insert_document()` - Store document data
- `insert_law_firm()` - Store law firm information
- `link_document_to_firm()` - Create relationships

## Best Practices

1. **Rate Limiting**: Use appropriate `request_delay` to avoid overwhelming servers
2. **Error Handling**: Check logs regularly for issues
3. **Data Validation**: Verify scraped data quality
4. **Incremental Scraping**: Use smaller `max_results` for testing
5. **Compliance**: Respect LexisNexis Terms of Service

## Legal & Ethical Considerations

⚠️ **Important:**
- Only use with valid LexisNexis subscription
- Comply with LexisNexis Terms of Service
- Respect rate limits and server resources
- Use scraped data responsibly and legally
- Check your organization's policies on web scraping

## Future Enhancements

- [ ] Add support for advanced search filters
- [ ] Implement document full-text extraction
- [ ] Add natural language processing for topic extraction
- [ ] Create data export functionality (CSV, JSON)
- [ ] Add email notifications for completed scrapes
- [ ] Implement incremental updates (avoid re-scraping)
- [ ] Add support for multiple search providers

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `scraper.log`
3. Verify configuration in `config.ini`
4. Ensure all dependencies are installed

## License

This tool is provided for educational and authorized use only. Users are responsible for compliance with LexisNexis Terms of Service and applicable laws.

---

**Created:** October 2025  
**Python Version:** 3.8+  
**Database:** PostgreSQL 12+
