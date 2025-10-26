# file: legal_nlp_agent.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from llm_saul import complete

class TaskEnvelope(BaseModel):
    task_id: str
    skill: str = Field(..., description="legal_summarize | issue_spot | bluebook_citations")
    input: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class ResultEnvelope(BaseModel):
    task_id: str
    status: str
    output: Dict[str, Any]
    trace: List[Dict[str, Any]] = []

SYSTEM_PREAMBLE = """You are a meticulous legal analyst. 
- Prefer U.S. legal reasoning style.
- Be concise, precise, and avoid hallucinations.
- If unsure, say what is missing.
"""

def _prompt(header: str, body: str) -> str:
    return f"{SYSTEM_PREAMBLE}\n\n{header}\n\n{body}\n"

def skill_legal_summarize(inp: Dict[str, Any]) -> Dict[str, Any]:
    text = inp.get("text", "")
    header = "TASK: Summarize the legal document in 5–8 sentences for an attorney."
    body = f"Document:\n{text}\n\nFocus on: parties, posture, issues, rules, holding, reasoning."
    out = complete(_prompt(header, body), max_tokens=400, temperature=0.2)
    return {"summary": out}

def skill_issue_spot(inp: Dict[str, Any]) -> Dict[str, Any]:
    text = inp.get("text", "")
    header = "TASK: Issue spotting. List discrete legal issues with brief explanations."
    body = f"Document:\n{text}\n\nReturn bullets. Include statutes/case-law hints if context implies."
    out = complete(_prompt(header, body), max_tokens=400, temperature=0.2)
    bullets = [line.strip("-• ").strip() for line in out.splitlines() if line.strip()]
    return {"issues": bullets}

def skill_bluebook_citations(inp: Dict[str, Any]) -> Dict[str, Any]:
    text = inp.get("text", "")
    header = "TASK: Suggest likely Bluebook-formatted citations found or implied by the text."
    body = f"""Document:\n{text}\n
Return 3–8 plausible citations (case or statute), Bluebook-ish. If the doc lacks explicit cites,
infer likely anchors (e.g., 'Fed. R. Civ. P. 12(b)(6)', 'Erie R.R. v. Tompkins, 304 U.S. 64 (1938)').
If uncertain, mark as 'possible'. Do NOT invent fake reporters; prefer generic 'possible' labels.
"""
    out = complete(_prompt(header, body), max_tokens=400, temperature=0.2)
    cits = [line.strip("-• ").strip() for line in out.splitlines() if line.strip()]
    return {"citations": cits}

SKILLS = {
    "legal_summarize": skill_legal_summarize,
    "issue_spot": skill_issue_spot,
    "bluebook_citations": skill_bluebook_citations,
}

app = FastAPI(title="LegalNLPAgent (A2A)")

@app.post("/a2a/task", response_model=ResultEnvelope)
def handle_task(task: TaskEnvelope):
    ts = datetime.now(timezone.utc).isoformat()
    if task.skill not in SKILLS:
        return ResultEnvelope(
            task_id=task.task_id, status="error",
            output={"error": "unknown skill", "known_skills": list(SKILLS.keys())},
            trace=[{"ts": ts, "event": "skill_not_found"}],
        )
    try:
        out = SKILLS[task.skill](task.input)
        return ResultEnvelope(task_id=task.task_id, status="ok", output=out, trace=[{"ts": ts, "event": "ran", "skill": task.skill}])
    except Exception as e:
        return ResultEnvelope(task_id=task.task_id, status="error", output={"error": repr(e)}, trace=[{"ts": ts, "event": "exception"}])

if __name__ == "__main__":
    uvicorn.run("legal_nlp_agent:app", host="0.0.0.0", port=8012, reload=True)
