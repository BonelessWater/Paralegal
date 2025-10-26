# OCR Pipeline

Production-ready OCR (Optical Character Recognition) pipeline for processing scanned legal documents and images.

## Features

- ✅ **GPU-Accelerated**: Uses EasyOCR with AMD ROCm GPU acceleration
- ✅ **Multi-Language**: Supports 80+ languages (default: English)
- ✅ **Batch Processing**: Process multiple images efficiently
- ✅ **Integration Ready**: Works with document classifier and ML pipeline
- ✅ **Production Tested**: Integrated with Evidence Sorter Agent

## Components

### 1. OCR Processor (`ocr_processor.py`)
Main OCR engine wrapping AMD_server/OCR.py with EasyOCR.

**Key Methods:**
- `extract_text_simple(image_path)` - Extract text as string
- `extract_text_with_confidence(image_path)` - Get text + bounding boxes + confidence scores
- `process_batch(image_paths)` - Process multiple images
- `extract_text_from_pdf_pages(pdf_path)` - OCR multi-page PDFs

### 2. Image Loader (`image_loader.py`)
Load images from database and disk.

**Key Methods:**
- `get_kaggle_images(dataset_name, limit)` - Load from Kaggle datasets (770K images available)
- `get_document_images(document_type, session_id)` - Load from legal_data.documents
- `verify_files_exist(file_paths)` - Check which files exist on disk
- `get_training_images(dataset_name, sample_size)` - Get training data

### 3. Test Suite (`test_ocr.py`)
Comprehensive test suite for OCR pipeline.

## Installation

### Prerequisites
EasyOCR is already installed on AMD server with ROCm support:
```bash
pip install easyocr opencv-python-headless pillow
```

For PDF support (optional):
```bash
pip install pdf2image
```

## Usage

### Basic OCR
```python
from ml_pipeline.ocr import OCRProcessor

# Initialize processor
processor = OCRProcessor(langs=['en'], gpu=True)

# Extract text from image
text = processor.extract_text_simple("scanned_document.jpg")
print(text)
```

### OCR + Classification
```python
from ml_pipeline.ml_inference import MLInference

# Initialize with OCR
ml = MLInference(load_ocr=True)

# Extract and classify in one call
result = ml.extract_and_classify_image("medical_bill.jpg")
print(f"Text: {result['text']}")
print(f"Type: {result['document_type']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### Batch Processing
```python
processor = OCRProcessor()

image_paths = [
    "doc1.jpg",
    "doc2.jpg",
    "doc3.jpg"
]

results = processor.process_batch(image_paths, detail=0)
for path, words in zip(image_paths, results):
    text = ' '.join(words)
    print(f"{path}: {len(text)} characters")
```

### With Evidence Sorter Agent
```python
from agents.evidence_sorter_agent import EvidenceSorterAgent
from backend.APIs.AMD.llm_client import AMDLLMClient

llm = AMDLLMClient(base_url="http://localhost:8000")
agent = EvidenceSorterAgent(llm, ocr_type='easy')

# Extract text and classify
text = agent.extract_text("scanned_medical_bill.jpg")
classification = agent.classify_document(text)

print(f"Document type: {classification['document_type']}")
```

## Testing

Run the test suite:
```bash
cd AMD_server/ml_pipeline/ocr
python test_ocr.py
```

Tests include:
1. OCR processor initialization
2. Image loader (database integration)
3. OCR on test images
4. Morgan document search
5. Batch processing

## Performance

### GPU Acceleration
- **AMD MI300X**: 192 GB VRAM
- **ROCm**: 6.2
- **PyTorch**: 2.5.1+rocm6.2
- **EasyOCR**: GPU-accelerated

### Benchmarks
- Single image (1 page): ~2-5 seconds
- Batch (10 images): ~15-30 seconds
- Large dataset (1000 images): ~30-60 minutes

### Memory Usage
- Model loading: ~1-2 GB VRAM
- Per image inference: ~500 MB VRAM
- Batch processing (32 images): ~4-6 GB VRAM

## Data Sources

### Kaggle Datasets
- **RVLCDIP**: 400,000 document images (16 types)
- **PubLayNet**: 360,000 layout-annotated images
- **Total**: 770K images (13 GB)

### Morgan & Morgan Documents
- 54 legal documents (mostly PDFs)
- Some may have scanned pages requiring OCR
- Database: `legal_data.documents`

## Integration Points

### 1. ML Inference API
```python
ml = MLInference(load_ocr=True)
result = ml.extract_text_from_image("doc.jpg")
```

### 2. Evidence Sorter Agent
```python
agent = EvidenceSorterAgent(llm)
text = agent.extract_text("image.jpg")
```

### 3. Document Classification Pipeline
```python
# OCR → Classify → Save to DB
text = processor.extract_text_simple("scan.jpg")
doc_type = classifier.predict([text])[0]
```

## Configuration

### Language Support
```python
# English only (default)
processor = OCRProcessor(langs=['en'])

# Multiple languages
processor = OCRProcessor(langs=['en', 'es', 'fr'])
```

### GPU Settings
```python
# GPU enabled (default)
processor = OCRProcessor(gpu=True)

# CPU only
processor = OCRProcessor(gpu=False)
```

### Detail Levels
```python
# Simple (words only)
words = processor.extract_text(image_path, detail=0)
# Returns: ['word1', 'word2', 'word3']

# Detailed (words + boxes + confidence)
results = processor.extract_text(image_path, detail=1)
# Returns: [
#   {'text': 'word1', 'confidence': 0.95, 'box': [[x1,y1], [x2,y2], ...]},
#   ...
# ]
```

## Troubleshooting

### Issue: "OCR module not available"
**Solution**: Ensure AMD_server/OCR.py is accessible:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from OCR import run_ocr
```

### Issue: "GPU not detected"
**Solution**: Verify ROCm installation:
```bash
rocm-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### Issue: "Image file not found"
**Solution**: Check file paths in database match actual locations:
```python
loader = ImageLoader()
paths = [img['file_path'] for img in loader.get_document_images()]
existing, missing = loader.verify_files_exist(paths)
print(f"Missing: {len(missing)} files")
```

## Next Steps

### Pipeline 3 Completion (OCR - DONE ✅)
- [x] OCR processor implementation
- [x] Image loader for database/disk
- [x] Integration with ML inference
- [x] Integration with Evidence Sorter Agent
- [x] Test suite
- [x] Documentation

### Optional Enhancements
- [ ] Image quality detection (blur, rotation)
- [ ] Auto-rotation for upside-down documents
- [ ] Layout analysis (headers, tables, signatures)
- [ ] Table extraction from images
- [ ] Handwriting recognition

## References

- [EasyOCR Documentation](https://github.com/JaidedAI/EasyOCR)
- [AMD ROCm](https://rocm.docs.amd.com/)
- [RVLCDIP Dataset](https://www.cs.cmu.edu/~aharley/rvl-cdip/)

---

**Status**: ✅ Production Ready (v1.0)  
**Last Updated**: October 25, 2025  
**Author**: BonelessWater Team
