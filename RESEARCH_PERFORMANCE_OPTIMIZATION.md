# 🚀 Research Performance Optimization Plan

## Problem Analysis

From the logs, the multi-agent research system is **timing out** because:
1. **30s timeout is too short** for complex legal analysis (2000-2700 char prompts)
2. **Too many LLM calls** - 3 agents × 5 cases × 3 cycles = 45 calls
3. **GPU at 0%** - vLLM is running but not processing (likely hung on a request)
4. **Cascading failures** - timeouts in Cycle 1 continue through Cycle 2 and 3

## Root Causes

### 1. Insufficient Timeouts
- Agent analysis: 30s (too short for 700-800 token responses)
- Query generation: 60s (recently added, but vLLM may still be hung from prior requests)
- Synthesis stages: 60s (adequate but can fail if LLM is backed up)

### 2. Too Much Parallel Work
- Running 3 agents on 5 cases = 15 parallel LLM calls
- Each call needs 30-60s
- vLLM can't handle this load → queue builds up → timeouts

### 3. Large Context Windows
- Opinion text: 4000 chars per case
- Agent prompts: 1500 chars of opinion + 500 chars instructions = 2000-2700 chars
- Total: ~600-700 tokens per request

## Optimization Strategy

### Phase 1: Immediate Fixes (< 5 min)

#### A. Increase All Timeouts to 90s
**Why**: Give vLLM breathing room for complex analysis

**Changes**:
```python
# multi_agent_researcher.py - Agent analysis calls
response = await self._ask_llm(prompt, max_tokens=800, timeout=90)  # was 60
response = await self._ask_llm(prompt, max_tokens=700, timeout=90)  # was 60

# multi_agent_researcher.py - Synthesis stages
organized_topics = await self._organize_findings(..., timeout=90)  # was 30
sections = await self._write_sections_parallel(..., timeout=90)  # implicit 30→90
integrated_memo = await self._integrate_sections(..., timeout=90)  # was 60
final_memo = await self._quality_check_memo(..., timeout=90)  # was 60

# query_generator.py - Query generation
self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=90.0)  # was 60
```

#### B. Reduce Parallel Load
**Why**: vLLM can't handle 15 simultaneous requests

**Changes**:
```python
# multi_agent_researcher.py - Process cases sequentially, not in parallel
# OLD: All agents analyze all cases in parallel (15 simultaneous calls)
# NEW: Analyze cases one-by-one with all 3 agents (3 simultaneous calls max)

async def _analyze_single_case(...):
    # Already implemented! Just need to reduce case count
    # Process 3 cases per cycle instead of 5
    for case in cases[:3]:  # CHANGE from [:5] to [:3]
```

#### C. Reduce Research Cycles
**Why**: 3 cycles × 15 calls = 45 total calls is overkill

**Changes**:
```python
# legal_researcher_agent.py
researcher = MultiAgentLegalResearcher(
    llm, 
    batch_size=10, 
    max_cycles=2  # CHANGE from 3 to 2
)
```

### Phase 2: Medium-term Optimizations (10-15 min)

#### D. Reduce Opinion Text Length
**Why**: 4000 chars is a lot - most relevant info is in first 2000 chars

**Changes**:
```python
# multi_agent_researcher.py - _fetch_single_opinion
if opinion_text:
    trimmed_text = opinion_text[:2000]  # CHANGE from 4000 to 2000
```

#### E. Add Exponential Backoff for Retries
**Why**: If vLLM is slow, retry with increasing delays

**Changes**:
```python
# multi_agent_researcher.py - _ask_llm
async def _ask_llm(self, prompt: str, max_tokens: int = 1000, 
                   temperature: float = 0.5, timeout: int = 90,
                   max_retries: int = 2) -> str:
    """Ask LLM with exponential backoff retries"""
    for attempt in range(max_retries + 1):
        try:
            # ... existing code ...
            return response.strip()
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"LLM request failed (attempt {attempt+1}/{max_retries+1}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"LLM request failed after {max_retries+1} attempts: {e}")
                return ""
```

