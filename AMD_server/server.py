# =========================
# file: server.py
# =========================
#!/usr/bin/env python3
"""
server.py — Prompt + OCR + Email ADK API on AMD server
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

from OCR import run_ocr  # existing
# New: email ADK orchestrator+reply
try:
    from ADK.email_adk import orchestrate_and_reply
except Exception as e:
    orchestrate_and_reply = None
    print(f"[SERVER] ADK.email_adk not available: {e}")
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

def _parse_email_prompt(prompt: str) -> dict:
    """Parse email data from the prompt string."""
    import re

    # Check if this is an email prompt
    if not prompt.startswith("EMAIL FROM:"):
        return None

    email_data = {}

    # Extract sender
    from_match = re.search(r"EMAIL FROM:\s*(.+?)(?:\n|$)", prompt, re.IGNORECASE)
    if from_match:
        email_data["from"] = from_match.group(1).strip()

    # Extract subject
    subject_match = re.search(r"SUBJECT:\s*(.+?)(?:\n|$)", prompt, re.IGNORECASE)
    if subject_match:
        email_data["subject"] = subject_match.group(1).strip()

    # Extract body (everything after "BODY:")
    body_match = re.search(r"BODY:\s*(.+)", prompt, re.IGNORECASE | re.DOTALL)
    if body_match:
        email_data["body"] = body_match.group(1).strip()

    return email_data if email_data else None


def _generate_reply_email(email_data: dict) -> dict:
    """Generate a reply email based on the incoming email data."""
    from datetime import datetime

    sender = email_data.get("from", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")

    # Extract sender name from email
    import re
    name_match = re.search(r"(.+?)\s*<", sender)
    sender_name = name_match.group(1).strip() if name_match else sender.split("@")[0]

    # Extract email address
    email_match = re.search(r"<(.+?)>", sender) or re.search(r"[\w\.-]+@[\w\.-]+", sender)
    sender_email = email_match.group(1) if email_match and "<" in sender else email_match.group(0) if email_match else sender

    # Classify the email content
    body_lower = body.lower()

    # Generate response based on content
    if "pip" in body_lower and "coverage" in body_lower:
        reply_body = f"""Dear {sender_name},

Thank you for reaching out with your questions regarding your Personal Injury Protection (PIP) coverage and settlement offer related to your March 20, 2022 accident.

I have carefully reviewed the details you've provided. Let me address your concerns:

**Regarding Your PIP Coverage:**

Florida PIP coverage typically provides $10,000 in medical benefits. However, the payments you're seeing may include:
- Direct payments to medical providers under PIP
- Additional payments from the at-fault driver's bodily injury (BI) coverage
- It's important to obtain a detailed breakdown from State Farm to understand which coverage paid for what

**Regarding the Settlement Offer:**

The $25,000 policy limit mentioned in the offer letter is likely from the at-fault driver's Bodily Injury (BI) coverage. This is separate from your PIP benefits.

Key points to consider:
1. **Bodily Injury Coverage**: The $25,000 appears to be the BI policy limit from Mr. Thomas's insurance
2. **Underinsured Motorist (UIM)**: After accepting the BI limit, you may be able to pursue UIM coverage if your own policy includes it and your damages exceed the $25,000
3. **PIP Treatment**: You should still qualify for continued treatment under PIP if benefits haven't been exhausted

**Next Steps:**

To provide you with the most accurate guidance, I recommend:
- Reviewing your complete insurance policy documents
- Obtaining a detailed payment breakdown from State Farm
- Scheduling a consultation to discuss settlement strategy

Please send me:
1. Your insurance policy declaration page
2. Complete PIP payment log
3. The settlement offer letter
4. Any EMC evaluation reports

I will review these documents and provide you with a comprehensive analysis within 24-48 hours.

**Important**: Do not accept any settlement offers until we've had a chance to review all the details together.

Best regards,
Paralegal AI Assistant
Law Office

**This is an automated initial response. A licensed attorney will review your case and follow up with you directly.**"""

    elif "settlement" in body_lower or "offer" in body_lower:
        reply_body = f"""Dear {sender_name},

Thank you for contacting us regarding your settlement offer.

I have received your inquiry and am reviewing the details you provided. Settlement decisions are important and require careful consideration of all factors.

I will need to:
1. Review the settlement offer details
2. Assess your total damages and expenses
3. Consult with the supervising attorney
4. Provide you with a comprehensive recommendation

Please do not accept or reject any settlement offers until we have had an opportunity to discuss this matter further.

I will follow up with you within 24 hours with next steps.

Best regards,
Paralegal AI Assistant
Law Office

**This is an automated initial response. A licensed attorney will review your case and follow up with you directly.**"""

    else:
        reply_body = f"""Dear {sender_name},

Thank you for your email. I have received your message and am reviewing the information you provided.

I will look into this matter and get back to you with a detailed response within 1-2 business days.

If you need immediate assistance, please don't hesitate to contact our office directly.

Best regards,
Paralegal AI Assistant
Law Office

**This is an automated initial response. A licensed attorney will review your case and follow up with you directly.**"""

    # Prepare reply subject
    reply_subject = subject
    if not reply_subject.lower().startswith("re:"):
        reply_subject = f"Re: {reply_subject}"

    # Create reply JSON structure
    reply = {
        "to": sender_email,
        "to_name": sender_name,
        "from": "paralegal@lawoffice.com",
        "from_name": "Paralegal AI Assistant",
        "subject": reply_subject,
        "body": reply_body,
        "timestamp": datetime.now().isoformat(),
        "in_reply_to": email_data.get("message_id", ""),
        "original_subject": subject,
        "classification": "pip_coverage" if "pip" in body_lower else "general_inquiry",
        "auto_send": False,
        "requires_review": True
    }

    return reply


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
    import re
    import json
    from datetime import datetime

    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    print(f"[SERVER] /prompt: {prompt[:140]}")

    # Parse email from prompt
    email_data = _parse_email_prompt(prompt)

    if email_data:
        # Generate reply email
        reply = _generate_reply_email(email_data)

        # Save JSON to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_reply_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), "replies", filename)

        # Create replies directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(reply, f, indent=2)

        print(f"[SERVER] Saved reply to: {filepath}")

        return jsonify({
            "response": f"Processed prompt: {prompt[:100].upper()}...",
            "reply_email": reply,
            "saved_to": filename
        })
    else:
        # Fallback for non-email prompts
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
    app.run(host="0.0.0.0", port=8080)

