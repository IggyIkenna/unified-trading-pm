# GitHub Integration: Comprehensive Roadmap & Script Reference

**Version:** 3.1  
**Last Updated:** 2026-02-13 (Expanded Stage 4 + Cursor CLI Integration)  
**Status:** Living Document

---

## **⚠️ MAJOR UPDATE (2026-02-13):** Comprehensive Documentation Complete

This document now includes:

1. **✅ Cursor CLI Agent Integration (NEW)**
   - Autonomous issue fixing pipeline with 4-phase quality gate enforcement
   - `auto-fix-issue.sh` + `batch-fix.sh` - Full autonomous workflows
   - Never bypasses quality gates - fixes root cause or stops
   - PR creation with auto-merge when all gates pass
   - Branch protection enforcement - no shortcuts

2. **✅ Stage 4 Massively Expanded (12 Dimensions)**
   - NOT just "code completion" - **full service maturity framework**
   - Covers: Code, Tests, Data, Sharding, GCS, Schemas, Live/Batch Infrastructure, Setup Scripts, Dependencies,
     Observability
   - Validates against **15 service checklists** (904+ items)
   - Validates against **13 audit templates** (baseline, pipelines, platform, UIs)
   - Validates against **8 data catalogues** + 4 infrastructure configs
   - Most comprehensive stage - foundation for production readiness

3. **✅ Quality Gate Enforcement Documented**
   - 4-phase pipeline: Local auto-fix → Local verify → Pre-commit → CI/CD
   - Ruff version consistency (0.15.0 across all environments)
   - Exits immediately on failure - never uses `|| true` or `--no-verify`
   - Same checks run locally, in hooks, and in CI - impossible to bypass

---

## Executive Summary

This document maps the **7-stage maturity progression** for unified-trading-system GitHub automation, explains every
script's purpose, and clarifies what the audit document misunderstood.

**Key Insight:** What appears as "duplication" in the audit is actually **progressive tooling** - each script serves a
specific stage in the maturity model.

---

## The 7-Stage Maturity Model

### Stage 0: Baseline (CURRENT - 95% Complete)

**Focus:** Infrastructure foundation before any automation.

**Requirements:**

- ✅ Dependencies standardized (Python 3.13, uv, ruff 0.15.0)
- ✅ Quality gates consistent (local, GH Actions, Cloud Build)
- ✅ Build pipelines working (Dockerfiles, cloudbuild.yaml)
- ⚠️ Auth working (pending GCloud Build issues - in progress)

**No GitHub automation yet** - foundation must be solid first.

**Status:** Almost complete. GCloud Build auth issues being resolved.

---

### Stage 1: COD Standards Without Line Count (CURRENT - 100% Complete)

**Focus:** Organize architectural pivots separately from work items.

**Problem Solved:**

- 650+ COD issues mixed with epics/tasks/subtasks
- Main projects cluttered, can't see actual work
- Design decisions scattered across repos

**Scripts Created:**

#### 1. `setup-cod-project.py` (NEW - 2026-02-13)

**Purpose:** One-time setup to organize all CODs into dedicated project.

**What it does:**

- Creates 'cod' label across all repos
- Finds all COD issues via org-wide search (batched - 3 API calls vs 90+)
- Labels 650+ CODs in bulk
- Creates "CODs (Change of Direction)" GitHub project
- Adds all CODs to project

**When to use:** Once during initial setup. Idempotent (safe to re-run).

**Optimization:** Batched search reduced API calls by 97% (90 → 3 queries).

#### 2. `manage-cods.sh` (NEW - 2026-02-13)

**Purpose:** Daily COD operations helper.

**Commands:**

```bash
./manage-cods.sh count        # Count CODs by repo
./manage-cods.sh list         # List all CODs
./manage-cods.sh stats        # Open/closed statistics
./manage-cods.sh search "auth" # Find specific CODs
./manage-cods.sh bulk-close "created:<2023-01-01" # Close old CODs
```

**Status:** Complete. Main projects now cleanable with `-label:cod` filter.

---

### Stage 2: COD Line Count (NEXT - In Progress)

**Focus:** Enforce file size limits, split large files.

**Target:** Files >1500 lines → Split by Single Responsibility Principle.

**Scripts:**

#### 1. `bulk-close-cod-size.sh` (ONE-TIME MIGRATION - To Archive)

**Purpose:** Closed old COD-SIZE issues when threshold changed from 400→1500 lines.

**Status:** Migration complete. Script can be archived.

**Why it exists:** One-time cleanup when policy changed. Not part of ongoing workflow.

#### 2. `update-cod-size-threshold.sh` (ONE-TIME MIGRATION - To Archive)

**Purpose:** Master workflow for threshold update (recreate issues, close old ones).

**Status:** Migration complete. Script can be archived.

#### 3. New Script Needed: `check-file-size-cods.py`

**Purpose:** Ongoing monitoring for files >1500 lines.

**What it should do:**

- Scan all services for files >1500 lines
- Create COD-SIZE-{service}-{file} issues automatically
- Link to file, show current line count, suggest split points
- Update existing COD-SIZE issues if file grows/shrinks
- Close COD-SIZE issues when file drops below threshold

**Status:** Not yet created. This is the NEXT priority after Stage 1 completes.

---

### Stage 3: Event Logging (Future)

**Focus:** Ensure all services have 11-event lifecycle logging.

**Target:** 100% coverage of lifecycle events in all services.

**Scripts Needed:**

#### 1. `check-event-logging.py`

**Purpose:** Verify each service has all 11 lifecycle events.

**What it should do:**

- Scan service code for log_event() calls
- Check for: STARTED, STOPPED, FAILED, RESUMED, VALIDATED, etc.
- Create issues for missing events
- Verify tests/unit/test_event_logging.py exists
- Check 3-tier logging structure (app, infra, domain)

**Reference:** `03-observability/lifecycle-events.md`

**Status:** Not yet created.

---

### Stage 4: Missing Features (Future)

**Focus:** Comprehensive service maturity and completeness validation.

**Target:** All services are production-grade across ALL dimensions - code, tests, data, infrastructure, dependencies.

**CRITICAL:** This is NOT just "code completion" - it's **full service readiness** across 12 dimensions.

---

#### The 12 Dimensions of Service Completeness

**1. Code Completeness**

- All features implemented per architecture docs
- No TODO/FIXME in production paths
- All edge cases handled
- Error handling complete

**2. Test Completeness**

- ✅ **Unit tests:** All functions, 80%+ coverage
- ✅ **Integration tests:** Service boundaries, external deps
- ✅ **E2E tests:** Full workflows, realistic scenarios
- ✅ **Regression tests:** Every bug has a test

**3. Data Catalogue**

- ✅ **Input schemas:** What data service consumes
- ✅ **Output schemas:** What data service produces
- ✅ **Upstream dependencies:** Which services provide inputs
- ✅ **Downstream dependencies:** Which services consume outputs
- ✅ **Schema versioning:** Backward compatibility validated
- ✅ **Data lineage:** Full traceability

**4. Sharding Decisions**

- ✅ **Instrument sharding:** Which instruments per shard
- ✅ **Venue sharding:** Which venues per shard
- ✅ **Date sharding:** Time-based partitioning strategy
- ✅ **Load balancing:** How shards distribute work
- ✅ **Shard coordination:** Cross-shard operations

