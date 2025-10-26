"""
Test Script for Multi-Stage Synthesis Pipeline

This script tests the new 4-stage synthesis architecture in multi_agent_researcher.py

Run on AMD server:
    cd ~/Paralegal/AMD_server/agents
    python test_multi_stage_synthesis.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm_client import AMDLLMClient
from multi_agent_researcher import MultiAgentLegalResearcher, AgentFinding, AgentRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_findings():
    """Create mock agent findings for testing"""
    findings = []
    
    # Mock Case Analyst findings
    findings.append(AgentFinding(
        agent_role=AgentRole.CASE_ANALYST,
        cycle=1,
        case_name="Smith v. Grocery Store, Inc.",
        finding="""Key Facts: Plaintiff slipped on wet floor in produce section. No warning sign present. 
        Broken wrist injury requiring surgery. Store employees knew of spill for 15 minutes before incident.
        
        Holding: Store liable under premises liability theory. Duty to warn of known hazards.
        
        Reasoning: Constructive notice established through employee knowledge. Failure to warn constitutes breach.
        Store's actual knowledge distinguishes from other slip-and-fall cases requiring showing of temporal notice.""",
        confidence=0.85,
        supporting_text="In Smith, the court emphasized actual knowledge..."
    ))
    
    findings.append(AgentFinding(
        agent_role=AgentRole.CASE_ANALYST,
        cycle=1,
        case_name="Jones v. Supermarket Chain",
        finding="""Key Facts: Plaintiff fell on spilled liquid in aisle. Warning cone placed but plaintiff claims 
        inadequate visibility. Fractured ankle requiring 6 weeks recovery.
        
        Holding: Jury question on adequacy of warning. Store not entitled to summary judgment.
        
        Reasoning: Even with warning, store may be liable if warning insufficient. Factfinder must assess 
        reasonableness of precautions taken. Size, placement, and visibility of warning cone disputed.""",
        confidence=0.80,
        supporting_text="Jones court held that presence of warning sign..."
    ))
    
    # Mock Precedent Hunter findings
    findings.append(AgentFinding(
        agent_role=AgentRole.PRECEDENT_HUNTER,
        cycle=1,
        case_name="Smith v. Grocery Store, Inc.",
        finding="""Precedents Cited: Relies heavily on Restatement (Second) of Torts § 343.
        Cites Martinez v. Shopping Center (actual notice standard) and Williams v. Retail Store (duty to inspect).
        
        Binding Authority: State supreme court decision - binding precedent in jurisdiction.
        
        Distinguishing Factors: Unlike earlier cases requiring showing of "reasonable time to discover," 
        Smith involves actual employee knowledge, making temporal element irrelevant.""",
        confidence=0.75,
        supporting_text="Smith distinguishes Martinez by..."
    ))
    
    findings.append(AgentFinding(
        agent_role=AgentRole.PRECEDENT_HUNTER,
        cycle=1,
        case_name="Jones v. Supermarket Chain",
        finding="""Precedents Cited: Follows Smith framework but adds analysis of warning adequacy.
        References Garcia v. Department Store (warning placement standards).
        
        Persuasive Authority: Federal district court - persuasive but not binding.
        
        Key Development: Expands Smith by holding that warning alone may be insufficient. 
        Creates new requirement for warnings to be "conspicuous and effective under the circumstances.""",
        confidence=0.70,
        supporting_text="Jones extends the Smith doctrine..."
    ))
    
    # Mock Legal Principles findings
    findings.append(AgentFinding(
        agent_role=AgentRole.LEGAL_PRINCIPLES,
        cycle=1,
        case_name="Smith v. Grocery Store, Inc.",
        finding="""Legal Principles:
        1. Premises Liability Doctrine: Landowner owes duty of reasonable care to invitees
        2. Constructive Notice Standard: Notice inferred from length of time hazard existed
        3. Actual Notice Standard: Direct knowledge by owner/employees of dangerous condition
        
        Test Applied: Modified two-part test: (1) Did store know/should have known of condition? 
        (2) Did store take reasonable steps to remedy or warn?
        
        Burden: Plaintiff bears burden of proving both notice and breach by preponderance.""",
        confidence=0.90,
        supporting_text="The controlling principle is..."
    ))
    
    findings.append(AgentFinding(
        agent_role=AgentRole.LEGAL_PRINCIPLES,
        cycle=1,
        case_name="Jones v. Supermarket Chain",
        finding="""Legal Principles:
        1. Warning Adequacy Standard: Warnings must be conspicuous and effective
        2. Comparative Negligence: Plaintiff's fault may reduce recovery
        3. Reasonableness Standard: Precautions judged by what reasonable person would do
        
        Test Applied: Three-factor warning test: (1) Size and visibility (2) Placement relative to hazard 
        (3) Effectiveness in preventing harm
        
        Standard of Review: Summary judgment inappropriate when reasonable minds could differ.""",
        confidence=0.85,
        supporting_text="Jones establishes that warnings must..."
    ))
    
    return findings


