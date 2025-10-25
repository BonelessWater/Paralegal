"""
LexisNexis Advance Web Scraper
Scrapes legal compliance data and stores it in PostgreSQL database
"""

import time
import logging
import configparser
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from database import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LexisNexisScraper:
    """Scraper for LexisNexis Advance legal database"""
    
    def __init__(self, config_file: str = 'config.ini'):
        """
        Initialize the scraper with configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.db = DatabaseManager(self.config['database'])
        self.session = self._create_session()
        self.driver = None
        self.is_authenticated = False
        
        logger.info("LexisNexis scraper initialized")
    
    def _load_config(self, config_file: str) -> Dict[str, Dict[str, Any]]:
        """Load configuration from INI file"""
        if not Path(config_file).exists():
            raise FileNotFoundError(
                f"Config file '{config_file}' not found. "
                f"Please copy config.ini.example to config.ini and fill in your credentials."
            )
        
        config = configparser.ConfigParser()
        config.read(config_file)
        
        return {
            'lexisnexis': dict(config['lexisnexis']),
            'database': dict(config['database']),
            'scraping': {
                'request_delay': config.getfloat('scraping', 'request_delay'),
                'max_retries': config.getint('scraping', 'max_retries'),
                'timeout': config.getint('scraping', 'timeout'),
                'user_agent': config.get('scraping', 'user_agent')
            }
        }
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config['scraping']['max_retries'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': self.config['scraping']['user_agent']
        })
        
        return session
    
    def _init_selenium_driver(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver for JavaScript-heavy pages"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.config["scraping"]["user_agent"]}')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.info("Make sure ChromeDriver is installed and in your PATH")
            raise
    
    def authenticate(self) -> bool:
        """
        Authenticate with LexisNexis using Selenium
        
        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.driver:
                self.driver = self._init_selenium_driver()
            
            logger.info("Attempting to authenticate with LexisNexis...")
            
            # Navigate to sign-in page
            signin_url = "https://signin.lexisnexis.com/lnaccess/app/signin"
            self.driver.get(signin_url)
            
            # Wait for username field and enter credentials
            wait = WebDriverWait(self.driver, 20)
            
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "userid"))
            )
            username_field.send_keys(self.config['lexisnexis']['username'])
            
            # Click next or find password field
            try:
                next_button = self.driver.find_element(By.ID, "nextbtn")
                next_button.click()
                time.sleep(2)
            except NoSuchElementException:
                pass
            
            # Enter password
            password_field = wait.until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys(self.config['lexisnexis']['password'])
            
            # Submit form
            submit_button = wait.until(
                EC.element_to_be_clickable((By.ID, "signin"))
            )
            submit_button.click()
            
            # Wait for redirect to main page
            time.sleep(5)
            
            # Check if we're on the main page (not login page)
            current_url = self.driver.current_url
            if 'signin' not in current_url.lower():
                self.is_authenticated = True
                logger.info("Successfully authenticated with LexisNexis")
                return True
            else:
                logger.error("Authentication failed - still on sign-in page")
                return False
                
        except TimeoutException:
            logger.error("Timeout during authentication")
            return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def search(self, query: str, max_results: int = None) -> int:
        """
        Perform a search on LexisNexis
        
        Args:
            query: Search query
            max_results: Maximum number of results to scrape
            
        Returns:
            session_id: Database session ID for this search
        """
        if not self.is_authenticated:
            if not self.authenticate():
                raise Exception("Failed to authenticate with LexisNexis")
        
        logger.info(f"Searching for: {query}")
        
        # Navigate to search page
        search_url = f"{self.config['lexisnexis']['base_url']}/search/"
        self.driver.get(search_url)
        time.sleep(2)
        
        try:
            # Find search box and enter query
            wait = WebDriverWait(self.driver, 20)
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[name='search']"))
            )
            search_box.clear()
            search_box.send_keys(query)
            
            # Submit search
            search_box.submit()
            time.sleep(5)
            
            # Create database session
            session_id = self.db.create_search_session(
                search_query=query,
                search_url=self.driver.current_url,
                total_results=0
            )
            
            logger.info(f"Created search session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def scrape_search_results(self, session_id: int, max_results: int = 100) -> List[Dict]:
        """
        Scrape search results from current page
        
        Args:
            session_id: Database session ID
            max_results: Maximum number of results to scrape
            
        Returns:
            List of scraped documents
        """
        documents = []
        scraped_count = 0
        page_num = 1
        
        try:
            while scraped_count < max_results:
                logger.info(f"Scraping page {page_num}...")
                
                # Get page source and parse with BeautifulSoup
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find result items (this will need to be adjusted based on actual HTML structure)
                result_items = soup.find_all('div', class_=re.compile(r'result|document|case'))
                
                if not result_items:
                    logger.warning("No results found on page - trying alternative selectors")
                    result_items = soup.find_all('article') or soup.find_all('li', class_=re.compile(r'result'))
                
                if not result_items:
                    logger.warning("Could not find any results on this page")
                    break
                
                for item in result_items:
                    if scraped_count >= max_results:
                        break
                    
                    try:
                        # Extract document data (adjust selectors based on actual HTML)
                        document_data = self._extract_document_data(item)
                        
                        if document_data:
                            # Insert into database
                            doc_id = self.db.insert_document(session_id, document_data)
                            
                            if doc_id:
                                documents.append(document_data)
                                scraped_count += 1
                                logger.info(f"Scraped document {scraped_count}/{max_results}")
                            
                            # Delay between items
                            time.sleep(self.config['scraping']['request_delay'])
                    
                    except Exception as e:
                        logger.error(f"Error scraping document: {e}")
                        continue
                
                # Try to go to next page
                if scraped_count < max_results:
                    if not self._go_to_next_page():
                        logger.info("No more pages available")
                        break
                    page_num += 1
                    time.sleep(self.config['scraping']['request_delay'])
                else:
                    break
            
            # Update session
            self.db.update_search_session(
                session_id,
                status='completed',
                notes=f'Scraped {scraped_count} documents'
            )
            
            logger.info(f"Scraping completed: {scraped_count} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self.db.update_search_session(
                session_id,
                status='failed',
                notes=str(e)
            )
            raise
    
    def _extract_document_data(self, item: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract document data from a result item
        
        Args:
            item: BeautifulSoup element containing document info
            
        Returns:
            Dictionary with document data
        """
        try:
            # These selectors are generic and will need to be adjusted
            # based on the actual HTML structure of LexisNexis results
            
            title_elem = item.find(['h2', 'h3', 'a'], class_=re.compile(r'title|heading'))
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract document ID from URL or data attribute
            link_elem = item.find('a', href=True)
            url = link_elem['href'] if link_elem else None
            document_id = None
            
            if url:
                # Try to extract document ID from URL
                id_match = re.search(r'document[=/]([a-zA-Z0-9-]+)', url)
                if id_match:
                    document_id = id_match.group(1)
                else:
                    # Use URL as document ID if no specific ID found
                    document_id = url.split('/')[-1][:255]
            
            # Extract other fields
            citation_elem = item.find(text=re.compile(r'\d+\s+[A-Z][a-z]+\.?\s+\d+'))
            citation = citation_elem.strip() if citation_elem else None
            
            date_elem = item.find(text=re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}|\w+\s+\d+,\s+\d{4}'))
            decision_date = None
            if date_elem:
                try:
                    # Try to parse date
                    decision_date = self._parse_date(date_elem.strip())
                except:
                    pass
            
            # Extract summary/snippet
            summary_elem = item.find(['p', 'div'], class_=re.compile(r'summary|snippet|abstract'))
            summary = summary_elem.get_text(strip=True) if summary_elem else None
            
            # Extract jurisdiction/court
            jurisdiction_elem = item.find(text=re.compile(r'Court|Jurisdiction'))
            jurisdiction = None
            court = None
            
            if jurisdiction_elem:
                parent = jurisdiction_elem.find_parent()
                if parent:
                    jurisdiction = parent.get_text(strip=True)
            
            document_data = {
                'document_id': document_id or f"doc_{int(time.time())}",
                'title': title,
                'document_type': 'case',  # Default, can be refined
                'jurisdiction': jurisdiction,
                'court': court,
                'decision_date': decision_date,
                'citation': citation,
                'url': url,
                'summary': summary,
                'full_text': None  # Would require visiting each document page
            }
            
            return document_data
            
        except Exception as e:
            logger.error(f"Error extracting document data: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _go_to_next_page(self) -> bool:
        """
        Navigate to next page of results
        
        Returns:
            bool: True if successfully navigated to next page
        """
        try:
            # Look for "Next" button (adjust selector as needed)
            next_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                'a[aria-label*="Next"], button[aria-label*="Next"], .pagination .next'
            )
            
            if next_button.is_enabled():
                next_button.click()
                time.sleep(3)
                return True
            
        except NoSuchElementException:
            logger.info("Next button not found")
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
        
        return False
    
    def scrape_document_details(self, document_url: str) -> Dict[str, Any]:
        """
        Scrape full details of a specific document
        
        Args:
            document_url: URL of the document
            
        Returns:
            Dictionary with full document data
        """
        try:
            self.driver.get(document_url)
            time.sleep(3)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract full text (adjust selectors as needed)
            full_text_elem = soup.find('div', class_=re.compile(r'document-body|full-text|content'))
            full_text = full_text_elem.get_text(separator='\n', strip=True) if full_text_elem else None
            
            return {
                'full_text': full_text
            }
            
        except Exception as e:
            logger.error(f"Error scraping document details: {e}")
            return {}
    
    def run(self, query: str = None, max_results: int = 100):
        """
        Run the complete scraping process
        
        Args:
            query: Search query (uses config if not provided)
            max_results: Maximum results to scrape
        """
        try:
            # Use query from config if not provided
            if not query:
                query = self.config['lexisnexis']['search_query']
            
            # Perform search
            session_id = self.search(query, max_results)
            
            # Scrape results
            documents = self.scrape_search_results(session_id, max_results)
            
            logger.info(f"Successfully scraped {len(documents)} documents")
            
            # Print statistics
            stats = self.db.get_session_stats(session_id)
            logger.info(f"Session stats: {stats}")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            self.close()
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
        
        if self.db:
            self.db.close_all_connections()
            logger.info("Database connections closed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape LexisNexis Advance')
    parser.add_argument('--config', default='config.ini', help='Config file path')
    parser.add_argument('--query', help='Search query (overrides config)')
    parser.add_argument('--max-results', type=int, default=100, help='Max results to scrape')
    parser.add_argument('--init-db', action='store_true', help='Initialize database schema')
    
    args = parser.parse_args()
    
    scraper = LexisNexisScraper(args.config)
    
    if args.init_db:
        logger.info("Initializing database schema...")
        scraper.db.initialize_schema('database_schema.sql')
        logger.info("Database schema initialized")
    
    scraper.run(query=args.query, max_results=args.max_results)


if __name__ == '__main__':
    main()
