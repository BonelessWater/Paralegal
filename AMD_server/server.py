#!/usr/bin/env python3
"""
server.py — Prompt + OCR API on AMD server + Database API
Run:
  cd ~/Paralegal/AMD_server
  source ~/venv/bin/activate
  python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import sys
import os
from OCR import run_ocr  # import our OCR function

# Import email processing components
try:
    from ml_pipeline.emailer.email_processor import EmailProcessor
    from ml_pipeline.emailer.email_classifier import EmailClassifier
    print("[SERVER] Email processing components imported")
    email_processor = EmailProcessor()
    email_classifier = EmailClassifier()
except ImportError as e:
    print(f"[SERVER] Could not import email components: {e}")
    email_processor = None
    email_classifier = None

# Add the backend APIs directory to the path
backend_apis_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'APIs')
backend_apis_path = os.path.abspath(backend_apis_path)
print(f"[SERVER] Looking for services in: {backend_apis_path}")
print(f"[SERVER] Path exists: {os.path.exists(backend_apis_path)}")
if os.path.exists(backend_apis_path):
    files = os.listdir(backend_apis_path)
    print(f"[SERVER] Files in directory: {files}")
sys.path.insert(0, backend_apis_path)

# Try to import database service first, then fall back to mock data
try:
    from database_service import DatabaseService, DatabaseConfig
    print("[SERVER] Database service imported successfully")
    # Try to connect to actual database
    try:
        db_config = DatabaseConfig(
            host='localhost',
            port=5432,
            database='paralegal_db',
            username='paralegal_user',
            password='hackathon2024'
        )
        database_service = DatabaseService(db_config)
        # Test the connection
        test_conn = database_service.get_connection()
        test_conn.close()
        print("[SERVER] Successfully connected to PostgreSQL database")
        data_service = database_service
        use_database = True
    except Exception as db_error:
        print(f"[SERVER] Could not connect to database: {db_error}")
        print("[SERVER] Falling back to mock data service")
        database_service = None
        use_database = False
        # Import mock service as fallback
        try:
            from mock_data_service import MockDataService
            print("[SERVER] Mock data service imported successfully")
            data_service = MockDataService
        except ImportError as e:
            print(f"[SERVER] Could not import mock_data_service: {e}")
            data_service = None
except ImportError as e:
    print(f"[SERVER] Could not import database_service: {e}")
    print("[SERVER] Falling back to mock data service")
    use_database = False
    try:
        from mock_data_service import MockDataService
        print("[SERVER] Mock data service imported successfully")
        data_service = MockDataService
    except ImportError as e:
        print(f"[SERVER] Could not import mock_data_service: {e}")
        data_service = None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Data service is already initialized above
if data_service:
    if use_database:
        print("[SERVER] Using PostgreSQL database for real data")
    else:
        print("[SERVER] Using mock data service for consistent frontend compatibility")
else:
    print("[SERVER] No data service available")
    use_database = False

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

@app.post("/email")
def handle_email():
    """
    Process incoming email and generate a response.

    Expected JSON body:
    {
        "from": "sender@example.com",
        "subject": "Email subject",
        "body": "Email body text",
        "attachments": []  # optional
    }

    Returns:
    {
        "analysis": {
            "classification": "CLIENT_COMMUNICATION",
            "urgency_score": 0.75,
            "sentiment": "NEGATIVE",
            "entities": {...},
            "action_required": true
        },
        "suggested_response": {
            "to": "sender@example.com",
            "subject": "Re: ...",
            "body": "Dear ...",
            "send": false
        }
    }
    """
    data = request.get_json(silent=True) or {}
    sender = data.get("from", "")
    subject = data.get("subject", "")
    body = data.get("body", "")
    attachments = data.get("attachments", [])

    print(f"[SERVER] /email from={sender} subj={subject}")

    if not body:
        return jsonify({"error": "Email body is required"}), 400

    # Process email if components are available
    if email_processor and email_classifier:
        try:
            # Analyze email
            from datetime import datetime
            analysis = email_processor.process_email(
                email_text=body,
                subject=subject,
                sender=sender,
                sent_date=datetime.now()
            )

            # Classify email type
            try:
                classification = email_classifier.predict(body)
                probabilities = email_classifier.predict_proba(body)
                analysis['classification'] = classification
                analysis['classification_probabilities'] = probabilities
            except Exception as e:
                # Fallback to keyword-based classification
                print(f"[SERVER] Classifier not trained, using fallback: {e}")
                analysis['classification'] = _classify_email_fallback(body, subject)

            # Generate response
            response = _generate_email_response(
                sender=sender,
                subject=subject,
                body=body,
                analysis=analysis
            )

            return jsonify({
                "analysis": analysis,
                "suggested_response": response,
                "status": "processed"
            })

        except Exception as e:
            print(f"[SERVER] Error processing email: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to process email",
                "details": str(e)
            }), 500
    else:
        # Fallback if email components not available
        return jsonify({
            "analysis": {
                "classification": _classify_email_fallback(body, subject),
                "urgency_score": 0.5,
                "sentiment": "NEUTRAL",
                "entities": {},
                "action_required": True
            },
            "suggested_response": _generate_email_response(
                sender=sender,
                subject=subject,
                body=body,
                analysis=None
            ),
            "status": "processed_fallback"
        })

def _classify_email_fallback(body: str, subject: str) -> str:
    """Simple keyword-based classification fallback."""
    text = (subject + " " + body).lower()

    if any(word in text for word in ['medical records', 'records request', 'hospital', 'doctor']):
        return 'RECORDS_REQUEST'
    elif any(word in text for word in ['settlement', 'offer', 'negotiate', 'compensation']):
        return 'SETTLEMENT_DISCUSSION'
    elif any(word in text for word in ['case law', 'precedent', 'research', 'statute']):
        return 'LEGAL_RESEARCH'
    elif any(word in text for word in ['filing', 'motion', 'court', 'deadline']):
        return 'COURT_FILING'
    elif any(word in text for word in ['pip', 'coverage', 'insurance', 'claim', 'accident']):
        return 'CLIENT_COMMUNICATION'
    else:
        return 'CLIENT_COMMUNICATION'

def _generate_email_response(sender: str, subject: str, body: str, analysis: dict) -> dict:
    """Generate a suggested email response based on email analysis."""

    # Extract sender name
    sender_name = sender.split('<')[0].strip() if '<' in sender else sender.split('@')[0]
    if not sender_name:
        sender_name = "there"

    # Determine classification
    if analysis and 'classification' in analysis:
        classification = analysis['classification']
        urgency = analysis.get('urgency_score', 0.5)
        sentiment = analysis.get('sentiment', 'NEUTRAL')
    else:
        classification = _classify_email_fallback(body, subject)
        urgency = 0.5
        sentiment = 'NEUTRAL'

    # Generate appropriate response based on classification
    response_body = ""

    if classification == 'RECORDS_REQUEST':
        response_body = f"""Dear {sender_name},

