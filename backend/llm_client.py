"""
AMD vLLM Client Wrapper
Provides simple interface to Saul-7B running on vLLM server
"""

import requests
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class AMDLLMClient:
    """
    Wrapper for vLLM server running Saul-7B Legal AI
    Provides OpenAI-compatible API interface
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        model_name: str = "Equall/Saul-7B-Instruct-v1",
        timeout: int = 30
    ):
        """
        Initialize AMD LLM Client
        
        Args:
            base_url: vLLM server URL (default: http://localhost:8000)
            model_name: Model identifier on vLLM server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        
        # OpenAI-compatible endpoints
        self.completions_url = f"{self.base_url}/v1/completions"
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.models_url = f"{self.base_url}/v1/models"
        
        logger.info(f"AMD LLM Client initialized: {base_url} (model: {model_name})")
    
    def health_check(self) -> bool:
        """
        Check if vLLM server is accessible
        
        Returns:
            True if server is responding, False otherwise
        """
        try:
            response = requests.get(self.models_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text completion using vLLM server
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            stop: List of stop sequences
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If generation fails
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
            
            if stop:
                payload["stop"] = stop
            
            logger.debug(f"Generating with prompt length: {len(prompt)}")
            
            response = requests.post(
                self.completions_url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            generated_text = result["choices"][0]["text"]
            logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text.strip()
            
        except requests.exceptions.Timeout:
            logger.error("Request to vLLM server timed out")
            raise Exception("LLM generation timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"LLM generation failed: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid response format: {e}")
            raise Exception("Invalid response from LLM server")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 1.0
    ) -> str:
        """
        Generate chat completion using OpenAI-compatible chat endpoint
        
        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated response text
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
            
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.HTTPError as e:
            # Log the ACTUAL error message from vLLM
            logger.error(f"Chat completion failed: {e}")
            try:
                error_detail = response.json() if response else None
                logger.error(f"vLLM error response: {error_detail}")
            except:
                logger.error(f"vLLM error text: {response.text if response else 'No response'}")
            # Calculate total prompt size for debugging
            total_chars = sum(len(m.get('content', '')) for m in messages)
            logger.error(f"Total prompt size: {total_chars} chars (~{total_chars // 4} tokens)")
            raise Exception(f"Chat completion failed: {str(e)}")
        except Exception as e:
            logger.error(f"Chat completion unexpected error: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """
        Get information about available models
        
        Returns:
            Dictionary with model information
        """
        try:
            response = requests.get(self.models_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}


# Convenience function for quick testing
def test_connection(base_url: str = "http://localhost:8000"):
    """Test connection to vLLM server"""
    client = AMDLLMClient(base_url)
    
    print(f"Testing connection to {base_url}...")
    
    if client.health_check():
        print("✅ Server is accessible")
        
        models = client.get_model_info()
        print(f"✅ Available models: {models}")
        
        try:
            response = client.generate(
                "What is personal injury law?",
                max_tokens=100,
                temperature=0.7
            )
            print(f"✅ Generation test successful")
            print(f"Response: {response[:200]}...")
            return True
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return False
    else:
        print("❌ Server is not accessible")
        return False


if __name__ == "__main__":
    # Test the client
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logging.basicConfig(level=logging.INFO)
    test_connection(base_url)
