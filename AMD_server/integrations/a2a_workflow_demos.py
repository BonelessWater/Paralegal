"""
A2A Workflow Demonstrations
Complete multi-agent scenarios showing realistic paralegal workflows via A2A protocol

This module demonstrates:
1. Simple single-agent workflows
2. Multi-agent chained workflows (client intake → research → records)
3. Parallel agent execution (multiple agents processing simultaneously)
4. Complex orchestration patterns (conditional routing, error handling)
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import sys
import os

# Add parent directory to path to access integrations and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

from integrations.adk_a2a_agents import ParalegalA2ARegistry
from config.amd_config import AMDConfig

logger = logging.getLogger(__name__)


class A2AWorkflowOrchestrator:
    """
    Orchestrates multi-agent workflows using A2A protocol
    
    This demonstrates how Google ADK would coordinate multiple specialist agents
    for complex legal workflows.
    """
    
    def __init__(self):
        """Initialize orchestrator with agent registry"""
        self.registry = ParalegalA2ARegistry()
        self.workflow_history = []
        logger.info("A2A Workflow Orchestrator initialized")
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a multi-step workflow
        
        Args:
            workflow_name: Name of workflow for logging
            steps: List of workflow steps, each with:
                - agent: Agent name to call
                - input: Input data for agent
                - description: Human-readable step description
        
        Returns:
            Complete workflow results with all step outputs
        """
        logger.info(f"Starting workflow: {workflow_name}")
        start_time = datetime.now()
        
        results = {
            "workflow_name": workflow_name,
            "start_time": start_time.isoformat(),
            "steps": [],
            "status": "running"
        }
        
        try:
            for idx, step in enumerate(steps, 1):
                step_start = datetime.now()
                logger.info(f"Step {idx}/{len(steps)}: {step['description']}")
                
                # Create A2A message
                message = {
                    "sender": "orchestrator",
                    "recipient": step["agent"],
                    "payload": step["input"],
                    "metadata": {
                        "workflow": workflow_name,
                        "step": idx,
                        "description": step["description"]
                    }
                }
                
                # Route to agent
                response = await self.registry.route_message(message)
                
                step_duration = (datetime.now() - step_start).total_seconds()
                
                # Record step result
                step_result = {
                    "step_number": idx,
                    "description": step["description"],
                    "agent": step["agent"],
                    "input": step["input"],
                    "output": response["payload"],
                    "status": response["metadata"].get("status"),
                    "duration_seconds": step_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                results["steps"].append(step_result)
                
                # Check for errors
                if response["metadata"].get("status") == "error":
                    logger.error(f"Step {idx} failed: {response['payload'].get('error')}")
                    results["status"] = "failed"
                    results["error_step"] = idx
                    break
            
            # Workflow completed successfully
            if results["status"] == "running":
                results["status"] = "completed"
            
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["total_duration_seconds"] = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Workflow '{workflow_name}' {results['status']} "
                f"in {results['total_duration_seconds']:.2f}s"
            )
            
            # Store in history
            self.workflow_history.append(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            return results
    
    async def execute_parallel_workflow(
        self,
        workflow_name: str,
        parallel_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel
        
        Args:
            workflow_name: Name of workflow
            parallel_steps: List of steps to execute simultaneously
        
        Returns:
            Results from all parallel executions
        """
        logger.info(f"Starting parallel workflow: {workflow_name}")
        start_time = datetime.now()
        
        # Create messages for all agents
        messages = []
        for step in parallel_steps:
            message = {
                "sender": "orchestrator",
                "recipient": step["agent"],
                "payload": step["input"],
                "metadata": {
                    "workflow": workflow_name,
                    "description": step["description"],
                    "parallel": True
                }
            }
            messages.append((step, message))
        
        # Execute all in parallel
        tasks = [
            self.registry.route_message(msg)
            for _, msg in messages
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        results = {
            "workflow_name": workflow_name,
            "start_time": start_time.isoformat(),
            "execution_mode": "parallel",
            "steps": [],
            "status": "completed"
        }
        
        for (step, _), response in zip(messages, responses):
            if isinstance(response, Exception):
                step_result = {
                    "agent": step["agent"],
                    "description": step["description"],
                    "status": "error",
                    "error": str(response)
                }
                results["status"] = "partial_failure"
            else:
                step_result = {
                    "agent": step["agent"],
                    "description": step["description"],
                    "input": step["input"],
                    "output": response["payload"],
                    "status": response["metadata"].get("status")
                }
            
            results["steps"].append(step_result)
        
        end_time = datetime.now()
        results["end_time"] = end_time.isoformat()
        results["total_duration_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Parallel workflow '{workflow_name}' completed "
            f"in {results['total_duration_seconds']:.2f}s"
        )
        
        self.workflow_history.append(results)
        return results


# ============================================================================
# WORKFLOW SCENARIOS
# ============================================================================

async def demo_1_simple_client_intake():
    """
    Scenario 1: Simple Client Intake
    Single agent processes messy client message
    """
    print("\n" + "="*80)
    print("DEMO 1: Simple Client Intake (Single Agent)")
    print("="*80)
    
    orchestrator = A2AWorkflowOrchestrator()
    
    workflow = await orchestrator.execute_workflow(
        workflow_name="simple_client_intake",
        steps=[
            {
                "agent": "paralegal-client-communication",
                "description": "Transform messy client message into professional response",
                "input": {
                    "message": """hey i was in a car accident last week and my neck really hurts 
                    and the insurance company is being really difficult they wont return my calls 
                    what should i do??? im freaking out here"""
                }
            }
        ]
    )
    
    print("\n📋 Workflow Results:")
    print(f"Status: {workflow['status']}")
    print(f"Duration: {workflow['total_duration_seconds']:.2f}s")
    print("\n📨 Original Message:")
    print(workflow['steps'][0]['input']['message'])
    print("\n✅ Polished Response:")
    print(workflow['steps'][0]['output']['polished_response'])
    
    return workflow


async def demo_2_case_research_workflow():
    """
    Scenario 2: Case Research Workflow
    Client intake → Legal research
    """
    print("\n" + "="*80)
    print("DEMO 2: Case Research Workflow (Sequential Multi-Agent)")
    print("="*80)
    
    orchestrator = A2AWorkflowOrchestrator()
    
    workflow = await orchestrator.execute_workflow(
        workflow_name="case_research_workflow",
        steps=[
            {
                "agent": "paralegal-client-communication",
                "description": "Process initial client inquiry",
                "input": {
                    "message": "I slipped and fell at the grocery store 3 days ago. "
                               "Broke my wrist. Store says not their fault. What can I do?"
                }
            },
            {
                "agent": "paralegal-legal-researcher",
                "description": "Research slip-and-fall case precedents",
                "input": {
                    "injury_type": "Broken wrist from slip and fall",
                    "jurisdiction": "California",
                    "case_details": "Grocery store accident, store denies liability"
                }
            }
        ]
    )
    
    print("\n📋 Workflow Results:")
    print(f"Status: {workflow['status']}")
    print(f"Duration: {workflow['total_duration_seconds']:.2f}s")
    print(f"Steps completed: {len(workflow['steps'])}")
    
    for step in workflow['steps']:
        print(f"\n{'='*80}")
        print(f"Step {step['step_number']}: {step['description']}")
        print(f"Agent: {step['agent']}")
        print(f"Duration: {step['duration_seconds']:.2f}s")
        print(f"\n Output preview:")
        
        if 'polished_response' in step['output']:
            print(step['output']['polished_response'][:300] + "...")
        elif 'research_memo' in step['output']:
            print(step['output']['research_memo'][:300] + "...")
    
    return workflow


async def demo_3_full_case_intake():
    """
    Scenario 3: Complete Case Intake
    Client communication → Legal research → Medical records request
    """
    print("\n" + "="*80)
    print("DEMO 3: Full Case Intake (3-Agent Sequential Pipeline)")
    print("="*80)
    
    orchestrator = A2AWorkflowOrchestrator()
    
    workflow = await orchestrator.execute_workflow(
        workflow_name="full_case_intake",
        steps=[
            {
                "agent": "paralegal-client-communication",
                "description": "Process client's initial case description",
                "input": {
                    "message": """My name is Sarah. I was rear-ended at a red light 2 weeks ago. 
                    Went to ER that night, then saw my doctor twice and now doing PT. 
                    Other driver admitted fault but their insurance is lowballing me. 
                    I have back pain, headaches, can't work. Help!!!"""
                }
            },
            {
                "agent": "paralegal-legal-researcher",
                "description": "Research rear-end collision case value",
                "input": {
                    "injury_type": "Back pain and headaches from rear-end collision",
                    "jurisdiction": "Florida",
                    "case_details": "Clear liability (other driver admitted fault), ER visit, "
                                   "ongoing treatment (PT), lost wages"
                }
            },
            {
                "agent": "paralegal-records-wrangler",
                "description": "Generate medical records requests",
                "input": {
                    "case_description": """Client: Sarah
                    Accident: Rear-end collision 2 weeks ago
                    Treatment: ER visit same day, 2 follow-up visits with primary doctor, 
                              ongoing physical therapy
                    Complaints: Back pain, headaches, unable to work"""
                }
            }
        ]
    )
    
    print("\n📋 Workflow Results:")
    print(f"Status: {workflow['status']}")
    print(f"Total Duration: {workflow['total_duration_seconds']:.2f}s")
    print(f"Steps completed: {len(workflow['steps'])}/3")
    
    for step in workflow['steps']:
        print(f"\n{'='*80}")
        print(f"✓ Step {step['step_number']}: {step['description']}")
        print(f"  Agent: {step['agent']}")
        print(f"  Duration: {step['duration_seconds']:.2f}s")
    
    print("\n" + "="*80)
    print("WORKFLOW COMPLETE - All case intake tasks finished!")
    print("="*80)
    
    return workflow


