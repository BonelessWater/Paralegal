#!/usr/bin/env python3
"""
Quick test script to verify PostgreSQL connection and schema
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def test_database_connection():
    """Test database connection and schema"""
    
    print("Testing PostgreSQL Database Connection...")
    print("=" * 60)
    
    try:
        # Connection parameters
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='paralegal_db',
            user='paralegal_user',
            password='hackathon2024'
        )
        
        print("✓ Connected to database successfully!")
        
        # Test schema exists
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'legal_data'
        """)
        
        if cursor.fetchone():
            print("✓ Schema 'legal_data' exists")
        else:
            print("✗ Schema 'legal_data' not found")
            return False
        
        # Test tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'legal_data'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("✗ No tables found in legal_data schema")
            return False
        
        # Test insert and query
        print("\nTesting data insertion...")
        
        cursor.execute("""
            INSERT INTO legal_data.search_sessions 
            (search_query, total_results, status, notes) 
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, ("test query", 0, "test", "Database connection test"))
        
        session_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✓ Test record inserted (session_id: {session_id})")
        
        # Clean up test data
        cursor.execute("""
            DELETE FROM legal_data.search_sessions 
            WHERE id = %s
        """, (session_id,))
        
        conn.commit()
        print("✓ Test record deleted")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ All database tests passed!")
        print("=" * 60)
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n✗ Connection Error: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running: sudo systemctl status postgresql")
        print("  2. Database 'paralegal_db' exists")
        print("  3. User 'paralegal_user' has correct password")
        return False
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
