#!/usr/bin/env python3
"""
Lawgorithm Call Service — Twilio Media Streams <-> OpenAI Realtime (Stable)

Quick Start
-----------
1) pip install:
   fastapi uvicorn "twilio>=9" python-dotenv websockets

2) Run your app:
   uvicorn lawgorithm:app --host 0.0.0.0 --port 8000

3) Expose publicly with ngrok (HTTPS terminates at ngrok):
   ngrok http --domain YOURSUB.ngrok-free.app 8000

4) .env (examples):
   OPENAI_API_KEY=sk-...
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
   SERVER_DOMAIN=YOURSUB.ngrok-free.app
   REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01

5) In Twilio (or via API), set Voice webhook to:
   https://YOURSUB.ngrok-free.app/voice
   (The app itself tells Twilio to stream to wss://YOURSUB.ngrok-free.app/twilio-media)

Notes
-----
- We use `track='inbound_track'` to avoid feedback/echo.
- We buffer OpenAI audio and flush ~every 60 ms as G.711 μ-law base64 payloads.
- Keep Uvicorn plain HTTP; let ngrok handle TLS. Do NOT point Twilio at http://.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from twilio.rest import Client
from twilio.twiml.voice_response import Connect, VoiceResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Lawgorithm (Stable Realtime Bridge)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # add your dev host(s) as needed, or use ["*"] during local dev:
        # "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],     # allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],     # allows Content-Type, Authorization, etc.
)


# =========================
# Load config
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
SERVER_DOMAIN = os.getenv("SERVER_DOMAIN", "example.com")
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview-2024-10-01")

DEFAULT_PHONE_NUMBER = os.getenv(
    "DEFAULT_PHONE_NUMBER", "+13526656965"
)  # quick tests via /make-call

# =========================
# Example client profile
# =========================
SAMPLE_CLIENT_PROFILE: Dict[str, Any] = {
    "client_id": "CL-20481",
    "full_name": "Alexandra (Alex) Reyes",
    "dob_last4": "1992",
    "email": "alex.reyes@example.com",
    "phone": "+1-352-555-0138",
    "preferred_contact": "email",
    "availability_windows_et": [
        {"days": "Mon–Thu", "from": "13:00", "to": "17:30"},
        {"days": "Fri", "from": "09:00", "to": "12:00"},
    ],
    "matters": [
        {
            "matter_id": "MAT-AXR-102",
            "nickname": "Auto claim / Sunshine Ins.",
            "practice_area": "Insurance / Personal Injury",
            "responsible_attorney": "Jordan Kim, Esq.",
            "status": "Waiting on insurer’s settlement response",
            "key_dates": {"demand_sent": "2025-10-10", "insurer_response_due": "2025-10-28"},
            "open_questions": [
                "What if no response by the 10/28 deadline?",
                "Timeline for independent medical exam (IME), if any?",
            ],
            "documents_on_file": [
                "Demand_Packet_2025-10-10.pdf",
                "ER_Visit_Notes_2025-09-17.pdf",
                "Police_Report_2025-09-15.pdf",
            ],
        },
        {
            "matter_id": "MAT-AXR-207",
            "nickname": "Lease dispute w/ Pine Vista Apts",
            "practice_area": "Landlord/Tenant",
            "responsible_attorney": "Jordan Kim, Esq.",
            "status": "Negotiation over early termination fee",
            "key_dates": {
                "lease_end_requested": "2025-11-30",
                "landlord_counter_due": "2025-10-31",
            },
            "open_questions": [
                "Validity of early termination clause Section 14(b)",
                "Whether key hand-off can be in mid-November",
            ],
            "documents_on_file": ["Lease_2024-12-01.pdf", "Email_Thread_Landlord_2025-10-12.eml"],
        },
    ],
}

# =========================
# Lawgorithm system instructions + tool schema
# =========================
LAWGORITHM_INSTRUCTIONS = """You are Lawgorithm, an empathetic, concise assistant that helps a client follow up with their lawyer about ongoing matters. You triage questions, summarize context, capture next actions, and prepare a crisp, lawyer-ready note.

