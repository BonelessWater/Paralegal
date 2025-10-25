"""
Specialist Agent 2: Records Wrangler
Handles medical records requests and tracking
"""

import logging
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from APIs.AMD.llm_client import AMDLLMClient

logger = logging.getLogger(__name__)


class RecordsWranglerAgent:
    """Agent that manages medical records requests"""
    
    SYSTEM_PROMPT = """You are a medical records coordinator for a personal injury law firm.
Your job is to analyze case descriptions and draft formal medical records requests.

Guidelines:
- Identify all medical providers mentioned
- List specific records needed (ER reports, treatment notes, imaging, billing)
- Draft professional request letters in proper legal format
- Include HIPAA authorization language
- Be thorough and specific"""
    
    def __init__(self, llm_client: AMDLLMClient):
        """
        Initialize Records Wrangler Agent
        
        Args:
            llm_client: AMDLLMClient instance
        """
        self.llm = llm_client
        logger.info("Records Wrangler Agent initialized")
    
    def process(self, case_description: str) -> Dict:
        """
        Generate medical records request from case description
        
        Args:
            case_description: Description of client's medical treatment
            
        Returns:
            Dict containing:
                - case_description: Original case info
                - providers: List of medical providers identified
                - records_needed: List of specific records to request
                - records_request: Formal request letter
                - agent: Agent identifier
        """
        logger.info(f"Processing records request for case: {len(case_description)} chars")
        
        try:
            prompt = f"""Case information:
{case_description}

Analyze this case and:
1. List all medical providers mentioned
2. Specify what medical records are needed
3. Draft a formal records request letter

Format your response clearly with sections."""
            
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.6,
                max_tokens=500
            )
            
            logger.info("Records request generated successfully")
            
            return {
                "case_description": case_description,
                "records_request": response.strip(),
                "agent": "RecordsWrangler"
            }
            
        except Exception as e:
            logger.error(f"Error generating records request: {e}")
            raise