Thank you for contacting us regarding your medical records request.

We have received your request and are working to process it as quickly as possible. We will:

1. Contact the relevant medical providers to obtain the requested records
2. Review the records for completeness
3. Forward them to you once received

This process typically takes 7-14 business days. We will keep you updated on our progress.

If you have any questions in the meantime, please don't hesitate to reach out.

Best regards,
Paralegal AI Assistant"""

    elif classification == 'SETTLEMENT_DISCUSSION':
        response_body = f"""Dear {sender_name},

Thank you for your email regarding the settlement offer.

I have carefully reviewed your message and the details you provided. We understand the importance of this matter to you.

To best assist you with this settlement discussion, I will need to:

1. Review the complete offer details
2. Consult with the supervising attorney
3. Prepare a thorough analysis of the proposed terms

I will follow up with you within 24-48 hours with our recommendations and next steps.

Please let me know if you have any additional information or questions.

Best regards,
Paralegal AI Assistant"""

    elif classification == 'CLIENT_COMMUNICATION':
        # Handle PIP coverage questions
        if 'pip' in body.lower() or 'personal injury protection' in body.lower():
            response_body = f"""Dear {sender_name},

Thank you for reaching out with your questions about PIP coverage and your settlement offer.

I understand you have concerns about:
- Your PIP (Personal Injury Protection) coverage details
- The settlement offer you've received
- Your accident from March 20, 2022

To provide you with accurate information, I will need to:

1. Review your insurance policy documents
2. Examine the settlement offer details
3. Consult with the supervising attorney regarding your specific situation

Could you please provide or confirm:
- Your insurance policy number
- Copy of the settlement offer (if available)
- Any recent correspondence from the insurance company

I will work on gathering this information and will have a detailed response for you within 1-2 business days.

If this is urgent, please don't hesitate to call our office directly.

Best regards,
Paralegal AI Assistant"""
        else:
            response_body = f"""Dear {sender_name},

Thank you for your email. I have received your message and am reviewing the details you provided.

I will look into this matter and get back to you with a thorough response within 1-2 business days.

If you need immediate assistance or have additional information to share, please feel free to reach out.

Best regards,
Paralegal AI Assistant"""

    elif classification == 'LEGAL_RESEARCH':
        response_body = f"""Dear {sender_name},

Thank you for your legal research inquiry.

I have noted your request and will begin researching the relevant case law and statutes. Our research will include:

