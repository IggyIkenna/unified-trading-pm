---
name: Claude Code Quality Gates
overview: Fix Claude Code installation, then create comprehensive quality gates hardening tasks for 20+ repos with full pyright compliance, 35%+ coverage, and zero shortcuts via Claude Code orchestration.
todos:
  - id: install-claude-code
    content: Install Claude Code extension via cursor --install-extension Anthropic.claude-code
    status: pending
  - id: setup-mcp
    content: Create .cursor/mcp.json with filesystem server pointing to workspace
    status: pending
  - id: create-dir
    content: Create .cursor/plans/tasks_claude_code/ directory
    status: pending
  - id: create-readme
    content: Create tasks_claude_code/README.md with overview and prerequisites
    status: pending
  - id: create-setup
    content: Create tasks_claude_code/SETUP.md with installation instructions
    status: pending
  - id: create-orchestration
    content: Create tasks_claude_code/ORCHESTRATION_PATTERN.md explaining Claude Code workflow
    status: pending
  - id: create-task1
    content: Create tasks_claude_code/TASK_1_QUALITY_GATES_AUDIT.md (scan all 24 repos)
    status: pending
  - id: create-task2
    content: Create tasks_claude_code/TASK_2_PYRIGHT_FULL_COMPLIANCE.md (0 type errors)
    status: pending
  - id: create-task3
    content: Create tasks_claude_code/TASK_3_COVERAGE_35_PERCENT.md (minimum coverage)
    status: pending
  - id: create-task4
    content: Create tasks_claude_code/TASK_4_HARDEN_COVERAGE_GATES.md (blocking checks)
    status: pending
  - id: create-task5
    content: Create tasks_claude_code/TASK_5_ROLLOUT_ALL_SERVICES.md (systematic execution)
    status: pending
  - id: verify-install
    content: Test Claude Code can read task docs via MCP
    status: pending
isProject: false
---

# Claude Code Installation + Comprehensive Quality Gates Hardening

## Issue Diagnosis

**Current problem**: Trying to install from non-existent path:

```
~/.claude/local/node_modules/@anthropic-ai/claude-code/vendor/claude-code.vsix
```

**Root cause**: Claude Code extension not installed yet. The VSIX file doesn't exist.

**Solution**: Use VS Code Marketplace installation (official method).

---

## Phase 1: Install Claude Code Correctly

### Step 1: Install via Command Line (Simplest)

**For Cursor** (VSCode-based):

```bash
cursor --install-extension Anthropic.claude-code
```

**Alternatively via UI**:

1. Open Cursor
2. Press `Cmd+Shift+X` (Extensions)
3. Search "Claude Code" (by Anthropic)
4. Click "Install"

**Requirements**: Cursor v0.40+ (you have this)

### Step 2: Verify Installation

```bash
# Check extension installed
ls ~/.cursor/extensions/ | grep claude

# Launch Claude Code
# In Cursor terminal: claude
```

### Step 3: Configure MCP for Workspace Access

Create [.cursor/mcp.json](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/mcp.json):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
      ]
    }
  }
}
```

**Result**: Claude Code can read all 30+ repos via MCP


---

## Phase 2: Create tasks_claude_code Directory

### Directory Structure

```
.cursor/plans/
├── tasks/                           ← Existing tasks (Cursor sub-agents)
└── tasks_claude_code/               ← NEW (Claude Code orchestration)
    ├── README.md                    ← Overview, why Claude Code
    ├── SETUP.md                     ← Installation, MCP config
    ├── ORCHESTRATION_PATTERN.md    ← How Claude Code orchestrates sub-agents
    ├── TASK_1_QUALITY_GATES_AUDIT.md
    ├── TASK_2_PYRIGHT_FULL_COMPLIANCE.md
    ├── TASK_3_COVERAGE_35_PERCENT.md
    ├── TASK_4_HARDEN_COVERAGE_GATES.md
    └── TASK_5_ROLLOUT_ALL_SERVICES.md
