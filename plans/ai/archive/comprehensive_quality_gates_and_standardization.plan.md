---
name: Comprehensive Quality Gates and Service Standardization
overview: Harden quality gates AND standardize service architecture across the entire workspace (30+ repos). Address quality gates (basedpyright, E501), CLI patterns (--operation + --mode), service structure (engine/adapters/cli), thin adapter delegation, DRY violations, and UI quality gates. Build on completed work in instruments-service and 6 hardened libraries.
todos:
  - id: lib-pyright-fix
    content: "Phase 1A: Fix 2 libraries still using pyright (unified-domain-client, unified-trade-execution-interface)"
    status: pending
  - id: service-quality-gates
    content: "Phase 1B: Harden 11 service quality gates (basedpyright, E501, codex checks)"
    status: pending
  - id: ui-quality-gates
    content: "Phase 1C: Add UI quality gates to 3 repos (onboarding-ui, execution-services/visualizer-ui, UTDv2/ui)"
    status: pending
  - id: instruments-remove-app-core
    content: "Phase 1D: CRITICAL - Delete instruments-service app/core/ directory (2 compatibility wrappers)"
    status: pending
  - id: cli-standardization
    content: "Phase 2: REQUIRED - Convert ALL 14 services to --operation + --mode (currently ZERO services use it)"
    status: pending
  - id: service-structure
    content: "Phase 3: Complete service structure refactoring (engine/adapters/cli for 13 services)"
    status: pending
  - id: thin-adapters
    content: "Phase 4: Enforce thin adapter pattern (delegate to libraries, remove DRY violations)"
    status: pending
  - id: clean-code
    content: "Phase 5: Remove orphaned code, duplicates, deprecated implementations"
    status: pending
  - id: codex-update
    content: "Phase 6: Update codex and cursor rules with all standardized patterns"
    status: pending
  - id: bypass-audits
    content: "Phase 7: Create QUALITY_GATE_BYPASS_AUDIT.md for all 17 repos"
    status: pending
  - id: final-verification
    content: "Phase 8: Verify all repos pass quality gates and follow standards"
    status: pending
isProject: false
---

# Comprehensive Quality Gates and Service Standardization Plan

## Executive Summary

Based on fresh investigation (Feb 23, 2026), this plan addresses **quality gate hardening** AND **service architecture standardization** across 30+ repos. Recent work hardened 9 repos (instruments-service + 6 libraries + 2 other services); 17 repos need hardening. Additionally, service structure and CLI patterns need standardization across all 14 services.

---

## 🎯 CRITICAL REQUIREMENTS (Non-Negotiable)

### 1. DELETE app/core/ from instruments-service (Phase 1D)

**STATUS:** instruments-service has `app/core/` with 2 compatibility wrappers — **MUST BE REMOVED**

**FILES TO DELETE:**
- `app/core/instruments_service.py` (50 lines, DEPRECATED marker)
- `app/core/instrument_processing_service.py` (~300 lines)
- `app/__init__.py`
- **Entire `app/` directory**

**WHY:** Compatibility wrappers are technical debt. Delete them to establish clean baseline.

**WHEN:** Phase 1D (after quality gate hardening, before CLI standardization)

### 2. ALL 14 Services MUST Use --operation + --mode (Phase 2)

**STATUS:** ZERO services use this pattern currently (100% need conversion)

**CURRENT PROBLEM:**
```bash
# ❌ Conflates WHAT + HOW
--mode instruments              # Is this batch or live? Unclear!
--mode corporate_actions_production  # What mode? Unclear!
--mode download                 # Batch or live? Unclear!
```

**REQUIRED TARGET:**
```bash
# ✅ Clean separation
--operation instrument --mode batch
--operation aggregate --mode batch
--operation fetch --mode live
--operation compute --mode batch
```

**NO EXCEPTIONS:** All 14 services must convert. This is a codex requirement per `04-architecture/batch-live-symmetry.md` and `06-coding-standards/cli-standards.md`.

### 3. ALL Services Get engine/adapters/cli Structure (Phase 3)

**STATUS:**
- 1/14 services has engine/adapters (instruments-service) but still has app/core/
- 13/14 services still have app/core/ or similar legacy structure

**TARGET:** ALL 14 services have:
- ✅ `engine/` (mode-agnostic business logic)
- ✅ `adapters/` (thin <100 line wrappers)
- ✅ `cli/` (orchestration with --operation + --mode)
- ❌ NO `app/core/` remaining (ZERO services may have this)

---

**Key insight:** instruments-service has been PARTIALLY refactored (has `engine/operations/`, `adapters/`, but still has `app/core/` wrappers and uses old `--mode` pattern). This plan completes the standardization and rolls out to all services.

---

## Current State (After Recent Work)

### ✅ Completed Work

**Hardened repos (9 total):**

1. ✅ instruments-service — Has `engine/`, `adapters/`, uses `basedpyright`, E501 enforced, 35% coverage
2. ✅ unified-trading-services — Uses `basedpyright`, passes all quality gates
3. ✅ unified-config-interface — Uses `basedpyright`, strict mode
4. ✅ unified-events-interface — Uses `basedpyright`, strict mode, has observability features
5. ✅ execution-algo-library — Uses `basedpyright`
6. ✅ unified-trading-deployment-v3 — Hardened quality gates
7. ✅ risk-and-exposure-service — Hardened quality gates
8. ✅ pnl-attribution-service — Hardened quality gates
9. ✅ alerting-system — Hardened quality gates

**Observability centralization:**

- ✅ `ErrorWarningCounter` in unified-events-interface
- ✅ Memory tracking helpers in unified-events-interface
- ✅ instruments-service uses UEI directly (no local implementation)

**Config centralization:**

- ✅ UCI overhaul complete (ConfigStore, TimeSeriesConfigStore, ConfigReloader)
- ✅ All services inherit from `UnifiedCloudConfig`
- ⚠️ Services don't use ConfigStore yet (only inheritance)

**API keys:**

- ✅ instruments-service uses `get_secret_client` (2 script exceptions documented)

### ⚠️ Partial Work

**instruments-service:**

- ✅ Has `engine/operations/instruments/orchestrator.py` (1112 lines)
- ✅ Has `adapters/` (2 files: data_source_adapter.py, storage_adapter.py)
- ❌ Has `app/core/` (2 compatibility wrappers: instruments_service.py 50 lines, instrument_processing_service.py 300 lines) — **MUST DELETE in Phase 1D**
- ❌ CLI uses `--mode` with mixed values ("instruments", "aggregate", "corporate_actions", "corporate_actions_production")
- ❌ **MUST convert to --operation + --mode in Phase 2 (currently does NOT follow codex pattern)**

**Libraries:**

- ⚠️ unified-domain-client: Uses `pyright` (not `basedpyright`) — line 80-116 in quality-gates.sh
- ⚠️ unified-trade-execution-interface: Uses `pyright` (not `basedpyright`) — line 249-282 in quality-gates.sh

### ❌ Needs Work (17 repos)

**Python services (11):**

1. market-tick-data-handler — Uses `pyright`, E501 ignored, has app/ structure
2. market-data-processing-service — Uses `pyright`, E501 ignored, has app/core/ and app/adapters/
3. features-calendar-service — Uses `pyright`, minimal ruff rules, has app/core/
4. features-delta-one-service — Uses `pyright`, minimal ruff rules
5. features-volatility-service — Uses `pyright`, E501 ignored
6. features-onchain-service — Uses `pyright`, minimal ruff rules
7. ml-training-service — Uses `pyright`, E501 ignored
8. ml-inference-service — Uses `pyright`, E501 ignored, **uses `pip` not `uv`** (P0!)
9. strategy-service — Uses `pyright` (informational only, not blocking), has app/core/
10. execution-services — Uses `pyright` (informational only), uses `pip` in one place
11. position-balance-monitor-service — Status unknown (likely hardened)

**Python libraries (2):**

- unified-domain-client — Coverage 14% (need 35%), uses `pyright`
- unified-market-interface — Coverage 22% (need 35%), already uses `basedpyright`

**TypeScript UIs (3):**

- onboarding-ui — Missing GitHub workflow
- execution-services/visualizer-ui — Missing quality-gates.sh, missing workflow, has `strict: false`
- unified-trading-deployment-v3/ui — Missing quality-gates.sh, missing workflow

**Deployment (1):**

- unified-trading-deployment-v3 — Already hardened ✅

---

## Architecture Gaps (Per Codex)

### Gap 1: CLI Pattern

**Current:** All services use `--mode` with mixed values


