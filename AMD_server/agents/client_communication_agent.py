"""
Specialist Agent 1: Client Communication Guru
Transforms messy client messages into clear, professional responses
"""

import logging
from typing import Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

logger = logging.getLogger(__name__)


class ClientCommunicationAgent:
    """Agent that rewrites messy client communications"""
    
    SYSTEM_PROMPT = """You are a compassionate legal assistant working at a personal injury law firm. 
Your job is to take messy, emotional, or unclear client messages and rewrite them as clear, 
professional, but warm responses. 

Guidelines:
- Maintain empathy and understanding
- Be concise but thorough
- Use professional but accessible language
- Address their concerns directly
- Include next steps when appropriate
- Keep responses under 200 words"""
    
    def __init__(self, llm_client: AMDLLMClient):
        """
        Initialize Client Communication Agent
        
        Args:
            llm_client: AMDLLMClient instance
        """
        self.llm = llm_client
        logger.info("Client Communication Agent initialized")
    
    def process(self, messy_message: str) -> Dict:
        """
        Transform messy client message into polished response
        
        Args:
            messy_message: Raw client message (emails, texts, etc.)
            
        Returns:
            Dict containing:
                - original: Original message
                - polished_response: Professional rewrite
                - agent: Agent identifier
        """
        logger.info(f"Processing client message: {len(messy_message)} chars")
        
        try:
            prompt = f"""Client's message:
{messy_message}

Rewrite this as a clear, empathetic professional response from the law firm."""
            
            polished_response = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=300
            )
            
            logger.info("Client communication processed successfully")
            
            return {
                "original": messy_message,
                "polished_response": polished_response.strip(),
                "agent": "ClientCommunicationGuru"
            }
            
        except Exception as e:
            logger.error(f"Error processing client message: {e}")
            raise
