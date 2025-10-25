"""
Google ADK Agent Wrappers for Paralegal Specialist Agents
Wraps existing agents as ADK LlmAgents
"""

from google.adk import LlmAgent, SequentialAgent, ParallelAgent
from backend.integrations.adk_llm_wrapper import get_saul_model
from AMD_server.agents.client_communication_agent import ClientCommunicationAgent
from AMD_server.agents.records_wrangler_agent import RecordsWranglerAgent
from AMD_server.agents.legal_researcher_agent import LegalResearcherAgent
from AMD_server.agents.evidence_sorter_agent import EvidenceSorterAgent
from backend.APIs.AMD.llm_client import AMDLLMClient
from config.amd_config import AMDConfig
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

    
class ClientCommunicationAdkAgent(LlmAgent):
    """ADK wrapper for Client Communication Agent"""
    
    def __init__(self):
        model = get_saul_model()
        super().__init__(
            name="client-communication",
            model=model,
            system_prompt="""You are a compassionate legal assistant helping clients with personal injury cases. 
Transform messy client messages into professional, empathetic responses. 
Keep responses under 200 words and provide clear next steps."""
        )
        
        # Keep reference to original agent for complex operations
        self.original_agent = ClientCommunicationAgent(
            AMDLLMClient(AMDConfig.VLLM_BASE_URL, AMDConfig.MODEL_FOLDER)
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process client communication request"""
        return self.original_agent.process(input_data)


class RecordsWranglerAdkAgent(LlmAgent):
    """ADK wrapper for Records Wrangler Agent"""
    
    def __init__(self):
        model = get_saul_model()
        super().__init__(
            name="records-wrangler",
            model=model,
            system_prompt="""You are a medical records coordinator for a law firm.
Generate HIPAA-compliant medical records requests from case descriptions.
Include all necessary legal language and provider information."""
        )
        
        self.original_agent = RecordsWranglerAgent(
            AMDLLMClient(AMDConfig.VLLM_BASE_URL, AMDConfig.MODEL_FOLDER)
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate medical records request"""
        return self.original_agent.process(input_data)


class LegalResearcherAdkAgent(LlmAgent):
    """ADK wrapper for Legal Researcher Agent"""
    
    def __init__(self):
        model = get_saul_model()
        super().__init__(
            name="legal-researcher",
            model=model,
            system_prompt="""You are a legal research specialist focused on personal injury law.
Provide relevant case law, settlement guidance, and legal strategies.
Use factual, precise language with temperature 0.5 for accuracy.""",
            temperature=0.5
        )
        
        self.original_agent = LegalResearcherAgent(
            AMDLLMClient(AMDConfig.VLLM_BASE_URL, AMDConfig.MODEL_FOLDER)
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct legal research"""
        return self.original_agent.process(input_data)


class EvidenceSorterAdkAgent(LlmAgent):
    """ADK wrapper for Evidence Sorter Agent"""
    
    def __init__(self):
        model = get_saul_model()
        super().__init__(
            name="evidence-sorter",
            model=model,
            system_prompt="""You are a document classification specialist for legal cases.
Classify documents by type (medical records, police reports, correspondence, etc.).
Use consistent categorization with temperature 0.3 for predictable results.""",
            temperature=0.3
        )
        
        self.original_agent = EvidenceSorterAgent(
            AMDLLMClient(AMDConfig.VLLM_BASE_URL, AMDConfig.MODEL_FOLDER)
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify evidence documents"""
        return self.original_agent.process(input_data)


# Workflow Agents

class ParalegalWorkflowAgent(SequentialAgent):
    """
    Sequential workflow agent for complete case intake
    Uses Google ADK's SequentialAgent for orchestration
    """
    
    def __init__(self):
        agents = [
            ClientCommunicationAdkAgent(),
            LegalResearcherAdkAgent(),
            RecordsWranglerAdkAgent(),
            EvidenceSorterAdkAgent()
        ]
        
        super().__init__(
            name="paralegal-workflow",
            agents=agents
        )
        
        logger.info("Initialized ParalegalWorkflowAgent with 4 sequential agents")


class ParalegalParallelWorkflowAgent(ParallelAgent):
    """
    Parallel workflow agent for faster processing
    Research and records requests can run simultaneously
    """
    
    def __init__(self):
        # Research and records don't depend on each other
        parallel_agents = [
            LegalResearcherAdkAgent(),
            RecordsWranglerAdkAgent()
        ]
        
        super().__init__(
            name="paralegal-parallel-workflow",
            agents=parallel_agents
        )
        
        logger.info("Initialized ParalegalParallelWorkflowAgent for parallel execution")


# Convenience function
def get_all_adk_agents():
    """Get all ADK-wrapped paralegal agents"""
    return {
        "client-communication": ClientCommunicationAdkAgent(),
        "records-wrangler": RecordsWranglerAdkAgent(),
        "legal-researcher": LegalResearcherAdkAgent(),
        "evidence-sorter": EvidenceSorterAdkAgent(),
        "workflow-sequential": ParalegalWorkflowAgent(),
        "workflow-parallel": ParalegalParallelWorkflowAgent()
    }