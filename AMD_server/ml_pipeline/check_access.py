"""
Diagnostic Script: Check Legal Database Access
Tests access to LexisNexis and CourtListener to determine available features.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccessChecker:
    """Check access levels for legal databases"""
    
    def __init__(self):
        self.results = {
            'lexisnexis': {},
            'courtlistener': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def check_courtlistener_api(self, api_token: Optional[str] = None) -> Dict:
        """
        Check CourtListener API access
        
        Args:
            api_token: Optional API token
            
        Returns:
            Dictionary with access details
        """
        logger.info("=" * 60)
        logger.info("CHECKING COURTLISTENER API ACCESS")
        logger.info("=" * 60)
        
        api_token = api_token or os.getenv('COURTLISTENER_API_TOKEN', '')
        base_url = "https://www.courtlistener.com/api/rest/v3"
        
        access_info = {
            'has_token': bool(api_token),
            'authenticated': False,
            'rate_limits': {},
            'available_endpoints': [],
            'test_results': {}
        }
        
        session = requests.Session()
        if api_token:
            session.headers.update({
                'Authorization': f'Token {api_token}',
                'Content-Type': 'application/json'
            })
        
        # Test different endpoints
        endpoints = [
            ('search', '/search/', {'q': 'test', 'type': 'o'}),
            ('opinions', '/opinions/', {}),
            ('dockets', '/dockets/', {}),
            ('clusters', '/clusters/', {}),
            ('courts', '/courts/', {})
        ]
        
        for name, endpoint, params in endpoints:
            try:
                logger.info(f"\nTesting {name} endpoint...")
                response = session.get(f"{base_url}{endpoint}", params=params, timeout=10)
                
                access_info['test_results'][name] = {
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'response_size': len(response.content)
                }
                
                if response.status_code == 200:
                    logger.info(f"✅ {name}: Accessible")
                    access_info['available_endpoints'].append(name)
                    
                    # Check rate limit headers
                    if 'X-RateLimit-Limit' in response.headers:
                        access_info['rate_limits'][name] = {
                            'limit': response.headers.get('X-RateLimit-Limit'),
                            'remaining': response.headers.get('X-RateLimit-Remaining'),
                            'reset': response.headers.get('X-RateLimit-Reset')
                        }
                        logger.info(f"   Rate limit: {access_info['rate_limits'][name]}")
                    
                    # Check result count
                    try:
                        data = response.json()
                        if 'count' in data:
                            logger.info(f"   Total results available: {data['count']}")
                            access_info['test_results'][name]['count'] = data['count']
                    except:
                        pass
                        
                elif response.status_code == 401:
                    logger.warning(f"❌ {name}: Authentication required")
                elif response.status_code == 403:
                    logger.warning(f"❌ {name}: Access forbidden (premium feature?)")
                elif response.status_code == 429:
                    logger.warning(f"⚠️  {name}: Rate limited")
                else:
                    logger.warning(f"⚠️  {name}: Status {response.status_code}")
                
                time.sleep(0.5)  # Be nice to the API
                
            except Exception as e:
                logger.error(f"❌ {name}: Error - {e}")
                access_info['test_results'][name] = {
                    'accessible': False,
                    'error': str(e)
                }
        
        access_info['authenticated'] = bool(access_info['available_endpoints'])
        
        return access_info
    
    def check_courtlistener_web(self, username: str = '', password: str = '') -> Dict:
        """
        Check CourtListener web access via browser
        
        Args:
            username: Optional username
            password: Optional password
            
        Returns:
            Dictionary with access details
        """
        logger.info("\n" + "=" * 60)
        logger.info("CHECKING COURTLISTENER WEB ACCESS")
        logger.info("=" * 60)
        
        access_info = {
            'has_credentials': bool(username and password),
            'can_login': False,
            'accessible_without_login': False,
            'premium_features': [],
            'free_features': []
        }
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Test unauthenticated access
            logger.info("\nTesting public access (no login)...")
            driver.get("https://www.courtlistener.com/")
            time.sleep(2)
            
            # Try a basic search
            try:
                driver.get("https://www.courtlistener.com/?q=employment%20discrimination&type=o")
                time.sleep(3)
                
                # Check if results are visible
                page_source = driver.page_source
                if 'results' in page_source.lower() or 'opinion' in page_source.lower():
                    access_info['accessible_without_login'] = True
                    access_info['free_features'].append('Basic search')
                    logger.info("✅ Basic search: Available without login")
                else:
                    logger.warning("⚠️  Basic search: May require login")
            except Exception as e:
                logger.error(f"❌ Basic search error: {e}")
            
            # Test login if credentials provided
            if username and password:
                logger.info(f"\nTesting login with username: {username}...")
                try:
                    driver.get("https://www.courtlistener.com/sign-in/")
                    time.sleep(2)
                    
                    wait = WebDriverWait(driver, 10)
                    username_field = wait.until(
                        EC.presence_of_element_located((By.NAME, "username"))
                    )
                    username_field.send_keys(username)
                    
                    password_field = driver.find_element(By.NAME, "password")
                    password_field.send_keys(password)
                    
                    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit_button.click()
                    time.sleep(3)
                    
                    # Check if login successful
                    if 'sign-in' not in driver.current_url.lower():
                        access_info['can_login'] = True
                        logger.info("✅ Login: Successful")
                        
                        # Check for premium features
                        driver.get("https://www.courtlistener.com/")
                        time.sleep(2)
                        page_source = driver.page_source
                        
                        if 'alert' in page_source.lower():
                            access_info['premium_features'].append('Search alerts')
                        if 'api' in page_source.lower():
                            access_info['premium_features'].append('API access')
                        if 'save' in page_source.lower():
                            access_info['premium_features'].append('Save searches')
                    else:
                        logger.warning("❌ Login: Failed - check credentials")
                        
                except Exception as e:
                    logger.error(f"❌ Login error: {e}")
            else:
                logger.info("⚠️  No credentials provided - skipping login test")
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Browser initialization error: {e}")
            logger.info("💡 Install ChromeDriver: brew install chromedriver (macOS)")
            access_info['error'] = str(e)
        
        return access_info
    
    def check_lexisnexis_access(self, username: str = '', password: str = '') -> Dict:
        """
        Check LexisNexis access
        
        Args:
            username: LexisNexis username
            password: LexisNexis password
            
        Returns:
            Dictionary with access details
        """
        logger.info("\n" + "=" * 60)
        logger.info("CHECKING LEXISNEXIS ACCESS")
        logger.info("=" * 60)
        
        access_info = {
            'has_credentials': bool(username and password),
            'can_login': False,
            'subscription_type': 'Unknown',
            'accessible_databases': []
        }
        
        if not username or not password:
            logger.warning("⚠️  No LexisNexis credentials provided")
            logger.info("💡 Credentials found in: AMD_server/scraper/config.ini")
            return access_info
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info(f"Testing login with username: {username}...")
            
            # Navigate to sign-in page
            signin_url = "https://signin.lexisnexis.com/lnaccess/app/signin"
            driver.get(signin_url)
            time.sleep(3)
            
            wait = WebDriverWait(driver, 20)
            
            # Enter username
            try:
                username_field = wait.until(
                    EC.presence_of_element_located((By.ID, "userid"))
                )
                username_field.send_keys(username)
                
                # Click next if button exists
                try:
                    next_button = driver.find_element(By.ID, "nextbtn")
                    next_button.click()
                    time.sleep(2)
                except:
                    pass
                
                # Enter password
                password_field = wait.until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                password_field.send_keys(password)
                
                # Submit
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "signin"))
                )
                submit_button.click()
                time.sleep(5)
                
                # Check if login successful
                current_url = driver.current_url
                if 'signin' not in current_url.lower():
                    access_info['can_login'] = True
                    logger.info("✅ Login: Successful")
                    
                    # Try to determine subscription type
                    page_source = driver.page_source
                    if 'academic' in page_source.lower():
                        access_info['subscription_type'] = 'Academic'
                    elif 'law firm' in page_source.lower():
                        access_info['subscription_type'] = 'Law Firm'
                    
                    # Check available databases
                    if 'case law' in page_source.lower():
                        access_info['accessible_databases'].append('Case Law')
                    if 'statutes' in page_source.lower():
                        access_info['accessible_databases'].append('Statutes')
                    if 'secondary sources' in page_source.lower():
                        access_info['accessible_databases'].append('Secondary Sources')
                    
                    logger.info(f"Subscription type: {access_info['subscription_type']}")
                    logger.info(f"Available databases: {access_info['accessible_databases']}")
                else:
                    logger.warning("❌ Login: Failed - still on signin page")
                    logger.info("💡 Check credentials in AMD_server/scraper/config.ini")
                    
            except TimeoutException:
                logger.error("❌ Login: Timeout - page elements not found")
            except Exception as e:
                logger.error(f"❌ Login error: {e}")
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Browser initialization error: {e}")
            access_info['error'] = str(e)
        
        return access_info
    
    def generate_report(self, output_file: str = 'access_report.json'):
        """Generate comprehensive access report"""
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING ACCESS REPORT")
        logger.info("=" * 60)
        
        # Save to JSON
        report_path = Path(__file__).parent / 'data' / output_file
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n✅ Report saved to: {report_path}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        
        # CourtListener
        cl_api = self.results.get('courtlistener', {}).get('api', {})
        cl_web = self.results.get('courtlistener', {}).get('web', {})
        
        logger.info("\n📊 CourtListener:")
        logger.info(f"  API Token: {'✅ Yes' if cl_api.get('has_token') else '❌ No'}")
        logger.info(f"  API Access: {'✅ Yes' if cl_api.get('authenticated') else '❌ No'}")
        logger.info(f"  Available Endpoints: {len(cl_api.get('available_endpoints', []))}")
        logger.info(f"  Web Access (no login): {'✅ Yes' if cl_web.get('accessible_without_login') else '❌ No'}")
        logger.info(f"  Can Login: {'✅ Yes' if cl_web.get('can_login') else '❌ No'}")
        
        # LexisNexis
        ln = self.results.get('lexisnexis', {})
        logger.info("\n📊 LexisNexis:")
        logger.info(f"  Has Credentials: {'✅ Yes' if ln.get('has_credentials') else '❌ No'}")
        logger.info(f"  Can Login: {'✅ Yes' if ln.get('can_login') else '❌ No'}")
        logger.info(f"  Subscription: {ln.get('subscription_type', 'Unknown')}")
        logger.info(f"  Databases: {', '.join(ln.get('accessible_databases', ['None']))}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if not cl_api.get('has_token'):
            logger.info("  • Get CourtListener API token: https://www.courtlistener.com/help/api/")
        if cl_web.get('accessible_without_login'):
            logger.info("  • CourtListener free tier available - no login needed for basic search")
        if ln.get('can_login'):
            logger.info("  • LexisNexis access confirmed - use for premium legal research")
        if not ln.get('can_login') and ln.get('has_credentials'):
            logger.info("  • Check LexisNexis credentials in AMD_server/scraper/config.ini")
        
        return report_path


def main():
    """Run access checks"""
    print("\n" + "=" * 60)
    print("LEGAL DATABASE ACCESS CHECKER")
    print("=" * 60)
    print("\nThis script will check your access to:")
    print("  1. CourtListener (API + Web)")
    print("  2. LexisNexis (Web)")
    print("\n" + "=" * 60)
    
    checker = AccessChecker()
    
    # Check CourtListener API
    api_token = os.getenv('COURTLISTENER_API_TOKEN', '')
    checker.results['courtlistener']['api'] = checker.check_courtlistener_api(api_token)
    
    # Check CourtListener Web
    cl_username = input("\nCourtListener username (press Enter to skip): ").strip()
    cl_password = input("CourtListener password (press Enter to skip): ").strip()
    checker.results['courtlistener']['web'] = checker.check_courtlistener_web(cl_username, cl_password)
    
    # Check LexisNexis
    # Read from config if available
    config_path = Path(__file__).parent.parent / 'scraper' / 'config.ini'
    ln_username = ''
    ln_password = ''
    
    if config_path.exists():
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        ln_username = config.get('lexisnexis', 'username', fallback='')
        ln_password = config.get('lexisnexis', 'password', fallback='')
        logger.info(f"\n✅ Found LexisNexis credentials in config file")
    else:
        ln_username = input("\nLexisNexis username (press Enter to skip): ").strip()
        ln_password = input("LexisNexis password (press Enter to skip): ").strip()
    
    checker.results['lexisnexis'] = checker.check_lexisnexis_access(ln_username, ln_password)
    
    # Generate report
    report_path = checker.generate_report()
    
    print("\n" + "=" * 60)
    print("✅ ACCESS CHECK COMPLETE")
    print("=" * 60)
    print(f"\nFull report saved to: {report_path}")
    print("\nNext steps:")
    print("  1. Review the report above")
    print("  2. Get API token if needed: https://www.courtlistener.com/help/api/")
    print("  3. Update config files with your credentials")
    print("\n")


if __name__ == "__main__":
    main()