async def demo_4_parallel_case_analysis():
    """
    Scenario 4: Parallel Case Analysis
    Multiple agents analyze different aspects simultaneously
    """
    print("\n" + "="*80)
    print("DEMO 4: Parallel Case Analysis (Concurrent Agent Execution)")
    print("="*80)
    
    orchestrator = A2AWorkflowOrchestrator()
    
    case_details = {
        "client": "John Doe",
        "incident": "Motorcycle accident with commercial truck",
        "injuries": "Multiple fractures, head injury",
        "treatment": "Hospital stay, surgery, ongoing rehab"
    }
    
    workflow = await orchestrator.execute_parallel_workflow(
        workflow_name="parallel_case_analysis",
        parallel_steps=[
            {
                "agent": "paralegal-legal-researcher",
                "description": "Research case precedents for commercial vehicle accidents",
                "input": {
                    "injury_type": "Multiple fractures and head injury from motorcycle accident",
                    "jurisdiction": "Texas",
                    "case_details": "Commercial truck involved, severe injuries, surgery required"
                }
            },
            {
                "agent": "paralegal-records-wrangler",
                "description": "Draft medical records requests",
                "input": {
                    "case_description": f"""Client: {case_details['client']}
                    Incident: {case_details['incident']}
                    Injuries: {case_details['injuries']}
                    Treatment: {case_details['treatment']}"""
                }
            },
            {
                "agent": "paralegal-client-communication",
                "description": "Draft client update email",
                "input": {
                    "message": "Need to send John an update - case looking strong, "
                               "waiting on medical records, will have settlement estimate soon"
                }
            }
        ]
    )
    
    print("\n📋 Parallel Workflow Results:")
    print(f"Status: {workflow['status']}")
    print(f"Total Duration: {workflow['total_duration_seconds']:.2f}s")
    print(f"Agents executed: {len(workflow['steps'])}")
    print("\n💡 All agents ran simultaneously - much faster than sequential!")
    
    for step in workflow['steps']:
        print(f"\n{'='*80}")
        print(f"✓ {step['description']}")
        print(f"  Agent: {step['agent']}")
        print(f"  Status: {step['status']}")
    
    return workflow


