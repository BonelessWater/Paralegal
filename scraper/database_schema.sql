-- Database schema for LexisNexis law firm compliance data
-- Run this script to create the necessary tables in your PostgreSQL database

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS legal_data;

-- Table for storing search results metadata
CREATE TABLE IF NOT EXISTS legal_data.search_sessions (
    id SERIAL PRIMARY KEY,
    search_query TEXT NOT NULL,
    search_url TEXT,
    total_results INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed',
    notes TEXT
);

-- Table for storing individual legal documents/cases
CREATE TABLE IF NOT EXISTS legal_data.documents (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES legal_data.search_sessions(id) ON DELETE CASCADE,
    document_id VARCHAR(255) UNIQUE,
    title TEXT,
    document_type VARCHAR(100),
    jurisdiction VARCHAR(255),
    court VARCHAR(255),
    decision_date DATE,
    citation TEXT,
    url TEXT,
    summary TEXT,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing law firms mentioned in documents
CREATE TABLE IF NOT EXISTS legal_data.law_firms (
    id SERIAL PRIMARY KEY,
    firm_name VARCHAR(500) UNIQUE NOT NULL,
    address TEXT,
    city VARCHAR(255),
    state VARCHAR(100),
    country VARCHAR(100),
    website VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table linking documents to law firms
CREATE TABLE IF NOT EXISTS legal_data.document_law_firms (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    law_firm_id INTEGER REFERENCES legal_data.law_firms(id) ON DELETE CASCADE,
    role VARCHAR(100), -- e.g., 'plaintiff', 'defendant', 'counsel'
    UNIQUE(document_id, law_firm_id, role)
);

-- Table for compliance topics/tags
CREATE TABLE IF NOT EXISTS legal_data.compliance_topics (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100)
);

-- Junction table for document topics
CREATE TABLE IF NOT EXISTS legal_data.document_topics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES legal_data.documents(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES legal_data.compliance_topics(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2), -- 0.00 to 1.00
    UNIQUE(document_id, topic_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_session ON legal_data.documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON legal_data.documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_date ON legal_data.documents(decision_date);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON legal_data.documents(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_law_firms_name ON legal_data.law_firms(firm_name);
CREATE INDEX IF NOT EXISTS idx_compliance_topics_name ON legal_data.compliance_topics(topic_name);

-- Create a view for easy querying of documents with related data
CREATE OR REPLACE VIEW legal_data.documents_summary AS
SELECT 
    d.id,
    d.document_id,
    d.title,
    d.document_type,
    d.jurisdiction,
    d.court,
    d.decision_date,
    d.citation,
    ss.search_query,
    ss.scraped_at,
    COUNT(DISTINCT dlf.law_firm_id) as num_law_firms,
    COUNT(DISTINCT dt.topic_id) as num_topics
FROM legal_data.documents d
LEFT JOIN legal_data.search_sessions ss ON d.session_id = ss.id
LEFT JOIN legal_data.document_law_firms dlf ON d.id = dlf.document_id
LEFT JOIN legal_data.document_topics dt ON d.id = dt.document_id
GROUP BY d.id, d.document_id, d.title, d.document_type, d.jurisdiction, 
         d.court, d.decision_date, d.citation, ss.search_query, ss.scraped_at;

COMMENT ON SCHEMA legal_data IS 'Schema for storing scraped legal compliance data from LexisNexis';
COMMENT ON TABLE legal_data.search_sessions IS 'Tracks each scraping session and search query executed';
COMMENT ON TABLE legal_data.documents IS 'Stores individual legal documents, cases, and articles';
COMMENT ON TABLE legal_data.law_firms IS 'Master table of law firms mentioned in documents';
COMMENT ON TABLE legal_data.compliance_topics IS 'Categorized compliance topics extracted from documents';
