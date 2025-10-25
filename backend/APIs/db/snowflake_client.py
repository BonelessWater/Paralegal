#!/usr/bin/env python3
"""
Snowflake Database Client for AI Legal Tender
Handles legal data storage, retrieval, and analytics for the hackathon
"""

import os
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.connector.errors import ProgrammingError, DatabaseError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Client for interacting with Snowflake data warehouse"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize Snowflake connection from config or environment variables
        
        Args:
            config: Optional dict with Snowflake credentials
                   If None, reads from environment variables
        """
        if config:
            self.account = config.get('account')
            self.user = config.get('user')
            self.password = config.get('password')
            self.warehouse = config.get('warehouse', 'COMPUTE_WH')
            self.database = config.get('database', 'PARALEGAL_DB')
            self.schema = config.get('schema', 'LEGAL_DATA')
        else:
            # Read from environment variables
            self.account = os.getenv('SNOWFLAKE_ACCOUNT')
            self.user = os.getenv('SNOWFLAKE_USER')
            self.password = os.getenv('SNOWFLAKE_PASSWORD')
            self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
            self.database = os.getenv('SNOWFLAKE_DATABASE', 'PARALEGAL_DB')
            self.schema = os.getenv('SNOWFLAKE_SCHEMA', 'LEGAL_DATA')
        
        self.conn = None
        self._validate_config()
        
    def _validate_config(self):
        """Validate that all required configuration is present"""
        required = ['account', 'user', 'password']
        missing = [field for field in required if not getattr(self, field)]
        
        if missing:
            raise ValueError(
                f"Missing required Snowflake configuration: {', '.join(missing)}\n"
                f"Set environment variables: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD"
            )
    
    def connect(self) -> bool:
        """
        Establish connection to Snowflake
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
                client_session_keep_alive=True
            )
            logger.info(f"✓ Connected to Snowflake: {self.database}.{self.schema}")
            return True
            
        except DatabaseError as e:
            logger.error(f"✗ Snowflake connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close Snowflake connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Disconnected from Snowflake")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a SELECT query and return results as list of dicts
        
        Args:
            query: SQL query string
            params: Optional tuple of query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        try:
            cursor = self.conn.cursor(DictCursor)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"✗ Query execution failed: {e}")
            return []
    
    def execute_command(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Execute an INSERT/UPDATE/DELETE command
        
        Args:
            query: SQL command string
            params: Optional tuple of query parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"✗ Command execution failed: {e}")
            return False
    
    # ========================================================================
    # SEARCH SESSIONS
    # ========================================================================
    
    def create_search_session(self, search_query: str, search_url: str = None,
                             total_results: int = 0, notes: str = None) -> str:
        """
        Create a new search session record
        
        Args:
            search_query: The search query used
            search_url: URL of the search
            total_results: Number of results found
            notes: Optional notes
            
        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO SEARCH_SESSIONS 
        (SESSION_ID, SEARCH_QUERY, SEARCH_URL, TOTAL_RESULTS, NOTES)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        success = self.execute_command(
            query, 
            (session_id, search_query, search_url, total_results, notes)
        )
        
        if success:
            logger.info(f"✓ Created search session: {session_id}")
            return session_id
        return None
    
    # ========================================================================
    # DOCUMENTS
    # ========================================================================
    
    def insert_document(self, doc_data: Dict) -> bool:
        """
        Insert a legal document into Snowflake
        
        Args:
            doc_data: Dict with document fields (document_id, title, etc.)
            
        Returns:
            True if successful
        """
        try:
            # Convert VARIANT fields to JSON strings
            for field in ['parties', 'judges', 'topics']:
                if field in doc_data and doc_data[field]:
                    if not isinstance(doc_data[field], str):
                        doc_data[field] = json.dumps(doc_data[field])
            
            query = """
            INSERT INTO DOCUMENTS 
            (DOCUMENT_ID, SESSION_ID, TITLE, DOCUMENT_TYPE, JURISDICTION, 
             COURT, DECISION_DATE, CITATION, URL, SUMMARY, FULL_TEXT,
             PARTIES, JUDGES, TOPICS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    PARSE_JSON(%s), PARSE_JSON(%s), PARSE_JSON(%s))
            """
            
            params = (
                doc_data.get('document_id'),
                doc_data.get('session_id'),
                doc_data.get('title'),
                doc_data.get('document_type'),
                doc_data.get('jurisdiction'),
                doc_data.get('court'),
                doc_data.get('decision_date'),
                doc_data.get('citation'),
                doc_data.get('url'),
                doc_data.get('summary'),
                doc_data.get('full_text'),
                doc_data.get('parties', '[]'),
                doc_data.get('judges', '[]'),
                doc_data.get('topics', '[]')
            )
            
            success = self.execute_command(query, params)
            
            if success:
                logger.info(f"✓ Inserted document: {doc_data.get('document_id')}")
            return success
            
        except Exception as e:
            logger.error(f"✗ Failed to insert document: {e}")
            return False
    
    def bulk_insert_documents(self, documents: List[Dict]) -> int:
        """
        Bulk insert multiple documents (faster than individual inserts)
        
        Args:
            documents: List of document dicts
            
        Returns:
            Number of documents successfully inserted
        """
        success_count = 0
        
        for doc in documents:
            if self.insert_document(doc):
                success_count += 1
        
        logger.info(f"✓ Bulk inserted {success_count}/{len(documents)} documents")
        return success_count
    
    def search_documents(self, query_text: str = None, jurisdiction: str = None,
                        document_type: str = None, limit: int = 10) -> List[Dict]:
        """
        Search documents by various criteria
        
        Args:
            query_text: Text to search in title/summary/full_text
            jurisdiction: Filter by jurisdiction
            document_type: Filter by document type
            limit: Max number of results
            
        Returns:
            List of matching documents
        """
        conditions = []
        params = []
        
        if query_text:
            conditions.append(
                "(TITLE ILIKE %s OR SUMMARY ILIKE %s OR FULL_TEXT ILIKE %s)"
            )
            search_term = f"%{query_text}%"
            params.extend([search_term, search_term, search_term])
        
        if jurisdiction:
            conditions.append("JURISDICTION = %s")
            params.append(jurisdiction)
        
        if document_type:
            conditions.append("DOCUMENT_TYPE = %s")
            params.append(document_type)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT * FROM DOCUMENTS
        WHERE {where_clause}
        ORDER BY DECISION_DATE DESC
        LIMIT %s
        """
        
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    
    # ========================================================================
    # LAW FIRMS
    # ========================================================================
    
    def insert_law_firm(self, firm_data: Dict) -> Optional[str]:
        """
        Insert a law firm record
        
        Args:
            firm_data: Dict with firm fields
            
        Returns:
            Firm ID if successful, None otherwise
        """
        firm_id = firm_data.get('firm_id') or str(uuid.uuid4())
        
        # Convert practice_areas to JSON if needed
        practice_areas = firm_data.get('practice_areas', [])
        if not isinstance(practice_areas, str):
            practice_areas = json.dumps(practice_areas)
        
        query = """
        INSERT INTO LAW_FIRMS 
        (FIRM_ID, FIRM_NAME, ADDRESS, CITY, STATE, COUNTRY, 
         ZIP_CODE, PHONE, WEBSITE, PRACTICE_AREAS, SIZE_CATEGORY)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s), %s)
        """
        
        params = (
            firm_id,
            firm_data.get('firm_name'),
            firm_data.get('address'),
            firm_data.get('city'),
            firm_data.get('state'),
            firm_data.get('country', 'USA'),
            firm_data.get('zip_code'),
            firm_data.get('phone'),
            firm_data.get('website'),
            practice_areas,
            firm_data.get('size_category')
        )
        
        if self.execute_command(query, params):
            logger.info(f"✓ Inserted law firm: {firm_data.get('firm_name')}")
            return firm_id
        
        return None
    
    def get_law_firm_by_name(self, firm_name: str) -> Optional[Dict]:
        """Get law firm by name (case-insensitive)"""
        query = "SELECT * FROM LAW_FIRMS WHERE FIRM_NAME ILIKE %s LIMIT 1"
        results = self.execute_query(query, (firm_name,))
        return results[0] if results else None
    
    # ========================================================================
    # COMPLIANCE ISSUES
    # ========================================================================
    
    def insert_compliance_issue(self, issue_data: Dict) -> Optional[str]:
        """
        Insert a compliance issue record
        
        Args:
            issue_data: Dict with issue fields
            
        Returns:
            Issue ID if successful
        """
        issue_id = issue_data.get('issue_id') or str(uuid.uuid4())
        
        query = """
        INSERT INTO COMPLIANCE_ISSUES
        (ISSUE_ID, DOCUMENT_ID, FIRM_ID, ISSUE_TYPE, SEVERITY,
         DESCRIPTION, OUTCOME, SANCTION_AMOUNT, RESOLUTION_DATE, STATUS)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            issue_id,
            issue_data.get('document_id'),
            issue_data.get('firm_id'),
            issue_data.get('issue_type'),
            issue_data.get('severity'),
            issue_data.get('description'),
            issue_data.get('outcome'),
            issue_data.get('sanction_amount'),
            issue_data.get('resolution_date'),
            issue_data.get('status', 'Open')
        )
        
        if self.execute_command(query, params):
            logger.info(f"✓ Inserted compliance issue: {issue_id}")
            return issue_id
        
        return None
    
    def get_recent_violations(self, limit: int = 20) -> List[Dict]:
        """Get recent compliance violations"""
        query = """
        SELECT * FROM VW_RECENT_VIOLATIONS
        ORDER BY DECISION_DATE DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    # ========================================================================
    # ANALYTICS (for AI agents and demo dashboard)
    # ========================================================================
    
    def get_firm_statistics(self) -> List[Dict]:
        """Get statistics for all law firms"""
        query = "SELECT * FROM VW_FIRM_ACTIVITY ORDER BY TOTAL_CASES DESC"
        return self.execute_query(query)
    
    def get_case_count_by_jurisdiction(self) -> List[Dict]:
        """Get case counts grouped by jurisdiction"""
        query = """
        SELECT 
            JURISDICTION,
            COUNT(*) AS CASE_COUNT,
            COUNT(DISTINCT DOCUMENT_TYPE) AS DOCUMENT_TYPES
        FROM DOCUMENTS
        GROUP BY JURISDICTION
        ORDER BY CASE_COUNT DESC
        """
        return self.execute_query(query)
    
    def get_total_stats(self) -> Dict:
        """Get overall database statistics"""
        stats = {}
        
        # Total documents
        result = self.execute_query("SELECT COUNT(*) AS CNT FROM DOCUMENTS")
        stats['total_documents'] = result[0]['CNT'] if result else 0
        
        # Total firms
        result = self.execute_query("SELECT COUNT(*) AS CNT FROM LAW_FIRMS")
        stats['total_firms'] = result[0]['CNT'] if result else 0
        
        # Total compliance issues
        result = self.execute_query("SELECT COUNT(*) AS CNT FROM COMPLIANCE_ISSUES")
        stats['total_compliance_issues'] = result[0]['CNT'] if result else 0
        
        # Total critical issues
        result = self.execute_query(
            "SELECT COUNT(*) AS CNT FROM COMPLIANCE_ISSUES WHERE SEVERITY = 'Critical'"
        )
        stats['critical_issues'] = result[0]['CNT'] if result else 0
        
        return stats


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_client() -> SnowflakeClient:
    """
    Get a connected Snowflake client (convenience function)
    
    Returns:
        Connected SnowflakeClient instance
    """
    client = SnowflakeClient()
    client.connect()
    return client


