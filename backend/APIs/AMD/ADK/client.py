#!/usr/bin/env python3
"""
client.py — Talks to your AMD server:
- prompt mode (default): send text to /prompt
- ocr mode: "ocr <path_or_url> [detail]" → posts image to /ocr
"""

import os, sys, base64, requests

BASE = os.getenv("SERVER_BASE", "http://134.199.202.8:8080")
PROMPT_URL = f"{BASE}/prompt"
OCR_URL    = f"{BASE}/ocr"

HEADERS = {"Content-Type": "application/json"}
# If you added auth earlier, uncomment:
# HEADERS["Authorization"] = f"Bearer {os.getenv('PROMPT_AUTH','changeme')}"

def post_prompt(text: str):
    r = requests.post(PROMPT_URL, headers=HEADERS, json={"prompt": text}, timeout=60)
    r.raise_for_status()
    return r.json()

def post_ocr(target: str, detail: int = 0):
    if target.lower().startswith("http://") or target.lower().startswith("https://"):
        payload = {"image_url": target, "detail": detail}
    else:
        with open(target, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {"image_b64": b64, "detail": detail}
    r = requests.post(OCR_URL, headers=HEADERS, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def main():
    print(f"Connected to {BASE}. Type your prompts.")
    print("To OCR an image:  ocr <path_or_url> [detail]\nExample: ocr C:\\scan.jpg  or  ocr https://site/img.png 1")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue
        if line.lower() in {"exit","quit"}:
            break

        if line.lower().startswith("ocr "):
            parts = line.split()
            if len(parts) >= 2:
                target = parts[1]
                detail = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 0
                try:
                    res = post_ocr(target, detail=detail)
                    print("OCR:", res.get("texts", res.get("results", res)))
                except Exception as e:
                    print("OCR error:", e)
            else:
                print("Usage: ocr <path_or_url> [detail]")
            continue

        # default: prompt mode
        try:
            res = post_prompt(line)
            print("Server:", res.get("response", res))
        except Exception as e:
            print("Prompt error:", e)

if __name__ == "__main__":
    main()
