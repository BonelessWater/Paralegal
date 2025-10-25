"""
Database module for PostgreSQL integration
Handles connections and data insertion for scraped legal data
"""

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from psycopg2 import pool
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize database connection pool
        
        Args:
            config: Dictionary with database connection parameters
                   (host, port, database, username, password, schema)
        """
        self.config = config
        self.schema = config.get('schema', 'legal_data')
        self.connection_pool = None
        
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # min and max connections
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['username'],
                password=config['password']
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        raise Exception("Connection pool not initialized")
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")
    
    def initialize_schema(self, schema_file: str):
        """
        Initialize database schema from SQL file
        
        Args:
            schema_file: Path to SQL schema file
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            cursor.execute(schema_sql)
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def create_search_session(self, search_query: str, search_url: str, 
                            total_results: int = 0) -> int:
        """
        Create a new search session record
        
        Args:
            search_query: The search query used
            search_url: URL of the search
            total_results: Total number of results found
            
        Returns:
            session_id: ID of the created session
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.search_sessions 
                (search_query, search_url, total_results, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (search_query, search_url, total_results, 'in_progress')
            )
            
            session_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Created search session {session_id}")
            return session_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create search session: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def update_search_session(self, session_id: int, status: str, notes: str = None):
        """Update search session status"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                UPDATE {self.schema}.search_sessions
                SET status = %s, notes = %s
                WHERE id = %s
                """,
                (status, notes, session_id)
            )
            
            conn.commit()
            logger.info(f"Updated search session {session_id} to status: {status}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to update search session: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def insert_document(self, session_id: int, document_data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a legal document into the database
        
        Args:
            session_id: ID of the search session
            document_data: Dictionary containing document information
            
        Returns:
            document_id: ID of the inserted document, or None if already exists
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if document already exists
            cursor.execute(
                f"SELECT id FROM {self.schema}.documents WHERE document_id = %s",
                (document_data.get('document_id'),)
            )
            existing = cursor.fetchone()
            
            if existing:
                logger.debug(f"Document {document_data.get('document_id')} already exists")
                return existing[0]
            
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.documents 
                (session_id, document_id, title, document_type, jurisdiction, 
                 court, decision_date, citation, url, summary, full_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    document_data.get('document_id'),
                    document_data.get('title'),
                    document_data.get('document_type'),
                    document_data.get('jurisdiction'),
                    document_data.get('court'),
                    document_data.get('decision_date'),
                    document_data.get('citation'),
                    document_data.get('url'),
                    document_data.get('summary'),
                    document_data.get('full_text')
                )
            )
            
            doc_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Inserted document {doc_id}")
            return doc_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to insert document: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def insert_law_firm(self, firm_data: Dict[str, str]) -> int:
        """
        Insert or get law firm ID
        
        Args:
            firm_data: Dictionary with law firm information
            
        Returns:
            firm_id: ID of the law firm
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try to get existing firm
            cursor.execute(
                f"SELECT id FROM {self.schema}.law_firms WHERE firm_name = %s",
                (firm_data.get('firm_name'),)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Insert new firm
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.law_firms 
                (firm_name, address, city, state, country, website)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    firm_data.get('firm_name'),
                    firm_data.get('address'),
                    firm_data.get('city'),
                    firm_data.get('state'),
                    firm_data.get('country'),
                    firm_data.get('website')
                )
            )
            
            firm_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Inserted law firm {firm_id}: {firm_data.get('firm_name')}")
            return firm_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to insert law firm: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def link_document_to_firm(self, document_id: int, firm_id: int, role: str = None):
        """Link a document to a law firm"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.document_law_firms 
                (document_id, law_firm_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, law_firm_id, role) DO NOTHING
                """,
                (document_id, firm_id, role)
            )
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to link document to firm: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def insert_compliance_topic(self, topic_name: str, description: str = None, 
                               category: str = None) -> int:
        """
        Insert or get compliance topic ID
        
        Args:
            topic_name: Name of the compliance topic
            description: Optional description
            category: Optional category
            
        Returns:
            topic_id: ID of the compliance topic
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try to get existing topic
            cursor.execute(
                f"SELECT id FROM {self.schema}.compliance_topics WHERE topic_name = %s",
                (topic_name,)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Insert new topic
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.compliance_topics 
                (topic_name, description, category)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (topic_name, description, category)
            )
            
            topic_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Inserted compliance topic {topic_id}: {topic_name}")
            return topic_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to insert compliance topic: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def link_document_to_topic(self, document_id: int, topic_id: int, 
                              relevance_score: float = None):
        """Link a document to a compliance topic"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                INSERT INTO {self.schema}.document_topics 
                (document_id, topic_id, relevance_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, topic_id) DO NOTHING
                """,
                (document_id, topic_id, relevance_score)
            )
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to link document to topic: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """Get statistics for a search session"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                f"""
                SELECT 
                    ss.id,
                    ss.search_query,
                    ss.total_results,
                    ss.status,
                    ss.scraped_at,
                    COUNT(d.id) as documents_scraped
                FROM {self.schema}.search_sessions ss
                LEFT JOIN {self.schema}.documents d ON d.session_id = ss.id
                WHERE ss.id = %s
                GROUP BY ss.id, ss.search_query, ss.total_results, ss.status, ss.scraped_at
                """,
                (session_id,)
            )
            
            result = cursor.fetchone()
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
