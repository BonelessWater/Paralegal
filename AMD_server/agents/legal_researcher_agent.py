"""
Specialist Agent 3: Legal Researcher
Provides case research and settlement guidance
Enhanced with:
- Intelligent Scraper (primary research tool for live case law)
- RAG (Retrieval-Augmented Generation for similar case retrieval from local DB)
"""

import logging
from typing import Dict, Optional
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

# Import ML inference for RAG capabilities
try:
    from ml_pipeline.ml_inference import MLInference
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG embeddings not available - legal research will work without similar case retrieval")

logger = logging.getLogger(__name__)


class LegalResearcherAgent:
    """
    Agent that provides comprehensive legal research using:
    1. Intelligent Scraper - Live case law research across 10.6M opinions
    2. RAG - Similar case retrieval from local database
    3. LLM Analysis - Expert legal analysis and settlement guidance
    """
    
    SYSTEM_PROMPT = """You are an expert legal research assistant specializing in personal injury law.
Your job is to analyze case law research and provide comprehensive research memos with settlement guidance.

Guidelines:
- Analyze the case research results provided
- Identify relevant legal principles and precedents
- Suggest reasonable settlement ranges based on similar cases
- Note key legal factors (comparative negligence, damages caps, jurisdiction-specific rules)
- Cite specific case examples when available
- Be realistic, thorough, and professional"""
    
    def __init__(self, llm_client, intelligent_scraper=None, use_rag: bool = True):
        """
        Initialize Legal Researcher Agent
        
        Args:
            llm_client: AMDLLMClient instance for generating analysis
            intelligent_scraper: ScrapingOrchestrator instance for live case research (optional)
            use_rag: Enable RAG for similar case retrieval from local DB (default: True)
        """
        self.llm = llm_client
        self.intelligent_scraper = intelligent_scraper
        self.use_rag = use_rag and RAG_AVAILABLE
        self.ml_inference = None
        
        # Initialize RAG if available
        if self.use_rag:
            try:
                logger.info("Initializing RAG embeddings for legal research...")
                self.ml_inference = MLInference(
                    load_document_classifier=False,
                    load_rag_embeddings=True,
                    load_audio_transcriber=False,
                    load_ocr=False,
                    load_email=False,
                    load_structured=False
                )
                logger.info("✅ RAG embeddings loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load RAG embeddings: {e}")
                logger.warning("Legal research will work without similar case retrieval")
                self.use_rag = False
        
        scraper_status = "enabled" if self.intelligent_scraper else "disabled"
        rag_status = "enabled" if self.use_rag else "disabled"
        logger.info(f"Legal Researcher Agent initialized (Scraper: {scraper_status}, RAG: {rag_status})")
    
    async def process_async(self, question: str) -> Dict:
        """
        Process a legal research request using intelligent scraper + LLM analysis
        
        This is the PRIMARY method that combines:
        1. Intelligent scraper for live case law research
        2. LLM for expert analysis and memo generation
        3. RAG for additional similar cases (optional)
        
        Args:
            question: Legal research question or case description
            
        Returns:
            Dict containing research results and analysis
        """
        logger.info(f"Processing legal research request: {question[:100]}...")
        
        research_data = {}
        scraper_summary = ""
        
        # Step 1: Use intelligent scraper for live case research if available
        if self.intelligent_scraper:
            try:
                logger.info("🚀 Running intelligent scraper for live case research...")
                research_result = await self.intelligent_scraper.research_question_async(question)
                
                total_cases = research_result.get('total_cases_found', 0)
                cases_per_sec = research_result.get('cases_per_second', 0)
                duration = research_result.get('duration_seconds', 0)
                
                research_data['scraper_results'] = research_result
                research_data['total_cases_found'] = total_cases
                research_data['scraping_speed'] = cases_per_sec
                
                scraper_summary = f"""
LIVE CASE RESEARCH RESULTS:
- Total Cases Found: {total_cases}
- Research Speed: {cases_per_sec:.1f} cases/sec
- Duration: {duration:.1f} seconds
- Source: CourtListener (10.6M legal opinions)

Generated Queries ({len(research_result.get('queries', []))})"""
                
                for i, q in enumerate(research_result.get('queries', [])[:3], 1):
                    scraper_summary += f"\n{i}. {q.get('query', 'N/A')}"
                
                logger.info(f"✅ Intelligent scraper found {total_cases} cases")
                
            except Exception as e:
                logger.error(f"Intelligent scraper error: {e}")
                scraper_summary = "\n(Live case research encountered an error)\n"
        
        # Step 2: Use RAG for similar cases from local database (if available)
        rag_summary = ""
        if self.use_rag and self.ml_inference:
            try:
                logger.info("Searching local database for similar cases...")
                results = self.ml_inference.search_similar_cases(
                    query=question,
                    top_k=3,
                    min_similarity=0.3
                )
                
                if results:
                    rag_summary = f"\n\nSIMILAR CASES FROM LOCAL DATABASE ({len(results)} found):"
                    for i, case in enumerate(results, 1):
                        rag_summary += f"\n{i}. {case['title']} ({case['similarity']:.1%} match)"
                        rag_summary += f"\n   {case['text_preview'][:150]}..."
                    research_data['rag_cases'] = results
                    
            except Exception as e:
                logger.error(f"RAG search error: {e}")
        
        # Step 3: Generate expert legal analysis with LLM
        try:
            logger.info("Generating legal analysis with LLM...")
            
            analysis_prompt = f"""Legal Research Question:
{question}

{scraper_summary}
{rag_summary}

Please provide a comprehensive legal research memo that includes:
1. Summary of Research Findings
2. Relevant Legal Principles & Precedents
3. Key Factors Affecting This Case Type
4. Settlement Range Considerations (if applicable)
5. Recommended Next Steps

Be specific, cite the research data provided, and give practical guidance."""

            # Use chat_completion method from LLM client
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis = self.llm.chat_completion(
                messages=messages,
                temperature=0.6,
                max_tokens=800
            )
            
            research_data['analysis'] = analysis.strip()
            research_data['response'] = f"""LEGAL RESEARCH MEMO

{analysis.strip()}

---
Research powered by Intelligent Scraping System
{scraper_summary}"""
            
            logger.info("✅ Legal research completed successfully")
            return research_data
            
        except Exception as e:
            logger.error(f"Error generating legal analysis: {e}")
            raise
    
    def process(self, question: str) -> Dict:
        """
        Synchronous wrapper for async process_async method.
        Creates event loop if needed to run async scraper.
        
        Args:
            question: Legal research question
            
        Returns:
            Dict containing research results
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new one
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.process_async(question))
            else:
                return loop.run_until_complete(self.process_async(question))
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.process_async(question))