# ============================================================================
# DEMO USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of SnowflakeClient
    
    Before running:
    1. Set environment variables in .env:
       SNOWFLAKE_ACCOUNT=GUWYXHN-OF53265
       SNOWFLAKE_USER=IMDANIAL
       SNOWFLAKE_PASSWORD=your_password
       SNOWFLAKE_WAREHOUSE=COMPUTE_WH
       SNOWFLAKE_DATABASE=PARALEGAL_DB
       SNOWFLAKE_SCHEMA=LEGAL_DATA
    
    2. Run snowflake_schema.sql in your Snowflake account
    """
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create and connect client
    client = SnowflakeClient()
    
    if not client.connect():
        print("Failed to connect to Snowflake")
        exit(1)
    
    try:
        # Example 1: Create a search session
        print("\n1. Creating search session...")
        session_id = client.create_search_session(
            search_query="law firm compliance violations Florida",
            search_url="https://advance.lexisnexis.com/...",
            total_results=150
        )
        print(f"Session ID: {session_id}")
        
        # Example 2: Insert a document
        print("\n2. Inserting sample document...")
        doc_data = {
            'document_id': 'doc_' + str(uuid.uuid4()),
            'session_id': session_id,
            'title': 'Sample Compliance Case - Smith Law Firm',
            'document_type': 'Court Decision',
            'jurisdiction': 'Florida',
            'court': 'Florida Supreme Court',
            'decision_date': '2024-01-15',
            'citation': '123 F.3d 456',
            'url': 'https://example.com/case123',
            'summary': 'Law firm sanctioned for failure to comply with discovery obligations.',
            'full_text': 'Full text of the court decision...',
            'parties': ['Smith Law Firm', 'State Bar of Florida'],
            'judges': ['Judge Johnson', 'Judge Williams'],
            'topics': ['Legal Ethics', 'Discovery Obligations']
        }
        client.insert_document(doc_data)
        
        # Example 3: Insert law firm
        print("\n3. Inserting sample law firm...")
        firm_id = client.insert_law_firm({
            'firm_name': 'Smith Law Firm',
            'city': 'Miami',
            'state': 'FL',
            'practice_areas': ['Personal Injury', 'Medical Malpractice'],
            'size_category': 'Medium'
        })
        
        # Example 4: Insert compliance issue
        print("\n4. Inserting compliance issue...")
        client.insert_compliance_issue({
            'document_id': doc_data['document_id'],
            'firm_id': firm_id,
            'issue_type': 'Discovery Violation',
            'severity': 'High',
            'description': 'Failed to produce documents within court-ordered deadline',
            'outcome': 'Monetary Sanction',
            'sanction_amount': 5000.00,
            'status': 'Resolved'
        })
        
        # Example 5: Search documents
        print("\n5. Searching documents...")
        results = client.search_documents(
            query_text="compliance",
            jurisdiction="Florida",
            limit=5
        )
        print(f"Found {len(results)} documents")
        for doc in results:
            print(f"  - {doc['TITLE']}")
        
        # Example 6: Get statistics
        print("\n6. Getting database statistics...")
        stats = client.get_total_stats()
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Total Law Firms: {stats['total_firms']}")
        print(f"Total Compliance Issues: {stats['total_compliance_issues']}")
        print(f"Critical Issues: {stats['critical_issues']}")
        
        print("\n✅ All examples completed successfully!")
        
    finally:
        client.disconnect()