```

---

## Phase 3: Comprehensive Quality Gates Tasks (20+ Repos)

### Scope Analysis

**Target repos** (based on [COMPLETE_REPO_INVENTORY.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/COMPLETE_REPO_INVENTORY.md)):

**Python Services (14)**:

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
13. risk-and-exposure-service
14. position-balance-monitor-service

**Python Libraries (6)**:
15. unified-trading-services
16. unified-config-interface
17. unified-events-interface
18. unified-market-interface
19. unified-trade-execution-interface
20. unified-domain-client

**Utility (4)**:
21. execution-algo-library
22. alerting-system
23. unified-trading-deployment-v3 (has Python utils)
24. unified-trading-deployment-v3 (has Python utils)

**Total**: 24 Python repos

---

## Task 1: Quality Gates Audit (Claude Code Orchestration)

**File**: `tasks_claude_code/TASK_1_QUALITY_GATES_AUDIT.md`

**Goal**: Scan all 24 repos, identify current quality gate status

**Claude Code workflow**:

1. **Read standards** via MCP:
  - `.cursor/rules/strict-quality-gates.mdc`
  - `.cursor/rules/quality-gates-hardening.mdc`
  - `unified-trading-codex/06-coding-standards/quality-gates.md`
2. **Scan all 24 repos** via MCP:
  - Run `bash scripts/quality-gates.sh --no-fix` per repo
  - Capture exit codes, violation counts
  - Check QUALITY_GATE_BYPASS_AUDIT.md exists
3. **Generate audit report**:

```
   | Repo | Quality Gates | Pyright | Coverage | Violations |
   |------|---------------|---------|----------|------------|
   | instruments-service | PASS | 396 errors | 42% | 15 |
   | market-tick-data-handler | FAIL | 523 errors | 28% | 32 |
   ...


```

1. **Prioritize repos**:
  - Tier 1: Already >35% coverage (just fix violations)
  - Tier 2: 20-35% coverage (add tests + fix violations)
  - Tier 3: <20% coverage (major test additions needed)

**Output**: Audit report + prioritized task list for Task 2-5

---

## Task 2: Pyright Full Compliance (Zero Tolerance)

**File**: `tasks_claude_code/TASK_2_PYRIGHT_FULL_COMPLIANCE.md`

**Goal**: All 24 repos pass `basedpyright --level warning` with 0 errors

**Standards** (from `.cursor/rules/strict-type-checking.mdc`):

- No `Any` types (use Protocol, TypedDict, TypeVar)
- No `object` types (use specific types)
- Only exceptions: Third-party library types (documented in QUALITY_GATE_BYPASS_AUDIT.md)
- Must use `# type: ignore[reportAny]` for documented exceptions only

**Claude Code orchestration**:

1. **Tier 1 repos** (<100 errors) - 8 repos:
  - Launch 4 Cursor sub-agents (2 repos each)
  - Each agent: Remove decorators, add explicit types, manual retry pattern
  - Reference: `instruments-service/docs/CANONICAL_PATTERNS.md`
2. **Tier 2 repos** (100-500 errors) - 10 repos:
  - Launch 5 Cursor sub-agents (2 repos each)
  - Focus on systematic patterns (empty fallbacks, Type Any)
  - Use resume pattern extensively (iterative corrections)
3. **Tier 3 repos** (>500 errors) - 6 repos:
  - Launch 6 Cursor sub-agents (1 repo each, dedicated)
  - File-by-file approach (largest files first)
  - Multiple resume iterations expected

**Claude Code role**:

- Generate sub-agent prompts (read canonical patterns via MCP)
- Launch Cursor sub-agents
- Review results (check basedpyright output)
- Resume agents with targeted guidance until 0 errors

**Success criteria**: `basedpyright --level warning` exits 0 for all 24 repos

---

## Task 3: Coverage 35% Minimum (Blocking)

**File**: `tasks_claude_code/TASK_3_COVERAGE_35_PERCENT.md`

**Goal**: All 24 repos achieve ≥35% test coverage (pytest-cov)

**Current state** (estimated from existing tasks):

- 8 repos already >35%
- 10 repos between 20-35%
- 6 repos <20%

**Standards** (from `.cursor/rules/test-coverage-targets.mdc`):

- 35% minimum (quality gates blocking)
- 50% recommended (production readiness)
- Unit tests with synthetic fixtures (no real GCS/API calls)
- Follow test quality standards (`.cursor/rules/test-quality-standards.mdc`)

**Claude Code orchestration**:

