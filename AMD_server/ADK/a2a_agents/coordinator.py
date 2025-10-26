# file: coordinator.py
import json
import uuid
import asyncio
import aiohttp
from pathlib import Path
from typing import Any, Dict, List

RETRIEVER_CARD = Path("retriever_card.json")
LEGAL_CARD = Path("legal_nlp_card.json")

def load_card(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text())

async def call_agent(session: aiohttp.ClientSession, endpoint: str, skill: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    envelope = {
        "task_id": str(uuid.uuid4()),
        "skill": skill,
        "input": payload,
        "context": {"caller": "Coordinator", "run_id": str(uuid.uuid4())},
    }
    async with session.post(endpoint, json=envelope, timeout=180) as resp:
        resp.raise_for_status()
        return await resp.json()

async def run_workflow(query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
    retriever = load_card(RETRIEVER_CARD)["endpoint"]
    legal = load_card(LEGAL_CARD)["endpoint"]

    async with aiohttp.ClientSession() as session:
        # Step 1 (RetrieverAgent): get focused context
        r = await call_agent(session, retriever, "retrieve", {"query": query, "documents": documents, "top_k": top_k})
        if r.get("status") != "ok":
            raise RuntimeError(f"Retriever failed: {r}")
        ctx = r["output"]["context"]

        # Step 2 (LegalNLPAgent): sequential summarize -> issues
        res_sum = await call_agent(session, legal, "legal_summarize", {"text": ctx})
        if res_sum.get("status") != "ok":
            raise RuntimeError(f"Summarize failed: {res_sum}")
        summary = res_sum["output"]["summary"]

        res_issues = await call_agent(session, legal, "issue_spot", {"text": summary})
        if res_issues.get("status") != "ok":
            raise RuntimeError(f"Issue spotting failed: {res_issues}")
        issues = res_issues["output"]["issues"]

        # Step 3 (parallel): issues on full context + Bluebook citations
        t1 = call_agent(session, legal, "issue_spot", {"text": ctx})
        t2 = call_agent(session, legal, "bluebook_citations", {"text": ctx})
        p_issues, p_cites = await asyncio.gather(t1, t2)

        if p_issues.get("status") != "ok":
            raise RuntimeError(f"Parallel issue spotting failed: {p_issues}")
        if p_cites.get("status") != "ok":
            raise RuntimeError(f"Citations failed: {p_cites}")

        return {
            "query": query,
            "retrieval": r["output"]["top_docs"],
            "analysis": {
                "summary_from_ctx": summary,
                "issues_from_summary": issues,
                "issues_from_full_ctx": p_issues["output"]["issues"],
                "bluebook_citation_hints": p_cites["output"]["citations"],
            },
        }

if __name__ == "__main__":
    # Minimal in-memory "corpus" (you can swap this for your parsed PDFs/OCR later)
    docs = [
        {
            "id": "complaint_001",
            "text": (
                "IN THE UNITED STATES DISTRICT COURT... Plaintiff alleges breach of contract and fraud. "
                "Defendant moves to dismiss under Fed. R. Civ. P. 12(b)(6), arguing the complaint fails to state a claim. "
                "The contract contains a New York choice-of-law clause. The alleged misrepresentations concern revenue projections."
            ),
            "meta": {"type": "complaint", "court": "USDC"},
        },
        {
            "id": "order_042",
            "text": (
                "ORDER: The Court considers Defendant's Rule 12(b)(6) motion. To survive dismissal, a complaint must state a plausible claim. "
                "See Ashcroft v. Iqbal, 556 U.S. 662 (2009); Bell Atl. Corp. v. Twombly, 550 U.S. 544 (2007). The statute of limitations defense "
                "is premature on the pleadings unless apparent on the face of the complaint."
            ),
            "meta": {"type": "order", "court": "USDC"},
        },
        {
            "id": "statute_ny_limitations",
            "text": (
                "Under New York law, breach of contract claims generally carry a six-year statute of limitations, N.Y. CPLR 213(2). "
                "Fraud claims typically have the greater of six years from accrual or two years from discovery, CPLR 213(8)."
            ),
            "meta": {"type": "statute", "jurisdiction": "NY"},
        },
    ]
    out = asyncio.run(run_workflow("12(b)(6) motion statute limitations NY breach of contract fraud", docs, top_k=3))
    print(json.dumps(out, indent=2))
