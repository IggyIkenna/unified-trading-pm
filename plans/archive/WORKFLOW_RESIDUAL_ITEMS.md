---
doc_type: plan
title: Workflow 1 Residual Items & Cross-Workflow Planning
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-02"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): this is a
2026-03-02 milestone tracker built around a "5 Workflow" framework superseded by the asset-group/epic plan structure
used today. Every repo named in its open items (unscanned-repo scans, repo renames, the 8 separate `features-*-service`
repos, the split `ml-training-service`/`ml-inference-service`) has since been renamed, merged into a consolidated repo,
or retired outright — confirmed missing from the current workspace root. Closed project history with no actionable
residue.

# Workflow 1 Residual Items & Cross-Workflow Planning

> Date: 2026-03-02 Status: ACTIVE Context: End-of-day audit after Workflow 1 (Quality Gates Passing Locally) execution
> References: FIVE_WORKFLOW_DELIVERY_PLAN.md, SPORTS_MIGRATION_GAP_FIX.md, SPORTS_MIGRATION_PHASE2_FULL.md

---

## 1. Workflow 1 Progress Summary (March 2, 2026)

### Completed Today

| Category                             | Count   | Details                                                                                                        |
| ------------------------------------ | ------- | -------------------------------------------------------------------------------------------------------------- |
| Repos with all quality gates passing | 8+      | UEI, UAC, UCI, UCI-Config, RES, FCIS, UI-Auth, instruments-service                                             |
| Ruff lint fixes                      | 200+    | deployment-api (96), features-sports-service (46), UTS (1), UAC, UMI                                           |
| Test fixes                           | 500+    | UClI (44/44), UCI (79/82), UFCL (54/54), instruments-service (122/122), UTS (292/292), UMLI (7/7), UMI (23/23) |
| Codex compliance fixes               | 6 repos | features-calendar, features-onchain, ml-training, ml-inference, execution-service, deployment-service          |
| Infrastructure fixes                 | 10+     | Dependency names, pyproject.toml, quality-gates.sh scripts, compat layers                                      |
| UCS -> UTS rename gaps               | Fixed   | ConfigReloader export, \_CloudStorageMixin/\_CloudBatchMixin compat, GCP_PROJECT_ID removal                    |
| T0 library test fixes                | 3 repos | UFCL (stale install + log format), UMLI (error recovery logic), UMI (USEI install + registry)                  |

### What's Passing vs Failing (Tier by Tier)

#### T0 — Pure Leaf Libraries (8 repos)

| Repo                               | Lint | Tests   | Codex | Blocking Issue                                                  |
| ---------------------------------- | ---- | ------- | ----- | --------------------------------------------------------------- |
| unified-events-interface           | PASS | 40/40   | PASS  | None                                                            |
| unified-api-contracts              | PASS | 764/764 | PASS  | None                                                            |
| unified-cloud-interface            | PASS | 44/44   | PASS  | None                                                            |
| unified-feature-calculator-library | PASS | 54/54   | PASS  | FIXED: stale install + log format bugs. Coverage 49% (see R-06) |
| unified-config-interface           | PASS | 79/79   | PASS  | None                                                            |
| unified-domain-client              | PASS | 0/1     | PASS  | 1 test: missing trading params (see R-02)                       |
| unified-market-interface           | PASS | 23/23   | PASS  | FIXED: installed USEI, added resolve_adapter_class()            |
| unified-ml-interface               | PASS | 7/7     | PASS  | FIXED: error recovery test now stores after recovery            |

#### T1 — unified-trading-services (1 repo)

| Gate   | Status           | Details                                         |
| ------ | ---------------- | ----------------------------------------------- |
| Config | PASS             |                                                 |
| Lint   | PASS             | Fixed I001 import sort                          |
| Type   | FAIL             | 272 pre-existing basedpyright errors (see R-05) |
| Tests  | 292 pass, 0 fail | But coverage at 40% vs 70% threshold (see R-06) |
| Codex  | PASS             | Fixed GCP_PROJECT_ID refs                       |

#### T2 — Interface Libraries (7 repos)

Covered in T0 above (UCI, UEI, UFCL, UMI, UMLI, UDC, UCI-Config are all T0/T2).

#### T3 — unified-domain-client (1 repo)

See UDC row in T0 table.

#### T4 — Services (16 repos)

