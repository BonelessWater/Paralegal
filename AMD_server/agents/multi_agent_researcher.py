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
import os
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from sentence_transformers import SentenceTransformer
import numpy as np

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
    
    async def _filter_top_cases_with_rag(self, question: str, cases: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Use RAG embeddings to filter down to most relevant cases.
        
        Args:
            question: Research question
            cases: All scraped cases (with metadata, no opinion text)
            top_n: Number of top cases to select
            
        Returns:
            Top N most relevant cases
        """
        logger.info(f"🔍 Filtering {len(cases)} cases to top {top_n} using RAG embeddings...")
        
        # Load sentence transformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Embed the research question
        question_embedding = model.encode([question], convert_to_numpy=True)[0]
        
        # Create text representations for each case (from metadata)
        case_texts = []
        for case in cases:
            # Build text from available metadata
            text_parts = []
            if case.get('case_name'):
                text_parts.append(f"Case: {case['case_name']}")
            if case.get('citation'):
                text_parts.append(f"Citation: {case['citation']}")
            if case.get('court'):
                text_parts.append(f"Court: {case['court']}")
            if case.get('snippet'):
                text_parts.append(f"Snippet: {case['snippet']}")
            
            case_texts.append(" | ".join(text_parts) if text_parts else "No case information")
        
        # Embed all case texts
        case_embeddings = model.encode(case_texts, convert_to_numpy=True, show_progress_bar=False)
        
        # Calculate cosine similarities
        similarities = np.dot(case_embeddings, question_embedding) / (
            np.linalg.norm(case_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        # Get top N indices
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Select top cases
        top_cases = [cases[i] for i in top_indices]
        
        logger.info(f"✅ Selected top {len(top_cases)} cases (similarity range: {similarities[top_indices[-1]]:.3f} - {similarities[top_indices[0]]:.3f})")
        
        return top_cases
    
    async def _fetch_opinion_texts(self, cases: List[Dict]) -> List[Dict]:
        """
        Fetch full opinion text for selected cases from CourtListener API.
        
        Args:
            cases: Cases with URLs but no opinion text
            
        Returns:
            Cases enriched with opinion_text field
        """
        logger.info(f"📥 Fetching full opinion text for {len(cases)} cases...")
        
        api_token = os.getenv('COURTLISTENER_API_TOKEN', '')
        if not api_token:
            logger.warning("No CourtListener API token found - opinion text will remain empty")
            return cases
        
        headers = {'Authorization': f'Token {api_token}'}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for case in cases:
                url = case.get('url', '')
                if url:
                    tasks.append(self._fetch_single_opinion(session, case, url, headers))
                else:
                    tasks.append(asyncio.sleep(0, result=case))  # Return case unchanged
            
            enriched_cases = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_cases = [c for c in enriched_cases if not isinstance(c, Exception)]
        
        # Count how many have opinion text
        with_text = sum(1 for c in valid_cases if c.get('opinion_text'))
        logger.info(f"✅ Fetched opinion text for {with_text}/{len(valid_cases)} cases")
        
        return valid_cases
    
    async def _fetch_single_opinion(self, session: aiohttp.ClientSession, case: Dict, url: str, headers: Dict) -> Dict:
        """Fetch opinion text for a single case"""
        try:
            # CourtListener URLs are like: https://www.courtlistener.com/opinion/4250579/state-v-montgomery-slip-opinion/
            # We need to extract the opinion ID and use the API endpoint
            # API endpoint: https://www.courtlistener.com/api/rest/v4/opinions/{id}/
            
            # Extract opinion ID from URL
            parts = url.rstrip('/').split('/')
            opinion_id = None
            for i, part in enumerate(parts):
                if part == 'opinion' and i + 1 < len(parts):
                    opinion_id = parts[i + 1]
                    break
            
            if not opinion_id:
                logger.debug(f"✗ Could not extract opinion ID from URL: {url}")
                return case
            
            # Construct API URL
            api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
            
            async with session.get(api_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    # Opinion text is in 'html_with_citations', 'html', 'plain_text', or 'html_lawbox'
                    opinion_text = (
                        data.get('html_with_citations') or 
                        data.get('html') or 
                        data.get('plain_text') or 
                        data.get('html_lawbox') or
                        data.get('xml_harvard') or
                        ''
                    )
                    
                    # Strip HTML tags if present to get plain text
                    if opinion_text and '<' in opinion_text:
                        # Simple HTML stripping - just remove tags
                        import re
                        opinion_text = re.sub(r'<[^>]+>', ' ', opinion_text)
                        opinion_text = re.sub(r'\s+', ' ', opinion_text).strip()
                    
                    # Limit to reasonable size (4000 chars to avoid context overflow)
                    if opinion_text:
                        trimmed_text = opinion_text[:4000]
                        case['opinion_text'] = trimmed_text
                        logger.info(f"✓ Fetched {len(trimmed_text)} chars (from {len(opinion_text)}) for {case.get('case_name', 'Unknown')[:50]}")
                    else:
                        logger.warning(f"✗ No opinion text in response for {case.get('case_name', 'Unknown')[:50]}")
                else:
                    logger.warning(f"✗ Failed to fetch opinion (status {response.status}): {case.get('case_name', 'Unknown')[:50]}")
        except Exception as e:
            logger.warning(f"✗ Error fetching opinion: {e}")
        
        return case
    
    async def research_async(self, 
                            question: str, 
                            cases: List[Dict],
                            previous_findings: Optional[List[AgentFinding]] = None) -> Dict[str, Any]:
        """
        Execute multi-agent iterative research.
        
        Args:
            question: Legal research question
            cases: List of case dictionaries (metadata only, no opinion text)
            previous_findings: Findings from previous cycles (for refinement)
            
        Returns:
            Comprehensive research results with all agent findings and synthesis
        """
        logger.info(f"🔬 Starting multi-agent research on {len(cases)} cases")
        logger.info(f"Question: {question}")
        
        # STEP 1: Filter to top N cases using RAG embeddings
        top_cases = await self._filter_top_cases_with_rag(question, cases, top_n=10)
        
        # STEP 2: Fetch full opinion text for top cases
        enriched_cases = await self._fetch_opinion_texts(top_cases)
        
        # STEP 3: Run multi-agent analysis on enriched cases
        logger.info(f"🎯 Running multi-agent analysis on {len(enriched_cases)} cases with opinion text")
        
        all_findings = []
        
        # Split cases into batches (should only be 1 batch of 10 now)
        case_batches = self._create_batches(enriched_cases, self.batch_size)
        
        # Execute research cycles
        for cycle_num in range(self.max_cycles):
            logger.debug(f"\n{'='*70}")
            logger.debug(f"CYCLE {cycle_num + 1}/{self.max_cycles}")
            logger.debug(f"{'='*70}")
            
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
        """Run all specialized agents on each case individually (one case per agent call)"""
        
        findings = []
        
        # Process each case individually with all agents in parallel
        # This keeps prompts small: 1 case + agent instructions = ~2000 chars
        tasks = []
        for case in cases[:5]:  # Top 5 cases per cycle
            case_text = self._get_case_text(case)
            if not case_text:
                continue
            
            # Run all 3 agents on this ONE case in parallel
            tasks.append(self._analyze_single_case(question, case, case_text, cycle_num, previous_findings))
        
        # Execute all case analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect findings
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent error: {result}")
            elif result:
                findings.extend(result)
        
        logger.info(f"Cycle {cycle_num + 1}: Generated {len(findings)} findings from {len(cases)} cases")
        
        return findings
    
    async def _analyze_single_case(self, 
                                   question: str, 
                                   case: Dict, 
                                   case_text: str,
                                   cycle: int,
                                   previous_findings: List[AgentFinding]) -> List[AgentFinding]:
        """Run all agents on a SINGLE case in parallel to minimize context per prompt"""
        
        findings = []
        
        # Run all 3 agents on this one case simultaneously
        tasks = [
            self._run_case_analyst_single(question, case, case_text, cycle),
            self._run_precedent_hunter_single(question, case, case_text, cycle, previous_findings),
            self._run_legal_principles_single(question, case, case_text, cycle)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Single case analysis error: {result}")
            elif result:
                findings.append(result)
        
        return findings
    
    async def _run_case_analyst_single(self, question: str, case: Dict, case_text: str, cycle: int) -> AgentFinding:
        """Case Analyst: Extract facts and holdings from ONE case"""
        try:
            prompt = f"""{self.agent_prompts[AgentRole.CASE_ANALYST]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}
Citation: {case.get('citation', 'N/A')}
Court: {case.get('court', 'Unknown')}

OPINION EXCERPT:
{case_text[:1500]}

RESEARCH QUESTION:
{question}

Analyze this case and extract:
1. Key facts relevant to the research question
2. The court's holding
3. The reasoning
4. How it relates to the research question

Be specific and quote the opinion."""

            response = await self._ask_llm(prompt, max_tokens=800)
            
            return AgentFinding(
                agent_role=AgentRole.CASE_ANALYST,
                cycle=cycle,
                case_name=case.get('case_name', 'Unknown'),
                finding=response,
                confidence=0.8,
                supporting_text=case_text[:500]
            )
            
        except Exception as e:
            logger.error(f"Case analyst error for {case.get('case_name')}: {e}")
            return None
    
    async def _run_precedent_hunter_single(self, 
                                          question: str, 
                                          case: Dict,
                                          case_text: str,
                                          cycle: int,
                                          previous_findings: List[AgentFinding]) -> AgentFinding:
        """Precedent Hunter: Identify relevant precedents from ONE case"""
        try:
            # Build minimal context from previous findings (max 3 to keep prompt small)
            previous_context = ""
            if previous_findings:
                prev_precedents = [f for f in previous_findings if f.agent_role == AgentRole.PRECEDENT_HUNTER][:3]
                if prev_precedents:
                    previous_context = "\n\nPREVIOUSLY IDENTIFIED:\n"
                    for f in prev_precedents:
                        previous_context += f"- {f.case_name}: {f.finding[:80]}...\n"
            
            prompt = f"""{self.agent_prompts[AgentRole.PRECEDENT_HUNTER]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}
Citation: {case.get('citation', 'N/A')}

OPINION EXCERPT:
{case_text[:1500]}

RESEARCH QUESTION:
{question}
{previous_context}

Identify:
1. What precedents does this case cite?
2. How is this case similar/different from others?
3. What makes this case binding or persuasive?
4. Key distinguishing factors"""

            response = await self._ask_llm(prompt, max_tokens=700)
            
            return AgentFinding(
                agent_role=AgentRole.PRECEDENT_HUNTER,
                cycle=cycle,
                case_name=case.get('case_name', 'Unknown'),
                finding=response,
                confidence=0.75,
                supporting_text=case_text[:500]
            )
            
        except Exception as e:
            logger.error(f"Precedent hunter error for {case.get('case_name')}: {e}")
            return None
    
    async def _run_legal_principles_single(self, question: str, case: Dict, case_text: str, cycle: int) -> AgentFinding:
        """Legal Principles Agent: Extract doctrines from ONE case"""
        try:
            prompt = f"""{self.agent_prompts[AgentRole.LEGAL_PRINCIPLES]}

CASE TO ANALYZE:
{case.get('case_name', 'Unknown')}

OPINION EXCERPT:
{case_text[:1500]}

RESEARCH QUESTION:
{question}

Extract:
1. What legal principles/doctrines are discussed?
2. What rules or tests does the court apply?
3. What standards of review or burdens of proof?
4. How do these principles apply to the question?

Quote specific passages."""

            response = await self._ask_llm(prompt, max_tokens=700)
            
            return AgentFinding(
                agent_role=AgentRole.LEGAL_PRINCIPLES,
                cycle=cycle,
                case_name=case.get('case_name', 'Unknown'),
                finding=response,
                confidence=0.85,
                supporting_text=case_text[:500]
            )
            
        except Exception as e:
            logger.error(f"Legal principles error for {case.get('case_name')}: {e}")
            return None
    
    # OLD BATCH METHODS - DEPRECATED (kept for reference, can be removed later)
    async def _run_case_analyst(self, question: str, cases: List[Dict], cycle: int) -> List[AgentFinding]:
        """Case Analyst: Extract facts and holdings from cases"""
        logger.debug(f"  🔍 Case Analyst analyzing {len(cases)} cases...")
        
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
{case_text[:1500]}

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
        
        logger.debug(f"    ✓ Case Analyst: {len(findings)} findings")
        return findings
    
    async def _run_precedent_hunter(self, 
                                    question: str, 
                                    cases: List[Dict], 
                                    cycle: int,
                                    previous_findings: List[AgentFinding]) -> List[AgentFinding]:
        """Precedent Hunter: Identify relevant precedents and distinguish cases"""
        logger.debug(f"  🎯 Precedent Hunter analyzing {len(cases)} cases...")
        
        findings = []
        
        # Build context from previous findings (limit to 5 to avoid context overflow)
        previous_context = ""
        if previous_findings:
            previous_context = "\n\nPREVIOUSLY IDENTIFIED PRECEDENTS:\n"
            for f in previous_findings[:5]:
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
{case_text[:1500]}

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
        
        logger.debug(f"    ✓ Precedent Hunter: {len(findings)} findings")
        return findings
    
    async def _run_legal_principles(self, question: str, cases: List[Dict], cycle: int) -> List[AgentFinding]:
        """Legal Principles Agent: Extract legal doctrines and rules"""
        logger.debug(f"  ⚖️  Legal Principles analyzing {len(cases)} cases...")
        
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
{case_text[:1500]}

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
        
        logger.debug(f"    ✓ Legal Principles: {len(findings)} findings")
        return findings
    
    async def _synthesize_findings(self, question: str, findings: List[AgentFinding], all_cases: List[Dict]) -> str:
        """Synthesis Agent: Combine all findings into comprehensive memo"""
        logger.debug(f"  📝 Synthesis Agent combining {len(findings)} findings...")
        
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
        
        logger.debug(f"    ✓ Synthesis complete ({len(synthesis)} chars)")
        
        return synthesis
    
    def _get_case_text(self, case: Dict) -> str:
        """Extract opinion text from case dict"""
        return case.get('opinion_text', case.get('snippet', ''))
    
    async def _ask_llm(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.5) -> str:
        """Ask LLM with given prompt"""
        try:
            # Validate prompt size
            prompt_length = len(prompt)
            if prompt_length > 12000:  # ~3000 tokens at 4 chars/token
                logger.warning(f"⚠️  Prompt very large: {prompt_length} chars, truncating...")
                prompt = prompt[:12000]
            
            # Saul-7B requires alternating user/assistant roles - no system messages
            # Prepend system instruction to the user prompt instead
            full_prompt = "You are a specialized legal research assistant.\n\n" + prompt
            
            messages = [
                {"role": "user", "content": full_prompt}
            ]
            
            response = self.llm.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            logger.error(f"Prompt length: {len(prompt)} chars")
            logger.error(f"Prompt preview: {prompt[:200]}...")
            return ""
    
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
