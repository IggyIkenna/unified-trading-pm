---
name: System Hardening Workflow
overview: "Complete system hardening: instruments-service → 7 libraries → 14 services → 9 UIs. Re-enable ALL quality gates (no skips except documented third-party exceptions). Establish instruments-service as canonical standard, then replicate systematically."
todos:
  - id: phase1-task1a
    content: Add quality checks (empty fallbacks + Type Any) to 24 Python repos' quality-gates.sh scripts
    status: pending
  - id: phase1-task1b
    content: Fix violations in instruments-service using 4 sub-agents (establish canonical patterns)
    status: pending
  - id: phase1-task1c
    content: Document canonical patterns in instruments-service/docs/CANONICAL_PATTERNS.md
    status: pending
  - id: phase2-libraries
    content: Harden 7 platform libraries sequentially (UCS → UCI → UEI → UMI → UOI → UDS → execution-algo-library)
    status: pending
  - id: phase3a-services
    content: Harden 14 services using 4 parallel sub-agents (grouped by domain)
    status: pending
  - id: phase3b-uis
    content: Harden 9 TypeScript UIs using 3 parallel sub-agents (TypeScript quality gates)
    status: pending
  - id: documentation
    content: Create HARDENING_COMPLETE.md, CANONICAL_STANDARDS.md, TOKEN_USAGE_LOG.md
    status: pending
  - id: final-verification
    content: Verify all 33 repos pass quality gates with 0 violations (except documented third-party exceptions)
    status: pending
isProject: false
---

# System Hardening Workflow - Ground-Up Quality Gates

## Executive Summary

Systematic hardening of the entire unified trading system with **strict cursor rules adherence** via sub-agent supervision. Execute in 3 phases:

1. **Phase 1**: instruments-service (canonical standard) - 3 tasks
2. **Phase 2**: 7 platform libraries (UCS, UCI, UEI, UMI, UOI, UDS, execution-algo-library)
3. **Phase 3**: 14 services + 9 UIs (rollout)

**Quality Gates Philosophy**: Re-enable ALL checks. Only exceptions: third-party library type errors (CCXT, yfinance, pandas) documented in `QUALITY_GATE_BYPASS_AUDIT.md` sections 2.1-2.3.

---

## Phase 1: Instruments-Service Canonical Standard

**Goal**: Complete hardening of instruments-service to serve as template for all other repos.

**Location**: [instruments-service](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service)

**Existing Assets**:

- `.cursor/plans/tasks/TASK_1_ADD_QUALITY_CHECKS.md` - Add quality checks
- `.cursor/plans/tasks/TASK_2_FIX_VIOLATIONS.md` - Fix empty fallbacks + Type Any
- `.cursor/plans/tasks/TASK_3_TYPE_CLEANUP.md` - Fix 396 basedpyright errors
- `.cursor/plans/tasks/TEMPLATE.md` - Task structure template
- `.cursor/plans/tasks/RESUME_PATTERN.md` - Sub-agent iteration guide
- [instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md) - Exception inventory

### Task 1A: Add Quality Checks to ALL Python Repos

**Before starting TASK_2 (fixes), add checks to make violations visible across all repos.**

**Scope**: 24 Python repos (14 services + 6 libraries + 4 utility repos)

**Repos**:

- **Services (14)**: instruments-service, market-tick-data-handler, market-data-processing-service, pnl-attribution-service, features-calendar-service, features-delta-one-service, features-volatility-service, features-onchain-service, ml-training-service, ml-inference-service, strategy-service, execution-services, risk-and-exposure-service, position-balance-monitor-service
- **Libraries (6)**: unified-cloud-services, unified-config-interface, unified-events-interface, unified-market-interface, unified-trade-execution-interface, unified-domain-services
- **Utility (4)**: unified-trading-deployment-v3, unified-trading-deployment-v3, execution-algo-library, alerting-system

**Actions**:

1. **Add 2 checks to each repo's `scripts/quality-gates.sh`** (STEP 5: CODEX COMPLIANCE section):

```bash
# Check 1: Empty Dict/List Fallbacks (BLOCKING)
echo -n "Checking for empty dict/list fallbacks... "
EMPTY_DICT=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\{\}' --type py --glob "!tests/**" --glob "!scripts/**" ${SOURCE_DIR}/ 2>/dev/null || true)
EMPTY_LIST=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\[\]' --type py --glob "!tests/**" --glob "!scripts/**" ${SOURCE_DIR}/ 2>/dev/null || true)

if [ -n "$EMPTY_DICT" ] || [ -n "$EMPTY_LIST" ]; then
    echo -e "${RED}FAIL${NC}"
    echo -e "${RED}Empty dict/list fallbacks found:${NC}"
    [ -n "$EMPTY_DICT" ] && echo "$EMPTY_DICT" | head -5
    [ -n "$EMPTY_LIST" ] && echo "$EMPTY_LIST" | head -5
    echo -e "${RED}See: .cursor/rules/no-empty-fallbacks.mdc${NC}"
    CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# Check 2: Type Any Usage (BLOCKING)
echo -n "Checking for Type Any... "
ANY_USAGE=$(rg ': Any[^[]|-> Any[^[]' --type py --glob "!tests/**" --glob "!**/protocols.py" ${SOURCE_DIR}/ 2>/dev/null | grep -v "dict\[str, Any\]" | grep -v "# type: ignore\[reportAny\]" || true)

if [ -n "$ANY_USAGE" ]; then
    echo -e "${RED}FAIL${NC}"
    echo -e "${RED}Type Any found:${NC}"
    echo "$ANY_USAGE" | head -10
    echo -e "${RED}See: .cursor/rules/no-type-any-use-specific.mdc${NC}"
    CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi
```

1. **Run quality gates to confirm violations detected**:

```bash
cd ${REPO}
bash scripts/quality-gates.sh --no-fix
# Expected: CODEX COMPLIANCE FAILED with violation counts
```

**Execution**: Direct (no sub-agents) - systematic script updates across 24 repos

**Verification**:

- All 24 repos have new checks in STEP 5
- Running quality gates shows violations (proves checks work)
- Checks are BLOCKING (increment CODEX_VIOLATIONS counter)

**Token Estimate**: ~80K tokens (script updates + verification)

---

### Task 1B: Fix Violations in instruments-service Only

**Scope**: instruments-service only (establish canonical patterns)

**Issues**:

- Empty dict/list fallbacks: ~15 instances
- Type Any: ~47 instances
- basedpyright errors: 396 total (328 orchestrator.py, 47 aggregator.py, 21 handlers)

**Sub-Agents**: 4 total

- Agent 1: Fix empty fallbacks + Type Any across all modules
- Agent 2: Fix orchestrator.py type errors (328 → 0)
- Agent 3: Fix aggregator.py type errors (47 → 0)
- Agent 4: Fix handlers type errors (21 → 0)

**Key Patterns** (document in instruments-service as canonical):

**Pattern 1: Empty Fallback → Fail Loud**

```python
# ❌ BEFORE (defensive programming)
config = self._config.get("service", {})
if not isinstance(config, dict):
    config = {}

# ✅ AFTER (fail loud)
config = self._config.get("service")
if config is None:
    raise ValueError("service config required in pyproject.toml")
if not isinstance(config, dict):
    raise TypeError(f"service must be dict, got {type(config).__name__}")
```

**Pattern 2: Type Any → Specific Types**

```python
# ❌ BEFORE
from typing import Any
def process(data: Any) -> dict[str, Any]:
    return data.get("result")

# ✅ AFTER (TypedDict)
from typing import TypedDict
class DataDict(TypedDict):
    result: dict[str, str]
    count: int

def process(data: DataDict) -> dict[str, str]:
    return data["result"]
```

**Pattern 3: Decorator Removal → Manual Retry**

```python
# ❌ BEFORE (@handle_api_errors breaks type inference)
@handle_api_errors(max_retries=3)
async def fetch_data() -> dict[str, str]:
    return await api_call()

# ✅ AFTER (explicit retry logic - from cefi_processor.py lines 135-166)
async def fetch_data() -> dict[str, str]:
    max_retries: int = self.processing_config.retry_max_attempts
    for attempt in range(max_retries):
        try:
            return await api_call()
        except Exception as e:
            if attempt < max_retries - 1:
                backoff: float = self.processing_config.retry_backoff_factor * float(2 ** attempt)
                await asyncio.sleep(backoff)
            else:
                raise RuntimeError("Failed after retries") from e
```

