# file: llm_saul.py
import os
from typing import Optional
from openai import OpenAI

SAUL_BASE_URL = os.getenv("SAUL_BASE_URL", "http://localhost:8000/v1")
SAUL_MODEL = os.getenv("SAUL_MODEL", "Equall/Saul-7B-Instruct-v1")
SAUL_API_KEY = os.getenv("SAUL_API_KEY", "dummy")

_client = OpenAI(base_url=SAUL_BASE_URL, api_key=SAUL_API_KEY)

def complete(prompt: str, max_tokens: int = 384, temperature: float = 0.2, stop: Optional[list[str]] = None) -> str:
    """Call Saul via OpenAI completions and return plain text."""
    resp = _client.completions.create(
        model=SAUL_MODEL,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=stop,
    )
    return (resp.choices[0].text or "").strip()
