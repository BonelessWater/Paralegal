# file: ADK/email_adk.py
#!/usr/bin/env python3
"""
Email ADK — orchestrate an email payload and reply via SMTP.

Env (dotenv is optional; load before server if desired):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_STARTTLS=1
  ADK_DEFAULT_JURISDICTION="Florida state courts"
  ADK_DEFAULT_TERMS=""
  OCR_DETAIL=0
"""

from __future__ import annotations
import base64
import os
import re
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List, Tuple

from orchestrator import run_orchestrated
from OCR import run_ocr  # reuse server OCR

# ---- small utils ------------------------------------------------------------
IMG_MIMES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
    "image/tiff", "image/bmp"
}
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".bmp"}

def _lower(s: str) -> str: return (s or "").lower().strip()
def _ext(fn: str) -> str:
    import os
    return os.path.splitext(fn or "")[1].lower()

def _strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())

def _parse_directives(body: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in (body or "").splitlines()[:25]:
        m = re.match(r"^\s*(jurisdiction|terms|citext)\s*:\s*(.+)\s*$", line, flags=re.I)
        if m: out[m.group(1).lower()] = m.group(2).strip()
    return out

def _send_email(to_addr: str, subject: str, text: str) -> Tuple[bool, str]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    use_starttls = os.getenv("SMTP_STARTTLS", "1") not in {"0", "false", "False"}
    from_addr = user or os.getenv("SMTP_FROM", user or "noreply@example.com")

    if not (host and port and user and pwd):
        return False, "SMTP env missing (SMTP_HOST/PORT/USER/PASS)"

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = f"Re: {subject}"
    msg.set_content(text)

    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            if use_starttls:
                s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return True, "sent"
    except Exception as e:
        return False, f"SMTP error: {e}"

def _extract_address(header_val: str) -> str:
    from email.utils import parseaddr
    _, addr = parseaddr(header_val or "")
    return addr or header_val or ""

# ---- core API ----------------------------------------------------------------
def orchestrate_and_reply(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts JSON payload from /email and performs:
      1) Build docs from body + OCR(image attachments)
      2) Run orchestrator
      3) Email reply with the synthesized note
    Returns a compact JSON summary.
    """
    email_from   = payload.get("from", "")
    subject      = payload.get("subject", "").strip() or "Legal question"
    raw_body     = payload.get("body", "") or ""
    attachments  = payload.get("attachments", []) or []

    # Defaults with optional inline overrides
    defaults_jur = os.getenv("ADK_DEFAULT_JURISDICTION", "Florida state courts")
    defaults_terms = os.getenv("ADK_DEFAULT_TERMS", "")
    ocr_detail = int(os.getenv("OCR_DETAIL", "0"))

    # Normalize body
    is_html = bool(re.search(r"</?[a-z][\s\S]*>", raw_body, flags=re.I))
    body = _strip_html(raw_body) if is_html else raw_body
    directives = _parse_directives(body)

    jurisdiction = directives.get("jurisdiction") or payload.get("jurisdiction") or defaults_jur
    terms        = directives.get("terms") or payload.get("terms") or defaults_terms
    citext       = directives.get("citext") or payload.get("citext") or ""

    # Build docs
    docs: List[Dict[str, Any]] = []
    if body.strip():
        docs.append({
            "id": "email_body",
            "meta": {"id": "email_body", "from": email_from, "subject": subject},
            "text": body
        })

    # OCR image attachments
    ocr_docs: List[Dict[str, Any]] = []
    for att in attachments:
        fn = att.get("filename", "file")
        mime = _lower(att.get("mimetype", ""))
        b64 = att.get("content_b64")
        if not b64:
            continue
        is_img = mime in IMG_MIMES or _ext(fn) in IMG_EXTS
        if not is_img:
            continue
        try:
            res = run_ocr(image_b64=b64, image_url=None, langs=None, detail=ocr_detail)
            texts = res.get("texts") or res.get("results") or []
            text_joined = "\n".join(texts) if isinstance(texts, list) else str(texts)
            ocr_docs.append({"id": fn, "meta": {"id": fn, "source": "ocr"}, "text": text_joined})
        except Exception as e:
            ocr_docs.append({"id": fn, "meta": {"id": fn, "source": "ocr", "error": str(e)}, "text": ""})

    docs.extend(ocr_docs)

    # Run orchestrator (sync wrapper over async not required here; orchestrator provides sync helper internally)
    import asyncio
    result = asyncio.run(run_orchestrated(
        issue=subject,
        jurisdiction=jurisdiction,
        terms=terms,
        raw_citation_text=citext,
        docs=docs,
        selected_agents=None
    ))

    # Compose reply
    note = result.get("note") or "(no synthesized note)"
    reply_lines = [
        "Here is a concise synthesis based on your email and attachments.",
        "",
        f"Issue: {subject}",
        f"Jurisdiction: {jurisdiction}",
        f"Agents run: {', '.join(result.get('agents_run', [])) or 'auto'}",
        "",
        note,
        "",
        f"--",
        f"(ctx_len={result.get('ctx_len')}, build_time={result.get('build_time_sec')}s)"
    ]
    reply_text = "\n".join(reply_lines)

    to_addr = _extract_address(email_from)
    sent_ok, sent_msg = _send_email(to_addr, subject, reply_text)

    status = "ok" if sent_ok else "reply_failed"
    return {
        "status": status,
        "reply_status": sent_msg,
        "to": to_addr,
        "subject": subject,
        "agents_run": result.get("agents_run", []),
        "errors": result.get("errors", []),
        "ctx_len": result.get("ctx_len"),
        "build_time_sec": result.get("build_time_sec"),
        "docs_count": len(docs),
        "ocr_docs": len(ocr_docs),
    }
