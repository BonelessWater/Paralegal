"""
Centralized Configuration Management for Paralegal AI Backend
Handles environment variables, validation, and default values
"""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ServerConfig(BaseModel):
    """Server configuration with validation"""

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, ge=1, le=65535, description="Server port")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, production)")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # vLLM settings
    VLLM_BASE_URL: str = Field(default="http://localhost:8000", description="vLLM server URL")
    VLLM_TIMEOUT: int = Field(default=30, ge=1, le=300, description="vLLM timeout in seconds")

    # CORS settings
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
        ],
        description="Allowed CORS origins"
    )

    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, ge=1, le=500, description="Max concurrent workers")
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1, description="Requests per minute")

    # Database settings
    DB_HOST: Optional[str] = Field(default=None, description="Database host")
    DB_PORT: int = Field(default=5432, ge=1, le=65535, description="Database port")
    DB_NAME: Optional[str] = Field(default=None, description="Database name")
    DB_USER: Optional[str] = Field(default=None, description="Database user")
    DB_PASSWORD: Optional[str] = Field(default=None, description="Database password")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Ensure environment is valid"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Ensure log level is valid"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

def load_config() -> ServerConfig:
    """
    Load and validate server configuration

    Reads from environment variables and validates all settings.
    Raises ValueError if configuration is invalid.

    Returns:
        ServerConfig: Validated configuration object
    """
    return ServerConfig(
        HOST=os.getenv("HOST", "0.0.0.0"),
        PORT=int(os.getenv("PORT", "8080")),
        ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),
        DEBUG=os.getenv("DEBUG", "False").lower() == "true",
        VLLM_BASE_URL=os.getenv("VLLM_BASE_URL", "http://localhost:8000"),
        VLLM_TIMEOUT=int(os.getenv("VLLM_TIMEOUT", "30")),
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:4173").split(","),
        MAX_CONCURRENT_REQUESTS=int(os.getenv("MAX_CONCURRENT_REQUESTS", "100")),
        CACHE_ENABLED=os.getenv("CACHE_ENABLED", "True").lower() == "true",
        RATE_LIMIT_ENABLED=os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true",
        RATE_LIMIT_REQUESTS=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
        DB_HOST=os.getenv("DB_HOST"),
        DB_PORT=int(os.getenv("DB_PORT", "5432")),
        DB_NAME=os.getenv("DB_NAME"),
        DB_USER=os.getenv("DB_USER"),
        DB_PASSWORD=os.getenv("DB_PASSWORD"),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    )

# Global config instance
config = load_config()
