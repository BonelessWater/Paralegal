"""
A2A Protocol Server - Expose Paralegal Agents via A2A
"""

from flask import Flask, request, jsonify
from backend.integrations.a2a_agent_cards import ParalegalAgentCards
from backend.integrations.adk_agent_wrappers import get_all_adk_agents
from config.amd_config import AMDConfig
import logging

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Initialize agents
AGENTS = get_all_adk_agents()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Paralegal A2A Server",
        "agents": list(AGENTS.keys())
    })


@app.route('/agents', methods=['GET'])
def list_agents():
    """Agent Discovery - List all available agents"""
    agent_cards = ParalegalAgentCards.get_all_agent_cards()
    
    return jsonify({
        "jsonrpc": "2.0",
        "result": {
            "agents": agent_cards,
            "count": len(agent_cards)
        }
    })


@app.route('/agents/<agent_id>/invoke', methods=['POST'])
def invoke_agent(agent_id: str):
    """
    Invoke agent skill (A2A Task Execution)
    
    JSON-RPC 2.0 format:
    {
        "jsonrpc": "2.0",
        "method": "invoke_skill",
        "params": {"skill": "...", "input": {...}},
        "id": "request-123"
    }
    """
    try:
        rpc_request = request.json
        
        # Get agent
        agent_key = agent_id.replace("paralegal-", "")
        agent = AGENTS.get(agent_key)
        
        if not agent:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Agent not found: {agent_id}"},
                "id": rpc_request.get("id")
            }), 404
        
        # Execute
        params = rpc_request.get("params", {})
        input_data = params.get("input", {})
        result = agent.process(input_data)
        
        return jsonify({
            "jsonrpc": "2.0",
            "result": {"output": result, "status": "completed"},
            "id": rpc_request.get("id")
        })
        
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": rpc_request.get("id", None)
        }), 500


@app.route('/.well-known/agent-cards', methods=['GET'])
def well_known_agent_cards():
    """Well-known endpoint for agent discovery"""
    return jsonify(ParalegalAgentCards.get_all_agent_cards())


if __name__ == "__main__":
    print("\nParalegal A2A Server")
    print("="*80)
    print(f"\nServer URL: http://localhost:{AMDConfig.A2A_SERVER_PORT}")
    print(f"vLLM Backend: {AMDConfig.VLLM_BASE_URL}")
    print(f"Model: {AMDConfig.MODEL_NAME}")
    print("\nEndpoints:")
    print("  • Health: http://localhost:9000/health")
    print("  • List Agents: http://localhost:9000/agents")
    print("  • Agent Cards: http://localhost:9000/.well-known/agent-cards")
    print("  • Invoke: http://localhost:9000/agents/<agent_id>/invoke\n")
    
    app.run(
        host=AMDConfig.A2A_SERVER_HOST, 
        port=AMDConfig.A2A_SERVER_PORT, 
        debug=True
    )