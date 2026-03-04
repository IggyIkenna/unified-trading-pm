# Resume Pattern - Iterative Sub-Agent Feedback

**Purpose**: Keep sub-agent context across iterations (massive token savings)
**When**: Sub-agent needs corrections, improvements, or gets stuck

**⚠️ CRITICAL: RESUME IS MANDATORY FOR CORRECTIONS** - Never launch new agent when you can resume!

**Token savings**: 50-70% per iteration vs launching new agents

---

## 🎯 THE PROBLEM (Why Resume is MANDATORY)

**❌ WITHOUT RESUME** (Wasteful - launch new agent each time):

```
Agent 1: Fix orchestrator.py
         ↓ (uses 150K tokens, reads all files)
         Reports: 328 → 150 errors (stuck on pattern)

Launch NEW Agent 2: Continue orchestrator.py
         ↓ (uses 150K tokens, RE-READS all files! Wasteful!)
         Reports: 150 → 50 errors

Total: 300K tokens (~$0.23)
Master wasted tokens + money by not using resume!
```

**✅ WITH RESUME** (Efficient - MANDATORY pattern):

```
Agent 1: Fix orchestrator.py
         ↓ (uses 150K tokens, reads all files)
         Reports: 328 → 150 errors (stuck on pattern)

Resume SAME Agent 1: Fix remaining
         ↓ (uses 30K tokens, KEEPS context! No re-reading!)
         Reports: 150 → 0 errors

Total: 180K tokens (~$0.14)
Savings: 120K tokens, $0.09 (40%!)
```

**⚠️ RULE**: If sub-agent reports partial success or master finds issues → MUST resume, NEVER launch new!

---

## 🔧 HOW TO USE RESUME

### Step 1: Save Agent ID from Initial Launch

```
When you launch initial sub-agent, Cursor returns:
"Agent [agent-abc-123] launched..."

SAVE THIS ID: agent-abc-123
```

### Step 2: Resume with Targeted Feedback

```
Use Task tool with resume parameter:

description: Fix remaining issues in orchestrator.py
subagent_type: generalPurpose
resume: agent-abc-123  ← Use saved ID
model: fast
prompt: |
  Your previous work reduced errors from 328 → 150.

  Issue: Still have 150 decorator-related errors.

  Solution: Look at cefi_processor.py lines 135-166 (manual retry pattern).
  Apply this EXACT pattern to all remaining @handle_api_errors decorators.

  Verify: basedpyright orchestrator.py | grep error | wc -l
  Target: 0 errors

  RETURN:
  Errors: 150 → X
  Tokens this iteration: YK (should be small - you kept context!)
  Total tokens (all iterations): ZK
```

---

## 📊 TOKEN MATH

### Typical Iteration Costs:

**Initial Launch** (Fresh context):

- Read files: 80K
- Apply fixes: 50K
- Run tests: 20K
- **Total: 150K tokens**

**Resume Iteration** (Keeps context):

- Read your feedback: 5K
- Apply corrections: 15K
- Re-run tests: 10K
- **Total: 30K tokens** (80% savings!)

**Multiple Iterations**:

- 3 fresh agents: 150K × 3 = 450K tokens
- 1 agent + 2 resumes: 150K + 30K + 30K = 210K tokens
- **Savings: 240K tokens (53%!)**

---

## 🎓 WHEN TO RESUME (Mandatory Decision Tree)

### ✅ MUST RESUME When:

- Sub-agent reports partial success (e.g., 328 → 150 errors remaining)
- Master review finds violations (patterns don't match canonical standards)
- Tests fail (sub-agent needs specific test failure guidance)
- Quality gates fail (sub-agent needs targeted fix instructions)
- Sub-agent got stuck (needs example/pattern clarification)
- Wrong pattern applied (master provides correct pattern with code snippet)

**In ALL these cases: Resume with targeted feedback, NEVER launch new agent!**

### ❌ DON'T RESUME (Launch new agent):

- Sub-agent completely failed (wrong file, wrong approach, crash)
- Need different sub-agent (different repo/task entirely)
- Agent finished successfully (0 errors, tests pass, quality gates pass)
- Too many resume iterations (>4-5 without progress → new approach needed)

**Decision rule**: If agent has ANY context relevant to the fix → RESUME. Only launch new if starting from scratch.

---

## 🔄 MULTI-ITERATION EXAMPLE

### Real Scenario: orchestrator.py (328 errors)

**Iteration 1** (Initial launch):

```
Launch Agent 1: Fix orchestrator.py

Agent returns:
- Status: Partial success
- Errors: 328 → 200 (128 fixed)
- Issue: Confused about UMI adapter typing
- Tokens: 165K
- Agent ID: agent-orch-001
```

**Iteration 2** (Resume with guidance):

```
Resume agent-orch-001:

"Check unified-market-interface source code.
get_adapter() returns base adapter - use cast(TardisAdapter, adapter).
Apply to all get_adapter() calls."

Agent returns:
- Errors: 200 → 80 (120 fixed)
- Issue: Still some dict[str, Any] iterations
- Tokens: +45K = 210K total
```

**Iteration 3** (Resume with pattern):

```
Resume agent-orch-001:

"For dict iterations, use:
for key, value in mydict.items():
    key_str: str = str(key)
    value_dict: dict[str, Any] = cast(dict[str, Any], value)"

Agent returns:
- Errors: 80 → 0 ✅
- Tokens: +35K = 245K total
```

**Total: 245K tokens across 3 iterations**

**vs 3 Separate Agents: 165K × 3 = 495K tokens**

**Savings: 250K tokens (50%!)**

---

## 📋 RESUME TRACKING (MANDATORY)

**Master MUST track ALL iterations** - Required format:

```
Agent 1 (orchestrator.py):
- ID: agent-orch-001 (SAVED for resume)
- Iteration 1 (initial): 165K tokens (328 → 200 errors) - needs resume
- Iteration 2 (resume 1): +45K tokens (200 → 80 errors) - needs resume
- Iteration 3 (resume 2): +35K tokens (80 → 0 errors) ✅ COMPLETE
- Total: 245K tokens
- Cost: ~$0.18 (fast model)
- Savings vs 3 new agents: 495K - 245K = 250K tokens saved (~$0.19 saved!)

Agent 2 (aggregator.py):
- ID: agent-agg-002 (SAVED for resume)
- Iteration 1 (initial): 85K tokens (47 → 0 errors) ✅ COMPLETE (no resume needed)
- Total: 85K tokens
- Cost: ~$0.06

[etc.]
```

**Tracking checklist**:

- [ ] Agent ID saved at launch
- [ ] Initial iteration tokens recorded
- [ ] Each resume iteration tokens recorded (incremental, not cumulative)
- [ ] Total calculated (sum all iterations)
- [ ] Savings calculated (vs launching new agents)
- [ ] Decision documented (why resume vs new)

---

## 🎯 BEST PRACTICES

### 1. Save All Agent IDs

```
# At task start, create tracking file:
echo "Agent 1: agent-abc-123" > agent_ids.txt
echo "Agent 2: agent-def-456" >> agent_ids.txt
```

### 2. Give Specific Feedback

```
# ❌ Vague:
"Fix the remaining errors"

# ✅ Specific:
"Remove @handle_api_errors on lines 123, 456, 789.
Replace with manual retry pattern from cefi_processor.py lines 135-166."
```

### 3. Verify Progress

```
# After each resume, check error count decreased
basedpyright file.py | grep error | wc -l

# Should see: 200 → 150 → 100 → 50 → 0
```

### 4. Know When to Stop

```
# Stop resuming after 3-4 iterations
# If not converging, launch fresh agent with better instructions
```

---

## 💰 COST IMPACT

### Task 3 Example (3 agents, possible iterations):

**Best Case** (no iterations needed):

- 3 agents × 120K avg = 360K tokens
- Cost: ~$0.25

**Typical** (1-2 iterations per agent):

- Agent 1: 165K + 45K + 35K = 245K
- Agent 2: 85K (no resume needed)
- Agent 3: 50K + 20K = 70K
- Total: 400K tokens
- Cost: ~$0.28

**Worst Case** (many iterations):

- Agent 1: 165K + 45K + 35K + 30K + 25K = 300K
- Agent 2: 85K + 30K = 115K
- Agent 3: 50K + 20K + 15K = 85K
- Total: 500K tokens
- Cost: ~$0.35

**Still cheaper than master agent doing it**: ~800K × $15/1M = $12.00!

---

## ✅ SUMMARY

**Resume Pattern**:

- Saves 40-60% tokens per iteration
- Keeps sub-agent context
- Enables iterative improvement
- Master gives targeted feedback

**Key Rule**: ALWAYS save agent IDs from initial launch!

**When to use**: Any time sub-agent needs corrections or guidance

**Token savings**: Massive - agent doesn't re-read files!

---

**Include resume capability in all task prompts** ✅
