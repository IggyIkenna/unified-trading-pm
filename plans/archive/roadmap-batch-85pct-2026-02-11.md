> **Note:** Active task tracking has moved to `consolidated_remaining_work.plan.md`. This document retains historical
> context and completed-milestone records.

# Roadmap: Batch Production (49.0% → 85.0%)

**Current State:** 49.0% batch readiness  
**Target:** 85.0% batch readiness  
**Gap:** 36.0 percentage points  
**Last Updated:** 2026-02-11

---

## Executive Summary

This roadmap outlines the path from current 49% batch readiness to 85% production-ready state. Work is organized into
three phases prioritized by audit findings:

- **Phase 1 (P0):** Critical blockers that prevent production deployment
- **Phase 2 (P1):** High-priority issues that should be fixed before production
- **Phase 3 (P2):** Medium-priority improvements and quick wins

Program note:

- This roadmap is the audit-remediation lane and is tracked in the same PM system as new capability requests.
- Status lifecycle for all items: `pending -> in_progress -> ready_for_testing -> uat_accepted -> done`.
- Owner defaults are bootstrapped by policy and can be overridden per item.

Dual-cloud note:

- Batch milestone completion requires dual-cloud readiness criteria to be represented in codex and deployment checklist
  YAML gates where applicable.

---

## Phase 1: P0 Critical Blockers (Weeks 1-3)

**Objective:** Eliminate security risks and critical system failures that prevent production deployment.

**Estimated Completion:** 3 weeks  
**Risk Level:** HIGH (these issues block production deployment)

### 1.1 Remove Service Account Key Files (SEC-05)

**Priority:** P0  
**Status:** NOT_STARTED  
**Effort:** 16 hours (4 hours per step)

**Description:**  
Service account key file (`test-project-e35fb0ddafe2.json`) is committed to ALL 12 repos in git history. This is a
critical security vulnerability.

**Affected Services:** ALL (12/12)

- instruments-service
- market-tick-data-service
- market-data-processing-service
- features-delta-one-service
- features-calendar-service
- features-volatility-service
- features-onchain-service
- ml-inference-service
- ml-training-service
- strategy-service
- corporate-actions
- execution-service

**Work Items:**

1. **Remove from git history** (6 hours)
   - Use BFG Repo-Cleaner or `git filter-repo` to purge key file from all branches
   - Force push cleaned history (coordinate with team)
   - Verify removal with `git log --all --full-history -- "*e35fb0ddafe2.json"`

2. **Rotate compromised key** (2 hours)
   - Create new service account with proper IAM roles
   - Generate new key
   - Update GCP Secret Manager
   - Test all services with new credentials

3. **Update CI/CD** (4 hours)
   - Update GitHub Actions secrets
   - Update Cloud Build secret references
   - Verify all 12 repos build successfully

4. **Documentation** (4 hours)
   - Update `07-security/secrets-management.md` with incident learnings
   - Create runbook for emergency key rotation
   - Add pre-commit hook to block `.json` files

**Acceptance Criteria:**

- [ ] Key file absent from git history in all 12 repos
- [ ] Old service account key revoked in GCP IAM
- [ ] All services authenticate with new credentials
- [ ] CI/CD pipelines pass with new secrets
- [ ] Pre-commit hook prevents future commits

**Dependencies:** None

---

### 1.2 Replace Hardcoded Project ID (COD-20)

**Priority:** P0  
**Status:** NOT_STARTED  
**Effort:** 24 hours (2 hours per service)

**Description:**  
`test-project` is hardcoded in Dockerfiles, CI config, tests, and documentation across all 12 repos. This prevents
multi-environment deployment and violates cloud-agnostic principles.

**Affected Services:** ALL (12/12)

**Work Items:**

