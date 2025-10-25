"""
Google ADK A2A Protocol Integration for Paralegal Specialist Agents
Wraps existing agents to be A2A-compatible for multi-agent orchestration
"""

from typing import Dict, Any, Optional
import logging

# Note: Install google-adk first: pip install google-adk
# from google_adk import A2AAgent, A2AMessage  # Uncomment when ADK installed

import sys
import os
# Add parent directory to path to access agents and backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

from agents.client_communication_agent import ClientCommunicationAgent
from agents.records_wrangler_agent import RecordsWranglerAgent
from agents.legal_researcher_agent import LegalResearcherAgent
from agents.evidence_sorter_agent import EvidenceSorterAgent
from backend.APIs.AMD.llm_client import AMDLLMClient
from config.amd_config import AMDConfig

logger = logging.getLogger(__name__)


class ParalegalA2AAgent:
    """
    A2A-compatible wrapper for Paralegal specialist agents
    
    This class wraps existing specialist agents to make them compatible
    with Google's Agent Development Kit (ADK) A2A protocol.
    
    Supports agent-to-agent communication: agents can call other agents
    via the registry for complex multi-step reasoning.
    
    Usage:
        # Initialize agent
        agent = ParalegalA2AAgent("client-communication")
        
        # Process A2A message
        response = await agent.process_message(incoming_message)
    """
    
    AGENT_TYPES = {
        "client-communication": ClientCommunicationAgent,
        "records-wrangler": RecordsWranglerAgent,
        "legal-researcher": LegalResearcherAgent,
        "evidence-sorter": EvidenceSorterAgent
    }
    
    def __init__(self, agent_type: str, registry=None):
        """
        Initialize A2A-wrapped agent
        
        Args:
            agent_type: One of ["client-communication", "records-wrangler", 
                               "legal-researcher", "evidence-sorter"]
            registry: Optional ParalegalA2ARegistry for agent-to-agent calls
        """
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(
                f"Invalid agent_type '{agent_type}'. "
                f"Must be one of {list(self.AGENT_TYPES.keys())}"
            )
        
        self.agent_type = agent_type
        self.name = f"paralegal-{agent_type}"
        self.registry = registry  # For agent-to-agent communication
        
        # Initialize AMD LLM client (reads from .env via AMDConfig)
        self.llm_client = AMDLLMClient(
            base_url=AMDConfig.VLLM_BASE_URL,
            model=AMDConfig.MODEL_FOLDER
        )
        
        # Initialize specialist agent
        agent_class = self.AGENT_TYPES[agent_type]
        self.agent = agent_class(self.llm_client)
        
        logger.info(
            f"Initialized A2A agent '{self.name}' with model {AMDConfig.MODEL_NAME}"
        )
    
    async def call_other_agent(
        self,
        target_agent: str,
        payload: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Agent-to-agent communication: this agent calls another agent
        
        This enables complex multi-step reasoning where agents collaborate.
        For example:
          - Client Communication agent calls Legal Researcher for case value
          - Records Wrangler calls Evidence Sorter to classify documents
          - Legal Researcher calls Records Wrangler for supporting documents
        
        Args:
            target_agent: Name of agent to call (e.g., "paralegal-legal-researcher")
            payload: Input data for target agent
            context: Optional context explaining why this call is being made
        
        Returns:
            Response from target agent
        
        Raises:
            ValueError: If no registry available for agent-to-agent calls
        """
        if not self.registry:
            raise ValueError(
                f"Agent '{self.name}' cannot call other agents - no registry configured"
            )
        
        logger.info(
            f"Agent '{self.name}' calling '{target_agent}' - Context: {context}"
        )
        
        # Create A2A message from this agent to target agent
        message = {
            "sender": self.name,
            "recipient": target_agent,
            "payload": payload,
            "metadata": {
                "agent_to_agent": True,
                "context": context,
                "originating_agent": self.name
            }
        }
        
        # Route through registry
        response = await self.registry.route_message(message)
        
        logger.info(
            f"Agent '{self.name}' received response from '{target_agent}'"
        )
        
        return response
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming A2A message and return response
        
        Args:
            message: A2A message dict with structure:
                {
                    "sender": "orchestrator",
                    "recipient": "paralegal-client-communication",
                    "payload": { ... input data ... },
                    "metadata": { ... optional metadata ... }
                }
        
        Returns:
            A2A response message dict:
                {
                    "sender": "paralegal-client-communication",
                    "recipient": "orchestrator",
                    "payload": { ... agent result ... },
                    "metadata": {
                        "model": "Equall/Saul-7B-Instruct-v1",
                        "agent_type": "ClientCommunicationAgent",
                        "status": "success"
                    }
                }
        """
        try:
            # Extract input from A2A message
            input_data = message.get("payload", {})
            sender = message.get("sender", "unknown")
            
            logger.info(
                f"Processing A2A message from '{sender}' with agent '{self.name}'"
            )
            
            # Call specialist agent
            result = self.agent.process(input_data)
            
            # Wrap result in A2A message format
            response = {
                "sender": self.name,
                "recipient": sender,
                "payload": result,
                "metadata": {
                    "model": AMDConfig.MODEL_NAME,
                    "agent_type": self.agent.__class__.__name__,
                    "status": "success",
                    "vllm_endpoint": AMDConfig.VLLM_BASE_URL
                }
            }
            
            logger.info(f"Successfully processed message with agent '{self.name}'")
            return response
            
        except Exception as e:
            logger.error(f"Error processing A2A message: {e}", exc_info=True)
            
            # Return error response in A2A format
            return {
                "sender": self.name,
                "recipient": message.get("sender", "unknown"),
                "payload": {
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                "metadata": {
                    "status": "error",
                    "agent_type": self.agent.__class__.__name__
                }
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return agent capabilities for A2A discovery
        
        Returns:
            Dict describing agent capabilities
        """
        capabilities = {
            "client-communication": {
                "description": "Translates messy client messages into professional legal responses",
                "input_format": {"message": "str"},
                "output_format": {"original": "str", "polished_response": "str"},
                "use_cases": ["client intake", "email drafting", "communication polishing"]
            },
            "records-wrangler": {
                "description": "Organizes, categorizes, and indexes legal documents",
                "input_format": {"document": "str", "context": "str (optional)"},
                "output_format": {"summary": "str", "category": "str", "key_points": "list"},
                "use_cases": ["document organization", "case file management", "indexing"]
            },
            "legal-researcher": {
                "description": "Searches case law, statutes, and legal precedents",
                "input_format": {"query": "str", "jurisdiction": "str (optional)"},
                "output_format": {"findings": "str", "citations": "list", "relevance": "str"},
                "use_cases": ["legal research", "precedent finding", "statute lookup"]
            },
            "evidence-sorter": {
                "description": "Analyzes and categorizes evidence for case preparation",
                "input_format": {"evidence": "str", "case_type": "str (optional)"},
                "output_format": {"category": "str", "relevance": "str", "notes": "str"},
                "use_cases": ["evidence analysis", "case preparation", "discovery organization"]
            }
        }
        
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "model": AMDConfig.MODEL_NAME,
            "capabilities": capabilities.get(self.agent_type, {}),
            "status": "active",
            "version": "1.0.0"
        }


class ParalegalA2ARegistry:
    """
    Registry for all Paralegal A2A agents
    Manages agent lifecycle and discovery
    """
    
    def __init__(self):
        """Initialize registry with all specialist agents"""
        self.agents = {}
        
        # Register all specialist agents (with registry reference for agent-to-agent calls)
        for agent_type in ParalegalA2AAgent.AGENT_TYPES.keys():
            try:
                agent = ParalegalA2AAgent(agent_type, registry=self)
                self.agents[agent.name] = agent
                logger.info(f"Registered agent: {agent.name}")
            except Exception as e:
                logger.error(f"Failed to register agent '{agent_type}': {e}")
    
    def get_agent(self, agent_name: str) -> Optional[ParalegalA2AAgent]:
        """Get agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents with their capabilities"""
        return {
            name: agent.get_capabilities()
            for name, agent in self.agents.items()
        }
    
    async def route_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route A2A message to appropriate agent
        
        Args:
            message: A2A message with recipient field
        
        Returns:
            A2A response from agent
        """
        recipient = message.get("recipient")
        
        if not recipient:
            return {
                "sender": "registry",
                "recipient": message.get("sender", "unknown"),
                "payload": {"error": "No recipient specified"},
                "metadata": {"status": "error"}
            }
        
        agent = self.get_agent(recipient)
        
        if not agent:
            return {
                "sender": "registry",
                "recipient": message.get("sender", "unknown"),
                "payload": {
                    "error": f"Agent '{recipient}' not found",
                    "available_agents": list(self.agents.keys())
                },
                "metadata": {"status": "error"}
            }
        
        return await agent.process_message(message)
    
    def serve(self, host: str = "0.0.0.0", port: int = 9000):
        """
        Start A2A server (placeholder for actual ADK integration)
        
        In production, this would integrate with Google ADK's serving infrastructure.
        For now, this is a placeholder showing the interface.
        
        Args:
            host: Server host
            port: Server port
        """
        logger.info(f"Starting A2A registry server on {host}:{port}")
        logger.info(f"Registered agents: {list(self.agents.keys())}")
        logger.warning(
            "serve() is a placeholder. Integrate with actual Google ADK server when available."
        )
        
        # TODO: Integrate with Google ADK serving infrastructure
        # Example:
        # from google_adk import A2AServer
        # server = A2AServer(registry=self)
        # server.run(host=host, port=port)


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validate configuration
    try:
        AMDConfig.validate()
        AMDConfig.print_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
    
    # Initialize registry
    print("\n" + "="*70)
    print("Initializing Paralegal A2A Registry")
    print("="*70)
    
    registry = ParalegalA2ARegistry()
    
    # List agents
    print("\n📋 Registered Agents:")
    for name, capabilities in registry.list_agents().items():
        print(f"\n  • {name}")
        print(f"    Description: {capabilities['capabilities'].get('description', 'N/A')}")
    
    # Test routing
    print("\n" + "="*70)
    print("Testing A2A Message Routing")
    print("="*70)
    
    async def test_routing():
        # Test message to client communication agent
        test_message = {
            "sender": "test-orchestrator",
            "recipient": "paralegal-client-communication",
            "payload": {
                "message": "hey i need help with my case asap!!!"
            },
            "metadata": {
                "request_id": "test-123"
            }
        }
        
        print("\n📨 Sending test message to paralegal-client-communication agent...")
        response = await registry.route_message(test_message)
        
        print("\n✅ Response received:")
        print(f"  Status: {response['metadata'].get('status')}")
        print(f"  Agent: {response['metadata'].get('agent_type')}")
        print(f"  Model: {response['metadata'].get('model')}")
        if response['metadata'].get('status') == 'success':
            print(f"\n  Polished Response Preview:")
            polished = response['payload'].get('polished_response', '')
            print(f"  {polished[:200]}..." if len(polished) > 200 else f"  {polished}")
    
    # Run async test
    asyncio.run(test_routing())
    
    print("\n" + "="*70)
    print("✅ A2A Integration Test Complete")
    print("="*70)
    print("\nNext steps:")
    print("1. Install Google ADK: pip install google-adk")
    print("2. Uncomment ADK imports in this file")
    print("3. Integrate serve() with ADK server infrastructure")
    print("4. Deploy to production with proper monitoring")
