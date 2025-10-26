"""
FastAPI Backend Server - Paralegal AI
Connects React frontend to AMD vLLM agents + Intelligent Legal Research System

Features:
- 4 Specialist Agents (Client Comm, Records, Legal Research, Evidence)
- Intelligent Legal Scraper (41.7 cases/sec, 10.6M opinions)
- Task management (pending → processing → approval → sent)
- Real-time stats and monitoring

Port: 8080 (vLLM uses 8000)
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # Load .env file if it exists

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add project paths - add the parent directory so we can import AMD_server
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))  # This allows "from AMD_server..." to work

# Import our components
from llm_client import AMDLLMClient

# Import agents
from AMD_server.agents.client_communication_agent import ClientCommunicationAgent
from AMD_server.agents.records_wrangler_agent import RecordsWranglerAgent
from AMD_server.agents.legal_researcher_agent import LegalResearcherAgent
from AMD_server.agents.evidence_sorter_agent import EvidenceSorterAgent

# Import intelligent scraping system
from AMD_server.ml_pipeline.orchestrator import ScrapingOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class IncomingTask(BaseModel):
    """Incoming task from client (email/text/call)"""
    source: str  # 'email', 'text', 'call'
    content: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    priority: Optional[str] = "medium"

class TaskApproval(BaseModel):
    """Approval data for AI-generated response"""
    approved: bool
    edited_content: Optional[str] = None
    send_immediately: bool = True

class Task(BaseModel):
    """Task representation matching frontend types"""
    id: str
    status: str  # 'pending', 'processing', 'awaiting_approval', 'approved', 'sent', 'failed'
    source: str
    content: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    priority: str
    assigned_agent: Optional[str] = None
    ai_response: Optional[str] = None
    approved_response: Optional[str] = None
    created_at: str
    updated_at: str
    metadata: Optional[Dict] = {}

class Agent(BaseModel):
    """Agent status representation"""
    id: str
    name: str
    status: str  # 'idle', 'processing', 'error'
    tasks_processed: int
    success_rate: float
    avg_response_time: float
    current_task: Optional[str] = None

class SystemStats(BaseModel):
    """System-wide statistics"""
    total_tasks: int
    tasks_pending: int
    tasks_processing: int
    tasks_awaiting_approval: int
    tasks_completed: int
    total_agents: int
    active_agents: int
    avg_processing_time: float
    success_rate: float
    cases_scraped_today: int
    scraping_speed: float  # cases/sec

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Paralegal AI Backend",
    description="AMD-powered legal AI agent system with intelligent case research",
    version="2.0.0"
)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:4173",  # Vite preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL STATE (In-memory for demo)
# ============================================================================

# Task storage (in production, use database)
tasks_db: Dict[str, Task] = {}

# Agent instances (initialized on startup)
agents_db: Dict[str, Dict] = {}

# LLM client (initialized on startup)
llm_client: Optional[AMDLLMClient] = None

# Intelligent scraper (initialized on startup)
intelligent_scraper: Optional[ScrapingOrchestrator] = None

# Performance tracking
performance_metrics = {
    'tasks_created': 0,
    'tasks_completed': 0,
    'total_processing_time': 0.0,
    'cases_scraped': 0,
    'scraping_sessions': 0,
}

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize all components on server startup"""
    global llm_client, agents_db, intelligent_scraper
    
    logger.info("🚀 Starting Paralegal AI Backend Server...")
    
    # 1. Initialize LLM Client
    try:
        vllm_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
        llm_client = AMDLLMClient(base_url=vllm_url)
        
        if llm_client.health_check():
            logger.info(f"✅ vLLM server connected: {vllm_url}")
        else:
            logger.warning(f"⚠️  vLLM server not responding: {vllm_url}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM client: {e}")
        llm_client = None
    
    # 2. Initialize Specialist Agents
    try:
        agents_db['client_communication'] = {
            'instance': ClientCommunicationAgent(llm_client),
            'name': 'Client Communication Specialist',
            'tasks_processed': 0,
            'total_time': 0.0,
            'failures': 0,
            'status': 'idle',
            'current_task': None
        }
        
        agents_db['records_wrangler'] = {
            'instance': RecordsWranglerAgent(llm_client),
            'name': 'Records Wrangler',
            'tasks_processed': 0,
            'total_time': 0.0,
            'failures': 0,
            'status': 'idle',
            'current_task': None
        }
        
        # NOTE: legal_researcher initialized later with intelligent scraper integrated
        
        agents_db['evidence_sorter'] = {
            'instance': EvidenceSorterAgent(llm_client),
            'name': 'Evidence Sorter',
            'tasks_processed': 0,
            'total_time': 0.0,
            'failures': 0,
            'status': 'idle',
            'current_task': None
        }
        
        # NOTE: Legal researcher will be initialized after intelligent scraper
        # so we can pass the scraper instance to it
        
        logger.info(f"✅ Initialized {len(agents_db) - 1} specialist agents (legal researcher pending)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
    
    # 3. Initialize Intelligent Scraping System
    try:
        intelligent_scraper = ScrapingOrchestrator(
            use_lexisnexis=False,  # Use CourtListener for demo
            max_concurrent_requests=100,  # HYPER-PARALLELIZED!
            cache_results=True
        )
        logger.info("✅ Intelligent scraping system initialized (100 concurrent workers)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize intelligent scraper: {e}")
        intelligent_scraper = None
    
    # 4. Now initialize Legal Researcher with Intelligent Scraper integrated
    try:
        agents_db['legal_researcher'] = {
            'instance': LegalResearcherAgent(
                llm_client,
                intelligent_scraper=intelligent_scraper  # INTEGRATED!
            ),
            'name': 'Legal Researcher',
            'tasks_processed': 0,
            'total_time': 0.0,
            'failures': 0,
            'status': 'idle',
            'current_task': None
        }
        logger.info("✅ Legal researcher agent initialized with integrated intelligent scraper")
    except Exception as e:
        logger.error(f"❌ Failed to initialize legal researcher: {e}")
    
    logger.info(f"🎉 Server startup complete! {len(agents_db)} agents ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("👋 Shutting down Paralegal AI Backend Server...")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def classify_task(content: str, source: str) -> str:
    """
    Classify incoming task to determine which agent should handle it.
    
    Simple keyword-based classification for demo.
    In production, use LLM-based classification.
    """
    content_lower = content.lower()
    
    # Legal research keywords
    if any(word in content_lower for word in ['case', 'precedent', 'ruling', 'court', 'judge', 'law', 'statute']):
        return 'legal_researcher'
    
    # Records keywords
    if any(word in content_lower for word in ['medical', 'record', 'document', 'file', 'report', 'evidence']):
        return 'records_wrangler'
    
    # Evidence keywords
    if any(word in content_lower for word in ['photo', 'image', 'video', 'witness', 'evidence', 'proof']):
        return 'evidence_sorter'
    
    # Default to client communication
    return 'client_communication'

async def process_task_background(task_id: str):
    """
    Background task processor.

    1. Classify task → determine agent
    2. Call agent.process()
    3. Update task with AI response
    4. Set status to 'awaiting_approval'
    """
    agent_id = None  # Initialize to avoid NameError in exception handler
    try:
        task = tasks_db.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        logger.info(f"Starting background processing for task {task_id}")

        # Update status
        task.status = 'processing'
        task.updated_at = datetime.now().isoformat()

        # Classify and route to agent
        agent_id = classify_task(task.content, task.source)
        task.assigned_agent = agent_id

        logger.info(f"Task {task_id} classified as: {agent_id}")

        # Get agent
        agent_data = agents_db.get(agent_id)
        if not agent_data:
            raise Exception(f"Agent {agent_id} not found")

        agent_instance = agent_data['instance']
        agent_data['status'] = 'processing'
        agent_data['current_task'] = task_id

        # Process with agent (agent handles its own intelligent tools)
        start_time = datetime.now()

        # Call agent's process method - properly handle both async and sync
        if hasattr(agent_instance, 'process_async'):
            logger.info(f"Calling async process_async for {agent_id}")
            result = await agent_instance.process_async(task.content)
        else:
            logger.info(f"Calling sync process for {agent_id} in thread executor")
            # Run synchronous process in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent_instance.process, task.content)
        
        # Extract response from result - handle different agent response formats
        # LegalResearcherAgent: {'response': '...', 'analysis': '...'}
        # ClientCommunicationAgent: {'polished_response': '...'}
        # RecordsWranglerAgent: {'records_request': '...'}
        # EvidenceSorterAgent: {'classification': '...'}
        ai_response = (
            result.get('response') or
            result.get('polished_response') or
            result.get('records_request') or
            result.get('classification') or
            result.get('analysis') or
            str(result)  # Fallback to string representation
        )

        logger.info(f"Extracted AI response ({len(ai_response)} chars) from {agent_id}")
        
        # For legal researcher, update scraper metrics if available
        if agent_id == 'legal_researcher' and 'total_cases_found' in result:
            performance_metrics['cases_scraped'] += result.get('total_cases_found', 0)
            performance_metrics['scraping_sessions'] += 1
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Update agent stats
        agent_data['tasks_processed'] += 1
        agent_data['total_time'] += processing_time
        agent_data['status'] = 'idle'
        agent_data['current_task'] = None
        
        # Update task
        task.ai_response = ai_response
        task.status = 'awaiting_approval'
        task.updated_at = datetime.now().isoformat()
        task.metadata['processing_time'] = processing_time
        task.metadata['agent'] = agent_id
        
        # Update performance
        performance_metrics['tasks_completed'] += 1
        performance_metrics['total_processing_time'] += processing_time

        logger.info(f"✅ Task {task_id} completed successfully!")
        logger.info(f"   Agent: {agent_id}")
        logger.info(f"   Processing time: {processing_time:.2f}s")
        logger.info(f"   Status: {task.status}")
        logger.info(f"   Response length: {len(ai_response)} chars")

    except Exception as e:
        import traceback
        logger.error(f"❌ TASK PROCESSING FAILED - Task ID: {task_id}")
        logger.error(f"   Error: {e}")
        logger.error(f"   Agent: {agent_id}")
        logger.error(f"   Full traceback:\n{traceback.format_exc()}")

        task = tasks_db.get(task_id)
        if task:
            task.status = 'failed'
            task.metadata['error'] = str(e)
            task.metadata['error_traceback'] = traceback.format_exc()
            task.updated_at = datetime.now().isoformat()
            logger.error(f"   Task {task_id} marked as 'failed'")

        # Update agent failure count
        if agent_id and agent_id in agents_db:
            agents_db[agent_id]['failures'] += 1
            agents_db[agent_id]['status'] = 'idle'
            agents_db[agent_id]['current_task'] = None
            logger.error(f"   Agent {agent_id} returned to idle state")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Paralegal AI Backend",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "4 Specialist AI Agents",
            "Intelligent Legal Research (41.7 cases/sec)",
            "10.6M Legal Opinions (CourtListener)",
            "AMD MI300X GPU Acceleration"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    vllm_status = llm_client.health_check() if llm_client else False
    scraper_status = intelligent_scraper is not None

    return {
        "status": "healthy" if vllm_status else "degraded",
        "vllm_connected": vllm_status,
        "intelligent_scraper": scraper_status,
        "agents_initialized": len(agents_db),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tasks", response_model=List[Task])
async def get_tasks(status: Optional[str] = None):
    """
    Get all tasks, optionally filtered by status

    Query params:
        status: Filter by status (pending, processing, awaiting_approval, approved, sent)
    """
    all_tasks = list(tasks_db.values())

    if status:
        all_tasks = [t for t in all_tasks if t.status == status]

    # Sort by created_at descending (newest first)
    all_tasks.sort(key=lambda t: t.created_at, reverse=True)

    return all_tasks

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get specific task by ID"""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/ingest")
async def ingest_task(task_data: IncomingTask, background_tasks: BackgroundTasks):
    """
    Ingest new task from client communication (email/text/call)

    This triggers background processing:
    1. Classify task
    2. Route to appropriate agent
    3. Generate AI response
    4. Wait for human approval
    """
    # Create task
    task_id = str(uuid.uuid4())

    task = Task(
        id=task_id,
        status='pending',
        source=task_data.source,
        content=task_data.content,
        sender=task_data.sender,
        subject=task_data.subject,
        priority=task_data.priority,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        metadata={}
    )

    tasks_db[task_id] = task
    performance_metrics['tasks_created'] += 1

    logger.info(f"📥 Task {task_id} created - Source: {task_data.source}, Content length: {len(task_data.content)} chars")

    # Start background processing
    background_tasks.add_task(process_task_background, task_id)
    logger.info(f"🔄 Background processing queued for task {task_id}")

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Task received and queued for processing"
    }

@app.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, approval: TaskApproval):
    """
    Approve (or reject) AI-generated response
    
    If approved, task moves to 'approved' status
    If edited, use edited version
    If send_immediately=True, trigger outreach (email/SMS/call)
    """
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != 'awaiting_approval':
        raise HTTPException(
            status_code=400, 
            detail=f"Task is in '{task.status}' status, cannot approve"
        )
    
    if approval.approved:
        # Use edited content if provided, otherwise use AI response
        task.approved_response = approval.edited_content or task.ai_response
        task.status = 'approved'
        
        if approval.send_immediately:
            # In production, trigger actual outreach here
            # For demo, just mark as sent
            task.status = 'sent'
            task.metadata['sent_at'] = datetime.now().isoformat()
            logger.info(f"📤 Task {task_id} marked as sent")
    else:
        # Rejected - move back to pending or mark as rejected
        task.status = 'rejected'
        task.metadata['rejected_at'] = datetime.now().isoformat()
    
    task.updated_at = datetime.now().isoformat()
    
    return {
        "task_id": task_id,
        "status": task.status,
        "message": "Task updated successfully"
    }

@app.get("/agents", response_model=List[Agent])
async def get_agents():
    """Get status of all agents"""
    agents_list = []
    
    for agent_id, agent_data in agents_db.items():
        tasks_processed = agent_data['tasks_processed']
        failures = agent_data['failures']
        
        success_rate = (
            (tasks_processed - failures) / tasks_processed * 100 
            if tasks_processed > 0 else 100.0
        )
        
        avg_time = (
            agent_data['total_time'] / tasks_processed 
            if tasks_processed > 0 else 0.0
        )
        
        agents_list.append(Agent(
            id=agent_id,
            name=agent_data['name'],
            status=agent_data['status'],
            tasks_processed=tasks_processed,
            success_rate=success_rate,
            avg_response_time=avg_time,
            current_task=agent_data['current_task']
        ))
    
    return agents_list

@app.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agent_data = agents_db.get(agent_id)
    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    tasks_processed = agent_data['tasks_processed']
    failures = agent_data['failures']
    
    success_rate = (
        (tasks_processed - failures) / tasks_processed * 100 
        if tasks_processed > 0 else 100.0
    )
    
    avg_time = (
        agent_data['total_time'] / tasks_processed 
        if tasks_processed > 0 else 0.0
    )
    
    return Agent(
        id=agent_id,
        name=agent_data['name'],
        status=agent_data['status'],
        tasks_processed=tasks_processed,
        success_rate=success_rate,
        avg_response_time=avg_time,
        current_task=agent_data['current_task']
    )

@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system-wide statistics"""
    all_tasks = list(tasks_db.values())
    
    stats = SystemStats(
        total_tasks=len(all_tasks),
        tasks_pending=len([t for t in all_tasks if t.status == 'pending']),
        tasks_processing=len([t for t in all_tasks if t.status == 'processing']),
        tasks_awaiting_approval=len([t for t in all_tasks if t.status == 'awaiting_approval']),
        tasks_completed=len([t for t in all_tasks if t.status in ['approved', 'sent']]),
        total_agents=len(agents_db),
        active_agents=len([a for a in agents_db.values() if a['status'] == 'processing']),
        avg_processing_time=(
            performance_metrics['total_processing_time'] / performance_metrics['tasks_completed']
            if performance_metrics['tasks_completed'] > 0 else 0.0
        ),
        success_rate=(
            performance_metrics['tasks_completed'] / performance_metrics['tasks_created'] * 100
            if performance_metrics['tasks_created'] > 0 else 100.0
        ),
        cases_scraped_today=performance_metrics['cases_scraped'],
        scraping_speed=(
            performance_metrics['cases_scraped'] / performance_metrics['scraping_sessions']
            if performance_metrics['scraping_sessions'] > 0 else 0.0
        )
    )
    
    return stats

# ============================================================================
# MAIN - RUN SERVER
# ============================================================================

if __name__ == "__main__":
    # Run on port 8081 (vLLM uses 8000)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,  # Changed from 8080 to avoid conflicts
        log_level="info"
    )