1. **Per-service cleanup** (18 hours, 1.5 hours each)
   - Find: `rg "test-project" --type py --type yaml --type dockerfile`
   - Replace with `config.gcp_project_id` or `config.project_id`
   - Update `Dockerfile` ENV vars
   - Update `cloudbuild.yaml` substitutions
   - Update tests to use `config.gcp_project_id` from fixtures

2. **Cross-cutting changes** (6 hours)
   - Update `unified-trading-services` config base class documentation
   - Update `unified-trading-deployment-v3` Terraform variables
   - Update codex examples in `06-coding-standards/`
   - Update audit checklist COD-20 verification steps

**Acceptance Criteria:**

- [ ] Zero instances of `test-project` in any repo (verified by `rg`)
- [ ] All services read project ID from `UnifiedCloudServicesConfig`
- [ ] Tests pass with mocked project ID
- [ ] Services deploy successfully to `dev` environment (different project)
- [ ] Documentation updated with correct patterns

**Dependencies:**

- Requires `UnifiedCloudServicesConfig` already adopted (completed in Stage 2)

---

### 1.3 Implement Position Reconciliation (WRK-03)

**Priority:** P0 for live, P1 for batch  
**Status:** PLANNED  
**Effort:** 40 hours

**Description:**  
No automated position reconciliation exists. Manual reconciliation is error-prone and not scalable for production.
Critical for live trading; important for batch backtesting to verify P&L accuracy.

**Affected Services:**

- execution-service (primary)
- strategy-service (position tracking)
- unified-trading-services (shared reconciliation logic)

**Work Items:**

1. **Design reconciliation service** (8 hours)
   - Define reconciliation frequency (EOD for batch, real-time for live)
   - Design multi-source reconciliation: internal position DB vs broker reports vs GCS audit logs
   - Define break notification workflow (Slack, PagerDuty, email)
   - Document in `08-workflows/position-reconciliation.md`

2. **Implement reconciliation engine** (16 hours)
   - Create `reconciliation_service/reconcile.py`
   - Build position aggregator from GCS event logs
   - Implement broker report parsers (per venue)
   - Build diff engine with tolerance thresholds
   - Add break categorization (missing trades, price discrepancies, quantity mismatches)

3. **Batch mode integration** (8 hours)
   - Add EOD reconciliation to batch pipeline DAG
   - Generate reconciliation report in `gs://positions/reconciliation/YYYY-MM-DD/`
   - Fail batch run if unreconciled breaks exceed threshold

4. **Testing** (8 hours)
   - Unit tests: synthetic positions with known breaks
   - Integration tests: mock broker API responses
   - E2E test: full batch run with reconciliation
   - Regression test: historical batch runs should reconcile

**Acceptance Criteria:**

- [ ] Reconciliation runs automatically EOD for batch backtests
- [ ] Reports stored in GCS with standardized schema
- [ ] Breaks detected and categorized correctly (100% accuracy on test fixtures)
- [ ] Batch pipeline fails if breaks exceed 0.01% of notional
- [ ] Documentation complete in `08-workflows/`

**Dependencies:**

- Requires position tracking in execution-service (already exists)
- Requires GCS event logs (WRK-05, covered in Phase 2)

---

### 1.4 Data Catalogue (BATCH-03)

**Priority:** P0  
**Status:** PLANNED  
**Effort:** 24 hours

**Description:**  
No central data catalogue exists. Engineers manually discover datasets in GCS. This blocks pipeline dependency
verification and causes data discovery friction.

**Affected Services:** ALL (data producers and consumers)

**Work Items:**

1. **Design catalogue schema** (6 hours)
   - Define metadata fields: dataset name, schema, partition keys, update frequency, owner, dependencies
   - Choose catalogue storage: BigQuery table vs GCS JSON vs Dataplex
   - Design registration workflow: automatic (on GCS write) vs manual (in CI)
   - Document in `02-data/data-catalogue.md`

2. **Implement catalogue service** (10 hours)
   - Create `data-catalogue-service/` in `unified-trading-services`
   - Build schema registration API
   - Build schema discovery API
   - Add automatic registration to `publish_dataframe()` in StandardizedDomainCloudService
   - Create CLI tool for manual queries: `ucs-catalogue list|describe`

