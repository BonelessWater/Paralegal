#!/usr/bin/env python3
"""
server.py — Prompt + OCR API on AMD server
Run:
  cd ~/Paralegal/AMD_server
  source ~/venv/bin/activate
  python server.py
"""

from flask import Flask, request, jsonify
import time
from OCR import run_ocr  # import our OCR function

app = Flask(__name__)

@app.post("/prompt")
def handle_prompt():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    print(f"[SERVER] Received prompt: {prompt}")
    time.sleep(0.05)
    return jsonify({"response": f"Processed prompt: {prompt.upper()}"})

@app.post("/ocr")
def ocr_endpoint():
    """
    Body (JSON):
      { "image_url": "https://..." }  OR  { "image_b64": "<base64>" }
    Optional:
      { "langs": ["en","es"], "detail": 0|1 }
    Default reply with detail=0 is:
      { "texts": ["...","..."] }
    """
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url")
    image_b64 = data.get("image_b64")
    langs     = data.get("langs")
    detail    = int(data.get("detail", 0))  # default words only

    if not image_url and not image_b64:
        return jsonify(error="Provide image_url or image_b64"), 400

    try:
        res = run_ocr(image_b64=image_b64, image_url=image_url, langs=langs, detail=detail)
        if "error" in res:
            return jsonify(res), 400
        return jsonify(res)
    except Exception as e:
        print(f"[SERVER][OCR] Error: {e}")
        return jsonify(error="OCR failed"), 500

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    # Listen on all interfaces so your client can reach it
    app.run(host="0.0.0.0", port=8080)
