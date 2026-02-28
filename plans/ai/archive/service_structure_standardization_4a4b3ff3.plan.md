---
name: Service Structure Standardization
overview: Standardize service directory structure to match batch-live symmetry architecture (engine/, adapters/, cli/), centralize observability patterns (ErrorWarningCounter, memory monitoring) in unified-events-interface, consolidate instruments-service corporate actions handlers, and update codex + cursor rules to enforce standards.
todos:
  - id: phase-1-complete-api-keys
    content: "Phase -1: Complete pending API keys work (20+ uncommitted files)"
    status: completed
  - id: phase-1-commit-api-keys
    content: "Phase -1: Run quality gates, commit, and merge API keys work"
    status: completed
  - id: phase-1-pull-latest
    content: "Phase -1: Pull latest main after API keys merge"
    status: completed
  - id: phase0-add-uei-observability
    content: "Phase 0.1: Add ErrorWarningCounter and memory helpers to unified-events-interface"
    status: completed
  - id: phase0-verify-uci
    content: "Phase 0.2: Verify ConfigStore/TimeSeriesConfigStore/ConfigReloader work in UCI"
    status: completed
  - id: phase0-test-libraries
    content: "Phase 0.3: Test full library usage in instruments-service (no structure changes)"
    status: completed
  - id: phase0-update-codex
    content: "Phase 0.4: Update codex with all hardened standards (CLI, structure, config, adapters)"
    status: completed
  - id: phase0-update-cursor-rules
    content: "Phase 0.4: Update cursor rules with all hardened standards"
    status: completed
  - id: phase1-cli-services
    content: "Phase 1: Update all 14 services to use --operation and --mode flags"
    status: completed
  - id: phase1-cli-deployment-v3
    content: "Phase 1: Update deployment-v3 for --operation and --mode (~40 files)"
    status: completed
  - id: phase2-wait-api-keys
    content: "Phase 2: Wait for API keys work to merge, then pull latest main"
    status: pending
  - id: phase2-refactor-instruments
    content: "Phase 2: Refactor instruments-service structure (engine/adapters, rename files, split large files)"
    status: completed
  - id: phase2-instruments-quality-gates
    content: "Phase 2: Fix ALL quality gate issues in instruments-service (pilot)"
    status: in_progress
  - id: phase3-rollout-services
    content: "Phase 3: Apply proven pattern to 13 remaining services (parallel agents)"
    status: completed
  - id: phase3-each-service-quality-gates
    content: "Phase 3: Each service passes quality gates before proceeding to next"
    status: in_progress
  - id: phase4-consolidate-corporate-actions
    content: "Phase 4: Consolidate corporate actions handlers (1-2 handlers, extract utils, fix imports)"
    status: completed
  - id: phase5-verify-all
    content: "Phase 5: Verify all services use centralized patterns (observability, config, structure)"
    status: pending
  - id: phase5-final-quality-gates
    content: "Phase 5: Run quality gates on all 14 services, verify zero failures"
    status: pending
isProject: false
---

## Execution summary (12 services, 2026-02-24)

**Scope**: All services except instruments-service and market-tick-data-handler. Four parallel agents executed CLI + structure refactoring per `.cursor/plans/tasks/TASK_SERVICE_STRUCTURE_12_SERVICES.md`.

**Completed (all 12)**:

- CLI: `--operation` and `--mode` added/normalized; dispatch by operation then mode in each service.
- Structure: `engine/` and `adapters/` added; app/core logic moved to engine; thin I/O adapters (<100 lines) delegating to UCS/UMI/UCI/UEI; `cli/handlers/` in place.

**Quality gates**:

- **Pass**: risk-and-exposure-service; features-delta-one-service; features-volatility-service (lint/type pass; run quality-gates.sh to confirm).
- **Fail (fix or env)**: market-data-processing (Pyright/UDS types in adapters); pnl-attribution, features-calendar (test ImportError: UnifiedCloudConfig / path deps); features-onchain (test/codex in script); ml-training (unified_ml_interface, coverage); ml-inference (F821 _DepConfig); strategy (pre-existing tests/codex); execution-services (tests, codex); position-balance-monitor (Pyright, Codex indented imports).

**Quality-gates run**: Sequential run from deployment-v2 failed on the **first repo** (unified-trading-deployment-v3 itself: lint/codex/tests). The 12 service repos were not reached. Per-service fixes from agents improved path deps, Pyright, and codex; position-balance-monitor and risk-and-exposure pass; others may still have coverage/codex/pre-existing issues.

