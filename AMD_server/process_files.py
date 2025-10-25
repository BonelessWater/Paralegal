#!/usr/bin/env python3
"""
legal_ingest.py — Ingest legal documents (PDFs, images, text) and convert
into a standardized, LLM‑ready JSON schema plus chunked prompt blocks.

NEW: Optional Saul summaries via local OpenAI-compatible server.

Key features
------------
- Handles: native PDFs (text), scanned PDFs (OCR), images (OCR), plain text.
- Auto‑detects when a PDF needs OCR (low text density) and falls back.
- Pluggable OCR backends: Tesseract (pytesseract) and/or EasyOCR (no system deps).
- Extracts structured cues with lightweight regex rules (case #, court, dates, citations).
- Heuristic sectionizer for ALL‑CAPS / numbered headings.
- Chunker with token budget (estimates tokens if tiktoken is unavailable).
- **Saul integration**: generate a concise summary per document and (optionally) per chunk.
- Produces one JSON per input (or streams to STDOUT), ready for prompting.

Install
-------
# Minimal core (fitz = PyMuPDF)
pip install pymupdf pillow langdetect

# Optional OCR backends (install any you prefer)
pip install pytesseract
pip install easyocr

# Optional token counting (nicer chunking with OpenAI/Anthropic encodings)
pip install tiktoken

# Saul (OpenAI compatible client)
pip install openai

System notes
------------
- Tesseract backend requires system binary `tesseract` in PATH (sudo apt install tesseract-ocr).
- EasyOCR is pure‑pip but larger (Torch will be pulled in). Good on GPU boxes.
- Saul server assumed at http://localhost:8000/v1 with model "Equall/Saul-7B-Instruct-v1".

Usage
-----
python legal_ingest.py INPUT_PATH [more paths ...] \
  --out out_dir \
  --ocr auto|tesseract|easyocr|none \
  --chunk-tokens 1200 \
  --max-chars 0 \
  --emit pretty|compact|ndjson \
  --doc-id-prefix "CaseA" \
  --language en \
  [--saul-enable] [--saul-url http://localhost:8000/v1] \
  [--saul-api-key dummy] [--saul-model Equall/Saul-7B-Instruct-v1] \
  [--saul-max-tokens 160] [--saul-temperature 0.2] \
  [--saul-chunks 0]

Examples
--------
# Single PDF -> JSON to out_dir
python legal_ingest.py ./docs/complaint.pdf --out ./out --ocr auto --saul-enable

# Folder of mixed files -> NDJSON to stdout (no summaries)
python legal_ingest.py ./inbox --emit ndjson --ocr auto > inbox.ndjson

# Force EasyOCR, chunk around 1500 tokens + make Saul doc summary and top 3 chunk summaries
python legal_ingest.py ./scans --ocr easyocr --chunk-tokens 1500 --out ./out \
  --saul-enable --saul-chunks 3

"""
from __future__ import annotations
import os, re, io, sys, json, argparse, hashlib, time, mimetypes, glob
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

# -------- Optional imports guarded ---------
try:
    import fitz  # PyMuPDF
except Exception as e:
    print("ERROR: PyMuPDF (pymupdf) is required. pip install pymupdf", file=sys.stderr)
    raise

try:
    from PIL import Image
except Exception:
    Image = None  # Will error only if we actually need OCR on images

try:
    import tiktoken  # for accurate token counts
except Exception:
    tiktoken = None

try:
    from langdetect import detect
except Exception:
    detect = None

# OCR backends (optional)
try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import easyocr as _easyocr
except Exception:
    _easyocr = None

# Saul (OpenAI-compatible) — optional
try:
    from openai import OpenAI as _OpenAI
except Exception:
    _OpenAI = None

