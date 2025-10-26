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