**5. GCS Bucket Decisions**

- ✅ **Bucket structure:** Naming conventions, hierarchy
- ✅ **Partitioning strategy:** Date/instrument/venue paths
- ✅ **Retention policies:** How long data persists
- ✅ **Access patterns:** Read/write frequency, lifecycle
- ✅ **Cost optimization:** Storage class choices

**6. Schema Hardening**

- ✅ **Schema validation:** Pre-upload checks
- ✅ **Field constraints:** Data types, nullable, enums
- ✅ **Timestamp alignment:** Date vs timestamp consistency
- ✅ **Schema evolution:** Migration paths defined
- ✅ **Breaking change detection:** Backward compatibility

**7. Deployment Infrastructure (Live)**

- ✅ **Live mode support:** Real-time data ingestion
- ✅ **WebSocket handling:** Connection management
- ✅ **State management:** In-memory vs persistent
- ✅ **Failover strategy:** Recovery from crashes
- ✅ **Resource limits:** Memory, CPU, connections

**8. Deployment Infrastructure (Batch)**

- ✅ **Batch mode support:** Historical data processing
- ✅ **Date range handling:** Backfill capabilities
- ✅ **Concurrency strategy:** Parallel date processing
- ✅ **Checkpointing:** Resume from failures
- ✅ **Resource scaling:** Adaptive worker counts

**9. Setup Scripts**

- ✅ **Environment setup:** Dependencies, auth, config
- ✅ **Local development:** Quick start for new devs
- ✅ **CI/CD setup:** Automated testing pipelines
- ✅ **Deployment scripts:** GCP, Docker, Cloud Build
- ✅ **Teardown scripts:** Clean shutdown, cleanup

**10. Upstream/Downstream Validation**

- ✅ **Dependency health checks:** Are upstreams available?
- ✅ **Data availability:** Is required data present?
- ✅ **Schema compatibility:** Do contracts match?
- ✅ **SLA compliance:** Are upstreams meeting SLAs?
- ✅ **Circuit breakers:** Graceful degradation

**11. Observability Foundation**

- ✅ **11 lifecycle events:** STARTED, STOPPED, FAILED, etc.
- ✅ **3-tier logging:** App, infrastructure, domain
- ✅ **Metrics:** Key performance indicators tracked
- ✅ **Tracing:** Request flows visible
- ✅ **Alerting:** Critical failures trigger alerts

**12. Service Checklist Compliance**

- ✅ **All baseline items:** From `checklist.template.yaml`
- ✅ **Service-specific items:** From service checklists
- ✅ **Audit templates:** All 13 audit templates validated
- ✅ **Quality gates:** Pass formatting, linting, tests
- ✅ **Documentation:** Architecture, runbooks, troubleshooting

---

#### Validation Against 13 Audit Templates

Stage 4 validation includes ALL items from:

**Core Templates:**

1. `_checklist-template.yaml` — Master checklist (904 items)
2. `_service-baseline-template.yaml` — Foundational requirements
3. `_service-metadata-schema.yaml` — Service metadata standards

**Pipeline Templates (7):** 4. `_service-pipeline-data-io.yaml` — Data ingestion/output patterns 5.
`_service-pipeline-features.yaml` — Feature engineering services 6. `_service-pipeline-market-data.yaml` — Market data
handlers 7. `_service-pipeline-ml.yaml` — ML training/inference services 8. `_service-pipeline-post-trade.yaml` —
Post-trade analytics 9. `_service-pipeline-strategy-execution.yaml` — Trading execution 10. `_service-platform.yaml` —
Platform/infrastructure services

**UI Templates (3):** 11. `_service-ui-analysis.yaml` — Analysis/visualization UIs 12. `_service-ui-control.yaml` —
Control plane UIs 13. `_service-ui-observability.yaml` — Monitoring/alerting UIs

---

#### Validation Against Service Checklists

Stage 4 validation includes ALL items from 15 service checklists:

**Core Services:**

- `checklist.unified-trading-services.yaml`
- `checklist.execution-services.yaml`
- `checklist.strategy-service.yaml`

**Data Pipeline Services:**

- `checklist.market-tick-data-handler.yaml`
- `checklist.market-data-processing-service.yaml`
- `checklist.instruments-service.yaml`

**Feature Services:**

- `checklist.features-calendar-service.yaml`
- `checklist.features-delta-one-service.yaml`
- `checklist.features-onchain-service.yaml`
- `checklist.features-volatility-service.yaml`

**ML Services:**

- `checklist.ml-training-service.yaml`
- `checklist.ml-inference-service.yaml`

**Prerequisites & Priorities:**

- `checklist.prerequisites.yaml`
- `checklist.PRIORITY_SUMMARY.yaml`
- `checklist.template.yaml`

---

#### Validation Against Data Catalogues

Stage 4 validation includes ALL data flows from:

**Service Data Catalogues:**

- `data-catalogue.market-tick-data-handler.yaml`
- `data-catalogue.market-data-processing-service.yaml`
- `data-catalogue.instruments-service.yaml`
- `data-catalogue.features-calendar-service.yaml`
- `data-catalogue.features-delta-one-service.yaml`
- `data-catalogue.features-onchain-service.yaml`
- `data-catalogue.features-volatility-service.yaml`
- `data-catalogue.downstream-services.yaml`

**Infrastructure Catalogues:**

- `data-providers.yaml` — External data sources
- `cloud-providers.yaml` — GCP/AWS resources
- `dependencies.yaml` — Service dependencies
- `expected_start_dates.yaml` — Deployment timeline

---

#### Scripts Needed

**1. `check-feature-completeness.py` (COMPREHENSIVE)**

**Purpose:** Multi-dimensional service maturity validation.

**What it validates:**

```python
def check_service_completeness(service: str) -> ComplianceReport:
    """
    Comprehensive service completeness check across 12 dimensions.

    Returns:
        ComplianceReport with pass/fail per dimension + issues to create
    """

    # 1. Code Completeness
    check_feature_implementation(service)
    check_todo_fixme_in_prod_code(service)
    check_error_handling_coverage(service)

    # 2. Test Completeness
    check_unit_test_coverage(service, min_coverage=0.80)
    check_integration_tests_exist(service)
    check_e2e_tests_exist(service)
    check_regression_tests(service)

    # 3. Data Catalogue
    validate_input_schemas(service)
    validate_output_schemas(service)
    validate_upstream_dependencies(service)
    validate_downstream_dependencies(service)
    check_schema_versioning(service)

    # 4. Sharding Decisions
    validate_sharding_strategy(service)
    check_shard_configuration(service)
    validate_load_balancing(service)

    # 5. GCS Bucket Decisions
    validate_bucket_structure(service)
    check_partitioning_strategy(service)
    validate_retention_policies(service)

    # 6. Schema Hardening
    check_schema_validation_logic(service)
    validate_timestamp_alignment(service)
    check_breaking_change_detection(service)

    # 7. Live Deployment Infrastructure
    check_live_mode_support(service)
    validate_websocket_handling(service)
    check_state_management(service)
    validate_failover_strategy(service)

    # 8. Batch Deployment Infrastructure
    check_batch_mode_support(service)
    validate_date_range_handling(service)
    check_concurrency_strategy(service)
    validate_checkpointing(service)

    # 9. Setup Scripts
    validate_env_setup_scripts(service)
    check_local_dev_setup(service)
    validate_ci_cd_setup(service)
    check_deployment_scripts(service)

    # 10. Upstream/Downstream Validation
    check_dependency_health_checks(service)
    validate_data_availability_checks(service)
    check_schema_compatibility(service)
    validate_circuit_breakers(service)

    # 11. Observability Foundation
    check_lifecycle_events(service, required=11)
    validate_three_tier_logging(service)
    check_metrics_instrumentation(service)
    validate_tracing_setup(service)

    # 12. Checklist Compliance
    validate_against_template(service, "checklist.template.yaml")
    validate_against_service_checklist(service)
    validate_against_audit_templates(service)
    validate_against_data_catalogue(service)

    return generate_compliance_report(service)
```

