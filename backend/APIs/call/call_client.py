"""
Clinovance Platform - Integrated Application
Serves React frontend (Flask) + CareTrackr call service (FastAPI) on same port
"""

import os
import json
import asyncio
import websockets
import httpx
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from starlette.applications import Starlette
from starlette.routing import Host, Mount, Route, WebSocketRoute
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.responses import RedirectResponse, Response as StarletteResponse

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect

load_dotenv()

# -------------------------
# Configuration
# -------------------------
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
SERVER_DOMAIN = os.getenv('SERVER_DOMAIN', 'clinovance.com')
PRIMARY_DOMAIN = os.environ.get('PRIMARY_DOMAIN', 'clinovance.com')
DEFAULT_PHONE_NUMBER = '+13526656965'
PATIENT_DATA_PATH = Path('LLM/patient_data.json')

# Store patient responses and transcripts
patient_responses = {}

# CareTrackr instructions
CARETRACKR_INSTRUCTIONS = """You are CareTrackr, an automated post-surgery follow-up assistant. 

When the conversation starts, immediately greet the patient and follow this flow:

1. Say: "Hello, I am CareTrackr, a service that collects feedback and provides information regarding any symptoms to the physician to help schedule follow-ups if needed."

2. Ask: "Did you have an appendectomy 2 days ago? Please answer yes or no."
   - If NO: Say "I apologize for the confusion. This call is for post-appendectomy follow-up. Have a good day." Then end.
   - If YES: Continue to step 3.

3. Say: "The normal symptoms that you should be experiencing are mild pain and discomfort around the surgical site, fatigue, drowsiness, and mild swelling of the stomach."

4. Ask: "Are you experiencing any issues after your surgery? Please describe any symptoms that concern you."
   - Listen carefully and ask clarifying questions about severity, location, or duration
   - Flag urgent symptoms: severe pain, high fever (over 101°F), excessive bleeding, pus, difficulty breathing

5. Say: "Thank you for this information. I have recorded your responses and will forward them to your physician. They will contact you if a follow-up appointment is needed. Is there anything else you'd like to add?"

6. Say: "Thank you for your time. Take care and get well soon. Goodbye."

Be warm, empathetic, professional, and concise. Use the save_patient_response function to record answers."""

# -------------------------
# Helper Functions
# -------------------------

def load_patient_data():
    """Load patient data from JSON file"""
    try:
        if PATIENT_DATA_PATH.exists():
            with open(PATIENT_DATA_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f'⚠️  Error loading patient data: {e}')
    return {}

def save_patient_data(data):
    """Save patient data to JSON file"""
    try:
        # Ensure directory exists
        PATIENT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(PATIENT_DATA_PATH, 'w') as f:
            json.dump(data, indent=2, fp=f)
        print(f'✅ Patient data saved to {PATIENT_DATA_PATH}')
        return True
    except Exception as e:
        print(f'❌ Error saving patient data: {e}')
        return False

def update_patient_symptoms(patient_id, symptoms_data, transcript):
    """Update patient symptoms in patient_data.json"""
    try:
        patient_data = load_patient_data()
        
        # Find or create patient record
        if patient_id not in patient_data:
            patient_data[patient_id] = {
                'name': patient_id,
                'phone': '',
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        
        # Update current_symptoms
        patient_data[patient_id]['current_symptoms'] = {
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'symptoms': symptoms_data.get('symptoms', ''),
            'severity': symptoms_data.get('severity', 'unknown'),
            'needs_followup': symptoms_data.get('needs_followup', False),
            'additional_notes': symptoms_data.get('additional_notes', ''),
            'full_transcript': transcript
        }
        
        patient_data[patient_id]['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        save_patient_data(patient_data)
        print(f'✅ Updated symptoms for patient {patient_id}')
        return True
    except Exception as e:
        print(f'❌ Error updating patient symptoms: {e}')
        import traceback
        traceback.print_exc()
        return False

# -------------------------
# Flask app (serves frontend)
# -------------------------
flask_app = Flask(
    __name__,
    static_folder="../frontend/build",
    static_url_path=""
)
CORS(flask_app)

@flask_app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})

@flask_app.route("/api/data", methods=["POST"])
def post_data():
    data = request.get_json()
    return jsonify({"received": data, "status": "success"})