3. **Backfill existing datasets** (4 hours)
   - Run catalogue registration for all existing GCS paths
   - Verify metadata correctness with per-service schema owners

4. **Testing** (4 hours)
   - Unit tests: schema registration and discovery
   - Integration tests: publish → catalogue → discover
   - E2E test: full pipeline with catalogue lookups

**Acceptance Criteria:**

- [ ] All existing datasets registered in catalogue
- [ ] New datasets automatically registered on publish
- [ ] CLI tool lists all datasets with metadata
- [ ] Schema evolution tracked (added/removed columns)
- [ ] Documentation complete in `02-data/`

**Dependencies:**

- Requires `StandardizedDomainCloudService` publish interface (DAT-19, covered in Phase 2)

---

### 1.5 Verify Pipeline Dependency Chain (BATCH-04)

**Priority:** P0  
**Status:** PLANNED  
**Effort:** 16 hours

**Description:**  
No end-to-end verification of pipeline dependency chain. Services may start before upstream data is ready, causing
silent failures or stale data reads.

**Affected Services:** ALL pipeline services (10 of 12, excluding client-facing services)

**Work Items:**

1. **Document dependency DAG** (4 hours)
   - Create `04-architecture/batch/dependency-dag.md`
   - List per-service: upstream dependencies, downstream consumers, trigger mechanism
   - Identify circular dependencies (should be zero)
   - Add mermaid graph visualization

2. **Implement DATA_READY event system** (6 hours)
   - Add `DATA_READY` event to lifecycle events (`03-observability/lifecycle-events.md`)
   - Update all services to emit `DATA_READY` after successful GCS write
   - Create `wait_for_upstream()` helper in `unified-trading-services`
   - Add timeout and retry logic

3. **Add dependency checks to services** (4 hours)
   - Update batch entry points to call `wait_for_upstream()` before processing
   - Fail fast if upstream data missing after timeout
   - Log dependency wait times for observability

4. **Testing** (2 hours)
   - Integration test: chain of 3 services with DATA_READY events
   - Test failure case: timeout if upstream never completes
   - Verify no deadlocks in DAG

**Acceptance Criteria:**

- [ ] Dependency DAG documented with mermaid diagram
- [ ] All services emit DATA_READY events
- [ ] Services wait for upstream dependencies before processing
- [ ] E2E batch run completes without manual intervention
- [ ] Logs show dependency wait times

**Dependencies:**

- Requires event logging (OBS-05, covered in Phase 2)

---

## Phase 1 Summary

| Work Item                        | Effort (hours) | Affected Services                   | Risk if Skipped                          |
| -------------------------------- | -------------- | ----------------------------------- | ---------------------------------------- |
| SEC-05: Remove key files         | 16             | ALL (12/12)                         | Production security breach               |
| COD-20: Remove hardcoded project | 24             | ALL (12/12)                         | Cannot deploy to other environments      |
| WRK-03: Position reconciliation  | 40             | execution-service, strategy-service | Undetected P&L errors                    |
| BATCH-03: Data catalogue         | 24             | ALL (10/10 pipeline)                | Manual data discovery, fragile pipelines |
| BATCH-04: Dependency chain       | 16             | ALL (10/10 pipeline)                | Race conditions, stale data              |
| **Total**                        | **120 hours**  |                                     |                                          |

**Target Completion:** 3 weeks with 1 FTE (40 hours/week)

---

## Phase 2: P1 High Priority (Weeks 4-7)

**Objective:** Fix high-priority issues that create operational risk or hinder development velocity.

**Estimated Completion:** 4 weeks  
**Risk Level:** MEDIUM (production possible but risky)

### 2.1 Add log_event() Calls (OBS-05, OBS-07, OBS-08)

