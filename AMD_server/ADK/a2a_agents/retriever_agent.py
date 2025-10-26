# file: retriever_agent.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from collections import Counter
import math

# ---------------- A2A-ish envelopes ----------------
class TaskEnvelope(BaseModel):
    task_id: str
    skill: str = Field(..., description="retrieve")
    input: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class ResultEnvelope(BaseModel):
    task_id: str
    status: str  # "ok" | "error"
    output: Dict[str, Any]
    trace: List[Dict[str, Any]] = []

# ---------------- App + skill ----------------------
app = FastAPI(title="RetrieverAgent (A2A)")

def _score(doc_text: str, query_terms: List[str]) -> float:
    tokens = [t.lower() for t in doc_text.split()]
    counts = Counter(tokens)
    score = 0.0
    for qt in query_terms:
        score += counts.get(qt.lower(), 0)
    # gentle length penalty
    score = score / math.sqrt(len(tokens) + 1)
    return score

def skill_retrieve(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      {
        "query": "motion to dismiss statute of limitations",
        "documents": [{"id": "...", "text": "...", "meta": {...}}, ...],
        "top_k": 3
      }
    Output:
      {
        "top_docs": [{"id": "...", "score": 1.23, "snippet": "...", "meta": {...}}, ...],
        "context": "concatenated relevant snippets"
      }
    """
    query = inp.get("query", "")
    docs = inp.get("documents", [])
    top_k = int(inp.get("top_k", 3))
    terms = [w for w in query.split() if w.strip()]

    scored = []
    for d in docs:
        s = _score(d.get("text", ""), terms)
        if s > 0:
            snippet = d.get("text", "")[:1000]
            scored.append({"id": d.get("id"), "score": s, "snippet": snippet, "meta": d.get("meta", {})})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]
    context = "\n\n---\n\n".join([t["snippet"] for t in top]) if top else ""

    return {"top_docs": top, "context": context}

@app.post("/a2a/task", response_model=ResultEnvelope)
def handle_task(task: TaskEnvelope):
    ts = datetime.now(timezone.utc).isoformat()
    if task.skill != "retrieve":
        return ResultEnvelope(
            task_id=task.task_id,
            status="error",
            output={"error": "unknown skill", "known_skills": ["retrieve"]},
            trace=[{"ts": ts, "event": "skill_not_found"}],
        )
    out = skill_retrieve(task.input)
    return ResultEnvelope(task_id=task.task_id, status="ok", output=out, trace=[{"ts": ts, "event": "ran"}])

if __name__ == "__main__":
    uvicorn.run("retriever_agent:app", host="0.0.0.0", port=8011, reload=True)