async def test_multi_stage_synthesis():
    """Test the 4-stage synthesis pipeline"""
    
    logger.info("="*70)
    logger.info("TESTING MULTI-STAGE SYNTHESIS PIPELINE")
    logger.info("="*70)
    
    # Initialize LLM client
    logger.info("\n1. Initializing LLM client...")
    try:
        llm_client = AMDLLMClient(base_url="http://localhost:8000")  # Fixed: removed /v1
        logger.info("✓ LLM client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize LLM client: {e}")
        logger.error("Make sure vLLM server is running on port 8000")
        return
    
    # Initialize multi-agent researcher with multi-stage synthesis ENABLED
    logger.info("\n2. Initializing multi-agent researcher (multi-stage synthesis: ON)...")
    researcher = MultiAgentLegalResearcher(
        llm_client=llm_client,
        batch_size=10,
        max_cycles=1,
        enable_multi_stage_synthesis=True  # NEW PARAMETER
    )
    logger.info("✓ Researcher initialized with 4-stage synthesis")
    
    # Create mock findings
    logger.info("\n3. Creating mock research findings...")
    findings = create_mock_findings()
    logger.info(f"✓ Created {len(findings)} mock findings")
    for f in findings:
        logger.info(f"   - {f.agent_role.value}: {f.case_name}")
    
    # Mock cases
    mock_cases = [
        {
            'case_name': 'Smith v. Grocery Store, Inc.',
            'citation': '123 State 456 (2023)',
            'court': 'State Supreme Court'
        },
        {
            'case_name': 'Jones v. Supermarket Chain',
            'citation': '789 F.Supp.2d 101 (D. State 2024)',
            'court': 'Federal District Court'
        }
    ]
    
    question = "What is the liability standard for slip and fall cases at grocery stores with broken wrist injuries?"
    
    # Test the synthesis
    logger.info("\n4. Running 4-stage synthesis pipeline...")
    logger.info(f"   Question: {question}")
    
    try:
        synthesis = await researcher._synthesize_findings(question, findings, mock_cases)
        
        logger.info("\n" + "="*70)
        logger.info("✅ SYNTHESIS COMPLETE")
        logger.info("="*70)
        logger.info(f"\nFinal Memo ({len(synthesis)} characters):\n")
        logger.info("-"*70)
        logger.info(synthesis)
        logger.info("-"*70)
        
        # Validate output
        logger.info("\n5. Validating output...")
        checks = {
            "Has Executive Summary": "EXECUTIVE SUMMARY" in synthesis.upper() or "SUMMARY" in synthesis.upper(),
            "Has Legal Framework": "LEGAL FRAMEWORK" in synthesis.upper() or "PRINCIPLES" in synthesis.upper(),
            "Has Case Analysis": "CASE" in synthesis.upper() and "ANALYSIS" in synthesis.upper(),
            "Has Practical Guidance": "PRACTICAL" in synthesis.upper() or "GUIDANCE" in synthesis.upper() or "RECOMMENDATION" in synthesis.upper(),
            "Mentions Smith case": "Smith" in synthesis,
            "Mentions Jones case": "Jones" in synthesis,
            "Reasonable length": 500 < len(synthesis) < 5000
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✓" if result else "✗"
            logger.info(f"   {status} {check}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("\n✅ ALL VALIDATION CHECKS PASSED")
        else:
            logger.warning("\n⚠️  Some validation checks failed")
        
    except Exception as e:
        logger.error(f"\n✗ Synthesis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    # Compare with old single-shot synthesis
    logger.info("\n" + "="*70)
    logger.info("COMPARISON: Testing single-shot synthesis (old method)")
    logger.info("="*70)
    
    researcher_old = MultiAgentLegalResearcher(
        llm_client=llm_client,
        batch_size=10,
        max_cycles=1,
        enable_multi_stage_synthesis=False  # Disable multi-stage
    )
    
    try:
        synthesis_old = await researcher_old._synthesize_findings(question, findings, mock_cases)
        logger.info(f"\nOld Single-Shot Synthesis ({len(synthesis_old)} characters):\n")
        logger.info("-"*70)
        logger.info(synthesis_old)
        logger.info("-"*70)
        
        logger.info("\n📊 COMPARISON:")
        logger.info(f"   Multi-Stage Length: {len(synthesis)} chars")
        logger.info(f"   Single-Shot Length: {len(synthesis_old)} chars")
        logger.info(f"   Difference: {len(synthesis) - len(synthesis_old):+d} chars")
        
    except Exception as e:
        logger.error(f"✗ Old synthesis failed: {e}")
    
    logger.info("\n" + "="*70)
    logger.info("TEST COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(test_multi_stage_synthesis())
