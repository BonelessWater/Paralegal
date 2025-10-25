"""
Specialist Agent 3: Legal Researcher
Provides case research and settlement guidance
"""

import logging
from typing import Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from APIs.AMD.llm_client import AMDLLMClient

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
    
    def __init__(self, llm_client: AMDLLMClient):
        """
        Initialize Legal Researcher Agent
        
        Args:
            llm_client: AMDLLMClient instance
        """
        self.llm = llm_client
        logger.info("Legal Researcher Agent initialized")
    
    def process(
        self, 
        injury_type: str, 
        jurisdiction: str, 
        case_details: str
    ) -> Dict:
        """
        Generate legal research memo
        
        Args:
            injury_type: Type of injury (e.g., "broken wrist from slip and fall")
            jurisdiction: Legal jurisdiction (e.g., "Florida")
            case_details: Additional case context
            
        Returns:
            Dict containing:
                - injury_type: Injury description
                - jurisdiction: Legal jurisdiction
                - case_details: Case context
                - research_memo: Comprehensive research memo
                - agent: Agent identifier
        """
        logger.info(f"Researching case: {injury_type} in {jurisdiction}")
        
        try:
            prompt = f"""Case Details:
Injury Type: {injury_type}
Jurisdiction: {jurisdiction}
Additional Context: {case_details}

Provide a legal research memo including:
1. Relevant legal principles for this injury type
2. Settlement range considerations
3. Key factors affecting case value
4. Similar case precedents (if applicable)
5. Recommended next steps"""
            
            research_memo = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.5,  # Lower temp for more factual output
                max_tokens=600
            )
            
            logger.info("Legal research completed successfully")
            
            return {
                "injury_type": injury_type,
                "jurisdiction": jurisdiction,
                "case_details": case_details,
                "research_memo": research_memo.strip(),
                "agent": "LegalResearcher"
            }
            
        except Exception as e:
            logger.error(f"Error conducting legal research: {e}")
            raise