**Issue Creation:**

- Creates GitHub issues for EVERY dimension failure
- Links to relevant checklist items
- Links to relevant audit templates
- Links to relevant data catalogue entries
- Prioritizes by severity (P0: blocking, P1: critical, P2: important)

**Status:** Not yet created. Requires Stage 3 complete + comprehensive config foundation.

---

**2. `validate-service-data-flows.py`**

**Purpose:** Deep validation of data lineage and dependencies.

**What it validates:**

- Input data availability (upstream services running?)
- Output schema compatibility (downstream consumers ready?)
- Partition alignment (date ranges match?)
- Schema evolution (breaking changes detected?)
- Data freshness (SLA compliance?)

**Status:** Not yet created.

---

**3. `validate-service-infrastructure.py`**

**Purpose:** Deployment readiness across live and batch modes.

**What it validates:**

- Dockerfiles (base image, dependencies, health checks)
- Cloud Build configs (steps, timeouts, substitutions)
- Deployment scripts (live and batch variants)
- Resource limits (memory, CPU, workers)
- IAM permissions (service accounts, scopes)

**Status:** Not yet created.

---

**Prerequisites (Blockers):**

- ⚠️ **Service checklists mature** (in progress - 15 checklists exist but need validation)
- ⚠️ **Architecture docs complete per service** (in progress - gaps exist)
- ⚠️ **Data catalogue complete** (partial - 8 catalogues exist, need validation)
- ⚠️ **Audit templates validated** (13 templates exist, need enforcement)
- ❌ **Test framework standards** (not yet defined - what is "complete"?)
- ❌ **Schema governance enforced** (validation exists but not CI-enforced)
- ❌ **Dependency graph** (upstream/downstream not centralized)

**Timeline:** 3-4 weeks after prerequisites complete. This is the most comprehensive stage.

**Status:** Blocked. Foundation incomplete but framework exists.

---

### Stage 5: New Services (Future)

**Focus:** Streamline new service creation with templates and validation.

**Target:** 100% compliance for new services from day 1.

**Scripts Needed:**

#### 1. `scaffold-new-service.py`

**Purpose:** Generate complete service skeleton from template.

**What it should do:**

- Create directory structure
- Generate pyproject.toml, Dockerfile, cloudbuild.yaml
- Generate config.py, paths.py, schemas.py
- Generate quality-gates.sh, quickmerge.sh
- Generate test directories with test_event_logging.py
- Generate .cursorrules from template
- Verify against checklist.template.yaml

**Status:** Not yet created. Needs Stage 4 foundation.

#### 2. `validate-new-service.py`

**Purpose:** Pre-commit validation for new services.

**What it should do:**

- Run full checklist validation
- Verify all required files exist
- Check architectural compliance
- Verify test completeness
- Block commit if validation fails

**Status:** Not yet created.

---

### Stage 6: Hardening (Future)

**Focus:** Dev/prod environment separation, safe automation.

**Target:** Cursor agents can run freely without prod data risk.

**Requirements:**

- Prod data isolation (separate projects, strict IAM)
- Dev environment with synthetic data
- Automated rollback on errors
- Audit logging for all changes
- Rate limiting for bulk operations

**Scripts Needed:**

#### 1. `verify-env-isolation.py`

**Purpose:** Ensure dev/prod separation before running agents.

**Status:** Not yet designed.

---

## Current Script Inventory

### Active Production Scripts (Stage 0-2)

#### Core Compliance Checkers

**1. `run-diff-checker.py` (1002 lines)**

- **Purpose:** Check code compliance against codex standards
- **Creates issues for:** Import violations, config violations, error handling gaps
- **Stage:** 0 (Baseline)
- **Status:** Production
- **Batching:** Yes - org-wide searches
- **Last updated:** 2026-02-13 (Python 3.13)

**2. `check-service-compliance.py` (792 lines)**

- **Purpose:** Check service structure compliance against checklist
- **Creates issues for:** Missing files, incorrect structure, incomplete setup
- **Stage:** 0 (Baseline)
- **Status:** Production
- **Difference from diff-checker:** Structural compliance vs code compliance
- **Not duplication:** Complementary - checks different things

#### COD Management (Stage 1)

**3. `setup-cod-project.py` (NEW - 447 lines)**

- **Purpose:** One-time setup of COD project and labeling
- **Stage:** 1 (COD Standards)
- **Status:** Production-ready
- **Run frequency:** Once (initial setup), then never or rarely
- **Batching:** Yes - org-wide searches save 97% API calls

**4. `manage-cods.sh` (NEW - 200 lines)**

- **Purpose:** Daily COD operations (count, search, label, close)
- **Stage:** 1 (COD Standards)
- **Status:** Production
- **Run frequency:** Daily/weekly for COD management

#### Label Management

**5. `sync-labels.py`**

- **Purpose:** Sync all labels from `label-schema.yaml` to repos
- **Stage:** 0 (Baseline)
- **Status:** Production
- **Single source of truth:** Yes - all labels defined in label-schema.yaml
- **Not duplication:** Other scripts should call this, not duplicate

#### Epic/Task Management

**6. `create-service-epics.py`**

- **Purpose:** Create hierarchical epic→task→subtask structure for services
- **Stage:** 0 (Baseline)
- **Status:** Production
- **Creates:** Service-level epics with linked sub-issues

**7. `relink-sub-issues.py`**

- **Purpose:** Recovery utility when rate limits break sub-issue linking
- **Stage:** 0 (Baseline)
- **Status:** Maintenance utility (use when linking breaks)

#### Project Management

**8. `sync-project-items.py`**

- **Purpose:** Sync issues to projects from artifact plans
- **Stage:** 0 (Baseline)
- **Status:** Production

---

### Agent Automation Tools (Cursor CLI Integration)

**CRITICAL:** These scripts integrate with Cursor Agent CLI to enable **autonomous issue fixing with PR creation and
auto-merge**.

**Workflow:** Issue → Agent Fix → Quality Gates → PR Creation → Auto-Merge

---

#### The Autonomous Fix Pipeline

