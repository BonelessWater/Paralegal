#!/usr/bin/env python3
"""
Quick test to check database connectivity with different hosts
"""

import psycopg2
import sys

def test_connection(host, description):
    """Test database connection"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Host: {host}")
    print('='*60)
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=5432,
            database="paralegal_db",
            user="paralegal_user",
            password="hackathon2024"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM legal_data.documents WHERE session_id = 5")
        count = cursor.fetchone()[0]
        
        print(f"✅ SUCCESS!")
        print(f"✅ Connected to database")
        print(f"✅ Found {count} Morgan & Morgan documents")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60)
    
    # Test different connection methods
    tests = [
        ("localhost", "Local connection (should work on AMD server)"),
        ("127.0.0.1", "Loopback IP"),
        ("134.199.202.8", "External IP (may be blocked)"),
    ]
    
    results = {}
    for host, description in tests:
        results[host] = test_connection(host, description)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for host, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{host:20s} {status}")
    
    # Recommendation
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    
    if results.get("localhost"):
        print("\n✅ Use 'localhost' for database connection")
        print("\nTo fix rag_embeddings.py, run it with:")
        print("  python3 rag_embeddings_local.py")
        print("\nOr modify data_loader to use localhost")
    elif results.get("127.0.0.1"):
        print("\n✅ Use '127.0.0.1' for database connection")
    else:
        print("\n⚠️  Database may not be running locally")
        print("   Check if PostgreSQL is running: sudo systemctl status postgresql")
    
    print("="*60)
