"""
Specialist Agent 3: Legal Researcher
Provides case research and settlement guidance
Enhanced with RAG (Retrieval-Augmented Generation) for similar case retrieval
"""

import logging
from typing import Dict, Optional
import sys
import os

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
    """Agent that provides legal research and settlement guidance with RAG support"""
    
    SYSTEM_PROMPT = """You are a legal research assistant specializing in personal injury law.
Your job is to analyze cases and provide research memos with settlement guidance.

Guidelines:
- Consider injury type, liability, and jurisdiction
- Reference similar case precedents when possible
- Suggest reasonable settlement ranges
- Note key legal factors (comparative negligence, damages caps, etc.)
- Cite relevant legal principles
- Be realistic and thorough"""
    
    def __init__(self, llm_client, use_rag: bool = True):
        """
        Initialize Legal Researcher Agent
        
        Args:
            llm_client: AMDLLMClient instance
            use_rag: Enable RAG for similar case retrieval (default: True)
        """
        self.llm = llm_client
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
        
        logger.info(f"Legal Researcher Agent initialized (RAG: {'enabled' if self.use_rag else 'disabled'})")
    
    def process(
        self, 
        injury_type: str, 
        jurisdiction: str, 
        case_details: str,
        top_k_cases: int = 3
    ) -> Dict:
        """
        Generate legal research memo with RAG-enhanced similar case retrieval
        
        Args:
            injury_type: Type of injury (e.g., "broken wrist from slip and fall")
            jurisdiction: Legal jurisdiction (e.g., "Florida")
            case_details: Additional case context
            top_k_cases: Number of similar cases to retrieve (default: 3)
            
        Returns:
            Dict containing:
                - injury_type: Injury description
                - jurisdiction: Legal jurisdiction
                - case_details: Case context
                - similar_cases: List of similar cases found via RAG (if enabled)
                - research_memo: Comprehensive research memo
                - agent: Agent identifier
        """
        logger.info(f"Researching case: {injury_type} in {jurisdiction}")
        
        similar_cases = []
        similar_cases_text = ""
        
        # Retrieve similar cases using RAG if available
        if self.use_rag and self.ml_inference:
            try:
                logger.info("Searching for similar cases using RAG...")
                
                # Create search query from injury type and case details
                search_query = f"{injury_type} {case_details}"
                
                # Search for similar cases
                results = self.ml_inference.search_similar_cases(
                    query=search_query,
                    top_k=top_k_cases,
                    min_similarity=0.3
                )
                
                similar_cases = results
                
                # Format similar cases for LLM context
                if results:
                    logger.info(f"Found {len(results)} similar cases")
                    similar_cases_text = "\n\nSimilar Cases Found:\n"
                    for i, case in enumerate(results, 1):
                        similar_cases_text += f"\n{i}. {case['title']} (Similarity: {case['similarity']:.1%})\n"
                        similar_cases_text += f"   Type: {case['document_type']}\n"
                        similar_cases_text += f"   Preview: {case['text_preview']}\n"
                else:
                    logger.info("No similar cases found")
                    similar_cases_text = "\n\nNo similar cases found in database.\n"
                    
            except Exception as e:
                logger.error(f"Error searching similar cases: {e}")
                similar_cases_text = "\n\n(Similar case search encountered an error)\n"
        
        try:
            prompt = f"""Case Details:
Injury Type: {injury_type}
Jurisdiction: {jurisdiction}
Additional Context: {case_details}
{similar_cases_text}

Provide a legal research memo including:
1. Relevant legal principles for this injury type
2. Settlement range considerations
3. Key factors affecting case value
4. Analysis of similar cases (if provided above)
5. Recommended next steps"""
            
            research_memo = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.5,  # Lower temp for more factual output
                max_tokens=600
            )
            
            logger.info("Legal research completed successfully")
            
            result = {
                "injury_type": injury_type,
                "jurisdiction": jurisdiction,
                "case_details": case_details,
                "research_memo": research_memo.strip(),
                "agent": "LegalResearcher"
            }
            
            # Add similar cases to result if found
            if similar_cases:
                result["similar_cases"] = similar_cases
            
            return result
            
        except Exception as e:
            logger.error(f"Error conducting legal research: {e}")
            raise
