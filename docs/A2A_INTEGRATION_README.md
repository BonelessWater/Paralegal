# A2A Integration for Paralegal Agents
## Google ADK Agent-to-Agent Protocol Implementation

---

## 📋 Overview

This integration enables Paralegal specialist agents to communicate via Google's Agent Development Kit (ADK) A2A protocol, allowing complex multi-agent workflows for legal case management.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Google ADK A2A Orchestrator                      │
│              (Coordinates multi-agent workflows)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│              ParalegalA2ARegistry (Local)                        │
│          (Routes messages between specialist agents)             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │               │              │
        ↓              ↓               ↓              ↓
  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ Client  │    │ Records │    │  Legal  │    │Evidence │
  │  Comm   │    │Wrangler │    │Research │    │ Sorter  │
  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
       │              │               │              │
       └──────────────┴───────────────┴──────────────┘
                       │
                       ↓
              ┌────────────────┐
              │  AMD LLM API   │
              └────────┬───────┘
                       │
                       ↓
          ┌────────────────────────┐
          │   Saul-7B-Instruct     │
          │   (Legal LLM on AMD)   │
          └────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Ensure .env is configured
cat .env | grep -E "MODEL_NAME|VLLM_BASE_URL|HUGGING_FACE_HUB_TOKEN"

# Verify AMD vLLM server is running
curl http://your-amd-server:8000/health
```

### 2. Test A2A Integration

```bash
# Run basic integration test
python backend/integrations/adk_a2a_agents.py

# Run comprehensive workflow demos
python backend/integrations/a2a_workflow_demos.py

# Test monitoring capabilities
python backend/integrations/a2a_monitoring.py
```

### 3. Expected Output

```
✅ A2A agent 'paralegal-client-communication' initialized
✅ A2A agent 'paralegal-records-wrangler' initialized
✅ A2A agent 'paralegal-legal-researcher' initialized
✅ A2A agent 'paralegal-evidence-sorter' initialized

📨 Sending test message to paralegal-client-communication agent...
✅ Response received
```

---

## 📁 File Structure

```
backend/integrations/
├── adk_a2a_agents.py          # Core A2A agent wrappers
│   ├── ParalegalA2AAgent      # Wraps individual agents
│   └── ParalegalA2ARegistry   # Routes messages between agents
│
├── a2a_workflow_demos.py      # Comprehensive workflow demonstrations
│   ├── Demo 1: Simple client intake
│   ├── Demo 2: Case research workflow
│   ├── Demo 3: Full case intake (3-agent pipeline)
│   ├── Demo 4: Parallel case analysis
│   └── Demo 5: Error handling
│
└── a2a_monitoring.py          # Observability and metrics
    ├── A2AMessageTracer       # Track message flows
    ├── A2AMetricsCollector    # Performance metrics
    └── A2AHealthMonitor       # Agent health checks
```

---

## 🎯 Agent Capabilities

### 1. Client Communication Agent
**Purpose:** Transform messy client messages into professional responses

**A2A Input:**
```json
{
  "message": "hey i was in a car accident and need help!!!"
}
```

**A2A Output:**
```json
{
  "original": "hey i was in a car accident...",
  "polished_response": "Thank you for reaching out...",
  "agent": "ClientCommunicationGuru"
}
```

### 2. Records Wrangler Agent
**Purpose:** Generate medical records requests from case descriptions

**A2A Input:**
```json
{
  "case_description": "Client went to ER after car accident, then PT..."
}
```

**A2A Output:**
```json
{
  "case_description": "Client went to ER...",
  "records_request": "Dear Medical Records Department...",
  "agent": "RecordsWrangler"
}
```

### 3. Legal Researcher Agent
**Purpose:** Provide case research and settlement guidance

**A2A Input:**
```json
{
  "injury_type": "Broken wrist from slip and fall",
  "jurisdiction": "California",
  "case_details": "Grocery store accident, clear liability"
}
```

**A2A Output:**
```json
{
  "injury_type": "Broken wrist...",
  "jurisdiction": "California",
  "research_memo": "Legal Analysis:\n1. Premises liability...",
  "agent": "LegalResearcher"
}
```

### 4. Evidence Sorter Agent
**Purpose:** Classify legal documents (OCR + classification)

**A2A Input:**
```json
{
  "file_path": "/path/to/document.pdf"
}
```

**A2A Output:**
```json
{
  "file": "/path/to/document.pdf",
  "classification": "Medical Bill - High confidence",
  "text_preview": "Invoice #12345...",
  "agent": "EvidenceSorter"
}
```

---

## 🔄 Workflow Examples

### Example 1: Simple Single-Agent Call

```python
from backend.integrations.adk_a2a_agents import ParalegalA2ARegistry

# Initialize registry
registry = ParalegalA2ARegistry()

# Create A2A message
message = {
    "sender": "orchestrator",
    "recipient": "paralegal-client-communication",
    "payload": {
        "message": "i need help with my case!!!"
    }
}

# Route to agent
response = await registry.route_message(message)

# Use response
print(response["payload"]["polished_response"])
```

### Example 2: Multi-Agent Sequential Workflow

```python
from backend.integrations.a2a_workflow_demos import A2AWorkflowOrchestrator

