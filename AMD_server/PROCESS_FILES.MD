# Legal Document Ingestor — Quick Start

A lightweight CLI pipeline to convert PDFs, scanned images, or text legal documents into standardized JSON ready for AI prompt input.

## 🧩 Installation
```bash
pip install pymupdf pillow langdetect
# Optional OCR
pip install pytesseract easyocr
# Optional for token estimation
pip install tiktoken
```
Ensure `tesseract-ocr` is installed if using the Tesseract backend:
```bash
sudo apt-get install tesseract-ocr
```

## ⚙️ Usage
```bash
python legal_ingest.py INPUT_PATH [more paths ...] [options]
```
**Common examples:**
```bash
# Single PDF → JSON
python legal_ingest.py ./docs/complaint.pdf --out ./out --ocr auto

# Folder of mixed docs → NDJSON stream
python legal_ingest.py ./cases --emit ndjson --ocr auto > cases.ndjson

# Force EasyOCR backend
python legal_ingest.py ./scans --ocr easyocr --chunk-tokens 1500 --out ./out
```

## 🧠 Options
| Flag | Description |
|------|--------------|
| `--out DIR` | Output directory (default: stdout) |
| `--ocr auto|tesseract|easyocr|none` | Select OCR mode |
| `--chunk-tokens INT` | Max tokens per chunk (default: 1200) |
| `--max-chars INT` | Trim long documents |
| `--emit pretty|compact|ndjson` | Output JSON format |
| `--doc-id-prefix STR` | Prefix for document IDs |

## 📤 Output Structure (abridged)
```json
{
  "doc_id": "complaint.pdf-<hash>",
  "document_type": "complaint|motion|contract|court_order|unknown",
  "court": "UNITED STATES DISTRICT",
  "case_numbers": ["23-cv-01234"],
  "parties": ["Plaintiff", "Defendant"],
  "citations": {"statutes": ["28 U.S.C. § 1331"], "cases": ["410 U.S. 113"]},
  "prompt_blocks": {"summary": "...", "facts": "...", "issues": "..."},
  "chunks": [{"id": 1, "tokens": 1180, "text": "..."}]
}
```

## 🚀 Notes
- **Scanned PDFs/images** automatically OCR’d if `--ocr auto`.
- Works headless; suitable for batch or API integration.
- Use generated JSON as clean, structured input for LLM-based legal assistants.

---

## ⚡ Run Saul Summaries
Create quick summaries of each file’s content using your local Saul model.

```bash
# file: saul_run.py
python run_saul_completion.py
```
➡️ Runs a local Saul-7B model to summarize content using OpenAI-compatible API.

```bash
# Summarize every extracted file in /files directory
for f in /files/*.json; do \
  python run_saul_completion.py --prompt "Summarize: $(cat $f | jq -r .extracted_text | head -c 2000)"; \
done
```
➡️ Iterates through all extracted documents and generates concise AI summaries for each.

```bash
# Save all Saul summaries to a new folder
mkdir -p /summaries && \
for f in /files/*.json; do \
  out=/summaries/$(basename "$f" .json)_summary.txt; \
  python run_saul_completion.py --prompt "Summarize: $(cat $f | jq -r .extracted_text | head -c 2000)" > "$out"; \
done
```
➡️ Stores each summary output neatly for downstream LLM evaluation or dataset building.