| Service                        | Current `--mode` Values                                                         | Conflates?           |
| ------------------------------ | ------------------------------------------------------------------------------- | -------------------- |
| instruments-service            | "instruments", "aggregate", "corporate_actions", "corporate_actions_production" | ✅ YES (WHAT + HOW)   |
| market-tick-data-handler       | "download"                                                                      | ✅ YES                |
| market-data-processing-service | Subcommands ("process", "list")                                                 | ⚠️ Different pattern |
| features-*                     | "batch", "info", "incremental"                                                  | ⚠️ Mixed             |
| ml-training-service            | "train", "evaluate", "grid-search", etc.                                        | ✅ YES                |
| strategy-service               | "batch"                                                                         | ⚠️ Only HOW          |


**Target (Codex):** ALL services use `--operation` (WHAT) and `--mode` (HOW) separately

```bash
# Codex standard
--operation instrument --mode batch
--operation aggregate --mode batch
--operation fetch --mode live
--operation compute --mode batch
```

### Gap 2: Service Structure

**Current:** Most services have `app/core/` (not `engine/adapters/`)


| Service                        | Structure              | Has engine/? | Has adapters/?             |
| ------------------------------ | ---------------------- | ------------ | -------------------------- |
| instruments-service            | Hybrid                 | ✅ Yes        | ✅ Yes (+ legacy app/core/) |
| market-data-processing-service | app/                   | ❌ No         | ⚠️ app/adapters/           |
| All others                     | app/core/ or cli/ only | ❌ No         | ❌ No                       |


**Target (Codex):** `engine/` (mode-agnostic), `adapters/` (thin wrappers), `cli/` (orchestration)

### Gap 3: Thin Adapter Pattern

**Current:** Services have thick adapters with business logic, or no adapters at all

**Target:** Adapters <100 lines, delegate to unified libraries (UCS, UMI, UCI, UEI)

```python
# ✅ Good adapter (thin)
from unified_trading_services import get_storage_client

class GCSDataSource:
    def __init__(self, bucket: str):
        self.client = get_storage_client()  # Delegate to UCS
        self.bucket = bucket

    def read(self, path: str) -> pd.DataFrame:
        return self.client.read_parquet(self.bucket, path)  # Just delegate
```

### Gap 4: DRY Violations

**Known duplicates to remove:**

- `_load_instruments_by_venue` in market-tick-data-handler, market-data-processing-service (use InstrumentsDomainClient)
- Error counter implementations in services (use UEI ErrorWarningCounter)
- Memory tracking logic (use UEI helpers)
- Dependency checker patterns (standardize template)

---

## Comprehensive Hardening Standard

### Python Repos (Services + Libraries)

**Quality gates MUST include:**

1. **Type checking:** `basedpyright>=1.20.0,<2.0.0`
  - Command: `basedpyright <source>/ --level warning` (blocking, not informational)
  - Config: `pyrightconfig.json` with `reportAny: "error"`, `reportUnknown*: "error"`
  - Tests excluded per audit
2. **Linting:** Ruff 0.15.0 with E501 enforced
  - Remove E501 from `ignore` in `pyproject.toml`
  - Use `--line-length 120` in all ruff commands
  - Full rules: `select = ["E", "F", "W", "I", "UP"]`
3. **Testing:** 35% minimum coverage (50% recommended, 80% audit goal)
  - `pytest --cov=<source> --cov-fail-under=35`
  - `pytest-xdist` for parallel execution (`-n auto`)
  - 4-tier structure: unit, integration, e2e, smoke
4. **Codex compliance:** 12 ripgrep checks
  - print() statements, os.getenv(), datetime.now(), bare except
  - Empty fallbacks, Any types, imports in functions, hardcoded project IDs
  - Credential .gitignore, broad except Exception, file size limits
5. **Package manager:** `uv pip install` only (never `pip install` except bootstrap)
6. **Bypass documentation:** `QUALITY_GATE_BYPASS_AUDIT.md` with all exceptions documented

### TypeScript UI Repos

**Quality gates MUST include:**

1. **Type checking:** `tsc --noEmit`
  - Script: `"type-check": "tsc --noEmit"` in `package.json`
  - Config: `tsconfig.json` with `"strict": true`
2. **Linting:** ESLint
  - Script: `"lint": "eslint ."` in `package.json`
3. **Optional:** Playwright smoke tests
  - Reference: `onboarding-ui` (12 tests, 6.4s runtime)

---

## Phase 1: Quality Gate Hardening (17 Repos)

### Phase 1A: Fix 2 Libraries (pyright → basedpyright)

**Priority: P1** (blocks services that depend on them)

**Repos:**

1. **unified-domain-client**
  - Replace `pyright` with `basedpyright` in scripts/quality-gates.sh (lines 80-116)
  - Coverage already 35%+ ✅
  - Add tests if needed to maintain 35% minimum
2. **unified-trade-execution-interface**
  - Replace `pyright` with `basedpyright` in scripts/quality-gates.sh (lines 249-282)
  - Coverage already 35%+ ✅

**Changes per library:**

```bash
# pyproject.toml
[project.optional-dependencies]
dev = [
    "basedpyright>=1.20.0,<2.0.0",  # NOT pyright
]

# scripts/quality-gates.sh (replace pyright detection)
if command -v basedpyright &> /dev/null; then
    TYPE_CHECKER="basedpyright"
elif python3 -c "import basedpyright" &> /dev/null; then
    TYPE_CHECKER="python3 -m basedpyright"
else
    uv pip install "basedpyright>=1.20.0" --quiet
    TYPE_CHECKER="basedpyright"
fi

# Run type checker (blocking)
$TYPE_CHECKER unified_domain_client/ --level warning
```

### Phase 1B: Harden 11 Service Quality Gates

**Category B1: P0 Critical (1 repo) — Blocks all other work**

**ml-inference-service:**

- Uses `pip install ruff` instead of `uv pip install ruff` (lines 205, 229 in quality-gates.sh)
- Violates `.cursor/rules/uv-package-manager.mdc`
- **Action:** Fix immediately before proceeding

**Category B2: pyright → basedpyright + E501 removal (5 repos)**

These have full ruff config but need type checker upgrade and E501 removal:

1. **market-tick-data-handler**
2. **market-data-processing-service**
3. **features-volatility-service**
4. **ml-training-service**
5. **ml-inference-service** (after P0 fix)

**Changes per repo:**

```toml
# pyproject.toml
[tool.ruff.lint]
ignore = [
    # "E501",  ← REMOVE THIS LINE
    "E722",  # Keep: Bare except in scripts only
]

[project.optional-dependencies]
dev = [
    "basedpyright>=1.20.0,<2.0.0",  # NOT pyright
]
```

**Category B3: Minimal ruff → full ruff + basedpyright (3 repos)**

These have minimal ruff config (`select = ["I", "UP"]`) and need expansion:

1. **features-calendar-service**
2. **features-delta-one-service**
3. **features-onchain-service**

**Changes per repo:**

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP"]  # Was ["I", "UP"]