When the conversation starts:
1) Greet warmly and disclose: “I’m Lawgorithm, here to help organize your questions and prepare a message for your attorney. I’m not a lawyer and can’t give legal advice.”
2) Verify the client with TWO soft checks from profile context (e.g., last name + matter nickname OR preferred email). Then confirm which matter they’re calling about. If multiple matters exist, present a short numbered list (≤3 items).
3) Clarify the goal in one sentence: scheduling, case status, document request, billing, settlement offer, court date, or other.
4) Ask targeted questions to gather essentials:
   • Deadline or urgency window (e.g., “needs reply by Oct 28, 5pm ET”)
   • Specific questions for the lawyer (bulleted)
   • Any documents referenced (names/dates)
   • Preferred contact method & times
   • Consent to share the summarized note with the firm
5) Triage & flag URGENT if any of: imminent deadline (<48h), court/hearing within 7 days, threatened harm/safety, time-sensitive settlement/offer, or loss of rights.
6) Generate a short “Lawyer Handoff Summary” with:
   • Matter: <name / ID>
   • Client questions (bulleted)
   • Facts received (1–3 bullets; no speculation)
   • Deadlines/urgency
   • Requested next action (call, email, docs, meeting)
   • Client availability & preferred contact
   • Attachments referenced (names only)
   • Consent: yes/no
7) Read back a one-paragraph confirmation and invite corrections.
8) Use the function tool `save_client_followup` once essentials are captured.
9) Close with next steps and expected response method. Thank the client.

