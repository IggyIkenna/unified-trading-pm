---
doc_type: codex-ssot
title: SSOT Reference Mapping
summary:
  Defines which of the 5 information sources is authoritative per domain — pm/configs for operational data (sharding /
  start-dates / venues / data-catalogue), codex docs for standards, epics for implementation detail,
  service-registry.yaml for metadata, mvp-universe.yaml for MVP scope — plus the conflict-resolution and drift-detection
  protocol. Some tooling references predate unified-trading-codex archival.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [deployment-service, instruments-service, market-data-processing-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [ssot, ssot-audit, data-catalogue, mvp, consolidation]
related: [/codex/10-audit/consolidation-gap-analysis.md, codex/11-project-management/mvp-universe.yaml]
created: 2026-03-27
authoritative_for: [SSOT authority mapping by domain (operational-config vs codex vs epic vs registry vs MVP)]
referenced_by:
  [
    /codex/10-audit/CONTRACTS_SEPARATION_AUDIT.md,
    /codex/10-audit/PARSER_FIXES_AND_BOOK_SNAPSHOT_CLARIFICATION.md,
    /codex/10-audit/VALIDATOR_COVERAGE_MATRIX.md,
    /codex/10-audit/consolidation-gap-analysis.md,
    /codex/10-audit/gap-analysis-2026-03-11.md,
  ]
owner:
last_reviewed:
code_refs:
---

# SSOT Reference Mapping

**Version**: 1.0 **Last Updated**: 2026-03-03 **Status**: Active (Post-Audit Reconciliation)

---

## Purpose

After conflict reconciliation (Phase 0), this document defines which source is **authoritative** for each domain. When
there are conflicts between sources, consult this mapping to determine which source should be updated vs which should be
treated as derivative.

---

## The 5 Information Sources

1. **`unified-trading-pm/configs/`** - Operational data SSOT (sharding, data availability, venue mappings); symlinked
   into `deployment-service/configs/`
2. **`unified-trading-pm/codex/` docs** - Architectural standards and patterns
3. **`unified-trading-pm/codex/11-project-management/epics/`** - Implementation details and requirements
4. **`unified-trading-pm/codex/11-project-management/service-registry.yaml`** - Service metadata
5. **Service code in 32 repos** - Current implementation reality

---

## SSOT Hierarchy by Domain

### 1. Operational Data → PM Configs (symlinked into deployment-service)

**Authority**: `unified-trading-pm/configs/` files are SSOT for operational parameters (symlinked into
`deployment-service/configs/`).

| Domain                     | SSOT File                       | What It Defines                                                                                                                                          | Checklist Items             |
| -------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Sharding dimensions**    | `sharding.{service}.yaml`       | Exact shard keys (category×venue×date), CLI args (`--asset-group`, `--venue`, `--date`), compute recommendations (vCPUs, RAM), runtime estimates         | BASE-20                     |
| **Data availability**      | `expected_start_dates.yaml`     | Earliest expected data per service/category/venue. Used by data-status CLI to calculate completion %. Defines "Skip Invalid Dates Philosophy"            | BASE-21, HARDENING-03       |
| **Shard completion**       | `data-catalogue.{service}.yaml` | Tracks which shards have `stage_1_has_run` (job submitted), `stage_2_data_complete` (data verified in GCS)                                               | BASE-23                     |
| **Venue mappings**         | `venues.yaml`                   | Canonical category→venue mapping (CEFI/TRADFI/DEFI), expected data types per venue, provider mappings (Tardis, Databento, The Graph)                     | BASE-22, validation scripts |
| **Operational checklists** | `checklist.{service}.yaml`      | 52-item operational readiness checklist per service (7 phases: Repo Foundation, Testing, Deployment, Local Validation, Production, Docs, Data Catalogue) | N/A (operational tracking)  |

**Derivative sources that MUST align**:

- Codex `04-architecture/batch-live-architecture.md` - Documents sharding patterns generically
- Codex `02-data/` - Documents data availability philosophy
- Epic task descriptions - Reference specific sharding dimensions when deploying
- Per-repo `.cursorrules` - Enforce sharding patterns for that service

**Update protocol**:

```bash
# When changing sharding dimensions for a service:
1. Update sharding.{service}.yaml (SSOT)
2. Update 04-architecture/batch-live-architecture.md if pattern changes
3. Update relevant epic tasks if they reference sharding
4. Update {service}/.cursorrules with new sharding pattern
5. Run: python scripts/validate-alignment.py --check-drift
```

---

### 2. Architectural Standards → Codex Docs

**Authority**: `unified-trading-pm/codex/` documentation is SSOT for cross-cutting standards.

| Domain                  | SSOT Doc                                                      | What It Defines                                                                                                                 | Checklist Items                   |
| ----------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| **Batch-live symmetry** | `04-architecture/batch-live-architecture.md`                  | 4 seams pattern (data source, data sink, persistence thread, trigger), mode-agnostic engine, 90% code sharing                   | BASE-28, BASE-29, ARC-01          |
| **Config management**   | `06-coding-standards/README.md#configuration`                 | UnifiedCloudConfig inheritance chain, BaseConfig → UnifiedCloudConfig → ServiceConfig, no `os.getenv()`                         | BASE-01, COD-01                   |
| **Event logging**       | `03-observability/lifecycle-events.md`                        | 11 required lifecycle events (STARTED, VALIDATION, CONFIG_LOADED, etc.), timing metadata, per-service events                    | BASE-02, OBS-01                   |
| **Hardening standards** | `.cursor/rules/hardening-standards.mdc`                       | No fallback imports, no bare except, fail-loud principles, explicit missing data handling                                       | HARDENING-01 through HARDENING-06 |
| **Quality gates**       | `06-coding-standards/quality-gates.md`                        | Three-stage consistency (Local, GitHub Actions, Cloud Build), ruff==0.15.0 everywhere, test-in-image pattern                    | BASE-24, BASE-25, BASE-26         |
| **Cloud-agnostic**      | `04-architecture/cloud-agnostic-migration.md`                 | Use `get_storage_client()`, `get_secret_client()` abstractions, never `from google.cloud import storage`                        | BASE-30, INF-02                   |
| **Testing**             | `06-coding-standards/testing.md`                              | 4-tier structure (unit/integration/e2e/smoke), regression tests for every bug, coverage gates (≥35% min, 80% target)            | BASE-24, COD-03                   |
| **UTC datetime**        | `06-coding-standards/README.md#utc`                           | Always `datetime.now(timezone.utc)`, never `datetime.now()` or `datetime.utcnow()`                                              | COD-02                            |
| **Async HTTP**          | `06-coding-standards/PERFORMANCE_STANDARDS.md#async-http`     | Use `aiohttp` not `requests` in async functions, never `asyncio.run()` in loops                                                 | COD-04                            |
| **Provider manifest**   | `unified-api-contracts/.../config/provider_api_versions.yaml` | API keys, testnet availability, data_type (central/private/both), secret_names per provider. SSOT for vendor API key inventory. | Plan 6, defi_keys                 |

**Derivative sources that MUST align**:

- Epic implementation tasks - Follow codex patterns when implementing features
- Service code - Implements codex standards
- Per-repo `.cursorrules` - Enforce codex standards during development
- Workspace `.cursor/rules/*.mdc` - Enforce workspace-wide codex patterns

**Update protocol**:

```bash
# When establishing new cross-cutting pattern:
1. Update codex doc (e.g., 06-coding-standards/README.md) (SSOT)
2. Update workspace .cursor/rules/ if it needs runtime enforcement
3. Update _service-baseline-template.yaml with new checklist item
4. Update relevant per-repo .cursorrules files
5. Run: python scripts/sync-rules-and-docs.py
```

---

### 3. Implementation Details → Epics

**Authority**: Epics are SSOT for **detailed implementation requirements** of specific features.

| Domain                        | SSOT Epic                                           | What It Defines                                                                                                                                         | Checklist Items                                     |
| ----------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Config UI with hot-reload** | `data-io-production-readiness-epic.md` Task 4       | Exact UI features (syntax highlighting, diff viewer, version history), GCS persistence schema, PubSub config-updates events, per-field restart policies | Service-specific items in pipeline templates        |
| **Adaptive max workers**      | `data-io-production-readiness-epic.md` Task 3       | RAMAwarePool implementation, TaskProfiler, 85%/90% RAM thresholds, worker reduction/increase logic, background monitoring thread (10s intervals)        | Service-specific for market-data-processing-service |
| **Performance tracing**       | `data-io-production-readiness-epic.md` Task 1.4-1.5 | PerformanceTracer API (`start_span()`, `end_span()`), nested spans with parent_span_id, GCS export format, timing metadata fields                       | Service-specific for data pipeline services         |
| **Immutable audit trail**     | TBD (to be created in Phase 1)                      | Write-once audit log schema (trades, orders, positions, risk checks), implementation options (Firestore/BigQuery/blockchain), hash chaining algorithm   | REGULATORY-01                                       |
| **FCA compliance reporting**  | TBD (to be created in Phase 1)                      | MiFID II transaction report format (ISO 20022 XML), ARM submission protocol (SFTP), best execution report template, quarterly deadlines                 | REGULATORY-03, REGULATORY-04                        |

**Derivative sources that MUST align**:

- Codex docs - May document pattern AFTER epic implements it successfully (e.g., Config UI pattern added to
  05-infrastructure/)
- Service code - Implements epic specifications exactly
- Service-specific checklist items - Reference epic tasks for validation

**Update protocol**:

```bash
# When creating epic implementation details:
1. Write detailed task/subtask in epic markdown (SSOT for that feature)
2. If pattern is reusable, add to codex docs after successful implementation
3. Add service-specific checklist items referencing epic task
4. Update per-repo .cursorrules if service-specific enforcement needed
```

**Note**: Epics are **forward-looking** (what needs to be built). Codex docs are **established patterns** (what has been
proven and should be replicated). After epic completes, successful patterns migrate from epic → codex.

---

### 4. Service Metadata → service-registry.yaml

**Authority**: `service-registry.yaml` is SSOT for **service classification and metadata**.

| Domain              | SSOT Source                                                | What It Defines                                                         |
| ------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Service type**    | `service-registry.yaml` services[].type                    | `pipeline`, `platform`, `ui-observability`, `ui-control`, `ui-analysis` |
| **Owner**           | `service-registry.yaml` services[].owner_default           | Default assignee for issues                                             |
| **Priority**        | `service-registry.yaml` services[].priority                | `P0-critical`, `P1-high`, `P2-medium`, `P3-low`                         |
| **Milestone**       | `service-registry.yaml` services[].milestone               | `TechReadiness`, `Batch85`, `Live90`, `Commercialization`               |
| **Domain coverage** | `service-registry.yaml` services[].domain_coverage         | Venues supported, asset classes covered                                 |
| **Data coverage**   | `service-registry.yaml` services[].data_coverage           | Start date, batch/live mode support                                     |
| **Test coverage**   | `service-registry.yaml` services[].readiness.test_coverage | Current % (updated periodically)                                        |

**Derivative sources that MUST align**:

- Codex per-service docs - Service description should match registry metadata
- `_service-metadata-schema.yaml` - Schema structure for classification
- GitHub issue assignments - Should use `owner_default` from registry

**Update protocol**:

```bash
# When changing service metadata:
1. Update service-registry.yaml (SSOT)
2. Update per-service docs if description/coverage changes
3. Update _service-metadata-schema.yaml if new fields added
4. Run: python scripts/validate-alignment.py --check-drift
```

---

### 5. MVP Scope → mvp-universe.yaml

**Authority**: `mvp-universe.yaml` is SSOT for **minimum viable product scope** (subset of available data).

| Domain                | SSOT Source                                    | What It Defines                                                           |
| --------------------- | ---------------------------------------------- | ------------------------------------------------------------------------- |
| **MVP instruments**   | `mvp-universe.yaml` instruments.included       | BTC, ETH only for MVP                                                     |
| **MVP venues**        | `mvp-universe.yaml` venues.{category}.included | Selected venues per category (CEFI: 6, DEFI: 3, TRADFI: 3)                |
| **MVP asset classes** | `mvp-universe.yaml` asset_groupes.included     | CRYPTO_CEFI, DEFI, TRADFI_FUTURES, TRADFI_ETFS (excludes OPTIONS, SPORTS) |
| **MVP strategies**    | `mvp-universe.yaml` strategies.defi_mvp        | 4 DeFi strategies (staking, lending, recursive staking, basis trade)      |
| **MVP exclusions**    | `mvp-universe.yaml` \*.excluded                | Explicitly excluded protocols, data types, services                       |

**Relationship to venues.yaml**:

- `venues.yaml` = **Available data** (what exists in APIs/GCS)
- `mvp-universe.yaml` = **MVP scope** (minimum viable product subset)
- MVP is a **subset** of available data (MVP ⊆ Available Data)

**Derivative sources that MUST align**:

- Epic goals/scope sections - Should reference MVP universe
- Per-service observability docs - Should document both available data AND MVP coverage
- Checklist item BASE-22 - Validates service supports MVP data coverage

**Update protocol**:

```bash
# When changing MVP scope:
1. Update mvp-universe.yaml (SSOT for MVP)
2. Update epic goals if MVP scope changes
3. Update per-service docs with MVP coverage matrix
4. DO NOT update venues.yaml (it tracks available data, not MVP)
5. Run: python scripts/validate-alignment.py --check-drift
```

---

## Conflict Resolution Protocol

When conflicts are detected between sources:

### Step 1: Determine Authority

Consult this document to identify which source is authoritative for the conflicting domain.

### Step 2: Resolve Case-by-Case

User (Ikenna) reviews each conflict and documents resolution in `alignment-resolution-decisions.yaml`.

### Step 3: Synchronize Sources

Run `python scripts/apply-alignment-resolutions.py` to update all derivative sources per resolution decisions.

### Step 4: Validate Alignment

Run `python scripts/validate-alignment.py --check-drift` to verify 100% alignment after synchronization.

---

## Ongoing Enforcement

### Workspace Cursor Rules

`.cursor/rules/ssot-alignment-enforcement.mdc` enforces SSOT hierarchy:

- Warns when SSOT files are modified
- Requires updating derivative sources
- Mandates running drift detection before commits

### Per-Repo Cursor Rules

Each of 32 production services has `.cursorrules` that:

- References operational SSOTs (e.g., "Sharding per sharding.{service}.yaml")
- References codex standards (e.g., "Config extends UnifiedCloudConfig")
- Includes validation reminder before committing pattern changes

### Pre-Commit Hook (Optional)

```bash
# .git/hooks/pre-commit (in unified-trading-codex repo)
#!/bin/bash

# Check if any SSOT files changed
SSOT_FILES=$(git diff --cached --name-only | grep -E '(sharding\.|expected_start_dates|venues\.yaml|mvp-universe|10-audit/_service-baseline)')

if [ -n "$SSOT_FILES" ]; then
    echo "🔍 SSOT files changed, checking alignment..."
    python scripts/validate-alignment.py --check-drift
    if [ $? -ne 0 ]; then
        echo "❌ Alignment check failed. Update related sources before committing."
        echo "See: unified-trading-pm/codex/10-audit/ssot-reference-mapping.md"
        exit 1
    fi
fi
```

---

## Example: Changing Sharding Dimensions

**Scenario**: instruments-service needs to add `instrument_type` shard dimension.

### Incorrect Approach ❌

```bash
# DON'T: Update only one source
vim deployment-service/configs/sharding.instruments-service.yaml
# Add instrument_type to shard_dimensions
git add sharding.instruments-service.yaml
git commit -m "Add instrument_type sharding"
# ❌ Now codex docs, epic, and cursorrules are out of sync!
```

### Correct Approach ✅

```bash
# 1. Update operational SSOT
vim deployment-service/configs/sharding.instruments-service.yaml
# Add instrument_type to shard_dimensions

# 2. Update codex if pattern changes
vim unified-trading-pm/codex/04-architecture/batch-live-architecture.md
# Add section on instrument_type sharding rationale

# 3. Update epic if it specifies sharding
vim unified-trading-pm/codex/11-project-management/epics/data-io-production-readiness-epic.md
# Update Task 5 deployment command examples to include --instrument-type

# 4. Update per-repo cursorrules
vim instruments-service/.cursorrules
# Add: "Sharding per sharding.instruments-service.yaml: category × venue × date × instrument_type"

# 5. Validate alignment
cd unified-trading-codex
python scripts/validate-alignment.py --check-drift
# ✅ Exit code 0 = all sources aligned

# 6. Commit all changes together
cd deployment-service
git add configs/sharding.instruments-service.yaml
cd ../unified-trading-codex
git add 04-architecture/batch-live-architecture.md
git add 11-project-management/epics/data-io-production-readiness-epic.md
cd ../instruments-service
git add .cursorrules

# Commit via quickmerge in each repo
```

---

## Example: Adding New Codex Standard

**Scenario**: Establish new standard for "No print() statements in production code".

### Correct Approach ✅

```bash
# 1. Update codex standard (SSOT for standards)
vim unified-trading-pm/codex/06-coding-standards/README.md
# Add section: "No print() statements (use logger.info() instead)"

# 2. Add checklist item
vim unified-trading-pm/codex/10-audit/_service-baseline-template.yaml
# Add: COD-05 "No print() statements"

# 3. Add workspace cursor rule
vim .cursor/rules/coding-standards.mdc
# Add enforcement: "NEVER use print() - use logger.info()"

# 4. Add validator
vim unified-trading-pm/codex/scripts/validators/validate-no-print.py
# Scan for print() statements, fail if found

# 5. Update all per-repo cursorrules (automated)
python unified-trading-pm/codex/scripts/sync-rules-and-docs.py
# Propagates to all 32 .cursorrules files

# 6. Validate
python scripts/validate-alignment.py --check-drift
# ✅ Codex + checklist + cursor rules + validator all aligned
```

---

## Cross-Reference Table: Checklist Item → SSOT

| Checklist Item                        | SSOT Source                                               | Type              |
| ------------------------------------- | --------------------------------------------------------- | ----------------- |
| BASE-01 through BASE-18               | Codex `06-coding-standards/`, `04-architecture/`, etc.    | Standards         |
| BASE-19 (Classification)              | `service-registry.yaml` + `_service-metadata-schema.yaml` | Metadata          |
| BASE-20 (Sharding)                    | `sharding.{service}.yaml`                                 | Operational       |
| BASE-21 (Start dates)                 | `expected_start_dates.yaml`                               | Operational       |
| BASE-22 (MVP coverage)                | `mvp-universe.yaml` + `venues.yaml`                       | Operational + MVP |
| BASE-23 (Data catalogue)              | `data-catalogue.{service}.yaml`                           | Operational       |
| BASE-24 through BASE-27 (CI/CD)       | Codex `06-coding-standards/quality-gates.md`              | Standards         |
| BASE-28, BASE-29 (Deployment)         | Codex `04-architecture/batch-live-architecture.md`        | Standards         |
| BASE-30, BASE-31 (Libraries)          | Codex `05-infrastructure/unified-libraries/`              | Standards         |
| BASE-32 (Security)                    | Codex `07-security/secrets-management.md`                 | Standards         |
| HARDENING-01 through HARDENING-06     | Codex + `.cursor/rules/hardening-standards.mdc`           | Standards         |
| REGULATORY-01 through REGULATORY-04   | Codex `07-security/fca-compliance.md` (to be created)     | Standards         |
| DR-01 through DR-03                   | Codex `08-workflows/disaster-recovery.md` (to be created) | Standards         |
| SECURITY-03, SECURITY-04, SECURITY-05 | Codex `07-security/`                                      | Standards         |
| Service-specific items                | Epic tasks (e.g., `data-io-epic.md` Task 4 for Config UI) | Implementation    |

---

## FAQ

### Q: What if codex doc and epic conflict?

**A**: Depends on the domain:

- **Established pattern** (e.g., config management) → Codex wins, update epic
- **New feature** (e.g., Config UI hot-reload) → Epic wins, codex documents it after proven
- **Ambiguous** → User resolves case-by-case in `alignment-resolution-decisions.yaml`

### Q: What if operational config and codex conflict?

**A**: Operational config wins for operational data (sharding, start dates), codex wins for standards (patterns, best
practices).

### Q: Should I update service code or SSOT docs first?

**A**: Update SSOT docs first (UTD v2 configs + Codex + Epics), then implement in service code. This ensures code is
built against aligned specifications.

### Q: What if I find a bug in an SSOT file?

**A**: Fix the SSOT, then update derivative sources, then run drift detection:

```bash
# 1. Fix SSOT
vim deployment-service/configs/sharding.instruments-service.yaml
# Fix: category_shards: 3 (was incorrectly 4)

# 2. Update derivatives
vim unified-trading-pm/codex/04-architecture/batch-live-architecture.md
# Update text referencing 3 category shards

# 3. Validate
python scripts/validate-alignment.py --check-drift

# 4. Update service code to match corrected SSOT
vim instruments-service/instruments_service/orchestration_service.py
# Implement 3 category shards
```

---

**Maintained by**: Production Readiness Working Group **Review cycle**: After any Phase 0 reconciliation **Last
reconciliation**: 2026-02-21 (Phase 0 initial)
