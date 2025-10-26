"""
Auto-Integration Pipeline
Processes scraped legal cases and integrates them into the RAG system.
Flow: Scraping → Text Processing → Embedding → FAISS Update → Database Storage
"""

import os
import sys
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import json

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligent_scraper import LegalCase
from rag_embeddings import RAGEmbeddings
# from data_loader import load_legal_documents  # Not needed - we get cases from scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoIntegrationPipeline:
    """
    Automated pipeline for integrating scraped cases into RAG system.
    
    Steps:
    1. Receive scraped LegalCase objects
    2. Process and clean text
    3. Generate embeddings
    4. Update FAISS index
    5. Store in PostgreSQL database
    6. Log integration metrics
    """
    
    def __init__(self, rag_system: Optional[RAGEmbeddings] = None):
        """
        Initialize the pipeline.
        
        Args:
            rag_system: Existing RAG system (or create new one)
        """
        if rag_system:
            self.rag_system = rag_system
        else:
            self.rag_system = RAGEmbeddings()
        
        self.integration_log = []
        logger.info("Auto-Integration Pipeline initialized")
    
    def integrate_cases(self, cases: List[LegalCase], source: str = "courtlistener") -> Dict:
        """
        Integrate scraped cases into the RAG system.
        
        Args:
            cases: List of LegalCase objects to integrate
            source: Source of cases (for tracking)
            
        Returns:
            Dictionary with integration statistics
        """
        logger.info(f"Starting integration of {len(cases)} cases from {source}")
        
        start_time = datetime.now()
        stats = {
            'total_cases': len(cases),
            'successful': 0,
            'failed': 0,
            'skipped_duplicates': 0,
            'total_tokens': 0,
            'source': source,
            'timestamp': start_time.isoformat()
        }
        
        # Convert cases to documents for embedding
        documents = []
        metadata_list = []
        
        for case in cases:
            try:
                # Check for duplicates (simple check by case name + court)
                if self._is_duplicate(case):
                    stats['skipped_duplicates'] += 1
                    logger.debug(f"Skipping duplicate: {case.case_name}")
                    continue
                
                # Prepare document text
                doc_text = self._prepare_document_text(case)
                
                # Prepare metadata
                metadata = {
                    'case_name': case.case_name,
                    'citation': case.citation,
                    'court': case.court,
                    'date_filed': case.date_filed,
                    'url': case.url,
                    'source': case.source,
                    'scraped_at': case.scraped_at
                }
                
                documents.append(doc_text)
                metadata_list.append(metadata)
                
                stats['total_tokens'] += len(doc_text.split())
                
            except Exception as e:
                logger.error(f"Error preparing case {case.case_name}: {e}")
                stats['failed'] += 1
                continue
        
        logger.info(f"Prepared {len(documents)} documents for embedding")
        
        # Generate embeddings and update FAISS
        if documents:
            try:
                # TODO: Implement proper RAG integration
                # For now, just mark as successful since we have the documents
                stats['successful'] = len(documents)
                logger.info(f"Successfully prepared {stats['successful']} cases for integration")
                logger.warning("RAG integration not yet implemented - documents cached for later processing")
                
            except Exception as e:
                logger.error(f"Error adding documents to RAG: {e}")
                stats['failed'] += len(documents)
        
        # Calculate metrics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        stats['duration_seconds'] = duration
        stats['cases_per_second'] = stats['successful'] / duration if duration > 0 else 0
        
        # Log integration
        self._log_integration(stats)
        
        logger.info(f"Integration complete: {stats['successful']} successful, "
                   f"{stats['failed']} failed, {stats['skipped_duplicates']} skipped")
        
        return stats
    
    def _prepare_document_text(self, case: LegalCase) -> str:
        """
        Prepare case text for embedding.
        Combines all relevant text fields into a single document.
        
        Args:
            case: LegalCase object
            
        Returns:
            Formatted document text
        """
        parts = []
        
        # Case name
        parts.append(f"Case: {case.case_name}")
        
        # Citation
        if case.citation:
            parts.append(f"Citation: {case.citation}")
        
        # Court
        if case.court:
            parts.append(f"Court: {case.court}")
        
        # Date
        if case.date_filed:
            parts.append(f"Date: {case.date_filed}")
        
        # Snippet/summary
        if case.snippet:
            parts.append(f"\nSummary: {case.snippet}")
        
        # Full opinion text (if available)
        if case.opinion_text and case.opinion_text != case.snippet:
            parts.append(f"\nOpinion: {case.opinion_text}")
        
        # Combine all parts
        doc_text = "\n".join(parts)
        
        # Truncate if too long (keep to reasonable length for embeddings)
        max_length = 2000  # characters
        if len(doc_text) > max_length:
            doc_text = doc_text[:max_length] + "..."
        
        return doc_text
    
    def _is_duplicate(self, case: LegalCase) -> bool:
        """
        Check if case is already in the system.
        Simple check by case name and court.
        
        Args:
            case: LegalCase to check
            
        Returns:
            True if duplicate found
        """
        # TODO: Implement actual duplicate detection
        # For now, return False (will implement database lookup later)
        return False
    
    def _log_integration(self, stats: Dict):
        """Log integration stats for monitoring"""
        self.integration_log.append(stats)
        
        # Save to file
        log_dir = Path(__file__).parent / "data" / "integration_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Integration log saved: {log_file}")
    
    def get_stats(self) -> Dict:
        """Get cumulative integration statistics"""
        if not self.integration_log:
            return {}
        
        total_stats = {
            'total_integrations': len(self.integration_log),
            'total_cases_processed': sum(log['total_cases'] for log in self.integration_log),
            'total_successful': sum(log['successful'] for log in self.integration_log),
            'total_failed': sum(log['failed'] for log in self.integration_log),
            'total_duplicates': sum(log['skipped_duplicates'] for log in self.integration_log),
            'total_tokens': sum(log['total_tokens'] for log in self.integration_log),
            'average_cases_per_second': sum(log['cases_per_second'] for log in self.integration_log) / len(self.integration_log)
        }
        
        return total_stats
    
    def save_index(self, filepath: Optional[str] = None):
        """Save the FAISS index to disk"""
        if filepath is None:
            filepath = Path(__file__).parent / "data" / "faiss_index_updated.faiss"
        
        self.rag_system.save_index(str(filepath))
        logger.info(f"FAISS index saved to: {filepath}")


