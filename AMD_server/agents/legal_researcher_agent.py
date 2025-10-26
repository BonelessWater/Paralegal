"""
Specialist Agent 3: Legal Researcher
Provides case research and settlement guidance
Enhanced with:
- Intelligent Scraper (primary research tool for live case law)
- RAG (Retrieval-Augmented Generation for similar case retrieval from local DB)
- Multi-Agent Research (specialized agents working iteratively)
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

# Import multi-agent researcher
try:
    from agents.multi_agent_researcher import MultiAgentLegalResearcher
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    print("⚠️  Multi-agent research not available - using single-agent mode")

logger = logging.getLogger(__name__)


class LegalResearcherAgent:
    """
    Agent that provides comprehensive legal research using:
    1. Intelligent Scraper - Live case law research across 10.6M opinions
    2. RAG - Similar case retrieval from local database
    3. Multi-Agent Research - Specialized agents working iteratively (optional)
    4. LLM Analysis - Expert legal analysis and settlement guidance
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
    
    def __init__(self, llm_client, intelligent_scraper=None, use_rag: bool = True, use_multi_agent: bool = False):
        """
        Initialize Legal Researcher Agent
        
        Args:
            llm_client: AMDLLMClient instance for generating analysis
            intelligent_scraper: ScrapingOrchestrator instance for live case research (optional)
            use_rag: Enable RAG for similar case retrieval from local DB (default: True)
            use_multi_agent: Enable multi-agent iterative research (default: False)
        """
        self.llm = llm_client
        self.intelligent_scraper = intelligent_scraper
        self.use_rag = use_rag and RAG_AVAILABLE
        self.use_multi_agent = use_multi_agent and MULTI_AGENT_AVAILABLE
        self.ml_inference = None
        self.multi_agent_researcher = None
        
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
        
        # Initialize multi-agent researcher if enabled
        if self.use_multi_agent:
            try:
                logger.info("Initializing multi-agent research system...")
                self.multi_agent_researcher = MultiAgentLegalResearcher(
                    llm_client=llm_client,
                    batch_size=10,    # Analyze 10 cases per cycle
                    max_cycles=3       # 3 refinement cycles
                )
                logger.info("✅ Multi-agent research system loaded")
            except Exception as e:
                logger.warning(f"Failed to load multi-agent system: {e}")
                self.use_multi_agent = False
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
        case_citations = ""
        
        # Step 1: Use intelligent scraper for live case research if available
        if self.intelligent_scraper:
            try:
                logger.info("🚀 Running intelligent scraper for live case research...")
                research_result = await self.intelligent_scraper.research_question_async(question)
                
                logger.info(f"DEBUG: research_result type = {type(research_result)}")
                logger.info(f"DEBUG: research_result = {research_result if isinstance(research_result, dict) else f'<{type(research_result).__name__} with {len(research_result) if hasattr(research_result, '__len__') else 0} items>'}")
                
                # Handle case where scraper returns unexpected format
                if not isinstance(research_result, dict):
                    logger.error(f"Intelligent scraper returned unexpected type: {type(research_result)}")
                    research_result = {}
                
                total_cases = research_result.get('total_cases_found', 0)
                cases_per_sec = research_result.get('cases_per_second', 0)
                duration = research_result.get('duration_seconds', 0)
                cases_data = research_result.get('cases', [])
                
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
                
                # Format case citations for LLM context with FULL TEXT
                if cases_data:
                    case_citations = f"\n\nRELEVANT CASES FOUND ({len(cases_data)} cases):\n"
                    case_citations += "\nTop 5 Cases with Full Analysis:\n"
                    
                    # Include full opinion text for top 5 cases
                    for i, case in enumerate(cases_data[:5], 1):
                        case_citations += f"\n{'='*70}\n"
                        case_citations += f"CASE {i}: {case.get('case_name', 'Unknown')}\n"
                        case_citations += f"Citation: {case.get('citation', 'No citation')}\n"
                        case_citations += f"Court: {case.get('court', 'Unknown Court')}\n"
                        case_citations += f"Date Filed: {case.get('date_filed', 'Unknown')}\n"
                        case_citations += f"URL: {case.get('url', 'N/A')}\n"
                        
                        # Include opinion text if available (first 1500 chars for context)
                        opinion_text = case.get('opinion_text', case.get('snippet', ''))
                        if opinion_text and len(opinion_text.strip()) > 10:
                            case_citations += f"\nOPINION EXCERPT:\n{opinion_text[:1500]}\n"
                            if len(opinion_text) > 1500:
                                case_citations += "...[excerpt truncated for length]\n"
                        else:
                            case_citations += f"\n[Opinion text not available - metadata only]\n"
                        case_citations += f"{'='*70}\n"
                    
                    # Brief listing of remaining cases (metadata only)
                    if len(cases_data) > 5:
                        case_citations += f"\n\nAdditional Cases Found ({len(cases_data) - 5} more):\n"
                        for i, case in enumerate(cases_data[5:10], 6):  # Show up to 10 total
                            case_citations += f"\n{i}. {case.get('case_name', 'Unknown')}"
                            if case.get('citation'):
                                case_citations += f", {case.get('citation')}"
                            case_citations += f" ({case.get('court', 'Unknown Court')}, {case.get('date_filed', 'N/A')})"
                    
                    research_data['case_citations'] = cases_data
                
                logger.info(f"✅ Intelligent scraper found {total_cases} cases")
                
            except Exception as e:
                import traceback
                logger.error(f"Intelligent scraper error: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
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
        
                # Step 3: Choose analysis method: Multi-Agent or Standard LLM
        if self.use_multi_agent and self.multi_agent_researcher and cases_data and len(cases_data) >= 10:
            # Use multi-agent iterative research for comprehensive analysis
            try:
                logger.info("🔬 Using multi-agent iterative research system...")
                
                multi_agent_results = await self.multi_agent_researcher.research_async(
                    question=question,
                    cases=cases_data,
                    previous_findings=None
                )
                
                analysis = multi_agent_results['synthesis']
                
                # Add multi-agent metadata
                research_data['multi_agent_findings'] = multi_agent_results['agent_findings']
                research_data['research_cycles'] = multi_agent_results['research_cycles']
                research_data['total_agent_findings'] = multi_agent_results['total_findings']
                
                logger.info(f"✅ Multi-agent research complete: {multi_agent_results['total_findings']} findings across {multi_agent_results['cycles']} cycles")
                
            except Exception as e:
                logger.error(f"Multi-agent research error: {e}, falling back to standard analysis")
                # Fall through to standard LLM analysis
                self.use_multi_agent = False
        
        # Step 3b: Standard LLM analysis (if multi-agent not used or failed)
        if not self.use_multi_agent or not analysis:
            try:
                logger.info("Generating legal analysis with standard LLM...")
                
                analysis_prompt = f"""Legal Research Question:
{question}

{scraper_summary}
{case_citations}
{rag_summary}

Please provide a comprehensive legal research memo that includes:

1. SUMMARY OF RESEARCH FINDINGS
   - Brief overview of the legal issue
   - Number and quality of cases found

2. RELEVANT LEGAL PRINCIPLES & PRECEDENTS
   - Key legal doctrines applicable to this issue
   - ONLY cite cases that have opinion text provided above
   - Use proper citations format: Case Name, Citation (Court, Year)

3. CASE ANALYSIS
   - Analyze the TOP 5 cases with opinion excerpts provided above
   - Quote relevant passages from the opinion text
   - Explain how each case applies to the research question
   - DO NOT make up case holdings - only discuss what's in the text provided

4. KEY FACTORS & CONSIDERATIONS
   - What facts matter most in these cases?
   - What trends do you see across the cases?

5. PRACTICAL GUIDANCE
   - Settlement considerations (if applicable)
   - Recommended next steps for counsel

CRITICAL INSTRUCTIONS:
- ONLY cite and discuss cases that have opinion text provided above
- Quote actual text from opinions when analyzing cases
- If a case has no opinion text, do NOT make claims about what "the court held"
- Be honest about limitations - if opinion text is unavailable, say so
- Use proper legal citation format throughout"""

                # Use chat_completion method from LLM client
                messages = [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": analysis_prompt}
                ]
                
                analysis = self.llm.chat_completion(
                    messages=messages,
                    temperature=0.5,  # Lower for more factual analysis
                    max_tokens=2500   # Increased for detailed citations and analysis
                )
                
                research_data['analysis'] = analysis.strip()
                research_data['response'] = f"""LEGAL RESEARCH MEMO

{analysis.strip()}

---
Research powered by Intelligent Scraping System
{scraper_summary}"""
                
            except Exception as e:
                logger.error(f"Standard LLM analysis error: {e}")
                # If we get here and don't have analysis, raise the error
                if not analysis:
                    raise
        
        logger.info("✅ Legal research completed successfully")
        return research_data
    
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
