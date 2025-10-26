# file: test_system.py
"""
Comprehensive test suite for Paralegal Research ADK
Tests all agents, orchestrator modes, and workflows
"""

import asyncio
import json
from datetime import datetime
from Paralegal.AMD_server.ADK.research_adk import (
    ParalegalOrchestrator,
    ResearchTask,
    SaulConfig,
    configure_dspy,
    DocumentAnalysisAgent,
    CaseLawResearchAgent,
    StatutoryResearchAgent,
    CitationExtractionAgent,
    LegalMemorandomAgent,
    DiscoveryAnalysisAgent,
    generate_fake_case_data
)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def record_pass(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")
    
    def record_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        print("="*80)
        if self.errors:
            print("\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        return self.failed == 0


results = TestResults()


def test_saul_connection():
    """Test 1: Verify vLLM connection"""
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
        resp = client.completions.create(
            model="Equall/Saul-7B-Instruct-v1",
            prompt="What is negligence?",
            max_tokens=32,
            temperature=0.2
        )
        assert len(resp.choices[0].text) > 0
        results.record_pass("Saul-7B Connection")
    except Exception as e:
        results.record_fail("Saul-7B Connection", str(e))


def test_document_analysis_agent():
    """Test 2: Document Analysis Agent"""
    try:
        agent = DocumentAnalysisAgent()
        result = agent(
            case_brief="Test case",
            document_list="doc1.pdf\ndoc2.pdf"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'document_analysis'
        assert 'relevant_documents' in result
        assert 'timestamp' in result
        results.record_pass("Document Analysis Agent")
    except Exception as e:
        results.record_fail("Document Analysis Agent", str(e))


def test_case_law_agent():
    """Test 3: Case Law Research Agent"""
    try:
        agent = CaseLawResearchAgent()
        result = agent(
            legal_issue="Negligence standard",
            jurisdiction="Federal"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'case_law_research'
        assert 'case_precedents' in result
        results.record_pass("Case Law Research Agent")
    except Exception as e:
        results.record_fail("Case Law Research Agent", str(e))


def test_statutory_agent():
    """Test 4: Statutory Research Agent"""
    try:
        agent = StatutoryResearchAgent()
        result = agent(
            legal_area="Contracts",
            jurisdiction="State",
            search_terms="breach of contract"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'statutory_research'
        assert 'relevant_statutes' in result
        results.record_pass("Statutory Research Agent")
    except Exception as e:
        results.record_fail("Statutory Research Agent", str(e))


def test_citation_agent():
    """Test 5: Citation Extraction Agent"""
    try:
        agent = CitationExtractionAgent()
        result = agent(
            raw_text="See Smith v. Jones, 123 F.3d 456 (5th Cir. 2020)"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'citation_extraction'
        assert 'case_citations' in result
        results.record_pass("Citation Extraction Agent")
    except Exception as e:
        results.record_fail("Citation Extraction Agent", str(e))


def test_memo_agent():
    """Test 6: Legal Memorandum Agent"""
    try:
        agent = LegalMemorandomAgent()
        result = agent(
            case_brief="Test case",
            research_findings="Finding 1, Finding 2"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'legal_memorandum'
        assert 'issue_statement' in result
        assert 'analysis' in result
        results.record_pass("Legal Memorandum Agent")
    except Exception as e:
        results.record_fail("Legal Memorandum Agent", str(e))


def test_discovery_agent():
    """Test 7: Discovery Analysis Agent"""
    try:
        agent = DiscoveryAnalysisAgent()
        result = agent(
            case_theory="Test theory",
            document_collection="doc1, doc2, doc3"
        )
        assert 'agent_name' in result
        assert result['agent_name'] == 'discovery_analysis'
        assert 'privileged_documents' in result
        results.record_pass("Discovery Analysis Agent")
    except Exception as e:
        results.record_fail("Discovery Analysis Agent", str(e))


def test_sequential_execution():
    """Test 8: Sequential Execution Mode"""
    try:
        orchestrator = ParalegalOrchestrator()
        tasks = [
            ResearchTask(
                agent_type='document_analysis',
                params={'case_brief': 'test', 'document_list': 'doc1'},
                priority=1
            ),
            ResearchTask(
                agent_type='citation_extraction',
                params={'raw_text': 'test citation'},
                priority=2
            )
        ]
        result = orchestrator.run_sequential(tasks)
        assert result['execution_mode'] == 'sequential'
        assert result['total_tasks'] == 2
        assert len(result['agent_results']) == 2
        results.record_pass("Sequential Execution")
    except Exception as e:
        results.record_fail("Sequential Execution", str(e))


def test_parallel_execution():
    """Test 9: Parallel Execution Mode"""
    try:
        orchestrator = ParalegalOrchestrator()
        tasks = [
            ResearchTask(
                agent_type='document_analysis',
                params={'case_brief': 'test', 'document_list': 'doc1'},
                priority=1
            ),
            ResearchTask(
                agent_type='case_law_research',
                params={'legal_issue': 'test', 'jurisdiction': 'Federal'},
                priority=1
            )
        ]
        result = asyncio.run(orchestrator.run_parallel(tasks))
        assert result['execution_mode'] == 'parallel'
        assert result['total_tasks'] == 2
        assert len(result['agent_results']) == 2
        results.record_pass("Parallel Execution")
    except Exception as e:
        results.record_fail("Parallel Execution", str(e))


def test_full_workflow():
    """Test 10: Full Research Workflow"""
    try:
        orchestrator = ParalegalOrchestrator()
        result = asyncio.run(
            orchestrator.full_research_workflow(
                case_brief="Test case brief",
                document_list="doc1.pdf\ndoc2.pdf",
                legal_issue="Test issue",
                jurisdiction="Test jurisdiction",
                execution_mode='parallel'
            )
        )
        assert 'workflow' in result
        assert result['workflow'] == 'full_research'
        assert 'phase1_results' in result
        assert 'final_memorandum' in result
        results.record_pass("Full Research Workflow")
    except Exception as e:
        results.record_fail("Full Research Workflow", str(e))


def test_fake_data_generation():
    """Test 11: Fake Data Generator"""
    try:
        data = generate_fake_case_data()
        assert 'case_brief' in data
        assert 'document_list' in data
        assert 'legal_issue' in data
        assert 'jurisdiction' in data
        assert len(data['case_brief']) > 100
        results.record_pass("Fake Data Generation")
    except Exception as e:
        results.record_fail("Fake Data Generation", str(e))


def test_research_task_creation():
    """Test 12: ResearchTask Object Creation"""
    try:
        task = ResearchTask(
            agent_type='document_analysis',
            params={'test': 'value'},
            priority=1
        )
        assert task.agent_type == 'document_analysis'
        assert task.params == {'test': 'value'}
        assert task.priority == 1
        results.record_pass("ResearchTask Creation")
    except Exception as e:
        results.record_fail("ResearchTask Creation", str(e))


def test_error_handling():
    """Test 13: Error Handling for Invalid Agent"""
    try:
        orchestrator = ParalegalOrchestrator()
        tasks = [
            ResearchTask(
                agent_type='invalid_agent',
                params={'test': 'value'},
                priority=1
            )
        ]
        result = orchestrator.run_sequential(tasks)
        assert result['failed_tasks'] == 1
        assert 'error' in result['agent_results'][0]
        results.record_pass("Error Handling")
    except Exception as e:
        results.record_fail("Error Handling", str(e))


def test_result_metadata():
    """Test 14: Result Metadata Presence"""
    try:
        agent = DocumentAnalysisAgent()
        result = agent(
            case_brief="Test",
            document_list="doc1"
        )
        assert 'timestamp' in result
        assert 'agent_name' in result
        # Verify timestamp format
        datetime.fromisoformat(result['timestamp'])
        results.record_pass("Result Metadata")
    except Exception as e:
        results.record_fail("Result Metadata", str(e))


def test_priority_handling():
    """Test 15: Task Priority Handling"""
    try:
        task1 = ResearchTask('document_analysis', {}, priority=1)
        task2 = ResearchTask('case_law_research', {}, priority=2)
        assert task1.priority < task2.priority
        results.record_pass("Priority Handling")
    except Exception as e:
        results.record_fail("Priority Handling", str(e))


def performance_test():
    """Performance Test: Measure execution time"""
    print("\n" + "="*80)
    print("PERFORMANCE TESTS")
    print("="*80)
    
    try:
        orchestrator = ParalegalOrchestrator()
        case_data = generate_fake_case_data()
        
        # Test sequential performance
        start = datetime.now()
        tasks = [
            ResearchTask('document_analysis', 
                        {'case_brief': case_data['case_brief'][:100],
                         'document_list': case_data['document_list'][:100]},
                        priority=1)
        ]
        orchestrator.run_sequential(tasks)
        seq_time = (datetime.now() - start).total_seconds()
        print(f"Sequential (1 agent): {seq_time:.2f}s")
        
        # Test parallel performance
        start = datetime.now()
        tasks = [
            ResearchTask('document_analysis',
                        {'case_brief': case_data['case_brief'][:100],
                         'document_list': case_data['document_list'][:100]},
                        priority=1),
            ResearchTask('citation_extraction',
                        {'raw_text': case_data['raw_citation_text'][:100]},
                        priority=1)
        ]
        asyncio.run(orchestrator.run_parallel(tasks))
        par_time = (datetime.now() - start).total_seconds()
        print(f"Parallel (2 agents): {par_time:.2f}s")
        
        if par_time < seq_time * 2:
            print("✓ Parallel execution shows performance benefit")
        else:
            print("⚠ Parallel execution may need optimization")
            
    except Exception as e:
        print(f"Performance test error: {e}")


def integration_test():
    """Integration Test: Complete workflow with fake data"""
    print("\n" + "="*80)
    print("INTEGRATION TEST")
    print("="*80)
    
    try:
        print("Running complete workflow with fake data...")
        orchestrator = ParalegalOrchestrator()
        case_data = generate_fake_case_data()
        
        result = asyncio.run(
            orchestrator.full_research_workflow(
                case_brief=case_data['case_brief'],
                document_list=case_data['document_list'],
                legal_issue=case_data['legal_issue'],
                jurisdiction=case_data['jurisdiction']
            )
        )
        
        # Verify structure
        assert 'phase1_results' in result
        assert 'final_memorandum' in result
        
        # Verify phase 1
        phase1 = result['phase1_results']
        print(f"Phase 1: {phase1['successful_tasks']}/{phase1['total_tasks']} tasks successful")
        
        # Verify phase 2
        memo = result['final_memorandum']
        print(f"Phase 2: Memorandum generated with {len(memo)} fields")
        
        # Save result
        with open('integration_test_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("✓ Integration test passed - results saved to integration_test_result.json")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PARALEGAL RESEARCH ADK - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().isoformat()}\n")
    
    # Configure system
    print("Configuring Saul-7B...")
    try:
        config = SaulConfig()
        configure_dspy(config)
        print("✓ Configuration successful\n")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        print("Make sure vLLM server is running!")
        return 1
    
    # Run unit tests
    print("="*80)
    print("UNIT TESTS")
    print("="*80)
    
    test_saul_connection()
    test_document_analysis_agent()
    test_case_law_agent()
    test_statutory_agent()
    test_citation_agent()
    test_memo_agent()
    test_discovery_agent()
    test_sequential_execution()
    test_parallel_execution()
    test_full_workflow()
    test_fake_data_generation()
    test_research_task_creation()
    test_error_handling()
    test_result_metadata()
    test_priority_handling()
    
    # Performance tests
    performance_test()
    
    # Integration test
    integration_test()
    
    # Print summary
    success = results.summary()
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())