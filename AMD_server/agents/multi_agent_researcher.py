"""
Multi-Agent Legal Research System

A sophisticated research system that uses multiple specialized agents working
iteratively to produce comprehensive legal analysis.

Architecture:
1. Case Analyst Agent - Analyzes facts and holdings from cases
2. Precedent Hunter Agent - Identifies relevant precedents and distinguishes cases
3. Legal Principles Agent - Extracts legal doctrines and rules
4. Synthesis Agent - Combines findings into comprehensive memo

Workflow:
- Agents work in parallel on batches of cases
- Each agent focuses on their specialty
- Results are iteratively refined over multiple cycles
- Final synthesis combines all perspectives
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized research agent roles"""
    CASE_ANALYST = "case_analyst"
    PRECEDENT_HUNTER = "precedent_hunter"
    LEGAL_PRINCIPLES = "legal_principles"
    SYNTHESIS = "synthesis"


@dataclass
class AgentFinding:
    """Finding from a specialized agent"""
    agent_role: AgentRole
    cycle: int
    case_name: str
    finding: str
    confidence: float
    supporting_text: str
    

@dataclass
class ResearchCycle:
    """One iteration of multi-agent research"""
    cycle_number: int
    cases_analyzed: List[Dict]
    agent_findings: List[AgentFinding]
    refinements: str
    