orchestrator = A2AWorkflowOrchestrator()

workflow = await orchestrator.execute_workflow(
    workflow_name="case_intake",
    steps=[
        {
            "agent": "paralegal-client-communication",
            "description": "Process client message",
            "input": {"message": "..."}
        },
        {
            "agent": "paralegal-legal-researcher",
            "description": "Research case value",
            "input": {"injury_type": "...", "jurisdiction": "..."}
        },
        {
            "agent": "paralegal-records-wrangler",
            "description": "Generate records requests",
            "input": {"case_description": "..."}
        }
    ]
)

print(f"Workflow completed in {workflow['total_duration_seconds']:.2f}s")
```

### Example 3: Parallel Agent Execution

```python
workflow = await orchestrator.execute_parallel_workflow(
    workflow_name="parallel_analysis",
    parallel_steps=[
        {
            "agent": "paralegal-legal-researcher",
            "description": "Research",
            "input": {...}
        },
        {
            "agent": "paralegal-records-wrangler",
            "description": "Records",
            "input": {...}
        },
        {
            "agent": "paralegal-client-communication",
            "description": "Draft update",
            "input": {...}
        }
    ]
)
# All 3 agents run simultaneously - much faster!
```

### Example 4: Agent-to-Agent Communication

Agents can call other agents directly:

```python
# Inside an agent's process_message method:
async def process_message(self, message):
    # Do initial processing
    result = self.agent.process(message["payload"])
    
    # Agent decides it needs help from another agent
    research_response = await self.call_other_agent(
        target_agent="paralegal-legal-researcher",
        payload={
            "injury_type": extracted_injury,
            "jurisdiction": "California",
            "case_details": "..."
        },
        context="Need case value estimate for client response"
    )
    
    # Use research results in final response
    return combined_response
```

---

## 📊 Monitoring and Observability

### Message Tracing

Track complete message flow across agents:

```python
from backend.integrations.a2a_monitoring import get_tracer

tracer = get_tracer()

# Start trace
trace_id = tracer.start_trace(
    "case-123",
    workflow_name="client_intake",
    initiator="user@example.com"
)

# Log messages
tracer.log_message(
    trace_id,
    sender="orchestrator",
    recipient="paralegal-client-communication",
    payload_summary="Process client message"
)

# End trace
tracer.end_trace(trace_id, status="completed")

# Export for analysis
tracer.export_trace(trace_id, "trace-case-123.json")
```

### Performance Metrics

Collect agent and workflow metrics:

```python
from backend.integrations.a2a_monitoring import get_metrics

metrics = get_metrics()

# Record agent call
metrics.record_agent_call(
    agent_name="paralegal-client-communication",
    latency_ms=150.5,
    success=True
)

# Record workflow execution
metrics.record_workflow_execution(
    workflow_name="case_intake",
    duration_seconds=2.3,
    success=True
)

# Print report
metrics.print_report()
```

**Sample Output:**
```
A2A METRICS REPORT
================================================================================

System Uptime: 0:15:32
Total Agent Calls: 47
Total Workflow Executions: 12

AGENT METRICS
--------------------------------------------------------------------------------

paralegal-client-communication:
  Calls: 15 (✓ 15 / ✗ 0)
  Success Rate: 100.0%
  Latency: avg=142.30ms, min=98ms, max=201ms

paralegal-legal-researcher:
  Calls: 12 (✓ 11 / ✗ 1)
  Success Rate: 91.7%
  Latency: avg=324.15ms, min=201ms, max=456ms

WORKFLOW METRICS
--------------------------------------------------------------------------------

case_intake:
  Executions: 5 (✓ 5 / ✗ 0)
  Success Rate: 100.0%
  Duration: avg=2.35s, min=1.87s, max=3.12s
```

### Health Monitoring

Monitor agent and system health:

```python
from backend.integrations.a2a_monitoring import get_health_monitor
from backend.APIs.AMD.llm_client import AMDLLMClient
from config.amd_config import AMDConfig

health_monitor = get_health_monitor()

# Check system health
llm_client = AMDLLMClient(AMDConfig.VLLM_BASE_URL, AMDConfig.MODEL_FOLDER)
health = await health_monitor.check_system_health(registry, llm_client)

print(f"Overall Status: {health['overall_status']}")
print(f"LLM Backend: {health['components']['llm_backend']['status']}")
print(f"Agents Available: {health['components']['agents']['total']}")
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Model Configuration
MODEL_NAME=Equall/Saul-7B-Instruct-v1
MODEL_FOLDER=saul-7b-instruct

# AMD vLLM Server
VLLM_BASE_URL=http://your-amd-server:8000

# LLM Parameters
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=500
MAX_MODEL_LEN=4096
```

### Agent Configuration

Agents automatically read from `AMDConfig` (which reads `.env`):

```python
from config.amd_config import AMDConfig

# Validate configuration
AMDConfig.validate()

