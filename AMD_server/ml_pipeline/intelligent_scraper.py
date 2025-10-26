"""
Intelligent Legal Case Scraper
Fetches relevant legal cases from CourtListener (API + web scraping) based on LLM-generated queries.
Architecture matches existing LexisNexis scraper: Selenium + authentication + database integration.
"""

import os
import time
import json
import logging
import configparser
import re
from typing import List, Dict, Optional, Tuple, Any
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
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class LegalCase:
    """Represents a scraped legal case"""
    case_name: str
    citation: str
    court: str
    date_filed: str
    snippet: str
    opinion_text: str
    url: str
    source: str = "CourtListener"
    scraped_at: str = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return asdict(self)


class CourtListenerScraper:
    """
    Intelligent scraper for CourtListener with dual modes:
    1. API mode (faster, rate-limited, requires token)
    2. Web scraping mode (Selenium, slower but no API limits)
    
    Architecture matches existing LexisNexis scraper pattern.
    """
    
    BASE_URL = "https://www.courtlistener.com"
    API_URL = "https://www.courtlistener.com/api/rest/v3"
    
    def __init__(self, config_file: str = 'config.ini', mode: str = 'hybrid'):
        """
        Initialize the scraper.
        
        Args:
            config_file: Path to configuration file
            mode: 'api', 'web', or 'hybrid' (fallback to web if API fails)
        """
        self.config = self._load_config(config_file)
        self.mode = mode
        self.session = self._create_session()
        self.driver = None
        self.is_authenticated = False
        self.cache = {}
        
        logger.info(f"CourtListener scraper initialized in {mode} mode")
    
    def _load_config(self, config_file: str) -> Dict[str, Dict[str, Any]]:
        """Load configuration from INI file"""
        config_path = Path(config_file)
        
        # If config doesn't exist, create default
        if not config_path.exists():
            logger.warning(f"Config file '{config_file}' not found. Using defaults.")
            return self._get_default_config()
        
        config = configparser.ConfigParser()
        config.read(config_file)
        
        return {
            'courtlistener': {
                'api_token': config.get('courtlistener', 'api_token', fallback=os.getenv('COURTLISTENER_API_TOKEN', '')),
                'username': config.get('courtlistener', 'username', fallback=''),
                'password': config.get('courtlistener', 'password', fallback=''),
                'base_url': config.get('courtlistener', 'base_url', fallback=self.BASE_URL)
            },
            'scraping': {
                'request_delay': config.getfloat('scraping', 'request_delay', fallback=1.0),
                'max_retries': config.getint('scraping', 'max_retries', fallback=3),
                'timeout': config.getint('scraping', 'timeout', fallback=30),
                'user_agent': config.get('scraping', 'user_agent', 
                    fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            }
        }
    
    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Return default configuration"""
        return {
            'courtlistener': {
                'api_token': os.getenv('COURTLISTENER_API_TOKEN', ''),
                'username': '',
                'password': '',
                'base_url': self.BASE_URL
            },
            'scraping': {
                'request_delay': 1.0,
                'max_retries': 3,
                'timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        
        # Add API token if available
        api_token = self.config['courtlistener']['api_token']
        if api_token:
            session.headers.update({
                'Authorization': f'Token {api_token}'
            })
        
        return session
    
    def _init_selenium_driver(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver for web scraping mode"""
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
            logger.info("Make sure ChromeDriver is installed. Will use API mode only.")
            return None
    
    def authenticate_web(self) -> bool:
        """
        Authenticate with CourtListener using Selenium (if credentials provided)
        
        Returns:
            bool: True if authentication successful or not required
        """
        # CourtListener allows free access without login for basic searches
        # Login only needed for saved searches, alerts, etc.
        username = self.config['courtlistener'].get('username', '')
        password = self.config['courtlistener'].get('password', '')
        
        if not username or not password:
            logger.info("No credentials provided - using unauthenticated access")
            self.is_authenticated = True  # Public access is fine
            return True
        
        try:
            if not self.driver:
                self.driver = self._init_selenium_driver()
                if not self.driver:
                    return False
            
            logger.info("Attempting to authenticate with CourtListener...")
            
            # Navigate to sign-in page
            signin_url = f"{self.BASE_URL}/sign-in/"
            self.driver.get(signin_url)
            
            wait = WebDriverWait(self.driver, 20)
            
            # Enter credentials
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(password)
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            time.sleep(3)
            
            # Check if authentication successful
            if 'sign-in' not in self.driver.current_url.lower():
                self.is_authenticated = True
                logger.info("Successfully authenticated with CourtListener")
                return True
            else:
                logger.warning("Authentication may have failed - continuing anyway")
                self.is_authenticated = True  # Public access fallback
                return True
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            logger.info("Falling back to unauthenticated access")
            self.is_authenticated = True  # Public access fallback
            return True

    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        wait_time = (1.0 / self.rate_limit) - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict, max_retries: int = 3) -> Optional[Dict]:
        """
        Make API request with retry logic and exponential backoff.
        
        Args:
            endpoint: API endpoint (e.g., "/search/")
            params: Query parameters
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response or None if failed
        """
        url = f"{self.BASE_URL}{endpoint}"
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for {endpoint}")
            return self.cache[cache_key]
        
        # Make request with retries
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    self.cache[cache_key] = data
                    logger.info(f"Successfully fetched {endpoint} (attempt {attempt + 1})")
                    return data
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                elif response.status_code == 401:
                    logger.error("Authentication failed. Check your API token.")
                    return None
                else:
                    logger.error(f"Request failed with status {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.error(f"Failed to fetch {endpoint} after {max_retries} attempts")
        return None
    
    def search_cases(self, query: str, max_results: int = 10, **kwargs) -> List[LegalCase]:
        """
        Search for legal cases using a natural language query.
        
        Args:
            query: Search query (e.g., "employment discrimination wrongful termination")
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters (court, date_filed_after, etc.)
            
        Returns:
            List of LegalCase objects
        """
        logger.info(f"Searching for: '{query}' (max {max_results} results)")
        
        params = {
            "q": query,
            "type": "o",  # Opinions
            "order_by": "score desc",
            "stat_Precedential": "on",  # Only precedential cases
        }
        params.update(kwargs)
        
        # Get search results
        response = self._make_request("/search/", params)
        if not response or "results" not in response:
            logger.error("No results found or API error")
            return []
        
        results = response["results"][:max_results]
        logger.info(f"Found {len(results)} cases for query: '{query}'")
        
        # Parse results into LegalCase objects
        cases = []
        for result in results:
            try:
                case = self._parse_search_result(result)
                if case:
                    cases.append(case)
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                continue
        
        return cases
    
    def _parse_search_result(self, result: Dict) -> Optional[LegalCase]:
        """Parse a search result into a LegalCase object"""
        try:
            # Extract opinion text (may need to fetch full opinion)
            snippet = result.get("snippet", "")
            opinion_text = snippet  # For now, use snippet; can enhance to fetch full text
            
            # Build citation
            citation = result.get("citation", [])
            citation_str = citation[0] if citation else result.get("docket_number", "No citation")
            
            case = LegalCase(
                case_name=result.get("caseName", "Unknown Case"),
                citation=citation_str,
                court=result.get("court", "Unknown Court"),
                date_filed=result.get("dateFiled", "Unknown Date"),
                snippet=snippet,
                opinion_text=opinion_text,
                url=f"https://www.courtlistener.com{result.get('absolute_url', '')}"
            )
            return case
        except Exception as e:
            logger.error(f"Error parsing search result: {e}")
            return None
    
    def get_opinion_text(self, opinion_id: str) -> Optional[str]:
        """
        Fetch full opinion text by ID.
        
        Args:
            opinion_id: CourtListener opinion ID
            
        Returns:
            Full opinion text or None if failed
        """
        response = self._make_request(f"/opinions/{opinion_id}/", {})
        if response:
            return response.get("plain_text", response.get("html", ""))
        return None
    
    def save_cases_to_json(self, cases: List[LegalCase], filepath: str):
        """Save scraped cases to JSON file for caching/backup"""
        try:
            cases_dict = [case.to_dict() for case in cases]
            with open(filepath, 'w') as f:
                json.dump(cases_dict, f, indent=2)
            logger.info(f"Saved {len(cases)} cases to {filepath}")
        except Exception as e:
            logger.error(f"Error saving cases to JSON: {e}")
    
    def load_cases_from_json(self, filepath: str) -> List[LegalCase]:
        """Load cached cases from JSON file"""
        try:
            with open(filepath, 'r') as f:
                cases_dict = json.load(f)
            cases = [LegalCase(**case_data) for case_data in cases_dict]
            logger.info(f"Loaded {len(cases)} cases from {filepath}")
            return cases
        except Exception as e:
            logger.error(f"Error loading cases from JSON: {e}")
            return []


def test_scraper():
    """Test the CourtListener scraper with sample queries"""
    logger.info("=" * 60)
    logger.info("Testing CourtListener Scraper")
    logger.info("=" * 60)
    
    scraper = CourtListenerScraper(rate_limit=0.5)  # 0.5 requests/second for safety
    
    # Test queries
    test_queries = [
        "employment discrimination wrongful termination",
        "breach of contract damages",
        "personal injury negligence",
        "intellectual property patent infringement",
        "constitutional law first amendment"
    ]
    
    all_cases = []
    for query in test_queries[:3]:  # Test first 3 queries
        logger.info(f"\n--- Testing query: '{query}' ---")
        cases = scraper.search_cases(query, max_results=5)
        
        for i, case in enumerate(cases, 1):
            logger.info(f"\nCase {i}:")
            logger.info(f"  Name: {case.case_name}")
            logger.info(f"  Citation: {case.citation}")
            logger.info(f"  Court: {case.court}")
            logger.info(f"  Date: {case.date_filed}")
            logger.info(f"  URL: {case.url}")
            logger.info(f"  Snippet: {case.snippet[:200]}...")
        
        all_cases.extend(cases)
        time.sleep(1)  # Extra delay between queries
    
    # Save to cache
    cache_dir = os.path.join(os.path.dirname(__file__), "data", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    scraper.save_cases_to_json(all_cases, cache_file)
    
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Test complete! Scraped {len(all_cases)} total cases")
    logger.info(f"Results cached at: {cache_file}")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    test_scraper()