1. Reviewing applicable precedents
2. Analyzing current statutory requirements
3. Preparing a comprehensive summary of findings

I expect to have initial research findings for you within 2-3 business days.

Best regards,
Paralegal AI Assistant"""

    elif classification == 'COURT_FILING':
        response_body = f"""Dear {sender_name},

Thank you for your email regarding the court filing.

I have received your message and am reviewing the filing requirements and deadlines. I will:

1. Verify all filing deadlines
2. Prepare the necessary documents
3. Coordinate with the supervising attorney for review

I will update you on our progress within 24 hours.

Best regards,
Paralegal AI Assistant"""

    else:
        response_body = f"""Dear {sender_name},

Thank you for your email.

I have received your message and will review it carefully. I will get back to you with a detailed response within 1-2 business days.

If you need immediate assistance, please don't hesitate to call our office.

Best regards,
Paralegal AI Assistant"""

    # Adjust tone based on urgency and sentiment
    if urgency and urgency > 0.7:
        response_body = response_body.replace("within 1-2 business days", "within 24 hours")
        response_body = response_body.replace("within 2-3 business days", "within 1-2 business days")

    # Create response subject
    response_subject = subject
    if not response_subject.lower().startswith('re:'):
        response_subject = f"Re: {response_subject}"

    return {
        "to": sender,
        "subject": response_subject,
        "body": response_body,
        "send": False,  # Require manual approval before sending
        "classification": classification,
        "urgency": urgency if analysis else 0.5
    }

@app.get("/healthz")
def healthz():
    return "ok", 200

# ============================================================================
# DATABASE API ENDPOINTS
# ============================================================================

@app.get("/api/tasks")
def get_tasks():
    """Get tasks from the data service"""
    print(f"[DEBUG] data_service is: {data_service}")
    if not data_service:
        print("[DEBUG] Data service not available")
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        print("[DEBUG] Calling data_service.get_tasks()")
        limit = request.args.get('limit', 50, type=int)
        tasks = data_service.get_tasks()
        print(f"[DEBUG] Got {len(tasks)} tasks")
        # Apply limit if specified
        if limit and limit < len(tasks):
            tasks = tasks[:limit]
        return jsonify({"tasks": tasks})
    except Exception as e:
        print(f"[API] Error getting tasks: {e}")
        import traceback
        print(f"[API] Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to fetch tasks"}), 500

@app.get("/api/agents")
def get_agents():
    """Get agent statistics"""
    if not data_service:
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        agents = data_service.get_agents()
        return jsonify({"agents": agents})
    except Exception as e:
        print(f"[API] Error getting agents: {e}")
        return jsonify({"error": "Failed to fetch agents"}), 500

@app.get("/api/outreach")
def get_outreach():
    """Get outreach activities"""
    if not data_service:
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        limit = request.args.get('limit', 50, type=int)
        outreach = data_service.get_outreach_activities()
        # Apply limit if specified
        if limit and limit < len(outreach):
            outreach = outreach[:limit]
        return jsonify({"outreach": outreach})
    except Exception as e:
        print(f"[API] Error getting outreach: {e}")
        return jsonify({"error": "Failed to fetch outreach activities"}), 500

@app.get("/api/stats")
def get_stats():
    """Get system statistics"""
    if not data_service:
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        stats = data_service.get_system_stats()
        return jsonify({"stats": stats})
    except Exception as e:
        print(f"[API] Error getting stats: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500

@app.get("/api/tasks/<task_id>")
def get_task_by_id(task_id):
    """Get a specific task by ID"""
    if not data_service:
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        task = data_service.get_task_by_id(task_id)
        if task:
            return jsonify({"task": task})
        else:
            return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        print(f"[API] Error getting task {task_id}: {e}")
        return jsonify({"error": "Failed to fetch task"}), 500

@app.put("/api/tasks/<task_id>")
def update_task(task_id):
    """Update a task's status and AI draft"""
    if not data_service:
        return jsonify({"error": "Data service not available"}), 503
    
    try:
        data = request.get_json() or {}
        status = data.get('status')
        ai_draft = data.get('ai_draft')
        
        if not status:
            return jsonify({"error": "Status is required"}), 400
        
        success = data_service.update_task_status(task_id, status, ai_draft)
        if success:
            return jsonify({"message": "Task updated successfully"})
        else:
            return jsonify({"error": "Failed to update task"}), 500
    except Exception as e:
        print(f"[API] Error updating task {task_id}: {e}")
        return jsonify({"error": "Failed to update task"}), 500

if __name__ == "__main__":
    # Listen on all interfaces so your client can reach it
    app.run(host="0.0.0.0", port=8080, debug=True)