[project.optional-dependencies]
dev = [
    "basedpyright>=1.20.0,<2.0.0",  # NOT pyright
]
```

**Category B4: Make pyright blocking (2 repos)**

These have hardened quality gates but pyright is "informational only":

1. **strategy-service** — Remove `|| true` or informational flags, make blocking
2. **execution-services** — Remove `|| true`, fix `pip` → `uv pip` (one occurrence)

**Category B5: Verify position-balance-monitor (1 repo)**

- Check if already hardened (likely yes based on earlier investigation)
- If not, apply Category B2 pattern

### Phase 1C: Harden 3 UI Quality Gates

**onboarding-ui:**

- Missing: `.github/workflows/quality-gates.yml`
- Already has: `scripts/quality-gates.sh`, `tsconfig.json` with `strict: true`
- **Action:** Copy GitHub workflow from `backtest-ui`

**execution-services/visualizer-ui (embedded):**

- Missing: `scripts/quality-gates-ui.sh` in execution-services
- Missing: GitHub workflow step for UI
- Issue: `tsconfig.json` has `strict: false` (should be `true`)
- **Actions:**
  1. Create quality-gates-ui.sh in execution-services/scripts/
  2. Add workflow step to .github/workflows/quality-gates.yml
  3. Update `tsconfig.json` to set `strict: true`

**unified-trading-deployment-v3/ui (embedded):**

- Missing: `scripts/quality-gates-ui.sh` in UTDv2
- Missing: GitHub workflow step for UI
- Already has: `tsconfig.app.json` with `strict: true`
- **Actions:**
  1. Create quality-gates-ui.sh in UTDv2/scripts/
  2. Add workflow step to .github/workflows/quality-gates.yml

---

## Phase 2: CLI Standardization (CRITICAL - ALL 14 Services MUST Convert)

**CRITICAL REQUIREMENT:** Per codex `04-architecture/batch-live-symmetry.md` and `06-coding-standards/cli-standards.md`, ALL 14 services MUST separate "WHAT to run" (--operation) from "HOW to run" (--mode).

**CURRENT STATE:** ZERO services use this pattern correctly. All need conversion.

**RATIONALE:** Conflating WHAT + HOW creates confusion:
- `--mode instruments` — Is this batch or live? Unclear!
- `--mode corporate_actions_production` — What mode is this? Not clear!
- `--mode batch` — Batch what? Missing operation!

**TARGET:** Clean separation enables proper batch-live symmetry architecture.

### Current State Analysis (ALL Services Need Conversion)

**ZERO services use `--operation` + `--mode` pattern yet:**


| Service                        | Current Pattern                                                                                       | Issues               |
| ------------------------------ | ----------------------------------------------------------------------------------------------------- | -------------------- |
| instruments-service            | `--mode` with values: "instruments", "aggregate", "corporate_actions", "corporate_actions_production" | Conflates WHAT + HOW |
| market-tick-data-handler       | `--mode download`                                                                                     | Conflates WHAT + HOW |
| market-data-processing-service | Subcommands: "process", "list"                                                                        | Different pattern    |
| features-calendar-service      | `--mode` with "batch", "info"                                                                         | Inconsistent         |
| features-delta-one-service     | `--mode` with "batch", "incremental"                                                                  | Inconsistent         |
| ml-training-service            | `--mode` with "train", "evaluate", "grid-search", etc.                                                | Conflates WHAT + HOW |
| Others                         | `--mode batch` only                                                                                   | Missing --operation  |


### Target Pattern (Codex Standard)

**ALL services MUST use:**

```bash
--operation <what>  # Service-specific: instrument, aggregate, fetch, compute, train, etc.
--mode <how>        # Universal: batch or live
```

**Examples:**

```bash
# instruments-service
--operation instrument --mode batch --start-date 2024-01-01
--operation aggregate --mode batch
--operation corporate_actions --mode batch

# market-tick-data-handler
--operation fetch --mode batch --start-date 2024-01-01
--operation fetch --mode live

# features-delta-one-service
--operation compute --mode batch --start-date 2024-01-01
--operation compute --mode live --interval 15
```

### Operation Mapping per Service


| Service                          | Operations                               | Notes                                          |
| -------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| instruments-service              | instrument, aggregate, corporate_actions | 3 operations                                   |
| market-tick-data-handler         | fetch                                    | 1 operation                                    |
| market-data-processing-service   | process                                  | 1 operation (replace subcommands)              |
| features-calendar-service        | compute                                  | 1 operation (remove "info" mode)               |
| features-delta-one-service       | compute                                  | 1 operation (replace "incremental" with batch) |
| features-volatility-service      | compute                                  | 1 operation                                    |
| features-onchain-service         | compute                                  | 1 operation                                    |
| ml-training-service              | train                                    | 1 operation (stages via --stage flag)          |
| ml-inference-service             | infer                                    | 1 operation                                    |
| strategy-service                 | backtest, live_trade                     | 2 operations                                   |
| execution-services               | execute                                  | 1 operation (event-driven, mode from config)   |
| risk-and-exposure-service        | compute                                  | 1 operation (mode from config)                 |
| position-balance-monitor-service | monitor                                  | 1 operation (mode from config)                 |
| pnl-attribution-service          | compute                                  | 1 operation (mode hardcoded)                   |


### Implementation Pattern

**Update cli/parser.py in ALL services:**

```python
def parse_arguments():
    parser = argparse.ArgumentParser()

    # Operation: WHAT to run (service-specific)
    parser.add_argument(
        "--operation",
        required=True,
        choices=["instrument", "aggregate", "corporate_actions"],  # Service-specific
        help="Operation to perform"
    )

    # Mode: HOW to run (universal)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["batch", "live"],
        help="Execution mode: batch (date range) or live (scheduled/continuous)"
    )

    # Batch-specific
    parser.add_argument("--start-date", help="Start date (batch mode)")
    parser.add_argument("--end-date", help="End date (batch mode)")

    # Live-specific
    parser.add_argument("--interval", type=int, default=15, help="Interval minutes (live mode)")

    args = parser.parse_args()

    # Backward compatibility: Auto-convert old --mode values (NO DUPLICATE LOGIC)
    if args.mode in ["instrument", "aggregate", "corporate_actions", "corporate_actions_production"]:
        logger.warning(
            f"⚠️ --mode {args.mode} is deprecated. "
            f"Use --operation {args.mode} --mode batch instead."
        )
        args.operation = args.mode.replace("_production", "")
        args.mode = "batch"

    return args
```

**Key:** Conversion happens ONCE at parse time, all downstream code uses `args.operation` and `args.mode`.

### Rollout Strategy

**Use parallel agents (4 agents, 3-4 services each):**

- Agent 1: instruments-service, market-tick-data-handler, market-data-processing-service
- Agent 2: features-calendar, features-delta-one, features-volatility, features-onchain
- Agent 3: ml-training, ml-inference, strategy-service
- Agent 4: execution-services, risk-and-exposure, position-balance-monitor, pnl-attribution

**Per-service effort:** ~15-20 min each × 4 agents in parallel = ~15-20 min total

---

## Phase 3: Service Structure Refactoring (engine/adapters/cli)

### Current State


| Service                        | Has engine/? | Has adapters/?   | Has app/core/?     | Status       |
| ------------------------------ | ------------ | ---------------- | ------------------ | ------------ |
| instruments-service            | ✅ Yes        | ✅ Yes            | ⚠️ Legacy wrappers | 90% complete |
| market-data-processing-service | ❌ No         | ⚠️ app/adapters/ | ✅ Yes              | 20% complete |
| All other services             | ❌ No         | ❌ No             | ✅ Yes              | 0% complete  |


### Target Structure (Codex Standard)

```
{service_module}/
  engine/                    # Mode-agnostic (90% of code)
    orchestrator.py          # Top-level orchestration
    operations/              # Operation-specific logic (if multiple operations)
      operation1/
        orchestrator.py
        processors/
      operation2/
    processors/              # Shared processors
    validation/              # dependency_checker.py (standardized)
    venues/                  # Venue-specific logic (if applicable)
  adapters/                  # Thin wrappers (<100 lines)
    data_source.py           # GCSDataSource, StreamDataSource
    data_sink.py             # GCSDataSink, BroadcastSink
  cli/
    main.py                  # Entry point with --operation + --mode
    handlers/                # Operation-specific handlers
  config.py                  # Top-level singleton (uses ConfigStore)
  schemas/                   # Service-owned schemas
```

### Refactoring Steps per Service

**Step 1: Create new directories**

```bash
mkdir -p {service_module}/engine/operations
mkdir -p {service_module}/engine/processors
mkdir -p {service_module}/engine/validation
mkdir -p {service_module}/adapters
```

**Step 2: Move app/core/ logic to engine/**

- Move business logic, calculators, processors
- Remove I/O code (GCS, APIs) from moved files
- Keep engine/ pure (no storage, no API calls)

**Step 3: Extract I/O to adapters/ (THIN wrappers)**

- Create GCSDataSource, GCSDataSink
- Delegate to unified libraries (UCS, UMI, UCI, UEI)
- Max 100 lines per adapter
- NO business logic in adapters

**Step 4: Update imports**

```bash
# Automated script (service-specific)
find . -name "*.py" -exec sed -i '' 's/from {service}.app.core/from {service}.engine/g' {} \;
```

**Step 5: Update tests**

- Update import paths
- Add adapter integration tests
- Verify all tests pass

**Step 6: Remove app/core/ after verification**

- Ensure all imports updated
- Ensure all tests pass
- Delete app/core/ directory

**Step 7: Run quality gates**

```bash
bash scripts/quality-gates.sh --no-fix
```

### Pilot: Complete instruments-service

**Current state:**

- ✅ Has engine/operations/instruments/orchestrator.py (1112 lines)
- ✅ Has adapters/ (2 files)
- ⚠️ Has app/core/ (2 compatibility wrappers)
- ❌ Needs CLI update (--operation + --mode)

**Actions:**

1. Update CLI to use `--operation` + `--mode` (Phase 2)
2. Test app/core/ wrappers can be removed safely
3. Remove app/core/ after verification
4. Run quality gates to verify

**Time estimate:** ~30 min

### Tier 1: Services with Partial Structure (2 repos)

**market-data-processing-service:**

- Has app/adapters/ already (good start)
- Move app/core/ to engine/
- Update adapters to be thin (delegate to libraries)

**strategy-service:**

- Has app/core/adapters/ (archive_backtest_adapter.py)
- Move app/core/ to engine/
- Refactor adapters to be thin

### Tier 3: All Other Services (10 repos)

Apply full refactoring pattern:

- Create engine/, adapters/
- Move app/core/ logic
- Extract I/O to thin adapters
- Update imports and tests

**Use parallel agents (4 agents, 2-3 services each)**

---

## Phase 4: Thin Adapter Pattern Enforcement

### Anti-Pattern Detection

**Check all adapters for violations:**

```bash
# Find adapters > 100 lines
find . -path "*/adapters/*.py" -exec wc -l {} \; | awk '$1 > 100 {print}'

# Find business logic in adapters (transformations, filtering)
rg "\.pct_change\(|\.dropna\(|\.apply\(" --type py --glob "**/adapters/*.py"

# Find direct cloud imports in adapters
rg "from google\.cloud|from boto3" --type py --glob "**/adapters/*.py"

# Find duplicate retry logic in adapters
rg "for.*retry|for.*attempt|while.*retry" --type py --glob "**/adapters/*.py"
```

### Remediation Pattern

**For thick adapters:**

```python
# Before (thick adapter - 150 lines)
class GCSDataSource:
    def read(self, path: str) -> pd.DataFrame:
        # ❌ Auth logic (50 lines)
        client = storage.Client(project=...)

        # ❌ Retry logic (30 lines)
        for attempt in range(3):
            try:
                data = blob.download()
                break
            except Exception:
                time.sleep(2 ** attempt)

        # ❌ Validation logic (40 lines)
        df = pd.read_parquet(...)
        if df.empty:
            raise ValueError("Empty")
        if "timestamp" not in df.columns:
            raise ValueError("Missing timestamp")

        # ❌ Transformation logic (30 lines)
        df['returns'] = df['close'].pct_change()
        df = df.dropna()

        return df

# After (thin adapter - 15 lines)
from unified_trading_services import get_storage_client

class GCSDataSource:
    def __init__(self, bucket: str):
        self.client = get_storage_client()  # UCS handles: auth, retry, errors
        self.bucket = bucket

    def read(self, path: str) -> pd.DataFrame:
        # Just delegate to UCS - validation/transformation in engine/
        return self.client.read_parquet(self.bucket, path)
```

### DRY Violations to Remove

**Known duplicates:**

1. **Instrument loading** (2 services):
  - `market-tick-data-handler/download_handler.py`: `_load_instruments_by_venue`
  - `market-data-processing-service/cloud_data_provider.py`: `_load_instruments_by_venue`
  - **Fix:** Use `InstrumentsDomainClient.get_instruments_for_date()` from UCS
2. **Error counting** (if any services still have local):
  - **Fix:** Use `ErrorWarningCounter` from UEI
3. **Memory tracking** (if services have custom logic):
  - **Fix:** Use UEI memory helpers
4. **Dependency checker** (each service has different implementation):
  - **Fix:** Standardize pattern (inherit from `BaseDependencyChecker` in UCS)

---

## Phase 5: Clean Code (Remove Orphaned/Deprecated)

### Known Items to Remove

**instruments-service:**

- ⚠️ `app/core/` (2 compatibility wrappers) — Remove after testing
- ✅ Corporate actions deprecated handlers — Already removed (confirmed by git log)

**unified-trading-services:**

- ✅ Cleaned recently (per git log: removed clients/, adapters/, bigquery/, empty dirs)

**Other services:**

- Check for empty directories (only `__pycache__`)
- Check for deprecated/ or archive/ directories with old code
- Check for unused imports in `__init__.py`

### Cleanup Checklist per Repo

```bash
# Find empty directories
find . -type d -empty -path "./{service_module}/*"

# Find directories with only __pycache__
find . -type d -not -path "*/__pycache__" -not -path "*/.venv*" \
  -exec sh -c '[ -d "$1/__pycache__" ] && [ -z "$(find "$1" -maxdepth 1 -type f -name "*.py")" ] && echo "$1"' _ {} \;

# Find files marked DEPRECATED or TODO REMOVE
rg "DEPRECATED|TODO.*REMOVE|LEGACY|SUPERSEDED" --type py -i

# Find unused __init__ exports
# (Manual check - compare exports vs actual imports)
```

---

## Phase 6: Documentation Updates

### Codex Updates

**1. CLI Standards** (NEW file)

- Create: `unified-trading-codex/06-coding-standards/cli-standards.md`
- Document: --operation + --mode pattern, backward compatibility, examples

**2. Service Structure Standards** (UPDATE existing)

- Update: `unified-trading-codex/04-architecture/batch-live-symmetry.md`
- Add: Current implementation status table
- Add: Migration guide reference

**3. Quality Gates Standards** (UPDATE existing)

- Update: `unified-trading-codex/06-coding-standards/quality-gates.md`
- Confirm: basedpyright is standard (not pyright)
- Confirm: E501 enforced (not ignored)

**4. Thin Adapter Pattern** (NEW or UPDATE)

- Create/update: `unified-trading-codex/06-coding-standards/thin-adapters-pattern.md`
- Document: Delegation to libraries, max 100 lines, no business logic

**5. Dependency Management** (UPDATE)

- Update: `unified-trading-codex/06-coding-standards/dependency-management.md`
- Add: UV package manager standard (never pip except bootstrap)

### Cursor Rules Updates

**1. Workspace .cursorrules** (UPDATE)

- Add CLI standards summary
- Add service structure enforcement
- Add thin adapter pattern summary

**2. New rules files** (CREATE)

- `.cursor/rules/cli-standards.mdc` — --operation + --mode pattern
- `.cursor/rules/service-structure-enforcement.mdc` — engine/adapters/cli structure
- `.cursor/rules/thin-adapters.mdc` — Delegation pattern

**3. Update existing rules** (UPDATE)

- `.cursor/rules/git-workflow.mdc` — Reference new standards
- `.cursor/rules/quality-gates-hardening.mdc` — Confirm basedpyright standard

---

## Phase 7: Create Quality Gate Bypass Audits

**ALL 17 repos that need hardening MUST have `QUALITY_GATE_BYPASS_AUDIT.md`**

**Template:** `instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md`

**Sections required:**

1. **Script Exclusions**
  - 1.1: Path/glob exclusions per check
  - 1.2: Import whitelist files
  - 1.3: grep -v pattern exclusions
2. **Inline Code Bypasses**
  - 2.1: `type: ignore[reportAny]` (list all with file:line:reason)
  - 2.2: `type: ignore[assignment]` (list all)
  - 2.3: `pyright: ignore` (list all)
  - 2.4: `noqa` (ruff bypasses)
3. **Ruff Config Bypasses**
  - Global ignores (E722, etc.)
  - Per-file-ignores
4. **Test Bypasses**
  - pytest.skip / @pytest.mark.skipif (list all with reason)
5. **Classification**
  - 7.1: Valid (acceptable — no action)
  - 7.2: Hardening flags (audit concerns — consider fixing)

**Implementation:**

- Use parallel agents (4 agents, 4-5 repos each)
- Generate audit from actual code (not template guesses)
- Document actual exceptions, not hypothetical

---

## Phase 8: Final Verification

### Verification Matrix


| Verification                 | Tool/Command                              | Pass Criteria                |
| ---------------------------- | ----------------------------------------- | ---------------------------- |
| **Local quality gates**      | `bash scripts/quality-gates.sh --no-fix`  | Exit 0 for all repos         |
| **Ruff version consistency** | `./scripts/check-ruff-versions.sh`        | All repos use 0.15.0         |
| **All quality gates**        | `./scripts/run-all-quality-gates.sh`      | All repos pass               |
| **CLI patterns**             | Manual check                              | All use --operation + --mode |
| **Structure patterns**       | Manual check                              | All have engine/adapters/cli |
| **Thin adapters**            | `find adapters/ -name "*.py" -exec wc -l` | All <100 lines               |
| **DRY violations**           | Grep for duplicates                       | Zero found                   |
| **GitHub Actions**           | CI status after merge                     | All green                    |
| **Cloud Build**              | Image tests after deploy                  | All green                    |


### Success Criteria

**Per Repo:**

- Uses `basedpyright>=1.20.0` (not old pyright)
- E501 NOT in ignore (enforced at 120 chars)
- Full ruff rules (`select = ["E", "F", "W", "I", "UP"]`)
- Uses `uv pip install` (never `pip install`)
- Coverage ≥35% (Python repos)
- Has `pyrightconfig.json` with `reportAny: "error"`
- Has `QUALITY_GATE_BYPASS_AUDIT.md`
- CLI uses `--operation` + `--mode` (not mixed)
- Has `engine/`, `adapters/`, `cli/` structure
- Adapters <100 lines each
- Passes local quality gates
- Passes GitHub Actions
- Passes Cloud Build

**Workspace-Wide:**

- All 17 repos hardened
- All repos pass quality gates
- Ruff 0.15.0 everywhere
- CLI standardized across all services
- Structure standardized across all services
- Zero DRY violations
- Zero orphaned code
- Codex updated with all patterns
- Cursor rules updated
- All tests pass

---

## Execution Strategy: 9 Phases, Parallel Within Phases

### Phase 1: Quality Gate Hardening (Parallel, 3 waves)

**Wave 1A: Libraries (2 repos, 2 agents in parallel) — 15 min**

- Agent 1: unified-domain-client (pyright → basedpyright)
- Agent 2: unified-trade-execution-interface (pyright → basedpyright)

**Wave 1B: P0 Critical (1 repo, 1 agent) — 5 min**

- Agent 1: ml-inference-service (pip → uv, BLOCKING)

**Wave 1C: Services (11 repos, 4 agents in parallel) — 20 min**

- Agent 1: market-tick-data-handler, market-data-processing-service, features-volatility-service
- Agent 2: ml-training-service, ml-inference-service (after P0), features-calendar-service
- Agent 3: features-delta-one-service, features-onchain-service, position-balance-monitor-service
- Agent 4: strategy-service, execution-services

**Wave 1D: UI Repos (3 repos, 3 agents in parallel) — 15 min**

- Agent 1: onboarding-ui (add workflow)
- Agent 2: execution-services/visualizer-ui (add script, workflow, strict mode)
- Agent 3: unified-trading-deployment-v3/ui (add script, workflow)

**Total Phase 1 time:** ~55 min (parallel execution)

### Phase 1D: Remove instruments-service app/core/ (Sequential) — 30 min

**CRITICAL:** Must happen BEFORE Phase 2 (CLI) and Phase 3 (structure) to establish clean baseline.

**WHY NOW:** instruments-service is the pilot. Complete it fully (remove compatibility wrappers) before rolling out patterns to other services.

**BLOCKING:** Phase 2 and Phase 3 should reference a CLEAN instruments-service without legacy code.

**Steps:**

1. **Search for all imports of app/core:**
```bash
cd instruments-service
rg "from instruments_service\.app\.core|import instruments_service\.app\.core" --type py
```

2. **Update imports to use engine/ directly:**
```bash
# Automated replacement
find . -name "*.py" -type f -exec sed -i '' \
  's/from instruments_service\.app\.core/from instruments_service.engine/g' {} \;
```

3. **Verify instrument_processing_service.py logic exists in engine/:**
```bash
# Check if InstrumentProcessingService is used anywhere
rg "InstrumentProcessingService" --type py
# If only in app/core, logic should be in engine/operations/
```

4. **Remove entire app/ directory:**
```bash
rm -rf instruments_service/app/
```

5. **Run quality gates:**
```bash
bash scripts/quality-gates.sh --no-fix
```

6. **Run all tests:**
```bash
pytest tests/ -v
```

7. **Verify no references to app/core:**
```bash
rg "app\.core" --type py
# Should return ZERO results
```

**Checkpoint:** instruments-service has NO app/ directory, all imports use engine/, quality gates pass

### Phase 2: CLI Standardization (CRITICAL - ALL 14 Services, Parallel, 4 agents) — 20 min

**REQUIRED:** ALL services MUST use `--operation` + `--mode` per codex. Currently ZERO services use this pattern.

**Agent assignments:**
- Agent 1: instruments-service, market-tick-data-handler, market-data-processing-service
- Agent 2: features-calendar, features-delta-one, features-volatility, features-onchain
- Agent 3: ml-training, ml-inference, strategy-service
- Agent 4: execution-services, risk-and-exposure, position-balance-monitor, pnl-attribution

**Each agent updates:**
1. `cli/parser.py` — Add `--operation` flag, change `--mode` to universal ["batch", "live"]
2. `cli/main.py` — Dispatch by operation, execute by mode
3. Add backward compatibility conversion (old --mode values auto-convert)
4. Test locally with both old and new CLI syntax
5. Update tests using old CLI syntax

**Checkpoint:** ALL 14 services use --operation + --mode, backward compatibility works, old syntax still works

### Phase 3: Service Structure Refactoring (Sequential by tier) — 2-3 hours

**Tier 1: Complete instruments-service (pilot) — 30 min**

- Remove app/core/ wrappers
- Verify engine/adapters/cli structure
- Run quality gates

**Tier 2: Services with partial structures (2 repos, 2 agents in parallel) — 45 min**

- Agent 1: market-data-processing-service
- Agent 2: strategy-service

**Tier 3: Remaining services (10 repos, 4 agents in parallel) — 90 min**

- Agent 1: market-tick-data-handler, features-calendar-service, features-delta-one-service
- Agent 2: features-volatility-service, features-onchain-service, ml-training-service
- Agent 3: ml-inference-service, risk-and-exposure-service, position-balance-monitor-service
- Agent 4: pnl-attribution-service, execution-services

**Checkpoint:** ALL 14 services have engine/adapters/cli structure, ZERO services have app/core/ remaining

### Phase 4: Thin Adapter Enforcement (Parallel, 4 agents) — 45 min

**Audit all adapters:**

- Find adapters >100 lines
- Find business logic in adapters
- Find direct cloud imports
- Find duplicate retry/error logic

**Fix per service (parallel):**

- Agent 1: Services 1-4
- Agent 2: Services 5-8
- Agent 3: Services 9-11
- Agent 4: Services 12-14

**Checkpoint:** All adapters <100 lines, delegate to libraries

### Phase 5: Clean Code (Parallel, 4 agents) — 30 min

**Remove per service:**

- Empty directories
- Orphaned code
- Deprecated implementations
- Unused imports

**Use parallel agents (4 agents, 3-4 services each)**

**Checkpoint:** Zero orphaned code, zero empty dirs

### Phase 6: Documentation (Sequential) — 45 min

**Codex updates:**

1. Create cli-standards.md
2. Update batch-live-symmetry.md
3. Create/update thin-adapters-pattern.md
4. Update quality-gates.md
5. Update dependency-management.md

**Cursor rules updates:**

1. Update .cursorrules
2. Create cli-standards.mdc
3. Create service-structure-enforcement.mdc
4. Create thin-adapters.mdc

**Checkpoint:** All standards documented

### Phase 7: Bypass Audits (Parallel, 4 agents) — 30 min

- Agent 1: Repos 1-5
- Agent 2: Repos 6-10
- Agent 3: Repos 11-14
- Agent 4: Repos 15-17

**Checkpoint:** All repos have comprehensive QUALITY_GATE_BYPASS_AUDIT.md

### Phase 8: Final Verification (Sequential) — 30 min

1. Verify ruff version consistency
2. Run all quality gates
3. Verify CLI patterns
4. Verify structure patterns
5. Verify thin adapters
6. Verify DRY violations removed

**Checkpoint:** All verification passes

**Total time estimate:** ~6-7 hours (with aggressive parallelization)

---

## Repository Groups for Parallel Execution

### Group A: Libraries (6 repos)

- unified-trading-services ✅ (done)
- unified-config-interface ✅ (done)
- unified-events-interface ✅ (done)
- unified-domain-client ⚠️ (needs pyright fix)
- unified-market-interface ⚠️ (needs coverage boost)
- unified-trade-execution-interface ⚠️ (needs pyright fix)
- execution-algo-library ✅ (done)

### Group B: Data Pipeline Services (3 repos)

- instruments-service ⚠️ (90% complete)
- market-tick-data-handler ❌ (needs hardening + structure)
- market-data-processing-service ❌ (needs hardening + structure)

### Group C: Features Services (4 repos)

- features-calendar-service ❌
- features-delta-one-service ❌
- features-volatility-service ❌
- features-onchain-service ❌

### Group D: ML Services (2 repos)

- ml-training-service ❌
- ml-inference-service ❌ (P0: pip→uv)

### Group E: Trading Services (4 repos)

- strategy-service ⚠️ (quality gates partial)
- execution-services ⚠️ (quality gates partial)
- risk-and-exposure-service ✅ (done)
- position-balance-monitor-service ⚠️ (verify)

### Group F: PnL/Alerting (2 repos)

- pnl-attribution-service ✅ (done)
- alerting-system ✅ (done)

### Group G: UI Repos (3 repos)

- onboarding-ui ❌ (needs workflow)
- execution-services/visualizer-ui ❌ (needs script + workflow + strict)
- unified-trading-deployment-v3/ui ❌ (needs script + workflow)

### Group H: Deployment (1 repo)

- unified-trading-deployment-v3 ✅ (done)

**Total:** 9 done ✅, 6 partial ⚠️, 11 needs work ❌

---

## Critical Dependencies and Merge Order

### Dependency Order (When Changing Libraries)

1. **Libraries first** (merge to main):
  - unified-domain-client, unified-trade-execution-interface (Phase 1A)
2. **Services second** (after library merges):
  - All services (Phase 1B-1C)

### Cross-Repo Coordination

**Parallel-safe operations** (zero conflict risk):

- Different repos in same phase
- Same repo, different files
- Documentation updates

**Sequential operations** (must wait):

- Library changes before service changes
- Quality gate fixes before structure refactoring
- Structure refactoring before cleanup

---

## Risk Mitigation


| Risk                                          | Impact | Mitigation                                                            |
| --------------------------------------------- | ------ | --------------------------------------------------------------------- |
| **Breaking changes from basedpyright**        | High   | basedpyright is stricter; fix type errors or document in bypass audit |
| **E501 reveals many long lines**              | Medium | Run ruff format first (fixes many), manually break remaining          |
| **Structure refactoring breaks imports**      | High   | Update imports systematically, test after each service                |
| **Thin adapter pattern requires logic moves** | Medium | Move business logic to engine/, keep adapters pure                    |
| **CLI changes break deployments**             | High   | Backward compatibility via auto-conversion, test both patterns        |
| **Low coverage blocks development**           | High   | Add tests in parallel with hardening, use synthetic fixtures          |
| **Merge conflicts (30+ repos)**               | Medium | Use parallel agents for different repos, merge dependencies first     |


---

## Detailed Implementation (Per Phase)

### Phase 1A: Fix 2 Libraries (pyright → basedpyright)

**Files to change per library:**

1. `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "basedpyright>=1.20.0,<2.0.0",  # Change from pyright>=1.1.390
]
```

1. `scripts/quality-gates.sh`:

```bash
# Replace pyright detection block (lines 80-116 for UDS, 249-282 for UOI)
if command -v basedpyright &> /dev/null; then
    TYPE_CHECKER="basedpyright"