**Priority:** P1  
**Status:** PARTIAL (test files exist but source code missing calls)  
**Effort:** 24 hours (8 hours per service)

**Description:**  
3 services have `test_event_logging.py` but zero `log_event()` calls in source code. This breaks lifecycle observability
and violates 3-tier event logging standard.

**Affected Services:**

- market-tick-data-service (worst offender)
- features-delta-one-service
- ml-inference-service

**Work Items (per service):**

1. **Add lifecycle events** (4 hours)
   - Add `log_event("STARTED")` to service entry point
   - Add `log_event("DATA_READY", details={...})` after successful output
   - Add `log_event("STOPPED")` to graceful shutdown
   - Add `log_event("FAILED", details={...})` to exception handlers

2. **Add resource monitoring** (2 hours)
   - Call `setup_cloud_logging(enable_resource_monitoring=True)` at startup
   - Verify CPU/memory metrics appear in Cloud Monitoring

3. **Update tests** (2 hours)
   - Verify test_event_logging.py expectations match actual calls
   - Add integration test: run service and verify events in Cloud Logging

**Acceptance Criteria (per service):**

- [ ] All 11 lifecycle events present in source code
- [ ] `test_event_logging.py` passes
- [ ] Integration test verifies events logged to Cloud Logging
- [ ] Resource monitoring enabled

**Total Effort:** 24 hours (3 services × 8 hours)

---

### 2.2 Remove Try-Except Import Fallbacks (COD-24)

**Priority:** P1  
**Status:** FAILING (all re-audited services)  
**Effort:** 12 hours (2 hours per service)

**Description:**  
All 6 re-audited services have try-except import fallbacks (e.g., `try: import lightgbm except: lightgbm = None`). This
creates silent degradation when optional dependencies are missing, leading to runtime failures hours into execution.

**Affected Services:**

- instruments-service
- market-tick-data-service
- market-data-processing-service
- features-delta-one-service
- ml-inference-service
- strategy-service
- Likely also in the 6 not-yet-re-audited services

**Work Items:**

1. **Per-service cleanup** (1 hour each)
   - Find: `rg "except.*ImportError" --type py`
   - Remove try-except wrapper
   - If dependency is truly optional, document in README when it's needed
   - If dependency is required, add to `pyproject.toml` [core] deps

2. **Add dependency validation** (6 hours)
   - Create `check-dependencies.sh` script for each service
   - Run in CI before tests
   - Fail loudly if required imports missing

**Acceptance Criteria:**

- [ ] Zero try-except import fallbacks in all services (verified by `rg`)
- [ ] All required dependencies in `pyproject.toml`
- [ ] CI validates dependencies before running tests
- [ ] Services fail fast at startup if imports missing

**Total Effort:** 12 hours

---

### 2.3 Replace print() with logger (COD-08)

**Priority:** P1  
**Status:** FAILING (multiple services)  
**Effort:** 16 hours

**Description:**  
210+ `print()` statements in execution-service alone. `print()` produces unstructured output that doesn't integrate with
Cloud Logging severity levels, filtering, or structured fields.

**Affected Services:**

- execution-service (210+ prints, worst offender)
- market-tick-data-service (moderate)
- market-data-processing-service (moderate)

**Work Items:**

1. **Execution-services cleanup** (10 hours)
   - Find: `rg "print\(" --type py execution-service/`
   - Replace with appropriate log level: `logger.info()`, `logger.debug()`, `logger.warning()`
   - Convert f-strings to structured logging: `logger.info("Order placed", extra={"order_id": order_id})`
   - Test output in Cloud Logging console

2. **Other services cleanup** (4 hours)
   - Market-tick-data-handler: replace ~30 print statements
   - Market-data-processing-service: replace ~20 print statements

3. **Add pre-commit hook** (2 hours)
   - Block new `print()` statements (except in test fixtures)
   - Update `.pre-commit-config.yaml` with custom hook

**Acceptance Criteria:**

- [ ] Zero `print()` statements in production code (verified by `rg`, except tests)
- [ ] Logs appear in Cloud Logging with correct severity
- [ ] Pre-commit hook prevents new print() statements
- [ ] Documentation updated in `03-observability/README.md`

**Total Effort:** 16 hours

---

### 2.4 Add Missing .env.example (INF-03)

**Priority:** P1  
**Status:** FAILING  
**Effort:** 4 hours (2 hours per service)

**Description:**  
2 services missing `.env.example`, making it difficult for new developers to set up local environments.

**Affected Services:**

- features-delta-one-service
- strategy-service

**Work Items (per service):**

1. **Create .env.example** (1 hour)
   - List all env vars read by service
   - Add comments explaining purpose and expected format
   - Include example values (non-sensitive)

2. **Update README** (0.5 hours)
   - Add "Local Setup" section referencing `.env.example`
   - Document how to get actual values (GCP Secret Manager, team leads)

3. **Validate in CI** (0.5 hours)
   - Add step to verify `.env.example` exists
   - Compare with env vars actually read by code (detect drift)

**Acceptance Criteria (per service):**

- [ ] `.env.example` exists and is complete
- [ ] README updated with setup instructions
- [ ] CI validates `.env.example` presence

**Total Effort:** 4 hours

---

### 2.5 Move Imports to Module Level (COD-09)

**Priority:** P1  
**Status:** FAILING  
**Effort:** 8 hours

**Description:**  
Imports inside functions cause performance degradation (repeated import overhead) and hinder static analysis tools.

**Affected Services:**

- ml-training-service (worst offender)
- market-data-processing-service
- features-delta-one-service

**Work Items:**

1. **Per-service refactor** (6 hours, 2 hours each)
   - Find: `rg "^\s+import " --type py` (indented imports)
   - Move to top of file
   - Handle conditional imports (e.g., type checking): use `if TYPE_CHECKING:` block
   - Verify tests pass (imports may have hidden circular dependency issues)

2. **Add linter rule** (2 hours)
   - Configure ruff to flag imports inside functions
   - Add to `pyproject.toml` for all services
   - Verify in CI

**Acceptance Criteria:**

- [ ] All imports at module level (verified by `rg`)
- [ ] Ruff configured to prevent future violations
- [ ] Tests pass (no circular import issues)

**Total Effort:** 8 hours

---

### 2.6 Implement Normalized Publish/Subscribe (DAT-19, DAT-20)

**Priority:** P1  
**Status:** PLANNED  
**Effort:** 40 hours

**Description:**  
No service fully uses `StandardizedDomainCloudService` for publish/subscribe. Most services use direct GCS paths or
custom `publish_dataframe()` implementations. This causes schema drift, partition inconsistencies, and hinders
batch-live symmetry.

**Affected Services:** ALL (10/10 pipeline services)

**Work Items:**

1. **Enhance StandardizedDomainCloudService** (12 hours)
   - Add `publish_dataframe(df, dataset_name, partition_keys)` base method
   - Add `subscribe_dataframe(dataset_name, filters)` base method
   - Implement automatic schema validation (using `validate_timestamp_date_alignment()`)
   - Add automatic DATA_READY event emission
   - Integrate with data catalogue registration (BATCH-03)

2. **Per-service migration** (20 hours, ~2 hours per service)
   - Replace custom `publish_dataframe()` with inherited base method
   - Replace direct GCS reads with `subscribe_dataframe()`
   - Update tests to use new interface
   - Verify backward compatibility (old data still readable)

3. **Documentation** (4 hours)
   - Update `02-data/schema-governance.md` with publish/subscribe patterns
   - Update `02-data/subscription-model.md` with code examples
   - Update codex `06-coding-standards/README.md`

4. **Testing** (4 hours)
   - Integration test: publish → subscribe across 2 services
   - Test schema validation (reject invalid schemas)
   - Test partition alignment (reject misaligned timestamps)

