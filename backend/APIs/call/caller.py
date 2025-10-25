"""
CareTrackr Call Service
Handles automated post-surgery follow-up calls
"""

import os
import json
import asyncio
import websockets
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
SERVER_DOMAIN = os.getenv('SERVER_DOMAIN', 'clinovance.com')

# Default phone number for testing
DEFAULT_PHONE_NUMBER = '+13526656965'

# Store patient responses
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

# Create FastAPI app
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

@caretrackr.get('/make-call')
async def make_call_get(to: str = None, patientId: str = None):
    """
    Make a call via GET request (browser friendly)
    Visit: http://localhost:8000/make-call
    Or: http://localhost:8000/make-call?to=+1234567890&patientId=John
    """
    print(f"GET /make-call - to={to}, patientId={patientId}")
    try:
        return await _initiate_call(to, patientId, is_browser=True)
    except Exception as e:
        print(f"❌ Error in make_call_get: {str(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <pre>{str(e)}</pre>
            </body>
            </html>
        """, status_code=500)

@caretrackr.post('/make-call')
async def make_call_post(request: Request):
    """
    Make a call via POST request with JSON body
    """
    try:
        data = await request.json()
    except:
        data = {}
    
    to_number = data.get('to')
    patient_id = data.get('patientId')
    
    return await _initiate_call(to_number, patient_id, is_browser=False)

async def _initiate_call(to_number: str = None, patient_id: str = None, is_browser: bool = False):
    """Internal function to initiate a call"""
    
    # Use default number if none provided
    if not to_number:
        to_number = DEFAULT_PHONE_NUMBER
    
    if not patient_id:
        patient_id = 'Test Patient'
    
    print(f'📞 CareTrackr: Initiating call to {to_number} | Patient: {patient_id}')
    
    # Check credentials first
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        error_msg = "Missing Twilio credentials. Please check your .env file."
        print(f'❌ {error_msg}')
        
        if is_browser:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CareTrackr - Configuration Error</title>
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
                    .code {{
                        background: #f3f4f6;
                        padding: 10px;
                        border-radius: 4px;
                        font-family: monospace;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>⚙️ Configuration Error</h1>
                    <div class="error">
                        <strong>Missing Twilio Credentials</strong>
                    </div>
                    <p>Please create a <code>.env</code> file in the backend directory with:</p>
                    <div class="code">
TWILIO_ACCOUNT_SID=ACxxxxxxxxx<br>
TWILIO_AUTH_TOKEN=your_token<br>
TWILIO_PHONE_NUMBER=+1234567890<br>
OPENAI_API_KEY=sk-proj-xxx<br>
SERVER_DOMAIN=localhost:8000
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html, status_code=500)
        else:
            return JSONResponse(content={'success': False, 'error': error_msg}, status_code=500)
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f'https://{SERVER_DOMAIN}/voice',
            status_callback=f'https://{SERVER_DOMAIN}/call-status',
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        print(f'✅ Call initiated - SID: {call.sid}')
        
        if patient_id:
            patient_responses[call.sid] = {
                'patientId': patient_id,
                'responses': {}
            }
        
        result = {
            'success': True,
            'callSid': call.sid,
            'to': to_number,
            'patientId': patient_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Return HTML for browser, JSON for API
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
                        color: #1f2937;
                    }}
                    .button {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: #059669;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
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
                        <div class="detail">
                            <span class="label">📞 Calling:</span> {to_number}
                        </div>
                        <div class="detail">
                            <span class="label">👤 Patient:</span> {patient_id}
                        </div>
                        <div class="detail">
                            <span class="label">🆔 Call SID:</span> {call.sid}
                        </div>
                        <div class="detail">
                            <span class="label">⏰ Time:</span> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </div>
                    </div>
                    <p>Your phone should ring shortly! 📱</p>
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
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: #059669;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
                    }}
                    code {{
                        background: #f3f4f6;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: monospace;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>❌ Call Failed</h1>
                    <div class="error">
                        <strong>Error:</strong> {error_msg}
                    </div>
                    <p>Please check:</p>
                    <ul>
                        <li>Your Twilio credentials are correct</li>
                        <li>Your Twilio phone number is verified</li>
                        <li>The destination number is valid</li>
                        <li>Your <code>.env</code> file is properly configured</li>
                    </ul>
                    <a href="/make-call" class="button">Try Again</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html, status_code=500)
        else:
            return JSONResponse(content={'success': False, 'error': error_msg}, status_code=500)

@caretrackr.post('/call-status')
async def call_status(request: Request):
    """Receive call status updates"""
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    status = form_data.get('CallStatus')
    print(f'📊 Call status: {status} | SID: {call_sid}')
    return {'status': 'ok'}

@caretrackr.websocket('/twilio-media')
async def twilio_media_stream(websocket: WebSocket):
    """Handle Twilio Media Stream WebSocket"""
    await websocket.accept()
    print('🔌 CareTrackr: Twilio WebSocket connected')
    
    stream_sid = None
    call_sid = None
    openai_ws = None
    conversation_log = []
    has_triggered_greeting = False
    
    twilio_packet_count = 0
    openai_packet_count = 0
    
    try:
        print('🔗 Connecting to OpenAI Realtime API...')
        
        openai_ws = await websockets.connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
            additional_headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'OpenAI-Beta': 'realtime=v1'
            }
        )
        
        print('✅ OpenAI WebSocket OPEN')
        
        # Session configuration
        session_config = {
            'type': 'session.update',
            'session': {
                'modalities': ['text', 'audio'],
                'instructions': CARETRACKR_INSTRUCTIONS,
                'voice': 'shimmer',
                'input_audio_format': 'g711_ulaw',
                'output_audio_format': 'g711_ulaw',
                'input_audio_transcription': {'model': 'whisper-1'},
                'turn_detection': {
                    'type': 'server_vad',
                    'threshold': 0.5,
                    'prefix_padding_ms': 300,
                    'silence_duration_ms': 500
                },
                'tools': [{
                    'type': 'function',
                    'name': 'save_patient_response',
                    'description': 'Save patient responses',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'had_appendectomy': {'type': 'boolean'},
                            'symptoms_reported': {'type': 'string'},
                            'is_urgent': {'type': 'boolean'},
                            'additional_notes': {'type': 'string'}
                        },
                        'required': ['had_appendectomy', 'symptoms_reported']
                    }
                }],
                'temperature': 0.8,
                'max_response_output_tokens': 'inf'
            }
        }
        
        await openai_ws.send(json.dumps(session_config))
        
        # Handle OpenAI messages
        async def handle_openai():
            nonlocal has_triggered_greeting, openai_packet_count, call_sid
            
            async for message in openai_ws:
                try:
                    event = json.loads(message)
                    event_type = event.get('type')
                    
                    if event_type == 'session.updated':
                        print('✅ Session configured')
                        if not has_triggered_greeting:
                            has_triggered_greeting = True
                            await asyncio.sleep(1)
                            await openai_ws.send(json.dumps({
                                'type': 'response.create',
                                'response': {
                                    'modalities': ['text', 'audio'],
                                    'instructions': 'Start the post-surgery follow-up call.'
                                }
                            }))
                    
                    elif event_type == 'response.audio.delta':
                        delta = event.get('delta')
                        if delta and stream_sid:
                            openai_packet_count += 1
                            await websocket.send_json({
                                'event': 'media',
                                'streamSid': stream_sid,
                                'media': {'payload': delta}
                            })
                    
                    elif event_type == 'response.audio_transcript.done':
                        print(f'🤖 AI: {event["transcript"]}')
                    
                    elif event_type == 'conversation.item.input_audio_transcription.completed':
                        print(f'🗣️  Patient: {event["transcript"]}')
                    
                    elif event_type == 'response.function_call_arguments.done':
                        func_name = event.get('name')
                        if func_name == 'save_patient_response':
                            args = json.loads(event.get('arguments'))
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
                
                except Exception as e:
                    print(f'❌ OpenAI error: {str(e)}')
        
        # Handle Twilio messages
        async def handle_twilio():
            nonlocal stream_sid, call_sid, twilio_packet_count
            
            async for message in websocket.iter_text():
                try:
                    msg = json.loads(message)
                    event = msg.get('event')
                    
                    if event == 'start':
                        stream_sid = msg['start']['streamSid']
                        call_sid = msg['start']['callSid']
                        print(f'🎬 Stream started: {call_sid}')
                    
                    elif event == 'media':
                        twilio_packet_count += 1
                        await openai_ws.send(json.dumps({
                            'type': 'input_audio_buffer.append',
                            'audio': msg['media']['payload']
                        }))
                    
                    elif event == 'stop':
                        print(f'⏹️  Stream stopped. Packets: {twilio_packet_count}')
                
                except Exception as e:
                    print(f'❌ Twilio error: {str(e)}')
        
        await asyncio.gather(handle_openai(), handle_twilio())
    
    except Exception as e:
        print(f'❌ WebSocket error: {str(e)}')
    
    finally:
        print('🔌 Closing connections')
        if openai_ws:
            await openai_ws.close()

# Run the app
if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting CareTrackr Call Service...")
    print(f"📞 Default phone number: {DEFAULT_PHONE_NUMBER}")
    print(f"🌐 Visit: http://localhost:8000/make-call")
    print("-" * 60)
    
    # Check environment variables
    print("🔧 Configuration Check:")
    print(f"   OPENAI_API_KEY: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"   TWILIO_ACCOUNT_SID: {'✅ Set' if TWILIO_ACCOUNT_SID else '❌ Missing'}")
    print(f"   TWILIO_AUTH_TOKEN: {'✅ Set' if TWILIO_AUTH_TOKEN else '❌ Missing'}")
    print(f"   TWILIO_PHONE_NUMBER: {TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else '❌ Missing'}")
    print(f"   SERVER_DOMAIN: {SERVER_DOMAIN}")
    print("-" * 60)
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("⚠️  WARNING: Some Twilio credentials are missing!")
        print("   Calls will fail without proper Twilio configuration")
        print("   Check your .env file")
    
    print("\n✅ Server starting...\n")
    uvicorn.run(caretrackr, host="localhost", port=8000)