"""
Google ADK Agent Wrappers for Paralegal Specialist Agents
Uses the working agents from AMD_server/ADK/agents/
"""

from google.adk import LlmAgent, SequentialAgent, ParallelAgent
from .adk_llm_wrapper import get_saul_model
# Import the WORKING agents from AMD_server/ADK/agents/
from ..ADK.agents.client_communication_agent import ClientCommunicationAgent
from ..ADK.agents.records_wrangler_agent import RecordsWranglerAgent
from ..ADK.agents.legal_researcher_agent import LegalResearcherAgent  
from ..ADK.agents.evidence_sorter_agent import EvidenceSorterAgent
# Import LLM client from backend
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
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
        
        # Use the WORKING agent from AMD_server/ADK/agents/
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


# Workflow Agents using Google ADK orchestration

class ParalegalWorkflowAgent(SequentialAgent):
    """Sequential workflow using Google ADK"""
    
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
    """Parallel workflow using Google ADK"""
    
    def __init__(self):
        parallel_agents = [
            LegalResearcherAdkAgent(),
            RecordsWranglerAdkAgent()
        ]
        
        super().__init__(
            name="paralegal-parallel-workflow",
            agents=parallel_agents
        )
        
        logger.info("Initialized ParalegalParallelWorkflowAgent for parallel execution")


def get_all_adk_agents():
    """Get all ADK-wrapped paralegal agents"""
    return {
        "client-communication": ClientCommunicationAdkAgent(),
        "records-wrangler": RecordsWranglerAdkAgent(),
        "legal-researcher": LegalResearcherAdkAgent(),
        "evidence-sorter": EvidenceSorterAdkAgent(),
        "workflow-sequential": ParalegalWorkflowAgent(),
        "workflow-parallel": ParallelWorkflowAgent()
    }