**Acceptance Criteria:**

- [ ] All services inherit from StandardizedDomainCloudService
- [ ] All services use base class publish/subscribe methods
- [ ] Schema validation runs on every publish
- [ ] DATA_READY events emitted automatically
- [ ] Tests pass with new interface

**Total Effort:** 40 hours

---

## Phase 2 Summary

| Work Item                         | Effort (hours) | Affected Services | Benefit                                |
| --------------------------------- | -------------- | ----------------- | -------------------------------------- |
| OBS-05: Add log_event()           | 24             | 3 services        | Lifecycle observability                |
| COD-24: Remove try-except imports | 12             | 6+ services       | Fail fast on missing deps              |
| COD-08: Replace print()           | 16             | 3 services        | Structured logging                     |
| INF-03: Add .env.example          | 4              | 2 services        | Developer onboarding                   |
| COD-09: Move imports to top       | 8              | 3 services        | Performance, static analysis           |
| DAT-19/20: Normalized pub/sub     | 40             | 10 services       | Schema governance, batch-live symmetry |
| **Total**                         | **104 hours**  |                   |                                        |

**Target Completion:** 4 weeks with 1 FTE (26 hours/week)

---

## Phase 3: P2 Medium Priority + Quick Wins (Weeks 8-10)

**Objective:** Address technical debt and improve maintainability.

**Estimated Completion:** 3 weeks  
**Risk Level:** LOW (can defer to post-production)

### 3.1 Implement Batch-Live Symmetry (ARC-11)

**Priority:** P2  
**Status:** PLANNED  
**Effort:** 60 hours

**Description:**  
Most services are batch-only. Batch-live symmetry pattern (90% shared code, mode-specific logic isolated to 4 seams) not
yet implemented.

**Affected Services:**

- market-tick-data-service (high priority for live)
- market-data-processing-service (embedded package, medium priority)
- features-delta-one-service (high priority for live)
- features-volatility-service (medium priority)
- features-onchain-service (medium priority)
- ml-inference-service (high priority for live)
- strategy-service (high priority for live)

**Work Items:**

1. **Design reference implementation** (12 hours)
   - Update `04-architecture/batch-live-symmetry.md` with concrete code patterns
   - Design adapter interfaces for 4 seams: data source, data sink, persistence, trigger
   - Create example implementation in `market-tick-data-service`

2. **Per-service implementation** (40 hours, ~8 hours per 5 services)
   - Refactor service to use adapter pattern
   - Implement batch adapter (existing logic)
   - Implement live adapter (new logic)
   - Add `--mode batch|live` CLI flag
   - Update tests to run in both modes

3. **Testing** (8 hours)
   - Add mode-switching integration tests
   - Verify batch and live produce equivalent outputs (on same input data)
   - Add E2E test: live mode with simulated WebSocket

**Acceptance Criteria:**

- [ ] 5 services support `--mode batch|live`
- [ ] Mode-specific logic isolated to adapters (<10% of codebase)
- [ ] Tests pass in both modes
- [ ] Documentation complete

**Total Effort:** 60 hours (can be split across multiple engineers)

---

### 3.2 Add Regression Tests (COD-21)

**Priority:** P2  
**Status:** PARTIAL  
**Effort:** 16 hours

**Description:**  
No systematic regression testing. Known bugs may reoccur. Best practice: every bug fix gets a regression test named
`test_regression_{issue}_{description}`.

**Affected Services:** ALL (add regression tests for historical bugs)

**Work Items:**

1. **Audit historical issues** (4 hours)
   - Query GitHub closed issues with `label:bug`
   - Identify which have regression tests (search for `test_regression_`)
   - Create list of missing regression tests

2. **Write regression tests** (8 hours)
   - Per identified bug: write `test_regression_{issue_number}_{short_description}`
   - Use minimal fixtures (5-20 rows)
   - Verify test fails without the fix (revert, run test, re-apply fix)

3. **Document pattern** (2 hours)
   - Update `06-coding-standards/testing.md` with regression test guidelines
   - Add regression test template to issue templates

4. **Add CI check** (2 hours)
   - Verify every closed bug issue has corresponding regression test
   - Add to PR checklist

**Acceptance Criteria:**

- [ ] All historical bugs have regression tests
- [ ] New bug fixes include regression tests (enforced in PR template)
- [ ] Documentation updated

**Total Effort:** 16 hours

---

### 3.3 Split Large Files (COD-25)

**Priority:** P2  
**Status:** FAILING (multiple services)  
**Effort:** 40 hours

**Description:**  
Multiple services have files exceeding 1500-line guideline. Largest offenders:

- instruments-service: 5600+ line file
- market-data-processing-service: 1500+ line file (borderline, may be acceptable for centralized scripts)

**Work Items:**

1. **Instruments-service refactor** (20 hours)
   - Analyze 5600-line file structure
   - Split by Single Responsibility Principle: separate classes/functions into modules
   - Likely split: venue adapters, schema definitions, utility functions
   - Update imports in dependent files
   - Verify tests pass

2. **Market-data-processing refactor** (10 hours)
   - Split 1500-line file into processing pipeline stages
   - Separate normalization, aggregation, output logic

3. **Features-delta-one refactor** (6 hours)
   - Split 800-line file into feature calculation modules

4. **Add linter check** (4 hours)
   - Configure ruff to warn on files > 1500 lines
   - Add to CI (warning, not failure for now)

**Acceptance Criteria:**

- [ ] No files > 1500 lines (1500 is max for centralized scripts; aim for <500 for most modules)
- [ ] Tests pass after refactoring
- [ ] Linter warns on large files

**Total Effort:** 40 hours

---

### 3.4 Clean Up Wasteful Documentation (COD-19)

**Priority:** P2  
**Status:** FAILING  
**Effort:** 8 hours

**Description:**  
Multiple services have 10+ documentation files cluttering repos. Worst: features-delta-one with 14 files. Consolidate
into single README or move to codex.

**Affected Services:**

- features-delta-one-service (14 files)
- market-data-processing-service (10 files)
- strategy-service (8 files)

**Work Items:**

1. **Per-service consolidation** (6 hours, 2 hours each)
   - Audit existing doc files
   - Merge into single README or move architecture docs to codex
   - Delete redundant/outdated files
   - Update links in other services

2. **Add guideline** (2 hours)
   - Update `06-coding-standards/README.md`: "Max 3 doc files per service"
   - Document which docs belong in service vs codex

**Acceptance Criteria:**

- [ ] Each service has ≤3 doc files
- [ ] No redundant/outdated documentation
- [ ] Links updated

**Total Effort:** 8 hours

---

### 3.5 Add Type Hints to Public APIs (COD-23)

**Priority:** P3  
**Status:** PARTIAL  
**Effort:** 24 hours

**Description:**  
Type hints missing on many public API signatures. This hinders IDE autocomplete and refactoring safety.

**Affected Services:** ALL (prioritize shared libraries first)

**Work Items:**

1. **Unified-cloud-services type hints** (8 hours)
   - Add type hints to all public methods in StandardizedDomainCloudService
   - Add type hints to config classes
   - Add type hints to utility functions

2. **Per-service type hints** (12 hours, 1 hour per service)
   - Add type hints to main entry point function
   - Add type hints to public utility functions
   - No need for private functions or tests (diminishing returns)

3. **Add mypy check** (4 hours)
   - Configure mypy for each service
   - Add to CI (warning level, not strict)

**Acceptance Criteria:**

- [ ] All public APIs have type hints
- [ ] Mypy runs in CI (warning level)
- [ ] IDE autocomplete works

**Total Effort:** 24 hours

---

## Phase 3 Summary

