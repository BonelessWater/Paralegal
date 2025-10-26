"""
Saul-backed agent definitions (no A2A). Edit this file to add/remove agents.
The orchestrator imports AVAILABLE_AGENTS and runs them in parallel.
"""

from __future__ import annotations
import os
import asyncio
from typing import Any, Dict, Callable, Awaitable, TypedDict
from openai import OpenAI

# ---------------- Saul client (vLLM) ----------------
SAUL_BASE_URL = os.getenv("SAUL_BASE_URL", "http://localhost:8000/v1")
SAUL_MODEL    = os.getenv("SAUL_MODEL", "Equall/Saul-7B-Instruct-v1")
SAUL_API_KEY  = os.getenv("SAUL_API_KEY", "dummy")
SAUL_TEMP     = float(os.getenv("SAUL_TEMP", "0.2"))
SAUL_MAXTOK   = int(os.getenv("SAUL_MAXTOK", "512"))

_client = OpenAI(base_url=SAUL_BASE_URL, api_key=SAUL_API_KEY)

def _saul_complete(prompt: str, max_tokens: int = SAUL_MAXTOK, temperature: float = SAUL_TEMP) -> str:
    resp = _client.completions.create(
        model=SAUL_MODEL,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (resp.choices[0].text or "").strip()

async def saul_complete(prompt: str, max_tokens: int = SAUL_MAXTOK, temperature: float = SAUL_TEMP) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _saul_complete, prompt, max_tokens, temperature)


# -------------- Shared prompt bits -------------------
SYS = (
    "You are a careful U.S. legal analyst. Be precise, concise, and avoid hallucinations. "
    "Use short Bluebook-style cites when certain; mark 'possible' when uncertain."
)

