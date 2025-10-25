#!/usr/bin/env python3
import os
import time
import email
from email.header import decode_header, make_header
from dotenv import load_dotenv
from imapclient import IMAPClient

POLL_INTERVAL = 3  # seconds
DOC_EXTS = {".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".pptx"}

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_HOST  = os.getenv("IMAP_HOST", "imap.gmail.com")
MAILBOXES  = [mb.strip() for mb in os.getenv("MAILBOXES", "INBOX,[Gmail]/All Mail").split(",") if mb.strip()]

# Track last UID per mailbox and a global set of seen Message-IDs to avoid duplicates
last_seen = {}
seen_message_ids = set()

def connect():
    srv = IMAPClient(IMAP_HOST, ssl=True)
    srv.login(EMAIL_USER, EMAIL_PASS)
    return srv

def latest_uid(srv, mailbox):
    srv.select_folder(mailbox, readonly=True)
    uids = srv.search(['ALL'])
    return max(uids) if uids else 0

def decode_header_str(raw):
    try:
        return str(make_header(decode_header(raw or "")))
    except Exception:
        return raw or ""

def save_attachments(msg):
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        filename = decode_header_str(filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext in DOC_EXTS:
            data = part.get_payload(decode=True)
            with open(filename, "wb") as f:
                f.write(data)
            print(f"💾 Saved attachment: {filename}")

def fetch_and_print(srv, mailbox, uids):
    if not uids:
        return
    srv.select_folder(mailbox, readonly=True)
    data = srv.fetch(uids, ['RFC822'])
    for uid in sorted(data.keys()):
        msg = email.message_from_bytes(data[uid][b'RFC822'])
        msg_id = msg.get("Message-ID")
        if msg_id in seen_message_ids:
            continue  # skip duplicates across mailboxes
        seen_message_ids.add(msg_id)

        subj = decode_header_str(msg.get('Subject', '(no subject)'))
        frm  = decode_header_str(msg.get('From', '(unknown)'))
        print(f"📩 [{mailbox}] UID {uid} | From: {frm} | Subject: {subj}")
        save_attachments(msg)

def main():
    print(f"📬 Polling {EMAIL_USER} on {', '.join(MAILBOXES)} every {POLL_INTERVAL}s...")
    srv = None
    try:
        srv = connect()
        # Initialize per-mailbox UID trackers
        for mb in MAILBOXES:
            newest = latest_uid(srv, mb)
            last_seen[mb] = max(0, newest - 1)
            print(f"Starting [{mb}] at UID: {last_seen[mb]} (newest is {newest})")

        while True:
            try:
                for mb in MAILBOXES:
                    srv.select_folder(mb, readonly=True)
                    new_uids = srv.search(['UID', f'{last_seen[mb]+1}:*'])
                    new_uids = [uid for uid in new_uids if uid > last_seen[mb]]
                    if new_uids:
                        fetch_and_print(srv, mb, new_uids)
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
                # catch up any missed messages
                for mb in MAILBOXES:
                    srv.select_folder(mb, readonly=True)
                    catch_up = srv.search(['UID', f'{last_seen[mb]+1}:*'])
                    catch_up = [uid for uid in catch_up if uid > last_seen[mb]]
                    if catch_up:
                        fetch_and_print(srv, mb, catch_up)
                        last_seen[mb] = max(last_seen[mb], max(catch_up))
    finally:
        try:
            if srv:
                srv.logout()
        except Exception:
            pass

if __name__ == "__main__":
    main()
