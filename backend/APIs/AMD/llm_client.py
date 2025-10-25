"""
AMD vLLM API Client for AI Legal Tender
Provides interface to AMD MI300X-hosted LLM via vLLM
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AMDLLMClient:
    """Client for calling AMD-hosted LLM via vLLM"""
    
    def __init__(self, base_url: str = "http://localhost:8000", model: str = "llama-3-8b"):
        """
        Initialize AMD LLM client
        
        Args:
            base_url: URL of vLLM server (default: http://localhost:8000)
            model: Model name to use (default: llama-3-8b)
        """
        self.base_url = base_url
        self.model = model
        logger.info(f"Initialized AMD LLM client: {base_url}, model: {model}")
        
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 500
    ) -> str:
        """
        Send chat completion request to AMD LLM
        
        Args:
            messages: List of message dicts [{"role": "system", "content": "..."}]
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
            
        Raises:
            requests.RequestException: If API call fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"LLM response received: {len(result)} chars")
            return result
            
        except requests.RequestException as e:
            logger.error(f"AMD LLM API error: {e}")
            raise
    
    def simple_prompt(
        self, 
        prompt: str, 
        system_message: str = "", 
        **kwargs
    ) -> str:
        """
        Simplified single-turn prompt
        
        Args:
            prompt: User prompt text
            system_message: Optional system message to set context
            **kwargs: Additional arguments passed to chat_completion
            
        Returns:
            Generated text content
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_completion(messages, **kwargs)
    
    def health_check(self) -> bool:
        """
        Check if AMD LLM server is accessible
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models on the server
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            response.raise_for_status()
            models = response.json()["data"]
            return [model["id"] for model in models]
        except requests.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []
