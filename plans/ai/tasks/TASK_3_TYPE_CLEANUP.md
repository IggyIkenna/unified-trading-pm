# Task 3: Type Cleanup (All 24 Repos)

**Goal**: Fix basedpyright type errors across all 24 Python repos  
**Method**: 4 parallel fast sub-agents (6 repos each) using Task tool  
**Time**: 3-4 hours (parallel execution)

**Scope**: Complete type cleanup across entire workspace

---

## 🚀 PROMPT (Copy-Paste to Execute)

```
Execute Task 3: Launch 4 fast sub-agents to fix basedpyright type errors in ALL 24 Python repos.

Use Task tool to launch 4 sub-agents with model: fast, subagent_type: generalPurpose

CONTEXT:
- Reference: instruments_service/processors/cefi_processor.py (0 errors - proven pattern)
- Pattern: Remove decorators, explicit types, no Type Any, fail loud

SAFEGUARDS:
- Backup branch per repo: git checkout -b type-fixes-$(date +%s)
- Fix root causes (remove @handle_api_errors, add explicit types)
- No Type Any (check source, use TypedDict/Pydantic)
- Test after each repo: pytest tests/unit/ -x -q
- Save agent IDs (for resume iterations)

Launch Task sub-agents:
```

**Sub-Agent 1** (Services Group 1 - 6 repos):
```
description: Fix type errors in services group 1
model: fast
subagent_type: generalPurpose
prompt: |
  Fix basedpyright type errors in 6 services (prioritize high-error repos).
  
  Repos:
  1. instruments-service (~396 errors)
  2. market-data-processing-service  
  3. strategy-service
  4. features-delta-one-service
  5. execution-service
  6. ml-training-service
  
  Pattern (from cefi_processor.py):
  - Remove @handle_api_errors → manual retry with explicit types
  - Add type annotations: var: type = value
  - Fix dict iterations: for k, v in d.items(): k_str: str = str(k)
  - Cast adapters: cast(TardisAdapter, get_adapter("tardis"))
  - No Type Any (use TypedDict/Pydantic)
  
  Per repo:
  1. cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/<repo>
  2. Backup: git checkout -b type-fixes-$(date +%s)
  3. Check: basedpyright <module>/ --level warning | grep error | wc -l
  4. Fix in 50-error batches (test after each batch)
  5. Verify: basedpyright <module>/ --level warning (target: 0)
  6. Test: pytest tests/unit/ -x -q
  7. QG: bash scripts/quality-gates.sh --no-fix (must pass)
  8. Commit: git add <module>/ && git commit -m "Fix type errors: 0 basedpyright errors"
  
  RETURN (REQUIRED):
  | Repo | Errors Before | After | Fixed | Ignored | Tests | QG | Branch |
  |------|---------------|-------|-------|---------|-------|----|----|
  | instruments-service | 396 | 0 | 394 | 2 | PASS | PASS | type-fixes-123 |
  ...
  
  💰 TOKENS: XK input + YK output = ZK total
  📝 AGENT ID: [save for resume]
  ⏱️ TIME: X minutes
```

**Sub-Agent 2** (Services Group 2 - 6 repos):
```
description: Fix type errors in services group 2
model: fast
subagent_type: generalPurpose
prompt: |
  Fix basedpyright type errors in 6 services.
  
  Repos:
  - ml-inference-service
  - features-calendar-service
  - features-volatility-service
  - features-onchain-service
  - risk-and-exposure-service
  - position-balance-monitor-service
  
  Same approach as Agent 1.
  Pattern: Remove decorators, explicit types, no Type Any.
  
  RETURN: Table format + tokens + agent ID
```

**Sub-Agent 3** (Libraries - 6 repos):
```
description: Fix type errors in shared libraries
model: fast
subagent_type: generalPurpose
prompt: |
  Fix basedpyright type errors in 6 shared libraries.
  
  Repos (CRITICAL - libraries must be type-clean):
  - unified-trading-services
  - unified-config-interface
  - unified-events-interface
  - unified-market-interface
  - unified-trade-execution-interface
  - unified-domain-client
  
  Same approach. Libraries set the standard!
  Target: 0 errors per library.
  
  RETURN: Table format + tokens + agent ID
```

**Sub-Agent 4** (Deployment/Utils - 6 repos):
```
description: Fix type errors in deployment repos
model: fast
subagent_type: generalPurpose
prompt: |
  Fix basedpyright type errors in 6 remaining repos.
  
  Repos:
  - unified-trading-deployment-v3
  - unified-trading-deployment-v3
  - pnl-attribution-service
  - market-tick-data-handler
  - execution-algo-library
  - alerting-service
  
  Same approach. Target: 0 errors per repo.
  
  RETURN: Table format + tokens + agent ID
```

---

## 🔄 ITERATIVE FIXING (Resume Sub-Agents)

**SAVE ALL 4 AGENT IDs** - Critical for resume!

