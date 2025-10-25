import os, time, statistics, argparse
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

# OpenAI >=1.0 client
from openai import OpenAI

load_dotenv()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL  = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # will fallback if unavailable
SAUL_MODEL    = os.getenv("SAUL_MODEL", "Equall/Saul-7B-Instruct-v1")

DEFAULT_PROMPTS = [
    "Write a one-sentence summary of what gradient descent does.",
]

from dataclasses import dataclass
from typing import List

@dataclass
class RunResult:
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

def usage_numbers(usage) -> tuple[int, int, int]:
    """Handle pydantic object or dict or None."""
    if usage is None:
        return (0, 0, 0)
    # Pydantic object (OpenAI SDK types)
    pt = getattr(usage, "prompt_tokens", None)
    ct = getattr(usage, "completion_tokens", None)
    tt = getattr(usage, "total_tokens", None)
    if pt is not None and ct is not None and tt is not None:
        return (int(pt), int(ct), int(tt))
    # Dict-like (some servers / older clients)
    if isinstance(usage, dict):
        return (
            int(usage.get("prompt_tokens", 0)),
            int(usage.get("completion_tokens", 0)),
            int(usage.get("total_tokens", 0)),
        )
    # Fallback
    return (0, 0, 0)

def try_openai_chat(client, model: str, prompts: List[str], max_tokens: int) -> List[RunResult]:
    results: List[RunResult] = []
    for p in prompts:
        t0 = time.perf_counter()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": p}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        t1 = time.perf_counter()
        pt, ct, tt = usage_numbers(getattr(r, "usage", None))
        results.append(RunResult(
            latency_s=t1 - t0,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=tt,
        ))
    return results

def summarize(name: str, results: List[RunResult]) -> Dict[str, Any]:
    lat = [r.latency_s for r in results]
    pt  = sum(r.prompt_tokens for r in results)
    ct  = sum(r.completion_tokens for r in results)
    tt  = sum(r.total_tokens for r in results)
    def pct(a, q): 
        if not a: return 0.0
        a2 = sorted(a)
        i = max(0, min(len(a2)-1, int(round((q/100.0)*(len(a2)-1)))))
        return a2[i]
    return {
        "engine": name,
        "runs": len(lat),
        "lat_mean_ms": 1000*statistics.mean(lat),
        "lat_median_ms": 1000*statistics.median(lat),
        "lat_p90_ms": 1000*pct(lat, 90),
        "lat_p95_ms": 1000*pct(lat, 95),
        "lat_min_ms": 1000*min(lat) if lat else 0.0,
        "lat_max_ms": 1000*max(lat) if lat else 0.0,
        "tokens_prompt": pt,
        "tokens_completion": ct,
        "tokens_total": tt,
        "tokens_per_sec": (tt / sum(lat)) if sum(lat) > 0 else 0.0,
    }

import numpy as np

def token_speed_stats(name: str, results: list[RunResult]):
    if not results:
        print(f"{name}: no results")
        return
    speeds = []
    for r in results:
        if r.latency_s > 0:
            speeds.append(r.total_tokens / r.latency_s)
    arr = np.array(speeds)
    mean = arr.mean()
    median = np.median(arr)
    p95 = np.percentile(arr, 95)
    print(f"\n=== Token Throughput: {name} ===")
    print(f"  Mean   : {mean:8.2f} tokens/sec")
    print(f"  Median : {median:8.2f} tokens/sec")
    print(f"  P95    : {p95:8.2f} tokens/sec")


def main():
    ap = argparse.ArgumentParser(description="Benchmark Saul-7B(vLLM) vs OpenAI")
    ap.add_argument("--runs", type=int, default=10, help="repetitions per engine")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--prompt", type=str, default=None, help="single ad-hoc prompt")
    ap.add_argument("--warmup", type=int, default=2, help="warmup calls per engine (excluded from stats)")
    args = ap.parse_args()

    prompts = [args.prompt] if args.prompt else DEFAULT_PROMPTS
    prompts = prompts * args.runs  # repeat

    # ---------- vLLM / Saul ----------
    vllm_client = OpenAI(base_url=f"{VLLM_BASE_URL}", api_key="EMPTY")  # vLLM doesn't require a real key by default
    # Warmups
    if args.warmup > 0:
        _ = try_openai_chat(vllm_client, SAUL_MODEL, prompts[:args.warmup], args.max_new_tokens)
    saul_res = try_openai_chat(vllm_client, SAUL_MODEL, prompts[args.warmup:], args.max_new_tokens)
    saul_summary = summarize("Saul-7B (vLLM ROCm)", saul_res)

    # ---------- OpenAI  ----------
    # Try requested model; if it fails, fallback to gpt-4o-mini
    openai_client = OpenAI(api_key=OPENAI_KEY)
    openai_model_used = OPENAI_MODEL
    try:
        # Warmups
        if args.warmup > 0:
            _ = try_openai_chat(openai_client, OPENAI_MODEL, prompts[:args.warmup], args.max_new_tokens)
        oai_res = try_openai_chat(openai_client, OPENAI_MODEL, prompts[args.warmup:], args.max_new_tokens)
    except Exception as e:
        print(f"[warn] OpenAI model '{OPENAI_MODEL}' failed ({e}). Falling back to 'gpt-4o-mini'.")
        openai_model_used = "gpt-4o-mini"
        # warmup + runs with fallback
        if args.warmup > 0:
            _ = try_openai_chat(openai_client, openai_model_used, prompts[:args.warmup], args.max_new_tokens)
        oai_res = try_openai_chat(openai_client, openai_model_used, prompts[args.warmup:], args.max_new_tokens)

    oai_summary = summarize(f"OpenAI ({openai_model_used})", oai_res)

    # ---------- Print ----------
    def pretty(d: Dict[str, Any]):
        keys = [
            "engine","runs","lat_mean_ms","lat_median_ms","lat_p90_ms","lat_p95_ms",
            "lat_min_ms","lat_max_ms","tokens_prompt","tokens_completion","tokens_total",
            "tokens_per_sec",
        ]
        for k in keys:
            v = d[k]
            if isinstance(v, float): 
                if "tokens" in k:
                    print(f"{k:>18}: {v:.0f}")
                else:
                    print(f"{k:>18}: {v:.2f}")
            else:
                print(f"{k:>18}: {v}")
        print("-"*60)

    print("\n=== Benchmark Results ===")
    pretty(saul_summary)
    pretty(oai_summary)

    token_speed_stats("Saul-7B (vLLM ROCm)", saul_res)
    token_speed_stats(f"OpenAI ({openai_model_used})", oai_res)

if __name__ == "__main__":
    main()
