# ADK/orchestrator.py
from __future__ import annotations
import argparse, asyncio, json, os, re, time, math
from typing import Any, Dict, List, Tuple
from openai import OpenAI

# Import all agents from the agents module
from basic_agents.agents import (
    AVAILABLE_AGENTS,          # parallel skills registry with all agents
    AgentInput,                # type for agent inputs
    saul_complete,             # shared completion function
)

# --------- tiny context reranker (unchanged) ---------
def _tok(s: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9_]+", s)]

def rerank_context(query: str, docs: List[Dict[str,Any]], top_k: int=5, max_chars: int=8000) -> str:
    if not docs: return ""
    q = _tok(query); N = len(docs)
    df: Dict[str,int] = {}
    for d in docs:
        toks = set(_tok(d.get("text","")))
        for t in set(q):
            if t in toks: df[t] = df.get(t,0)+1
    avg_len = sum(len(_tok(d.get("text",""))) for d in docs)/max(1,N)
    scored: List[Tuple[float, Dict[str,Any]]] = []
    for d in docs:
        toks = _tok(d.get("text","")); L = len(toks) or 1
        tf: Dict[str,int] = {}
        for t in toks: tf[t] = tf.get(t,0)+1
        s = 0.0
        for t in q:
            idf = math.log((N - df.get(t,0) + 0.5)/(df.get(t,0) + 0.5) + 1.0)
            s += idf * (tf.get(t,0)*(1.2+1)) / (tf.get(t,0) + 1.2*(1 - 0.75 + 0.75*L/avg_len))
        scored.append((s,d))
    scored.sort(key=lambda x: x[0], reverse=True)
    chunks = []
    for s,d in scored[:top_k]:
        meta = d.get("meta",{})
        chunks.append(f"[score={s:.2f}] {meta.get('id', d.get('id','doc'))} :: {d.get('text','')}")
    ctx = "\n\n---\n\n".join(chunks)
    return ctx if len(ctx)<=max_chars else ctx[:max_chars//2] + "\n\n[...]\n\n" + ctx[-max_chars//2:]

# --------- Saul client for final synthesis ---------
SAUL_BASE_URL = os.getenv("SAUL_BASE_URL", "http://localhost:8000/v1")
SAUL_MODEL    = os.getenv("SAUL_MODEL", "Equall/Saul-7B-Instruct-v1")
_client = OpenAI(base_url=SAUL_BASE_URL, api_key=os.getenv("SAUL_API_KEY","dummy"))

def saul_complete_sync(prompt: str, max_tokens: int = 650, temperature: float = 0.15) -> str:
    r = _client.completions.create(model=SAUL_MODEL, prompt=prompt, max_tokens=max_tokens, temperature=temperature)
    return (r.choices[0].text or "").strip()

# --------- Simple planner (no external plan_agent dependency) ---------
async def simple_planner(task: Dict[str,Any], available_skills: List[str]) -> Dict[str,Any]:
    """
    Simple heuristic planner that selects agents based on task content.
    Returns: {"skills": [...], "plan": "..."}
    """
    issue = task.get("issue", "").lower()
    raw_text = task.get("raw_text", "").lower()
    terms = task.get("terms", "").lower()
    
    selected_skills = []
    plan_parts = []
    
    # Always include case law and statutes for legal research
    if "case" in issue or "precedent" in issue or "law" in issue:
        selected_skills.append("case_law")
        plan_parts.append("Research relevant case law")
    
    if "statute" in issue or "regulatory" in issue or "code" in issue or terms:
        selected_skills.append("statutes")
        plan_parts.append("Research applicable statutes")
    
    # Add citations if raw_text contains citation-like patterns
    if raw_text and any(x in raw_text for x in ["v.", "§", "u.s.", "f.", "so."]):
        selected_skills.append("citations")
        plan_parts.append("Extract and normalize citations")
    
    # Contract-related
    if "contract" in issue or "agreement" in issue:
        selected_skills.append("contract_review")
        plan_parts.append("Review contract terms and risks")
    
    # Fact-based analysis
    if "fact" in issue or raw_text:
        selected_skills.append("fact_extraction")
        plan_parts.append("Extract material facts")
    
    # Timeline creation
    if "timeline" in issue or "chronolog" in issue or "sequence" in issue:
        selected_skills.append("timeline")
        plan_parts.append("Create chronological timeline")
    
    # Discovery
    if "discovery" in issue or "request" in issue:
        selected_skills.append("discovery_analysis")
        plan_parts.append("Analyze discovery requests")
    
    # Issue spotting for complex scenarios
    if "issue" in issue or "problem" in issue:
        selected_skills.append("issue_spotting")
        plan_parts.append("Identify legal issues")
    
    # Privilege
    if "privilege" in issue or "confidential" in issue or "attorney-client" in issue:
        selected_skills.append("privilege_log")
        plan_parts.append("Identify privileged materials")
    
    # Compliance
    if "complian" in issue or "regulation" in issue or "violation" in issue:
        selected_skills.append("compliance_check")
        plan_parts.append("Check regulatory compliance")
    
    # If memo is requested or we have multiple outputs
    if "memo" in issue or len(selected_skills) >= 3:
        selected_skills.append("memo_drafting")
        plan_parts.append("Draft research memo")
    
    # Ensure only available skills are selected
    selected_skills = [s for s in selected_skills if s in available_skills]
    
    # Default to basic research if nothing selected
    if not selected_skills:
        selected_skills = ["case_law", "statutes"]
        plan_parts = ["Research case law", "Research statutes"]
    
    plan = "; ".join(plan_parts) if plan_parts else "Basic legal research"
    
    return {
        "skills": selected_skills,
        "plan": plan
    }

# --------- orchestrated run ---------
async def run_orchestrated(
    issue: str, 
    jurisdiction: str, 
    terms: str, 
    raw_citation_text: str, 
    docs: List[Dict[str,Any]],
    selected_agents: List[str] | None = None
) -> Dict[str,Any]:
    """
    Main orchestration function that runs selected agents in parallel.
    
    Args:
        issue: Legal issue to research
        jurisdiction: Jurisdiction (e.g., "Florida state courts")
        terms: Search terms
        raw_citation_text: Text containing citations to extract
        docs: Document corpus for context
        selected_agents: Optional list of agent names to run. If None, uses planner.
    """
    t0 = time.time()
    
    # Build focused context once
    ctx_query = f"{issue} {jurisdiction} {terms}"
    ctx = rerank_context(ctx_query, docs, top_k=5)

    # 1) DETERMINE WHICH AGENTS TO RUN
    available = list(AVAILABLE_AGENTS.keys())
    
    if selected_agents:
        # User specified which agents to run
        chosen = [s for s in selected_agents if s in available]
        plan_text = f"Running user-selected agents: {', '.join(chosen)}"
    else:
        # Use simple planner
        task = {
            "issue": issue, 
            "jurisdiction": jurisdiction, 
            "terms": terms, 
            "raw_text": raw_citation_text, 
            "context": ctx
        }
        plan_result = await simple_planner(task, available)
        chosen = plan_result["skills"]
        plan_text = plan_result["plan"]

    if not chosen:
        return {
            "status": "no_agents_selected",
            "reason": "No agents were selected for this task.",
            "available_agents": available,
            "ctx_len": len(ctx),
            "build_time_sec": round(time.time()-t0, 3),
        }

    # 2) PARALLEL EXECUTION
    base_input: AgentInput = {
        "issue": issue, 
        "jurisdiction": jurisdiction, 
        "terms": terms, 
        "context": ctx, 
        "raw_text": raw_citation_text
    }
    
    tasks = [asyncio.create_task(AVAILABLE_AGENTS[name](base_input)) for name in chosen]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    outputs, errors = {}, []
    for r in results:
        if isinstance(r, Exception):
            errors.append(f"Exception: {repr(r)}")
        elif isinstance(r, dict):
            if r.get("status") == "ok":
                outputs[r["name"]] = r["output"]
            else:
                errors.append(f"{r.get('name', 'unknown')}: {r.get('error', 'unknown error')}")

    # 3) Synthesize final note
    join_prompt = f"""You are a careful U.S. legal analyst. Synthesize a concise note (12–18 lines).
Prefer certain authorities; mark 'possible' when uncertain.

Plan: {plan_text}

Focused context:
{ctx or '(none)'}

Agent outputs:
{json.dumps(outputs, indent=2)}

Return sections:
1) Issues
2) Key Authorities
3) Application to Facts
4) Gaps / Next Steps
"""
    note = saul_complete_sync(join_prompt)

    return {
        "status": "ok",
        "plan": plan_text,
        "agents_run": chosen,
        "agent_outputs": outputs,
        "errors": errors,
        "note": note,
        "ctx_len": len(ctx),
        "build_time_sec": round(time.time()-t0, 3),
    }

# --------- demo ----------
def demo_docs() -> List[Dict[str, Any]]:
    return [
        {"id":"order_042","meta":{"id":"order_042","court":"USDC"},
         "text":"ORDER: To survive Rule 12(b)(6)... Iqbal, 556 U.S. 662 (2009); Twombly, 550 U.S. 544 (2007)."},
        {"id":"fl_624_155","meta":{"id":"fl_624_155"},
         "text":"Fla. Stat. § 624.155 creates a civil remedy for insurer bad faith."},
        {"id":"Berges","meta":{"id":"Berges v. Infinity"},
         "text":"Berges v. Infinity Ins. Co., 896 So. 2d 665 (Fla. 2004) discusses bad faith duties."},
        {"id":"Laforet","meta":{"id":"State Farm v. Laforet"},
         "text":"State Farm v. Laforet, 658 So. 2d 55 (Fla. 1995) addresses statutory bad faith and damages."},
    ]

def list_available_agents():
    """Print all available agents"""
    print("\n=== AVAILABLE AGENTS ===")
    for i, agent_name in enumerate(AVAILABLE_AGENTS.keys(), 1):
        print(f"{i:2d}. {agent_name}")
    print(f"\nTotal: {len(AVAILABLE_AGENTS)} agents\n")

def main():
    ap = argparse.ArgumentParser(
        "ADK Orchestrator - Legal Research Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available agents
  python orchestrator.py --list-agents
  
  # Run with automatic agent selection
  python orchestrator.py --issue "Insurance bad faith" --jurisdiction "Florida"
  
  # Run specific agents
  python orchestrator.py --agents case_law,statutes,memo_drafting --issue "Contract dispute"
  
  # Run all agents
  python orchestrator.py --agents all --issue "Complex litigation matter"
"""
    )
    ap.add_argument("--list-agents", action="store_true", help="List all available agents and exit")
    ap.add_argument("--agents", help="Comma-separated agent names to run, or 'all' for all agents")
    ap.add_argument("--issue", default="Insurance bad faith after auto accident")
    ap.add_argument("--jurisdiction", default="Florida state courts")
    ap.add_argument("--terms", default="bad faith, claim denial, delay, settlement authority")
    ap.add_argument("--citext", default="See Harvey v. GEICO; Berges v. Infinity Ins. Co.; Fla. Stat. § 624.155; State Farm v. Laforet.")
    ap.add_argument("--out", default="adk_joined.json", help="Output JSON file")
    args = ap.parse_args()

    # List agents and exit
    if args.list_agents:
        list_available_agents()
        return

    # Parse agent selection
    selected_agents = None
    if args.agents:
        if args.agents.lower() == "all":
            selected_agents = list(AVAILABLE_AGENTS.keys())
            print(f"\n🚀 Running ALL {len(selected_agents)} agents...\n")
        else:
            selected_agents = [a.strip() for a in args.agents.split(",")]
            invalid = [a for a in selected_agents if a not in AVAILABLE_AGENTS]
            if invalid:
                print(f"⚠️  WARNING: Unknown agents will be skipped: {invalid}")
            selected_agents = [a for a in selected_agents if a in AVAILABLE_AGENTS]
            if selected_agents:
                print(f"\n🎯 Running selected agents: {', '.join(selected_agents)}\n")
            else:
                print("❌ No valid agents selected. Use --list-agents to see available agents.")
                return

    # Run orchestrator
    result = asyncio.run(run_orchestrated(
        args.issue, 
        args.jurisdiction, 
        args.terms, 
        args.citext, 
        demo_docs(),
        selected_agents=selected_agents
    ))

    # Save results
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("ORCHESTRATION RESULTS")
    print("="*60)
    print(f"Status: {result.get('status')}")
    print(f"Plan: {result.get('plan', 'N/A')}")
    print(f"Agents run: {', '.join(result.get('agents_run', []))}")
    print(f"Errors: {len(result.get('errors', []))}")
    print(f"Build time: {result.get('build_time_sec')}s")
    print(f"\nResults saved to: {args.out}")
    
    if result.get('note'):
        print("\n" + "="*60)
        print("SYNTHESIZED NOTE")
        print("="*60)
        print(result['note'])
    
    print("\n")

if __name__ == "__main__":
    main()