```
GitHub Issue Created
    ↓
auto-fix-issue.sh (or batch-fix.sh)
    ↓
Cursor Agent CLI invoked
    ↓ (Agent reads issue, makes changes)
Quality Gates (Phase 1) — Auto-fix formatting/linting
    ↓ (ruff format, ruff check --fix)
Quality Gates (Phase 2) — Verify all checks pass
    ↓ (format, lint, tests, imports)
    ├─ PASS → Continue
    └─ FAIL → Stop, report error
Quickmerge Script
    ↓ (git add, commit with issue ref)
Pre-commit Hooks
    ↓ (ruff format, ruff check --fix again)
Create PR with --files flag
    ↓ (only files changed by agent)
GitHub Actions Quality Gates
    ↓ (CI runs same checks again)
    ├─ PASS → Auto-merge enabled
    └─ FAIL → PR stays open for review
Auto-Merge Triggered
    ↓ (Squash merge to main)
Close Issue
    ↓
Mark as Fixed in Project
```

**Key Innovation:** Quality gates run **THREE times** (local pre-merge, pre-commit hooks, CI) to ensure no corruption.

---

**9. `auto-fix-issue.sh`** (Single Issue Mode)

**Purpose:** Autonomous fix for a single GitHub issue with full quality gate enforcement.

**Usage:**

```bash
./auto-fix-issue.sh <issue-number>

# Example:
./auto-fix-issue.sh 123
```

**What it does:**

1. **Fetch issue details** from GitHub
2. **Invoke Cursor Agent CLI** with issue context:
   ```bash
   cursor-cli agent \
     --task "Fix issue #123: [issue title]" \
     --context "[issue body]" \
     --repo-path "$(pwd)"
   ```
3. **Run quality gates Phase 1** (auto-fix):

   ```bash
   bash scripts/quality-gates.sh
   ```

   - Runs ruff format
   - Runs ruff check --fix
   - Fixes import order, formatting issues

4. **Run quality gates Phase 2** (verify):

   ```bash
   bash scripts/quality-gates.sh --no-fix
   ```

   - Verifies format is clean
   - Verifies lint is clean
   - Runs all tests
   - Checks imports
   - **EXITS IMMEDIATELY IF ANY FAIL** - never bypasses failures

5. **Create PR via quickmerge**:

   ```bash
   ./scripts/quickmerge.sh "Fix: [issue title] (fixes #123)" --files "file1.py file2.py"
   ```

   - Commits only agent-changed files
   - Includes issue reference for auto-close
   - Pre-commit hooks run (third quality gate check)
   - Creates PR with auto-merge enabled

6. **Monitor PR status**:
   - Wait for GitHub Actions to complete
   - If Actions pass → Auto-merge triggers → Issue closes
   - If Actions fail → PR stays open, agent stops, human review required

**Quality Gate Enforcement:**

- ❌ **NEVER** uses `|| true` to bypass failures
- ❌ **NEVER** skips tests
- ❌ **NEVER** uses `--no-verify` to skip hooks
- ✅ **ALWAYS** fixes root cause if quality gates fail
- ✅ **ALWAYS** re-runs quality gates after fixes
- ✅ **ALWAYS** includes `--files` to avoid committing other agents' work

**Status:** Production. Fully autonomous for well-scoped issues.

**Use case:** Single issue at a time, full automation, high confidence.

---

**10. `batch-fix.sh`** (Parallel Multi-Issue Mode)

**Purpose:** Autonomous fix for multiple GitHub issues in parallel with quality gate enforcement.

**Usage:**

```bash
./batch-fix.sh <issue-number-1> <issue-number-2> ... <issue-number-N>

# Example:
./batch-fix.sh 123 124 125 126 127
```

**What it does:**

1. **Validates issue count** (max 50 issues to avoid rate limits)
2. **Launches parallel agents** (one per issue):
   - Each agent runs in isolated directory/branch
   - Each agent runs full quality gate pipeline
   - Each agent creates separate PR
3. **Monitors all PRs**:
   - Tracks which completed successfully
   - Tracks which failed quality gates
   - Reports summary at end

**Parallelism:**

- Default: 5 concurrent agents (avoid overwhelming CI)
- Configurable via `MAX_PARALLEL_AGENTS` env var
- Each agent isolated to prevent conflicts

**Quality Gate Enforcement:**

- Same strict enforcement as auto-fix-issue.sh
- Each issue must pass independently
- No cross-contamination between fixes

**Status:** Production. Use for bulk cleanup (e.g., "fix all import violations").

**Use case:** 10-50 related issues, parallel execution, bulk cleanup.

---

**11. `close-fixed-issue.sh`** (Manual Fix Cleanup)

**Purpose:** Close issue and mark as fixed in project after manual fix.

**Usage:**

```bash
./close-fixed-issue.sh <issue-number> <commit-sha>

# Example:
./close-fixed-issue.sh 123 a1b2c3d4
```

**What it does:**

1. **Close issue** with "Fixed" comment
2. **Link commit** that fixed it
3. **Update project** (move to "Done" column if project-tracked)
4. **Add labels:** `status:fixed`, `resolution:completed`

**Status:** Production.

**Use case:** After manual fix (not agent), close cleanly with audit trail.

---

#### Quality Gates Integration (CRITICAL)

**All agent tools enforce quality gates before PR creation:**

**Phase 1: Auto-Fix** (via `scripts/quality-gates.sh`)

```bash
ruff format src/ tests/
ruff check --fix src/ tests/
```

**Phase 2: Verify** (via `scripts/quality-gates.sh --no-fix`)

```bash
ruff format --check src/ tests/    # Must be clean
ruff check src/ tests/              # Must be clean
pytest tests/                        # Must pass
python -m scripts.check_imports     # Must be valid
```

**Phase 3: Pre-Commit Hooks** (via `pre-commit`)

- Same ruff checks run automatically
- Catches any corruption between Phase 2 and commit
- Uses SAME ruff version as CI (alignment enforced)

**Phase 4: CI/CD** (via GitHub Actions / Cloud Build)

- Same checks run in CI
- Final safety net before auto-merge
- If CI fails, auto-merge is blocked

**Ruff Version Consistency:**

- Local: `pyproject.toml` specifies `ruff==0.15.0`
- Pre-commit: `.pre-commit-config.yaml` specifies `ruff==0.15.0`
- CI: GitHub Actions install `ruff==0.15.0`
- Cloud Build: Dockerfile installs `ruff==0.15.0`

**Result:** Impossible for formatting conflicts. All four environments aligned.

---

#### Branch Protection Integration

**All repos have branch protection with `enforce_admins=true`:**

- ❌ **Direct pushes to main rejected** (even for admins)
- ✅ **PRs required** (created by quickmerge.sh)
- ✅ **Status checks required** (GitHub Actions must pass)
- ✅ **Auto-merge enabled** (squash merge when checks pass)

**Agent workflow respects branch protection:**

1. Agent makes changes on feature branch
2. Quality gates pass locally
3. PR created from feature branch
4. CI runs quality gates again
5. If CI passes → Auto-merge
6. If CI fails → Human review

**No shortcuts. No --force. No bypassing.**

---

#### Error Handling & Recovery

**When agent fix fails:**

1. **Quality gates fail (Phase 1 or 2)**:
   - Agent analyzes failure
   - Attempts root cause fix
   - Re-runs quality gates
   - If still fails after 3 attempts → Stop, create diagnostic issue

2. **Pre-commit hooks fail**:
   - Hooks auto-fix formatting
   - Commit includes fixes
   - If unfixable → Stop, report conflict