elif python3 -c "import basedpyright" &> /dev/null; then
    TYPE_CHECKER="python3 -m basedpyright"
else
    uv pip install "basedpyright>=1.20.0" --quiet
    TYPE_CHECKER="basedpyright"
fi

# Run (blocking)
$TYPE_CHECKER unified_domain_client/ --level warning
```

1. `.github/workflows/quality-gates.yml`:

```yaml
- name: Install dependencies
  run: |
    uv pip install --system basedpyright>=1.20.0
    uv pip install --system -e ".[dev]"

- name: Type check (basedpyright)
  run: basedpyright unified_domain_client/ --level warning
```

**Test locally:**

```bash
cd unified-domain-client
bash scripts/quality-gates.sh --no-fix
```

**Commit:**

```bash
bash scripts/quickmerge.sh "Harden quality gates: use basedpyright instead of pyright"
```

### Phase 1B: Harden 11 Service Quality Gates

**Step 1: ml-inference-service P0 fix**

Replace `pip install ruff` with `uv pip install ruff==0.15.0` in lines 205, 229 of quality-gates.sh.

**Step 2: Category B2 (5 repos with E501) - Parallel**

For each repo:

1. Remove E501 from ignore:

```toml
# pyproject.toml - BEFORE
[tool.ruff.lint]
ignore = ["E501"]  # Line too long

# AFTER
[tool.ruff.lint]
ignore = [
    # E501 removed - enforced at 120 chars
]
```

1. Update type checker to basedpyright (same pattern as Phase 1A)
2. Run quality gates and fix violations:

```bash
bash scripts/quality-gates.sh  # Auto-fix
# Fix any remaining E501 violations manually
bash scripts/quality-gates.sh --no-fix  # Verify
```

**Step 3: Category B3 (3 repos with minimal ruff) - Parallel**

1. Expand ruff rules:

```toml
# BEFORE
select = ["I", "UP"]

# AFTER
select = ["E", "F", "W", "I", "UP"]
```

1. Update type checker to basedpyright
2. Run quality gates and fix NEW violations from expanded rules

**Step 4: Category B4 (2 repos with informational pyright) - Parallel**

1. Make pyright blocking:

```bash
# BEFORE
pyright strategy_service/ --level warning || echo "Pyright informational only"

# AFTER
pyright strategy_service/ --level warning
if [ $? -ne 0 ]; then
    PYRIGHT_STATUS=1
fi
```

1. Fix execution-services: `pip install ruff` → `uv pip install ruff==0.15.0`

**Step 5: Add tests to low-coverage libraries (if needed)**

- unified-domain-client: 14% → 35%
- unified-market-interface: 22% → 35%

### Phase 1C: Harden 3 UI Quality Gates

**Pattern for standalone UIs (onboarding-ui):**

Copy `.github/workflows/quality-gates.yml` from `backtest-ui`.

**Pattern for embedded UIs (execution-services/visualizer-ui, UTDv2/ui):**

1. Create `scripts/quality-gates-ui.sh`:

```bash
#!/bin/bash
set -e

echo "======================================================================"
echo "UI QUALITY GATES (TypeScript)"
echo "======================================================================"

cd visualizer-ui  # Or cd ui for UTDv2

npm run type-check || exit 1
npm run lint || exit 1
npm run build || exit 1

echo "✅ All UI quality gates passed"
```

1. Add to main quality-gates.sh or create workflow step
2. Fix `tsconfig.json` strict mode (visualizer-ui only):

```json
{
  "compilerOptions": {
    "strict": true  // Change from false
  }
}
```

---

## Phase 2: CLI Standardization

### Implementation per Service

**1. Update cli/parser.py:**

```python
def parse_arguments():
    parser = argparse.ArgumentParser()

    # Add --operation
    parser.add_argument(
        "--operation",
        required=True,
        choices=["instrument", "aggregate", "corporate_actions"],  # Service-specific
        help="Operation to perform"
    )

    # Update --mode to universal values
    parser.add_argument(
        "--mode",
        required=True,
        choices=["batch", "live"],
        help="Execution mode"
    )

    args = parser.parse_args()

    # Backward compatibility: auto-convert old values
    old_modes = {
        "instruments": ("instrument", "batch"),
        "aggregate": ("aggregate", "batch"),
        "corporate_actions": ("corporate_actions", "batch"),
        "corporate_actions_production": ("corporate_actions", "batch"),
        "download": ("fetch", "batch"),  # market-tick-data-handler
        # Add service-specific mappings
    }

    if args.mode in old_modes:
        logger.warning(f"⚠️ --mode {args.mode} is deprecated")
        args.operation, args.mode = old_modes[args.mode]

    return args
```

**2. Update cli/main.py:**

```python
def main():
    args = parse_arguments()

    # Dispatch by operation (not mode)
    if args.operation == "instrument":
        handler = InstrumentHandler(config, mode=args.mode)
    elif args.operation == "aggregate":
        handler = AggregateHandler(config, mode=args.mode)
    # ... more operations

    # Execute by mode
    if args.mode == "batch":
        result = handler.run_batch(start_date=args.start_date, end_date=args.end_date)
    elif args.mode == "live":
        result = handler.run_live(interval=args.interval)
