"""
Email Pipeline - Email classification and analysis

Processes legal emails for task routing and entity extraction.
"""

from .email_loader import EmailLoader
from .email_classifier import EmailClassifier, EMAIL_TYPES
from .email_processor import EmailProcessor

__all__ = [
    'EmailLoader',
    'EmailClassifier', 
    'EmailProcessor',
    'EMAIL_TYPES'
]