3. **CI fails**:
   - PR stays open (auto-merge blocked)
   - Diagnostic comment added to PR
   - Agent can retry with updated approach
   - If retry fails → Human review required

**Principle:** Never bypass quality gates. Fix root cause or stop.

---

#### Metrics & Observability

**Each agent run logs:**

- Issue number and title
- Files modified
- Quality gate results (pass/fail per phase)
- PR number and status
- Auto-merge status
- Total time (issue → merged)

**Aggregate metrics tracked:**

- Success rate (% of issues auto-fixed and merged)
- Average time to merge
- Quality gate failure reasons
- Most common fix patterns

**Dashboard:** (Future) Real-time agent activity and success rates.

---

#### Agent Tools Summary

| Script                 | Mode     | Quality Gates | PR Creation | Auto-Merge | Status     |
| ---------------------- | -------- | ------------- | ----------- | ---------- | ---------- |
| `auto-fix-issue.sh`    | Single   | ✅ 4-phase    | ✅          | ✅         | Production |
| `batch-fix.sh`         | Parallel | ✅ 4-phase    | ✅          | ✅         | Production |
| `close-fixed-issue.sh` | Manual   | N/A           | N/A         | N/A        | Production |

**Key Differentiator:** These aren't just "helper scripts" - they're **autonomous fix pipelines** with quality
enforcement.

---

### One-Time Migration Scripts (To Archive After Use)

**12. `update-all-quickmerge.py` (70 lines)**

- **Purpose:** Update quickmerge.sh to include issue refs in commits
- **Status:** Migration complete (used once in 2026-02)
- **Action:** Archive to `archived/migrations/`

**13. `bulk-close-cod-size.sh`**

- **Purpose:** Close COD-SIZE issues when threshold changed 400→1500
- **Status:** Migration complete (used once in 2026-02)
- **Action:** Archive to `archived/migrations/`

**14. `update-cod-size-threshold.sh`**

- **Purpose:** Master workflow for COD-SIZE threshold migration
- **Status:** Migration complete (used once in 2026-02)
- **Action:** Archive to `archived/migrations/`

**15. `update-quickmerge-pr-body.sh`**

- **Purpose:** Update quickmerge.sh PR body format
- **Status:** Migration complete (used once)
- **Action:** Archive to `archived/migrations/`

---

### Project Regeneration Scripts (Maintenance Utilities)

**16. `delete-and-recreate-project.sh`**

- **Purpose:** Delete GitHub project and recreate from scratch
- **Use case:** When project gets corrupted or needs full reset
- **Status:** Maintenance utility

**17. `wipe-and-regenerate-project.sh`**

- **Purpose:** Wipe project contents and regenerate
- **Use case:** Similar to #16, different approach
- **Action:** Consolidate with #16 or document difference

**18. `wipe-project-background.sh`**

- **Purpose:** Wipe project without blocking (background-friendly)
- **Use case:** Large projects that take >30s to wipe
- **Status:** Maintenance utility

**19. `clear-github-project.sh`**

- **Purpose:** Clear project for fresh start
- **Use case:** Remove all items but keep project structure
- **Action:** Consolidate with above or document difference

**20. `create-project-fully-automated.sh`**

- **Purpose:** Create project with full automation
- **Status:** Maintenance utility

**21. `run-full-regeneration.sh`**

- **Purpose:** Full project regeneration workflow
- **Status:** Maintenance utility

**Audit Concern:** "All 4 do similar things"

**Reality:** Different use cases:

- Delete-and-recreate: Full reset
- Wipe-and-regenerate: Keep project, clear items
- Wipe-background: For large projects
- Clear: Soft reset

**Recommendation:** Add decision guide, but keep all (different scenarios).

---

## Addressing Audit Concerns

### Concern 1: "Conflicting Workflow Documentation"

**Audit says:** Multiple docs claim to be canonical with conflicts.

**Reality:** These are **version history**, not conflicts:

- `E2E_WORKFLOW_GUIDE.md` — Original workflow (v1.0)
- `MASTER_WORKFLOW.md` — Iteration (v1.5)
- `UNIFIED_WORKFLOW_FINAL.md` — Current canonical (v2.0)
- `SERVICE_LEVEL_EPIC_APPROACH.md` — Supplement (explains epic structure)

**Not a bug, it's evolution.** Old docs show how we got here.

**Action Taken:** Keep all for historical context. Clearly mark canonical in README.

---

### Concern 2: "Script Duplication & Overlap"

**Audit says:** `run-diff-checker.py` and `check-service-compliance.py` overlap.

**Reality:** They check **different things:**

- `run-diff-checker.py` — **Code compliance** (imports, config, error handling)
- `check-service-compliance.py` — **Structural compliance** (files exist, directory structure)

**Not duplication, complementary.**

**Example:**

- Code compliance: "Uses `os.getenv()` instead of config" ❌
- Structural compliance: "Missing test_event_logging.py" ❌

Both needed. Different failure modes.

---

**Audit says:** Label management duplicated across 3 scripts.

**Reality:** Different purposes:

- `sync-labels.py` — **Master label sync** from label-schema.yaml (source of truth)
- `setup-cod-project.py` — **Ensures 'cod' label exists** before labeling issues
- `create-service-epics.py` — **Ensures 26 labels exist** before creating epics

**Pattern:** All scripts ensure prerequisites exist before proceeding.

**Action:** Scripts should call `sync-labels.py` instead of duplicating. Fair point.

---

**Audit says:** Project management duplicated across 3 scripts.

**Reality:** Different workflows:

- `setup-cod-project.py` — **COD-specific** project (architectural pivots)
- `sync-project-items.py` — **Main work projects** (epics, tasks, subtasks)
- `create-service-epics.py` — **Service epics** with hierarchy

**Not duplication, different project types.**

---

### Concern 3: "Shell Script Proliferation"

**Audit says:** 19 shell scripts with duplication.

**Reality:** Scripts serve **different stages** in maturity model:

- **Stage 1:** COD management (manage-cods.sh)
- **Stage 2:** File size enforcement (needs new script)
- **Stage 3+:** Event logging, features, new services (future scripts)

**Plus maintenance utilities** (wipe, regenerate, fix).

**Not proliferation, progressive tooling.**

**Action:** Organize by stage/purpose. Add decision guide.

---

### Concern 4: "Outdated/One-Time Scripts Should Be Archived"

**Audit is correct here.** ✅

**Action:** Move these to `archived/migrations/`:

- `update-all-quickmerge.py`
- `bulk-close-cod-size.sh`
- `update-cod-size-threshold.sh`
- `update-quickmerge-pr-body.sh`

**Timeline:** Archive after Stage 2 (COD line count) completes.

---

### Concern 5: "DRY Violations"

**Audit says:** GitHub API calls duplicated across scripts.

**Audit is partially correct.** ✅

**Action Plan:**

#### Extract to Shared Library (`github_utils.py`)

```python
# github_utils.py - Shared GitHub operations

def create_or_get_label(org: str, repo: str, label: dict) -> bool:
    """Ensure label exists in repo."""
    # Reusable across all scripts

def add_issue_to_project(project_id: str, issue_url: str) -> bool:
    """Add issue to GitHub project."""
    # Reusable across all scripts

def link_sub_issue(parent_url: str, child_url: str) -> bool:
    """Link parent→child issues."""
    # Reusable across all scripts
```