async def demo_5_error_handling():
    """
    Scenario 5: Error Handling
    Demonstrate workflow behavior when an agent fails
    """
    print("\n" + "="*80)
    print("DEMO 5: Error Handling (Agent Failure Recovery)")
    print("="*80)
    
    orchestrator = A2AWorkflowOrchestrator()
    
    workflow = await orchestrator.execute_workflow(
        workflow_name="error_handling_demo",
        steps=[
            {
                "agent": "paralegal-client-communication",
                "description": "Process valid client message",
                "input": {
                    "message": "I need help with my case"
                }
            },
            {
                "agent": "paralegal-nonexistent-agent",  # Invalid agent!
                "description": "Try to call non-existent agent (will fail)",
                "input": {
                    "some_data": "test"
                }
            },
            {
                "agent": "paralegal-legal-researcher",
                "description": "This step won't execute due to previous failure",
                "input": {
                    "injury_type": "Test",
                    "jurisdiction": "Test",
                    "case_details": "Test"
                }
            }
        ]
    )
    
    print("\n📋 Workflow Results:")
    print(f"Status: {workflow['status']}")
    print(f"Steps executed: {len(workflow['steps'])}/3")
    
    if workflow['status'] == 'failed':
        print(f"❌ Workflow failed at step {workflow.get('error_step')}")
        failed_step = workflow['steps'][workflow['error_step'] - 1]
        print(f"   Error: {failed_step['output'].get('error')}")
        print("\n💡 Orchestrator detected failure and stopped execution")
    
    return workflow


