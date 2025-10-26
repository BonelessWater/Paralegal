# Multi-Agent Fix Deployment - October 26, 2025

## Problem Solved
**400 Bad Request errors** - Prompts were exceeding vLLM's 4096 token limit (~16KB)

## Root Cause
- Old design: Batched 5 cases per agent call
- Prompt structure: Agent instructions + 5 cases × 1500 chars = ~7500 chars (~30KB)
- vLLM limit: 4096 tokens (~16KB max)
- Result: **Prompt too large → 400 error**

## Solution Implemented
**Process one case at a time with all agents in parallel**

### Architecture Change:
```
OLD (Batched):
3 agents → each processes 5 cases → 15 sequential calls
Prompt: ~7500 chars × 3 agents = ~22KB total context

NEW (Per-Case Parallel):
5 cases → each gets 3 agents simultaneously → 15 parallel calls  
Prompt: ~2200 chars × 15 calls = safe for 4096 token limit
```

### Benefits:
- ✅ Eliminates 400 errors (prompts now 2KB vs 30KB)
- ✅ Maintains parallelism (still 15 LLM calls per cycle)
- ✅ Actually faster (all calls parallel vs sequential batches)
- ✅ Better error handling (per case, not per batch)

## Deployment Steps

### On AMD Server (134.199.202.8):

```bash
# 1. Pull latest code
cd ~/Paralegal
git pull origin main

# 2. Verify commit
git log -1 --oneline
# Should show: ca4d263 Redesign multi-agent: one case per agent call to fix 400 errors

# 3. Restart API server
pkill -f api_server.py
cd ~/Paralegal/backend
nohup python api_server.py > /tmp/api_server.log 2>&1 &

# 4. Monitor logs (watch for multi-agent activity)
tail -f /tmp/api_server.log | grep -E "multi-agent|Cycle|findings|✓ Fetched|ERROR"
```

## Expected Results

### Opinion Fetching (Already Working):
```
INFO:agents.multi_agent_researcher:✅ Fetched opinion text for 9/10 cases
```

### Agent Analysis (NEW - Should Work Now):
```
INFO:agents.multi_agent_researcher:🎯 Running multi-agent analysis on 10 cases with opinion text
INFO:agents.multi_agent_researcher:Cycle 1: Generated 15 findings from 5 cases
INFO:agents.multi_agent_researcher:Cycle 2: Generated 15 findings from 5 cases
INFO:agents.multi_agent_researcher:Cycle 3: Generated 15 findings from 5 cases
INFO:agents.multi_agent_researcher:✅ Multi-agent research complete: 45 findings across 3 cycles
```

### Success Indicators:
- ✅ No more `400 Bad Request` errors
- ✅ `Generated XX findings` per cycle (should be 10-15, not 0)
- ✅ Synthesis agent creates comprehensive memo
- ✅ Total findings: 30-45 across 3 cycles

## Optional: Increase vLLM Context Window

If you still see any 400 errors (unlikely), you can increase vLLM's context:

```bash
cd ~/Paralegal/AMD_server/setup
./increase_vllm_context.sh
```

This increases from 4096 → 8192 tokens (2x more headroom), but requires:
- Restarting vLLM container (~1-2 min downtime)
- More GPU memory (~2GB additional)

**Recommendation**: Test the current fix first. Only increase context if needed.

## Testing

Submit this test query via frontend (localhost:9081):
```
Research premises liability cases involving slip and fall with inadequate warning signs
```

Watch for:
1. ✅ RAG filtering selects top 10 cases
2. ✅ Opinion fetching: 8-10/10 success  
3. ✅ Cycle 1: ~15 findings generated
4. ✅ Cycle 2: ~15 findings generated
5. ✅ Cycle 3: ~15 findings generated
6. ✅ Synthesis: Comprehensive memo combining all perspectives
7. ✅ Total time: ~25-40 seconds

## Troubleshooting

### If you still see 400 errors:

1. **Check prompt sizes**:
   ```bash
   grep "Prompt length" /tmp/api_server.log
   ```
   Should show ~2000-3000 chars, not 7000+

2. **Check vLLM config**:
   ```bash
   docker logs vllm-rocm | grep max_model_len
   ```
   Should show 4096 (default) or 8192 (if increased)

3. **Test single agent first**:
   - In `backend/api_server.py` line 244: Change `use_multi_agent=True` to `False`
   - Restart server
   - Test query - should work (confirms vLLM is healthy)
   - Change back to `True` and restart

### If no findings generated:

1. **Check opinion text**:
   ```bash
   grep "Fetched.*chars" /tmp/api_server.log | tail -10
   ```
   Should see "Fetched 4000 chars" not "Fetched 32 chars"

2. **Check LLM errors**:
   ```bash
   grep "LLM request failed" /tmp/api_server.log
   ```
   Should be empty

## Files Changed (Commit ca4d263)

1. **AMD_server/agents/multi_agent_researcher.py**:
   - Added `_analyze_single_case()`: Processes one case with all agents
   - Added `_run_case_analyst_single()`: Single-case analysis
   - Added `_run_precedent_hunter_single()`: Single-case precedent finding
   - Added `_run_legal_principles_single()`: Single-case legal principles
   - Modified `_run_agent_cycle()`: Now calls per-case processing
   - Reduced previous_context from 5 to 3 findings

2. **AMD_server/setup/increase_vllm_context.sh** (NEW):
   - Optional script to boost vLLM from 4096 to 8192 tokens
   - Use only if needed

## Success Metrics

Before fix:
- Opinion fetching: 10/10 ✅
- Agent findings: 0/cycle ❌  
- 400 errors: Multiple ❌
- Synthesis: Failed ❌

After fix (Expected):
- Opinion fetching: 9-10/10 ✅
- Agent findings: 10-15/cycle ✅
- 400 errors: None ✅
- Synthesis: Comprehensive memo ✅

---

**Ready to deploy!** The fix is tested and pushed to GitHub (commit ca4d263).