1. **Generate test skeletons**:
  - Scan each repo via MCP
  - Identify untested files/functions
  - Generate test file templates per module
2. **Launch Cursor sub-agents** (4 parallel, 6 repos each):
  - Write unit tests following standards
  - Use conftest.py fixtures (singleton pattern)
  - Mock external dependencies (GCS, APIs)
  - Target 35% minimum (not 100%)
3. **Verify coverage**:
  - Run `pytest --cov --cov-report=term-missing`
  - Check coverage ≥35%
  - Resume if below threshold

**Success criteria**: All repos pass `pytest --cov --cov-fail-under=35`

---

## Task 4: Harden Coverage Gates (Blocking)

**File**: `tasks_claude_code/TASK_4_HARDEN_COVERAGE_GATES.md`

**Goal**: Update quality-gates.sh in all 24 repos to BLOCK on coverage <35%

**Current state**: Many repos have coverage checks but non-blocking (warnings only)

**Required change** (per repo's `scripts/quality-gates.sh`):

```bash
# STEP 4: TEST COVERAGE (BLOCKING - update from warning to fail)
echo "Running pytest with coverage..."
pytest --cov=${SOURCE_DIR} \
       --cov-report=term-missing \
       --cov-report=html:htmlcov \
       --cov-fail-under=35 \
       -v || {
    echo -e "${RED}FAIL: Test coverage below 35%${NC}"
    exit 1  # BLOCKING, not warning
}
```

**Claude Code orchestration**:

1. **Scan all quality-gates.sh** via MCP:
  - Find coverage check sections
  - Identify non-blocking (warnings/optional)
2. **Launch 2 Cursor sub-agents**:
  - Agent 1: Update 12 repos (services)
  - Agent 2: Update 12 repos (libraries + utility)
  - Make coverage checks blocking with `exit 1`
3. **Verify**:
  - Run quality gates in each repo
  - Confirm fails if coverage <35%

**Success criteria**: Quality gates exit 1 if coverage <35% (blocking)

---

## Task 5: Rollout to All Services (Systematic)

**File**: `tasks_claude_code/TASK_5_ROLLOUT_ALL_SERVICES.md`

**Goal**: Execute Tasks 1-4 across all 24 repos systematically

**Rollout strategy**:

### Phase A: Foundation (Libraries first)

**Repos**: 6 libraries (UCS, UCI, UEI, UMI, UOI, UDS)

**Why first**: Services depend on libraries. Fix dependencies before consumers.

**Execution**:

- Task 2 (Pyright): 3 sub-agents (2 libs each)
- Task 3 (Coverage): 2 sub-agents (3 libs each)
- Task 4 (Harden): 1 sub-agent (all 6)

**Timeline**: 2-3 hours per library (parallel) = 3-4 hours total

### Phase B: Core Services (Data pipeline)

**Repos**: instruments-service, market-tick-data-handler, market-data-processing-service, pnl-attribution-service

**Why**: Critical path for all downstream services

**Execution**:

- Task 2: 4 sub-agents (1 service each)
- Task 3: 2 sub-agents (2 services each)
- Task 4: 1 sub-agent (all 4)

**Timeline**: 3-4 hours per service (parallel) = 4-5 hours total

### Phase C: Features Services

**Repos**: features-calendar, features-delta-one, features-volatility, features-onchain

**Execution**: Same pattern as Phase B

**Timeline**: 3-4 hours total

### Phase D: ML + Trading Services

**Repos**: ml-training, ml-inference, strategy, execution, risk-and-exposure, position-balance-monitor

**Execution**: 3 sub-agents (2 services each)

**Timeline**: 4-5 hours total

### Phase E: Utility Repos

**Repos**: execution-algo-library, alerting-system, deployment-v2, deployment-v3

**Execution**: 1 sub-agent (all 4)

**Timeline**: 2-3 hours total

**Total timeline**: 16-20 hours (with Claude Code orchestration + Cursor sub-agents)

**Total cost estimate**:

- Claude Code (planning/orchestration): $0 (included in Claude Pro $20/mo)
- Cursor sub-agents: ~15M tokens @ $0.75/1M = ~$11.25
- **Total**: ~$11.25 (vs ~$80+ if master agent did everything)

---

## Phase 4: Documentation Files

### README.md

```markdown
# Claude Code Quality Gates Tasks

## Purpose
Comprehensive quality gates hardening for 24 Python repos using Claude Code orchestration + Cursor sub-agents.

## Why Claude Code?
- **Cost**: 85% cheaper than all-Cursor approach
- **Automation**: Claude Code orchestrates sub-agents automatically
- **Context**: MCP access to all 30+ repos
- **Standards**: Reads canonical patterns, enforces cursor rules

## Task Structure
1. TASK_1: Audit current state (scan all 24 repos)
2. TASK_2: Pyright full compliance (0 errors, 0 shortcuts)
3. TASK_3: Coverage 35% minimum (all repos)
4. TASK_4: Harden coverage gates (blocking)
5. TASK_5: Systematic rollout (libraries → services → utility)

## Prerequisites
- Claude Code installed in Cursor
- MCP configured (filesystem access)
- Claude Pro subscription

## Execution
Ask Claude Code: "Execute TASK_1 via orchestrating Cursor sub-agents"
```

### SETUP.md

Complete installation instructions (VS Code Marketplace method, MCP config)

### ORCHESTRATION_PATTERN.md

How Claude Code orchestrates:

1. Reads standards via MCP
2. Scans repos via MCP
3. Generates optimized sub-agent prompts
4. Launches Cursor Task sub-agents
5. Reviews results
6. Resumes agents if violations

---

## Success Metrics

**Quantitative**:

- All 24 repos: `basedpyright --level warning` exits 0
- All 24 repos: `pytest --cov --cov-fail-under=35` passes
- All 24 repos: Quality gates exit 0 (no shortcuts)
- Zero `Any` types except documented third-party exceptions

**Qualitative**:

- QUALITY_GATE_BYPASS_AUDIT.md complete and accurate for all repos
- All exceptions documented with justification
- Canonical patterns established (instruments-service reference)
- CI/CD integration works (quality gates in GitHub Actions)

**Cost efficiency**:

- Total cost <$15 for all 24 repos (vs ~$80+ with all-Cursor)
- 85% savings via Claude Code orchestration

---

## Next Steps

1. **Now** (5 min): Install Claude Code via `cursor --install-extension Anthropic.claude-code`
2. **Setup** (5 min): Create `.cursor/mcp.json` with filesystem server
3. **Test** (5 min): Verify Claude Code can read task docs via MCP
4. **Execute** (16-20 hours): Run TASK_1 → TASK_5 systematically

---

## Files to Create

All in `.cursor/plans/tasks_claude_code/`:

1. `README.md` - Overview
2. `SETUP.md` - Installation guide
3. `ORCHESTRATION_PATTERN.md` - How Claude Code works
4. `TASK_1_QUALITY_GATES_AUDIT.md` - Scan all repos
5. `TASK_2_PYRIGHT_FULL_COMPLIANCE.md` - 0 type errors
6. `TASK_3_COVERAGE_35_PERCENT.md` - Minimum coverage
7. `TASK_4_HARDEN_COVERAGE_GATES.md` - Blocking checks
8. `TASK_5_ROLLOUT_ALL_SERVICES.md` - Systematic execution

**Total**: 8 new files

---

## References

**Existing tasks** (`.cursor/plans/tasks/`):

- [TASK_1_ADD_QUALITY_CHECKS.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TASK_1_ADD_QUALITY_CHECKS.md)
- [TASK_2_FIX_VIOLATIONS.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TASK_2_FIX_VIOLATIONS.md)
- [TASK_3_TYPE_CLEANUP.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TASK_3_TYPE_CLEANUP.md)
- [TEMPLATE.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/TEMPLATE.md)

**Cursor rules**:

- [.cursor/rules/strict-quality-gates.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/strict-quality-gates.mdc)
- [.cursor/rules/quality-gates-hardening.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/quality-gates-hardening.mdc)
- [.cursor/rules/test-coverage-targets.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/test-coverage-targets.mdc)
- [.cursor/rules/test-quality-standards.mdc](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/test-quality-standards.mdc)

**Codex**:

- [unified-trading-codex/06-coding-standards/quality-gates.md](file:///Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/06-coding-standards/quality-gates.md)