@flask_app.route("/api/call/<phone_number>", methods=["POST"])
def flask_make_call(phone_number):
    """
    Flask endpoint to initiate a call
    POST /api/call/+1234567890
    Optional JSON body: {"patientId": "John Doe"}
    """
    try:
        data = request.get_json() if request.is_json else {}
        patient_id = data.get('patientId', 'Patient')
        
        # Validate phone number format
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        print(f'📞 Flask: Initiating call to {phone_number} | Patient: {patient_id}')
        
        # Check credentials
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            return jsonify({
                'success': False,
                'error': 'Missing Twilio credentials. Check environment variables.'
            }), 500
        
        # Create Twilio client and make call
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f'https://{SERVER_DOMAIN}/voice',
            status_callback=f'https://{SERVER_DOMAIN}/call-status'
        )
        
        # Initialize tracking for this call
        patient_responses[call.sid] = {
            'patient_id': patient_id,
            'phone': phone_number,
            'call_sid': call.sid,
            'transcript': [],
            'responses': {},
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify({
            'success': True,
            'callSid': call.sid,
            'to': phone_number,
            'patientId': patient_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        print(f'❌ Error making call: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flask_app.route("/api/initiate-call", methods=["POST"])
def initiate_call():
    """
    Initiate a call using the internal API endpoint
    POST /api/initiate-call
    Body: {"patientId": "P001", "patientName": "John Doe", "phoneNumber": "+13526656965"}
    """
    try:
        data = request.get_json()
        patient_id = data.get('patientId', 'Unknown')
        patient_name = data.get('patientName', 'Patient')
        phone_number = data.get('phoneNumber', DEFAULT_PHONE_NUMBER)
        
        # Validate phone number
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        print(f'📞 Initiating call for {patient_name} ({patient_id}) at {phone_number}')
        
        # Use the internal call API endpoint
        # Make internal HTTP request to the call endpoint
        call_data = {
            'patientId': patient_id,
            'patientName': patient_name
        }
        
        # Call the flask_make_call function directly
        with flask_app.test_request_context(
            f'/api/call/{phone_number}',
            method='POST',
            json=call_data
        ):
            response = flask_make_call(phone_number)
            response_data = json.loads(response.get_data(as_text=True))

            from LLM.process_patient import run_risk_assessment

            run_risk_assessment("LLM/patient_data.json")
            
            if response_data.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Call initiated successfully',
                    'patient_id': patient_id,
                    'patient_name': patient_name,
                    'call_sid': response_data.get('callSid')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': response_data.get('error', 'Unknown error')
                }), 500
        
    except Exception as e:
        print(f'❌ Error in initiate_call: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flask_app.route("/")
def serve_index():
    return send_from_directory(flask_app.static_folder, "index.html")

@flask_app.errorhandler(404)
def not_found(e):
    # SPA fallback
    return send_from_directory(flask_app.static_folder, "index.html")

# Wrap Flask (WSGI) so ASGI servers can run it
flask_asgi = WSGIMiddleware(flask_app)

# -------------------------
# CareTrackr app (FastAPI)
# -------------------------
caretrackr = FastAPI()

@caretrackr.get('/healthz')
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'service': 'CareTrackr',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@caretrackr.post('/voice')
async def voice_webhook(request: Request):
    """Twilio incoming call webhook"""
    form_data = await request.form()
    caller = form_data.get('From', 'Unknown')
    print(f'📞 CareTrackr: Incoming call from: {caller}')
    
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f'wss://{SERVER_DOMAIN}/twilio-media')
    response.append(connect)
    
    return PlainTextResponse(str(response), media_type='application/xml')

@caretrackr.post('/call-status')
async def call_status(request: Request):
    """Handle Twilio call status callbacks"""
    form_data = await request.form()
    call_sid = form_data.get('CallSid', 'Unknown')
    call_status = form_data.get('CallStatus', 'Unknown')
    print(f'📊 Call {call_sid}: {call_status}')
    
    # If call completed, process and save transcript
    if call_status == 'completed' and call_sid in patient_responses:
        call_data = patient_responses[call_sid]
        patient_id = call_data.get('patient_id', 'Unknown')
        transcript = '\n'.join(call_data.get('transcript', []))
        symptoms_data = call_data.get('responses', {})
        
        print(f'📝 Call completed. Processing transcript for {patient_id}')
        update_patient_symptoms(patient_id, symptoms_data, transcript)
    
    return PlainTextResponse('OK')

@caretrackr.get('/call/{phone_number}')
@caretrackr.post('/call/{phone_number}')
async def make_call_simple(phone_number: str, request: Request):
    """
    Simple endpoint to make a call with just a phone number
    GET or POST /call/+1234567890
    Optional query params: ?patientId=John
    Optional JSON body: {"patientId": "John Doe"}
    """
    patient_id = request.query_params.get('patientId')
    
    if not patient_id and request.method == 'POST':
        try:
            data = await request.json()
            patient_id = data.get('patientId')
        except:
            pass
    
    if not patient_id:
        patient_id = 'Patient'
    
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    return await _initiate_call(phone_number, patient_id, is_browser=False)

@caretrackr.get('/make-call')
async def make_call_get(to: str = None, patientId: str = None):
    """
    Make a call via GET request (browser friendly)
    Visit: http://localhost:8000/make-call
    Or: http://localhost:8000/make-call?to=+1234567890&patientId=John
    """
    return await _initiate_call(to, patientId, is_browser=True)

@caretrackr.post('/make-call')
async def make_call_post(request: Request):
    """Make a call via POST request with JSON body"""
    try:
        data = await request.json()
    except:
        data = {}
    
    to_number = data.get('to')
    patient_id = data.get('patientId')
    
    return await _initiate_call(to_number, patient_id, is_browser=False)

async def _initiate_call(to_number: str = None, patient_id: str = None, is_browser: bool = False):
    """Internal function to initiate a call"""
    
    if not to_number:
        to_number = DEFAULT_PHONE_NUMBER
    
    if not patient_id:
        patient_id = 'Test Patient'
    
    if not to_number.startswith('+'):
        to_number = '+' + to_number
    
    print(f'📞 CareTrackr: Initiating call to {to_number} | Patient: {patient_id}')
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        error_msg = "Missing Twilio credentials. Check environment variables."
        if is_browser:
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head><title>Configuration Error</title></head>
                <body style="font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #dc2626;">⚠️ Configuration Error</h1>
                    <p>{error_msg}</p>
                </body>
                </html>
            """, status_code=500)
        else:
            return JSONResponse(content={'success': False, 'error': error_msg}, status_code=500)
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f'https://{SERVER_DOMAIN}/voice',
            status_callback=f'https://{SERVER_DOMAIN}/call-status'
        )
        
        # Initialize tracking for this call
        patient_responses[call.sid] = {
            'patient_id': patient_id,
            'phone': to_number,
            'call_sid': call.sid,
            'transcript': [],
            'responses': {},
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = {
            'success': True,
            'callSid': call.sid,
            'to': to_number,
            'patientId': patient_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if is_browser:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CareTrackr - Call Initiated</title>
                <style>
                    body {{
                        font-family: system-ui, -apple-system, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .card {{
                        background: white;
                        border-radius: 12px;
                        padding: 30px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #059669;
                        margin: 0 0 20px 0;
                    }}
                    .info {{
                        background: #f0fdf4;
                        border-left: 4px solid #059669;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 4px;
                    }}
                    .detail {{
                        margin: 10px 0;
                        color: #374151;
                    }}
                    .label {{
                        font-weight: 600;
                        color: #059669;
                    }}
                    .button {{
                        display: inline-block;
                        background: #059669;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 8px;
                        text-decoration: none;
                        margin-top: 20px;
                    }}
                    .button:hover {{
                        background: #047857;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✅ Call Initiated Successfully</h1>
                    <div class="info">
                        <div class="detail"><span class="label">Call SID:</span> {call.sid}</div>
                        <div class="detail"><span class="label">Calling:</span> {to_number}</div>
                        <div class="detail"><span class="label">Patient:</span> {patient_id}</div>
                        <div class="detail"><span class="label">Status:</span> {call.status}</div>
                    </div>
                    <p>📱 The call is being placed now. The patient should receive a call shortly.</p>
                    <p>📝 Transcript will be saved to LLM/patient_data.json</p>
                    <a href="/make-call" class="button">Make Another Call</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html)
        else:
            return JSONResponse(content=result)
        
    except Exception as e:
        error_msg = str(e)
        print(f'❌ Error making call: {error_msg}')
        import traceback
        traceback.print_exc()
        
        if is_browser:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CareTrackr - Error</title>
                <style>
                    body {{
                        font-family: system-ui, -apple-system, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .card {{
                        background: white;
                        border-radius: 12px;
                        padding: 30px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #dc2626;
                        margin: 0 0 20px 0;
                    }}
                    .error {{
                        background: #fef2f2;
                        border-left: 4px solid #dc2626;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 4px;
                        color: #991b1b;
                    }}
                    .button {{
                        display: inline-block;
                        background: #dc2626;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 8px;
                        text-decoration: none;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>❌ Error Making Call</h1>
                    <div class="error">
                        <strong>Error:</strong> {error_msg}
                    </div>
                    <a href="/make-call" class="button">Try Again</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html, status_code=500)
        else:
            return JSONResponse(
                content={'success': False, 'error': error_msg},
                status_code=500
            )

@caretrackr.websocket('/twilio-media')
async def twilio_media_stream(websocket: WebSocket):
    """Handle Twilio media stream and connect to OpenAI Realtime API"""
    await websocket.accept()
    print('🔌 Twilio WebSocket connected')
    
    if not OPENAI_API_KEY:
        print('❌ ERROR: OPENAI_API_KEY not set!')
        await websocket.close()
        return
    
    stream_sid = None
    call_sid = None
    openai_ws = None
    twilio_packet_count = 0
    
    try:
        print('🤖 Connecting to OpenAI Realtime API...')
        openai_ws = await websockets.connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
            additional_headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'OpenAI-Beta': 'realtime=v1'
            }
        )
        print('✅ Connected to OpenAI!')
        
        print('⚙️  Configuring OpenAI session...')
        await openai_ws.send(json.dumps({
            'type': 'session.update',
            'session': {
                'modalities': ['text', 'audio'],
                'instructions': CARETRACKR_INSTRUCTIONS,
                'voice': 'sage',
                'input_audio_format': 'g711_ulaw',
                'output_audio_format': 'g711_ulaw',
                'input_audio_transcription': {'model': 'whisper-1'},
                'turn_detection': {'type': 'server_vad'},
                'tools': [
                    {
                        'type': 'function',
                        'name': 'save_patient_response',
                        'description': 'Save patient responses from the follow-up call',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'had_surgery': {'type': 'boolean'},
                                'symptoms': {'type': 'string'},
                                'severity': {'type': 'string'},
                                'needs_followup': {'type': 'boolean'},
                                'additional_notes': {'type': 'string'}
                            }
                        }
                    }
                ],
                'temperature': 0.8
            }
        }))
        print('✅ Session configured')
        
        async def handle_openai():
            nonlocal stream_sid, call_sid
            
            try:
                async for message in openai_ws:
                    try:
                        event = json.loads(message)
                        event_type = event.get('type')
                        
                        if event_type == 'session.updated':
                            print('✅ OpenAI session confirmed')
                        
                        elif event_type == 'error':
                            print(f'❌ OpenAI error: {event}')
                        
                        elif event_type == 'response.audio.delta':
                            audio_payload = event['delta']
                            await websocket.send_json({
                                'event': 'media',
                                'streamSid': stream_sid,
                                'media': {'payload': audio_payload}
                            })
                        
                        elif event_type == 'response.audio_transcript.delta':
                            delta_text = event.get("delta", "")
                            print(f'🗣️  AI: {delta_text}', end='', flush=True)
                            # Save to transcript
                            if call_sid and call_sid in patient_responses:
                                if patient_responses[call_sid]['transcript']:
                                    if not patient_responses[call_sid]['transcript'][-1].startswith('AI: '):
                                        patient_responses[call_sid]['transcript'].append(f'AI: {delta_text}')
                                    else:
                                        patient_responses[call_sid]['transcript'][-1] += delta_text
                                else:
                                    patient_responses[call_sid]['transcript'].append(f'AI: {delta_text}')
                        
                        elif event_type == 'response.audio_transcript.done':
                            print()  # New line after transcript
                        
                        elif event_type == 'conversation.item.input_audio_transcription.completed':
                            transcript_text = event.get('transcript', '')
                            if transcript_text and call_sid and call_sid in patient_responses:
                                patient_responses[call_sid]['transcript'].append(f'Patient: {transcript_text}')
                                print(f'👤 Patient: {transcript_text}')
                        
                        elif event_type == 'input_audio_buffer.speech_started':
                            print('👂 User started speaking')
                        
                        elif event_type == 'input_audio_buffer.speech_stopped':
                            print('🤐 User stopped speaking')
                        
                        elif event_type == 'response.function_call_arguments.done':
                            if event.get('name') == 'save_patient_response':
                                args = json.loads(event.get('arguments', '{}'))
                                print(f'💾 Saving: {args}')
                                
                                if call_sid:
                                    if call_sid not in patient_responses:
                                        patient_responses[call_sid] = {'responses': {}}
                                    patient_responses[call_sid]['responses'] = args
                                
                                await openai_ws.send(json.dumps({
                                    'type': 'conversation.item.create',
                                    'item': {
                                        'type': 'function_call_output',
                                        'call_id': event.get('call_id'),
                                        'output': json.dumps({'success': True})
                                    }
                                }))
                                await openai_ws.send(json.dumps({'type': 'response.create'}))
                    
                    except json.JSONDecodeError as e:
                        print(f'❌ JSON decode error: {str(e)}')
                    except Exception as e:
                        print(f'❌ OpenAI message error: {str(e)}')
            except Exception as e:
                print(f'❌ OpenAI handler error: {str(e)}')
        
        async def handle_twilio():
            nonlocal stream_sid, call_sid, twilio_packet_count
            
            try:
                async for message in websocket.iter_text():
                    try:
                        msg = json.loads(message)
                        event = msg.get('event')
                        
                        if event == 'start':
                            stream_sid = msg['start']['streamSid']
                            call_sid = msg['start']['callSid']
                            print(f'🎬 Stream started: {call_sid}')
                            
                            # Initialize if not already done
                            if call_sid not in patient_responses:
                                patient_responses[call_sid] = {
                                    'patient_id': 'Unknown',
                                    'transcript': [],
                                    'responses': {},
                                    'started_at': datetime.now(timezone.utc).isoformat()
                                }
                        
                        elif event == 'media':
                            twilio_packet_count += 1
                            if twilio_packet_count % 100 == 0:
                                print(f'📦 Received {twilio_packet_count} audio packets')
                            
                            await openai_ws.send(json.dumps({
                                'type': 'input_audio_buffer.append',
                                'audio': msg['media']['payload']
                            }))
                        
                        elif event == 'stop':
                            print(f'⏹️  Stream stopped. Packets: {twilio_packet_count}')
                            
                            # Save transcript when call ends
                            if call_sid and call_sid in patient_responses:
                                call_data = patient_responses[call_sid]
                                patient_id = call_data.get('patient_id', 'Unknown')
                                transcript = '\n'.join(call_data.get('transcript', []))
                                symptoms_data = call_data.get('responses', {})
                                
                                print(f'📝 Saving transcript for {patient_id}')
                                update_patient_symptoms(patient_id, symptoms_data, transcript)
                    
                    except json.JSONDecodeError as e:
                        print(f'❌ Twilio JSON error: {str(e)}')
                    except Exception as e:
                        print(f'❌ Twilio message error: {str(e)}')
            except Exception as e:
                print(f'❌ Twilio handler error: {str(e)}')
        
        await asyncio.gather(handle_openai(), handle_twilio())
    
    except websockets.exceptions.WebSocketException as e:
        print(f'❌ WebSocket connection error: {str(e)}')
    except Exception as e:
        print(f'❌ WebSocket error: {str(e)}')
        import traceback
        traceback.print_exc()
    
    finally:
        print('🔌 Closing connections')
        if openai_ws:
            try:
                await openai_ws.close()
            except:
                pass

# -------------------------
# Unified Router (Starlette)
# -------------------------

caretrackr_mount = Mount("/caretrackr", app=caretrackr)

async def redirect_call(request):
    phone = request.path_params.get('phone', '')
    return RedirectResponse(url=f'/caretrackr/call/{phone}')

from starlette.applications import Starlette as SubStarlette
flask_container = SubStarlette(routes=[
    Route('/call/{phone:path}', redirect_call),
    Mount("/", app=flask_asgi)
])

async def root_voice_webhook(request):
    """Root-level voice webhook for Twilio"""
    form_data = await request.form()
    caller = form_data.get('From', 'Unknown')
    print(f'📞 Root: Incoming call from: {caller}')
    
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f'wss://{SERVER_DOMAIN}/twilio-media')
    response.append(connect)
    
    return StarletteResponse(content=str(response), media_type='application/xml')

async def root_call_status(request):
    """Root-level call status callback for Twilio"""
    form_data = await request.form()
    call_sid = form_data.get('CallSid', 'Unknown')
    call_status = form_data.get('CallStatus', 'Unknown')
    print(f'📊 Root: Call {call_sid}: {call_status}')
    
    # Process transcript on call completion
    if call_status == 'completed' and call_sid in patient_responses:
        call_data = patient_responses[call_sid]
        patient_id = call_data.get('patient_id', 'Unknown')
        transcript = '\n'.join(call_data.get('transcript', []))
        symptoms_data = call_data.get('responses', {})
        
        print(f'📝 Call completed. Processing transcript for {patient_id}')
        update_patient_symptoms(patient_id, symptoms_data, transcript)
    
    return StarletteResponse(content='OK', media_type='text/plain')

async def root_twilio_media(websocket):
    """Root-level WebSocket endpoint"""
    print('📞 Root WebSocket: Forwarding to CareTrackr handler')
    await twilio_media_stream(websocket)

local_routes = [
    Route('/voice', root_voice_webhook, methods=['POST']),
    Route('/call-status', root_call_status, methods=['POST']),
    WebSocketRoute('/twilio-media', root_twilio_media),
    caretrackr_mount,
    Mount("/", app=flask_container),
]

production_routes = [
    Host(f"call.{PRIMARY_DOMAIN}", app=caretrackr),
    Host(f"www.{PRIMARY_DOMAIN}", app=flask_container),
    Host(PRIMARY_DOMAIN, app=flask_container),
]

USE_LOCAL_ROUTING = os.getenv('USE_LOCAL_ROUTING', 'true').lower() == 'true'
routes = local_routes if USE_LOCAL_ROUTING else production_routes

app = Starlette(routes=routes)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🏥 CARETRACKR + FLASK INTEGRATED SERVER")
    print("=" * 70)
    
    if USE_LOCAL_ROUTING:
        print("🔧 MODE: Local Development (Path-based routing)")
        print(f"🌐 Server: http://localhost:8000")
        print()
        print("📍 Available endpoints:")
        print("  ┌─ Flask (React App)")
        print("  │  ├─ http://localhost:8000/                        [GET]")
        print("  │  ├─ http://localhost:8000/api/hello               [GET]")
        print("  │  ├─ http://localhost:8000/api/call/{phonenumber}  [POST]")
        print("  │  └─ http://localhost:8000/api/initiate-call       [POST] ⭐")
        print("  │")
        print("  ├─ Quick Access (Redirects)")
        print("  │  └─ http://localhost:8000/call/{phonenumber}      [GET] → /caretrackr/call/...")
        print("  │")
        print("  ├─ Twilio Webhooks (Root Level)")
        print("  │  ├─ http://localhost:8000/voice                   [POST] 🔗")
        print("  │  ├─ http://localhost:8000/call-status             [POST] 🔗")
        print("  │  └─ ws://localhost:8000/twilio-media              [WS] 🔗")
        print("  │")
        print("  └─ CareTrackr (Call Service)")
        print("     ├─ http://localhost:8000/caretrackr/call/+13526656965      [GET/POST] ✨")
        print("     ├─ http://localhost:8000/caretrackr/make-call              [GET/POST]")
        print("     └─ http://localhost:8000/caretrackr/healthz                [GET]")
        print()
        print("💡 TIP: Visit http://localhost:8000/call/+13526656965")
        print("📝 TIP: Transcripts saved to LLM/patient_data.json")
    else:
        print("🚀 MODE: Production (Host-based routing)")
        print(f"📞 CareTrackr: call.{PRIMARY_DOMAIN}:8000")
        print(f"🌐 Flask App: www.{PRIMARY_DOMAIN}:8000")
    
    print()
    print(f"📱 Default test number: {DEFAULT_PHONE_NUMBER}")
    print(f"🌍 SERVER_DOMAIN: {SERVER_DOMAIN}")
    print(f"📁 Patient data: {PATIENT_DATA_PATH}")
    print("-" * 70)
    print("🔧 Configuration Check:")
    print(f"   OPENAI_API_KEY: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"   TWILIO_ACCOUNT_SID: {'✅ Set' if TWILIO_ACCOUNT_SID else '❌ Missing'}")
    print(f"   TWILIO_AUTH_TOKEN: {'✅ Set' if TWILIO_AUTH_TOKEN else '❌ Missing'}")
    print(f"   TWILIO_PHONE_NUMBER: {TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else '❌ Missing'}")
    print("-" * 70)
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("⚠️  WARNING: Some Twilio credentials are missing!")
        print("   Calls will fail without proper Twilio configuration")
    
    print()
    print("✅ Server starting on http://localhost:8000")
    print("=" * 70)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)