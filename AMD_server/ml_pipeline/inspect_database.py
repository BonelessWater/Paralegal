#!/usr/bin/env python3
"""
Database Schema Inspector
Connects to PostgreSQL and shows actual table structure
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def inspect_database():
    """Inspect actual database schema"""
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="paralegal_db",
            user="paralegal_user",
            password="hackathon2024"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=" * 80)
        print("DATABASE SCHEMA INSPECTION")
        print("=" * 80)
        
        # Get all schemas
        print("\n1. SCHEMAS:")
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        schemas = cursor.fetchall()
        for schema in schemas:
            print(f"   - {schema['schema_name']}")
        
        # Get all tables in legal_data schema
        print("\n2. TABLES IN 'legal_data' SCHEMA:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'legal_data'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("   ⚠️  No tables found in 'legal_data' schema!")
            
            # Check if documents table exists in public schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'documents'
            """)
            public_docs = cursor.fetchall()
            if public_docs:
                print("\n   ℹ️  'documents' table found in 'public' schema instead!")
        else:
            for table in tables:
                print(f"   - {table['table_name']}")
        
        # Inspect documents table structure (try both schemas)
        print("\n3. DOCUMENTS TABLE STRUCTURE:")
        
        for schema in ['legal_data', 'public']:
            try:
                cursor.execute(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = '{schema}' 
                    AND table_name = 'documents'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                if columns:
                    print(f"\n   Schema: {schema}.documents")
                    print(f"   {'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
                    print(f"   {'-'*80}")
                    for col in columns:
                        print(f"   {col['column_name']:<30} {col['data_type']:<20} "
                              f"{col['is_nullable']:<10} {str(col['column_default'] or ''):<20}")
                    break
            except:
                continue
        
        # Check what's actually in documents table
        print("\n4. SAMPLE DATA FROM DOCUMENTS TABLE:")
        
        for schema in ['legal_data', 'public']:
            try:
                cursor.execute(f"""
                    SELECT * FROM {schema}.documents 
                    WHERE session_id = 5 
                    LIMIT 1
                """)
                sample = cursor.fetchone()
                
                if sample:
                    print(f"\n   Schema: {schema}.documents")
                    print(f"   Found data with session_id = 5")
                    print(f"\n   Available columns:")
                    for key in sample.keys():
                        print(f"      - {key}")
                    break
            except Exception as e:
                continue
        
        # Count documents
        print("\n5. DOCUMENT COUNTS:")
        for schema in ['legal_data', 'public']:
            try:
                cursor.execute(f"""
                    SELECT 
                        session_id,
                        COUNT(*) as count
                    FROM {schema}.documents 
                    GROUP BY session_id
                    ORDER BY session_id
                """)
                counts = cursor.fetchall()
                
                if counts:
                    print(f"\n   Schema: {schema}.documents")
                    for row in counts:
                        print(f"      Session {row['session_id']}: {row['count']} documents")
            except:
                continue
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_database()