class MultiAgentLegalResearcher:
    """
    Multi-agent legal research system with iterative refinement.
    
    Uses specialized agents working in parallel to analyze cases from
    different perspectives, then synthesizes findings across multiple cycles.
    """
    
    def __init__(self, llm_client, batch_size: int = 10, max_cycles: int = 3):
        """
        Initialize multi-agent researcher.
        
        Args:
            llm_client: LLM client for agent reasoning
            batch_size: Number of cases to analyze per cycle
            max_cycles: Maximum refinement cycles
        """
        self.llm = llm_client
        self.batch_size = batch_size
        self.max_cycles = max_cycles
        self.research_cycles: List[ResearchCycle] = []
        
        # Agent prompts
        self.agent_prompts = {
            AgentRole.CASE_ANALYST: self._case_analyst_prompt(),
            AgentRole.PRECEDENT_HUNTER: self._precedent_hunter_prompt(),
            AgentRole.LEGAL_PRINCIPLES: self._legal_principles_prompt(),
            AgentRole.SYNTHESIS: self._synthesis_prompt()
        }
        
        logger.info(f"Initialized multi-agent researcher (batch_size={batch_size}, max_cycles={max_cycles})")
    
    async def research_async(self, 
                            question: str, 
                            cases: List[Dict],
                            previous_findings: Optional[List[AgentFinding]] = None) -> Dict[str, Any]:
        """
        Execute multi-agent iterative research.
        
        Args:
            question: Legal research question
            cases: List of case dictionaries with opinion text
            previous_findings: Findings from previous cycles (for refinement)
            
        Returns:
            Comprehensive research results with all agent findings and synthesis
        """
        logger.info(f"🔬 Starting multi-agent research on {len(cases)} cases")
        logger.info(f"Question: {question}")
        
        all_findings = []
        
        # Split cases into batches
        case_batches = self._create_batches(cases, self.batch_size)
        
        # Execute research cycles
        for cycle_num in range(self.max_cycles):
            logger.info(f"\n{'='*70}")
            logger.info(f"CYCLE {cycle_num + 1}/{self.max_cycles}")
            logger.info(f"{'='*70}")
            
            # Get batch for this cycle
            if cycle_num < len(case_batches):
                batch = case_batches[cycle_num]
            else:
                # Later cycles refine existing findings
                batch = cases[:self.batch_size]
            
            # Run specialized agents in parallel
            cycle_findings = await self._run_agent_cycle(
                question=question,
                cases=batch,
                cycle_num=cycle_num,
                previous_findings=all_findings
            )
            
            all_findings.extend(cycle_findings)
            
            # Store cycle
            self.research_cycles.append(ResearchCycle(
                cycle_number=cycle_num + 1,
                cases_analyzed=batch,
                agent_findings=cycle_findings,
                refinements=f"Analyzed {len(batch)} cases with {len(cycle_findings)} findings"
            ))
        
        # Final synthesis
        logger.info(f"\n{'='*70}")
        logger.info("FINAL SYNTHESIS")
        logger.info(f"{'='*70}")
        
        synthesis = await self._synthesize_findings(question, all_findings, cases)
        
        return {
            'question': question,
            'total_cases': len(cases),
            'cycles': self.max_cycles,
            'total_findings': len(all_findings),
            'agent_findings': [self._finding_to_dict(f) for f in all_findings],
            'synthesis': synthesis,
            'research_cycles': [self._cycle_to_dict(c) for c in self.research_cycles]
        }
    
    async def _run_agent_cycle(self,
                               question: str,
                               cases: List[Dict],
                               cycle_num: int,
                               previous_findings: List[AgentFinding]) -> List[AgentFinding]:
        """Run all specialized agents on a batch of cases"""
        
        findings = []
        
        # Run agents in parallel
        tasks = [
            self._run_case_analyst(question, cases, cycle_num),
            self._run_precedent_hunter(question, cases, cycle_num, previous_findings),
            self._run_legal_principles(question, cases, cycle_num)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect findings
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent error: {result}")
            elif result:
                findings.extend(result)
        
        logger.info(f"Cycle {cycle_num + 1}: Generated {len(findings)} findings from {len(cases)} cases")
        
        return findings
    
    async def _run_case_analyst(self, question: str, cases: List[Dict], cycle: int) -> List[AgentFinding]:
        """Case Analyst: Extract facts and holdings from cases"""
        logger.info(f"  🔍 Case Analyst analyzing {len(cases)} cases...")
        
        findings = []
        
        for case in cases[:5]:  # Top 5 cases per cycle
            try:
                case_text = self._get_case_text(case)
                if not case_text:
                    continue
                
                prompt = f"""{self.agent_prompts[AgentRole.CASE_ANALYST]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}
Citation: {case.get('citation', 'N/A')}
Court: {case.get('court', 'Unknown')}

OPINION EXCERPT:
{case_text[:2000]}

RESEARCH QUESTION:
{question}

Analyze this case and extract:
1. Key facts relevant to the research question
2. The court's holding
3. The reasoning
4. How it relates to the research question

Be specific and quote the opinion."""

                response = await self._ask_llm(prompt, max_tokens=800)
                
                findings.append(AgentFinding(
                    agent_role=AgentRole.CASE_ANALYST,
                    cycle=cycle,
                    case_name=case.get('case_name', 'Unknown'),
                    finding=response,
                    confidence=0.8,
                    supporting_text=case_text[:500]
                ))
                
            except Exception as e:
                logger.error(f"Case analyst error: {e}")
        
        logger.info(f"    ✓ Case Analyst: {len(findings)} findings")
        return findings
    
    async def _run_precedent_hunter(self, 
                                    question: str, 
                                    cases: List[Dict], 
                                    cycle: int,
                                    previous_findings: List[AgentFinding]) -> List[AgentFinding]:
        """Precedent Hunter: Identify relevant precedents and distinguish cases"""
        logger.info(f"  🎯 Precedent Hunter analyzing {len(cases)} cases...")
        
        findings = []
        
        # Build context from previous findings
        previous_context = ""
        if previous_findings:
            previous_context = "\n\nPREVIOUSLY IDENTIFIED PRECEDENTS:\n"
            for f in previous_findings[:10]:
                if f.agent_role == AgentRole.PRECEDENT_HUNTER:
                    previous_context += f"- {f.case_name}: {f.finding[:100]}...\n"
        
        for case in cases[:5]:
            try:
                case_text = self._get_case_text(case)
                if not case_text:
                    continue
                
                prompt = f"""{self.agent_prompts[AgentRole.PRECEDENT_HUNTER]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}
Citation: {case.get('citation', 'N/A')}

OPINION EXCERPT:
{case_text[:2000]}

RESEARCH QUESTION:
{question}
{previous_context}

Identify:
1. What precedents does this case cite?
2. How is this case similar/different from others?
3. What makes this case binding or persuasive?
4. Key distinguishing factors"""

                response = await self._ask_llm(prompt, max_tokens=700)
                
                findings.append(AgentFinding(
                    agent_role=AgentRole.PRECEDENT_HUNTER,
                    cycle=cycle,
                    case_name=case.get('case_name', 'Unknown'),
                    finding=response,
                    confidence=0.75,
                    supporting_text=case_text[:500]
                ))
                
            except Exception as e:
                logger.error(f"Precedent hunter error: {e}")
        
        logger.info(f"    ✓ Precedent Hunter: {len(findings)} findings")
        return findings
    
    async def _run_legal_principles(self, question: str, cases: List[Dict], cycle: int) -> List[AgentFinding]:
        """Legal Principles Agent: Extract legal doctrines and rules"""
        logger.info(f"  ⚖️  Legal Principles analyzing {len(cases)} cases...")
        
        findings = []
        
        for case in cases[:5]:
            try:
                case_text = self._get_case_text(case)
                if not case_text:
                    continue
                
                prompt = f"""{self.agent_prompts[AgentRole.LEGAL_PRINCIPLES]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}

OPINION EXCERPT:
{case_text[:2000]}

RESEARCH QUESTION:
{question}

Extract:
1. What legal principles/doctrines are discussed?
2. What rules or tests does the court apply?
3. What standards of review or burdens of proof?
4. How do these principles apply to the question?

Quote specific passages."""

                response = await self._ask_llm(prompt, max_tokens=700)
                
                findings.append(AgentFinding(
                    agent_role=AgentRole.LEGAL_PRINCIPLES,
                    cycle=cycle,
                    case_name=case.get('case_name', 'Unknown'),
                    finding=response,
                    confidence=0.85,
                    supporting_text=case_text[:500]
                ))
                
            except Exception as e:
                logger.error(f"Legal principles error: {e}")
        
        logger.info(f"    ✓ Legal Principles: {len(findings)} findings")
        return findings
    
    async def _synthesize_findings(self, question: str, findings: List[AgentFinding], all_cases: List[Dict]) -> str:
        """Synthesis Agent: Combine all findings into comprehensive memo"""
        logger.info(f"  📝 Synthesis Agent combining {len(findings)} findings...")
        
        # Organize findings by agent type
        case_analyses = [f for f in findings if f.agent_role == AgentRole.CASE_ANALYST]
        precedents = [f for f in findings if f.agent_role == AgentRole.PRECEDENT_HUNTER]
        principles = [f for f in findings if f.agent_role == AgentRole.LEGAL_PRINCIPLES]
        
        # Build synthesis prompt
        synthesis_context = f"""
RESEARCH QUESTION:
{question}

TOTAL CASES ANALYZED: {len(all_cases)}
RESEARCH CYCLES: {self.max_cycles}
TOTAL FINDINGS: {len(findings)}

CASE ANALYSES ({len(case_analyses)} findings):
"""
        for f in case_analyses[:10]:
            synthesis_context += f"\n{f.case_name}:\n{f.finding}\n"
        
        synthesis_context += f"\n\nPRECEDENT ANALYSIS ({len(precedents)} findings):\n"
        for f in precedents[:10]:
            synthesis_context += f"\n{f.case_name}:\n{f.finding}\n"
        
        synthesis_context += f"\n\nLEGAL PRINCIPLES ({len(principles)} findings):\n"
        for f in principles[:10]:
            synthesis_context += f"\n{f.case_name}:\n{f.finding}\n"
        
        prompt = f"""{self.agent_prompts[AgentRole.SYNTHESIS]}

{synthesis_context}

Create a comprehensive legal research memo that synthesizes ALL agent findings above into:

1. EXECUTIVE SUMMARY
   - Research question and scope
   - Key findings across all analyses

2. LEGAL FRAMEWORK
   - Governing legal principles identified by agents
   - Applicable tests and standards

3. CASE LAW ANALYSIS
   - Deep dive into most relevant cases
   - How precedents interact
   - Key holdings and reasoning

4. SYNTHESIS & APPLICATION
   - How do all findings come together?
   - Patterns across multiple perspectives
   - Conflicts or tensions in the law

5. PRACTICAL GUIDANCE
   - Strongest arguments
   - Potential weaknesses
   - Recommended strategy

Use proper legal citations and quote from the agent findings."""

        synthesis = await self._ask_llm(prompt, max_tokens=3500, temperature=0.4)
        
        logger.info(f"    ✓ Synthesis complete ({len(synthesis)} chars)")
        
        return synthesis
    
    def _get_case_text(self, case: Dict) -> str:
        """Extract opinion text from case dict"""
        return case.get('opinion_text', case.get('snippet', ''))
    
    async def _ask_llm(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.5) -> str:
        """Ask LLM with given prompt"""
        try:
            messages = [
                {"role": "system", "content": "You are a specialized legal research assistant."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"[Error: {str(e)}]"
    
    def _create_batches(self, cases: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split cases into batches"""
        return [cases[i:i + batch_size] for i in range(0, len(cases), batch_size)]
    
    def _finding_to_dict(self, finding: AgentFinding) -> Dict:
        """Convert AgentFinding to dictionary"""
        return {
            'agent_role': finding.agent_role.value,
            'cycle': finding.cycle,
            'case_name': finding.case_name,
            'finding': finding.finding,
            'confidence': finding.confidence,
            'supporting_text': finding.supporting_text
        }
    
    def _cycle_to_dict(self, cycle: ResearchCycle) -> Dict:
        """Convert ResearchCycle to dictionary"""
        return {
            'cycle_number': cycle.cycle_number,
            'cases_analyzed': len(cycle.cases_analyzed),
            'findings_generated': len(cycle.agent_findings),
            'refinements': cycle.refinements
        }
    
    # Agent Prompt Definitions
    
    def _case_analyst_prompt(self) -> str:
        return """You are a CASE ANALYST agent specializing in extracting facts and holdings from legal opinions.

Your role:
- Identify key facts relevant to the research question
- Extract the court's holding and reasoning
- Note procedural posture
- Highlight relevant quotations from the opinion

Be precise, cite specific passages, and focus on facts that matter."""
    
    def _precedent_hunter_prompt(self) -> str:
        return """You are a PRECEDENT HUNTER agent specializing in identifying relevant precedents and distinguishing cases.

Your role:
- Identify what precedents this case cites
- Determine binding vs persuasive authority
- Note how this case is similar/different from others
- Identify key distinguishing factors
- Track evolution of legal doctrines

Focus on connections between cases and precedential value."""
    
    def _legal_principles_prompt(self) -> str:
        return """You are a LEGAL PRINCIPLES agent specializing in extracting legal doctrines, rules, and tests.

Your role:
- Identify governing legal principles and doctrines
- Extract specific legal tests or standards
- Note burdens of proof and standards of review
- Explain how principles apply to facts
- Track policy considerations

Focus on the law itself, not just the facts."""
    
    def _synthesis_prompt(self) -> str:
        return """You are a SYNTHESIS agent responsible for combining findings from multiple specialized agents into a comprehensive legal memo.

Your role:
- Integrate findings from Case Analyst, Precedent Hunter, and Legal Principles agents
- Identify patterns and themes across all analyses
- Resolve contradictions or tensions
- Provide holistic view of the legal landscape
- Deliver practical, actionable guidance

Create a polished memo that synthesizes all perspectives."""


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '..')
    from llm.llm_client import LLMClient
    
    # Initialize
    llm = LLMClient()
    researcher = MultiAgentLegalResearcher(llm, batch_size=10, max_cycles=3)
    
    # Mock cases for testing
    test_cases = [
        {
            'case_name': 'Test Case v. Example',
            'citation': '123 F.3d 456',
            'court': 'Test Court',
            'opinion_text': 'This is a test opinion with some legal analysis...'
        }
    ] * 15
    
    # Run research
    async def test():
        results = await researcher.research_async(
            question="Test legal question",
            cases=test_cases
        )
        print(f"Findings: {results['total_findings']}")
        print(f"Synthesis:\n{results['synthesis']}")
    
    asyncio.run(test())