**Reference Implementation**: [instruments_service/engine/operations/instruments/processors/cefi_processor.py](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service/instruments_service/engine/operations/instruments/processors/cefi_processor.py) (0 basedpyright errors)

**Strict Review Protocol**:

For EACH sub-agent result:

1. **Read diff**: Check every changed line
2. **Verify pattern**: Matches canonical patterns (fail loud, specific types, manual retry)
3. **Check exceptions**: Only third-party bypasses (CCXT, yfinance, pandas) allowed in QUALITY_GATE_BYPASS_AUDIT.md
4. **Run tests**: `pytest tests/unit/ -x -q` must pass
5. **Run quality gates**: `bash scripts/quality-gates.sh --no-fix` must pass (exit 0)
6. **Approve or Resume**: If issues found, use Resume pattern to guide sub-agent

**Resume Pattern** (when sub-agent needs corrections):

```
Resume Task sub-agent:
description: Fix remaining issues in [file]
subagent_type: generalPurpose
resume: [agent-id-from-initial-launch]
model: fast
prompt: |
  Your previous work reduced errors from X → Y.

  Issue: [Specific problem found in review]

  Solution: [Explicit guidance with code example]

  Verify: [Command to check]
  Target: 0 errors

  RETURN:
  Errors: Y → Z
  Tokens this iteration: XK (incremental)
```

**Token Estimate**: ~600K tokens total

- Master agent: ~120K (launching 4 agents, reviews)
- Sub-agents: ~480K (with resume iterations)

**Success Criteria**:

- All empty fallbacks replaced with fail-loud validation
- All Type Any replaced with specific types (or documented third-party exceptions)
- basedpyright: 0 errors (or only documented exceptions)
- pytest: All tests pass
- Quality gates: Exit code 0
- QUALITY_GATE_BYPASS_AUDIT.md: Updated with any new third-party exceptions

---

### Task 1C: Document Canonical Patterns

**Create**: `instruments-service/docs/CANONICAL_PATTERNS.md`

**Contents**:

1. **Empty Fallback Elimination**: Before/after examples, rationale
2. **Type Any Replacement**: Pattern library (TypedDict, Protocol, TypeVar, Union)
3. **Decorator Removal**: Manual retry pattern with explicit types
4. **Third-Party Exceptions**: When `# type: ignore[reportAny]` is acceptable
5. **Quality Gate Integration**: How checks enforce patterns

**This document becomes the template for all repos going forward.**

**Token Estimate**: ~30K tokens

---

## Phase 2: Platform Libraries (7 Repos)

**Goal**: Harden all shared libraries using instruments-service canonical patterns.

**Repos** (dependency order - fix dependencies before consumers):

1. unified-cloud-services (UCS) - no dependencies
2. unified-config-interface (UCI) - depends on UCS
3. unified-events-interface (UEI) - depends on UCS, UCI
4. unified-market-interface (UMI) - depends on UCS
5. unified-trade-execution-interface (UOI) - depends on UCS, UMI
6. unified-domain-services (UDS) - depends on UCS, UCI, UEI, UMI
7. execution-algo-library - depends on UCS, UOI

**Approach**: Sequential (respect dependency order)

**Per-Library Process**:

1. **Audit current state**:
  - Run quality gates (violations already visible from Task 1A)
  - Check existing QUALITY_GATE_BYPASS_AUDIT.md
  - Count violations: empty fallbacks, Type Any, basedpyright errors
2. **Launch sub-agent** (1 per library):

```
description: Harden [library-name] using canonical patterns
model: fast
subagent_type: generalPurpose
prompt: |
  Harden [library-name] following instruments-service canonical patterns.

  Read: instruments-service/docs/CANONICAL_PATTERNS.md
  Read: .cursor/rules/no-empty-fallbacks.mdc
  Read: .cursor/rules/no-type-any-use-specific.mdc

  Current violations:
  - Empty fallbacks: X
  - Type Any: Y
  - basedpyright errors: Z

  Fix ALL violations using canonical patterns:
  1. Empty fallbacks → Fail loud validation
  2. Type Any → TypedDict/Protocol/Union
  3. Remove decorators if breaking type inference

  Only exception: Third-party library types (document in QUALITY_GATE_BYPASS_AUDIT.md)

  Test: pytest tests/unit/ -x -q
  Verify: bash scripts/quality-gates.sh --no-fix (must exit 0)

  RETURN:
  Empty fallbacks: X → 0
  Type Any: Y → Z (document exceptions)
  basedpyright: Z → 0 (or only documented exceptions)
  Tests: PASS/FAIL
  Quality gates: PASS/FAIL
  Tokens: XK
```