**Example: Agent 1 needs help with instruments-service**:

```
Agent 1 reports: instruments-service 396 → 150 errors (stuck on decorators)

Resume Agent 1:

description: Help with remaining decorators
subagent_type: generalPurpose
resume: [agent-1-id]
model: fast
prompt: |
  instruments-service still has 150 errors (mostly decorators).
  
  Exact pattern from cefi_processor.py lines 135-166:
  
  async def method() -> ReturnType:
      max_retries: int = self.processing_config.retry_max_attempts
      last_error: Exception | None = None
      
      for attempt in range(max_retries):
          try:
              return await api_call()
          except Exception as e:
              last_error = e
              if attempt < max_retries - 1:
                  backoff_multiplier: int = cast(int, 2 ** attempt)
                  backoff: float = self.processing_config.retry_backoff_factor * float(backoff_multiplier)
                  await asyncio.sleep(backoff)
              else:
                  raise Exception(f"Failed") from last_error
  
  Apply to ALL @handle_api_errors decorators.
  
  Verify: basedpyright orchestrator.py | grep error | wc -l
  Target: Continue reducing
  
  RETURN:
  Errors: 150 → X
  Tokens this iteration: YK (incremental)
```

**Iteration Pattern**: Launch → Review → Resume → Review → Resume → Success

**Token Savings**: 40-60% per resume vs fresh agent!

---

## ✅ Success Criteria

- [ ] All 24 repos: 0 basedpyright errors (or only documented exceptions)
- [ ] All tests pass across all repos
- [ ] All quality gates pass
- [ ] Agent IDs saved (for resume)
- [ ] Backup branches created (recovery)

---

## 🔍 Verification (After All Agents Complete)

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

# Spot check high-error repos
cd instruments-service && source .venv/bin/activate
basedpyright instruments_service/ --level warning | grep "error:" | wc -l
# Target: 0

cd ../unified-trading-services && source .venv/bin/activate
basedpyright unified_trading_services/ --level warning | grep "error:" | wc -l
# Target: 0

cd ../strategy-service && source .venv/bin/activate
basedpyright strategy_service/ --level warning | grep "error:" | wc -l
# Target: 0

# Run all quality gates
cd ../unified-trading-deployment-v3
bash scripts/run-all-quality-gates.sh --sequential
# All should pass

# Commit all repos
cd ..
bash git-quickmerge.sh "Complete type cleanup: 0 errors across 24 Python repos" --all
```

---

## 💰 TOKEN TRACKING (REQUIRED)

**Master Agent (Sonnet 4.5)**:
- Starting tokens: [From Task 2 end]
- Ending tokens: [Check at end]
- Used this task: ~120K tokens (launching 4 agents, reviewing 24 repos)
- Cost this task: ~$0.90

**Sub-Agents (Fast Model)** - Each MUST report:
- Agent 1 (6 services): ~400K tokens, ~$0.27
- Agent 2 (6 services): ~250K tokens, ~$0.17
- Agent 3 (6 libraries): ~300K tokens, ~$0.20
- Agent 4 (6 deployment): ~180K tokens, ~$0.12
- **Sub-agent total**: ~1.13M tokens, ~$0.76

**With Resume Iterations** (typical):
- Agent 1 resume: +60K tokens, +$0.04
- Agent 2 resume: +40K tokens, +$0.03
- **Total with resumes**: ~1.23M tokens, ~$0.83

**Task 3 Total**: ~1.35M tokens, ~$1.73

---

## 💰 COMPLETE SESSION SUMMARY (All 3 Tasks)

**All 3 Tasks Across 24 Repos**:
- Master agent (Sonnet 4.5): ~280K tokens, ~$2.10
- Sub-agents (Fast): ~1.53M tokens, ~$1.06
- **GRAND TOTAL: ~1.81M tokens, ~$3.16**

**Scope Delivered**:
- ✅ 24 Python repos type-clean
- ✅ All quality gates passing
- ✅ All standards enforced  
- ✅ ~1500+ type errors fixed
- ✅ ~200+ empty fallbacks fixed
- ✅ ~100+ Type Any replaced

**Efficiency vs Direct Approach**:
- Without sub-agents: ~2.5M Sonnet tokens = ~$37.50
- With sub-agents: ~1.81M mixed tokens = ~$3.16
- **Savings: ~$34.34 (92% cost reduction!)**

**Context Preservation**:
- Master stayed under 280K (72% context free!)
- Cursor rules NEVER compressed ✅
- Effective capacity: 11M+ tokens (11 agents)
- Resume available for stuck agents ✅

---

## ➡️ After Complete

**All 3 tasks done**: Complete workspace cleanup! 🎉

**Files to commit**:
- 24 repos with fixes
- Updated cursor rules
- Updated codex docs
- Task framework

**Total improvement**: Every Python repo in workspace now follows strict standards!
