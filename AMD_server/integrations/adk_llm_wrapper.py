"""
Google ADK LLM Wrapper for AMD vLLM Server
Connects Saul-7B on AMD server to Google ADK framework
"""

from google.adk import LlmModel
from typing import Dict, Any, Optional
import requests
import json
import sys
import os

# Add config path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from config.amd_config import AMDConfig
except ImportError:
    class AMDConfig:
        VLLM_BASE_URL = "http://localhost:8000"
        MODEL_FOLDER = "saul-7b-instruct-v1"
        MODEL_NAME = "Saul-7B-Instruct-v1"

class SaulLlmModel(LlmModel):
    """
    Custom LLM Model implementation for Saul-7B on AMD vLLM server
    """
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        api_key: Optional[str] = None
    ):
        self.base_url = (base_url or AMDConfig.VLLM_BASE_URL).rstrip('/')
        self.model = model or AMDConfig.MODEL_FOLDER
        self.api_key = api_key
        
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Generate text using Saul-7B on AMD vLLM server"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"]
            
        except Exception as e:
            raise RuntimeError(f"Saul-7B generation failed: {e}")
    
    def generate_chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Generate chat response using Saul-7B"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise RuntimeError(f"Saul-7B chat generation failed: {e}")


def get_saul_model(config_from_env: bool = True) -> SaulLlmModel:
    """Get configured Saul-7B model for ADK"""
    if config_from_env:
        return SaulLlmModel(
            base_url=AMDConfig.VLLM_BASE_URL,
            model=AMDConfig.MODEL_FOLDER
        )
    else:
        return SaulLlmModel()