```

**3. Update deployment configs:**

UTDv3 has ~40 files referencing old CLI patterns. Update in parallel with service changes.

---

## Phase 3: Service Structure Refactoring

### Pilot: Complete instruments-service

**Current state:**

- ✅ Has `engine/operations/instruments/orchestrator.py` (1112 lines)
- ✅ Has `adapters/` (data_source_adapter.py 3854 bytes, storage_adapter.py 4078 bytes)
- ⚠️ Has `app/core/` (2 files: instruments_service.py 1468 bytes, instrument_processing_service.py 11564 bytes)

**app/core/ analysis:**

- `instruments_service.py`: 50 lines, delegation wrapper (DEPRECATED marker)
- `instrument_processing_service.py`: ~300 lines, still has logic

**Actions:**

1. Review `instrument_processing_service.py` — is logic duplicated in engine/operations/?
2. If duplicated: Remove app/core/ entirely
3. If unique: Move remaining logic to engine/operations/
4. Update any remaining imports to use engine/ directly
5. Test: Run quality gates and all tests
6. Remove app/core/ directory after verification

**Time:** ~30 min

### Tier 1: market-data-processing-service (has app/adapters/)

**Current:** Has `app/core/` and `app/adapters/`

**Actions:**

1. Create `engine/` and move `app/core/` logic
2. Refactor `app/adapters/` to be thin (currently may have business logic)
3. Move adapters to top-level `adapters/`
4. Remove `app/` directory
5. Update imports

**Time:** ~45 min

### Tier 2: All Other Services (10 repos)

**Current:** All have `app/core/` or similar, no `engine/`, no `adapters/`

**Actions (per service):**

1. Create `engine/`, `adapters/` directories
2. Move `app/core/` business logic to `engine/`
3. Extract I/O to thin `adapters/` (delegate to libraries)
4. Update imports (automated script + manual fixes)
5. Update tests
6. Remove `app/core/`
7. Run quality gates

**Time:** ~45 min per service × 10 services ÷ 4 agents = ~2 hours

---

## Phase 4: Thin Adapter Enforcement

### Adapter Audit

**Criteria for thin adapter:**

- ✅ <100 lines
- ✅ Delegates to unified libraries (UCS, UMI, UCI, UEI)
- ✅ NO business logic (no transformations, filtering, calculations)
- ✅ NO retry logic (use UCS decorators)
- ✅ NO direct cloud imports (use UCS abstractions)

### Violations to Fix

**Example violations:**

```python
# ❌ THICK adapter (150 lines, has business logic)
class GCSDataSource:
    def read(self, path: str) -> pd.DataFrame:
        # Auth (50 lines) - should use UCS
        client = storage.Client(...)

        # Retry (30 lines) - should use UCS
        for attempt in range(3): ...

        # Validation (40 lines) - should be in engine/
        if df.empty: raise ValueError(...)

        # Transformation (30 lines) - should be in engine/
        df['returns'] = df['close'].pct_change()

        return df

# ✅ THIN adapter (15 lines, delegates)
from unified_trading_services import get_storage_client

class GCSDataSource:
    def __init__(self, bucket: str):
        self.client = get_storage_client()
        self.bucket = bucket

    def read(self, path: str) -> pd.DataFrame:
        return self.client.read_parquet(self.bucket, path)
```

### Remediation Steps

**For each thick adapter:**

1. Move business logic to `engine/`
2. Move validation to `engine/validation/`
3. Replace auth/retry with UCS primitives
4. Remove transformations (move to engine/)
5. Verify adapter is <100 lines
6. Run quality gates

---

## Phase 5: Clean Code

### Orphaned Code Detection

**Script to find:**

```bash
#!/bin/bash
# Find empty directories
find . -type d -empty -path "./*_service/*" -o -path "./*-interface/*"

# Find directories with only __pycache__
find . -type d -not -path "*/__pycache__" -not -path "*/.venv*" \
  -exec sh -c '[ -d "$1/__pycache__" ] && [ -z "$(find "$1" -maxdepth 1 -type f -name "*.py")" ] && echo "$1"' _ {} \;

# Find DEPRECATED markers
rg "DEPRECATED|TODO.*REMOVE|LEGACY|SUPERSEDED" --type py -i

# Find unused imports in __init__.py
# (Manual review needed)
```

### Known Cleanup Items

**instruments-service:**

- `app/core/` (2 files) — Remove after verifying engine/ is complete

**All services:**

- Check for empty directories
- Check for deprecated/ folders with old code
- Check for archive/ folders with unused code
- Check for orphaned test files (test_**old.py, test**_backup.py)

---

## Phase 6: Documentation Updates

### Codex Updates (6 files)

**1. Create: `06-coding-standards/cli-standards.md`**

Contents:

- Universal pattern: --operation + --mode
- Flag definitions
- Mode behavior (batch vs live)
- Implementation pattern
- Backward compatibility approach
- Service-specific operation mappings
- Examples

**2. Update: `04-architecture/batch-live-symmetry.md`**

Add sections:

- Current implementation status (table showing which services have engine/adapters/)
- Migration guide reference
- CLI standards reference

**3. Create/Update: `06-coding-standards/thin-adapters-pattern.md`**

Contents:

- Adapter responsibilities (delegation only)
- Max 100 lines guideline
- Library delegation matrix
- Good vs bad adapter examples
- Quality gate enforcement

**4. Update: `06-coding-standards/quality-gates.md`**

Confirm:

- basedpyright is standard (not pyright)
- E501 enforced (not ignored)
- UV package manager standard

**5. Update: `06-coding-standards/dependency-management.md`**

Add:

- UV package manager section
- Never pip except bootstrap

**6. Update: `06-coding-standards/README.md`**

Add to table of contents:

- CLI standards
- Service structure standards
- Thin adapters pattern

### Cursor Rules Updates (4 files)

**1. Update: `.cursorrules` (workspace root)**

Add sections:

- CLI standards summary (reference codex)
- Service structure enforcement (reference codex)
- Thin adapter pattern (reference codex)
- Quality gate hardening summary

**2. Create: `.cursor/rules/cli-standards.mdc`**

Summarize codex cli-standards.md with enforcement rules.

**3. Create: `.cursor/rules/service-structure-enforcement.mdc`**

Summarize engine/adapters/cli structure requirements.

**4. Create: `.cursor/rules/thin-adapters.mdc`**

Summarize delegation pattern, max 100 lines, no business logic.

---

## Phase 7: Create Bypass Audits (17 Repos)

### Repos Needing QUALITY_GATE_BYPASS_AUDIT.md

**Services (11):**

1. market-tick-data-handler
2. market-data-processing-service
3. features-calendar-service
4. features-delta-one-service
5. features-volatility-service
6. features-onchain-service
7. ml-training-service
8. ml-inference-service
9. strategy-service
10. execution-services
11. position-balance-monitor-service

**Libraries (2):**

1. unified-domain-client
2. unified-market-interface

**UIs (3):**

1. onboarding-ui
2. execution-services/visualizer-ui
3. unified-trading-deployment-v3/ui

**Deployment (1):**

1. (UTDv3 already has one if needed)

### Audit Generation Process

**Don't copy template blindly.** Generate from actual code:

1. **Run quality gates** to see what bypasses are actually present
2. **Search for inline bypasses:**

```bash
rg "# type: ignore|# noqa|# pyright:" --type py
rg "pytest.skip|@pytest.mark.skip" tests/
```

1. **Check ruff config** for per-file-ignores
2. **Check quality-gates.sh** for path exclusions
3. **Document in audit file** with file:line:reason
4. **Classify** as valid (7.1) or hardening flag (7.2)

### Parallel Execution

- Agent 1: Repos 1-5
- Agent 2: Repos 6-10
- Agent 3: Repos 11-14
- Agent 4: Repos 15-17

**Time:** ~30 min total (parallel)

---

## Phase 8: Final Verification

### Verification Checklist

**1. Ruff version consistency**

```bash
cd unified-trading-deployment-v3
./scripts/check-ruff-versions.sh
# All repos should show ruff==0.15.0
```

**2. All quality gates pass**

```bash
./scripts/run-all-quality-gates.sh --sequential
# Exit 0, all repos green
```

**3. CLI patterns verified**

```bash
# All services should have --operation and --mode
rg "add_argument.*--operation" --type py */cli/parser.py
# Should return 14 results (one per service)
```

**4. Structure patterns verified**

```bash
# All services should have engine/, adapters/, cli/
for service in *-service/; do
    ls -d ${service}*/engine/ ${service}*/adapters/ ${service}*/cli/ 2>/dev/null || echo "Missing: $service"
done
```

**5. Thin adapters verified**

```bash
# No adapter should exceed 100 lines
find . -path "*/adapters/*.py" ! -path "*/.venv/*" -exec sh -c '
    lines=$(wc -l < "$1")
    if [ $lines -gt 100 ]; then
        echo "❌ $1: $lines lines (max 100)"
    fi
