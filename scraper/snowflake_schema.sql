-- Snowflake Schema for LexisNexis Legal Data
-- Optimized for fast querying and analytics
-- Run this in your Snowflake account to create the warehouse and tables

-- ============================================================================
-- 1. CREATE WAREHOUSE (optimized for scraping workload)
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS LEGAL_SCRAPER_WH
    WAREHOUSE_SIZE = 'SMALL'           -- Start small, can scale up
    AUTO_SUSPEND = 300                 -- Suspend after 5 min of inactivity
    AUTO_RESUME = TRUE                 -- Auto-resume on queries
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for LexisNexis scraper data ingestion and queries';

-- ============================================================================
-- 2. CREATE DATABASE AND SCHEMA
-- ============================================================================

CREATE DATABASE IF NOT EXISTS PARALEGAL_DB
    COMMENT = 'Legal data for AI Legal Tender hackathon';

USE DATABASE PARALEGAL_DB;

CREATE SCHEMA IF NOT EXISTS LEGAL_DATA
    COMMENT = 'LexisNexis scraped data and compliance information';

USE SCHEMA LEGAL_DATA;

-- ============================================================================
-- 3. TABLES (Optimized for Snowflake)
-- ============================================================================

-- Table: Search Sessions
-- Tracks each scraping session for audit/debugging
CREATE TABLE IF NOT EXISTS SEARCH_SESSIONS (
    SESSION_ID STRING PRIMARY KEY,                    -- UUID from scraper
    SEARCH_QUERY STRING NOT NULL,
    SEARCH_URL STRING,
    TOTAL_RESULTS NUMBER,
    SCRAPED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    STATUS STRING DEFAULT 'completed',                -- completed, failed, partial
    NOTES STRING,
    METADATA VARIANT                                  -- JSON for flexible data
);

-- Table: Legal Documents
-- Core table for all scraped legal documents
CREATE TABLE IF NOT EXISTS DOCUMENTS (
    DOCUMENT_ID STRING PRIMARY KEY,                   -- Unique doc ID from LexisNexis
    SESSION_ID STRING,                                -- FK to SEARCH_SESSIONS
    TITLE STRING,
    DOCUMENT_TYPE STRING,                             -- Case, Statute, Regulation, etc.
    JURISDICTION STRING,
    COURT STRING,
    DECISION_DATE DATE,
    FILING_DATE DATE,
    CITATION STRING,
    URL STRING,
    SUMMARY STRING,
    FULL_TEXT STRING,                                 -- Full document text (can be large)
    PARTIES VARIANT,                                  -- JSON array of parties
    JUDGES VARIANT,                                   -- JSON array of judges
    TOPICS VARIANT,                                   -- JSON array of legal topics
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Clustering for fast queries on common filters
    CLUSTER BY (JURISDICTION, DOCUMENT_TYPE, DECISION_DATE)
);

-- Table: Law Firms
-- Normalized table for law firms mentioned in documents
CREATE TABLE IF NOT EXISTS LAW_FIRMS (
    FIRM_ID STRING PRIMARY KEY,                       -- Generated UUID
    FIRM_NAME STRING NOT NULL,
    ADDRESS STRING,
    CITY STRING,
    STATE STRING,
    COUNTRY STRING DEFAULT 'USA',
    ZIP_CODE STRING,
    PHONE STRING,
    WEBSITE STRING,
    PRACTICE_AREAS VARIANT,                           -- JSON array
    SIZE_CATEGORY STRING,                             -- Small, Medium, Large, BigLaw
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Deduplication constraint
    CONSTRAINT UNIQUE_FIRM_NAME UNIQUE (FIRM_NAME)
);