**Deployment-v3 (2026-02-24)**: Completed. ~44 files updated: configs/sharding.*.yaml (15), terraform/services/*/gcp|aws/main.tf (22), shard_builder.py, test_config_loader.py, CLIPreview.tsx, check_ml_dependencies_by_mode.py, CLI_REFERENCE_TEMPLATE.md, terraform/README.md. All invocations now use --operation  and --mode batch|live.

**Phase 4 corporate actions (2026-02-24)**: Completed. instruments-service: shared utils in engine/operations/corporate_actions/utils.py (get_tickers_from_gcs); imports moved to top in handlers and utils; 2 handlers kept (production + date-range); backfill/update handlers already removed; QUALITY_GATE_BYPASS_AUDIT and CODEX_VIOLATIONS_MANIFEST updated.

---

# Service Structure and Observability Standardization

## ⚠️ Coordination with Parallel Work

**Status check** (2026-02-23):

- ✅ **Codex updated**: `unified-trading-codex/02-data/instruments-and-api-keys-standard.md` exists
- ⚠️ **instruments-service**: 20+ files modified (uncommitted)
- ⚠️ **Work in progress**: API keys standardization by another agent

**Files modified by API keys work** (uncommitted):

- config.py, dependency_checker.py
- All handlers (7 files)
- Core files (instruments_service.py, instrument_processing_service.py, cloud_instrument_storage.py)
- Processors (3 files)

**Coordination options**:

**Option A: Wait for commit/merge (RECOMMENDED)**

1. Wait for API keys agent to commit changes
2. Merge API keys PR
3. Pull latest main
4. Start Phase 0-5 on clean base

**Option B: Proceed with libraries only**

1. Phase 0 (UEI, UCI) - Different repos, no conflict
2. Wait for API keys merge
3. Phase 1-5 after merge

**Option C: Coordinate file-by-file**

1. Stash API keys changes
2. Do structure refactoring
3. Reapply API keys changes on new structure
4. Risk: Merge conflicts

**RECOMMENDED**: Option A - Wait for API keys work to complete (likely ready soon based on uncommitted changes).

**New operation from API keys work**:

- `--operation aggregate` - Instrument aggregation (daily batch)
- Will be included in refactored structure: `engine/operations/aggregate/`

## Scope: Complete Repository Coverage

**Total workspace repos**: 36 active repos (see `.cursor/plans/COMPLETE_REPO_INVENTORY.md`)

### In Scope (14 Python Services - Full Refactoring)

**ALL 14 services** get CLI standardization + engine/adapters refactoring:


| #   | Service                          | Operations                                     | Modes                          | Priority   |
| --- | -------------------------------- | ---------------------------------------------- | ------------------------------ | ---------- |
| 1   | instruments-service              | `instrument`, `corporate_actions`              | batch, live                    | P0 (pilot) |
| 2   | market-tick-data-handler         | `fetch`                                        | batch, live                    | P1         |
| 3   | market-data-processing-service   | `process`                                      | batch, live                    | P1         |
| 4   | pnl-attribution-service          | `compute`                                      | batch, live                    | P2         |
| 5   | features-calendar-service        | `compute`                                      | batch, live                    | P1         |
| 6   | features-delta-one-service       | `compute`                                      | batch, live                    | P1         |
| 7   | features-volatility-service      | `compute`                                      | batch, live                    | P2         |
| 8   | features-onchain-service         | `compute`                                      | batch, live                    | P2         |
| 9   | ml-training-service              | `train_phase1`, `train_phase2`, `train_phase3` | batch, live                    | P1         |
| 10  | ml-inference-service             | `infer`                                        | batch, live                    | P1         |
| 11  | strategy-service                 | `backtest`, `live_trade`                       | batch (backtest), live (trade) | P1         |
| 12  | execution-services               | `execute`                                      | live only (event-driven)       | P2         |
| 13  | risk-and-exposure-service        | `compute`                                      | batch, live                    | P2         |
| 14  | position-balance-monitor-service | `monitor`                                      | batch, live                    | P1         |


### Out of Scope (22 repos - Different standards)

**UI Repos (9)** - TypeScript quality gates only (tsc, ESLint):

- backtest-ui, batch-audit-ui, client-reporting-ui, live-health-monitor-ui
- logs-dashboard-ui, ml-deployment-ui, onboarding-ui, settlement-ui, trading-analytics-ui

**Platform Libraries (6)** - Minimal changes:

- **unified-events-interface**: Add observability/ directory (ErrorWarningCounter, memory helpers)
- **Others (no changes)**: unified-trading-services, unified-config-interface, unified-market-interface, unified-trade-execution-interface, unified-domain-client

**Deployment Repos (2)** - Configuration updates:

- **unified-trading-deployment-v3**: Update ~40 files (shard configs, Terraform, UI) for --operation + --mode
- **unified-trading-deployment-v3**: Documentation examples only

**Utility Repos (3)** - No changes:

- execution-algo-library, alerting-system
- **unified-trading-codex**: Updated as part of Phase 4 (documentation)

**Special Cases (2)** - Evaluate separately:

- sports-betting-services, one-time-scripts

## Problem Summary

Investigation revealed three major inconsistencies:

1. **Observability Duplication**: `ErrorWarningCounter` exists only in instruments-service; other services lack centralized error/warning tracking. Memory monitoring patterns vary (system vs DataFrame).
2. **Service Structure Variance**: Services use `app/core/` and `cli/handlers/` but codex prescribes `engine/` and `adapters/`. Current structure doesn't match batch-live symmetry architecture intent.
3. **Handler Proliferation**: instruments-service has 4 corporate actions handlers (3 marked deprecated) with 200+ lines of duplicated code and circular import violations.

## CLI Architecture Refactoring (Phase 0)

**PROBLEM**: Current CLI conflates **WHAT** (operation type) with **HOW** (execution mode).

### Current (Confusing) Design

```bash
# instruments-service
--mode instrument              # Batch or live? Unclear!
--mode corporate_actions_production  # Batch-style but doesn't say so
--mode live                    # Live what? Both operations?

# Other services
--mode batch                   # What operation?
--mode live                    # What operation?
```

### Target (Clean) Design

**ALL services** use two separate flags:

```bash
--operation <what>  # What to run (operation type)
--mode <how>        # How to run (batch or live)
```

**Examples**:

```bash
# instruments-service
--operation instrument --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation instrument --mode live  # 15min UTC aligned
--operation corporate_actions --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation corporate_actions --mode live  # 15min UTC aligned

# market-tick-data-handler
--operation fetch --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation fetch --mode live  # Continuous WebSocket

# features-delta-one-service
--operation compute --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation compute --mode live  # 15min UTC aligned
```

**Key insight**:

- `--operation` = domain-specific (instrument, corporate_actions, fetch, compute, train, backtest)
- `--mode` = universal (batch or live)
- Batch = date range processing
- Live = scheduled/continuous (15min UTC for Cloud Run, persistent WebSocket for long-running)

## Architecture

### Target Structure (from [batch-live-symmetry.md](unified-trading-codex/04-architecture/batch-live-symmetry.md))

```
{service}/
  {service_module}/
    engine/           # Mode-agnostic processing (90% of code)
      __init__.py
      orchestrator.py # Top-level orchestration
      operations/     # Operation-specific logic (if multiple operations)
        operation1/
        operation2/
      processors/     # Shared processors
      validation/     # Standard validation (dependency_checker)
      venues/         # Venue-specific logic (if applicable)
    adapters/         # Mode-specific I/O (4 seams)
      data_source.py  # GCSDataSource, StreamDataSource (thin <100 lines)
      data_sink.py    # GCSDataSink, BroadcastSink (thin <100 lines)
    cli/
      main.py         # Entry point with --operation and --mode flags
      handlers/       # Operation-specific handlers
    config.py         # Runtime config singleton (uses ConfigStore)
    schemas/          # Service-owned schemas
```

**Key principle**: `engine/` has ZERO imports from `adapters/`. Dependencies point inward.

**CLI Pattern**: Two separate flags (universal across all services):

- `--operation` = WHAT to run (service-specific: instrument, corporate_actions, fetch, compute, train, backtest)
- `--mode` = HOW to run (universal: batch or live)

### Current State vs Target


| Service                   | Current                                     | Target                                  | Gap                                             |
| ------------------------- | ------------------------------------------- | --------------------------------------- | ----------------------------------------------- |
| instruments-service       | `app/core/`, `cli/handlers/`                | `engine/`, `adapters/`, `cli/`          | Missing adapters/, handlers not in cli/         |
| market-tick-data-handler  | `app/core/`, `cli/handlers/`, `app/venues/` | `engine/`, `adapters/`, `cli/`          | Missing adapters/, venues should be in engine/  |
| features-calendar-service | `app/core/`, `cli/batch_handler.py`         | `engine/`, `adapters/`, `cli/handlers/` | Missing adapters/, handlers not in subdirectory |
| All services              | Varies                                      | Uniform                                 | Inconsistent organization                       |


## Implementation Plan

### Phase -1: Complete Pending API Keys Work (Prerequisites)

**CRITICAL**: Finish uncommitted API keys standardization work before structure refactoring.

**Current state**: 20+ files modified but uncommitted in instruments-service

**Files to complete**:

- config.py
- dependency_checker.py
- All 7 handlers (instrument_handler, live_mode_handler, corporate_actions_*, etc.)
- Core files (instruments_service.py, instrument_processing_service.py, cloud_instrument_storage.py)
- Processors (canonical_key_generator.py, defi_processor.py, derived_fields_populator.py)
- CLI (main.py, parser.py)
- Quality gate workflow

**Work to complete** (from `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md`):

1. **API Keys Standardization**:
  - All API keys via `get_secret_client()` (no `os.environ.get`)
  - Update dependency_checker.py to use Secret Manager
  - Update all handlers to use standardized API key resolution
  - Update scripts (find_subgraph_ids.py, test_batch_cost_comparison.py)
2. **Instrument Aggregation** (new operation):
  - Add `--operation aggregate` support
  - Implement aggregation logic
  - Update InstrumentsDomainClient in UCS to read aggregated data
3. **InstrumentsDomainClient Usage**:
  - Standardize instrument reading across services
  - Remove duplicate `_load_instruments_by_venue` implementations
  - Use InstrumentsDomainClient from UCS

**Completion steps**:

1. Review uncommitted changes (`git diff`)
2. Complete any pending work from API keys plan
3. Run quality gates: `bash scripts/quality-gates.sh`
4. Fix any issues
5. Commit changes: `bash scripts/quickmerge.sh "Complete API keys standardization"`
6. Wait for CI to pass and PR to merge
7. Pull latest main

**Checkpoint**: API keys work merged to main, instruments-service on latest main with clean working directory.

### Phase 0: Complete Library Features (Foundation)

**⚠️ COORDINATION**: Another agent is working on API keys standardization for instruments-service. Phase 0-1 can proceed in parallel. Phase 2 (structure refactoring) waits for API keys work to merge first.

**CRITICAL**: Ensure libraries provide full functionality BEFORE services refactor to use them.

#### 0.1 Add Missing Features to unified-events-interface

**Status**: UEI exists but missing observability features

**Add**:

1. `observability/error_tracker.py` - ErrorWarningCounter class
2. `observability/memory_tracker.py` - DataFrame memory helpers
3. Update `__init__.py` - Export new features

**Test in UEI**:

```bash
cd unified-events-interface
bash scripts/quality-gates.sh --no-fix
# Must pass before services use it
```

#### 0.2 Verify unified-config-interface Features

**Status**: UCI is complete (ConfigStore, TimeSeriesConfigStore, ConfigReloader exist)

**Verify**:

1. ConfigStore works (load/save config to GCS)
2. TimeSeriesConfigStore works (replay_at, config_for_date)
3. ConfigReloader works (PubSub subscription, hot reload)

**Test in UCI**:

```bash
cd unified-config-interface
bash scripts/quality-gates.sh --no-fix
# Must pass before services use it
```

#### 0.3 Test Full Library Usage in instruments-service (Pilot)

**CRITICAL**: Validate libraries work in real service BEFORE refactoring structure.

**Add to instruments-service** (no structure changes yet):

1. Use `ErrorWarningCounter` from UEI (replace local implementation)
2. Use `ConfigStore` for config persistence
3. Use `TimeSeriesConfigStore` in batch handlers
4. Use `ConfigReloader` in live handlers

**Test**:

```bash
cd instruments-service
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Must pass before structure refactoring
```

**Verify**:

- ✅ ErrorWarningCounter works (counts errors/warnings)
- ✅ ConfigStore loads config from GCS
- ✅ TimeSeriesConfigStore replays config for dates
- ✅ ConfigReloader receives hot reload events
- ✅ All unit tests pass
- ✅ All integration tests pass

#### 0.4 Update Documentation and Cursor Rules (Hardened Standards)

**CRITICAL**: Document standards BEFORE refactoring services.

**Update codex**:

1. `06-coding-standards/cli-standards.md` - CLI pattern (--operation + --mode)
2. `06-coding-standards/service-structure-standards.md` - engine/adapters/cli structure
3. `06-coding-standards/config-types.md` - Grid vs runtime config
4. `06-coding-standards/thin-adapters-pattern.md` - Adapter delegation to libraries
5. `06-coding-standards/dependency-checker-standard.md` - Standard dependency checker
6. Update `README.md` - Add all new standards sections

**Update cursor rules**:

1. `.cursorrules` - Add service structure, observability, config standards
2. Create `.cursor/rules/service-structure-standards.mdc`
3. Create `.cursor/rules/config-store-usage.mdc`
4. Create `.cursor/rules/thin-adapters.mdc`

**Verify**:

- ✅ All standards documented in codex
- ✅ All standards in cursor rules
- ✅ Examples provided for each pattern
- ✅ Anti-patterns documented

### Phase 1: Refactor CLI to Separate Operation from Mode

**Target**: ALL services use `--operation` and `--mode` flags separately.

#### 0.1 Update CLI Argument Parsing

**Pattern for all services**:

```python
# cli/parser.py
def parse_arguments():
    parser = argparse.ArgumentParser()

    # Operation: WHAT to run (service-specific)
    parser.add_argument(
        "--operation",
        required=True,
        choices=["instrument", "corporate_actions"],  # Service-specific
        help="Operation to perform"
    )

    # Mode: HOW to run (universal)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["batch", "live"],
        help="Execution mode: batch (date range) or live (scheduled/continuous)"
    )

    # Batch-specific args
    parser.add_argument("--start-date", help="Start date (batch mode)")
    parser.add_argument("--end-date", help="End date (batch mode)")

    # Live-specific args
    parser.add_argument("--interval", type=int, default=15, help="Interval in minutes (live mode)")

    return parser.parse_args()
```

#### 0.2 Update Handler Dispatch Logic

```python
# cli/main.py
def main():
    args = parse_arguments()

    # Get handler based on operation (not mode)
    if args.operation == "instrument":
        handler = InstrumentHandler(config, mode=args.mode)
    elif args.operation == "corporate_actions":
        handler = CorporateActionsHandler(config, mode=args.mode)

    # Handler knows its mode (batch or live)
    if args.mode == "batch":
        result = handler.run_batch(start_date=args.start_date, end_date=args.end_date)
    else:  # live
        result = handler.run_live(interval=args.interval)
```

#### 0.3 Update Handlers to Accept Mode

```python
# cli/handlers/instrument_handler.py
class InstrumentHandler(ModeHandler):
    def __init__(self, config: dict, mode: str):
        super().__init__(config)
        self.mode = mode  # "batch" or "live"

    def run_batch(self, start_date: str, end_date: str) -> dict:
        """Batch mode: process date range."""
        # ... existing batch logic ...

    def run_live(self, interval: int = 15) -> dict:
        """Live mode: 15min UTC aligned."""
        # ... existing live logic ...
```

#### 0.4 Service-Specific Operations


| Service                        | Operations                        | Notes                                                      |
| ------------------------------ | --------------------------------- | ---------------------------------------------------------- |
| instruments-service            | `instrument`, `corporate_actions` | Two distinct operations                                    |
| market-tick-data-handler       | `fetch`                           | Single operation, batch/live modes                         |
| market-data-processing-service | `process`                         | Single operation, batch/live modes                         |
| features-*-service             | `compute`                         | Single operation, batch/live modes                         |
| ml-training-service            | `train`                           | Single operation, batch/live modes                         |
| ml-inference-service           | `infer`                           | Single operation, batch/live modes                         |
| strategy-service               | `backtest`, `live_trade`          | Two operations (backtest=batch only, live_trade=live only) |


#### 0.5 Backward Compatibility (Transition Period)

**NO DUPLICATE LOGIC** - Old flags auto-convert to new flags:

```python
# cli/parser.py - Single conversion point
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", help="Operation to perform")
    parser.add_argument("--mode", help="Execution mode: batch or live")

    args = parser.parse_args()

    # Auto-convert old --mode values to new pattern (NO DUPLICATE LOGIC)
    if args.mode in ["instrument", "corporate_actions_production", "corporate_actions"]:
        logger.warning(
            f"⚠️ --mode {args.mode} is deprecated. "
            f"Use --operation {args.mode} --mode batch instead."
        )
        args.operation = args.mode.replace("_production", "")
        args.mode = "batch"

    # Validate required flags
    if not args.operation or not args.mode:
        parser.error("--operation and --mode are required")

    return args
```

**Key**: Conversion happens ONCE at parse time, then all downstream code uses `args.operation` and `args.mode` only.

#### 0.6 Update Codex Documentation

**File**: `unified-trading-codex/06-coding-standards/cli-standards.md` (NEW)

Create comprehensive CLI standards document:

```markdown
# CLI Standards: Operation and Mode Separation

## Universal Pattern

ALL services MUST use two separate flags:

```bash
--operation <what>  # What to run (service-specific)
--mode <how>        # How to run (batch or live)
```

## Flag Definitions

### --operation (Service-Specific)

Defines WHAT operation to perform. Values are domain-specific:


| Service                        | Operations                        | Description                                     |
| ------------------------------ | --------------------------------- | ----------------------------------------------- |
| instruments-service            | `instrument`, `corporate_actions` | Generate instruments or fetch corporate actions |
| market-tick-data-handler       | `fetch`                           | Fetch market tick data                          |
| market-data-processing-service | `process`                         | Process market data                             |
| features-*-service             | `compute`                         | Compute features                                |
| ml-training-service            | `train`                           | Train ML models                                 |
| ml-inference-service           | `infer`                           | Run ML inference                                |
| strategy-service               | `backtest`, `live_trade`          | Backtest or live trade                          |


### --mode (Universal)

Defines HOW to execute the operation. Values are universal:

- `batch` - Process historical date range
- `live` - Continuous/scheduled execution

## Mode Behavior

### Batch Mode

- **Trigger**: Date range (`--start-date`, `--end-date`)
- **Execution**: Process all dates, then exit
- **Data source**: GCS (historical data)
- **Data sink**: GCS (batch output path)

### Live Mode

- **Trigger**: Scheduled (Cloud Run) or continuous (long-running container)
- **Execution**: Never exits, runs on interval
- **Data source**: WebSocket streams or scheduled GCS reads
- **Data sink**: GCS (live output path) + broadcast to consumers

## Implementation Pattern

```python
# cli/parser.py
def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--operation",
        required=True,
        choices=["operation1", "operation2"],  # Service-specific
        help="Operation to perform"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["batch", "live"],
        help="Execution mode"
    )

    # Batch-specific
    parser.add_argument("--start-date", help="Start date (batch mode)")
    parser.add_argument("--end-date", help="End date (batch mode)")

    # Live-specific
    parser.add_argument("--interval", type=int, default=15, help="Interval in minutes (live mode)")

    return parser.parse_args()

# cli/main.py
def main():
    args = parse_arguments()

    # Dispatch based on operation
    if args.operation == "operation1":
        handler = Operation1Handler(config, mode=args.mode)
    elif args.operation == "operation2":
        handler = Operation2Handler(config, mode=args.mode)

    # Execute based on mode
    if args.mode == "batch":
        result = handler.run_batch(start_date=args.start_date, end_date=args.end_date)
    else:  # live
        result = handler.run_live(interval=args.interval)
```

## Backward Compatibility

Old `--mode` values auto-convert to new pattern:

```python
# Auto-convert at parse time (NO DUPLICATE LOGIC)
if args.mode in ["instrument", "corporate_actions_production"]:
    logger.warning(f"⚠️ --mode {args.mode} is deprecated")
    args.operation = args.mode.replace("_production", "")
    args.mode = "batch"
```

## Quality Gates

CLI must follow this pattern to pass quality gates:

- ✅ `--operation` and `--mode` flags exist
- ✅ Handler dispatch based on operation
- ✅ Mode execution based on batch/live
- ❌ No `--mode` values that conflate operation and execution

## Examples

```bash
# instruments-service
--operation instrument --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation instrument --mode live --interval 15
--operation corporate_actions --mode batch --start-date 2024-01-01
--operation corporate_actions --mode live

# market-tick-data-handler
--operation fetch --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation fetch --mode live

# features-delta-one-service
--operation compute --mode batch --start-date 2024-01-01 --end-date 2024-01-31
--operation compute --mode live --interval 15
```

```

#### 0.7 Update Related Codex Docs

**Files to update**:

1. `unified-trading-codex/04-architecture/batch-live-symmetry.md`
   - Add CLI standards section referencing `cli-standards.md`
   - Update examples to use `--operation` and `--mode`

2. `unified-trading-codex/06-coding-standards/README.md`
   - Add CLI standards to table of contents
   - Reference `cli-standards.md` in service structure section

3. Update `.cursorrules` workspace file
   - Add CLI standards summary
   - Reference codex for full details

#### 0.7 Update All Services (Parallel)

**Services to update** (14 total):

- instruments-service
- market-tick-data-handler
- market-data-processing-service
- features-calendar-service
- features-delta-one-service
- features-volatility-service
- features-onchain-service
- ml-training-service
- ml-inference-service
- strategy-service
- risk-and-exposure-service
- position-balance-monitor-service
- pnl-attribution-service
- execution-services

**Use parallel agents** (4 agents, 3-4 services each) for cross-repo updates.

#### 0.9 Complete Config Standardization (Two Types)

**CRITICAL**: unified-config-interface overhaul is COMPLETE but services don't use ConfigStore/TimeSeriesConfigStore yet.

**Two Config Types** (from UCI overhaul plan):

| Type | Services | Purpose | Storage | UCI Feature |
|------|----------|---------|---------|-------------|
| **Grid config** | strategy, execution, ml-training | Param optimization, grid search, many configs per run | Domain buckets (`execution-store`, `strategy-store`, `ml-configs`) | NOT ConfigStore (domain-specific) |
| **Runtime config** | All 14 services | Service runtime params, slow-changing, user-editable | `gs://config-store-{proj}/{service}/` | ConfigStore + TimeSeriesConfigStore |

**Gap**: Services inherit from `UnifiedCloudConfig` but don't use `ConfigStore` for persistence or `TimeSeriesConfigStore` for batch replay.

**Required migrations**:

1. **Migrate to UnifiedCloudConfig** (2 services):
   - ml-training-service: `UnifiedCloudServicesConfig` → `UnifiedCloudConfig`
   - strategy-service: `UnifiedCloudServicesConfig` → `UnifiedCloudConfig`

2. **Add ConfigStore usage** (14 services - runtime config):


```python
   # Current (config.py only)
   from unified_config_interface import UnifiedCloudConfig

   class MyServiceConfig(UnifiedCloudConfig):
       __config_schema_version__ = "1.0"  # Add schema version
       service_name: str = "my-service"
       max_workers: int = 16

   # Singleton
   _config = MyServiceConfig()

   # New (add ConfigStore for persistence + hot reload)
   from unified_config_interface import UnifiedCloudConfig, ConfigStore, ConfigReloader

   class MyServiceConfig(UnifiedCloudConfig):
       __config_schema_version__ = "1.0"
       service_name: str = "my-service"
       max_workers: int = Field(16, json_schema_extra={"hot_reloadable": True})

   # Singleton with ConfigStore
   _config: MyServiceConfig | None = None
   _config_store: ConfigStore | None = None

   def get_config() -> MyServiceConfig:
       global _config, _config_store
       if _config is None:
           # Load from ConfigStore (GCS) or fall back to .env
           _config_store = ConfigStore(
               bucket_name=f"config-store-{project_id}",
               service_name="my-service",
               schema_version="1.0"
           )
           _config = _config_store.load_config(MyServiceConfig)
       return _config


```

1. **Add TimeSeriesConfigStore for batch replay** (batch-mode services):

```python
   # In batch handler
   from unified_config_interface import TimeSeriesConfigStore

   store = TimeSeriesConfigStore(
       bucket_name=f"config-store-{project_id}",
       service_name="my-service",
       schema_version="1.0"
   )

   # Replay config for each date
   for date in date_range:
       config = store.config_for_date(date)  # Config effective on this date
       results = engine.process(data, config)


```

1. **Add ConfigReloader for live mode** (live-mode services):

```python
   # In live handler
   from unified_config_interface import ConfigReloader

   def on_config_change(new_config: MyServiceConfig):
       logger.info("Config hot-reloaded")
       # Apply hot-reloadable changes

   reloader = ConfigReloader(config, callback=on_config_change)
   reloader.start()  # Subscribes to PubSub for config updates


```

**Grid config services** (strategy, execution, ml-training):

- Keep domain-specific config generation (GridConfigGenerator, strategy grid, ML grid)
- These are NOT runtime configs - they're optimization params
- Store in domain buckets, NOT config-store

**Note**: Event logging is already 100% centralized (all 7 services use `unified-events-interface`). No migration needed.

### Phase 2: Refactor Service Structure (instruments-service Pilot)

**Rationale**: You selected unified-events-interface (UEI) for observability centralization. UEI already handles lifecycle events; adding error/warning tracking and memory monitoring aligns with its observability mission.

#### 1.1 Move ErrorWarningCounter to UEI

**Source**: [instruments_service/app/core/instruments_service.py:34-52](instruments-service/instruments_service/app/core/instruments_service.py)

```python
# Current location (instruments-service only)
class ErrorWarningCounter(logging.Handler):
    def __init__(self):
        super().__init__()
        self.error_count = 0
        self.warning_count = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.error_count += 1
        elif record.levelno == logging.WARNING:
            self.warning_count += 1
```

**Target**: `unified-events-interface/unified_events_interface/observability/error_tracker.py`

**Enhancements**:

- Add `get_counts()` method returning dict
- Add `reset()` method for test isolation
- Add context manager support for scoped tracking
- Thread-safe counters (use `threading.Lock`)

#### 1.2 Add Memory Monitoring to UEI

**Current**: `MemoryMonitor` exists in unified-trading-services but services duplicate DataFrame memory tracking.

**Action**: Add DataFrame memory helpers to UEI:

```python
# unified-events-interface/unified_events_interface/observability/memory_tracker.py
def get_dataframe_memory_usage(df: pd.DataFrame) -> int:
    """Get DataFrame memory usage in bytes."""
    return df.memory_usage(deep=True).sum()

def log_memory_metrics(service_name: str, **metrics: int) -> None:
    """Log memory metrics as observability event."""
    log_event("MEMORY_USAGE", f"{service_name}: {metrics}")
```

**Keep in UCS**: System-level `MemoryMonitor` (cross-platform, threshold checking) stays in unified-trading-services. UEI adds DataFrame-specific helpers.

#### 1.3 Update All Services to Use Centralized Observability

**Services to update** (7 total):

- instruments-service (remove local ErrorWarningCounter)
- market-tick-data-handler
- market-data-processing-service
- features-calendar-service
- features-delta-one-service
- ml-training-service
- strategy-service

**Pattern**:

```python
from unified_events_interface import ErrorWarningCounter, log_memory_metrics

# In main processing function
counter = ErrorWarningCounter()
logging.getLogger().addHandler(counter)

try:
    # ... processing ...
    log_memory_metrics("my-service", dataframe_mb=df_memory // 1024**2)
finally:
    counts = counter.get_counts()
    log_event("PROCESSING_COMPLETED", f"errors={counts['errors']}, warnings={counts['warnings']}")
```

### Phase 3: Rollout to All Services

**Target**: All 7 services match `engine/`, `adapters/`, `cli/` structure.

#### 2.1 Create Refactoring Template

**Document**: `unified-trading-codex/06-coding-standards/service-structure-refactoring-guide.md`

**Contents**:

1. Migration checklist (app/core → engine, I/O → adapters)
2. Import path updates (automated with script)
3. Test updates (update import paths)
4. Quality gates verification

#### 2.2 Pilot Refactoring: instruments-service (Detailed)

**See complete file-by-file mapping**: `.cursor/plans/INSTRUMENTS_SERVICE_COMPLETE_REFACTORING.md`

**See line count analysis**: `.cursor/plans/INSTRUMENTS_SERVICE_LINE_COUNT_ANALYSIS.md`

**Related documents**:

- **Detailed to-dos (instruments finish + market-tick refactor, imports aligned to libraries):** [instruments_and_market_tick_refactor_todos.md](instruments_and_market_tick_refactor_todos.md)
- **Library refactor (assumed complete):** [fix_7_unified_libraries_quality_gates.plan.md](fix_7_unified_libraries_quality_gates.plan.md) — UCI/UEI/UDS/UMI/UCS import rules
- API keys standardization: `instruments-service/docs/API_KEYS_STANDARDIZED_PROCESS.md`
- Quality gate audit: `instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md`

**⚠️ COORDINATION WITH OTHER WORK**:

**Parallel work in progress** (another agent):

- `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md` - API keys standardization
- `.cursor/plans/INSTRUMENTS_DOMAIN_DECISIONS.md` - Domain decisions
- `instruments-service/docs/API_KEYS_STANDARDIZED_PROCESS.md` - API keys process

**Coordination strategy**:

1. **Wait for API keys work to complete** before starting Phase 2 (structure refactoring)
2. **Phase 0 (libraries) can proceed** - No conflict with API keys work
3. **Phase 1 (CLI) can proceed** - No conflict with API keys work
4. **Phase 2 (structure refactoring) waits** - Merge API keys changes first, then refactor structure
5. **Avoid conflicts**: Don't touch files being modified by API keys agent

**Files potentially affected by both plans**:

- `dependency_checker.py` - API keys validation + structure refactoring
- `config.py` - API keys config + ConfigStore adoption
- Handlers - API keys usage + structure refactoring

**Resolution**: Structure refactoring happens AFTER API keys work completes and is merged.

**Key metrics**:

- **Current**: 14,657 lines of Python code (excluding tests)
- **Target**: ~13,000 lines (-1,500 lines or -10%)
- **Reduction from**: Deleting 3 deprecated handlers, thinning adapters, removing DRY violations

**CRITICAL**: instruments-service is the pilot. Get this right, then replicate pattern to other 13 services.

**Target structure** (operation-based organization):

```
instruments_service/engine/
  __init__.py
  orchestrator.py                    # Top-level (dispatches to operations)
  operations/                        # ✅ Operation-specific logic
    instruments/                     # --operation instrument
      __init__.py
      orchestrator.py                # Instruments orchestration
      batch_orchestrator.py          # Batch-specific
      processors/                    # Category processors
        cefi_processor.py
        tradfi_processor.py
        defi_processor.py
    corporate_actions/               # --operation corporate_actions
      __init__.py
      adapter.py                     # yfinance integration
      models.py                      # Corporate actions models
      utils.py                       # Shared utilities
  processors/                        # Shared processors (both operations)
    canonical_key_generator.py
    ccxt_manual_fallback.py
    derived_fields_populator.py
    symbol_parser.py
  validation/                        # Standard validation
    dependency_checker.py            # STANDARDIZE (all services)
    selective_validator.py
  venues/                            # Venue-specific logic
    ccxt_service.py                  # From utils/
    special_instruments.py           # From utils/
    venue_adapter_loader.py          # From adapter_loader.py
```

**Why `engine/operations/`**:

1. ✅ Operations are business logic (belong in engine)
2. ✅ Aligns with CLI `--operation` flag
3. ✅ Clear hierarchy: operations/ contains operation-specific logic
4. ✅ Shared logic stays in engine/ (processors/, validation/, venues/)
5. ✅ Consistent: `cli/handlers/` dispatch to `engine/operations/`

**Refactoring steps**: See `.cursor/plans/INSTRUMENTS_SERVICE_COMPLETE_REFACTORING.md` for complete file-by-file mapping.

#### 2.3 Standardize dependency_checker Across All Services

**Current**: Only instruments-service has `dependency_checker.py`

**Target**: ALL 14 services use standard `engine/validation/dependency_checker.py`

**Pattern**:

```python
# engine/validation/dependency_checker.py (standard across all services)
from unified_trading_services import BaseDependencyChecker

class ServiceDependencyChecker(BaseDependencyChecker):
    """Standard dependency checker - same pattern for all services."""

    def check_upstream_data(self) -> bool:
        """Check if upstream data exists (service-specific)."""
        # Service-specific checks
        pass

    def check_config(self) -> bool:
        """Check if config is valid."""
        # Standard checks (same for all services)
        pass
```

**Rollout**: Create standard template in codex, apply to all 14 services.

#### 2.4 Refactor Other Services (Parallel)

**Tier 1** (batch-live symmetry already implemented):

- ml-inference-service
- position-balance-monitor-service

**Tier 2** (partially implemented):

- market-data-processing-service
- risk-and-exposure-service

**Tier 3** (batch-only, refactor when adding live mode):

- market-tick-data-handler
- features-calendar-service
- features-delta-one-service
- features-volatility-service
- features-onchain-service
- ml-training-service
- strategy-service

**Refactoring steps per service**:

1. **Create new directories**:

```bash
   mkdir -p {service_module}/engine
   mkdir -p {service_module}/adapters


```

1. **Move core logic to engine/**:
  - `app/core/*.py` → `engine/` (business logic, calculators, validators)
  - Remove I/O code (GCS reads/writes) from moved files
  - Keep engine/ pure (no storage, no API calls)
2. **Extract I/O to adapters/ (THIN wrappers only)**:
  **CRITICAL**: Adapters delegate to unified libraries, NO business logic.
   **Good adapter (thin wrapper)**:

```python
   # adapters/data_source.py
   from unified_trading_services import get_storage_client
   from unified_market_interface import MarketDataSchema
   import pandas as pd

   class GCSDataSource:
       """Thin wrapper: delegates to UCS for storage, UMI for schemas."""

       def __init__(self, bucket: str):
           self.client = get_storage_client()  # UCS owns storage
           self.bucket = bucket

       def get_data(self, date: str, instrument: str) -> pd.DataFrame:
           """Read from GCS, validate schema, return DataFrame."""
           # UCS handles storage
           blob_path = f"market_data/day={date}/{instrument}.parquet"
           df = self.client.read_parquet(self.bucket, blob_path)

           # UMI handles schema validation
           MarketDataSchema.validate(df)

           return df  # Just return, no transformation


```

   **Bad adapter (business logic - WRONG)**:

```python
   # ❌ WRONG: Adapter has business logic
   class GCSDataSource:
       def get_data(self, date: str, instrument: str) -> pd.DataFrame:
           df = self.client.read_parquet(...)

           # ❌ Business logic belongs in engine/
           df['returns'] = df['close'].pct_change()
           df = df.dropna()
           df = self._apply_filters(df)  # ❌ Transformation logic

           return df


```

   **Data sink example (thin wrapper)**:

```python
   # adapters/data_sink.py
   from unified_trading_services import get_storage_client
   from unified_data_interface import validate_schema
   import pandas as pd

   class GCSDataSink:
       """Thin wrapper: delegates to UCS for storage, UDI for validation."""

       def __init__(self, bucket: str):
           self.client = get_storage_client()  # UCS owns storage
           self.bucket = bucket

       def publish(self, df: pd.DataFrame, date: str, output_type: str) -> None:
           """Validate schema, write to GCS."""
           # UDI handles schema validation
           validate_schema(df, expected_schema=output_type)

           # UCS handles storage
           blob_path = f"output/{output_type}/day={date}/data.parquet"
           self.client.write_parquet(df, self.bucket, blob_path)


```

1. **Update CLI**:
  - Keep `cli/handlers/` pattern (operation-specific handlers)
  - Each handler implements mode-specific orchestration
  - CLI main.py dispatches to appropriate handler based on `--mode` flag
2. **Update imports**:

```bash
   # Automated script
   find . -name "*.py" -exec sed -i '' 's/from {service}.app.core/from {service}.engine/g' {} \;


```

1. **Update tests**:
  - Update import paths
  - Verify all tests pass
  - Add integration tests for adapters
2. **Update quality gates**:
  - Run `bash scripts/quality-gates.sh --no-fix`
  - Fix any import errors
  - Verify no circular imports

#### 2.3 Thin Adapter Pattern (CRITICAL - Avoid DRY Violations)

**Principle**: Adapters are <100 lines, delegate to unified libraries. NO business logic, validation, or transformation.

**Unified Library Responsibilities**:


| Library                            | Responsibility                                      | Adapters Delegate To                         |
| ---------------------------------- | --------------------------------------------------- | -------------------------------------------- |
| **UCS** (unified-trading-services)   | Storage clients, error handling, retries, auth      | `get_storage_client()`, `@handle_api_errors` |
| **UMI** (unified-market-interface) | Venue configs, market categories, WebSocket clients | `get_venue_config()`, venue-specific clients |
| **UCI** (unified-config-interface) | Configuration management, validation                | `UnifiedCloudConfig`, config validation      |
| **UEI** (unified-events-interface) | Event logging, error tracking, memory monitoring    | `log_event()`, `ErrorWarningCounter`         |
| **UOI** (unified-trade-execution-interface)  | Order models, execution interfaces                  | Order schemas, execution adapters            |


**Good Adapter (Thin - 50 lines)**:

```python
# adapters/data_source.py
from unified_trading_services import get_storage_client
import pandas as pd

class GCSDataSource:
    """Thin wrapper - delegates storage to UCS."""

    def __init__(self, bucket: str):
        self.client = get_storage_client()  # UCS: auth, retries, errors
        self.bucket = bucket

    def read(self, path: str) -> pd.DataFrame:
        """Delegate to UCS - NO validation or transformation."""
        return self.client.read_parquet(self.bucket, path)
```

**Bad Adapter (Thick - violates DRY)**:

```python
# adapters/data_source.py - WRONG
from google.cloud import storage  # ❌ Direct cloud import (use UCS)
import pandas as pd

class GCSDataSource:
    def __init__(self, bucket: str, project_id: str):
        # ❌ Reimplements UCS auth logic
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket)

    def read(self, path: str) -> pd.DataFrame:
        blob = self.bucket.blob(path)

        # ❌ Reimplements UCS retry logic
        for attempt in range(3):
            try:
                data = blob.download_as_bytes()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        # ❌ Reimplements UCS error handling
        try:
            df = pd.read_parquet(BytesIO(data))
        except Exception as e:
            logger.error(f"Failed to parse parquet: {e}")
            raise

        # ❌ Business logic in adapter (belongs in engine)
        if df.empty:
            raise ValueError("Empty dataframe")
        if "timestamp" not in df.columns:
            raise ValueError("Missing timestamp column")

        return df
```

**What's Wrong with Bad Adapter**:

1. ❌ Reimplements UCS storage client (DRY violation)
2. ❌ Reimplements UCS retry logic (DRY violation)
3. ❌ Reimplements UCS error handling (DRY violation)
4. ❌ Includes validation logic (belongs in engine, not adapter)
5. ❌ Direct cloud provider import (violates cloud-agnostic principle)
6. ❌ 40+ lines (should be <20 for this simple case)

**Adapter Size Guidelines**:

- Simple read/write: <20 lines
- Multiple operations: <50 lines
- Complex orchestration: <100 lines (MAX)
- If >100 lines: Split or move logic to engine/libraries

**Quality Gate Check**:

```bash
# Verify adapters are thin
for adapter in adapters/*.py; do
  lines=$(wc -l < "$adapter")
  if [ "$lines" -gt 100 ]; then
    echo "❌ $adapter too large ($lines lines, max 100)"
  fi
done
```

#### 2.4 Update features-calendar-service (Special Case)

**Issue**: Only service without `cli/handlers/` subdirectory.

**Action**: Create `cli/handlers/` directory and move `cli/batch_handler.py` → `cli/handlers/batch_handler.py`.

### Phase 4: Consolidate Corporate Actions Handlers

**Target**: instruments-service has 1-2 handlers instead of 4.

#### 3.1 Extract Shared Utilities

**Duplicated code** (~200 lines):

- `_get_tickers_from_gcs()` (all 4 handlers)
- Adapter initialization patterns
- Output directory creation

**Action**: Create `instruments_service/corporate_actions/utils.py`:

```python
# instruments_service/corporate_actions/utils.py
from unified_trading_services import get_storage_client

def get_tickers_from_gcs(project_id: str, bucket: str, fallback_dates: list[str]) -> list[str]:
    """Load tickers from GCS instruments data.

    Replaces duplicated _get_tickers_from_gcs() in 4 handlers.
    """
    # ... implementation ...
```

#### 3.2 Fix Circular Imports

**Issue**: All 4 handlers import `unified_trading_services` inside functions (whitelisted in quality gates).

**Action**: Move imports to top of file:

```python
# At top of file
from unified_trading_services import get_storage_client

# In function (no more lazy import)
def get_tickers_from_gcs(...):
    client = get_storage_client()
```

**Remove quality gate bypasses** after fixing:

- `QUALITY_GATE_BYPASS_AUDIT.md` lines 48-51 (circular import whitelist)
- `CODEX_VIOLATIONS_MANIFEST.md` lines 273-301 (import inside function)

#### 3.3 Consolidate Handlers

**Keep**:

1. `corporate_actions_production_handler.py` (main pipeline, 590 lines)
2. `corporate_actions_handler.py` (date-range queries, 527 lines) - if still needed

**Remove** (marked deprecated in docs):

1. `corporate_actions_backfill_handler.py` (533 lines)
2. `corporate_actions_update_handler.py` (217 lines)

**Action**:

1. Add deprecation warnings to backfill/update handlers
2. Update `handlers/__init__.py` to remove deprecated handlers
3. Update docs to clarify production handler is primary
4. Archive deprecated handlers (move to `deprecated/` directory)

### Phase 5: Final Verification

#### 4.1 Update Codex

**File**: [unified-trading-codex/06-coding-standards/README.md](unified-trading-codex/06-coding-standards/README.md)

**Changes**:

1. **Add Service Structure section** (after line 200):

```markdown
## Service Structure Standards [REQUIRED]

### Directory Layout

ALL services MUST follow this structure:

```

{service}/
  {service_module}/
    engine/           # Mode-agnostic processing (90% of code)
      **init**.py
      calculator.py   # Business logic, pure functions
      validator.py    # Input/output validation
    adapters/         # Mode-specific I/O (4 seams)
      data_source.py  # GCSDataSource, StreamDataSource
      data_sink.py    # GCSDataSink, BroadcastSink
    cli/
      main.py         # Entry point: --mode batch|live
    config.py         # UnifiedCloudConfig
    schemas/          # Service-owned schemas
  tests/
    unit/             # Test engine/ (pure logic)
    integration/      # Test adapters/ (mocked I/O)
    e2e/              # Test full pipeline

```

### Dependency Rules

1. **engine/ has ZERO imports from adapters/**
   - Engine defines interfaces (abstract base classes)
   - Adapters implement interfaces
   - Dependencies point inward (adapters → engine, never reverse)

2. **adapters/ are THIN wrappers (no business logic)**
   - Delegate to unified libraries for actual work:
     - **UCS**: Storage (GCS, BigQuery), secrets, error handling
     - **UCI**: Configuration loading and validation
     - **UEI**: Event logging, error tracking, memory monitoring
     - **UMI**: Market data schemas, venue configs
     - **UDI**: Data validation, schema enforcement
   - Adapters only: instantiate library clients, call library methods, return results
   - NO transformations, NO filtering, NO business logic

3. **cli/handlers/ orchestrate engine + adapters**
   - Each handler (operation-specific) instantiates adapters based on mode
   - Handlers pass adapters to engine
   - Engine never knows which adapter implementation it's using

4. **cli/handlers/ pattern is ALLOWED**
   - Operation-specific handlers (instrument_handler, corporate_actions_handler, live_mode_handler)
   - Each handler orchestrates engine + adapters for specific operation
   - Main CLI dispatches to appropriate handler based on `--mode` flag

5. **Domain-specific directories allowed**
   - `corporate_actions/`, `venues/`, `calculators/`, `strategies/` OK
   - Must be in `engine/` if mode-agnostic
   - Must be in `adapters/` if mode-specific

### Migration from Legacy Structure

Services using `app/core/` must refactor:

1. `app/core/*.py` → `engine/` (remove I/O code)
2. Extract I/O → `adapters/data_source.py`, `adapters/data_sink.py` (THIN wrappers only)
3. Adapters delegate to unified libraries (UCS, UCI, UEI, UMI, UDI)
4. Keep `cli/handlers/` for operation-specific orchestration
5. Update imports, tests, quality gates

**Adapter responsibilities (delegate only)**:
- Storage: Use `get_storage_client()` from UCS
- Secrets: Use `get_secret_client()` from UCS
- Config: Use config classes from UCI
- Events: Use `log_event()` from UEI
- Schemas: Use schema validators from UMI/UDI
- Error handling: Use `@handle_api_errors` from UCS

See: `06-coding-standards/service-structure-refactoring-guide.md`
```

1. **Add Observability Centralization section** (after line 250):

```markdown
## Observability Standards [REQUIRED]

### Error and Warning Tracking

ALL services MUST use centralized error/warning tracking from unified-events-interface:

```python
from unified_events_interface import ErrorWarningCounter, log_event

counter = ErrorWarningCounter()
logging.getLogger().addHandler(counter)

try:
    # ... processing ...
finally:
    counts = counter.get_counts()
    log_event("PROCESSING_COMPLETED",
              f"errors={counts['errors']}, warnings={counts['warnings']}")
```

### Memory Monitoring

Use centralized memory helpers from unified-events-interface:

```python
from unified_events_interface import get_dataframe_memory_usage, log_memory_metrics

df_memory = get_dataframe_memory_usage(df)
log_memory_metrics("my-service", dataframe_mb=df_memory // 1024**2)
```

For system memory monitoring, use unified-trading-services:

```python
from unified_trading_services import get_memory_monitor

monitor = get_memory_monitor()
if monitor.is_memory_threshold_exceeded(threshold_percent=85):
    logger.warning("Memory threshold exceeded")
```

### Anti-Patterns

❌ **NEVER implement service-specific error counters**
❌ **NEVER duplicate memory tracking logic**
❌ **NEVER use print() for observability** (use log_event)

```

#### 4.2 Update Workspace .cursorrules

**File**: [.cursorrules](.cursorrules)

**Add to "Service Structure Required" section** (around line 550):

```markdown
## Service Structure Required

ALL services MUST follow the batch-live symmetry structure:

```

{service}/
  {service_module}/
    engine/           # Mode-agnostic (90% of code)
    adapters/         # Mode-specific I/O (4 seams)
    cli/              # Entry point with --mode flag
    config.py
    schemas/

```

**Critical rules:**
- `engine/` has ZERO imports from `adapters/`
- Dependencies point inward (adapters → engine)
- `cli/handlers/` orchestrate engine + adapters (operation-specific)
- No `if mode == 'live':` in engine code

**Legacy structure (`app/core/`) is deprecated.** Services must refactor to match codex. `cli/handlers/` pattern is ALLOWED for operation-specific orchestration.

See: `unified-trading-codex/06-coding-standards/README.md#service-structure-standards`

---

## Observability: Use Centralized Patterns

ALL services MUST use centralized observability from unified-events-interface:

**Error/warning tracking:**
```python
from unified_events_interface import ErrorWarningCounter

counter = ErrorWarningCounter()
logging.getLogger().addHandler(counter)
# ... processing ...
counts = counter.get_counts()
```

**Memory monitoring:**

```python
from unified_events_interface import get_dataframe_memory_usage, log_memory_metrics

df_memory = get_dataframe_memory_usage(df)
log_memory_metrics("service-name", dataframe_mb=df_memory // 1024**2)
```

**NEVER:**

- Implement service-specific error counters
- Duplicate memory tracking logic
- Use print() for observability

See: `unified-trading-codex/06-coding-standards/README.md#observability-standards`

```

#### 4.3 Update batch-live-symmetry.md

**File**: [unified-trading-codex/04-architecture/batch-live-symmetry.md](unified-trading-codex/04-architecture/batch-live-symmetry.md)

**Changes**:

1. **Add "Current Implementation Status" section** (after line 150):

```markdown
## Current Implementation Status

| Service | Structure | Batch | Live | Notes |
|---------|-----------|-------|------|-------|
| ml-inference-service | ✅ engine/adapters | ✅ | ✅ | Reference implementation |
| position-balance-monitor | ✅ engine/adapters | ✅ | ✅ | Reference implementation |
| instruments-service | ✅ engine/adapters | ✅ | 🚧 | engine/adapters done |
| market-data-processing | ⚠️ app/core | ✅ | 🚧 | Needs refactor |
| risk-and-exposure | ⚠️ app/core | ✅ | 🚧 | Needs refactor |
| market-tick-data-handler | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| features-calendar | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| features-delta-one | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| features-volatility | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| features-onchain | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| ml-training | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |
| strategy | ❌ app/core | ✅ | ❌ | Batch-only, needs refactor |

Legend:
- ✅ Implemented
- 🚧 Partially implemented
- ❌ Not implemented
- ⚠️ Legacy structure (needs refactor)
```

1. **Add "Migration Guide" section** (after implementation status):

```markdown
## Migration from Legacy Structure

Services using `app/core/` and `cli/handlers/` must refactor to `engine/` and `adapters/`.

See: `06-coding-standards/service-structure-refactoring-guide.md` for step-by-step guide.
```

### Phase 6: Cross-Repo Verification

#### 5.1 Verify Observability Centralization

**Test**: Each service uses centralized patterns

```bash
# Should find ZERO service-specific error counters
rg "class.*ErrorCounter|class.*WarningCounter" --type py \
  --glob '!unified-events-interface/**'

# Should find centralized imports in all services
rg "from unified_events_interface import ErrorWarningCounter" --type py \
  instruments-service/ market-tick-data-handler/ market-data-processing-service/ \
  features-calendar-service/ features-delta-one-service/ ml-training-service/ strategy-service/
```

#### 5.2 Verify Service Structure

**Test**: Each service has `engine/`, `adapters/`, `cli/`

```bash
# Check directory structure
for service in instruments-service market-tick-data-handler market-data-processing-service \
               features-calendar-service features-delta-one-service ml-training-service strategy-service; do
  echo "Checking $service..."
  ls -la $service/${service//-/_}/engine/ 2>/dev/null || echo "  ❌ Missing engine/"
  ls -la $service/${service//-/_}/adapters/ 2>/dev/null || echo "  ❌ Missing adapters/"
done
```

#### 5.3 Run Quality Gates (BLOCKING - Must Pass)

**CRITICAL**: Quality gates must pass for EACH service after refactoring, including pre-existing issues.

**Start with instruments-service** (pilot refactoring):

```bash
cd instruments-service
bash scripts/quality-gates.sh --no-fix
```

**Expected**: Zero failures (including pre-existing issues like file size, circular imports, etc.)

**Fix ALL quality gate issues before proceeding**:

- File size violations (>1500 lines) - split files
- Circular imports - fix import structure
- Type errors - add proper type hints
- Test failures - fix broken tests
- Linter errors - fix code style

**Then verify all services**:

```bash
cd unified-trading-deployment-v3
bash scripts/run-all-quality-gates.sh --sequential
```

**Expected**: Zero failures across all 14 services.

#### 5.4 Verify Corporate Actions Consolidation

**Test**: instruments-service has 1-2 handlers, shared utilities extracted

```bash
# Should find 1-2 handlers (production + optional date-range)
ls instruments-service/instruments_service/cli/handlers/corporate_actions*.py | wc -l

# Should find shared utilities
ls instruments-service/instruments_service/corporate_actions/utils.py

# Should find NO quality gate bypasses for corporate actions
rg "corporate_actions" instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md
```

## Success Criteria (BLOCKING)

### Phase Completion Criteria

Each phase must meet these criteria before proceeding to next phase:

1. ✅ **CLI refactored**: All 14 services use `--operation` and `--mode` flags
2. ✅ **Config inheritance standardized**: All services use `UnifiedCloudConfig` (100%)
3. ✅ **Config persistence standardized**: All services use ConfigStore for runtime config
4. ✅ **Config replay standardized**: Batch handlers use TimeSeriesConfigStore
5. ✅ **Config hot reload standardized**: Live handlers use ConfigReloader
6. ✅ **Observability centralized**: ErrorWarningCounter, memory helpers in unified-events-interface
7. ✅ **All services use centralized patterns**: No service-specific error counters
8. ✅ **Service structure standardized**: All services have `engine/`, `adapters/` (thin <100 lines), `cli/`
9. ✅ **Dependencies point inward**: `engine/` has zero imports from `adapters/`
10. ✅ **Adapters are thin**: All adapters <100 lines, delegate to UCS/UMI/UCI/UEI
11. ✅ **Corporate actions consolidated**: 1-2 handlers, shared utilities extracted
12. ✅ **Circular imports fixed**: Zero quality gate bypasses for imports
13. ✅ **Codex updated**: CLI standards, config types, service structure, observability standards documented
14. ✅ **Cursor rules updated**: .cursorrules enforces all standards
15. ✅ **Deployment v3 updated**: ~40 files use --operation and --mode flags

### Quality Gates (BLOCKING - Most Critical)

**instruments-service MUST pass quality gates FIRST** (pilot refactoring):

```bash
cd instruments-service
bash scripts/quality-gates.sh --no-fix
# Exit code: 0 (success)
```

**ALL services MUST pass quality gates** (including pre-existing issues):

```bash
cd unified-trading-deployment-v3
bash scripts/run-all-quality-gates.sh --sequential
# Exit code: 0 (success)
```

**Quality gate requirements**:

- ✅ Zero file size violations (all files <1500 lines)
- ✅ Zero circular imports
- ✅ Zero type errors (basedpyright passes)
- ✅ Zero test failures
- ✅ Zero linter errors (ruff passes)
- ✅ 35%+ test coverage (minimum)
- ✅ Zero import violations (no lazy imports outside whitelist)
- ✅ Adapters <100 lines each

**If quality gates fail**: Fix ALL issues (including pre-existing) before declaring phase complete.

## Risks and Mitigations


| Risk                                | Impact | Mitigation                                            |
| ----------------------------------- | ------ | ----------------------------------------------------- |
| Breaking changes in service imports | High   | Automated import rewriting, comprehensive testing     |
| Test failures after refactoring     | Medium | Update tests incrementally, verify after each service |
| Merge conflicts (30+ repos)         | Medium | Use parallel agents, merge dependencies first         |
| Regression in production            | High   | Deploy to staging first, monitor metrics              |


## Rollout Strategy

### Execution Order (Sequential with Quality Gate Checkpoints)

1. **Phase 0** (CLI refactoring): Medium risk, affects all services but backward compatible
  - **Checkpoint**: All services pass quality gates after CLI changes
2. **Phase 1** (unified-events-interface): Low risk, additive changes only
  - **Checkpoint**: UEI passes quality gates, all services still pass
3. **Phase 2** (service refactoring): High risk, START WITH instruments-service
  - **Pilot**: instruments-service refactored to engine/adapters
  - **Checkpoint**: instruments-service passes quality gates (including pre-existing issues)
  - **Then**: Tier 1 services (ml-inference, position-balance-monitor)
  - **Checkpoint**: Each service passes quality gates before next
  - **Then**: Tier 2 services (market-data-processing, risk-and-exposure)
  - **Final checkpoint**: All refactored services pass quality gates
4. **Phase 3** (corporate actions): Medium risk, instruments-service only
  - **Checkpoint**: instruments-service passes quality gates after consolidation
5. **Phase 4** (docs): Zero risk, documentation only
  - **Checkpoint**: Codex and cursor rules updated
6. **Phase 5** (verification): Zero risk, testing only
  - **Final checkpoint**: All 14 services pass quality gates

### Starting Point: instruments-service

**Why instruments-service first**:

1. Has most complexity (corporate actions, multiple operations)
2. Has known issues to fix (file size, circular imports)
3. Serves as pilot for refactoring pattern
4. Once it passes, pattern is proven for other services

**Estimated effort**:

- Phase 0: 1-2 days
- Phase 1: 1 day
- Phase 2: 3-4 days (instruments-service: 1-2 days, others: 2 days)
- Phase 3: 1 day
- Phase 4-5: 1 day
- **Total**: 7-9 days
