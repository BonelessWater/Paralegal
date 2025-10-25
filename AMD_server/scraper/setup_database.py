"""
Quick database setup script
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server (not a specific database)
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='paralegal_db'")
    exists = cursor.fetchone()
    
    if not exists:
        print("Creating database 'paralegal_db'...")
        cursor.execute("CREATE DATABASE paralegal_db")
        print("✓ Database created successfully!")
    else:
        print("✓ Database 'paralegal_db' already exists")
    
    cursor.close()
    conn.close()
    
    # Now connect to the database and initialize schema
    print("\nInitializing database schema...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='paralegal_db',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    
    # Read and execute schema file
    with open('database_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor.execute(schema_sql)
    conn.commit()
    
    print("✓ Database schema initialized successfully!")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Database setup complete! Ready to scrape.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nPlease check:")
    print("1. PostgreSQL is running")
    print("2. Username/password in config.ini are correct")
    print("3. You have permission to create databases")
