"""
Specialist Agent 4: Evidence Sorter
OCR + Classification for legal documents
"""

import logging
from typing import Dict
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

logger = logging.getLogger(__name__)


class EvidenceSorterAgent:
    """Agent that extracts text from documents and classifies them"""
    
    SYSTEM_PROMPT = """You are a document classification specialist for a personal injury law firm.
Your job is to categorize legal documents based on their content.

Document Categories:
- Medical Bill
- Medical Records (treatment notes, discharge summaries)
- Police Report
- Insurance Correspondence
- Legal Filing
- Photograph/Evidence
- Employment Records
- Expert Report
- Other

Be specific and accurate in your classification."""
    
    def __init__(self, llm_client, ocr_type: str = 'paddle'):  # Removed AMDLLMClient type hint
        """
        Initialize Evidence Sorter Agent
        
        Args:
            llm_client: AMDLLMClient instance
            ocr_type: OCR backend to use ('paddle', 'easy', 'tesseract')
        """
        self.llm = llm_client
        self.ocr_type = ocr_type
        logger.info(f"Evidence Sorter Agent initialized with {ocr_type} OCR")
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from image or PDF
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text content
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try to import OCR processor
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from ml_pipeline.ocr.ocr_processor import OCRProcessor
            
            processor = OCRProcessor(langs=['en'], gpu=True)
            text = processor.extract_text_simple(str(file_path))
            logger.info(f"✓ Extracted {len(text)} characters from {file_path_obj.name}")
            return text
            
        except Exception as e:
            logger.warning(f"OCR extraction failed, using placeholder: {e}")
            return f"[OCR extraction placeholder for: {file_path_obj.name}]"
    
    def classify_document(self, extracted_text: str) -> Dict:
        """
        Classify document based on extracted text
        
        Args:
            extracted_text: Text extracted from document
            
        Returns:
            Dict with classification results
        """
        logger.info("Classifying document")
        
        try:
            prompt = f"""Document text:
{extracted_text[:2000]}  

Classify this document into one of these categories:
- Medical Bill
- Medical Records
- Police Report
- Insurance Correspondence
- Legal Filing
- Photograph/Evidence
- Employment Records
- Expert Report
- Other

Provide:
1. Category (single choice)
2. Confidence (high/medium/low)
3. Brief reasoning (one sentence)"""
            
            classification = self.llm.simple_prompt(
                prompt=prompt,
                system_message=self.SYSTEM_PROMPT,
                temperature=0.3,  # Low temp for consistent classification
                max_tokens=200
            )
            
            return {
                "classification": classification.strip(),
                "text_preview": extracted_text[:500],
                "agent": "EvidenceSorter"
            }
            
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            raise
    
    def process(self, file_path: str) -> Dict:
        """
        Complete pipeline: Extract text and classify
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dict containing:
                - file: File path
                - extracted_text: Full extracted text
                - classification: Classification results
                - agent: Agent identifier
        """
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Extract text
            extracted_text = self.extract_text(file_path)
            
            # Step 2: Classify
            classification_result = self.classify_document(extracted_text)
            
            logger.info("Document processed and classified successfully")
            
            return {
                "file": file_path,
                "extracted_text": extracted_text,
                **classification_result
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