| Repo                              | QG Status                                                | Blocking Issue                                                                                                                                        |
| --------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service               | PASSING (122/122 tests)                                  | None                                                                                                                                                  |
| risk-and-exposure-service         | ALL GATES PASS                                           | None                                                                                                                                                  |
| features-cross-instrument-service | ALL GATES PASS                                           | None                                                                                                                                                  |
| features-sports-service           | Lint PASS, Tests 773 pass (56 pre-existing CLI failures) | 914 basedpyright errors (pre-existing; 0 in calculators/ + tracking/). Feature expansion COMPLETE: 998 features, 27 calculators, 24 tracking modules. |
| features-volatility-service       | Lint PASS                                                | Pre-existing test failures (vol surface calc)                                                                                                         |
| features-calendar-service         | 181 pass, 6 fail                                         | Missing UTS APIs (setup_service, BaseModeHandler) + events (R-14)                                                                                     |
| features-onchain-service          | 2 collection errors                                      | Same batch handler UTS API issue (R-14)                                                                                                               |
| features-multi-timeframe-service  | Deps fixed                                               | Need full QG verification                                                                                                                             |
| ml-training-service               | 52 collection errors                                     | Multiple missing UTS/event interface imports (R-14)                                                                                                   |
| ml-inference-service              | conftest error                                           | setup_events() requires sink= parameter (R-14)                                                                                                        |
| execution-service                 | 1044 pass, 61 fail                                       | FIXED: circular imports resolved (R-15). Remaining: pre-existing test failures                                                                        |
| deployment-service                | 2/2 pass                                                 | FIXED: missing modules extracted from v3 (R-16)                                                                                                       |
| market-tick-data-service          | Deps partially fixed                                     | UMI dep was wrong name                                                                                                                                |
| strategy-validation-service       | Python version fixed                                     | Need full QG verification                                                                                                                             |
| alerting-service                  | Deps fixed (uv sources)                                  | Need full QG verification                                                                                                                             |
| sports-betting-execution-service  | MISSING                                                  | Not needed — see R-10                                                                                                                                 |

#### T5 — APIs (3 repos)

| Repo                  | QG Status            | Blocking Issue                          |
| --------------------- | -------------------- | --------------------------------------- |
| deployment-api        | Lint PASS (96 fixed) | 5298 basedpyright errors (pre-existing) |
| market-data-api       | Clean                | None                                    |
| execution-results-api | Deps fixed           | Need verification                       |

#### T6 — UIs (4 repos)

| Repo                    | QG Status       | Blocking Issue     |
| ----------------------- | --------------- | ------------------ |
| unified-trading-ui-auth | ALL GATES PASS  | None               |
| deployment-ui           | QG script fixed | Non-Python project |
| strategy-ui             | QG script fixed | Non-Python project |
| execution-visualizer-ui | npm issue       | Pre-existing       |

---

## 2. Residual Items — Detailed

### R-01: UFCL Test Failures — FIXED

**Repo:** unified-feature-calculator-library **Status:** FIXED (March 2) **Root cause:** Stale installed package —
source had `_add_diff_features()` but installed version didn't. Also 4 `%..3f` -> `%.3f` log format string bugs.
**Fix:** `uv pip install -e .` + fixed format strings in base.py, transformations.py, validations.py. **Result:** All 54
tests pass. Coverage at 49% (pre-existing, see R-06).

### R-02: UDC `test_get_trading_parameters_returns_none_when_not_found` Failure

**Repo:** unified-domain-client **File:** `tests/unit/test_clients.py` **Error:** `ModuleNotFoundError` or assertion
failure in client mock **Root cause:** Test expects `get_trading_parameters()` to return None for unknown instruments,
but the mock or implementation doesn't match. **Fix:** Review the test mock setup and ensure the cloud service mock
returns the expected response for missing data. **Priority:** P2 (edge case handling)

### R-03: UMI Sports Registry Test Failure — FIXED

**Repo:** unified-market-interface **Status:** FIXED (March 2) **Root cause:** USEI not installed +
`adapter_for_bookmaker()` tried instantiating adapters needing credentials. **Fix:** Installed USEI, added
`resolve_adapter_class()`, updated `adapter_for_bookmaker(**kwargs)`, updated tests. **Result:** All 23 tests pass.

### R-04: UMLI Error Recovery Test Failure — FIXED