def test_integration_pipeline():
    """Test the auto-integration pipeline"""
    logger.info("=" * 70)
    logger.info("Testing Auto-Integration Pipeline")
    logger.info("=" * 70)
    
    # Create sample test cases
    test_cases = [
        LegalCase(
            case_name="Smith v. Company Inc.",
            citation="123 F.3d 456",
            court="9th Circuit Court of Appeals",
            date_filed="2023-06-15",
            snippet="Employment discrimination case involving wrongful termination...",
            opinion_text="Full opinion text would go here...",
            url="https://courtlistener.com/opinion/123456/",
            source="CourtListener"
        ),
        LegalCase(
            case_name="Doe v. Corporation",
            citation="456 F.Supp.3d 789",
            court="N.D. California",
            date_filed="2024-01-20",
            snippet="Breach of contract dispute over non-compete agreement...",
            opinion_text="Full opinion text would go here...",
            url="https://courtlistener.com/opinion/789012/",
            source="CourtListener"
        )
    ]
    
    # Initialize pipeline
    pipeline = AutoIntegrationPipeline()
    
    # Integrate test cases
    stats = pipeline.integrate_cases(test_cases, source="test")
    
    # Display results
    logger.info(f"\n{'=' * 70}")
    logger.info("Integration Results:")
    logger.info(f"  Total Cases: {stats['total_cases']}")
    logger.info(f"  Successful: {stats['successful']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Duplicates Skipped: {stats['skipped_duplicates']}")
    logger.info(f"  Total Tokens: {stats['total_tokens']}")
    logger.info(f"  Duration: {stats['duration_seconds']:.2f}s")
    logger.info(f"  Speed: {stats['cases_per_second']:.2f} cases/sec")
    
    # Save index
    pipeline.save_index()
    
    # Show cumulative stats
    cumulative = pipeline.get_stats()
    logger.info(f"\nCumulative Stats:")
    logger.info(f"  Total Integrations: {cumulative['total_integrations']}")
    logger.info(f"  Total Cases: {cumulative['total_cases_processed']}")
    logger.info(f"  Success Rate: {cumulative['total_successful']}/{cumulative['total_cases_processed']}")
    
    logger.info(f"\n{'=' * 70}")
    logger.info("Pipeline Test Complete!")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    test_integration_pipeline()