#### F. Add Request Queue Management
**Why**: Prevent overwhelming vLLM with parallel requests

**Changes**:
```python
# multi_agent_researcher.py - Add semaphore for rate limiting
class MultiAgentLegalResearcher:
    def __init__(self, ...):
        # ... existing code ...
        self.llm_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent LLM calls
    
    async def _ask_llm(self, ...):
        async with self.llm_semaphore:
            # ... existing LLM call code ...
```

### Phase 3: Long-term Improvements (30+ min)

#### G. Implement Response Caching
**Why**: Don't re-analyze same cases multiple times

**Changes**:
```python
# Add LRU cache for agent responses
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def _cache_key(self, case_name: str, agent_role: str, question: str) -> str:
    return hashlib.md5(f"{case_name}:{agent_role}:{question}".encode()).hexdigest()
```

#### H. Pre-filter Cases Before Multi-Agent Analysis
**Why**: Only analyze truly relevant cases

**Changes**:
```python
# Use RAG similarity threshold to filter cases
top_cases = [c for c in cases if similarity_score > 0.15]  # Only highly relevant
```

#### I. Batch LLM Requests
**Why**: Send multiple prompts in one request to vLLM

**Changes**:
```python
# Use vLLM's batch API (if available) to process multiple agents at once
```

## Implementation Priority

### 🔴 CRITICAL (Do Now)
1. **Increase all timeouts to 90s** (Phase 1A)
2. **Reduce cases per cycle: 5→3** (Phase 1B)
3. **Reduce max cycles: 3→2** (Phase 1C)

### 🟡 HIGH (Do Next)
4. **Reduce opinion text: 4000→2000 chars** (Phase 2D)
5. **Add semaphore for max 3 concurrent LLM calls** (Phase 2F)

### 🟢 MEDIUM (Nice to Have)
6. **Add exponential backoff retries** (Phase 2E)
7. **Implement response caching** (Phase 3G)

## Expected Performance Impact

### Before Optimization
- Total LLM calls: 45 (3 agents × 5 cases × 3 cycles)
- Timeout rate: ~40% (6/15 calls timing out per cycle)
- Total research time: 3-5 minutes (with failures)
- Success rate: 60%

### After Phase 1 (Critical Fixes)
- Total LLM calls: 18 (3 agents × 3 cases × 2 cycles)
- Timeout rate: ~10% (1-2 calls timing out)
- Total research time: 2-3 minutes
- Success rate: 90%

### After Phase 2 (High Priority)
- Total LLM calls: 18 (queued via semaphore)
- Timeout rate: <5%
- Total research time: 90-120 seconds
- Success rate: 95%

## Testing Plan

1. **Before optimization**: Run test query, observe timeout count
2. **After Phase 1**: Re-run same query, measure:
   - Number of timeouts (should drop from 6→1-2)
   - Total time (should drop from 5min→2-3min)
   - Success rate (should improve from 60%→90%)
3. **After Phase 2**: Verify:
   - No more than 3 concurrent LLM calls
   - Consistent completion times
   - 95%+ success rate

## Rollback Plan

If optimizations cause issues:
1. Revert timeout changes: `git diff HEAD~1 AMD_server/agents/multi_agent_researcher.py`
2. Restore original values
3. Test with minimal changes (just timeout increase to 60s)

## Monitoring

Watch for these log patterns:
```bash
# Good signs:
INFO:agents.multi_agent_researcher:Cycle 1: Generated 9 findings from 10 cases  # 9/9 success
INFO:agents.multi_agent_researcher:✓ Final memo ready  # Synthesis completed

# Bad signs:
ERROR:llm_client:Chat completion unexpected error: Read timed out  # Still timing out
ERROR:agents.multi_agent_researcher:LLM request failed  # Request failures
```

## Next Steps

1. Implement Phase 1 changes (all timeout increases + reduced workload)
2. Commit and push to GitHub
3. Deploy to AMD server
4. Test with sample query
5. Monitor logs for timeout errors
6. If successful, implement Phase 2 optimizations
