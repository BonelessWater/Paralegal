"""
Quick test script for the scraper
Tests basic functionality without actually scraping LexisNexis
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import requests
        print("✓ requests")
    except ImportError as e:
        print(f"✗ requests: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4")
    except ImportError as e:
        print(f"✗ beautifulsoup4: {e}")
        return False
    
    try:
        import psycopg2
        print("✓ psycopg2")
    except ImportError as e:
        print(f"✗ psycopg2: {e}")
        return False
    
    try:
        from selenium import webdriver
        print("✓ selenium")
    except ImportError as e:
        print(f"✗ selenium: {e}")
        return False
    
    print("\n✓ All imports successful!\n")
    return True


def test_config():
    """Test configuration file"""
    print("Testing configuration...")
    
    config_file = Path("config.ini")
    if not config_file.exists():
        print(f"✗ config.ini not found")
        print(f"  Please copy config.ini.example to config.ini")
        return False
    
    print("✓ config.ini exists")
    
    import configparser
    config = configparser.ConfigParser()
    config.read(config_file)
    
    required_sections = ['lexisnexis', 'database', 'scraping']
    for section in required_sections:
        if section in config:
            print(f"✓ Section [{section}] found")
        else:
            print(f"✗ Section [{section}] missing")
            return False
    
    # Check if credentials are still default
    if config['lexisnexis']['username'] == 'your_lexisnexis_username':
        print(f"⚠ Warning: LexisNexis credentials not configured")
        print(f"  Update config.ini with your actual credentials")
    
    if config['database']['password'] == 'your_db_password':
        print(f"⚠ Warning: Database password not configured")
        print(f"  Update config.ini with your actual password")
    
    print("\n✓ Configuration file valid!\n")
    return True


def test_database_connection():
    """Test database connectivity"""
    print("Testing database connection...")
    
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=config['database']['host'],
            port=config['database']['port'],
            database=config['database']['database'],
            user=config['database']['username'],
            password=config['database']['password']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[0][:50]}...")
        
        # Check if schema exists
        cursor.execute(f"""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = '{config['database']['schema']}'
        """)
        
        if cursor.fetchone():
            print(f"✓ Schema '{config['database']['schema']}' exists")
        else:
            print(f"⚠ Schema '{config['database']['schema']}' not found")
            print(f"  Run: python scrape.py --init-db")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database connection successful!\n")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print(f"  Check your config.ini database settings")
        print(f"  Make sure PostgreSQL is running")
        return False


def test_chromedriver():
    """Test ChromeDriver availability"""
    print("Testing ChromeDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('about:blank')
        driver.quit()
        
        print("✓ ChromeDriver is working")
        print("\n✓ ChromeDriver test successful!\n")
        return True
        
    except Exception as e:
        print(f"✗ ChromeDriver test failed: {e}")
        print(f"  Install ChromeDriver:")
        print(f"  - choco install chromedriver")
        print(f"  - Or download from https://chromedriver.chromium.org/")
        return False


def test_scraper_module():
    """Test that scraper module loads"""
    print("Testing scraper module...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from database import DatabaseManager
        print("✓ database.py imports successfully")
        
        # Note: Can't import scrape.py if config doesn't exist
        # Just check the file exists
        if Path("scrape.py").exists():
            print("✓ scrape.py exists")
        else:
            print("✗ scrape.py not found")
            return False
        
        print("\n✓ Scraper modules valid!\n")
        return True
        
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("LexisNexis Scraper - Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("Scraper Module Test", test_scraper_module),
        ("Database Connection Test", test_database_connection),
        ("ChromeDriver Test", test_chromedriver),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! The scraper is ready to use.")
        print("\nRun the scraper with:")
        print('  python scrape.py --query "law firm data compliance" --max-results 10')
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