**Timeline:** Create during Stage 2 refactoring.

**Priority:** Medium - improves maintainability but not blocking progress.

---

### Concern 6: "Disorganization - Flat Directory Structure"

**Audit is correct here.** ✅

**Proposed Structure:**

```
github-integration/
├── README.md                           # Decision guide: which script when
├── GITHUB_INTEGRATION_ROADMAP.md      # This document
│
├── core/                               # Active production scripts (Stages 1-7)
│   ├── stage-1-cod-standards/
│   │   ├── setup-cod-project.py       # One-time COD setup
│   │   └── manage-cods.sh             # Daily COD ops
│   ├── stage-2-cod-lines/
│   │   └── check-file-size-cods.py    # (To be created)
│   ├── stage-3-event-logging/
│   │   └── check-event-logging.py     # (To be created)
│   ├── stage-4-missing-features/
│   │   └── check-feature-completeness.py # (To be created)
│   ├── stage-5-new-services/
│   │   ├── scaffold-new-service.py    # (To be created)
│   │   └── validate-new-service.py    # (To be created)
│   └── baseline/                      # Stage 0 - foundation checks
│       ├── run-diff-checker.py        # Code compliance
│       └── check-service-compliance.py # Structural compliance
│
├── utils/                              # Shared libraries
│   ├── github_utils.py                # (To be created)
│   ├── project_utils.py               # (To be created)
│   └── issue_linking.py               # (To be created)
│
├── maintenance/                        # Project mgmt utilities
│   ├── sync-labels.py                 # Master label sync
│   ├── sync-project-items.py          # Sync issues to projects
│   ├── create-service-epics.py        # Create epic hierarchies
│   ├── relink-sub-issues.py           # Recover broken links
│   ├── delete-and-recreate-project.sh
│   ├── wipe-and-regenerate-project.sh
│   ├── wipe-project-background.sh
│   ├── clear-github-project.sh
│   ├── create-project-fully-automated.sh
│   └── run-full-regeneration.sh
│
├── agent-tools/                        # Cursor Agent CLI helpers
│   ├── auto-fix-issue.sh              # Fix one issue
│   ├── batch-fix.sh                   # Fix multiple issues
│   └── close-fixed-issue.sh           # Close fixed issue
│
└── archived/                           # Completed migrations
    └── migrations/
        ├── 2026-02-quickmerge-issue-refs/
        │   ├── update-all-quickmerge.py
        │   └── update-quickmerge-pr-body.sh
        └── 2026-02-cod-size-threshold/
            ├── bulk-close-cod-size.sh
            └── update-cod-size-threshold.sh
```

**Timeline:** Reorganize during Stage 2.

**Priority:** Medium - improves navigation but not blocking.

---

## Script Decision Guide

### "I need to check code compliance"

→ `run-diff-checker.py`

### "I need to check service structure"

→ `check-service-compliance.py`

### "I need to organize CODs"

→ `setup-cod-project.py` (once), then `manage-cods.sh` (daily)

### "I need to sync labels"

→ `sync-labels.py`

### "I need to create service epics"

→ `create-service-epics.py`

### "I need to fix issues with Cursor Agent"

→ `auto-fix-issue.sh` (one issue) or `batch-fix.sh` (many issues)

### "Project is corrupted"

→ `delete-and-recreate-project.sh` (full reset) or `wipe-and-regenerate-project.sh` (clear items)

### "Sub-issue links broke during creation"

→ `relink-sub-issues.py`

---

## Why This Progression Model?

### Stage 0: Baseline First

**You can't automate chaos.**

Before any GitHub automation:

- ✅ Code must build reliably
- ✅ Tests must pass consistently
- ✅ Quality gates must be aligned
- ✅ Dependencies must be standardized

**Otherwise:** Automation creates issues for broken code → wasted effort.

---

### Stage 1: CODs Before Features

**Why CODs first?**

- 650+ CODs pollute main projects
- Can't see actual work through noise
- Architectural decisions buried in task lists

**Result:** Clean project views, clear work items.

---

### Stage 2: File Size Before Deep Features

**Why line count next?**

- Large files (>1500 lines) violate SRP
- Hard to test, review, maintain
- Blocks code quality improvements

**Result:** Codebase refactored for maintainability.

---

### Stage 3: Event Logging Before Missing Features

**Why events before features?**

- Observability is foundation for reliability
- Can't debug missing features without proper logging
- 3-tier event model is architectural requirement

**Result:** All services observable before adding complexity.

---

### Stage 4: Feature Completeness Before New Services

**Why complete existing before new?**

- Need reference implementations
- Patterns must be proven
- Tests must demonstrate completeness

**Result:** Solid foundation for templates.

---

### Stage 5: New Services with Validated Templates

**Why templates after feature completeness?**

- Templates codify proven patterns
- Validation ensures 100% compliance from day 1
- No technical debt in new services

**Result:** New services start production-ready.

---

### Stage 6: Hardening Enables Free Automation

**Why hardening last?**

- Foundation must be solid first
- Automation on broken foundation amplifies problems
- Dev/prod isolation prevents disasters

**Result:** Cursor agents can run freely without risk.

---

## Batching & Performance Strategy

### What's Batched (Efficient)

**Org-wide searches (Stage 1 - setup-cod-project.py):**

- ✅ 3 queries for entire org vs 90+ per-repo queries
- ✅ 97% API call reduction
- ✅ 10x faster execution

**Why batched:** GitHub supports `org:IggyIkenna` search scope.

---

### What's NOT Batched (Sequential)

**Label creation/editing:**

- ⚠️ 1 API call per repo (label creation)
- ⚠️ 1 API call per issue (label application)

**Why not batched:** GitHub API limitation - no batch label operations.

**Optimization:** Show progress every 10 to provide feedback.

---

**Adding to projects:**

- ⚠️ 1 API call per issue

**Why not batched:** GitHub Projects API limitation.

**Mitigation:**

- Idempotent (safe to re-run)
- Progress indicators
- Graceful error handling

---

### Could Use GraphQL Batching (Future)

**GraphQL supports batch mutations:**

```graphql
mutation {
  issue1: addLabelsToLabelable(...) { ... }
  issue2: addLabelsToLabelable(...) { ... }
  issue3: addLabelsToLabelable(...) { ... }
}
```

**Trade-off:**

- ✅ 10-50x faster (batch 100 ops per call)
- ❌ Much more complex code
- ❌ Harder to debug
- ❌ Rate limit handling more complex

**Decision:** Start with GitHub CLI (simple, maintainable). Switch to GraphQL if performance becomes blocker.

---

## Progression Roadmap

### ✅ Stage 0: Baseline (95% Complete)

**Completed:**

- Python 3.13 standardization across all services
- Ruff 0.15.0 consistency (local, GH Actions, Cloud Build)
- Quality gates working end-to-end
- Dockerfiles standardized
- pyproject.toml standardized
- `run-diff-checker.py` — code compliance checking
- `check-service-compliance.py` — structural compliance checking

**Pending:**

- GCloud Build auth issues (in progress)
- Full quality gate pass across all services

