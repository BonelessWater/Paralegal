#!/usr/bin/env python3
"""
Snowflake Integration Wrapper for LexisNexis Scraper
Allows scraper to write to Snowflake instead of (or in addition to) PostgreSQL
"""

import os
import sys
import uuid
from typing import Dict, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.APIs.db.snowflake_client import SnowflakeClient


class SnowflakeScraperAdapter:
    """
    Adapter that implements the same interface as PostgreSQL DatabaseManager
    but writes to Snowflake instead
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Snowflake adapter
        
        Args:
            config: Optional config dict (uses env vars if None)
        """
        self.client = SnowflakeClient(config)
        self.client.connect()
        self.current_session_id = None
    
    def start_search_session(self, search_query: str, search_url: str = None,
                            total_results: int = 0) -> str:
        """
        Start a new search session
        
        Args:
            search_query: The search query used
            search_url: URL of the search
            total_results: Number of results expected
            
        Returns:
            Session ID
        """
        self.current_session_id = self.client.create_search_session(
            search_query=search_query,
            search_url=search_url,
            total_results=total_results
        )
        return self.current_session_id
    
    def insert_document(self, doc: Dict) -> bool:
        """
        Insert a document from scraper
        
        Args:
            doc: Document dict from scraper with fields like title, url, etc.
            
        Returns:
            True if successful
        """
        # Map scraper fields to Snowflake schema
        doc_data = {
            'document_id': doc.get('id') or str(uuid.uuid4()),
            'session_id': self.current_session_id,
            'title': doc.get('title'),
            'document_type': doc.get('type', 'Unknown'),
            'jurisdiction': doc.get('jurisdiction'),
            'court': doc.get('court'),
            'decision_date': doc.get('date'),
            'citation': doc.get('citation'),
            'url': doc.get('url'),
            'summary': doc.get('summary'),
            'full_text': doc.get('content') or doc.get('full_text'),
            'parties': doc.get('parties', []),
            'judges': doc.get('judges', []),
            'topics': doc.get('topics', [])
        }
        
        return self.client.insert_document(doc_data)
    
    def insert_law_firm(self, firm: Dict) -> str:
        """
        Insert a law firm record
        
        Args:
            firm: Law firm dict with name, address, etc.
            
        Returns:
            Firm ID
        """
        return self.client.insert_law_firm(firm)
    
    def insert_compliance_issue(self, issue: Dict) -> str:
        """
        Insert a compliance issue
        
        Args:
            issue: Compliance issue dict
            
        Returns:
            Issue ID
        """
        return self.client.insert_compliance_issue(issue)
    
    def close(self):
        """Close the Snowflake connection"""
        self.client.disconnect()


class DualDatabaseManager:
    """
    Manager that writes to BOTH PostgreSQL and Snowflake
    Useful for migration or redundancy
    """
    
    def __init__(self, postgres_manager=None, snowflake_adapter=None):
        """
        Initialize dual database manager
        
        Args:
            postgres_manager: Existing PostgreSQL DatabaseManager
            snowflake_adapter: SnowflakeScraperAdapter instance
        """
        self.postgres = postgres_manager
        self.snowflake = snowflake_adapter or SnowflakeScraperAdapter()
        
        # Determine backend from environment
        self.backend = os.getenv('SCRAPER_DB_BACKEND', 'both').lower()
    
    def start_search_session(self, search_query: str, search_url: str = None,
                            total_results: int = 0) -> str:
        """Start search session in active backends"""
        session_id = None
        
        if self.backend in ['postgres', 'both'] and self.postgres:
            pg_session = self.postgres.start_search_session(
                search_query, search_url, total_results
            )
        
        if self.backend in ['snowflake', 'both'] and self.snowflake:
            session_id = self.snowflake.start_search_session(
                search_query, search_url, total_results
            )
        
        return session_id
    
    def insert_document(self, doc: Dict) -> bool:
        """Insert document to active backends"""
        success = True
        
        if self.backend in ['postgres', 'both'] and self.postgres:
            success = success and self.postgres.insert_document(doc)
        
        if self.backend in ['snowflake', 'both'] and self.snowflake:
            success = success and self.snowflake.insert_document(doc)
        
        return success
    
    def insert_law_firm(self, firm: Dict) -> str:
        """Insert law firm to active backends"""
        firm_id = None
        
        if self.backend in ['postgres', 'both'] and self.postgres:
            pg_id = self.postgres.insert_law_firm(firm)
        
        if self.backend in ['snowflake', 'both'] and self.snowflake:
            firm_id = self.snowflake.insert_law_firm(firm)
        
        return firm_id
    
    def close(self):
        """Close all database connections"""
        if self.postgres:
            self.postgres.close()
        if self.snowflake:
            self.snowflake.close()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    Example: Using Snowflake adapter with scraper
    
    Before running:
    1. Set SNOWFLAKE_* environment variables in .env
    2. Run snowflake_schema.sql in your Snowflake account
    """
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Option 1: Use Snowflake only
    print("Testing Snowflake adapter...")
    adapter = SnowflakeScraperAdapter()
    
    # Start a session
    session_id = adapter.start_search_session(
        search_query="Florida legal compliance",
        search_url="https://advance.lexisnexis.com/...",
        total_results=50
    )
    print(f"✓ Created session: {session_id}")
    
    # Insert a sample document
    sample_doc = {
        'id': 'test_doc_123',
        'title': 'Test Legal Document',
        'type': 'Case Law',
        'jurisdiction': 'Florida',
        'court': 'Florida Supreme Court',
        'date': '2024-10-25',
        'citation': '456 So. 3d 789',
        'url': 'https://example.com/case',
        'summary': 'This is a test case for Snowflake integration.',
        'content': 'Full text of the legal document...',
        'parties': ['Plaintiff A', 'Defendant B'],
        'judges': ['Chief Justice Smith'],
        'topics': ['Contract Law', 'Commercial Litigation']
    }
    
    if adapter.insert_document(sample_doc):
        print("✓ Document inserted to Snowflake")
    
    # Insert a law firm
    sample_firm = {
        'firm_name': 'Test & Associates',
        'city': 'Miami',
        'state': 'FL',
        'practice_areas': ['Personal Injury', 'Medical Malpractice'],
        'size_category': 'Small'
    }
    
    firm_id = adapter.insert_law_firm(sample_firm)
    if firm_id:
        print(f"✓ Law firm inserted: {firm_id}")
    
    adapter.close()
    print("\n✅ Snowflake integration test complete!")