# ---------------- Token utils ----------------
def estimate_tokens(text: str, model_hint: str = "o200k_base") -> int:
    """Return approximate token count.
    - If tiktoken available, use chosen encoding; else fallback heuristic.
    """
    if tiktoken:
        try:
            enc = tiktoken.get_encoding(model_hint)
            return len(enc.encode(text))
        except Exception:
            pass
    # heuristic: ~1 token per 4 chars as rough average
    return max(1, len(text) // 4)

# --------------- OCR backends ----------------
class OCRBackend:
    def ocr(self, image: Image.Image, lang: str = "eng") -> str:  # type: ignore
        raise NotImplementedError

class TesseractOCR(OCRBackend):
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if pytesseract is None:
            raise RuntimeError("pytesseract not installed. pip install pytesseract and system tesseract.")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    def ocr(self, image: Image.Image, lang: str = "eng") -> str: # type: ignore
        return pytesseract.image_to_string(image, lang=lang)

class EasyOCROCR(OCRBackend):
    def __init__(self, lang: str = "en"):
        if _easyocr is None:
            raise RuntimeError("easyocr not installed. pip install easyocr")
        # lazy reader: instantiate once
        self.reader = _easyocr.Reader([lang], gpu=True if self._has_torch_cuda() else False)
    def _has_torch_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False
    def ocr(self, image: Image.Image, lang: str = "eng") -> str: # type: ignore
        # EasyOCR expects a numpy array; PIL -> np
        import numpy as np
        arr = np.array(image.convert("RGB"))
        results = self.reader.readtext(arr, detail=0, paragraph=True)
        return "\n".join(results)

# --------------- Regex heuristics ------------
RE_CASE_NO = re.compile(r"\bCase\s+No\.?\s*[:#]?\s*([A-Za-z0-9\-:/\.]+)")
RE_COURT = re.compile(r"\bIN THE\s+([A-Z ,.'\-]+?)\s+COURT\b")
RE_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b")
RE_USC = re.compile(r"\b\d+\s+U\.S\.C\.\s*§+\s*\d+[A-Za-z0-9\-]*\b")
RE_CASE_CITE = re.compile(r"\b\d+\s+[A-Z][A-Za-z\d\. ]+\s+\d+\b")  # e.g., 410 U.S. 113

RE_SECTION_HEADER = re.compile(r"^(?:[A-Z0-9][A-Z0-9 .\-]{3,}|\d+\.[^\n]+)$")

# --------------- Helpers --------------------
def guess_language(text: str, default: str = "en") -> str:
    if not text:
        return default
    if detect:
        try:
            return detect(text) or default
        except Exception:
            return default
    return default

def sha1_of_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Chunk:
    id: int
    text: str
    tokens: int

@dataclass
class Extraction:
    doc_id: str
    source_path: str
    mime_type: str
    ingested_at: str
    detected_language: str
    document_type: str
    parties: List[str]
    case_numbers: List[str]
    court: str
    dates: Dict[str, List[str]]
    citations: Dict[str, List[str]]
    sections: List[Dict[str, str]]
    extracted_text: str
    prompt_blocks: Dict[str, str]
    chunks: List[Chunk]
    saul: Dict[str, Any] = field(default_factory=dict)  # holds Saul summaries if enabled

# --------------- Saul helpers ----------------
def _saul_client(base_url: str, api_key: str):
    if _OpenAI is None:
        raise RuntimeError("openai client not installed. pip install openai")
    return _OpenAI(base_url=base_url, api_key=api_key)

def _saul_summarize_text(client, model: str, text: str, max_tokens: int = 160, temperature: float = 0.2) -> str:
    # trim overly long prompts to ~4k chars for safety if needed
    snippet = text[:8000]
    prompt = (
        "You are a legal summarizer. Write a single concise paragraph (2-4 sentences) "
        "capturing key parties, issues, relief, and posture.\n\nTEXT:\n" + snippet
    )
    try:
        resp = client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return (resp.choices[0].text or "").strip()
    except Exception as e:
        return f"[SAUL_ERROR] {e}"

# --------------- Core pipeline --------------
class Ingestor:
    def __init__(self, ocr_mode: str = "auto", preferred_lang: str = "eng", tesseract_cmd: Optional[str] = None, easyocr_lang: str = "en",
                 saul_enabled: bool = False, saul_url: str = "http://localhost:8000/v1", saul_api_key: str = "dummy",
                 saul_model: str = "Equall/Saul-7B-Instruct-v1", saul_max_tokens: int = 160, saul_temperature: float = 0.2,
                 saul_chunks: int = 0):
        self.ocr_mode = ocr_mode
        self.preferred_lang = preferred_lang
        self._ocr_backend: Optional[OCRBackend] = None
        self._tesseract_cmd = tesseract_cmd
        self._easyocr_lang = easyocr_lang
        # Saul
        self.saul_enabled = saul_enabled
        self.saul_url = saul_url
        self.saul_api_key = saul_api_key
        self.saul_model = saul_model
        self.saul_max_tokens = saul_max_tokens
        self.saul_temperature = saul_temperature
        self.saul_chunks = max(0, saul_chunks)
        self._saul_client = None

    def _get_backend(self) -> Optional[OCRBackend]:
        if self.ocr_mode == "none":
            return None
        if self._ocr_backend is not None:
            return self._ocr_backend
        if self.ocr_mode in ("auto", "tesseract"):
            try:
                self._ocr_backend = TesseractOCR(self._tesseract_cmd)
                return self._ocr_backend
            except Exception:
                if self.ocr_mode == "tesseract":
                    raise
        if self.ocr_mode in ("auto", "easyocr"):
            self._ocr_backend = EasyOCROCR(self._easyocr_lang)
            return self._ocr_backend
        return None

    def _get_saul(self):
        if not self.saul_enabled:
            return None
        if self._saul_client is None:
            self._saul_client = _saul_client(self.saul_url, self.saul_api_key)
        return self._saul_client

    # ---------- File handlers ----------
    def ingest_path(self, path: str, chunk_tokens: int = 1200, max_chars: int = 0, language_hint: Optional[str] = None) -> Extraction:
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "application/octet-stream"
        base_id = os.path.basename(path)
        with open(path, "rb") as f:
            blob = f.read()
        doc_hash = sha1_of_bytes(blob)[:10]
        doc_id = f"{base_id}-{doc_hash}"

        text, sections = "", []
        if mime == "application/pdf" or path.lower().endswith(".pdf"):
            text, sections = self._extract_pdf(path)
        elif mime and mime.startswith("image/"):
            text = self._extract_image(blob)
        else:
            # Try text fallback
            try:
                text = blob.decode("utf-8", errors="ignore")
            except Exception:
                text = ""

        if max_chars > 0:
            text = text[:max_chars]

        lang = language_hint or guess_language(text)
        fields = self._light_structures(text)
        doc_type = self._guess_document_type(text)
        citations = self._find_citations(text)

        if not sections:
            sections = self._sectionize(text)

        prompt_blocks = self._prompt_blocks(text, sections, fields)
        chunks = self._chunk_text(text, tokens_per_chunk=chunk_tokens)

        ex = Extraction(
            doc_id=doc_id,
            source_path=os.path.abspath(path),
            mime_type=mime,
            ingested_at=now_iso(),
            detected_language=lang,
            document_type=doc_type,
            parties=fields.get("parties", []),
            case_numbers=fields.get("case_numbers", []),
            court=fields.get("court", ""),
            dates={"mentions": fields.get("dates", [])},
            citations=citations,
            sections=sections,
            extracted_text=text,
            prompt_blocks=prompt_blocks,
            chunks=chunks,
        )

        # Optionally attach Saul summaries
        if self.saul_enabled and text.strip():
            client = self._get_saul()
            if client:
                doc_sum = _saul_summarize_text(client, self.saul_model, prompt_blocks.get("summary") or text,
                                               max_tokens=self.saul_max_tokens, temperature=self.saul_temperature)
                chunk_summaries = []
                if self.saul_chunks > 0:
                    for ch in ex.chunks[: self.saul_chunks]:
                        s = _saul_summarize_text(client, self.saul_model, ch.text,
                                                 max_tokens=self.saul_max_tokens, temperature=self.saul_temperature)
                        chunk_summaries.append({"chunk_id": ch.id, "summary": s})
                ex.saul = {
                    "model": self.saul_model,
                    "doc_summary": doc_sum,
                    "chunk_summaries": chunk_summaries,
                }
        return ex

    # ---------- PDF ----------
    def _extract_pdf(self, path: str) -> Tuple[str, List[Dict[str, str]]]:
        doc = fitz.open(path)
        texts: List[str] = []
        # Try native text first
        for page in doc:
            txt = page.get_text("text") or ""
            texts.append(txt)
        native_text = "\n".join(texts).strip()
        if len(native_text) >= 300:  # heuristic: plenty of live text
            return native_text, []
        # If not enough, OCR each page
        backend = self._get_backend()
        if backend is None:
            return native_text, []  # No OCR requested/available
        ocr_texts: List[str] = []
        for i, page in enumerate(doc):
            # Render page to image
            pix = page.get_pixmap(dpi=300)  # decent OCR res
            if Image is None:
                raise RuntimeError("Pillow not installed. pip install pillow")
            pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_txt = backend.ocr(pil, lang=self.preferred_lang)
            ocr_texts.append(ocr_txt)
        return "\n".join(ocr_texts), []

    # ---------- Images ----------
    def _extract_image(self, blob: bytes) -> str:
        backend = self._get_backend()
        if backend is None:
            raise RuntimeError("Image requires OCR but no backend available. Install pytesseract or easyocr and use --ocr.")
        if Image is None:
            raise RuntimeError("Pillow not installed. pip install pillow")
        with io.BytesIO(blob) as bio:
            img = Image.open(bio).convert("RGB")
        return backend.ocr(img, lang=self.preferred_lang)

    # ---------- Light structure ----------
    def _light_structures(self, text: str) -> Dict[str, Any]:
        heads = [ln.strip() for ln in text.splitlines()[:80] if ln.strip()]
        parties: List[str] = []
        court = ""
        case_nos: List[str] = []
        dates: List[str] = []

        # Court (caption style)
        for ln in heads:
            m = RE_COURT.search(ln)
            if m:
                court = m.group(1).strip()
                break

        # Case numbers & dates
        for ln in heads[:120]:
            for m in RE_CASE_NO.finditer(ln):
                case_nos.append(m.group(1))
            dates.extend(RE_DATE.findall(ln))

        # Parties (extremely heuristic)
        # Look for 'Plaintiff', 'Defendant', etc., in first 120 lines
        role_words = ("Plaintiff", "Defendant", "Petitioner", "Respondent", "Appellant", "Appellee")
        for ln in heads[:120]:
            if any(w in ln for w in role_words):
                # Keep a cleaned version
                parties.append(re.sub(r"\s{2,}", " ", ln))

        return {
            "court": court,
            "case_numbers": sorted(set(case_nos)),
            "dates": sorted(set(dates)),
            "parties": parties,
        }

    def _guess_document_type(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["complaint", "petition", "answer", "motion", "brief", "memorandum"]):
            # pick a best guess by first match
            for k in ["complaint","petition","answer","motion","brief","memorandum"]:
                if k in t:
                    return k
        if any(k in t for k in ["agreement", "contract", "terms and conditions", "nda", "lease"]):
            return "contract"
        if "order" in t and "court" in t:
            return "court_order"
        return "unknown"

    def _find_citations(self, text: str) -> Dict[str, List[str]]:
        statutes = sorted(set(RE_USC.findall(text)))
        cases = sorted(set(RE_CASE_CITE.findall(text)))
        return {"statutes": statutes, "cases": cases}

    # ---------- Sectionizer ----------
    def _sectionize(self, text: str) -> List[Dict[str, str]]:
        lines = text.splitlines()
        sections: List[Dict[str, str]] = []
        cur_title = "Preamble"
        cur_buf: List[str] = []
        def flush():
            nonlocal cur_title, cur_buf
            content = "\n".join(cur_buf).strip()
            if content:
                sections.append({"title": cur_title.strip(), "content": content})
            cur_buf = []
        for ln in lines:
            if RE_SECTION_HEADER.match(ln.strip()) and len(ln.strip()) <= 120:
                # new section
                flush()
                cur_title = ln.strip()
            else:
                cur_buf.append(ln)
        flush()
        return sections

    # ---------- Prompt blocks ----------
    def _prompt_blocks(self, text: str, sections: List[Dict[str, str]], fields: Dict[str, Any]) -> Dict[str, str]:
        # Very light extractive summaries — safe defaults (no LLMs used here)
        # Keep short: these are starting points for your prompting pipeline.
        def first_n_chars(s: str, n: int) -> str:
            return (s[:n] + ("…" if len(s) > n else ""))
        summary = first_n_chars(text.replace("\n", " "), 1000)
        facts = []
        for sec in sections:
            title = sec.get("title", "").lower()
            if any(k in title for k in ["facts", "background", "allegations", "statement of facts"]):
                facts.append(first_n_chars(sec.get("content", ""), 1500))
        facts_text = "\n\n".join(facts) if facts else first_n_chars(text, 1200)
        issues = []
        for sec in sections:
            title = sec.get("title", "").lower()
            if any(k in title for k in ["issue", "issues", "questions presented"]):
                issues.append(first_n_chars(sec.get("content", ""), 800))
        issues_text = "\n\n".join(issues)
        reqs = []
        for sec in sections:
            title = sec.get("title", "").lower()
            if any(k in title for k in ["prayer", "relief", "request", "wherefore"]):
                reqs.append(first_n_chars(sec.get("content", ""), 800))
        reqs_text = "\n\n".join(reqs)
        # Minimal caption
        caption = {
            "court": fields.get("court", ""),
            "case_numbers": fields.get("case_numbers", []),
            "parties": fields.get("parties", []),
        }
        caption_text = json.dumps(caption, ensure_ascii=False)
        return {
            "summary": summary,
            "facts": facts_text,
            "issues": issues_text,
            "requests": reqs_text,
            "caption": caption_text,
        }

    # ---------- Chunking ----------
    def _chunk_text(self, text: str, tokens_per_chunk: int = 1200) -> List[Chunk]:
        # Split by paragraphs; accumulate until token budget reached
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: List[Chunk] = []
        buf: List[str] = []
        cur_tokens = 0
        cid = 1
        for p in paras:
            t = estimate_tokens(p)
            if cur_tokens + t > tokens_per_chunk and buf:
                joined = "\n\n".join(buf)
                chunks.append(Chunk(id=cid, text=joined, tokens=estimate_tokens(joined)))
                cid += 1
                buf, cur_tokens = [], 0
            buf.append(p)
            cur_tokens += t
        if buf:
            joined = "\n\n".join(buf)
            chunks.append(Chunk(id=cid, text=joined, tokens=estimate_tokens(joined)))
        return chunks

# --------------- CLI ------------------------
def discover_paths(inputs: List[str]) -> List[str]:
    out: List[str] = []
    for p in inputs:
        if os.path.isdir(p):
            for ext in ("*.pdf", "*.PDF", "*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.txt"):
                out.extend(glob.glob(os.path.join(p, "**", ext), recursive=True))
        else:
            out.append(p)
    return sorted(set(out))

def to_json(o: Any) -> Any:
    if isinstance(o, Chunk):
        return asdict(o)
    if isinstance(o, Extraction):
        d = asdict(o)
        return d
    raise TypeError(type(o))

def main():
    ap = argparse.ArgumentParser(description="Ingest legal documents -> standardized JSON for LLMs (optional Saul summaries)")
    ap.add_argument("inputs", nargs="+", help="Files or directories")
    ap.add_argument("--out", default=None, help="Output directory (if omitted, prints to stdout)")
    ap.add_argument("--emit", choices=["pretty","compact","ndjson"], default="pretty", help="JSON output style")
    ap.add_argument("--ocr", choices=["auto","tesseract","easyocr","none"], default="auto")
    ap.add_argument("--tesseract-cmd", default=None, help="Path to tesseract binary if not in PATH")
    ap.add_argument("--chunk-tokens", type=int, default=1200)
    ap.add_argument("--max-chars", type=int, default=0, help="Trim extracted text to this many characters (0=off)")
    ap.add_argument("--doc-id-prefix", default=None)
    ap.add_argument("--language", default=None, help="Language hint (e.g., en)")
    # Saul flags
    ap.add_argument("--saul-enable", action="store_true", help="Enable Saul summarization")
    ap.add_argument("--saul-url", default="http://localhost:8000/v1", help="Saul server base URL")
    ap.add_argument("--saul-api-key", default="dummy", help="API key for Saul server")
    ap.add_argument("--saul-model", default="Equall/Saul-7B-Instruct-v1", help="Saul model name")
    ap.add_argument("--saul-max-tokens", type=int, default=160)
    ap.add_argument("--saul-temperature", type=float, default=0.2)
    ap.add_argument("--saul-chunks", type=int, default=0, help="Also summarize first N chunks")

    args = ap.parse_args()

    ing = Ingestor(
        ocr_mode=args.ocr,
        tesseract_cmd=args.tesseract_cmd,
        saul_enabled=args.saul_enable,
        saul_url=args.saul_url,
        saul_api_key=args.saul_api_key,
        saul_model=args.saul_model,
        saul_max_tokens=args.saul_max_tokens,
        saul_temperature=args.saul_temperature,
        saul_chunks=args.saul_chunks,
    )

    paths = discover_paths(args.inputs)
    if not paths:
        print("No input files found.", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True) if args.out else None

    def write_obj(obj: Extraction):
        payload = to_json(obj)
        if args.doc_id_prefix:
            payload["doc_id"] = f"{args.doc_id_prefix}-{payload['doc_id']}"
        if args.emit == "ndjson":
            line = json.dumps(payload, ensure_ascii=False)
            if args.out:
                # one .ndjson per batch is tricky; here we dump <doc_id>.jsonl
                outp = os.path.join(args.out, f"{payload['doc_id']}.jsonl")
                with open(outp, "w", encoding="utf-8") as f:
                    f.write(line + "\n")
            else:
                print(line)
        else:
            text = json.dumps(payload, ensure_ascii=False, indent=(2 if args.emit=="pretty" else None))
            if args.out:
                outp = os.path.join(args.out, f"{payload['doc_id']}.json")
                with open(outp, "w", encoding="utf-8") as f:
                    f.write(text)
            else:
                print(text)

    for p in paths:
        try:
            ex = ing.ingest_path(p, chunk_tokens=args.chunk_tokens, max_chars=args.max_chars, language_hint=args.language)
            write_obj(ex)
        except Exception as e:
            print(f"[ERROR] {p}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