1. **Review sub-agent result** (same strict protocol as Task 1B):
  - Read all changes
  - Verify canonical patterns used
  - Check QUALITY_GATE_BYPASS_AUDIT.md for valid exceptions only
  - Run tests + quality gates
  - Resume if needed
2. **Merge when clean**:

```bash
cd [library-name]
bash scripts/quickmerge.sh "Harden [library]: 0 violations (canonical patterns)"
```

**Cross-Repo Dependencies**: When library changes affect consumers:

- Fix library first, merge to main
- Consumer repos see updated library on next pull
- If consumer breaks, fix consumer immediately

**Token Estimate**: ~800K tokens

- Master agent: ~100K (launching 7 agents, reviews)
- Sub-agents: ~700K (7 × 100K avg with resume iterations)

**Success Criteria Per Library**:

- Empty fallbacks: 0 (all fail-loud)
- Type Any: 0 or documented third-party exceptions
- basedpyright: 0 errors or documented exceptions
- Tests: All pass
- Quality gates: Exit 0
- QUALITY_GATE_BYPASS_AUDIT.md: Complete and accurate

---

## Phase 3: Services + UIs Rollout

**Goal**: Harden remaining 14 services + 9 UIs using canonical patterns.

### Phase 3A: Services (14 Repos)

**Repos** (by domain):

- **Data (3)**: market-tick-data-handler, market-data-processing-service, pnl-attribution-service
- **Features (4)**: features-calendar-service, features-delta-one-service, features-volatility-service, features-onchain-service
- **ML (2)**: ml-training-service, ml-inference-service
- **Trading (3)**: strategy-service, execution-services, risk-and-exposure-service
- **Monitoring (1)**: position-balance-monitor-service
- **Alert (1)**: alerting-system

**Parallelization Strategy**: Group by domain, launch 4 sub-agents

**Sub-Agent 1** (Data pipeline - 3 repos):

```
Harden: market-tick-data-handler, market-data-processing-service, pnl-attribution-service
Patterns: Same as libraries
Context: instruments-service/docs/CANONICAL_PATTERNS.md
```

**Sub-Agent 2** (Features - 4 repos):

```
Harden: features-calendar, features-delta-one, features-volatility, features-onchain
Patterns: Same as libraries
```

**Sub-Agent 3** (ML + Trading - 5 repos):

```
Harden: ml-training, ml-inference, strategy, execution, risk-and-exposure
Patterns: Same as libraries
```

**Sub-Agent 4** (Monitoring + Alert - 2 repos):

```
Harden: position-balance-monitor, alerting-system
Patterns: Same as libraries
```

**Review Protocol**: Same as Phase 2 (strict review, approve/resume)

**Token Estimate**: ~1.2M tokens

- Master agent: ~200K (launching 4 agents, reviewing 14 repos)
- Sub-agents: ~1M (4 agents × 250K avg)

---

### Phase 3B: UIs (9 Repos)

**Different Approach**: UIs use TypeScript, not Python.

**Repos**: backtest-ui, batch-audit-ui, client-reporting-ui, live-health-monitor-ui, logs-dashboard-ui, ml-deployment-ui, onboarding-ui, settlement-ui, trading-analytics-ui

**Quality Gates** (TypeScript-specific):

- `tsc --noEmit` (type checking)
- ESLint (linting)
- Prettier (formatting)
- `npm test` (unit tests)

**Hardening Focus**:

1. **Type safety**: Explicit types (no `any`)
2. **Error boundaries**: Proper React error handling
3. **API error handling**: No silent failures
4. **Test coverage**: 50% minimum

**Approach**: 3 sub-agents (3 UIs each)

**Sub-Agent Pattern** (per group):