-- Table: Document-Law Firm Relationships
-- Junction table linking documents to law firms
CREATE TABLE IF NOT EXISTS DOCUMENT_LAW_FIRMS (
    ID STRING PRIMARY KEY,                            -- Generated UUID
    DOCUMENT_ID STRING NOT NULL,
    FIRM_ID STRING NOT NULL,
    ROLE STRING,                                      -- Plaintiff, Defendant, Amicus, etc.
    ATTORNEYS VARIANT,                                -- JSON array of attorney names
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Foreign keys (Snowflake supports but doesn't enforce)
    FOREIGN KEY (DOCUMENT_ID) REFERENCES DOCUMENTS(DOCUMENT_ID),
    FOREIGN KEY (FIRM_ID) REFERENCES LAW_FIRMS(FIRM_ID)
);

-- Table: Attorneys
-- Individual attorney information
CREATE TABLE IF NOT EXISTS ATTORNEYS (
    ATTORNEY_ID STRING PRIMARY KEY,                   -- Generated UUID
    FULL_NAME STRING NOT NULL,
    BAR_NUMBER STRING,
    STATE_ADMITTED STRING,
    FIRM_ID STRING,                                   -- Current firm
    EMAIL STRING,
    PHONE STRING,
    SPECIALIZATION VARIANT,                           -- JSON array
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    FOREIGN KEY (FIRM_ID) REFERENCES LAW_FIRMS(FIRM_ID)
);

-- Table: Document-Attorney Relationships
CREATE TABLE IF NOT EXISTS DOCUMENT_ATTORNEYS (
    ID STRING PRIMARY KEY,
    DOCUMENT_ID STRING NOT NULL,
    ATTORNEY_ID STRING NOT NULL,
    ROLE STRING,                                      -- Lead Counsel, Associate, etc.
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    FOREIGN KEY (DOCUMENT_ID) REFERENCES DOCUMENTS(DOCUMENT_ID),
    FOREIGN KEY (ATTORNEY_ID) REFERENCES ATTORNEYS(ATTORNEY_ID)
);

-- Table: Compliance Issues
-- Specific compliance violations/issues found in documents
CREATE TABLE IF NOT EXISTS COMPLIANCE_ISSUES (
    ISSUE_ID STRING PRIMARY KEY,                      -- Generated UUID
    DOCUMENT_ID STRING NOT NULL,
    FIRM_ID STRING,
    ISSUE_TYPE STRING,                                -- Ethics Violation, Malpractice, etc.
    SEVERITY STRING,                                  -- Low, Medium, High, Critical
    DESCRIPTION STRING,
    OUTCOME STRING,                                   -- Sanction, Dismissal, Fine, etc.
    SANCTION_AMOUNT NUMBER(15, 2),                   -- Monetary amount if applicable
    RESOLUTION_DATE DATE,
    STATUS STRING DEFAULT 'Open',                     -- Open, Resolved, Pending
    EXTRACTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    FOREIGN KEY (DOCUMENT_ID) REFERENCES DOCUMENTS(DOCUMENT_ID),
    FOREIGN KEY (FIRM_ID) REFERENCES LAW_FIRMS(FIRM_ID)
);

-- ============================================================================
-- 4. VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Recent Compliance Violations
CREATE OR REPLACE VIEW VW_RECENT_VIOLATIONS AS
SELECT 
    ci.ISSUE_ID,
    ci.ISSUE_TYPE,
    ci.SEVERITY,
    ci.DESCRIPTION,
    lf.FIRM_NAME,
    lf.CITY,
    lf.STATE,
    d.JURISDICTION,
    d.DECISION_DATE,
    ci.SANCTION_AMOUNT
FROM COMPLIANCE_ISSUES ci
JOIN LAW_FIRMS lf ON ci.FIRM_ID = lf.FIRM_ID
JOIN DOCUMENTS d ON ci.DOCUMENT_ID = d.DOCUMENT_ID
WHERE d.DECISION_DATE >= DATEADD(year, -2, CURRENT_DATE())
ORDER BY d.DECISION_DATE DESC;

-- View: Firm Activity Summary
CREATE OR REPLACE VIEW VW_FIRM_ACTIVITY AS
SELECT 
    lf.FIRM_ID,
    lf.FIRM_NAME,
    lf.STATE,
    COUNT(DISTINCT dlf.DOCUMENT_ID) AS TOTAL_CASES,
    COUNT(DISTINCT ci.ISSUE_ID) AS COMPLIANCE_ISSUES,
    SUM(CASE WHEN ci.SEVERITY = 'Critical' THEN 1 ELSE 0 END) AS CRITICAL_ISSUES,
    SUM(ci.SANCTION_AMOUNT) AS TOTAL_SANCTIONS
FROM LAW_FIRMS lf
LEFT JOIN DOCUMENT_LAW_FIRMS dlf ON lf.FIRM_ID = dlf.FIRM_ID
LEFT JOIN COMPLIANCE_ISSUES ci ON lf.FIRM_ID = ci.FIRM_ID
GROUP BY lf.FIRM_ID, lf.FIRM_NAME, lf.STATE;

-- View: Document Search (for AI agents)
CREATE OR REPLACE VIEW VW_DOCUMENT_SEARCH AS
SELECT 
    d.DOCUMENT_ID,
    d.TITLE,
    d.DOCUMENT_TYPE,
    d.JURISDICTION,
    d.COURT,
    d.DECISION_DATE,
    d.CITATION,
    d.SUMMARY,
    d.FULL_TEXT,
    ARRAY_AGG(DISTINCT lf.FIRM_NAME) AS FIRMS_INVOLVED,
    ARRAY_AGG(DISTINCT a.FULL_NAME) AS ATTORNEYS_INVOLVED
FROM DOCUMENTS d
LEFT JOIN DOCUMENT_LAW_FIRMS dlf ON d.DOCUMENT_ID = dlf.DOCUMENT_ID
LEFT JOIN LAW_FIRMS lf ON dlf.FIRM_ID = lf.FIRM_ID
LEFT JOIN DOCUMENT_ATTORNEYS da ON d.DOCUMENT_ID = da.DOCUMENT_ID
LEFT JOIN ATTORNEYS a ON da.ATTORNEY_ID = a.ATTORNEY_ID
GROUP BY d.DOCUMENT_ID, d.TITLE, d.DOCUMENT_TYPE, d.JURISDICTION, 
         d.COURT, d.DECISION_DATE, d.CITATION, d.SUMMARY, d.FULL_TEXT;

-- ============================================================================
-- 5. SEARCH OPTIMIZATION (for AI agent queries)
-- ============================================================================

-- Full-text search function (requires Snowflake Enterprise Edition)
-- For standard edition, use LIKE/ILIKE queries

-- Create search optimization service on frequently queried columns
-- ALTER TABLE DOCUMENTS ADD SEARCH OPTIMIZATION ON EQUALITY(JURISDICTION, DOCUMENT_TYPE);

-- ============================================================================
-- 6. GRANT PERMISSIONS (adjust based on your security model)
-- ============================================================================

-- Example: Grant read/write access to scraper role
-- CREATE ROLE IF NOT EXISTS SCRAPER_ROLE;
-- GRANT USAGE ON WAREHOUSE LEGAL_SCRAPER_WH TO ROLE SCRAPER_ROLE;
-- GRANT USAGE ON DATABASE PARALEGAL_DB TO ROLE SCRAPER_ROLE;
-- GRANT USAGE ON SCHEMA LEGAL_DATA TO ROLE SCRAPER_ROLE;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA LEGAL_DATA TO ROLE SCRAPER_ROLE;

-- Example: Grant read-only access to AI agents role
-- CREATE ROLE IF NOT EXISTS AI_AGENT_ROLE;
-- GRANT USAGE ON WAREHOUSE LEGAL_SCRAPER_WH TO ROLE AI_AGENT_ROLE;
-- GRANT USAGE ON DATABASE PARALEGAL_DB TO ROLE AI_AGENT_ROLE;
-- GRANT USAGE ON SCHEMA LEGAL_DATA TO ROLE AI_AGENT_ROLE;
-- GRANT SELECT ON ALL TABLES IN SCHEMA LEGAL_DATA TO ROLE AI_AGENT_ROLE;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA LEGAL_DATA TO ROLE AI_AGENT_ROLE;

-- ============================================================================
-- 7. USAGE NOTES
-- ============================================================================

/*
QUICKSTART:

1. Copy this file to your local machine
2. Log into Snowflake web UI: https://app.snowflake.com/
3. Open a new SQL worksheet
4. Paste and run this entire script
5. Verify tables created:
   
   USE DATABASE PARALEGAL_DB;
   SHOW TABLES IN SCHEMA LEGAL_DATA;

6. Update your .env file with Snowflake credentials:
   
   SNOWFLAKE_ACCOUNT=your_account.us-east-1
   SNOWFLAKE_USER=your_username
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_WAREHOUSE=LEGAL_SCRAPER_WH
   SNOWFLAKE_DATABASE=PARALEGAL_DB
   SNOWFLAKE_SCHEMA=LEGAL_DATA

PERFORMANCE TIPS:

- Use clustering keys for frequently filtered columns
- Set appropriate warehouse size based on data volume:
  - SMALL: < 10k documents
  - MEDIUM: 10k - 100k documents
  - LARGE: 100k+ documents
- Enable auto-suspend to save costs during idle periods
- Use views for complex joins (pre-computed for agents)

COST OPTIMIZATION:

- Auto-suspend after 5 minutes (already configured)
- Use SMALL warehouse initially (costs ~$2/hour, only when running)
- With auto-suspend, expect $0.50-$2/day for hackathon usage
- Snowflake trial gives $400 credit (enough for months of testing)
*/