| Work Item                   | Effort (hours) | Affected Services | Benefit                  |
| --------------------------- | -------------- | ----------------- | ------------------------ |
| ARC-11: Batch-live symmetry | 60             | 5 services        | Prepare for live trading |
| COD-21: Regression tests    | 16             | ALL               | Prevent bug recurrence   |
| COD-25: Split large files   | 40             | 3 services        | Maintainability          |
| COD-19: Clean up docs       | 8              | 3 services        | Reduce clutter           |
| COD-23: Type hints          | 24             | ALL               | IDE support, safety      |
| **Total**                   | **148 hours**  |                   |                          |

**Target Completion:** 3 weeks with 2 FTEs (24 hours/week each)

---

## Milestone: Batch 85% Ready

**Total Effort:** 372 hours (Phase 1: 120h, Phase 2: 104h, Phase 3: 148h)

**Timeline:**

- **Phase 1 (Weeks 1-3):** P0 critical blockers
- **Phase 2 (Weeks 4-7):** P1 high priority
- **Phase 3 (Weeks 8-10):** P2 medium priority

**Target Date:** 10 weeks from start (2.5 months with 1.5 FTE average)

**Success Metrics:**

- [ ] Batch readiness ≥85% on audit re-run
- [ ] All P0 items resolved (SEC-05, COD-20, WRK-03, BATCH-03, BATCH-04)
- [ ] All P1 items resolved (OBS-05, COD-24, COD-08, INF-03, COD-09, DAT-19/20)
- [ ] ≥50% of P2 items resolved (ARC-11, COD-21, COD-25)
- [ ] Zero high-severity security issues
- [ ] End-to-end batch pipeline runs successfully without manual intervention

---

## Risk Assessment

| Risk                                 | Likelihood | Impact   | Mitigation                                                             |
| ------------------------------------ | ---------- | -------- | ---------------------------------------------------------------------- |
| Key rotation breaks production       | Medium     | Critical | Test in dev environment first; coordinate with all engineers           |
| Refactoring introduces bugs          | Medium     | High     | Require 100% test coverage on refactored code; regression tests        |
| Phase 1 takes longer than 3 weeks    | High       | High     | Prioritize SEC-05 and COD-20; defer WRK-03 to Phase 2 if needed        |
| Batch-live symmetry scope creep      | Medium     | Medium   | Start with 1 reference implementation; other services can follow later |
| Missing dependencies discovered late | Low        | Medium   | Run `check-dependencies.sh` in CI early in Phase 2                     |

---

## Dependencies on Other Workstreams

- **unified-trading-services enhancements:** DAT-19/20 requires base class updates
- **unified-trading-deployment-v3:** Terraform must support multi-environment deployment (COD-20)
- **GCP IAM:** Need service account creation permissions (SEC-05)

---

## Success Criteria (Re-Audit Checklist)

After completing all phases, re-run audit to verify:

- [ ] SEC-05: PASS (no credential files)
- [ ] COD-20: PASS (no hardcoded project IDs)
- [ ] WRK-03: PASS (position reconciliation implemented)
- [ ] BATCH-03: PASS (data catalogue exists)
- [ ] BATCH-04: PASS (dependency chain verified)
- [ ] OBS-05: PASS (log_event in all services)
- [ ] COD-24: PASS (no try-except imports)
- [ ] COD-08: PASS (no print statements)
- [ ] INF-03: PASS (.env.example in all services)
- [ ] COD-09: PASS (imports at module level)
- [ ] DAT-19/20: PASS (normalized pub/sub)
- [ ] Overall batch readiness ≥85%

---

## Next Steps

1. **Immediate:** Review roadmap with engineering team
2. **Week 1:** Start Phase 1 work (SEC-05 key rotation)
3. **Week 3:** Re-assess timeline after Phase 1 completion
4. **Week 7:** Mid-point review; decide if Phase 3 items move to post-production
5. **Week 10:** Re-run audit to measure progress

**Owner:** Engineering Lead  
**Stakeholders:** All service owners, DevOps, Security