Tone: empathetic, professional, succinct. Avoid legal advice; say: “I’ll route this to your attorney for guidance.” Never invent dates/facts not in the profile or provided by the client.
"""

TOOLS_LEGAL = [
    {
        "type": "function",
        "name": "save_client_followup",
        "description": "Persist the client’s follow-up summary for the attorney handoff.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "matter_id": {"type": "string"},
                "matter_nickname": {"type": "string"},
                "responsible_attorney": {"type": "string"},
                "goal": {
                    "type": "string",
                    "enum": [
                        "schedule_call",
                        "case_status",
                        "document_request",
                        "billing",
                        "settlement_offer",
                        "court_date",
                        "other",
                    ],
                },
                "client_questions": {"type": "array", "items": {"type": "string"}},
                "facts_summary": {"type": "string"},
                "deadline_iso": {
                    "type": "string",
                    "description": "e.g., 2025-10-28T17:00:00-04:00",
                },
                "is_urgent": {"type": "boolean"},
                "requested_next_action": {"type": "string"},
                "preferred_contact": {
                    "type": "string",
                    "enum": ["email", "phone", "sms", "portal"],
                },
                "availability_windows_et": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "days": {"type": "string"},
                            "from": {"type": "string"},
                            "to": {"type": "string"},
                        },
                    },
                },
                "attachments_mentioned": {"type": "array", "items": {"type": "string"}},
                "consent_to_share_with_firm": {"type": "boolean"},
                "additional_notes": {"type": "string"},
            },
            "required": [
                "client_id",
                "matter_id",
                "goal",
                "client_questions",
                "preferred_contact",
                "consent_to_share_with_firm",
            ],
        },
    }
]

# =========================
# App + in-memory state
# =========================
app = FastAPI(title="Lawgorithm (Stable Realtime Bridge)")

followups: Dict[str, Any] = {}  # {call_sid: {"summary": {...}, "saved_at": "..."}}
active_profiles: Dict[str, Any] = {}  # {call_sid: client_profile}


# ---------- Simple pages ----------
@app.get("/")
async def root_index():
    return HTMLResponse(
        f"""
    <html><body style="font-family:system-ui;max-width:720px;margin:2rem auto">
      <h1>Lawgorithm</h1>
      <p>Automated check-ins for lawyer/case status via Twilio Media Streams ↔ OpenAI Realtime.</p>
      <ul>
        <li><a href="/healthz">/healthz</a> – health check</li>
        <li><a href="/make-call">/make-call</a> – start a call from your browser</li>
      </ul>
      <p><b>Note:</b> Set <code>SERVER_DOMAIN</code> to a public HTTPS host (e.g., ngrok).</p>
      <p>Current SERVER_DOMAIN: <code>{SERVER_DOMAIN}</code></p>
    </body></html>
    """
    )


@app.get("/call")
async def call_alias():
    return RedirectResponse(url="/make-call", status_code=status.HTTP_302_FOUND)


@app.get("/healthz")
async def health_check():
    return {
        "status": "ok",
        "service": "Lawgorithm",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------- Twilio webhooks ----------
@app.post("/voice")
async def voice_webhook(request: Request):
    """
    Twilio incoming call webhook -> returns TwiML that starts the media stream.
    IMPORTANT: Twilio must reach this over HTTPS on your public domain.
    """
    form = await request.form()
    caller = form.get("From", "Unknown")
    print(f"📞 Lawgorithm: Incoming call from: {caller}")
    vr = VoiceResponse()
    cx = Connect()

    # Use inbound_track only to avoid feedback/echo from both_tracks
    cx.stream(url=f"wss://{SERVER_DOMAIN}/twilio-media", track="inbound_track")
    vr.append(cx)
    return PlainTextResponse(str(vr), media_type="application/xml")


@app.post("/call-status")
async def call_status(request: Request):
    """Optional status callback."""
    form = await request.form()
    call_sid = form.get("CallSid")
    status_txt = form.get("CallStatus")
    print(f"📊 Call status: {status_txt} | SID: {call_sid}")
    return {"status": "ok"}


# ---------- Convenience: start an outbound call ----------
@app.get("/make-call")
async def make_call_get(to: str = None, clientName: str = None):
    try:
        return await _initiate_call(to, clientName, is_browser=True)
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>", status_code=500)

from fastapi.responses import Response

@app.options("/make-call")
async def options_make_call(request: Request):
    data = {}
    try:
        data = await request.json()
    except:
        pass
    to = data.get("to")
    client_name = data.get("clientName")
    return await _initiate_call(to, client_name, is_browser=False)

@app.post("/make-call")
async def make_call_post(request: Request):
    data = {}
    try:
        data = await request.json()
    except:
        pass
    to = data.get("to")
    client_name = data.get("clientName")
    return await _initiate_call(to, client_name, is_browser=False)


async def _initiate_call(to_number: str = None, client_name: str = None, is_browser: bool = False):
    if not to_number:
        to_number = DEFAULT_PHONE_NUMBER
    if not client_name:
        client_name = "Client"

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        msg = "Missing Twilio credentials. Check your .env."
        if is_browser:
            return HTMLResponse(f"<h2>Config Error</h2><pre>{msg}</pre>", status_code=500)
        return JSONResponse({"success": False, "error": msg}, status_code=500)

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"https://{SERVER_DOMAIN}/voice",
            status_callback=f"https://{SERVER_DOMAIN}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        print(f"✅ Outbound call initiated. SID={call.sid}")

        # seed profile for this call
        active_profiles[call.sid] = SAMPLE_CLIENT_PROFILE

        result = {
            "success": True,
            "callSid": call.sid,
            "to": to_number,
            "clientName": client_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if is_browser:
            return HTMLResponse(
                f"""
            <html><body style="font-family:system-ui;">
              <h1>✅ Lawgorithm Call Started</h1>
              <p><b>To:</b> {to_number}</p>
              <p><b>Client:</b> {client_name}</p>
              <p><b>Call SID:</b> {call.sid}</p>
              <p>Loaded example client profile for this call.</p>
              <a href="/make-call">Start another call</a>
            </body></html>"""
            )
        return JSONResponse(result)

    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        if is_browser:
            return HTMLResponse(f"<h2>Call Failed</h2><pre>{e}</pre>", status_code=500)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ---------- Media Stream bridge ----------
@app.websocket("/twilio-media")
async def twilio_media_stream(ws: WebSocket):
    """Twilio <-> OpenAI Realtime audio bridge (stable, buffered, inbound-only)."""
    await ws.accept()
    print("🔌 Lawgorithm: Twilio WebSocket connected")

    stream_sid = None
    call_sid = None
    openai_ws = None
    greet_sent = False
    connection_active = True  # Track if connection is still active

    twilio_packets = 0
    openai_packets = 0

    # Outbound audio buffer (OpenAI -> Twilio), flush ~every 60 ms
    audio_out_buffer = bytearray()
    last_flush_ts = time.time()
    FLUSH_EVERY_SEC = 0.06  # ~60ms @ 8kHz ulaw is ~480 bytes per 60ms

    async def _flush_audio_buffer(force: bool = False):
        nonlocal audio_out_buffer, last_flush_ts
        if force or (audio_out_buffer and (time.time() - last_flush_ts) >= FLUSH_EVERY_SEC):
            try:
                payload_b64 = base64.b64encode(bytes(audio_out_buffer)).decode("ascii")
                audio_out_buffer.clear()
                last_flush_ts = time.time()
                if stream_sid and connection_active and payload_b64:
                    await ws.send_json(
                        {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": payload_b64},
                        }
                    )
            except Exception as e:
                print(f"⚠️  Failed to flush audio buffer: {e}")

    try:
        print("🔗 Connecting to OpenAI Realtime...")
        openai_ws = await websockets.connect(
            f"wss://api.openai.com/v1/realtime?model={REALTIME_MODEL}",
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
        )
        print("✅ OpenAI Realtime connected")

        # Initial session config (set codecs + tools; metadata is attached later after Twilio start)
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": LAWGORITHM_INSTRUCTIONS,
                "voice": "shimmer",
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.6,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 700,
                },
                "tools": TOOLS_LEGAL,
                "temperature": 0.8,
                "max_response_output_tokens": "inf",
            },
        }
        await openai_ws.send(json.dumps(session_update))

        async def handle_openai():
            nonlocal openai_packets, call_sid, connection_active
            try:
                async for raw in openai_ws:
                    evt = json.loads(raw)
                    etype = evt.get("type")

                    if etype == "session.updated":
                        print("🧩 Session updated with Lawgorithm config")

                    elif etype == "response.audio.delta":
                        # Buffer deltas; flush on cadence for clean audio to Twilio
                        delta_b64 = evt.get("delta")
                        if delta_b64 and connection_active:
                            try:
                                chunk = base64.b64decode(delta_b64)
                                audio_out_buffer.extend(chunk)
                                openai_packets += 1
                                await _flush_audio_buffer(force=False)
                            except Exception as send_err:
                                print(f"⚠️  audio forward error: {send_err}")
                                connection_active = False
                                break

                    elif etype == "response.audio_transcript.done":
                        print(f"🤖 AI says: {evt.get('transcript','')}")

                    elif etype == "conversation.item.input_audio_transcription.completed":
                        print(f"🗣️  Client said: {evt.get('transcript','')}")

                    elif etype == "response.function_call_arguments.done":
                        if evt.get("name") == "save_client_followup":
                            try:
                                args = json.loads(evt.get("arguments") or "{}")
                            except json.JSONDecodeError:
                                args = {}
                            print(f"💾 save_client_followup: {args}")

                            if call_sid:
                                followups.setdefault(call_sid, {})
                                followups[call_sid]["summary"] = args
                                followups[call_sid]["saved_at"] = datetime.now(
                                    timezone.utc
                                ).isoformat()

                            # Acknowledge tool output
                            await openai_ws.send(
                                json.dumps(
                                    {
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": evt.get("call_id"),
                                            "output": json.dumps({"success": True}),
                                        },
                                    }
                                )
                            )
                            await openai_ws.send(json.dumps({"type": "response.create"}))
            except Exception as e:
                print(f"❌ OpenAI handler error: {e}")
                connection_active = False

        async def handle_twilio():
            nonlocal stream_sid, call_sid, twilio_packets, greet_sent, openai_ws, connection_active
            try:
                async for text in ws.iter_text():
                    msg = json.loads(text)
                    ev = msg.get("event")

                    if ev == "start":
                        stream_sid = msg["start"]["streamSid"]
                        call_sid = msg["start"]["callSid"]
                        print(f"🎬 Media stream started | Call SID: {call_sid}")

                        # Attach client profile as session metadata now that we have call_sid
                        client_profile = active_profiles.get(call_sid) or SAMPLE_CLIENT_PROFILE
                        await openai_ws.send(
                            json.dumps(
                                {
                                    "type": "session.update",
                                    "session": {"metadata": {"client_profile": client_profile}},
                                }
                            )
                        )
                        print("🧾 Attached client_profile metadata to session")

                        # Trigger greeting exactly once (now streamSid exists)
                        if not greet_sent:
                            greet_sent = True
                            await openai_ws.send(
                                json.dumps(
                                    {
                                        "type": "response.create",
                                        "response": {
                                            "modalities": ["text", "audio"],
                                            "instructions": (
                                                "Start the follow-up. Greet, disclose not-legal-advice, "
                                                "verify the client with two soft checks, and list matters to choose from."
                                            ),
                                        },
                                    }
                                )
                            )

                    elif ev == "media":
                        # Incoming 8k ulaw audio from Twilio → forward to OpenAI
                        twilio_packets += 1
                        await openai_ws.send(
                            json.dumps(
                                {
                                    "type": "input_audio_buffer.append",
                                    "audio": msg["media"]["payload"],
                                }
                            )
                        )

                    elif ev == "mark":
                        # can be ignored or used for latency metrics
                        pass

                    elif ev == "stop":
                        print(f"⏹️  Stream stopped. Packets in: {twilio_packets}")
                        connection_active = False
                        break

            except Exception as e:
                print(f"❌ Twilio WS handler error: {e}")
                connection_active = False

        async def _pinger():
            """Optional heartbeat + periodic forced flush for audio buffer."""
            nonlocal connection_active
            try:
                while connection_active:
                    await asyncio.sleep(0.2)
                    await _flush_audio_buffer(force=False)
                # final flush on exit
                await _flush_audio_buffer(force=True)
            except Exception:
                pass

        await asyncio.gather(handle_openai(), handle_twilio(), _pinger())

    except Exception as e:
        print(f"❌ WebSocket bridge error: {e}")

    finally:
        try:
            # final flush if anything remains
            await _flush_audio_buffer(force=True)
        except Exception:
            pass

        print("🔌 Closing connections")
        if openai_ws:
            try:
                await openai_ws.close()
            except Exception as e:
                print(f"⚠️  Error closing OpenAI WebSocket: {e}")
        try:
            await ws.close()
        except Exception as e:
            print(f"⚠️  Error closing Twilio WebSocket: {e}")


# ---------- Fetch the saved follow-up by Call SID ----------
@app.get("/followup")
async def get_followup(callSid: str):
    data = followups.get(callSid)
    if not data:
        return JSONResponse({"success": False, "error": "Not found"}, status_code=404)
    return JSONResponse({"success": True, "callSid": callSid, "data": data})


# ---------- Local dev entry ----------
if __name__ == "__main__":
    import uvicorn

    print("🏛️  Starting Lawgorithm Call Service...")
    print(f"📞 Default phone number: {DEFAULT_PHONE_NUMBER}")
    print(f"🌐 SERVER_DOMAIN: {SERVER_DOMAIN}")
    print(f"🤖 REALTIME_MODEL: {REALTIME_MODEL}")
    print("-" * 60)

    print("🔧 Configuration Check:")
    print(f"   OPENAI_API_KEY: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"   TWILIO_ACCOUNT_SID: {'✅ Set' if TWILIO_ACCOUNT_SID else '❌ Missing'}")
    print(f"   TWILIO_AUTH_TOKEN: {'✅ Set' if TWILIO_AUTH_TOKEN else '❌ Missing'}")
    print(f"   TWILIO_PHONE_NUMBER: {TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else '❌ Missing'}")
    print("-" * 60)

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, OPENAI_API_KEY]):
        print("⚠️  WARNING: Missing required environment variables; calls will fail.")

    uvicorn.run(app, host="0.0.0.0", port=8000)
