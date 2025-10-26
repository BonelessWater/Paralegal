# =========================
# file: APIs/client.py
# =========================
#!/usr/bin/env python3
"""
client.py — Talks to your AMD server:
- prompt mode (default): send text to /prompt
- ocr mode: "ocr <path_or_url> [detail]" → posts image to /ocr
- NEW: post_email(payload) → posts to /email
"""
import os, sys, base64, requests, json

BASE = os.getenv("SERVER_BASE", "http://134.199.202.8:8080").rstrip("/")
PROMPT_URL = f"{BASE}/prompt"
OCR_URL    = f"{BASE}/ocr"
EMAIL_URL  = f"{BASE}/email"

HEADERS = {"Content-Type": "application/json"}

def post_prompt(text: str):
    r = requests.post(PROMPT_URL, headers=HEADERS, json={"prompt": text}, timeout=60)
    r.raise_for_status()
    return r.json()

def post_ocr(target: str, detail: int = 0):
    if target.lower().startswith(("http://","https://")):
        payload = {"image_url": target, "detail": detail}
    else:
        with open(target, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {"image_b64": b64, "detail": detail}
    r = requests.post(OCR_URL, headers=HEADERS, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def post_email(payload: dict):
    # Expected keys: from, subject, body, attachments[]
    r = requests.post(EMAIL_URL, headers=HEADERS, data=json.dumps(payload), timeout=180)
    r.raise_for_status()
    return r.json()

# Optional CLI for manual testing (unchanged prompt/ocr modes)
def main():
    print(f"Connected to {BASE}. Type your prompts.")
    print("To OCR an image:  ocr <path_or_url> [detail]")
    print("To send email JSON: email <path_to_payload.json>")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line: continue
        if line.lower() in {"exit","quit"}: break
        if line.lower().startswith("ocr "):
            parts = line.split()
            target = parts[1] if len(parts)>=2 else ""
            detail = int(parts[2]) if len(parts)>=3 and parts[2].isdigit() else 0
            try:
                print("OCR:", post_ocr(target, detail))
            except Exception as e:
                print("OCR error:", e)
            continue
        if line.lower().startswith("email "):
            path = line.split(maxsplit=1)[1]
            try:
                with open(path,"r",encoding="utf-8") as f:
                    payload = json.load(f)
                print("EMAIL:", post_email(payload))
            except Exception as e:
                print("Email error:", e)
            continue
        try:
            print("Server:", post_prompt(line))
        except Exception as e:
            print("Prompt error:", e)

if __name__ == "__main__":
    main()