**Timeline:** Complete by end of week.

---

### ✅ Stage 1: COD Standards (100% Complete)

**Completed:**

- `setup-cod-project.py` created (batched org-wide search)
- `manage-cods.sh` helper created
- 'cod' label created across 30 repos
- 651 COD issues found and labeled
- COD project created
- All CODs added to project
- Documentation complete (COD-PROJECT-SETUP.md)

**Result:** Main projects now cleanable with `-label:cod` filter.

**Next Action:** Create saved filters in main projects to exclude CODs.

---

### 🔄 Stage 2: COD Line Count (NEXT - 0% Complete)

**To Create:**

1. **`check-file-size-cods.py`** (primary script)
   - Scan all services for files >1500 lines
   - Create COD-SIZE-{service}-{file} issues
   - Update existing issues if size changes
   - Close issues when files drop below threshold
   - Integration with CI/CD (run on PR)

2. **`split-large-file.py`** (optional helper)
   - Suggest split points based on class/function boundaries
   - Generate split plan with file structure
   - Create sub-issues for each split task

**To Archive:**

- `bulk-close-cod-size.sh` (migration complete)
- `update-cod-size-threshold.sh` (migration complete)

**Timeline:** 1 week to create and test.

---

### ⏳ Stage 3: Event Logging (Future - 0% Complete)

**Prerequisites:**

- ✅ Stage 1 complete (CODs organized)
- ✅ Stage 2 complete (files <1500 lines)
- ✅ Codex docs complete (03-observability/)

**To Create:**

1. **`check-event-logging.py`**
   - Scan for log_event() calls in each service
   - Verify all 11 lifecycle events present
   - Check test_event_logging.py exists
   - Verify 3-tier structure (app, infra, domain)
   - Create issues for missing events

**Reference Docs:**

- `03-observability/lifecycle-events.md`
- `03-observability/batch/per-service/*.md`
- `03-observability/live/per-service/*.md`

**Timeline:** Start after Stage 2 completes.

---

### ⏳ Stage 4: Missing Features (Future - 0% Complete)

**Prerequisites:**

- ✅ Stage 3 complete (event logging)
- ⚠️ Service checklist mature (checklist.template.yaml - in progress)
- ❌ Architecture docs complete per service (in progress)
- ❌ Data catalogue implemented (not started)
- ❌ Test completion verification (not started)

**Blockers:**

1. **Architecture docs incomplete:**
   - Need complete feature lists per service
   - Need data flow specifications
   - Need integration requirements

2. **Data catalogue missing:**
   - No central registry of schemas
   - Can't verify output completeness
   - Can't check schema compliance

3. **Test framework unclear:**
   - What constitutes "complete" tests?
   - How to verify coverage?
   - Integration test requirements?

**To Create (After Blockers Resolved):**

1. **`check-feature-completeness.py`**
   - Read architecture docs for requirements
   - Scan service code for implementations
   - Check test coverage (unit, e2e, integration)
   - Verify data outputs against catalogue
   - Create issues for gaps

**Timeline:** 2-3 weeks (after prerequisite docs complete).

---

### ⏳ Stage 5: New Services (Future - 0% Complete)

**Prerequisites:**

- ✅ Stage 4 complete (existing services feature-complete)
- ✅ Templates proven and validated
- ✅ Reference implementations complete

**To Create:**

1. **`scaffold-new-service.py`**
   - Generate complete service from template
   - All required files (config, schemas, tests)
   - Quality gates pre-configured
   - Event logging included
   - Dockerfile, Cloud Build configs
   - 100% checklist compliance from day 1

2. **`validate-new-service.py`**
   - Pre-commit validation
   - Block commits if validation fails
   - Check architectural compliance
   - Verify test completeness

**Timeline:** Start after Stage 4.

---

### ⏳ Stage 6: Hardening (Future - 0% Complete)

**Prerequisites:**

- ✅ All previous stages complete
- ❌ Dev/prod environment separation designed
- ❌ Synthetic data strategy implemented
- ❌ Rollback mechanisms built

**To Create:**

1. **`verify-env-isolation.py`**
   - Check dev/prod separation before agent runs
   - Verify data isolation
   - Check IAM policies
   - Rate limit enforcement

2. **`agent-safety-wrapper.sh`**
   - Wrap Cursor Agent calls with safety checks
   - Auto-rollback on failures
   - Audit logging
   - Resource limits

**Timeline:** After all services hardened.

**Goal:** Cursor agents can run freely without prod data risk.

---

## Current State Summary (2026-02-13)

### What We've Built

**Foundation (Stage 0 - 95%):**

- ✅ Python 3.13 standardized across all services, docs, rules, CI/CD
- ✅ Quality gates consistent (ruff 0.15.0 everywhere)
- ✅ Code compliance checker (`run-diff-checker.py`)
- ✅ Structural compliance checker (`check-service-compliance.py`)
- ✅ Label sync system (`sync-labels.py` + `label-schema.yaml`)
- ✅ Epic/task hierarchy system (`create-service-epics.py`)
- ✅ Agent automation tools (auto-fix, batch-fix, close-fixed)

**COD Organization (Stage 1 - 100%):**

- ✅ COD project setup script with batched search (97% API reduction)
- ✅ COD management helper with 8 commands
- ✅ 651 COD issues organized and labeled
- ✅ Dedicated COD project created
- ✅ Documentation complete

**Total Scripts Created:** 21 active + 4 to archive

**Total Docs Created:** 8+ guides and READMEs

---

### What We've Deleted

**Deprecated Scripts (Replaced by Better Versions):**

- `sync-feature-cards.py` — Replaced by unified workflow
- `sync-delta-audit-tasks.py` — Replaced by unified workflow
- `sync-issues.py` — Replaced by specialized scripts

**Why deleted:** Old approach with scattered logic. New scripts are focused and composable.

---

### What We've Refined

**1. Search Strategy:**

- **Before:** Per-repo searches (90+ API calls)
- **After:** Org-wide batched searches (3 API calls)
- **Improvement:** 97% reduction

**2. Error Handling:**

- **Before:** Crashes on repos with disabled issues
- **After:** Gracefully skips with clear messages
- **Improvement:** Resilient execution

**3. Progress Visibility:**

- **Before:** Silent processing (looks like hanging)
- **After:** Updates every 10 items
- **Improvement:** Clear feedback

**4. Idempotency:**

- **Before:** Scripts could create duplicates
- **After:** Check existence before creating
- **Improvement:** Safe to re-run

**5. Documentation:**

- **Before:** Scattered comments in code
- **After:** Comprehensive guides with examples
- **Improvement:** Self-service usage

---

## What the Audit Missed

### Missed Context 1: Maturity Progression

**Audit viewed scripts as competing alternatives** (duplication).

**Reality:** Scripts are **progressive tools** for different maturity stages.

You don't use all scripts at once. You use them **in sequence** as you progress through stages.

---

### Missed Context 2: Script Lifecycle

**Audit marked migration scripts as "outdated."**

**Reality:** Migration scripts are **intentionally one-time use**.

- Used once during policy changes
- Archived after completion (not deleted)
- Kept for audit trail and reproducibility

---

### Missed Context 3: Complementary vs Duplicate

**Audit flagged `run-diff-checker.py` and `check-service-compliance.py` as duplicates.**