# Print current config
AMDConfig.print_config()
```

---

## 🧪 Testing

### Run All Workflow Demos

```bash
cd /path/to/Paralegal
python backend/integrations/a2a_workflow_demos.py
```

This runs 5 comprehensive demos:
1. **Simple Client Intake** - Single agent processing
2. **Case Research Workflow** - Sequential 2-agent pipeline
3. **Full Case Intake** - Complete 3-agent pipeline
4. **Parallel Case Analysis** - Concurrent agent execution
5. **Error Handling** - Failure recovery demonstration

### Run Individual Tests

```bash
# Test basic A2A functionality
python backend/integrations/adk_a2a_agents.py

# Test monitoring
python backend/integrations/a2a_monitoring.py
```

### Custom Test

```python
import asyncio
from backend.integrations.adk_a2a_agents import ParalegalA2ARegistry

async def custom_test():
    registry = ParalegalA2ARegistry()
    
    message = {
        "sender": "test",
        "recipient": "paralegal-client-communication",
        "payload": {"message": "Your test message here"}
    }
    
    response = await registry.route_message(message)
    print(response["payload"])

asyncio.run(custom_test())
```

---

## 🚨 Troubleshooting

### Issue: "Cannot connect to AMD server"

**Solution:**
1. Check `VLLM_BASE_URL` in `.env`
2. Verify server is running: `curl http://your-server:8000/health`
3. Check network/firewall settings

### Issue: "Agent not found"

**Solution:**
- Ensure agent name format: `paralegal-<type>`
- Valid types: `client-communication`, `records-wrangler`, `legal-researcher`, `evidence-sorter`

### Issue: "Slow response times"

**Solution:**
1. Check AMD GPU utilization: `rocm-smi`
2. Reduce `MAX_MODEL_LEN` in `.env`
3. Lower `DEFAULT_MAX_TOKENS`
4. Enable parallel workflows for independent tasks

### Issue: "Workflow fails midway"

**Solution:**
- Check individual agent logs
- Review error in workflow result: `workflow['steps'][error_step]['output']`
- Use monitoring to trace message flow

---

## 📚 Integration with Google ADK

### Installing Google ADK (when available)

```bash
pip install google-adk
```

### Registering Agents with ADK

```python
from google_adk import A2AServer
from backend.integrations.adk_a2a_agents import ParalegalA2ARegistry

# Initialize registry
registry = ParalegalA2ARegistry()

# Create ADK server
server = A2AServer(registry=registry)

# Start A2A server
server.run(host="0.0.0.0", port=9000)
```

### ADK Orchestrator Integration

```python
from google_adk import A2AOrchestrator

# Configure orchestrator
orchestrator = A2AOrchestrator()

# Discover paralegal agents
agents = orchestrator.discover_agents(endpoint="http://localhost:9000")

# Execute workflow via ADK
result = orchestrator.execute_workflow(
    name="legal_case_intake",
    agents=["paralegal-client-communication", "paralegal-legal-researcher"],
    input_data={...}
)
```

---

## 🎓 Best Practices

### 1. Workflow Design

- **Keep agents focused:** Each agent has one clear responsibility
- **Use parallel execution:** When tasks are independent
- **Add error handling:** Always check agent response status
- **Log everything:** Use tracer and metrics for debugging

### 2. Performance Optimization

- **Batch similar requests:** Send multiple messages simultaneously
- **Cache common queries:** Store frequent research results
- **Monitor latency:** Use metrics to identify slow agents
- **Scale horizontally:** Run multiple agent instances

### 3. Error Handling

```python
response = await registry.route_message(message)

if response["metadata"]["status"] == "error":
    error_msg = response["payload"]["error"]
    # Handle error gracefully
    logger.error(f"Agent failed: {error_msg}")
else:
    # Process successful response
    result = response["payload"]
```

### 4. Monitoring in Production

```python
from backend.integrations.a2a_monitoring import (
    get_tracer,
    get_metrics,
    get_health_monitor
)

# Initialize monitoring
tracer = get_tracer()
metrics = get_metrics()
health = get_health_monitor()

# Instrument all workflows
trace_id = tracer.start_trace(...)
try:
    # Execute workflow
    result = await execute_workflow(...)
    tracer.end_trace(trace_id, "completed")
    metrics.record_workflow_execution(..., success=True)
except Exception as e:
    tracer.end_trace(trace_id, "failed", error=str(e))
    metrics.record_workflow_execution(..., success=False)
```

---

## 📞 Support

For issues or questions:
1. Check logs: `backend/integrations/*.log`
2. Run health checks: `python backend/integrations/a2a_monitoring.py`
3. Review metrics: `metrics.print_report()`
4. Check configuration: `AMDConfig.print_config()`

---

## ✅ Summary

You now have:
- ✅ **4 specialist agents** wrapped for A2A protocol
- ✅ **Agent registry** for message routing
- ✅ **Workflow orchestration** (sequential & parallel)
- ✅ **Agent-to-agent communication** (agents calling agents)
- ✅ **Comprehensive monitoring** (tracing, metrics, health)
- ✅ **5 workflow demonstrations** showing real use cases
- ✅ **Production-ready error handling** and logging

**You're ready to build complex multi-agent legal workflows! ⚖️🤖**
