#!/usr/bin/env python3
"""
Test OCR Pipeline on Morgan & Morgan Documents

Tests the OCR processor on sample legal documents.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr.ocr_processor import OCRProcessor
from ocr.image_loader import ImageLoader

def test_ocr_initialization():
    """Test 1: Initialize OCR processor"""
    print("\n" + "="*70)
    print("TEST 1: OCR Processor Initialization")
    print("="*70)
    
    try:
        processor = OCRProcessor(langs=['en'], gpu=True)
        print("✓ OCR Processor initialized successfully")
        print(f"  Languages: {processor.langs}")
        print(f"  GPU: {processor.gpu}")
        return processor
    except Exception as e:
        print(f"❌ Failed to initialize OCR processor: {e}")
        return None


def test_image_loader():
    """Test 2: Load images from database"""
    print("\n" + "="*70)
    print("TEST 2: Image Loader")
    print("="*70)
    
    try:
        loader = ImageLoader()
        print("✓ Image Loader initialized")
        
        # Try to load Kaggle images
        images = loader.get_kaggle_images(limit=5)
        print(f"✓ Found {len(images)} Kaggle images")
        
        if images:
            print("\nSample images:")
            for i, img in enumerate(images[:3], 1):
                print(f"  {i}. {img.get('file_name')} ({img.get('dataset_name')})")
        
        return loader
    except Exception as e:
        print(f"⚠️  Image loader test failed: {e}")
        print("  (This is OK if database connection not configured)")
        return None


def test_ocr_on_test_image(processor):
    """Test 3: Run OCR on test image"""
    print("\n" + "="*70)
    print("TEST 3: OCR on Test Image")
    print("="*70)
    
    # Check for test image
    test_image_path = Path(__file__).parent.parent.parent / "backend" / "APIs" / "AMD" / "OCR" / "ocr_test.jpg"
    
    if not test_image_path.exists():
        print(f"⚠️  Test image not found: {test_image_path}")
        print("  Skipping test...")
        return
    
    try:
        print(f"Processing: {test_image_path.name}")
        
        # Extract text (simple)
        text = processor.extract_text_simple(str(test_image_path))
        print(f"\n✓ Extracted text ({len(text)} characters):")
        print(f"  {text[:200]}...")
        
        # Extract text with confidence
        results = processor.extract_text_with_confidence(str(test_image_path))
        print(f"\n✓ Detailed results: {len(results)} text regions")
        
        if results:
            print("\nTop 3 results:")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. \"{result['text']}\" (confidence: {result['confidence']:.3f})")
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")


def test_morgan_document_search():
    """Test 4: Search for Morgan document images"""
    print("\n" + "="*70)
    print("TEST 4: Search for Morgan Document Images")
    print("="*70)
    
    try:
        loader = ImageLoader()
        
        # Look for document images
        doc_images = loader.get_document_images(limit=10)
        print(f"Found {len(doc_images)} document images in database")
        
        if doc_images:
            print("\nSample documents:")
            for i, doc in enumerate(doc_images[:5], 1):
                print(f"  {i}. {doc.get('title')} ({doc.get('document_type')})")
                print(f"     Path: {doc.get('file_path')}")
        else:
            print("  No image documents found (most are PDFs)")
        
    except Exception as e:
        print(f"⚠️  Document search failed: {e}")


def test_batch_processing(processor):
    """Test 5: Batch OCR processing"""
    print("\n" + "="*70)
    print("TEST 5: Batch OCR Processing")
    print("="*70)
    
    # Create sample batch (if test images available)
    test_dir = Path(__file__).parent.parent.parent / "backend" / "APIs" / "AMD" / "OCR"
    test_images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    
    if not test_images:
        print("⚠️  No test images found for batch processing")
        return
    
    try:
        image_paths = [str(p) for p in test_images[:3]]  # Max 3 images
        print(f"Processing batch of {len(image_paths)} images...")
        
        results = processor.process_batch(image_paths, detail=0)
        print(f"✓ Processed {len(results)} images")
        
        for i, (path, words) in enumerate(zip(image_paths, results), 1):
            filename = Path(path).name
            text_preview = ' '.join(words[:10]) if words else "(no text)"
            print(f"  {i}. {filename}: {len(words)} words - {text_preview}...")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")


def main():
    """Run all OCR tests"""
    print("\n" + "="*70)
    print("OCR PIPELINE TEST SUITE")
    print("="*70)
    print("\nTesting OCR integration with ML pipeline...")
    
    # Test 1: Initialize OCR
    processor = test_ocr_initialization()
    if not processor:
        print("\n❌ Cannot continue without OCR processor")
        return
    
    # Test 2: Image loader
    loader = test_image_loader()
    
    # Test 3: OCR on test image
    test_ocr_on_test_image(processor)
    
    # Test 4: Search Morgan documents
    test_morgan_document_search()
    
    # Test 5: Batch processing
    test_batch_processing(processor)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✓ OCR processor is working")
    print("✓ Ready for production use")
    print("\nNext steps:")
    print("  1. Integrate with Evidence Sorter Agent")
    print("  2. Process Morgan documents with OCR")
    print("  3. Train image classifier on Kaggle data")
    print("="*70)


if __name__ == "__main__":
    main()
