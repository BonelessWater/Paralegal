#!/usr/bin/env python3
"""
Quick test script for RAG-enhanced Legal Researcher Agent
Tests the integration without running full test suite
"""

import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from backend.APIs.AMD.llm_client import AMDLLMClient
from agents.legal_researcher_agent import LegalResearcherAgent
from config.amd_config import AMDConfig

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    print_section("RAG-Enhanced Legal Researcher - Quick Test")
    
    # Validate configuration
    try:
        AMDConfig.validate()
        print("✅ Configuration valid")
    except ValueError as e:
        print(f"\n❌ Configuration Error:\n{e}\n")
        sys.exit(1)
    
    # Initialize LLM client
    print("\n🔌 Connecting to vLLM server...")
    llm = AMDLLMClient(
        base_url=AMDConfig.VLLM_BASE_URL,
        model=AMDConfig.MODEL_FOLDER
    )
    
    # Health check
    if not llm.health_check():
        print("❌ vLLM server not responding!")
        print(f"   Expected at: {AMDConfig.VLLM_BASE_URL}")
        sys.exit(1)
    
    print("✅ Server is healthy!\n")
    
    # Initialize Legal Researcher with RAG
    print_section("Initializing Legal Researcher Agent (with RAG)")
    agent = LegalResearcherAgent(llm, use_rag=True)
    
    # Test Case 1: Car accident
    print_section("Test Case: Car Accident with Back Injury")
    
    injury = "Car accident with herniated disc"
    jurisdiction = "Florida"
    details = "Rear-end collision at stoplight, herniated disc L4-L5, 3 months physical therapy, ongoing pain"
    
    print(f"Input:")
    print(f"  Injury: {injury}")
    print(f"  Jurisdiction: {jurisdiction}")
    print(f"  Details: {details}")
    
    try:
        result = agent.process(injury, jurisdiction, details, top_k_cases=5)
        
        # Show similar cases if found
        if 'similar_cases' in result and result['similar_cases']:
            print("\n" + "=" * 80)
            print("📚 SIMILAR CASES FOUND VIA RAG")
            print("=" * 80)
            
            for i, case in enumerate(result['similar_cases'], 1):
                print(f"\n{i}. {case['title']}")
                print(f"   {'─' * 76}")
                print(f"   Similarity Score: {case['similarity']:.1%}")
                print(f"   Document Type:    {case['document_type']}")
                print(f"   Document ID:      {case['metadata']['document_id']}")
                if case['metadata'].get('jurisdiction'):
                    print(f"   Jurisdiction:     {case['metadata']['jurisdiction']}")
                print(f"\n   Preview:")
                print(f"   {case['text_preview']}")
        else:
            print("\nℹ️  No similar cases found (or RAG disabled)")
        
        # Show research memo
        print("\n" + "=" * 80)
        print("📝 LEGAL RESEARCH MEMO")
        print("=" * 80)
        print(result['research_memo'])
        print("\n" + "=" * 80)
        
        print("\n✅ TEST PASSED - RAG integration working!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print_section("Test Complete!")
    
    print("Summary:")
    print(f"  • RAG Status: {'✅ Enabled' if agent.use_rag else '❌ Disabled'}")
    print(f"  • Similar Cases Found: {len(result.get('similar_cases', []))}")
    print(f"  • Research Memo Length: {len(result['research_memo'])} chars")
    print()

if __name__ == "__main__":
    main()
