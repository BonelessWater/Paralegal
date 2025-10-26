# =========================
# file: server.py
# =========================
#!/usr/bin/env python3
"""
server.py — Prompt + OCR + Email ADK API on AMD server
"""
from flask import Flask, request, jsonify
import time

from OCR import run_ocr  # existing
# New: email ADK orchestrator+reply
try:
    from ADK.email_adk import orchestrate_and_reply
except Exception as e:
    orchestrate_and_reply = None
    print(f"[SERVER] ADK.email_adk not available: {e}")

app = Flask(__name__)

@app.post("/prompt")
def handle_prompt():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    print(f"[SERVER] /prompt: {prompt[:140]}")
    time.sleep(0.02)
    return jsonify({"response": f"Processed prompt: {prompt.upper()}"})

@app.post("/ocr")
def ocr_endpoint():
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url")
    image_b64 = data.get("image_b64")
    langs     = data.get("langs")
    detail    = int(data.get("detail", 0))
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

@app.post("/email")
def email_endpoint():
    """
    Body:
      {
        "from": "Alice <a@ex.com>",
        "subject": "Issue text",
        "body": "plain or html",
        "attachments": [
          {"filename":"scan.jpg","content_b64":"...","mimetype":"image/jpeg"}
        ],
        "jurisdiction":"optional",
        "terms":"optional",
        "citext":"optional"
      }
    """
    if orchestrate_and_reply is None:
        return jsonify(error="Email ADK not available"), 501
    payload = request.get_json(silent=True) or {}
    missing = [k for k in ("from","subject","body") if not (payload.get(k) or "").strip()]
    if missing:
        return jsonify(error=f"Missing fields: {', '.join(missing)}"), 400
    try:
        print(f"[SERVER] /email from={payload.get('from')} subj={payload.get('subject')}")
        res = orchestrate_and_reply(payload)
        code = 200 if res.get("status") in {"ok","reply_failed"} else 500
        return jsonify(res), code
    except Exception as e:
        print(f"[SERVER][EMAIL] Error: {e}")
        return jsonify(error="Email orchestration failed"), 500

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

