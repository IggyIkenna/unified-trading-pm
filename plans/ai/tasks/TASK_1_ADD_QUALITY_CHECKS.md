# Task 1: Add Quality Gate Checks

**Goal**: Add empty fallback and Type Any checks to 24 Python repos' quality gates  
**Method**: 2 Task sub-agents MANDATORY (preserve master context)  
**Time**: 30 minutes

**⚠️ CRITICAL: MUST USE SUB-AGENTS** - Master agent orchestrates ONLY, never edits directly!

---

## 🚀 PROMPT (Copy-Paste to Execute)

```
Execute Task 1: Launch 2 Task sub-agents to add quality checks to all Python repos.

⚠️ MANDATORY: Use Task tool with model: fast, subagent_type: generalPurpose

MASTER AGENT ROLE: Orchestrate ONLY (launch agents, review results, resume if needed)
SUB-AGENT ROLE: Edit quality-gates.sh scripts across repos

WHY SUB-AGENTS MANDATORY:
- Preserves master context (cursor rules stay fresh)
- Fast model cost-efficient for script edits
- Master reviews all changes before approval

Launch Task sub-agents:

**Sub-Agent 1** (Services + Utility - 12 repos):
```
description: Add quality checks to services group
model: fast
subagent_type: generalPurpose
prompt: |
  Add 2 quality checks to quality-gates.sh in 12 repos.
  
  Repos (services + utility):
  1. instruments-service
  2. market-tick-data-handler
  3. market-data-processing-service
  4. pnl-attribution-service
  5. features-calendar-service
  6. features-delta-one-service
  7. features-volatility-service
  8. features-onchain-service
  9. ml-training-service
  10. ml-inference-service
  11. strategy-service
  12. execution-service
  
  For EACH repo:
  1. cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/<repo>
  2. Edit scripts/quality-gates.sh
  3. Add 2 checks in STEP 5 (CODEX COMPLIANCE section):
  
  CHECK 1 - Empty Dict/List Fallbacks:
```bash
# Check for empty dict/list fallbacks (BLOCKING)
echo -n "Checking for empty dict/list fallbacks... "
EMPTY_DICT=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\{\}' --type py --glob "!tests/**" --glob "!scripts/**" instruments_service/ 2>/dev/null || true)
EMPTY_LIST=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\[\]' --type py --glob "!tests/**" --glob "!scripts/**" instruments_service/ 2>/dev/null || true)

if [ -n "$EMPTY_DICT" ] || [ -n "$EMPTY_LIST" ]; then
    echo -e "${RED}FAIL${NC}"
    echo -e "${RED}Empty dict/list fallbacks found (must fail loud):${NC}"
    [ -n "$EMPTY_DICT" ] && echo -e "${YELLOW}Empty dicts (.get(key, {})):${NC}" && echo "$EMPTY_DICT" | head -5
    [ -n "$EMPTY_LIST" ] && echo -e "${YELLOW}Empty lists (.get(key, [])):${NC}" && echo "$EMPTY_LIST" | head -5
    echo -e "${RED}See: .cursor/rules/no-empty-fallbacks.mdc${NC}"
    echo -e "${YELLOW}Fix: if val is None: raise ValueError('required')${NC}"
    CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi
```

  CHECK 2 - Type Any Usage:
  ```bash
  # Check for Type Any usage (BLOCKING)
  echo -n "Checking for Type Any (use specific types)... "
  ANY_USAGE=$(rg ': Any[^[]|-> Any[^[]' --type py --glob "!tests/**" --glob "!**/protocols.py" ${SOURCE_DIR}/ 2>/dev/null | grep -v "dict\[str, Any\]" | grep -v "# type: ignore\[reportAny\]" || true)
  
  if [ -n "$ANY_USAGE" ]; then
      echo -e "${RED}FAIL${NC}"
      echo -e "${RED}Type Any found (use specific types):${NC}"
      echo "$ANY_USAGE" | head -10
      echo -e "${RED}See: .cursor/rules/no-type-any-use-specific.mdc${NC}"
      echo -e "${YELLOW}Fix: Check source code, use TypedDict/Pydantic${NC}"
      CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
  else
      echo -e "${GREEN}PASS${NC}"
  fi
  ```
  
  4. Verify per repo: bash scripts/quality-gates.sh --no-fix (should FAIL with violations)
  
  RETURN (REQUIRED - Include token usage):
  | Repo | Checks Added | Violations Found | Branch |
  |------|--------------|------------------|--------|
  | instruments-service | ✅ | X empty, Y Any | main |
  ...
  
  💰 TOKENS USED: Check context and report total
  ⏱️ TIME: X minutes