```
description: Harden [UI-1, UI-2, UI-3] TypeScript quality
model: fast
subagent_type: generalPurpose
prompt: |
  Harden 3 UI repos:
  - [UI-1]
  - [UI-2]
  - [UI-3]

  TypeScript patterns:
  1. Replace `any` with specific types
  2. Add error boundaries for React components
  3. Explicit error handling in API calls
  4. Add missing tests (50% coverage target)

  Verify per repo:
  - tsc --noEmit (0 errors)
  - npm run lint (0 errors)
  - npm test (50%+ coverage)

  RETURN: Status per UI
```

**Token Estimate**: ~600K tokens

- Master agent: ~100K
- Sub-agents: ~500K (3 agents × ~165K avg)

---

## Verification & Documentation

### Final Verification Checklist

**Per Repo** (24 Python + 9 UI = 33 total):

- Quality gates pass (exit 0)
- All tests pass
- QUALITY_GATE_BYPASS_AUDIT.md complete
- CANONICAL_PATTERNS.md referenced (Python) or TypeScript standards (UI)
- No skipped checks except documented third-party exceptions

### Documentation Artifacts

**Create** (workspace root):

1. `**.cursor/plans/HARDENING_COMPLETE.md`**:
  - Summary of all repos hardened
  - Violation counts: before → after
  - Exception inventory (third-party only)
  - Token usage summary
  - Cost summary
2. `**.cursor/plans/CANONICAL_STANDARDS.md`**:
  - Links to instruments-service/docs/CANONICAL_PATTERNS.md
  - Cross-references to cursor rules
  - Migration guide for future repos
3. `**.cursor/plans/TOKEN_USAGE_LOG.md`**:
  - Master agent: Phase-by-phase usage
  - Sub-agents: Per-agent breakdown with resume iterations
  - Total cost: Phase 1 + 2 + 3
  - Efficiency analysis vs direct approach

---

## Token & Cost Budget

### Projected Usage (Conservative Estimates)


| Phase                             | Master Agent | Sub-Agents | Total     | Cost       |
| --------------------------------- | ------------ | ---------- | --------- | ---------- |
| **Phase 1** (instruments-service) | 150K         | 510K       | 660K      | ~$1.60     |
| **Phase 2** (7 libraries)         | 100K         | 700K       | 800K      | ~$1.20     |
| **Phase 3A** (14 services)        | 200K         | 1M         | 1.2M      | ~$1.80     |
| **Phase 3B** (9 UIs)              | 100K         | 500K       | 600K      | ~$0.90     |
| **Documentation**                 | 50K          | —          | 50K       | ~$0.40     |
| **TOTAL**                         | **600K**     | **2.71M**  | **3.31M** | **~$5.90** |


**Pricing** (approximate):

- Sonnet 4.5: $3/1M input, $15/1M output (avg ~$9/1M)
- Fast model: $0.25/1M input, $1.25/1M output (avg ~$0.75/1M)

**Context Preservation**:

- Master agent stays under 600K total (40% of 1M context)
- Cursor rules never compressed ✅
- Effective capacity: 7M+ tokens across all sub-agents

**Cost Comparison**:

- **With sub-agents**: ~$5.90 total
- **Without sub-agents** (master does all): ~3.5M Sonnet tokens = ~$31.50
- **Savings**: ~$25.60 (81% reduction)

---

## Risk Mitigation

### Backup Strategy