' _ {} \;
```

**6. DRY violations verified**

```bash
# Should find ZERO _load_instruments_by_venue in services
rg "_load_instruments_by_venue" --type py \
    --glob "!unified-trading-services/**" \
    --glob "!unified-domain-client/**"

# Should find ZERO service-specific error counters
rg "class.*ErrorCounter|class.*WarningCounter" --type py \
    --glob "!unified-events-interface/**"
```

**7. GitHub Actions pass**

After quickmerge, agent automatically starts ci-watcher to monitor CI.

**8. Cloud Build pass**

After merge, verify Cloud Build runs successfully for all changed repos.

---

## Known Exceptions (Apply to All Repos)

### Valid Exceptions (No Action Required)

1. **Path exclusions:** tests/, scripts/, examples/ exempt from production rules
2. **Import whitelist:** adapter_loader.py, **init**.py (lazy loading), TYPE_CHECKING blocks
3. **dict[str, Any]:** Allowed for non-finite nested dicts with `# type: ignore[reportAny]`
4. **E722 in scripts/:** Bare except allowed per codex
5. **pytest.skip:** GCP creds, API keys, environment-dependent tests
6. **file size: scripts/:** Exempt per codex

### Hardening Flags (Consider Fixing)

1. **type: ignore[reportAny]:** Replace with Protocol, TypedDict where feasible
2. **Circular imports:** Refactor to reduce (dependency injection, interfaces)
3. **Broad except Exception:** Use @handle_api_errors or specific exceptions
4. **Lazy imports:** Move to top or document in bypass audit

---

## Integration with Pending Work

### UCS Restructure Plan

**From:** `.cursor/plans/fix_7_unified_libraries_quality_gates.plan.md`

**Pending work:**

- Move domain clients to UDS
- Remove DataSourceMapping from UCS
- Remove UnifiedCloudService legacy class
- Move ML module to unified-ml-interface

**Coordination:** Phase 1A (library hardening) can proceed independently. UCS restructure is separate work (not blocking).

### Service Structure Plan

**From:** `.cursor/plans/service_structure_standardization_4a4b3ff3.plan.md`

**Completed:**

- ✅ ErrorWarningCounter in UEI
- ✅ Memory helpers in UEI
- ✅ UCI overhaul complete
- ✅ instruments-service 90% refactored

**Pending:**

- CLI standardization (covered in this plan Phase 2)
- Complete structure refactoring (covered in this plan Phase 3)
- UTDv3 updates (covered in this plan Phase 2)

### API Keys Plan

**From:** `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md`

**Completed:**

- ✅ instruments-service uses get_secret_client
- ✅ Aggregation operation added

**Pending:**

- market-tick-data-handler migration to InstrumentsDomainClient (covered in Phase 4)
- market-data-processing-service migration (covered in Phase 4)

---

## Success Metrics

### Code Quality Metrics


| Metric                    | Current            | Target | Verification                            |
| ------------------------- | ------------------ | ------ | --------------------------------------- |
| Repos with basedpyright   | 11/26 Python repos | 26/26  | Check quality-gates.sh                  |
| E501 enforced             | 11/26              | 26/26  | Check pyproject.toml ignore             |
| Coverage ≥35%             | 24/26              | 26/26  | Run check-all-coverage.sh               |
| Services with engine/     | 1/14               | 14/14  | ls *-service/*/engine/                  |
| Services with adapters/   | 2/14               | 14/14  | ls *-service/*/adapters/                |
| Adapters <100 lines       | Unknown            | 100%   | find adapters/ -name "*.py" -exec wc -l |
| Services with --operation | 0/14               | 14/14  | rg "add_argument.*--operation"          |
| DRY violations            | Unknown            | 0      | Manual audit                            |


### Process Metrics


| Phase                  | Repos Affected | Parallel Agents            | Estimated Time |
| ---------------------- | -------------- | -------------------------- | -------------- |
| Phase 1: Quality Gates | 17             | 4 agents/wave, 4 waves     | ~55 min        |
| Phase 2: CLI           | 14             | 4 agents                   | ~20 min        |
| Phase 3: Structure     | 14             | Sequential + 4 agents      | ~3 hours       |
| Phase 4: Thin Adapters | 14             | 4 agents                   | ~45 min        |
| Phase 5: Clean Code    | 14             | 4 agents                   | ~30 min        |
| Phase 6: Documentation | Codex + rules  | Sequential                 | ~45 min        |
| Phase 7: Bypass Audits | 17             | 4 agents                   | ~30 min        |
| Phase 8: Verification  | All            | Sequential                 | ~30 min        |
| **Total**              | 26+ repos      | Aggressive parallelization | **~7 hours**   |


---

## Critical Success Factors

### 1. Quality Gates Must Pass (BLOCKING)

Every repo must pass `bash scripts/quality-gates.sh --no-fix` before declaring phase complete.

**No shortcuts:**

- ❌ Don't skip tests
- ❌ Don't add `|| true`
- ❌ Don't disable checks
- ✅ Fix root causes
- ✅ Document exceptions in bypass audit

### 2. Incremental Testing

After each service refactoring:

1. Run quality gates locally
2. Run all tests
3. Commit and create PR
4. Monitor CI (ci-watcher auto-starts)
5. Fix CI failures before next service

### 3. Parallel Execution Where Safe

**Parallel-safe:**

- Different repos (zero conflict risk)
- Same repo, different files
- Quality gate fixes (independent)

**Sequential-required:**

- Library changes before services
- Structure refactoring (per service)
- Testing after refactoring

### 4. Documentation Before Implementation

Update codex and cursor rules BEFORE rolling out patterns to services. Services should reference codex, not reinvent.

---

## Related Documentation

**Plans:**

- `[.cursor/plans/fix_7_unified_libraries_quality_gates.plan.md](.cursor/plans/fix_7_unified_libraries_quality_gates.plan.md)` — Library restructure (UCS, UDS, UMI)
- `[.cursor/plans/service_structure_standardization_4a4b3ff3.plan.md](.cursor/plans/service_structure_standardization_4a4b3ff3.plan.md)` — CLI + structure work
- `[.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md](.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md)` — API keys + aggregation
- `[.cursor/plans/INSTRUMENTS_SERVICE_COMPLETE_REFACTORING.md](.cursor/plans/INSTRUMENTS_SERVICE_COMPLETE_REFACTORING.md)` — File-by-file mapping

**Codex:**

- `[unified-trading-codex/06-coding-standards/quality-gates.md](unified-trading-codex/06-coding-standards/quality-gates.md)`
- `[unified-trading-codex/04-architecture/batch-live-symmetry.md](unified-trading-codex/04-architecture/batch-live-symmetry.md)`
- `[unified-trading-codex/06-coding-standards/audit-remediation-guide.md](unified-trading-codex/06-coding-standards/audit-remediation-guide.md)`

**Cursor Rules:**

- `[.cursor/rules/quality-gates-hardening.mdc](.cursor/rules/quality-gates-hardening.mdc)`
- `[.cursor/rules/hardening-standards.mdc](.cursor/rules/hardening-standards.mdc)`
- `[.cursor/rules/strict-type-checking.mdc](.cursor/rules/strict-type-checking.mdc)`
- `[.cursor/rules/no-empty-fallbacks.mdc](.cursor/rules/no-empty-fallbacks.mdc)`

**Examples:**

- `[instruments-service/](instruments-service/)` — 90% complete pilot
- `[instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md](instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md)` — Bypass audit template
- `[backtest-ui/scripts/quality-gates.sh](backtest-ui/scripts/quality-gates.sh)` — UI quality gates reference

---

## Summary

This comprehensive plan addresses:

✅ **Quality gate hardening** — 17 repos need basedpyright, E501, codex checks
✅ **CLI standardization** — 14 services need --operation + --mode
✅ **Structure standardization** — 13 services need engine/adapters/cli
✅ **Thin adapter pattern** — Delegate to libraries, <100 lines, no business logic
✅ **DRY violation removal** — Eliminate duplicated instrument loading, error tracking, etc.
✅ **Clean code** — Remove orphaned, deprecated, superseded code
✅ **Documentation** — Update codex and cursor rules with all patterns
✅ **Bypass audits** — Document all exceptions comprehensively

**Built on:**

- 9 hardened repos (instruments-service + 6 libraries + 2 services)
- instruments-service 90% refactored (engine/adapters exist, CLI needs update)
- UCI overhaul complete (ConfigStore ready)
- UEI observability complete (ErrorWarningCounter ready)

**Total effort:** ~7 hours with aggressive parallelization across 26+ repos.