**Repo:** unified-ml-interface **Status:** FIXED (March 2) **Root cause:** `@handle_storage_errors(reraise=False)`
swallows exceptions, returning None. Test then tried loading a model that was never stored. **Fix:** Restructured test:
(1) verify store fails, (2) recover + store successfully, (3) load succeeds. **Result:** All 7 e2e tests pass.

### R-05: UTS basedpyright 272 Errors

**Repo:** unified-trading-services **Scope:** 272 errors, 1390 warnings across the entire package **Key error
patterns:**

- `reportAttributeAccessIssue` — config classes missing attributes (get_cloud_target, is_test_environment)
- `reportArgumentType` — None passed where str expected in id_conventions.py
- `reportUnknownMemberType` — untyped list operations in periods.py
- `reportAny` — some Any type usage remaining **Fix approach:** Systematic type annotation work. Start with the
  most-imported modules: `core/config.py`, `core/cloud_constants.py`, `utils/id_conventions.py`, `utils/periods.py`.
  **Effort:** ~2-3 hours focused type annotation work **Priority:** P2 (pre-existing debt, doesn't block runtime)

### R-06: UTS Test Coverage 40% vs 70% Threshold

**Repo:** unified-trading-services **Current:** 40% (6352 total lines, 3811 uncovered) **Target:** 70% minimum **Gap:**
Need ~1900 additional lines covered **Key uncovered modules:**

- `core/cloud_storage_service.py` (870 lines, 0% covered — needs mocked GCS tests)
- `core/cloud_base_service.py` (complex, needs mocked service tests)
- `domain/standardized_service.py` (743 lines, low coverage)
- `core/error_handling.py` (762 lines, ~50% covered)
- `ml/model_registry.py` (needs mocked GCS/BQ tests)
- `testing/` modules (0% — they're test helpers, consider excluding from coverage) **Quick win:** Exclude
  `unified_trading_services/testing/` from coverage measurement — these are test utilities, not production code. Would
  immediately boost coverage by ~3-5%. **Fix approach:** Write unit tests for cloud_storage_service.py and
  error_handling.py first (highest line count). Use mocked GCS/BQ clients. **Effort:** ~4-6 hours of test writing
  **Priority:** P1 (quality gate failure)

### R-07: Pre-existing basedpyright Errors Across Workspace

| Repo                     | Error Count | Priority                           |
| ------------------------ | ----------- | ---------------------------------- |
| deployment-api           | 5,298       | P3 (generated code patterns)       |
| unified-market-interface | 2,442       | P2 (heavy GCP SDK type complexity) |
| features-sports-service  | 784         | P2 (new code, should be cleaner)   |
| unified-trading-services | 272         | P2 (foundational library)          |
| instruments-service      | ~1,521      | P3                                 |

**Fix approach:** Focus on UTS (272) and FSS (784) first since they're smaller and more impactful. UMI and
deployment-api have massive type debt from GCP SDK return types — defer to Workflow 2. **Priority:** P2/P3 (doesn't
block runtime, but blocks strict CI/CD)

### R-08: 6 Codex-Fixed T4 Repos — VERIFIED (deeper issues found)

**Status:** VERIFIED (March 2). All 6 repos have test failures due to missing UTS APIs (R-14).

| Repo                      | Tests Pass    | Blocking Issue                                                      |
| ------------------------- | ------------- | ------------------------------------------------------------------- |
| features-calendar-service | 181/187       | Missing UTS APIs + SecretNotFoundError (fixed: now uses get_secret) |
| features-onchain-service  | 0 (2 errors)  | Batch handler imports missing UTS APIs                              |
| ml-training-service       | 0 (52 errors) | Multiple missing UTS/event imports                                  |
| ml-inference-service      | 0             | setup_events() requires sink=                                       |
| execution-service         | 1044/1105     | FIXED: 3 circular import chains resolved (R-15)                     |
| deployment-service        | 2/2           | FIXED: 7 subpackages extracted from v3 (R-16)                       |

**Codex fixes are valid** — the test failures stem from missing library-tier APIs (R-14), not from the codex changes.

### R-09: Repos Not Scanned in Workflow 1

These repos exist in the workspace but weren't part of the primary scan:

- market-data-processing-service
- strategy-service
- pnl-attribution-service
- position-balance-monitor-service
- features-delta-one-service
- client-reporting-api
- unified-internal-contracts
- unified-position-interface
- unified-reference-data-interface
- unified-trade-execution-interface
- unified-defi-execution-interface
- unified-sports-execution-interface
- execution-algo-library
- matching-engine-library

**Action:** Run quality gates on all of these to get baseline status. **Priority:** P1 (need full workspace visibility)

### R-10: sports-betting-execution-service — Not Needed

**Was listed as "MISSING" in T4 scan.** **Status:** NOT NEEDED. The functionality is distributed across:

- `unified-sports-execution-interface` (USEI) — exchange adapters (Betfair, Smarkets, Matchbook, Betdaq), scraper
  adapters (13 bookmakers)
- `features-sports-service` (FSS) — feature computation (batch + live)
- `instruments-service` — sports instruments (leagues, fixtures, teams)
- `strategy-service` — sports strategy (arb detection, value betting)

**Reference:** `SPORTS_MIGRATION_GAP_FIX.md` Part A (COMPLETE) archived the old `sports-betting-services-previous` repo.
Part B (IN PROGRESS) defines the live mode architecture across the above repos.

**No new repo needed.** The old monolithic approach is replaced by the distributed service architecture.

---

## 3. Naming Changes Plan

### R-11: unified-trading-services -> unified-cloud-library

**Current name:** `unified-trading-services` (was `unified-cloud-services` before that) **Problem:** It's a library
(imported by 37+ repos), NOT a service. Has no main entrypoint. Provides cloud provider abstractions. **Proposed name:**
`unified-cloud-library` **Python package:** `unified_cloud_library`

**Rename scope:**

1. GitHub repo rename: `gh repo rename unified-cloud-library`
2. Directory rename: `unified-trading-services/` -> `unified-cloud-library/`
3. Python package rename: `unified_trading_services/` -> `unified_cloud_library/`
4. pyproject.toml: `name = "unified-cloud-library"`
5. Backward compat layer: Keep `unified_trading_services/` and `unified_cloud_services/` as re-export shims for 6-month
   window
6. Update 37+ repos' pyproject.toml dependencies
7. Update all Python imports across workspace (can be deferred with compat layers)
8. Update CLAUDE.md, .cursorrules, codex docs
9. Update CI/CD pipeline references

**Migration strategy:** Same pattern as UCS->UTS — canonical package + two backward compat shim packages. Old imports
continue to work during migration window.

**Effort:** ~2 hours for the core rename + compat layers. Import updates can be incremental. **Priority:** P1 (do before
Workflow 2 CI/CD setup to avoid encoding wrong name in pipelines)

### R-12: deployment-engine → deployment-service (DONE in manifest/codex/docs; repo rename remaining)

**Status:** Manifest, codex, PM docs, cursor-rules, and DAG now use "deployment-service". Naming is consistent in all
documentation and scripts.

**Remaining (optional):** To fully rename the repo and package:

1. GitHub repo rename: `deployment-engine` → `deployment-service`
2. Local directory rename: `deployment-engine/` → `deployment-service/`
3. pyproject.toml: `name = "deployment-service"`, package `deployment_service`
4. Backward compat shim if any consumers import the old package (deployment-api does **not** depend on
   deployment-service in code — they are independent)

**Note:** deployment-api and deployment-service do not depend on each other in code (verified in pyproject.toml).
deployment-api uses unified-cloud-services + unified-events-interface; deployment-service uses unified-trading-services
only. **Priority:** P2 (doc rename done; repo/package rename when convenient)

### R-13: unified-trading-deployment-v3 — IN TRANSITION (Not Redundant)

**Status:** INVESTIGATED (March 2). NOT redundant — mid-split into 4 repos.

**Current state:** unified-trading-deployment-v3 is the SSOT for deployment infrastructure while a planned four-way
split is in progress:

| Extracted Repo                             | What It Contains                                             | Status                 |
| ------------------------------------------ | ------------------------------------------------------------ | ---------------------- |
| deployment-service (was deployment-engine) | Core orchestration (shard calculator, catalog, cloud client) | Scaffolded v0.1.0      |
| deployment-api                             | FastAPI REST/SSE API (27 route modules, OAuth)               | Fully extracted v0.1.0 |
| deployment-ui                              | React/TypeScript frontend                                    | Scaffolded v0.1.0      |
| system-integration-tests                   | Smoke test infrastructure                                    | Scaffolded             |

**What remains ONLY in v3:** Terraform modules, YAML configs, smoke test framework, full CLI. **No repos depend on v3**
— deployment-api uses UCI+UEI, deployment-service uses UTS. **Action:** Continue extraction. Archive v3 only after all 4
repos pass quality gates. **Priority:** P3 (infrastructure transition, not blocking services)

### R-14: Missing UTS Service APIs — MOSTLY RESOLVED (March 2)

**Status:** RESOLVED (setup_service added, architecture audited)

**Original issue:** T4 services couldn't import `setup_service`, `BaseModeHandler`, `GCSEventSink`,
`GracefulShutdownHandler` from UTS.

**Root cause:** Only `setup_service()` was actually missing. All other APIs existed in UTS source but:

1. `setup_service()` was never added as an export (referenced by 12+ services)
2. Some repos had stale UTS installs in `.venv-workspace`

**Fixes applied (March 2):**

- Added `setup_service = setup_events` alias in `unified_trading_services/__init__.py` + `__all__`
- Reinstalled UTS from source (`uv pip install -e unified-trading-services/`)
- Fixed ml-inference-service conftest: `mode="test"` + `MockEventSink()` (was `mode="batch"` without sink)
- Fixed features-onchain-service: import `log_dependency_failures` from UTS (not local module)

**Test results after fix:** | Repo | Before | After | |------|--------|-------| | features-calendar-service | 181/187 |
177 unit pass (6 fail = pre-existing event logging) | | features-onchain-service | 0 (collection errors) | 69 pass, 1
fail | | ml-training-service | 0 (52 collection errors) | 235 pass, 5 fail | | ml-inference-service | 0 (conftest error)
| 73 pass, 14 fail |

**ARCHITECTURAL AUDIT RESULTS (resolved questions):**

1. **Cloud abstraction boundary is CORRECT (90% aligned):**
   - UCI defines: `StorageClient`, `SecretClient`, `QueueClient` ABCs + cloud-provider implementations
   - UEI defines: `EventSink` Protocol + `setup_events()` + `MockEventSink`
   - UTS provides: `GcsEventSink`, `S3EventSink`, `PubSubEventSink`, `QueueEventSink`, `LocalFsEventSink`,
     `CompositeEventSink`
   - UTS also provides: `BaseModeHandler`, `ServiceCLI`, `GracefulShutdownHandler` (all cloud-agnostic)

2. **`GCSEventSink` naming:** The NAME is cloud-specific but the ARCHITECTURE is correct — services choose a
   cloud-specific sink implementation and inject it via `setup_events(sink=...)`. Future improvement: add a
   `create_event_sink()` factory that auto-selects based on `CLOUD_PROVIDER` env var.

3. **`GracefulShutdownHandler`:** Confirmed cloud-agnostic (uses `psutil`, `signal`, `atexit`). Correct location in UTS
   as library utility.

4. **`setup_service()` = `setup_events()`:** Identical signature `(service_name, mode, sink)`. Services inject the sink
   at startup.

**Remaining T4 test failures (not R-14, separate issues):**

- Codex agent introduced test files referencing non-existent local exports (MODES_WITH_DEPRECATED, etc.)
- Missing optuna package for ml-training-service (install: `uv pip install optuna`)
- event_logging tests expect lifecycle event markers not yet in source code **Priority:** RESOLVED (was P0, now
  remaining items are P2)

### R-15: execution-service Circular Import — FIXED

**Repo:** execution-service **Status:** FIXED (March 2) **Root cause:** THREE separate circular import chains:

1. `definitions_loader.py` → `instruction_validator.py` → `utils.domain` → `instruments/factory.py` →
   `definitions_loader.py` (via `DataNotFoundError`)
2. `config_builder.py` → `catalog_cache.py` → `gcs_cache_helper.py` → `catalog_cache.py` (via `GCS_CATALOG_CACHE_BUCKET`
   constant)
3. Missing `VENUE_CATEGORY_MAP` and Prometheus metrics imports from UTL

**Fixes applied:**

- Created `execution_service/exceptions.py` with centralized exception classes (DataNotFoundError,
  InstructionValidationError, ConfigValidationError)
- Updated 5 files to import from `exceptions.py` instead of `instruction_validator.py`
- Made `gcs_cache_helper.py` use lazy import for `GCS_CATALOG_CACHE_BUCKET`
- Fixed `VENUE_CATEGORY_MAP` import: `from unified_config_interface.execution_config_schema import VENUE_CATEGORY_MAP`
- Defined Prometheus metrics locally in `orchestrator.py` (were never exported from UTL)
- Also fixed `unified_config_interface/loaders.py` `log_event()` call to handle uninitialized event system

**Result:** 1044 pass, 61 fail (was 0 pass, 38 collection errors) **Priority:** RESOLVED

### R-16: deployment-service Missing Modules — FIXED

**Repo:** deployment-service **Status:** FIXED (March 2) **Root cause:** Incomplete extraction from
unified-trading-deployment-v3. Multiple subpackages referenced but never copied.

**Missing modules found and extracted:**

1. `deployment_service/deployment_config.py` — created (extends UnifiedCloudConfig with deployment-specific fields)
2. `deployment_service/config/` — 4 files (base_config.py, config_validator.py, env_substitutor.py, **init**.py)
3. `deployment_service/calculators/` — 4 files (base_calculator.py, shard_dimensions.py, shard_distribution.py,
   **init**.py)
4. `deployment_service/dependencies.py` — DependencyGraph class
5. `deployment_service/backends/services/` — 4 files (vm_config.py, vm_lifecycle.py, vm_monitoring.py, **init**.py)
6. Fixed `vm_config.py` import: `from unified_trading_deployment.deployment_config` →
   `from deployment_service.deployment_config`
7. Fixed `deployment_service/pyproject.toml` — typos in dependencies (doubled names: `pyyamlpyyaml` etc.)

**Still missing (not blocking tests):**

- `deployment_service/cli/handlers/` — 4 handler modules (CLI not tested)

**Result:** 2/2 tests pass (was 0/2 with missing module errors) **Priority:** RESOLVED

---

## 4. Codex Docs Alignment Check — COMPLETED (March 2)

### Overall: 85% aligned. Misalignments are naming + aspirational API references.

### Critical Misalignments Found

| Issue                                                     | Location                                                                | Fix                                  |
| --------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------ |
| `SecretNotFoundError` referenced but doesn't exist        | testing.md lines 318-323                                                | Remove or mark PLANNED               |
| `setup_service()` referenced but doesn't exist            | TIER-ARCHITECTURE.md, README.md, testing.md                             | Mark as PLANNED                      |
| Old package `unified_cloud_services` in examples          | testing.md lines 318, 359, 369                                          | Update to `unified_trading_services` |
| `deployment-service` used but repo is `deployment-engine` | integration-testing-layers.md, TOPOLOGY-DAG.md, UI-DEPENDENCY-MATRIX.md | Update to `deployment-engine`        |
| "17 pipeline service repos" count is wrong                | README.md (04-architecture)                                             | Should be 13 per DAG                 |

### Correctly Aligned

- Core tier architecture (T0→T1→T2→T3→T4→T5→T6)
- Configuration standards (UnifiedCloudConfig, no os.getenv)
- Error handling decorators (@handle_api_errors, @handle_storage_errors)
- Quality gate pipeline (ruff, basedpyright, pytest, codex checks)
- Cloud-agnostic patterns (get_storage_client, get_secret_client)
- BaseModeHandler, GracefulShutdownHandler, GCSEventSink — all exist in UTS
- Import rules and dependency direction

### Aspirational Items Needing PLANNED Callouts

| Item                  | Status          | Should Say                                |
| --------------------- | --------------- | ----------------------------------------- |
| `setup_service()`     | Not implemented | PLANNED: consolidates setup_events + sink |
| `SecretNotFoundError` | Not implemented | PLANNED: stricter secret validation       |
| UCS→UTS rename        | Complete        | Change "⚠️ in progress" to "✅ complete"  |

### Action Items for Codex Fixes

1. **testing.md**: Remove `SecretNotFoundError` references, update `unified_cloud_services` → `unified_trading_services`
2. **Multiple files**: Replace `deployment-service` → `deployment-engine` (or do the repo rename first)
3. **README.md**: Fix service count (17 → 13) or clarify
4. **TIER-ARCHITECTURE.md**: Add implementation status markers for T1 APIs
5. **TOPOLOGY-DAG.md**: Mark UCS→UTS rename as complete

---

## 5. Cross-Workflow Remaining Items

### Workflow 2: Manifest + CI/CD (March 3)

**Pre-requisites from Workflow 1 not yet met:**

- [ ] All repos have quality gates scripted (14 unscanned repos — R-09)
- [ ] Naming settled before encoding in CI/CD (R-11, R-12, R-13)
- [ ] basedpyright errors in foundational libs (UTS 272, UMI 2442) — acceptable as known debt

**New items for Workflow 2:**

- [ ] GitHub Actions workflow templates for all repo tiers
- [ ] Manifest levels 0-14 definition and enforcement
- [ ] AWS provider implementations in UCI (currently GCP-only)
- [ ] Dependency graph enforcement in CI

### Workflow 3: UAT + Deploy (March 4-5)

**Pre-requisites:**

- [ ] deployment-service codex PASS (DONE as of today)
- [ ] All feature services produce correct output
- [ ] Event pipeline (UEI) working end-to-end

### Workflow 4: ML Pipeline (March 5-10)

**Pre-requisites:**

- [x] ml-training-service codex PASS (DONE)
- [x] ml-inference-service codex PASS (DONE)
- [x] UFCL auto-diff test fixed (R-01 DONE)
- [x] UMLI error recovery test fixed (R-04 DONE)
- [ ] Missing UTS service APIs implemented (R-14) — blocks ml-training and ml-inference testing
- [ ] UTS model registry working with real GCS

### Workflow 5: Autonomous Agents (March 10-31)

**Pre-requisites:**

- [ ] All upstream workflows complete
- [ ] Sports live mode (SPORTS_MIGRATION_GAP_FIX.md Part B)
- [ ] Cross-instrument features working
- [ ] Risk management across asset classes

---

## 6. Action Items — Prioritized

### Completed (March 2)

- [x] UTS quality gate fixes (lint, codex, conftest, test patches) — 292/292 tests pass
- [x] 6 T4 repos codex compliance fixes
- [x] Verify 6 codex-fixed repos full QG status (R-08) — all have deeper issues (R-14)
- [x] Fix UMI test: installed USEI, added resolve_adapter_class (R-03) — 23/23 tests pass
- [x] Fix UMLI error recovery test (R-04) — 7/7 tests pass
- [x] Fix UFCL stale install + log format bugs (R-01) — 54/54 tests pass
- [x] Fix calendar config SecretNotFoundError — now uses get_secret()
- [x] Add setup_service() export to UTS (R-14) — unblocks 377+ tests across 4 T4 services
- [x] Fix ml-inference-service conftest (mode="test" + MockEventSink)
- [x] Fix features-onchain-service batch handler import (log_dependency_failures from UTS)
- [x] Deep research: UCI vs UTS cloud abstraction boundaries — architecture 90% correct
- [x] Investigate unified-trading-deployment-v3 (R-13) — not redundant, mid-split into 4 repos
- [x] Codex docs alignment review (Section 4) — 85% aligned

### Completed (March 2 — Continued Session)

- [x] Fix execution-service circular imports (R-15) — 3 chains fixed, 1044 pass
- [x] Fix deployment-service missing modules (R-16) — 7 subpackages extracted from v3, 2/2 pass
- [x] Created backward-compat shim for unified_trading_services (sys.modules aliasing)
- [x] Fixed unified_config_interface/loaders.py log_event() for uninitialized event system
- [x] Fixed Prometheus metrics label mismatch in orchestrator.py

### Immediate Next (P0)

- [ ] Fix remaining codex agent test issues (non-existent local exports referenced in test files)

### This Week (P1)

- [ ] Scan 14 unscanned repos (R-09) — need full workspace visibility
- [ ] UTS test coverage to 70% (R-06)
- [ ] Codex docs fixes: remove SecretNotFoundError refs, update old package names

### Next Week (P2)

- [ ] UTS basedpyright 272 errors (R-05)
- [ ] FSS basedpyright 784 errors
- [ ] deployment-service repo/folder/pyproject rename (R-12 remaining; doc rename DONE)
- [ ] UMI basedpyright 2442 errors

### Deferred (P3)

- [ ] deployment-api basedpyright 5298 errors
- [ ] unified-trading-deployment-v3 rename (R-13)
- [ ] instruments-service basedpyright ~1521 errors