**Before each phase**:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
git checkout -b backup-phase-X-$(date +%s)
git add -A && git commit -m "Backup before Phase X" || echo "Clean"
git checkout main
```

**Per-repo backups**: Each sub-agent creates backup branch before changes

### Rollback Plan

If quality gates cannot be fixed:

1. Identify blocker (third-party vs fixable)
2. If third-party: Document in QUALITY_GATE_BYPASS_AUDIT.md, continue
3. If fixable: Resume sub-agent with targeted guidance
4. If stuck after 3 resume iterations: Escalate to manual review
5. Nuclear option: `git checkout backup-phase-X` and restart phase

### Sub-Agent Amnesia Detection

**Watch for cursor rule violations** (from `.cursor/rules/rule-amnesia-detection.mdc`):

- Uses `os.getenv()` instead of config classes
- Uses `pip install` instead of `uv pip install`
- Suggests skipping tests or adding `|| true`
- Creates summary docs without being asked

**Action**: If detected → STOP sub-agent immediately, start fresh with explicit rule reminder

---

## Success Metrics

### Quantitative

- **Quality gate pass rate**: 33/33 repos (100%)
- **Test coverage**: ≥50% (production-ready)
- **Type Any reduction**: 95%+ (only third-party exceptions)
- **Empty fallbacks**: 0 (all fail-loud)
- **basedpyright errors**: 0 (or only documented exceptions)

### Qualitative

- **Canonical standard established**: instruments-service is reference implementation
- **Pattern library complete**: CANONICAL_PATTERNS.md guides all future work
- **Exception inventory audited**: QUALITY_GATE_BYPASS_AUDIT.md accurate for all repos
- **Cursor rules adherence**: Sub-agents never violate standards
- **Cost efficiency**: Token usage <3.5M via sub-agents

---

## Continuous Maintenance

### Post-Hardening Rules

**New code submissions**:

1. Quality gates must pass (no PRs merged with violations)
2. Third-party exceptions documented before merge
3. Tests required for new features
4. Type hints required (no `Any` unless documented)

**Monthly audits**:

- Run quality gates across all repos
- Check for new violations (code drift)
- Update QUALITY_GATE_BYPASS_AUDIT.md if new libraries added

**Codex updates**:

- [unified-trading-codex/06-coding-standards/quality-gates.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/06-coding-standards/quality-gates.md)
- [unified-trading-codex/06-coding-standards/audit-remediation-guide.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/06-coding-standards/audit-remediation-guide.md)

---

## Execution Checklist

### Phase 1 (instruments-service)

- Task 1A: Add quality checks to 24 Python repos
- Task 1B: Fix violations in instruments-service (4 sub-agents)
- Task 1C: Document canonical patterns
- Verify: Quality gates pass, tests pass, QUALITY_GATE_BYPASS_AUDIT.md complete

### Phase 2 (7 libraries)

- unified-cloud-services (UCS)
- unified-config-interface (UCI)
- unified-events-interface (UEI)
- unified-market-interface (UMI)
- unified-trade-execution-interface (UOI)
- unified-domain-services (UDS)
- execution-algo-library

### Phase 3A (14 services)

- Data pipeline (3): market-tick-data-handler, market-data-processing-service, pnl-attribution-service
- Features (4): features-calendar, features-delta-one, features-volatility, features-onchain
- ML (2): ml-training, ml-inference
- Trading (3): strategy, execution, risk-and-exposure
- Monitoring (1): position-balance-monitor
- Alert (1): alerting-system

### Phase 3B (9 UIs)

- backtest-ui, batch-audit-ui, client-reporting-ui
- live-health-monitor-ui, logs-dashboard-ui, ml-deployment-ui
- onboarding-ui, settlement-ui, trading-analytics-ui

### Documentation

- HARDENING_COMPLETE.md
- CANONICAL_STANDARDS.md
- TOKEN_USAGE_LOG.md

---

## Key References

**Cursor Rules**:

- [.cursor/rules/no-empty-fallbacks.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/no-empty-fallbacks.mdc)
- [.cursor/rules/no-type-any-use-specific.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/no-type-any-use-specific.mdc)
- [.cursor/rules/strict-type-checking.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/strict-type-checking.mdc)
- [.cursor/rules/quality-gates-audit-factors.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/quality-gates-audit-factors.mdc)
- [.cursor/rules/rule-amnesia-detection.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/rule-amnesia-detection.mdc)

**Task Templates**:

- [.cursor/plans/tasks/TEMPLATE.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TEMPLATE.md)
- [.cursor/plans/tasks/RESUME_PATTERN.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/RESUME_PATTERN.md)
- [.cursor/plans/tasks/TOKEN_TRACKING_GUIDE.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TOKEN_TRACKING_GUIDE.md)

**Codex**:

- [unified-trading-codex/06-coding-standards/quality-gates.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/06-coding-standards/quality-gates.md)
- [unified-trading-codex/06-coding-standards/audit-remediation-guide.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/06-coding-standards/audit-remediation-guide.md)

**Reference Implementation**:

- [instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md)
- [instruments_service/engine/operations/instruments/processors/cefi_processor.py](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service/instruments_service/engine/operations/instruments/processors/cefi_processor.py) (0 errors)
