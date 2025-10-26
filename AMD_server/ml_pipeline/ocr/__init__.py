"""
OCR Pipeline for ML Processing

Integrates with AMD_server/OCR.py (EasyOCR) for document image processing.
"""

from .ocr_processor import OCRProcessor
from .image_loader import ImageLoader

__all__ = ['OCRProcessor', 'ImageLoader']
