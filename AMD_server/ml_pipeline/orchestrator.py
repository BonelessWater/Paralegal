"""
Scraping Orchestrator
Coordinates intelligent multi-source scraping with LLM query generation.
Strategy: CourtListener for common cases, LexisNexis for rare/premium content.
"""

import os
import sys
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from query_generator import QueryGeneratorAgent, GeneratedQuery, SearchSource, QueryPriority
from intelligent_scraper import CourtListenerScraper, LegalCase
from auto_integration import AutoIntegrationPipeline

# For LexisNexis (if available)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))
    from scrape import LexisNexisScraper
    LEXISNEXIS_AVAILABLE = True
except:
    LEXISNEXIS_AVAILABLE = False
    logging.warning("LexisNexis scraper not available - will use CourtListener only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScrapingOrchestrator:
    """
    Intelligent orchestrator for multi-source legal case scraping.
    
    Features:
    - LLM-powered query generation
    - Smart source selection (CourtListener vs LexisNexis)
    - Parallel scraping of multiple queries
    - Automatic RAG integration
    - Progress tracking and caching
    """
    
    def __init__(self, 
                 use_lexisnexis: bool = True,
                 parallel_workers: int = 3,
                 cache_results: bool = True):
        """
        Initialize the orchestrator.
        
        Args:
            use_lexisnexis: Whether to use LexisNexis for premium searches
            parallel_workers: Number of parallel scraping threads
            cache_results: Whether to cache scraped results
        """
        # Initialize components
        self.query_generator = QueryGeneratorAgent()
        self.courtlistener = CourtListenerScraper(mode='hybrid')
        self.lexisnexis = None
        self.integration_pipeline = AutoIntegrationPipeline()
        
        # Check LexisNexis availability
        if use_lexisnexis and LEXISNEXIS_AVAILABLE:
            try:
                self.lexisnexis = LexisNexisScraper()
                logger.info("LexisNexis scraper initialized")
            except Exception as e:
                logger.warning(f"Could not initialize LexisNexis: {e}")
        
        self.parallel_workers = parallel_workers
        self.cache_results = cache_results
        self.scraping_history = []
        
        logger.info(f"Scraping Orchestrator initialized (workers: {parallel_workers})")
    
    def research_question(self, 
                          user_question: str, 
                          max_cases_per_query: int = 10,
                          auto_integrate: bool = True) -> Dict:
        """
        Research a legal question by generating queries and scraping multiple sources.
        
        Args:
            user_question: User's legal question
            max_cases_per_query: Maximum cases to scrape per query
            auto_integrate: Whether to automatically integrate into RAG
            
        Returns:
            Dictionary with research results and statistics
        """
        logger.info("=" * 70)
        logger.info(f"RESEARCHING: {user_question}")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
        # Step 1: Generate optimized queries using LLM
        logger.info("\n📝 Step 1: Generating search queries...")
        queries = self.query_generator.generate_queries(user_question, num_queries=3)
        
        logger.info(f"Generated {len(queries)} queries:")
        for i, q in enumerate(queries, 1):
            logger.info(f"  {i}. [{q.source.value.upper()}] {q.query} (priority: {q.priority.value})")
        
        # Step 2: Scrape cases from appropriate sources
        logger.info("\n🔍 Step 2: Scraping cases from sources...")
        all_cases = self._scrape_all_queries(queries, max_cases_per_query)
        
        logger.info(f"Scraped {len(all_cases)} total cases")
        
        # Step 3: Auto-integrate into RAG (if enabled)
        integration_stats = None
        if auto_integrate and all_cases:
            logger.info("\n🔗 Step 3: Integrating cases into RAG system...")
            integration_stats = self.integration_pipeline.integrate_cases(
                all_cases, 
                source="orchestrated_research"
            )
            logger.info(f"Integration: {integration_stats['successful']} successful, "
                       f"{integration_stats['failed']} failed")
        
        # Step 4: Cache results (if enabled)
        if self.cache_results and all_cases:
            self._cache_results(user_question, queries, all_cases)
        
        # Calculate stats
        duration = (datetime.now() - start_time).total_seconds()
        
        results = {
            'user_question': user_question,
            'num_queries': len(queries),
            'queries': [q.to_dict() for q in queries],
            'total_cases_found': len(all_cases),
            'cases_by_source': self._count_by_source(all_cases),
            'integration_stats': integration_stats,
            'duration_seconds': duration,
            'timestamp': start_time.isoformat()
        }
        
        # Log to history
        self.scraping_history.append(results)
        
        # Display summary
        self._display_summary(results)
        
        return results
    
    def _scrape_all_queries(self, queries: List[GeneratedQuery], max_cases: int) -> List[LegalCase]:
        """
        Scrape cases for all queries in parallel.
        
        Args:
            queries: List of generated queries
            max_cases: Max cases per query
            
        Returns:
            Combined list of all scraped cases
        """
        all_cases = []
        
        # Group queries by source
        courtlistener_queries = [q for q in queries if q.source in [SearchSource.COURTLISTENER, SearchSource.BOTH]]
        lexisnexis_queries = [q for q in queries if q.source in [SearchSource.LEXISNEXIS, SearchSource.BOTH]]
        
        # Scrape CourtListener queries
        if courtlistener_queries:
            logger.info(f"Scraping {len(courtlistener_queries)} CourtListener queries...")
            cl_cases = self._scrape_parallel(courtlistener_queries, "courtlistener", max_cases)
            all_cases.extend(cl_cases)
        
        # Scrape LexisNexis queries (if available)
        if lexisnexis_queries and self.lexisnexis:
            logger.info(f"Scraping {len(lexisnexis_queries)} LexisNexis queries...")
            ln_cases = self._scrape_parallel(lexisnexis_queries, "lexisnexis", max_cases)
            all_cases.extend(ln_cases)
        elif lexisnexis_queries:
            logger.warning("LexisNexis queries skipped - scraper not available")
        
        return all_cases
    
    def _scrape_parallel(self, queries: List[GeneratedQuery], source: str, max_cases: int) -> List[LegalCase]:
        """
        Scrape multiple queries in parallel.
        
        Args:
            queries: List of queries to scrape
            source: Source name ('courtlistener' or 'lexisnexis')
            max_cases: Max cases per query
            
        Returns:
            Combined list of scraped cases
        """
        all_cases = []
        
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all scraping tasks
            future_to_query = {}
            for query in queries:
                if source == "courtlistener":
                    future = executor.submit(self._scrape_courtlistener, query.query, max_cases)
                else:
                    future = executor.submit(self._scrape_lexisnexis, query.query, max_cases)
                future_to_query[future] = query
            
            # Collect results as they complete
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    cases = future.result()
                    all_cases.extend(cases)
                    logger.info(f"✅ [{source}] '{query.query}': {len(cases)} cases")
                except Exception as e:
                    logger.error(f"❌ [{source}] '{query.query}': Error - {e}")
        
        return all_cases
    
    def _scrape_courtlistener(self, query: str, max_cases: int) -> List[LegalCase]:
        """Scrape CourtListener for a query"""
        try:
            # Try API first (since user has token), fallback to web
            cases = self.courtlistener.search_cases_hybrid(query, max_results=max_cases)
            return cases
        except Exception as e:
            logger.error(f"CourtListener scraping error: {e}")
            return []
    
    def _scrape_lexisnexis(self, query: str, max_cases: int) -> List[LegalCase]:
        """Scrape LexisNexis for a query"""
        if not self.lexisnexis:
            return []
        
        try:
            # Use existing LexisNexis scraper
            session_id = self.lexisnexis.search(query, max_results=max_cases)
            documents = self.lexisnexis.scrape_search_results(session_id, max_results=max_cases)
            
            # Convert to LegalCase objects
            cases = []
            for doc in documents:
                case = LegalCase(
                    case_name=doc.get('title', 'Unknown'),
                    citation=doc.get('citation', ''),
                    court=doc.get('court', ''),
                    date_filed=str(doc.get('decision_date', '')),
                    snippet=doc.get('summary', ''),
                    opinion_text=doc.get('full_text', ''),
                    url=doc.get('url', ''),
                    source="LexisNexis"
                )
                cases.append(case)
            
            return cases
        except Exception as e:
            logger.error(f"LexisNexis scraping error: {e}")
            return []
    
    def _count_by_source(self, cases: List[LegalCase]) -> Dict[str, int]:
        """Count cases by source"""
        counts = {}
        for case in cases:
            source = case.source
            counts[source] = counts.get(source, 0) + 1
        return counts
    
    def _cache_results(self, question: str, queries: List[GeneratedQuery], cases: List[LegalCase]):
        """Cache scraping results to disk"""
        cache_dir = Path(__file__).parent / "data" / "cache" / "orchestrated"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cache_file = cache_dir / f"research_{timestamp}.json"
        
        cache_data = {
            'question': question,
            'queries': [q.to_dict() for q in queries],
            'cases': [case.to_dict() for case in cases],
            'timestamp': timestamp
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Results cached: {cache_file}")
    
    def _display_summary(self, results: Dict):
        """Display research summary"""
        logger.info("\n" + "=" * 70)
        logger.info("RESEARCH SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Question: {results['user_question']}")
        logger.info(f"Queries Generated: {results['num_queries']}")
        logger.info(f"Total Cases Found: {results['total_cases_found']}")
        logger.info(f"Cases by Source:")
        for source, count in results['cases_by_source'].items():
            logger.info(f"  - {source}: {count}")
        if results['integration_stats']:
            logger.info(f"Integration:")
            logger.info(f"  - Successful: {results['integration_stats']['successful']}")
            logger.info(f"  - Failed: {results['integration_stats']['failed']}")
        logger.info(f"Duration: {results['duration_seconds']:.2f}s")
        logger.info("=" * 70)
    
    def get_history(self) -> List[Dict]:
        """Get scraping history"""
        return self.scraping_history
    
    def cleanup(self):
        """Clean up resources"""
        if self.courtlistener:
            self.courtlistener.cleanup()
        if self.lexisnexis:
            pass  # LexisNexis cleanup if needed


def test_orchestrator():
    """Test the scraping orchestrator"""
    logger.info("=" * 70)
    logger.info("Testing Scraping Orchestrator")
    logger.info("=" * 70)
    
    orchestrator = ScrapingOrchestrator(
        use_lexisnexis=False,  # Set to True if you have LexisNexis credentials
        parallel_workers=2,
        cache_results=True
    )
    
    # Test question
    question = "Can my employer fire me for filing a workers compensation claim in California?"
    
    # Run research
    results = orchestrator.research_question(
        question,
        max_cases_per_query=5,
        auto_integrate=True
    )
    
    # Display detailed results
    logger.info("\n📊 DETAILED RESULTS:")
    logger.info(json.dumps(results, indent=2, default=str))
    
    # Cleanup
    orchestrator.cleanup()
    
    logger.info("\n" + "=" * 70)
    logger.info("Orchestrator Test Complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    test_orchestrator()