# ============================================================================
# MAIN DEMO RUNNER
# ============================================================================

async def run_all_demos():
    """Run all workflow demonstrations"""
    
    print("\n" + "="*80)
    print("A2A WORKFLOW DEMONSTRATIONS")
    print("Paralegal Specialist Agents + Google ADK A2A Protocol")
    print("="*80)
    
    # Validate configuration
    print("\n📋 Validating Configuration...")
    try:
        AMDConfig.validate()
        print("✅ Configuration valid")
        AMDConfig.print_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease configure .env file before running demos")
        return
    
    # Run demos
    demos = [
        ("Demo 1: Simple Client Intake", demo_1_simple_client_intake),
        ("Demo 2: Case Research Workflow", demo_2_case_research_workflow),
        ("Demo 3: Full Case Intake", demo_3_full_case_intake),
        ("Demo 4: Parallel Case Analysis", demo_4_parallel_case_analysis),
        ("Demo 5: Error Handling", demo_5_error_handling),
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            result = await demo_func()
            results[demo_name] = result
            
            # Pause between demos
            print("\n⏸️  Press Enter to continue to next demo...")
            input()
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.error(f"Demo error: {e}", exc_info=True)
    
    # Summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    
    for demo_name, result in results.items():
        status_icon = "✅" if result['status'] == 'completed' else "❌"
        duration = result.get('total_duration_seconds', 0)
        print(f"{status_icon} {demo_name}: {result['status']} ({duration:.2f}s)")
    
    print("\n" + "="*80)
    print("All demos completed!")
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              A2A WORKFLOW DEMONSTRATIONS FOR PARALEGAL AGENTS              ║
║                                                                            ║
║  This demo showcases realistic legal workflows using Google ADK A2A        ║
║  protocol to orchestrate multiple specialist agents.                      ║
║                                                                            ║
║  Requirements:                                                             ║
║   • AMD vLLM server running with Saul-7B model                            ║
║   • .env configured with VLLM_BASE_URL and model settings                 ║
║   • Network connectivity to vLLM endpoint                                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run all demonstrations
    asyncio.run(run_all_demos())