def p_case_law(issue: str, jurisdiction: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Case law research
Issue: {issue}
Jurisdiction: {jurisdiction}
Context (optional): {ctx}

Return 3–6 relevant precedents:
- Short Bluebook citation
- 1–2 line holding
- How it applies (1–2 lines)
- Distinguishing factors if any
"""

def p_statutes(issue: str, jurisdiction: str, terms: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Statutory & regulatory research
Issue: {issue}
Jurisdiction: {jurisdiction}
Search terms: {terms}
Context (optional): {ctx}

Return 3–8 likely authorities:
- Code section + title (or 'possible')
- 1–2 line excerpt/summary
- How it applies
Flag gaps to verify.
"""

def p_citations(raw_text: str) -> str:
    return f"""{SYS}

TASK: Extract/normalize citations
Text:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Case citations (normalized; mark 'possible' if unsure)
- Statute citations (normalized; mark 'possible' if unsure)
- Secondary sources (if any)
- Likely formatting errors/incomplete cites
"""


# -------------- Additional paralegal agents ----------------------

def p_contract_review(raw_text: str, focus_areas: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Contract review and risk assessment
Focus areas: {focus_areas if focus_areas else "General review"}
Context (optional): {ctx}

Contract text:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Key terms and obligations (both parties)
- Unusual or high-risk clauses
- Missing standard provisions (e.g., force majeure, arbitration, limitation of liability)
- Ambiguous language requiring clarification
- Recommendations for revision (if any)
"""

def p_fact_extraction(raw_text: str, issue: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Extract legally relevant facts
Issue/matter: {issue}
Context (optional): {ctx}

Source text:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Material facts (who, what, when, where)
- Dates, deadlines, and time-sensitive information
- Parties and their relationships
- Disputed vs. undisputed facts
- Evidentiary gaps or inconsistencies
- Facts requiring verification
"""

def p_timeline(raw_text: str, issue: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Create chronological timeline
Issue/matter: {issue}
Context (optional): {ctx}

Source text:
\"\"\"{raw_text.strip()}\"\"\"

Return chronological timeline with:
- Date/time (specific or approximate)
- Event description (brief)
- Source/evidence reference
- Legal significance (if any)
- Gaps in timeline requiring investigation

Format: Most recent first or specify if unclear.
"""

def p_discovery_analysis(raw_text: str, issue: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Discovery request analysis
Issue/matter: {issue}
Context (optional): {ctx}

Discovery text:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Summary of requests (categorized by type)
- Overly broad or vague requests
- Privileged or confidential information implicated
- Burdensome or disproportionate requests
- Missing or incomplete requests
- Suggested objections (with brief basis)
- Documents/information likely needed to respond
"""

def p_issue_spotting(raw_text: str, jurisdiction: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Legal issue identification
Jurisdiction: {jurisdiction}
Context (optional): {ctx}

Scenario/facts:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Primary legal issues (ranked by importance)
- Secondary or potential issues
- Applicable areas of law for each issue
- Elements that may be at issue
- Factual gaps affecting legal analysis
- Statute of limitations concerns (if any)
"""

def p_memo_drafting(issue: str, case_law: str, statutes: str, facts: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Draft concise legal research memo
Issue: {issue}
Context (optional): {ctx}

Available research:
Case law: {case_law}
Statutes: {statutes}
Facts: {facts}

Return structured memo (12–18 lines):
QUESTION PRESENTED: [1-2 lines]
BRIEF ANSWER: [2-3 lines]
APPLICABLE LAW: [3-5 lines with citations]
APPLICATION: [4-6 lines]
CONCLUSION: [2-3 lines]
NEXT STEPS: [1-2 lines if gaps exist]
"""

def p_privilege_log(raw_text: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Identify potentially privileged communications
Context (optional): {ctx}

Documents/communications:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Documents likely protected by attorney-client privilege
- Documents potentially protected by work product doctrine
- Date, author, recipient(s), and subject matter
- Type of privilege asserted
- Documents requiring further review
- Potential privilege waiver issues
"""

def p_compliance_check(raw_text: str, jurisdiction: str, regulations: str, ctx: str) -> str:
    return f"""{SYS}

TASK: Regulatory compliance analysis
Jurisdiction: {jurisdiction}
Applicable regulations: {regulations}
Context (optional): {ctx}

Activity/policy to review:
\"\"\"{raw_text.strip()}\"\"\"

Return:
- Regulatory requirements implicated
- Compliance gaps or violations (potential/actual)
- Required documentation or filings
- Deadlines or time-sensitive requirements
- Best practices recommendations
- Areas requiring legal review
"""


# -------------- Agent signatures ---------------------
class AgentInput(TypedDict, total=False):
    # generic inputs; agents will read what they need
    issue: str
    jurisdiction: str
    terms: str
    context: str
    raw_text: str

class AgentResult(TypedDict):
    name: str
    output: str
    status: str  # "ok" | "error"
    error: str | None


# -------------- Concrete agents ----------------------
async def case_law_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(p_case_law(inp.get("issue",""), inp.get("jurisdiction",""), inp.get("context","")))
        return {"name": "case_law", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "case_law", "output": "", "status": "error", "error": repr(e)}

async def statutes_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(p_statutes(inp.get("issue",""), inp.get("jurisdiction",""), inp.get("terms",""), inp.get("context","")))
        return {"name": "statutes", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "statutes", "output": "", "status": "error", "error": repr(e)}

async def citations_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(p_citations(inp.get("raw_text","")))
        return {"name": "citations", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "citations", "output": "", "status": "error", "error": repr(e)}

async def contract_review_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_contract_review(inp.get("raw_text",""), inp.get("terms",""), inp.get("context","")),
            max_tokens=800
        )
        return {"name": "contract_review", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "contract_review", "output": "", "status": "error", "error": repr(e)}

async def fact_extraction_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_fact_extraction(inp.get("raw_text",""), inp.get("issue",""), inp.get("context","")),
            max_tokens=600
        )
        return {"name": "fact_extraction", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "fact_extraction", "output": "", "status": "error", "error": repr(e)}

async def timeline_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_timeline(inp.get("raw_text",""), inp.get("issue",""), inp.get("context","")),
            max_tokens=700
        )
        return {"name": "timeline", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "timeline", "output": "", "status": "error", "error": repr(e)}

async def discovery_analysis_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_discovery_analysis(inp.get("raw_text",""), inp.get("issue",""), inp.get("context","")),
            max_tokens=800
        )
        return {"name": "discovery_analysis", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "discovery_analysis", "output": "", "status": "error", "error": repr(e)}

async def issue_spotting_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_issue_spotting(inp.get("raw_text",""), inp.get("jurisdiction",""), inp.get("context","")),
            max_tokens=600
        )
        return {"name": "issue_spotting", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "issue_spotting", "output": "", "status": "error", "error": repr(e)}

async def memo_drafting_agent(inp: AgentInput) -> AgentResult:
    try:
        case_law = inp.get("case_law", "")
        statutes = inp.get("statutes", "")
        facts = inp.get("raw_text", inp.get("context", ""))
        
        out = await saul_complete(
            p_memo_drafting(inp.get("issue",""), case_law, statutes, facts, inp.get("context","")),
            max_tokens=900,
            temperature=0.15
        )
        return {"name": "memo_drafting", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "memo_drafting", "output": "", "status": "error", "error": repr(e)}

async def privilege_log_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_privilege_log(inp.get("raw_text",""), inp.get("context","")),
            max_tokens=700
        )
        return {"name": "privilege_log", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "privilege_log", "output": "", "status": "error", "error": repr(e)}

async def compliance_check_agent(inp: AgentInput) -> AgentResult:
    try:
        out = await saul_complete(
            p_compliance_check(
                inp.get("raw_text",""), 
                inp.get("jurisdiction",""), 
                inp.get("terms",""), 
                inp.get("context","")
            ),
            max_tokens=700
        )
        return {"name": "compliance_check", "output": out, "status": "ok", "error": None}
    except Exception as e:
        return {"name": "compliance_check", "output": "", "status": "error", "error": repr(e)}


# -------------- 👇 Registry used by the orchestrator --------------
# Add a new parallel agent by inserting a new entry here.
# Key = skill name; Value = async callable(AgentInput) -> AgentResult
AVAILABLE_AGENTS: dict[str, Callable[[AgentInput], Awaitable[AgentResult]]] = {
    "case_law":           case_law_agent,
    "statutes":           statutes_agent,
    "citations":          citations_agent,
    "contract_review":    contract_review_agent,
    "fact_extraction":    fact_extraction_agent,
    "timeline":           timeline_agent,
    "discovery_analysis": discovery_analysis_agent,
    "issue_spotting":     issue_spotting_agent,
    "memo_drafting":      memo_drafting_agent,
    "privilege_log":      privilege_log_agent,
    "compliance_check":   compliance_check_agent,
}