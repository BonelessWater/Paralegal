"""
Enhanced AMD Configuration with Environment Variable Support
Teammates can configure everything via .env file
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AMDConfig:
    """AMD LLM Configuration - Fully customizable via .env file"""
    
    # ========================================================================
    # HUGGING FACE MODEL CONFIGURATION
    # ========================================================================
    
    # Hugging Face token for downloading models
    HF_TOKEN: Optional[str] = os.getenv("HUGGING_FACE_HUB_TOKEN")
    
    # Model name from Hugging Face Hub (e.g., "law-ai/InLegalBERT")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
    
    # Local folder name for the model
    MODEL_FOLDER: str = os.getenv("MODEL_FOLDER", "llama-3-8b")
    
    # ========================================================================
    # vLLM SERVER SETTINGS
    # ========================================================================
    
    # Base URL for vLLM API server
    VLLM_BASE_URL: str = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
    
    # Maximum sequence length
    MAX_MODEL_LEN: int = int(os.getenv("MAX_MODEL_LEN", "4096"))
    
    # Number of GPUs to use (tensor parallelism)
    TENSOR_PARALLEL_SIZE: int = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))
    
    # Model data type
    MODEL_DTYPE: str = os.getenv("MODEL_DTYPE", "float16")
    
    # ========================================================================
    # GENERATION PARAMETERS
    # ========================================================================
    
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "500"))
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # ========================================================================
    # PROJECT PATHS
    # ========================================================================
    
    PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "~/ai-legal-tender")
    MODELS_PATH: str = os.getenv("MODELS_PATH", "~/ai-legal-tender/models")
    
    # Computed full model path
    @classmethod
    def get_model_path(cls) -> str:
        """Get the full path to the model directory"""
        return os.path.join(
            os.path.expanduser(cls.MODELS_PATH),
            cls.MODEL_FOLDER
        )
    
    # ========================================================================
    # ADVANCED SETTINGS
    # ========================================================================
    
    ENABLE_PREFIX_CACHING: bool = os.getenv("ENABLE_PREFIX_CACHING", "false").lower() == "true"
    QUANTIZATION: Optional[str] = os.getenv("QUANTIZATION") or None
    TRUST_REMOTE_CODE: bool = os.getenv("TRUST_REMOTE_CODE", "false").lower() == "true"
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration and provide helpful error messages"""
        errors = []
        
        if not cls.VLLM_BASE_URL:
            errors.append("VLLM_BASE_URL must be set")
        
        if not cls.MODEL_NAME:
            errors.append("MODEL_NAME must be set (e.g., 'law-ai/InLegalBERT')")
        
        if not cls.MODEL_FOLDER:
            errors.append("MODEL_FOLDER must be set (e.g., 'legal-bert')")
        
        if cls.HF_TOKEN and len(cls.HF_TOKEN) < 10:
            errors.append("HUGGING_FACE_HUB_TOKEN appears invalid (too short)")
        
        if errors:
            error_msg = "\n".join([f"  ❌ {e}" for e in errors])
            raise ValueError(f"Configuration validation failed:\n{error_msg}\n\n"
                           f"Please check your .env file")
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (for debugging)"""
        print("=" * 70)
        print("AMD MI300X Configuration")
        print("=" * 70)
        print(f"Model Name:          {cls.MODEL_NAME}")
        print(f"Model Folder:        {cls.MODEL_FOLDER}")
        print(f"Full Model Path:     {cls.get_model_path()}")
        print(f"vLLM Server:         {cls.VLLM_BASE_URL}")
        print(f"Max Sequence Length: {cls.MAX_MODEL_LEN}")
        print(f"Tensor Parallel:     {cls.TENSOR_PARALLEL_SIZE}")
        print(f"Data Type:           {cls.MODEL_DTYPE}")
        print(f"Default Temp:        {cls.DEFAULT_TEMPERATURE}")
        print(f"HF Token Set:        {'Yes ✓' if cls.HF_TOKEN else 'No ✗'}")
        print("=" * 70)


class OCRConfig:
    """OCR Configuration"""
    
    # OCR Backend (paddle, easy, tesseract)
    OCR_BACKEND: str = os.getenv("OCR_BACKEND", "paddle")
    
    # Supported file types
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    SUPPORTED_PDF_FORMATS = ['.pdf']
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """Get all supported file formats"""
        return cls.SUPPORTED_IMAGE_FORMATS + cls.SUPPORTED_PDF_FORMATS
