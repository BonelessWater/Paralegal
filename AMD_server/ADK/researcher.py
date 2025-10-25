# File: paralegal_research_adk.py
"""
Paralegal Research ADK Architecture
Uses vLLM-served Saul-7B for legal research tasks
Includes orchestrator with parallel agent execution
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ========================== CONFIGURATION ==========================

class SaulConfig:
    """Configuration for vLLM-served Saul-7B"""
    def __init__(
        self,
        api_key: str = "dummy",
        model: str = "Equall/Saul-7B-Instruct-v1",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        api_base: str = "http://localhost:8000/v1"
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base


def configure_dspy(cfg: SaulConfig) -> None:
    """Configure DSPy with vLLM-served Saul-7B"""
    provider_key = f"openai/{cfg.model}"
    lm_kwargs = {
        "api_key": cfg.api_key,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "api_base": cfg.api_base,
    }
    lm = dspy.LM(provider_key, **lm_kwargs)
    dspy.configure(lm=lm)

def _as_text(x) -> str:
    """Coerce DSPy fields (which may be None/dict/list) into a string."""
    if x is None:
        return ""
    if isinstance(x, (str, int, float)):
        return str(x)
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)

def _safe_pick(pred, *field_names) -> dict:
    """
    Safely extract output fields from a DSPy prediction.
    Any missing/None field becomes "" so callers never explode.
    """
    out = {}
    for name in field_names:
        val = getattr(pred, name, "") if pred is not None else ""
        out[name] = _as_text(val)
    return out


# ========================== AGENT SIGNATURES ==========================

class DocumentAnalysisSignature(dspy.Signature):
    """Analyze client documents for relevant information"""
    case_brief = dspy.InputField(desc="Brief description of the case and legal issues")
    document_list = dspy.InputField(desc="List of available documents with brief descriptions")
    relevant_documents = dspy.OutputField(desc="Documents most relevant to the case with reasoning")
    key_findings = dspy.OutputField(desc="Key facts and information extracted from documents")
    missing_information = dspy.OutputField(desc="Information gaps that need to be addressed")


class CaseLawResearchSignature(dspy.Signature):
    """Research relevant case law and precedents"""
    legal_issue = dspy.InputField(desc="Specific legal issue or question to research")
    jurisdiction = dspy.InputField(desc="Relevant jurisdiction (state, federal, circuit)")
    case_precedents = dspy.OutputField(desc="Relevant case precedents with citations and holdings")
    applicable_standards = dspy.OutputField(desc="Legal standards and tests that apply")
    distinguishing_factors = dspy.OutputField(desc="Factors that may distinguish this case")


class StatutoryResearchSignature(dspy.Signature):
    """Research statutes and regulations"""
    legal_area = dspy.InputField(desc="Area of law (e.g., contract, tort, criminal)")
    jurisdiction = dspy.InputField(desc="Relevant jurisdiction")
    search_terms = dspy.InputField(desc="Specific terms or concepts to search")
    relevant_statutes = dspy.OutputField(desc="Applicable statutes with citations and text")
    regulatory_framework = dspy.OutputField(desc="Relevant regulations and administrative rules")
    statutory_interpretation = dspy.OutputField(desc="How statutes apply to the case")


class CitationExtractionSignature(dspy.Signature):
    """Extract and verify legal citations"""
    raw_text = dspy.InputField(desc="Text containing legal citations")
    case_citations = dspy.OutputField(desc="Extracted case citations with proper format")
    statute_citations = dspy.OutputField(desc="Extracted statute citations with proper format")
    secondary_sources = dspy.OutputField(desc="Law review articles, treatises, etc.")
    citation_errors = dspy.OutputField(desc="Formatting errors or incomplete citations")


class LegalMemorandomSignature(dspy.Signature):
    """Synthesize research into a legal memorandum"""
    case_brief = dspy.InputField(desc="Overview of the case and issues")
    research_findings = dspy.InputField(desc="Compiled research from all agents")
    issue_statement = dspy.OutputField(desc="Clear statement of legal issues")
    brief_answer = dspy.OutputField(desc="Concise answer to the legal question")
    analysis = dspy.OutputField(desc="Detailed legal analysis with citations")
    conclusion = dspy.OutputField(desc="Conclusion and recommendations")


class DiscoveryAnalysisSignature(dspy.Signature):
    """Analyze documents for discovery purposes"""
    case_theory = dspy.InputField(desc="Theory of the case and what to prove")
    document_collection = dspy.InputField(desc="Collection of documents to review")
    privileged_documents = dspy.OutputField(desc="Documents that may be privileged")
    responsive_documents = dspy.OutputField(desc="Documents responsive to discovery requests")
    key_evidence = dspy.OutputField(desc="Documents containing key evidence")
    redaction_recommendations = dspy.OutputField(desc="Recommendations for redactions")


# ========================== SPECIALIZED AGENTS ==========================

class DocumentAnalysisAgent(dspy.Module):
    """Analyzes client documents and extracts relevant information"""
    
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(DocumentAnalysisSignature)
    
    # DocumentAnalysisAgent
    def forward(self, case_brief: str, document_list: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.analyze(case_brief=case_brief, document_list=document_list)
        except Exception as e:
            # Keep going; we'll return structured error fields below
            pass

        fields = _safe_pick(pred, "relevant_documents", "key_findings", "missing_information")
        return {
            "agent_name": "document_analysis",
            **fields,
            "timestamp": datetime.now().isoformat()
        }



class CaseLawResearchAgent(dspy.Module):
    """Researches case law and precedents"""
    
    def __init__(self):
        super().__init__()
        self.research = dspy.ChainOfThought(CaseLawResearchSignature)
    
    # CaseLawResearchAgent
    def forward(self, legal_issue: str, jurisdiction: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.research(legal_issue=legal_issue, jurisdiction=jurisdiction)
        except Exception:
            pass

        fields = _safe_pick(pred, "case_precedents", "applicable_standards", "distinguishing_factors")
        return {
            "agent_name": "case_law_research",
            **fields,
            "timestamp": datetime.now().isoformat()
        }



class StatutoryResearchAgent(dspy.Module):
    """Researches statutes and regulations"""
    
    def __init__(self):
        super().__init__()
        self.research = dspy.ChainOfThought(StatutoryResearchSignature)
    
    def forward(self, legal_area: str, jurisdiction: str, search_terms: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.research(legal_area=legal_area, jurisdiction=jurisdiction, search_terms=search_terms)
        except Exception:
            pass

        fields = _safe_pick(pred, "relevant_statutes", "regulatory_framework", "statutory_interpretation")
        return {
            "agent_name": "statutory_research",
            **fields,
            "timestamp": datetime.now().isoformat()
        }


class CitationExtractionAgent(dspy.Module):
    """Extracts and verifies legal citations"""
    
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(CitationExtractionSignature)
    
    def forward(self, raw_text: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.extract(raw_text=raw_text)
        except Exception:
            pass

        fields = _safe_pick(pred, "case_citations", "statute_citations", "secondary_sources", "citation_errors")
        return {
            "agent_name": "citation_extraction",
            **fields,
            "timestamp": datetime.now().isoformat()
        }


class LegalMemorandomAgent(dspy.Module):
    """Synthesizes research into a legal memorandum"""
    
    def __init__(self):
        super().__init__()
        self.synthesize = dspy.ChainOfThought(LegalMemorandomSignature)
    
    # LegalMemorandomAgent
    def forward(self, case_brief: str, research_findings: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.synthesize(case_brief=case_brief, research_findings=research_findings)
        except Exception:
            pass

        fields = _safe_pick(pred, "issue_statement", "brief_answer", "analysis", "conclusion")
        return {
            "agent_name": "legal_memorandum",
            **fields,
            "timestamp": datetime.now().isoformat()
        }



class DiscoveryAnalysisAgent(dspy.Module):
    """Analyzes documents for discovery purposes"""
    
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(DiscoveryAnalysisSignature)
    
    # DiscoveryAnalysisAgent
    def forward(self, case_theory: str, document_collection: str) -> Dict[str, Any]:
        pred = None
        try:
            pred = self.analyze(case_theory=case_theory, document_collection=document_collection)
        except Exception:
            pass

        fields = _safe_pick(pred, "privileged_documents", "responsive_documents", "key_evidence", "redaction_recommendations")
        return {
            "agent_name": "discovery_analysis",
            **fields,
            "timestamp": datetime.now().isoformat()
        }



# ========================== RESEARCH ORCHESTRATOR ==========================

@dataclass
class ResearchTask:
    """Represents a research task to be executed"""
    agent_type: str
    params: Dict[str, Any]
    priority: int = 1


class ParalegalOrchestrator:
    """
    Orchestrates paralegal research tasks
    Can run agents sequentially or in parallel
    """
    
    def __init__(self):
        self.doc_agent = DocumentAnalysisAgent()
        self.case_law_agent = CaseLawResearchAgent()
        self.statutory_agent = StatutoryResearchAgent()
        self.citation_agent = CitationExtractionAgent()
        self.memo_agent = LegalMemorandomAgent()
        self.discovery_agent = DiscoveryAnalysisAgent()
        
        self.agent_map = {
            'document_analysis': self.doc_agent,
            'case_law_research': self.case_law_agent,
            'statutory_research': self.statutory_agent,
            'citation_extraction': self.citation_agent,
            'legal_memorandum': self.memo_agent,
            'discovery_analysis': self.discovery_agent
        }
    
    async def execute_agent_async(self, task: ResearchTask) -> Dict[str, Any]:
        """Execute a single agent task asynchronously"""
        try:
            agent = self.agent_map.get(task.agent_type)
            if not agent:
                return {
                    'agent_name': task.agent_type,
                    'error': f'Unknown agent type: {task.agent_type}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Execute agent in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent(**task.params))
            result['priority'] = task.priority
            return result
        except Exception as e:
            return {
                'agent_name': task.agent_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_parallel(
        self,
        tasks: List[ResearchTask]
    ) -> Dict[str, Any]:
        """
        Execute multiple research tasks in parallel
        Returns compiled results from all agents
        """
        print(f"[Orchestrator] Starting parallel execution of {len(tasks)} tasks...")
        
        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[self.execute_agent_async(task) for task in tasks],
            return_exceptions=True
        )
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'agent_name': tasks[i].agent_type,
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        # Compile results
        return {
            'execution_mode': 'parallel',
            'total_tasks': len(tasks),
            'successful_tasks': sum(1 for r in processed_results if 'error' not in r),
            'failed_tasks': sum(1 for r in processed_results if 'error' in r),
            'agent_results': processed_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def run_sequential(
        self,
        tasks: List[ResearchTask]
    ) -> Dict[str, Any]:
        """
        Execute research tasks sequentially
        Useful when later tasks depend on earlier results
        """
        print(f"[Orchestrator] Starting sequential execution of {len(tasks)} tasks...")
        
        results = []
        for task in tasks:
            try:
                agent = self.agent_map.get(task.agent_type)
                if not agent:
                    results.append({
                        'agent_name': task.agent_type,
                        'error': f'Unknown agent type: {task.agent_type}',
                        'timestamp': datetime.now().isoformat()
                    })
                    continue
                
                result = agent(**task.params)
                result['priority'] = task.priority
                results.append(result)
            except Exception as e:
                results.append({
                    'agent_name': task.agent_type,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return {
            'execution_mode': 'sequential',
            'total_tasks': len(tasks),
            'successful_tasks': sum(1 for r in results if 'error' not in r),
            'failed_tasks': sum(1 for r in results if 'error' in r),
            'agent_results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def full_research_workflow(
        self,
        case_brief: str,
        document_list: str,
        legal_issue: str,
        jurisdiction: str,
        execution_mode: str = 'parallel'
    ) -> Dict[str, Any]:
        """
        Execute a complete research workflow
        Phase 1: Initial research (parallel)
        Phase 2: Synthesis (sequential)
        """
        print("[Orchestrator] Starting full research workflow...")
        
        # Phase 1: Parallel research tasks
        phase1_tasks = [
            ResearchTask(
                agent_type='document_analysis',
                params={'case_brief': case_brief, 'document_list': document_list},
                priority=1
            ),
            ResearchTask(
                agent_type='case_law_research',
                params={'legal_issue': legal_issue, 'jurisdiction': jurisdiction},
                priority=1
            ),
            ResearchTask(
                agent_type='statutory_research',
                params={
                    'legal_area': legal_issue.split()[0],  # Extract first word as area
                    'jurisdiction': jurisdiction,
                    'search_terms': legal_issue
                },
                priority=1
            )
        ]
        
        if execution_mode == 'parallel':
            phase1_results = await self.run_parallel(phase1_tasks)
        else:
            phase1_results = self.run_sequential(phase1_tasks)
        
        # Compile findings for synthesis
        research_findings = json.dumps(phase1_results['agent_results'], indent=2)
        
        # Phase 2: Synthesis
        print("[Orchestrator] Synthesizing research into legal memorandum...")
        memo_result = self.memo_agent(
            case_brief=case_brief,
            research_findings=research_findings
        )
        
        return {
            'workflow': 'full_research',
            'phase1_results': phase1_results,
            'final_memorandum': memo_result,
            'timestamp': datetime.now().isoformat()
        }


# ========================== FAKE DATA GENERATORS ==========================

def generate_fake_case_data() -> Dict[str, Any]:
    """Generate fake case data for testing"""
    return {
        'case_brief': """
        Client: Sarah Martinez, plaintiff
        Defendant: Acme Insurance Company
        
        Case Type: Insurance Bad Faith & Negligence
        
        Facts: Client was rear-ended at a red light on I-95 in Miami, FL on March 15, 2024.
        Defendant driver was texting while driving. Client sustained whiplash and back injuries
        requiring 6 months of physical therapy. Defendant's insurance (Acme Insurance) initially
        denied claim, citing "pre-existing condition" despite no prior back issues. After 8 months,
        they offered $5,000 settlement for $45,000 in medical bills.
        
        Legal Issues: 
        1. Negligence per se (texting while driving violation)
        2. Insurance bad faith under FL Stat. §624.155
        3. Damages for medical expenses, pain and suffering, lost wages
        """,
        
        'document_list': """
        1. police_report_2024-03-15.pdf - Official accident report, witness statements
        2. medical_records_martinez.pdf - ER visit, X-rays, PT records (300 pages)
        3. insurance_policy_acme_2024.pdf - Client's policy with Acme Insurance
        4. claim_denial_letter.pdf - Initial denial letter citing pre-existing condition
        5. settlement_offer_letter.pdf - Low-ball settlement offer
        6. text_message_records.pdf - Defendant's phone records (subpoenaed)
        7. employment_records.pdf - Lost wage documentation
        8. photos_accident_scene.zip - 25 photos of vehicles and intersection
        9. medical_bills_itemized.xlsx - Detailed billing statements
        10. adjuster_notes.pdf - Insurance adjuster's investigation notes
        """,
        
        'legal_issue': 'Insurance bad faith and negligence in Florida auto accident case',
        
        'jurisdiction': 'Florida State Courts, 11th Judicial Circuit (Miami-Dade County)',
        
        'raw_citation_text': """
        Research notes on bad faith:
        - See Harvey v. GEICO, 354 F.3d 1321 (11th Cir 2003) - established standard
        - FL Stat. §624.155 requires prompt investigation and payment
        - Berges v. Infinity Ins. Co., 896 So. 2d 665 (Fla. 2004) - bad faith damages
        - Also check Restatement (Second) of Torts §§ 281-293 on negligence
        - State Farm v. Laforet, 658 So.2d 55 (Fla. 1995) about delay tactics
        - Imhof v. Nationwide Mut Ins Co (may have wrong citation?)
        """,
        
        'case_theory': """
        We will prove Acme Insurance acted in bad faith by:
        1. Unreasonably denying valid claim based on false "pre-existing condition"
        2. Failing to conduct adequate investigation
        3. Delaying payment for 8 months without justification
        4. Offering unconscionably low settlement ($5k for $45k in bills)
        5. Pattern and practice of similar denials (if discoverable)
        """,
        
        'document_collection_for_discovery': """
        Documents received from Acme Insurance via discovery:
        - Claims file for Sarah Martinez (500 pages)
        - Internal emails between adjusters and supervisors
        - Medical review reports by company doctor
        - Settlement authority guidelines
        - Training materials for claims adjusters
        - Similar claim files from same time period (requested)
        - Communications with defense counsel
        - Financial records showing claim reserves
        """
    }


# ========================== MAIN EXECUTION ==========================

def main():
    parser = argparse.ArgumentParser(
        description='Paralegal Research ADK using Saul-7B via vLLM'
    )
    
    parser.add_argument(
        '--api-base',
        default='http://localhost:8000/v1',
        help='vLLM API base URL'
    )
    parser.add_argument(
        '--model',
        default='Equall/Saul-7B-Instruct-v1',
        help='Model name'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.2,
        help='Temperature for generation'
    )
    parser.add_argument(
        '--mode',
        choices=['parallel', 'sequential', 'full'],
        default='full',
        help='Execution mode: parallel, sequential, or full workflow'
    )
    parser.add_argument(
        '--output',
        default='research_results.json',
        help='Output file for results'
    )
    parser.add_argument(
        '--use-fake-data',
        action='store_true',
        help='Use fake case data for testing'
    )
    
    args = parser.parse_args()
    
    # Configure Saul-7B
    print("[Config] Configuring vLLM-served Saul-7B...")
    config = SaulConfig(
        api_base=args.api_base,
        model=args.model,
        temperature=args.temperature
    )
    configure_dspy(config)
    
    # Initialize orchestrator
    orchestrator = ParalegalOrchestrator()
    
    # Get case data
    if args.use_fake_data:
        print("[Data] Using fake case data...")
        case_data = generate_fake_case_data()
    else:
        # In production, load from files or database
        raise NotImplementedError("Real data loading not yet implemented. Use --use-fake-data")
    
    # Execute based on mode
    if args.mode == 'full':
        result = asyncio.run(
            orchestrator.full_research_workflow(
                case_brief=case_data['case_brief'],
                document_list=case_data['document_list'],
                legal_issue=case_data['legal_issue'],
                jurisdiction=case_data['jurisdiction'],
                execution_mode='parallel'
            )
        )
    elif args.mode == 'parallel':
        tasks = [
            ResearchTask(
                agent_type='document_analysis',
                params={
                    'case_brief': case_data['case_brief'],
                    'document_list': case_data['document_list']
                },
                priority=1
            ),
            ResearchTask(
                agent_type='case_law_research',
                params={
                    'legal_issue': case_data['legal_issue'],
                    'jurisdiction': case_data['jurisdiction']
                },
                priority=1
            ),
            ResearchTask(
                agent_type='citation_extraction',
                params={'raw_text': case_data['raw_citation_text']},
                priority=2
            )
        ]
        result = asyncio.run(orchestrator.run_parallel(tasks))
    else:  # sequential
        tasks = [
            ResearchTask(
                agent_type='document_analysis',
                params={
                    'case_brief': case_data['case_brief'],
                    'document_list': case_data['document_list']
                },
                priority=1
            ),
            ResearchTask(
                agent_type='statutory_research',
                params={
                    'legal_area': 'Insurance',
                    'jurisdiction': case_data['jurisdiction'],
                    'search_terms': 'bad faith denial'
                },
                priority=1
            )
        ]
        result = orchestrator.run_sequential(tasks)
    
    # Save results
    print(f"[Output] Saving results to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"[Complete] Research complete. Results saved to {args.output}")
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    
    if 'phase1_results' in result:
        print(f"Phase 1 - Research Tasks: {result['phase1_results']['successful_tasks']}/{result['phase1_results']['total_tasks']} successful")
        print(f"Phase 2 - Memorandum: Generated")
    else:
        print(f"Tasks: {result['successful_tasks']}/{result['total_tasks']} successful")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())