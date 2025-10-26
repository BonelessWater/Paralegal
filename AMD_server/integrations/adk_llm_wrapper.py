"""
Google ADK LLM Wrapper for AMD vLLM Server
Works with actual project structure
"""

from google.adk import LlmModel
from typing import Dict, Any, Optional
import requests
import json
import sys
import os

# Add project root and backend to path
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..', '..')
backend_path = os.path.join(project_root, 'backend')
sys.path.extend([project_root, backend_path])

try:
    from config.amd_config import AMDConfig
except ImportError:
    # Fallback configuration if config doesn't exist
    class AMDConfig:
        VLLM_BASE_URL = "http://localhost:8000"
        MODEL_FOLDER = "saul-7b-instruct-v1"
        MODEL_NAME = "Saul-7B-Instruct-v1"


class SaulLlmModel(LlmModel):
    """Custom LLM Model for Saul-7B on AMD vLLM server"""
    
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
        """Generate text using Saul-7B"""
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
    return SaulLlmModel()


# Test function
def test_saul_model():
    """Test the Saul model connection"""
    try:
        model = get_saul_model()
        print(f"✅ Saul model initialized: {model.base_url}")
        return True
    except Exception as e:
        print(f"❌ Saul model initialization failed: {e}")
        return False


if __name__ == "__main__":
    test_saul_model()