```

**Sub-Agent 2** (Libraries + remaining - 12 repos):
```
description: Add quality checks to libraries group
model: fast
subagent_type: generalPurpose
prompt: |
  Add 2 quality checks to quality-gates.sh in 12 repos.
  
  Repos (libraries + remaining services):
  1. unified-trading-services
  2. unified-config-interface
  3. unified-events-interface
  4. unified-market-interface
  5. unified-trade-execution-interface
  6. unified-domain-client
  7. execution-algo-library
  8. risk-and-exposure-service
  9. position-balance-monitor-service
  10. unified-trading-deployment-v3
  11. unified-trading-deployment-v3
  12. alerting-service
  
  Same checks as Sub-Agent 1 (see above).
  Adjust ${SOURCE_DIR} per repo (e.g., unified_trading_services/, unified_config_interface/, etc.)
  
  RETURN: Table with results per repo + token usage
```

---

## 🔄 IF SUB-AGENT NEEDS CORRECTIONS

**SAVE AGENT IDs from launch** - critical for resume!

**If Agent 1 or 2 has issues**:
```
Resume Task sub-agent:

description: Fix check syntax in [repo-name]
subagent_type: generalPurpose
resume: [agent-id-from-launch]
model: fast
prompt: |
  Your previous work added checks but syntax error in [repo].
  
  Fix: [Specific correction]
  
  Verify: bash scripts/quality-gates.sh --no-fix (should run without errors)
  
  RETURN:
  Fixed: Yes/No
  Tokens this iteration: XK
```

---

## ✅ Success Criteria - **COMPLETE 2026-02-23**

- [x] 24 repos updated with 2 new checks ✅
- [x] Both sub-agents report complete (table with all repos) ✅
- [x] Checks are BLOCKING (increment CODEX_VIOLATIONS) ✅
- [x] Spot-verify 3 repos: quality gates show violations ✅
- [x] Agent IDs saved (for resume if needed) ✅

## 📊 ACTUAL RESULTS (2026-02-23)

**Sub-Agent 1** (Services - 12 repos):
- Agent ID: `efa5b7cb-1123-4ae1-9c5c-d5c92357c528`
- Status: ✅ COMPLETE
- Repos: All 12 updated successfully
- Tokens: ~53K (~$0.04)
- Time: ~5 minutes
- Issues: None
- Special cases handled:
  - SOURCE_DIR variable used (not hardcoded)
  - Quote escaping: `[\"']` pattern for bash compatibility

**Sub-Agent 2** (Libraries - 12 repos):
- Agent ID: `9741a66c-8c2e-43c9-b946-35e1739523ec`
- Status: ✅ COMPLETE
- Repos: All 12 updated successfully
- Tokens: ~53K (~$0.04)
- Time: ~8 minutes
- Issues: None
- Special cases handled:
  - position-balance-monitor-service: Uses `CODEX_STATUS` counter (not CODEX_VIOLATIONS)
  - unified-domain-client: Added CODEX section (was missing)
  - Quote escaping corrected: `[\"']` for bash syntax

**Master Agent Review**:
- Spot-verified: instruments-service, unified-trading-services, deployment-v2
- Both checks working correctly
- Quality gates run but took 7+ minutes (performance issue noted)

**Total Session Cost**:
- Sub-agents: ~106K tokens (~$0.08)
- Master: ~20K tokens (~$0.15)
- **Task 1 Total: ~$0.23**

---

## 🔍 Verification (Master Agent Reviews)

**After sub-agents complete, master agent spot-checks**:

```bash
# Verify 3 repos (services, libraries, utility)
cd instruments-service && bash scripts/quality-gates.sh --no-fix
# Expected: CODEX COMPLIANCE FAILED with violation counts

cd ../unified-trading-services && bash scripts/quality-gates.sh --no-fix
# Expected: Checks run, violations shown

cd ../unified-trading-deployment-v3 && bash scripts/quality-gates.sh --no-fix
# Expected: Checks run (may pass if no violations)
```

**Master reviews sub-agent results**:
- All 24 repos in sub-agent tables
- Checks correctly added to STEP 5
- ${SOURCE_DIR} variable used (not hardcoded paths)
- CODEX_VIOLATIONS counter incremented

---

## 💰 TOKEN TRACKING (REQUIRED)

**Master Agent (Sonnet 4.5)**:
- Starting tokens: [Check Cursor UI at start]
- Ending tokens: [Check Cursor UI at end]
- Used this task: ~40K tokens (launching 2 agents, reviews)
- Cost this task: ~$0.36

**Sub-Agents (Fast Model)** - Each MUST report:
- Agent 1 (12 services): ~XK tokens, $Y
- Agent 2 (12 libraries): ~XK tokens, $Y
- **Sub-agent total**: ~80K tokens, ~$0.06

**Task 1 Total**: ~120K tokens, ~$0.42

**Session cost so far**: ~$0.42

---

## ➡️ Next Task

After complete: Execute **`TASK_2_FIX_VIOLATIONS.md`**
