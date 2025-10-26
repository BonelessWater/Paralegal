"""
Enhanced A2A Server with ADK Integration
Uses working agents from AMD_server/ADK/agents/
"""

from flask import Flask, request, jsonify
from .adk_agent_wrapper import get_all_adk_agents
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from config.amd_config import AMDConfig
except ImportError:
    class AMDConfig:
        VLLM_BASE_URL = "http://localhost:8000"
        MODEL_FOLDER = "saul-7b-instruct-v1"
        MODEL_NAME = "Saul-7B-Instruct-v1"
import logging
import traceback

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Global agents variable
AGENTS = None

def init_agents():
    """Initialize ADK-wrapped agents"""
    global AGENTS
    try:
        print("🔄 Initializing ADK agents...")
        AGENTS = get_all_adk_agents()
        print(f"✅ Successfully initialized {len(AGENTS)} ADK agents:")
        for name, agent in AGENTS.items():
            print(f"   • {name}: {agent.__class__.__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        traceback.print_exc()
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check with full stack info"""
    return jsonify({
        "status": "healthy",
        "service": "Paralegal ADK+A2A Server",
        "agents_initialized": AGENTS is not None,
        "agents_count": len(AGENTS) if AGENTS else 0,
        "model": AMDConfig.MODEL_NAME,
        "vllm_url": AMDConfig.VLLM_BASE_URL,
        "integration_stack": [
            "HuggingFace Saul-7B-Instruct-v1",
            "AMD vLLM Server",
            "Google ADK Framework", 
            "A2A Protocol",
            "4 Paralegal Agents"
        ]
    })


@app.route('/agents', methods=['GET'])
def list_agents():
    """List all available agents via A2A protocol"""
    if not AGENTS:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Agents not initialized"}
        }), 500
    
    agent_cards = []
    for agent_key, agent in AGENTS.items():
        card = {
            "agent_id": f"paralegal-{agent_key}",
            "name": f"Paralegal {agent_key.replace('-', ' ').title()}",
            "description": f"ADK-wrapped {agent_key} using Saul-7B model",
            "version": "1.0.0",
            "capabilities": [agent_key, "legal-assistance", "saul-7b-powered"],
            "skills": [
                {
                    "name": "process",
                    "description": f"Process {agent_key} requests using Saul-7B",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "context": {"type": "object"}
                        }
                    }
                }
            ],
            "connection": {
                "protocol": "a2a",
                "endpoint": f"{AMDConfig.A2A_SERVER_URL}/agents/paralegal-{agent_key}",
                "transport": ["http"]
            },
            "metadata": {
                "provider": "Paralegal AI System",
                "model": "Saul-7B-Instruct-v1",
                "domain": "legal",
                "integration": "ADK+A2A",
                "backend": "AMD vLLM"
            }
        }
        agent_cards.append(card)
    
    return jsonify({
        "jsonrpc": "2.0",
        "result": {
            "agents": agent_cards,
            "count": len(agent_cards),
            "integration": "HuggingFace → AMD vLLM → Google ADK → A2A"
        }
    })


@app.route('/agents/<agent_id>/invoke', methods=['POST'])
def invoke_agent(agent_id: str):
    """Invoke agent via A2A JSON-RPC 2.0"""
    if not AGENTS:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Agents not initialized"}
        }), 500
    
    try:
        rpc_request = request.json
        
        # Map A2A agent_id to internal key
        agent_mapping = {
            "paralegal-client-communication": "client-communication",
            "paralegal-records-wrangler": "records-wrangler",
            "paralegal-legal-researcher": "legal-researcher", 
            "paralegal-evidence-sorter": "evidence-sorter",
            "paralegal-workflow-sequential": "workflow-sequential",
            "paralegal-workflow-parallel": "workflow-parallel"
        }
        
        agent_key = agent_mapping.get(agent_id)
        agent = AGENTS.get(agent_key) if agent_key else None
        
        if not agent:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Agent not found: {agent_id}"},
                "id": rpc_request.get("id")
            }), 404
        
        # Execute via ADK agent
        params = rpc_request.get("params", {})
        input_data = params.get("input", {})
        
        print(f"🚀 Invoking {agent_id} with input: {list(input_data.keys())}")
        result = agent.process(input_data)
        
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "output": result,
                "status": "completed",
                "agent": agent_id,
                "integration": "ADK+A2A",
                "model": "Saul-7B-Instruct-v1"
            },
            "id": rpc_request.get("id")
        })
        
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        traceback.print_exc()
        return jsonify({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)},
            "id": rpc_request.get("id", None)
        }), 500


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PARALEGAL ADK+A2A INTEGRATION SERVER")
    print("="*80)
    print("🔗 Complete Integration Stack:")
    print("   HuggingFace Saul-7B → AMD vLLM → Google ADK → A2A Protocol → 4 Agents")
    print(f"\n🌐 Server: http://localhost:{AMDConfig.A2A_SERVER_PORT}")
    print(f"🔧 vLLM Backend: {AMDConfig.VLLM_BASE_URL}")
    print(f"🤖 Model: {AMDConfig.MODEL_NAME}")
    
    # Initialize agents
    print(f"\n{'='*50}")
    if init_agents():
        print("🚀 Server ready for ADK+A2A requests!")
    else:
        print("❌ Server starting with agent initialization errors!")
    print("="*80)
    
    logging.basicConfig(level=logging.INFO)
    app.run(
        host=AMDConfig.A2A_SERVER_HOST,
        port=AMDConfig.A2A_SERVER_PORT,
        debug=True
    )