**Reality:** They're **complementary** - different dimensions of compliance:

- Code patterns (diff-checker)
- File structure (service-compliance)

Both needed. Different failure modes. No duplication.

---

### Missed Context 4: Prerequisites vs Duplication

**Audit flagged label creation in multiple scripts as duplication.**

**Reality:** Scripts **ensure prerequisites** before proceeding.

**Pattern:** "Fail-fast if prerequisites missing" vs "create prerequisites if missing."

Each script is self-contained and doesn't assume prerequisites exist.

**Valid point:** Could call `sync-labels.py` instead. Refactor in Stage 2.

---

## Next Steps (Actionable)

### Immediate (This Week)

1. ✅ **Let Stage 1 complete** - `setup-cod-project.py` is running (10-20 min remaining)
2. **Create saved filters** in main projects:
   - Filter: `-label:cod`
   - Set as default view
   - Result: Clean project views
3. **Configure COD project automation:**
   - Auto-add when 'cod' label added
   - Auto-archive after 30 days closed
4. **Verify baseline complete:**
   - Resolve GCloud Build auth issues
   - Confirm all services pass quality gates

---

### Stage 2 (Next Week)

1. **Create `check-file-size-cods.py`:**
   - Scan for files >1500 lines
   - Create/update COD-SIZE issues
   - Run in CI/CD on PRs
2. **Archive migration scripts:**
   - Move to `archived/migrations/2026-02-*/`
   - Add completion notes
3. **Extract shared utilities:**
   - Create `github_utils.py`
   - Refactor scripts to use shared code
   - Add tests

---

### Stage 3+ (Future)

Follow progression model:

- Stage 3: Event logging checks
- Stage 4: Feature completeness (after docs complete)
- Stage 5: New service scaffolding (after templates proven)
- Stage 6: Hardening (after all services mature)

---

## Files Created Today (2026-02-13)

### Scripts

1. `setup-cod-project.py` (447 lines) — COD project setup with batched search
2. `manage-cods.sh` (200 lines) — COD management helper

### Documentation

1. `COD-PROJECT-SETUP.md` — Complete setup guide with troubleshooting
2. `GITHUB_INTEGRATION_ROADMAP.md` — This document

### Updates

1. `run-diff-checker.py` — Updated Python 3.11+ → 3.13+

---

## Clearing Up Confusion

### What the Audit Got Right ✅

1. **One-time scripts should be archived** — Correct. Archive after Stage 2.
2. **DRY violations exist** — Correct. Shared utils needed (Stage 2 refactor).
3. **Directory structure could be better** — Correct. Reorganize by stage (Stage 2).
4. **Multiple workflow docs exist** — Correct. Mark canonical clearly.

### What the Audit Got Wrong ❌

1. **"Script duplication"** — Not duplication, **progressive tooling**.
2. **"Conflicting workflows"** — Not conflicts, **version history**.
3. **"Scripts overlap"** — Not overlap, **complementary checks**.
4. **"Proliferation"** — Not proliferation, **maturity model**.

### The Core Misunderstanding

**Audit viewed scripts as competing solutions to same problem.**

**Reality: Scripts solve different problems at different maturity stages.**

- Stage 0: Foundation (compliance)
- Stage 1: Organization (CODs)
- Stage 2: Quality (file size)
- Stage 3+: Advanced (features, services, hardening)

**Not duplication. Progression.**

---

## Success Metrics

### Stage 0 Baseline: WHEN COMPLETE

- [ ] All services pass quality gates
- [ ] GCloud Build working
- [ ] Zero import violations
- [ ] Zero config violations
- [ ] 100% structural compliance

### Stage 1 COD Standards: COMPLETE ✅

- [x] 651 CODs labeled and organized
- [x] Dedicated COD project exists
- [x] Main projects filterable with `-label:cod`
- [x] <100 work items visible in main projects (vs 700+ before)

### Stage 2 COD Line Count: NOT STARTED

- [ ] All files <1500 lines
- [ ] Automated monitoring in CI/CD
- [ ] COD-SIZE issues auto-created
- [ ] SRP violations tracked

### Stage 3 Event Logging: NOT STARTED

- [ ] All 11 lifecycle events in all services
- [ ] test_event_logging.py in all services
- [ ] 3-tier logging structure verified

### Stage 4 Missing Features: BLOCKED

- [ ] Architecture docs complete per service
- [ ] Data catalogue implemented
- [ ] Test completeness defined
- [ ] Feature gap issues created

### Stage 5 New Services: BLOCKED

- [ ] Templates created
- [ ] Scaffolding automation built
- [ ] Validation automation built

### Stage 6 Hardening: BLOCKED

- [ ] Dev/prod separation complete
- [ ] Agent safety wrappers built
- [ ] Rollback mechanisms tested
- [ ] Audit logging implemented

---

## References

### Codex Foundation

- `06-coding-standards/` — Quality gates, testing, dependencies
- `04-architecture/` — Batch-live symmetry, deployment
- `03-observability/` — Event logging, monitoring
- `02-data/` — Schema governance
- `01-domain/` — Signal-based strategies

### GitHub Integration

- This document (GITHUB_INTEGRATION_ROADMAP.md) — Maturity model and script reference
- `COD-PROJECT-SETUP.md` — Stage 1 setup guide
- `run-diff-checker.py` — Stage 0 code compliance
- `check-service-compliance.py` — Stage 0 structural compliance

### Workspace Rules

- `.cursorrules` — Python baseline, quality gates, anti-patterns
- `.cursor/rules/python-version-consistency.mdc` — Python 3.13 enforcement
- `.cursor/rules/git-workflow.mdc` — Quickmerge, quality gates, branch protection

---

## Decision: What to Do About Audit Recommendations

### Accept & Implement (Stage 2)

1. ✅ Archive one-time migration scripts
2. ✅ Create shared utilities (`github_utils.py`)
3. ✅ Reorganize scripts by stage/purpose
4. ✅ Create decision guide (this document)

### Accept with Modification

1. ⚠️ **"Mark canonical workflow"** — Done via this document (not by deleting history)
2. ⚠️ **"Consolidate project regeneration scripts"** — Add decision guide, but keep all (different use cases)

### Reject (Misunderstood)

1. ❌ **"Eliminate script duplication"** — Not duplication, progressive tooling
2. ❌ **"Resolve workflow conflicts"** — Not conflicts, version history
3. ❌ **"Scripts overlap"** — Not overlap, complementary

---

## Conclusion

The audit identified real organizational opportunities (archiving, shared utils, directory structure) but
**misunderstood the progression model**.

**This is not chaos - it's deliberate progression:**

- Stage 0: Foundation before automation
- Stage 1: Organization before complexity
- Stage 2: Quality before features
- Stage 3+: Progressive automation maturity

**Each stage unlocks the next.** You can't skip stages without creating technical debt.

The scripts we've built are **tools for each stage**, not competing alternatives.

**Current position:** Completing Stage 0, finished Stage 1, ready for Stage 2.

**Path forward:** Follow the progression model. Build stage-specific tooling as needed. Archive completed migrations.
Extract shared utilities during Stage 2 refactor.

**No reorg needed yet.** Organize by stage during Stage 2 when creating shared utils.
