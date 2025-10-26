"""
OCR Processor for ML Pipeline

Wraps the existing AMD_server/OCR.py module for use in ML pipelines.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

# Add AMD_server to path to access OCR module
AMD_SERVER_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(AMD_SERVER_DIR))

try:
    from OCR import run_ocr
except ImportError:
    print(f"Warning: Could not import OCR module from {AMD_SERVER_DIR}")
    run_ocr = None

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    OCR processor for extracting text from images and scanned documents.
    
    Uses EasyOCR with AMD ROCm GPU acceleration.
    """
    
    def __init__(self, langs: Optional[List[str]] = None, gpu: bool = True):
        """
        Initialize OCR processor.
        
        Args:
            langs: List of language codes (default: ['en'])
            gpu: Use GPU acceleration (default: True)
        """
        self.langs = langs or ['en']
        self.gpu = gpu
        
        if run_ocr is None:
            raise RuntimeError("OCR module not available. Ensure AMD_server/OCR.py is accessible.")
        
        logger.info(f"OCR Processor initialized (langs={self.langs}, gpu={gpu})")
    
    def extract_text(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_b64: Optional[str] = None,
        detail: int = 0
    ) -> Union[List[str], List[Dict]]:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to local image file
            image_url: URL to image
            image_b64: Base64-encoded image
            detail: 0 = words only, 1 = words + boxes + confidences
            
        Returns:
            List of words (detail=0) or list of dicts with text/box/conf (detail=1)
        """
        # Convert local path to base64 if provided
        if image_path:
            import base64
            with open(image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        if not image_url and not image_b64:
            raise ValueError("Must provide image_path, image_url, or image_b64")
        
        logger.info(f"Extracting text from image (detail={detail})")
        
        result = run_ocr(
            image_b64=image_b64,
            image_url=image_url,
            langs=self.langs,
            detail=detail
        )
        
        if "error" in result:
            raise RuntimeError(f"OCR failed: {result['error']}")
        
        if detail == 0:
            return result.get('texts', [])
        else:
            return result.get('results', [])
    
    def extract_text_simple(self, image_path: str) -> str:
        """
        Extract text from image and return as single string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text joined with spaces
        """
        words = self.extract_text(image_path=image_path, detail=0)
        return ' '.join(words)
    
    def extract_text_with_confidence(self, image_path: str) -> List[Dict]:
        """
        Extract text with bounding boxes and confidence scores.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of dicts with 'text', 'confidence', and 'box' keys
        """
        return self.extract_text(image_path=image_path, detail=1)
    
    def process_batch(
        self,
        image_paths: List[str],
        detail: int = 0
    ) -> List[Union[List[str], List[Dict]]]:
        """
        Process multiple images.
        
        Args:
            image_paths: List of image file paths
            detail: 0 = words only, 1 = words + boxes + confidences
            
        Returns:
            List of OCR results for each image
        """
        results = []
        total = len(image_paths)
        
        logger.info(f"Processing batch of {total} images")
        
        for i, path in enumerate(image_paths, 1):
            try:
                result = self.extract_text(image_path=path, detail=detail)
                results.append(result)
                if i % 10 == 0:
                    logger.info(f"  Processed {i}/{total} images")
            except Exception as e:
                logger.error(f"  Failed to process {path}: {e}")
                results.append([] if detail == 0 else [])
        
        logger.info(f"✓ Batch processing complete: {len(results)}/{total} successful")
        return results
    
    def extract_text_from_pdf_pages(self, pdf_path: str) -> List[str]:
        """
        Extract text from each page of a PDF (if converted to images).
        
        Note: Requires PDF to be converted to images first.
        This is a helper for multi-page document processing.
        
        Args:
            pdf_path: Path to PDF file (will be converted to images)
            
        Returns:
            List of extracted text for each page
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise RuntimeError("pdf2image not installed. Run: pip install pdf2image")
        
        logger.info(f"Converting PDF to images: {pdf_path}")
        images = convert_from_path(pdf_path)
        
        results = []
        for i, image in enumerate(images, 1):
            # Save to temp file
            temp_path = f"/tmp/pdf_page_{i}.jpg"
            image.save(temp_path, 'JPEG')
            
            # Extract text
            text = self.extract_text_simple(temp_path)
            results.append(text)
            
            # Clean up
            os.remove(temp_path)
            logger.info(f"  Page {i}/{len(images)}: {len(text)} characters")
        
        return results


if __name__ == "__main__":
    # Test OCR processor
    processor = OCRProcessor()
    print("✓ OCR Processor initialized")
    print(f"  Languages: {processor.langs}")
    print(f"  GPU: {processor.gpu}")
    print("\nReady for image processing!")
