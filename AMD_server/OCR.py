#!/usr/bin/env python3
"""
OCR.py — AMD ROCm-accelerated OCR (EasyOCR on PyTorch)
Provides run_ocr() that returns just the recognized words.

Install (inside your venv on the server):
  pip install --upgrade pip setuptools wheel
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
  pip install easyocr opencv-python-headless pillow requests
"""

from __future__ import annotations
import base64, io, os, threading
from typing import List, Dict, Any, Optional

import requests
from PIL import Image
import easyocr
import torch

# One global reader, lazily initialized (thread-safe)
_READER = None
_LOCK = threading.Lock()

def _get_reader(langs: Optional[List[str]] = None, gpu: Optional[bool] = None):
    global _READER
    if langs is None:
        langs = ["en"]
    if gpu is None:
        gpu = True  # uses ROCm via PyTorch
    with _LOCK:
        if _READER is None:
            try:
                print(f"[OCR] torch={torch.__version__} cuda_available={torch.cuda.is_available()}")
                if torch.cuda.is_available():
                    print(f"[OCR] device_count={torch.cuda.device_count()} current_device={torch.cuda.current_device()}")
            except Exception:
                pass
            _READER = easyocr.Reader(langs, gpu=gpu)
            print(f"[OCR] EasyOCR initialized langs={langs} gpu={gpu}")
    return _READER

def _bytes_from_b64(image_b64: str) -> bytes:
    # allow data: URIs or raw base64
    if "," in image_b64 and "base64" in image_b64.split(",", 1)[0]:
        image_b64 = image_b64.split(",", 1)[1]
    return base64.b64decode(image_b64)

def _bytes_from_url(image_url: str, timeout: int = 20) -> bytes:
    r = requests.get(image_url, timeout=timeout)
    r.raise_for_status()
    return r.content

def _pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGB")

def run_ocr(
    *,
    image_b64: Optional[str] = None,
    image_url: Optional[str] = None,
    langs: Optional[List[str]] = None,
    detail: int = 0,
) -> Dict[str, Any]:
    """
    Returns just the words by default:
        {"texts": ["word1","word2", ...]}

    Args:
        image_b64: base64 image
        image_url: http/https URL
        langs: e.g., ["en","es"]
        detail: 0 => words only, 1 => include boxes & confidences
    """
    if not image_b64 and not image_url:
        return {"error": "Provide image_b64 or image_url"}

    img_bytes = _bytes_from_b64(image_b64) if image_b64 else _bytes_from_url(image_url)
    img = _pil_from_bytes(img_bytes)
    tmp_path = "/tmp/ocr_input.jpg"
    img.save(tmp_path, format="JPEG")

    reader = _get_reader(langs=langs or ["en"], gpu=True)

    if detail == 0:
        texts = reader.readtext(tmp_path, detail=0)  # just words
        return {"texts": [str(t) for t in texts]}

    # detail=1 → (box, text, conf)
    results = reader.readtext(tmp_path, detail=1)
    out = []
    for box, text, conf in results:
        out.append({"text": str(text), "confidence": float(conf),
                    "box": [[float(x), float(y)] for x, y in box]})
    return {"results": out}
