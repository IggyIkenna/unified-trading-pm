# Task 4: Fix 3 Large Services (Complete TASK 2)

**Goal**: Fix empty fallbacks + Type Any in 3 large services with 100+ violations each  
**Method**: 3 parallel sub-agents (one per service)  
**Time**: 2-3 hours

**⚠️ CRITICAL: MUST USE 3 SUB-AGENTS** - Master reviews ALL changes!

---

## 🚀 PROMPT (Copy-Paste to Execute)

```
Execute Task 4: Launch 3 Task sub-agents to fix violations in large services.

⚠️ MANDATORY: Use Task tool with model: fast, subagent_type: generalPurpose (3 agents in parallel)

MASTER AGENT ROLE: Orchestrate, review ALL changes, resume if needed
SUB-AGENT ROLE: Fix violations using fail loud patterns

WHY SUB-AGENTS MANDATORY:
- Large violation counts (100+)
- Parallel execution (3 agents)
- Iterative corrections via resume
- Master reviews before approval

CODING STANDARDS (CANONICAL):
- NO .get("key", {}) → fail loud with ValueError
- NO Type Any → use specific types
- Check source code to determine actual type
- Test frequently (every 50 fixes)

Launch 3 Task sub-agents in parallel:
```

**Sub-Agent 1** (ml-training-service):
```
description: Fix ml-training violations (~20)
model: fast
subagent_type: generalPurpose
prompt: |
  Fix empty fallbacks and Type Any in ml-training-service.
  
  VIOLATIONS FOUND:
  - ~20 empty fallbacks (config_schema, models, model_registry, feature_selector, instrument_utils, hyperparam_grid_handler)
  - 5 Any usages
  
  STEPS:
  1. cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/ml-training-service
  2. Create backup: git checkout -b fix-hardening-ml-training-$(date +%s)
  3. Find violations:
     rg '\.get\(["\'][\w_-]+["\']\s*,\s*\{\}' --type py --glob "!tests/**" ml_training_service/
     rg ': Any[^[]|-> Any[^[]' --type py --glob "!tests/**" ml_training_service/
  4. Fix each using fail loud pattern (see TASK_2 doc)
  5. Test after every file: pytest tests/unit/ -x -q
  6. Run quality gates: bash scripts/quality-gates.sh --no-fix
  7. Commit if pass
  
  RETURN:
  | File | {} Fixed | [] Fixed | Any Fixed | Tests | QG | Branch |
  |------|----------|----------|-----------|-------|----|----|
  ...
  
  💰 TOKENS: Input XK + Output YK = Total ZK, Cost $X.XX
  ⏱️ TIME: X minutes
```

**Sub-Agent 2** (strategy-service):
```
description: Fix strategy violations (~56)
model: fast
subagent_type: generalPurpose
prompt: |
  Fix empty fallbacks and Type Any in strategy-service.
  
  VIOLATIONS FOUND:
  - 50+ empty fallbacks (gcs_storage_service, output_builders, order_batch_storage, grid_generator)
  - 6 Any usages
  - 195 print() statements (replace with logger.info)
  
  STEPS:
  1. cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/strategy-service
  2. Create backup: git checkout -b fix-hardening-strategy-$(date +%s)
  3. Find violations (same as Agent 1)
  4. Fix empty fallbacks with fail loud
  5. Fix Type Any with specific types
  6. Replace print() with logger.info() (high priority)
  7. Test frequently
  8. Run quality gates
  9. Commit if pass
  
  RETURN: Same table format
  💰 TOKENS: Input XK + Output YK = Total ZK
  ⏱️ TIME: X minutes
```

**Sub-Agent 3** (execution-service):
```
description: Fix execution violations (~75)
model: fast
subagent_type: generalPurpose
prompt: |
  Fix empty fallbacks and Type Any in execution-service.
  
  VIOLATIONS FOUND:
  - 60+ empty fallbacks (runner, factory, engine, config_builder, catalog, etc.)
  - 15+ Any usages
  
  STEPS:
  1. cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/execution-service
  2. Create backup: git checkout -b fix-hardening-execution-$(date +%s)
  3. Find violations
  4. Fix with fail loud patterns
  5. Fix Type Any with specific types
  6. Test frequently
  7. Run quality gates
  8. Commit if pass
  
  RETURN: Same table format
  💰 TOKENS: Input XK + Output YK = Total ZK
  ⏱️ TIME: X minutes
```

---

## 🔄 RESUME PATTERN

**SAVE ALL AGENT IDs FROM LAUNCH!**

If agent reports partial success or master finds violations:
```
Resume Task sub-agent:
description: Continue fixing [specific files]
subagent_type: generalPurpose
resume: [agent-id]
model: fast
prompt: |
  Your previous work fixed X violations, Y remain.
  
  Issue: [Specific problem]
  Solution: [Pattern/guidance]
  
  RETURN: Progress X → Y, Tokens +ZK
```

---

## ✅ Success Criteria

- [ ] All 3 sub-agents launched
- [ ] ml-training: ~20 violations → 0
- [ ] strategy: ~56 violations → 0 (+ print statements fixed)
- [ ] execution-service: ~75 violations → 0
- [ ] All tests pass
- [ ] All quality gates pass
- [ ] Master reviewed ALL changes
- [ ] Agent IDs saved

---

## 💰 TOKEN TRACKING (REQUIRED)

**Master Agent**: ~80K tokens
**Sub-Agents**: ~400K tokens total
**Total**: ~480K tokens, ~$0.36

---

**Ready to launch!** 🚀
