"""
Specialist Agent 3: Legal Researcher
Provides case research and settlement guidance
Enhanced with Snowflake database integration for real case precedents
"""

import logging
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from APIs.AMD.llm_client import AMDLLMClient

# Try to import Snowflake client (optional dependency)
try:
    from APIs.db.snowflake_client import SnowflakeClient
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    SnowflakeClient = None

logger = logging.getLogger(__name__)


class LegalResearcherAgent:
    """Agent that provides legal research and settlement guidance"""
    
    SYSTEM_PROMPT = """You are a legal research assistant specializing in personal injury law.
Your job is to analyze cases and provide research memos with settlement guidance.

Guidelines:
- Consider injury type, liability, and jurisdiction
- Reference similar case precedents when possible
- Suggest reasonable settlement ranges
- Note key legal factors (comparative negligence, damages caps, etc.)
- Cite relevant legal principles
- Be realistic and thorough"""
    
    def __init__(self, llm_client: AMDLLMClient, snowflake_client: Optional[SnowflakeClient] = None):
        """
        Initialize Legal Researcher Agent
        
        Args:
            llm_client: AMDLLMClient instance
            snowflake_client: Optional SnowflakeClient for case precedent lookups
        """
        self.llm = llm_client
        self.snowflake = snowflake_client
        
        if self.snowflake:
            logger.info("Legal Researcher Agent initialized with Snowflake integration")
        else:
            logger.info("Legal Researcher Agent initialized (no database)")
    
    def _search_precedents(self, injury_type: str, jurisdiction: str) -> List[Dict]:
        """
        Search Snowflake for similar case precedents
        
        Args:
            injury_type: Type of injury to search for
            jurisdiction: Legal jurisdiction
            
        Returns:
            List of relevant case precedents
        """
        if not self.snowflake:
            return []
        
        try:
            # Search for similar cases
            cases = self.snowflake.search_documents(
                query_text=injury_type,
                jurisdiction=jurisdiction,
                document_type="Case Law",
                limit=5
            )
            
            logger.info(f"Found {len(cases)} precedent cases for {injury_type} in {jurisdiction}")
            return cases
            
        except Exception as e:
            logger.error(f"Error searching precedents: {e}")
            return []
    
    def _format_precedents(self, cases: List[Dict]) -> str:
        """Format case precedents for inclusion in prompt"""
        if not cases:
            return "No similar cases found in database."
        
        formatted = "Similar Case Precedents:\n\n"
        for i, case in enumerate(cases, 1):
            formatted += f"{i}. {case.get('TITLE', 'Unknown Case')}\n"
            formatted += f"   Citation: {case.get('CITATION', 'N/A')}\n"
            formatted += f"   Court: {case.get('COURT', 'N/A')}\n"
            formatted += f"   Date: {case.get('DECISION_DATE', 'N/A')}\n"
            
            summary = case.get('SUMMARY', '')
            if summary:
                # Truncate long summaries
                summary = summary[:300] + "..." if len(summary) > 300 else summary
                formatted += f"   Summary: {summary}\n"
            
            formatted += "\n"
        
        return formatted
    
    def process(
        self, 
        injury_type: str, 
        jurisdiction: str, 
        case_details: str,
        use_precedents: bool = True
    ) -> Dict:
        """
        Generate legal research memo
        
        Args:
            injury_type: Type of injury (e.g., "broken wrist from slip and fall")
            jurisdiction: Legal jurisdiction (e.g., "Florida")
            case_details: Additional case context
            use_precedents: Whether to search database for similar cases (default: True)
            
        Returns:
            Dict containing:
                - injury_type: Injury description
                - jurisdiction: Legal jurisdiction
                - case_details: Case context
                - precedent_cases: List of similar cases (if found)
                - research_memo: Comprehensive research memo
                - agent: Agent identifier
        """
        logger.info(f"Researching case: {injury_type} in {jurisdiction}")
        
        # Search for precedent cases if Snowflake is available
        precedent_cases = []
        precedents_text = ""
        
        if use_precedents and self.snowflake:
            precedent_cases = self._search_precedents(injury_type, jurisdiction)
            precedents_text = self._format_precedents(precedent_cases)
        
        try:
            prompt = f"""Case Details:
Injury Type: {injury_type}
Jurisdiction: {jurisdiction}
Additional Context: {case_details}

{precedents_text}

Based on the case details{' and precedents' if precedent_cases else ''}, provide a legal research memo including:
1. Relevant legal principles for this injury type
2. Settlement range considerations
3. Key factors affecting case value
4. Analysis of similar case precedents{' from the database' if precedent_cases else ' (general knowledge)'}
5. Recommended next steps"""
            
            research_memo = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.5,  # Lower temp for more factual output
                max_tokens=800  # More tokens for precedent analysis
            )
            
            logger.info(f"Legal research completed successfully (with {len(precedent_cases)} precedents)")
            
            return {
                "injury_type": injury_type,
                "jurisdiction": jurisdiction,
                "case_details": case_details,
                "precedent_cases": [
                    {
                        "title": c.get('TITLE'),
                        "citation": c.get('CITATION'),
                        "court": c.get('COURT'),
                        "date": str(c.get('DECISION_DATE')) if c.get('DECISION_DATE') else None
                    }
                    for c in precedent_cases
                ],
                "research_memo": research_memo.strip(),
                "agent": "LegalResearcher"
            }
            
        except Exception as e:
            logger.error(f"Error conducting legal research: {e}")
            raise
