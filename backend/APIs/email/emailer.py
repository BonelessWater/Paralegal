# file: APIs/email/emailer.py
#!/usr/bin/env python3
import os
import time
import email
import mimetypes
from typing import Iterable, Optional, Tuple, List
from email.header import decode_header, make_header
from email.message import Message
from dotenv import load_dotenv
from imapclient import IMAPClient

POLL_INTERVAL = 3
DOC_EXTS = {".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".pptx"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_HOST  = os.getenv("IMAP_HOST", "imap.gmail.com")
MAILBOXES  = [mb.strip() for mb in os.getenv("MAILBOXES", "INBOX,[Gmail]/All Mail").split(",") if mb.strip()]
OCR_DETAIL = int(os.getenv("OCR_DETAIL", "0"))

last_seen: dict[str, int] = {}
seen_message_ids: set[str] = set()

# Import client from the package; run with: python -m APIs.email.emailer (repo root)
from ..client import post_prompt, post_ocr  # type: ignore

def connect() -> IMAPClient:
    srv = IMAPClient(IMAP_HOST, ssl=True)
    srv.login(EMAIL_USER, EMAIL_PASS)
    return srv

def latest_uid(srv: IMAPClient, mailbox: str) -> int:
    srv.select_folder(mailbox, readonly=True)
    uids = srv.search(['ALL'])
    return max(uids) if uids else 0

def decode_header_str(raw: Optional[str]) -> str:
    try:
        return str(make_header(decode_header(raw or "")))
    except Exception:
        return raw or ""

def is_attachment(part: Message) -> bool:
    cd = (part.get("Content-Disposition") or "").lower()
    filename = part.get_filename()
    return ("attachment" in cd) or bool(filename)

def normalize_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

def choose_text_body(msg: Message) -> Tuple[str, str]:
    if msg.is_multipart():
        plain_bodies: List[str] = []
        html_bodies: List[str] = []
        for part in msg.walk():
            if is_attachment(part):
                continue
            ctype = (part.get_content_type() or "").lower()
            if ctype == "text/plain":
                try:
                    charset = part.get_content_charset() or "utf-8"
                    plain_bodies.append(part.get_payload(decode=True).decode(charset, errors="replace"))
                except Exception:
                    continue
            elif ctype == "text/html":
                try:
                    charset = part.get_content_charset() or "utf-8"
                    html_bodies.append(part.get_payload(decode=True).decode(charset, errors="replace"))
                except Exception:
                    continue
        if plain_bodies:
            return ("text/plain", "\n".join(plain_bodies).strip())
        if html_bodies:
            import re
            text = re.sub(r"<[^>]+>", " ", "\n".join(html_bodies))
            text = " ".join(text.split())
            return ("text/html", text.strip())
        return ("", "")
    else:
        ctype = (msg.get_content_type() or "").lower()
        if ctype.startswith("text/"):
            try:
                charset = msg.get_content_charset() or "utf-8"
                return (ctype, msg.get_payload(decode=True).decode(charset, errors="replace").strip())
            except Exception:
                return (ctype, "")
        return ("", "")

def ensure_filename(part: Message, fallback_prefix: str = "attachment") -> str:
    fn = part.get_filename()
    if fn:
        return decode_header_str(fn)
    guessed = mimetypes.guess_extension((part.get_content_type() or "").lower())
    stamp = int(time.time() * 1000)
    return f"{fallback_prefix}_{stamp}{guessed or ''}"

def save_attachments(msg: Message) -> List[str]:
    saved: List[str] = []
    for part in msg.walk():
        if not is_attachment(part):
            continue
        filename = ensure_filename(part, "file")
        data = part.get_payload(decode=True)
        if not data:
            continue
        with open(filename, "wb") as f:
            f.write(data)
        print(f"💾 Saved attachment: {filename}")
        saved.append(filename)
    return saved

def send_prompt_to_server(frm: str, subj: str, body_text: str) -> None:
    if not body_text:
        body_text = "(no body)"
    prompt = f"EMAIL FROM: {frm}\nSUBJECT: {subj}\n\nBODY:\n{body_text}"
    try:
        res = post_prompt(prompt)
        print(f"🛰️  /prompt OK: {res}")
    except Exception as e:
        print(f"❌ /prompt error: {e}")

def send_ocr_for_images(files: Iterable[str], detail: int = OCR_DETAIL) -> None:
    for path in files:
        ext = normalize_ext(path)
        if ext not in IMG_EXTS:
            continue
        try:
            res = post_ocr(path, detail=detail)
            print(f"🛰️  /ocr {os.path.basename(path)} → {res.get('texts', res)}")
        except Exception as e:
            print(f"❌ /ocr error ({path}): {e}")

def fetch_and_process(srv: IMAPClient, mailbox: str, uids: List[int]) -> None:
    if not uids:
        return
    srv.select_folder(mailbox, readonly=True)
    data = srv.fetch(uids, ['RFC822'])
    for uid in sorted(data.keys()):
        try:
            msg = email.message_from_bytes(data[uid][b'RFC822'])
            msg_id = msg.get("Message-ID")
            if msg_id in seen_message_ids:
                continue
            seen_message_ids.add(msg_id)

            subj = decode_header_str(msg.get('Subject', '(no subject)'))
            frm  = decode_header_str(msg.get('From', '(unknown)'))
            print(f"📩 [{mailbox}] UID {uid} | From: {frm} | Subject: {subj}")

            _, body_text = choose_text_body(msg)
            send_prompt_to_server(frm, subj, body_text)

            saved_files = save_attachments(msg)
            if saved_files:
                send_ocr_for_images(saved_files, detail=OCR_DETAIL)

        except Exception as e:
            print(f"⚠️  Processing error for UID {uid}: {e}")

def main():
    print(f"📬 Polling {EMAIL_USER} on {', '.join(MAILBOXES)} every {POLL_INTERVAL}s...")
    srv: Optional[IMAPClient] = None
    try:
        srv = connect()
        # Initialize at the newest UID so startup processes nothing existing.
        for mb in MAILBOXES:
            newest = latest_uid(srv, mb)
            last_seen[mb] = newest       # <-- key change
            print(f"Starting [{mb}] at UID: {last_seen[mb]} (newest is {newest})")

        while True:
            try:
                for mb in MAILBOXES:
                    srv.select_folder(mb, readonly=True)
                    new_uids = srv.search(['UID', f'{last_seen[mb]+1}:*'])
                    new_uids = [uid for uid in new_uids if uid > last_seen[mb]]
                    if new_uids:
                        fetch_and_process(srv, mb, new_uids)
                        last_seen[mb] = max(last_seen[mb], max(new_uids))
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                print("\n👋 Stopping (Ctrl+C).")
                break
            except Exception as e:
                print(f"⚠️  Error: {e}. Reconnecting in 5s...")
                time.sleep(5)
                try:
                    if srv:
                        srv.logout()
                except Exception:
                    pass
                srv = connect()
                # Catch-up only from last_seen forward (still "new only").
                for mb in MAILBOXES:
                    srv.select_folder(mb, readonly=True)
                    catch_up = srv.search(['UID', f'{last_seen[mb]+1}:*'])
                    catch_up = [uid for uid in catch_up if uid > last_seen[mb]]
                    if catch_up:
                        fetch_and_process(srv, mb, catch_up)
                        last_seen[mb] = max(last_seen[mb], max(catch_up))
    finally:
        try:
            if srv:
                srv.logout()
        except Exception:
            pass

if __name__ == "__main__":
    main()
