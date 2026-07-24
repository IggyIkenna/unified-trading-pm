---
doc_type: issue
title: Repo docs → codex SSOT consolidation (kill doc duplication / stale drift, all repos)
summary:
status: resolved
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-01
parent_epic: plan_hygiene_master
assigned_vm: vm-ml
author: harsh + claude (session 67c17024)
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
source:
  [unified-trading-pm/codex/06-coding-standards/documentation-standards.md, unified-trading-pm/codex/00-SSOT-INDEX.md]
---

# Repo docs → codex SSOT consolidation

> **ARCHIVED 2026-06-01 (slot 7).** Plan-of-record is `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md`. The
> 8-repo audit registry + per-repo rollout list + FIX-STALE pass-1 evidence + follow-ups (URDI-in-code, features-service
> parked PR) were **folded into that plan's Appendix A**, and its Phase 0 pointer now references the appendix. Closed to
> stop dual-tracking; this file remains as historical evidence only.

> **📋 PLAN-OF-RECORD MOVED (2026-06-01)**: the canonical plan for this work is now
> [`../codex_vs_repo_docs_ssot_audit_2026_06_01.md`](../codex_vs_repo_docs_ssot_audit_2026_06_01.md) (opus-1m, all
> active repos, full methodology). **This file is retained as the pass-1 evidence appendix** — the FIX-STALE pass-1
> landings + the 8-repo read-only audit registry below. Do not add new methodology/phases here; they live in the
> plan-of-record.

> **Why**: stale repo docs are a recurring, systemic problem (2026-06-01 MTDS `GCS_PATHS.md` had both hyphen-partition
> drift AND un-tiered-bucket drift). Root cause: the **same canonical content is duplicated** in `pm/codex/` (SSOT) and
> a repo's `docs/` — the two copies drift. **Fix**: codex is the single SSOT; repo docs carry only repo-specific
> essentials + a link to the canonical codex doc. Contract codified in
> `/codex/06-coding-standards/documentation-standards.md` **§ S5.11** (2026-06-01).

## Contract (S5.11 — the durable fix)

- `pm/codex/` = SSOT for all canonical / cross-cutting content. Repo `docs/` = repo-specific essentials + codex links.
- **Never copy a codex table/contract/path-template into a repo doc — link it.** Canonical change → only codex edits.
- Required docs (S5.1/2/3) whose content is entirely canonical collapse to the **redirect template** (still substantive,
  clears the S5.4 stub bar). Non-required pure-duplicate docs are **deleted** (after migrating any unique delta).
- Stale repo-doc-vs-codex = review-blocking; fix by delete-and-link, never re-sync two copies.

## Method (per repo)

1. **Audit (read-only)** — classify every `docs/*.md` + root `README.md`: `KEEP-ESSENTIAL` / `REDIRECT→<codex doc>` /
   `DELETE` (pure dup) / `FIX-STALE`. Map each duplicate to its codex SSOT.
2. **Consolidate** — apply redirect template to required docs; delete non-required pure-dups (migrate unique deltas
   first); fix stale literals (bucket names → `resolve_bucket_name()`, etc.).
3. **Verify** — S5.7 audit script passes (no missing/stub required docs); `rg` finds no duplicated codex tables; repo
   builds/links resolve.

## Per-repo rollout (20 repos with docs/, ~520 docs)

Ordered by codex-duplication likelihood (data/arch/deploy SSOTs duplicated most):

- [x] ✅ **market-tick-data-service** (31) — `GCS_PATHS.md` env-tiered + hive-canonical + codex pointer (mtds@9acbee1);
      remaining: DEPLOYMENT_GUIDE_FEMI/SHAHRIYAR delete-redirect (P1 below).
- [ ] [DOCS] P0. **deployment-service** (79) — deploy-flow / infra / bucket / VM-tarball docs vs
      `codex/05-infrastructure`, `codex/08-workflows`. Highest duplication surface.
- [ ] [DOCS] P0. **unified-api-contracts** (36) — schema/contract docs vs `codex/02-data` (UAC layout,
      schema-governance).
- [ ] [DOCS] P0. **market-data-processing-service** (22) — path/manifest/candle docs vs `codex/02-data`.
- [ ] [DOCS] P0. **execution-service** (20) — execution-arch / venue docs vs `codex/04-architecture`, `codex/02-venues`.
- [ ] [DOCS] P0. **instruments-service** (19) — IS→MTDS contract / path docs vs `codex/04-architecture`,
      `codex/02-data`.
- [ ] [DOCS] P1. **strategy-service** (15) — archetype/promote docs vs `codex/09-strategy`, `codex/04-architecture`.
- [ ] [DOCS] P1. **unified-trading-library** (15) — events/cloud/bucket docs vs `codex/04-architecture`,
      `codex/05-infrastructure`.
- [ ] [DOCS] P1. **e2e-testing** (21) — defi/sports/prediction runbooks vs `codex/08-workflows`, `codex/15-runbooks`.
- [ ] [DOCS] P1. **agent-orchestrator** (10) — orchestrator docs vs `codex/12-agent-workflow`, `codex/04-architecture`.
- [ ] [DOCS] P2. **deployment-api** (8) / **client-reporting-api** (8) / **alerting-service** (8) — vs
      `codex/03-services`, `codex/03-observability`.
- [ ] [DOCS] P2. **trading-agent-service** (7) / **ibkr-gateway-infra** (4) / **batch-live-reconciliation-service** (1)
      / **system-integration-tests** (1).
- [ ] [DOCS] P2. **deployment-ui** (3) / **user-management-ui** — vs `codex/04-architecture` UI notes.
- [ ] [DOCS] P3. **unified-trading-system-ui** (152) — mostly UI-specific (lower codex overlap); audit for the
      data/path/contract docs that DO duplicate codex, leave genuine UI docs.

## MTDS finish (P1 — delete-redirect candidates already identified)

- [ ] [DOCS] P1. **market-tick-data-service**: `DEPLOYMENT_GUIDE_FEMI.md` (person-named onboarding dup) +
      `SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md` (infra-spec dup) → migrate any unique delta, replace with redirect to
      `codex/05-infrastructure` + `codex/08-workflows`, delete the dumps. Slim `DEPENDENCIES.md` / `ARCHITECTURE.md` to
      repo-local + codex links.

## FIX-STALE pass 1 — landed 2026-06-01 (operator chose FIX-STALE-only; DELETEs/REDIRECTs held)

Literal fixes only (env-tier bucket names → `{kind}-{ag}-{env}-{pid}` resolve via `resolve_bucket_name()`; hyphen hive
partitions → `key=value`; `pip`→`uv`; `test-project`→`{project_id}`; Python 3.11→3.13; `batch only`→`batch|live`;
retired names). ~340 fixes. All on `origin/live-defi-rollout`:

- deployment-service @ `9627260` (~110 bucket + 8 hyphen + test-project)
- instruments-service @ `8bea654` + `9ecc4b2` (27 bucket + 11 pip→uv; **URDI left — code still uses URDI symbols**,
  follow-up needed)
- execution-service @ `4b0ea42f` (47 bucket + hyphen + py3.13 + uv)
- market-data-processing-service @ `89161dc` (18 bucket + 15 hyphen)
- strategy-service @ `80d298fe` (bucket + hyphen + batch=live + retired name)
- e2e-testing @ `0de5471` (31 bucket/path)
- unified-trading-library @ `168e649` + `c88278b` (resolve_bucket_name + setup_events + uv + 2 more docs)
- market-tick-data-service @ `d97ca3c` (QUICK_START_GUIDE leftover)

**Parked — features-service**: another agent actively working; `live-defi-rollout` is branch-protected
(`quality-gates-v2` required). Docs commit `b9b4103e` is on `origin/tab/hk/10`; PR #4 exists but **bundles a foreign
commit (`603c2b9c`) — do NOT merge as-is**. Left for the owning agent; NO git surgery performed.

**Intentionally skipped in FIX-STALE** (handled elsewhere): delete-candidate docs (→ DELETE pass), MTDS `issues/*` +
`plans/*` (historical records, not living docs), UI `context/codex|pm/*` (vendored mirrors — re-sync from canonical
codex), legacy-example lines (deprecation notes, phase-2-6 cutover-runbook "from" state).

**Not yet done**: UI `docs/audits/dart-v2-audit-context.md` + `docs/under-review/.../DATA_PIPELINE_SPEC.md` (UI
branch-protection/ownership unverified); UAC deleted-dir refs (`SCHEMA_GOVERNANCE`/`MOCKS_AND_VCR`/`SCHEMA_CHANGELOG` —
contextual, fold into UAC REDIRECT pass).

**Follow-up finding**: `live-defi-rollout` branch protection is inconsistent across repos (features-service requires
`quality-gates-v2`; the other 8 accept direct LDR push) — contradicts the workspace "no CI on LDR" rule. Capture as
issue.

## Audit registry (read-only pass 1 — 8 repos, 2026-06-01)

> **Caveat**: audit agents proposed codex SSOT targets by grep; **verify each target exists before redirecting** (some
> proposed paths e.g. `/codex/05-infrastructure/gcs-lifecycle-policies.md`, `/codex/04-architecture/concurrency.md`,
> `/codex/02-data/bucket-naming-and-config.md` may need creating or remapping). Never redirect to a non-existent doc.

### deployment-service (~52 docs) — heaviest. DELETE-heavy (Feb-2026 planning dumps)

- **DELETE** (pure dup / dead planning artefacts): `MASTER_ML_IMPLEMENTATION_PLAN.md`, `ML_IMPLEMENTATION.md`,
  `MASTER_IMPLEMENTATION_INDEX.md`, `GCS_LIFECYCLE_AGGRESSIVE_STRATEGY.md`, `GCS_LIFECYCLE_COST_OPTIMIZATION.md`,
  `BIGQUERY_INTEGRATION_GUIDE.md`, `MAX_WORKERS_UNIFIED_IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_MAX_WORKERS.md`,
  `RESOURCE_MONITORING_AND_RIGHTSIZING.md`, `SPECS.md` (contractor onboarding), `UI_TYPESCRIPT_TYPES.md`,
  `specs/PLANS_ALIGNMENT.md`, `specs/README.md`, `archive/*` (BIGQUERY_HIVE_PARTITIONING_VALIDATION,
  MASSIVE_BACKFILL_COST_ANALYSIS, CONFIG_LOADING_PATTERNS, GCS_FUSE_VM_SETUP, ADAPTIVE_MAX_WORKERS_DESIGN,
  schema-change/×8).
- **FIX-STALE**: `TESTING.md` (hyphen paths + `test-project` + pip), `setup.md` (`deployment-service-v2`, venv/pip),
  `INFRASTRUCTURE.md` (`test-project` proj id), `local-dev/local-run-guide.md` (hardcoded `/Users/ikenna…` path),
  `INDEX.md` (dead links), `README.md`.
- **REDIRECT**: COST, HARDENING, MIGRATION, CLOUD_AGNOSTIC_MIGRATION, RUNBOOKS, GCS_PATHS, SCHEMA_VALIDATION,
  GCS_AND_SCHEMA, CACHE_AND_STATE, LIVE_MODE, CLOUD_BUILD_SUCCESS_CHECKLIST, GITHUB_TOKEN_CLOUD_BUILD,
  STANDARDIZED_EVENT_LOGGING, COMPREHENSIVE_SERVICE_AUDIT_FRAMEWORK, E2E_SPECS, UI_SPEC.
- **KEEP** (repo-specific): SHARDING_AND_DATA_ALIGNMENT, VM_HEALTH_AND_GCSFUSE_OPTIMIZATION, hybrid-live-seam,
  dev-environment, CONFIGURATION, ARCHITECTURE, DEPLOYMENT_GUIDE, cli, service-bundling-review, resource-profiles/\*.

### unified-api-contracts (36) — FIX-STALE on deleted-dir references

- **FIX-STALE**: `SCHEMA_GOVERNANCE.md` (refs deleted `canonical/normalize/`+`schemas/`), `MOCKS_AND_VCR.md` (old
  cassette path), `SCHEMA_CHANGELOG.md` (deleted flat modules).
- **DELETE** (live copies of already-archived/superseded): `ICLOUD_REPO_MIGRATION_PROMPT.md`,
  `SCHEMA_NORMALIZATION_GAPS_AUDIT.md`, `UAC_FULL_GAP_ANALYSIS_AND_BATCH_LIVE_SYMMETRY.md`, `VIX_LIVE_RESEARCH.md`.
- **REDIRECT**: PACKAGE_LAYOUT_AND_SCOPE, BATCH_LIVE_SYMMETRY, canonical-instrument-ids.
- **KEEP**: README, ARCHITECTURE, SCHEMA_AUDIT_MATRIX (generated), TESTING, archive/\*.

### market-data-processing-service (22)

- **FIX-STALE**: `DEPLOYMENT_GUIDE_FEMI.md` (un-tiered buckets + hyphen partitions), `GCS_PATHS.md` (un-tiered),
  `DEPENDENCIES.md` (`{category}` vocab + un-tiered).
- **DELETE**: `REFACTORING_STANDARDS_COMPLIANCE.md`, `specs/PLANS_ALIGNMENT.md`, `DEPLOYMENT_GUIDE.md` (stub),
  `TESTING.md` (stub).
- **REDIRECT**: SCHEMA_VALIDATION_AND_TIMEFRAME_SUFFIXING_E2E, UNIFIED_SCHEMA_AND_CLIENT_USAGE_GUIDE,
  TIMEFRAME_AGGREGATION_SPECIFICATION.

### execution-service (20)

- **DELETE**: `UNIFIED_BATCH_LIVE_ARCHITECTURE.md` (refs deleted codex file), `CLEAN_ALGORITHM_INTERFACE_DESIGN.md`,
  `DEFI_INTEGRATION_TODO.md`.
- **FIX-STALE**: `ARCHITECTURE.md` (split execution-store-\* bucket literals), `README.md` (Python 3.11 vs 3.13
  contradiction with BACKTEST_QUICKSTART), `BACKTEST_DEPLOYMENT.md` (refs SHAHRIYAR spec).
- **REDIRECT**: GCS_PATHS, ROUTING_MATRIX, CONFIGURATION, ERROR_HANDLING, DEPLOYMENT_GUIDE.
- **KEEP**: TESTING, SCHEMA_VALIDATION, BACKTEST_QUICKSTART, DEPENDENCIES, TROUBLESHOOTING, TRADE_ANALYTICS_INTEGRATION,
  VISUALIZER_QUICKSTART, specs/\*.

### instruments-service (19) — URDI phantom + dead `unified-trading-services` refs

- **FIX-STALE**: `instrument-catalogue.md` (un-tiered bucket + URDI + `category=`), `README.md` (URDI ×9).
- **DELETE**: `specs/CLOUD_OPERATIONS.md`, `specs/COMMAND_FLOW_ANALYSIS.md`, `specs/COMMAND_FLOW_DIAGRAM.md` (dead
  `unified-trading-services`), `specs/CORPORATE_ACTIONS.md`, `specs/SETUP_GUIDE.md`, `specs/TEST_ALIGNMENT.md`
  (pip/venv).
- **REDIRECT**: specs/MVP_INSTRUMENTS, specs/SECRETS_SETUP, specs/INSTRUMENT_SPECIFICATION.
- **KEEP**: {CEFI,DEFI,TRADFI,SPORTS}\_INSTRUMENTS, POLYMARKET_PREDICTION, ARCHITECTURE.

### unified-trading-library (15)

- **FIX-STALE**: `CLOUD_API_PATTERNS.md` (`client.bucket()` anti-pattern), `README.md` (`setup_cloud_logging` + pip).
- **REDIRECT**: ERROR_HANDLING, ARCHITECTURE, PATTERNS, ID_NAMING_CONVENTIONS, DEPENDENCIES, CONFIGURATION, DEV_SETUP,
  data-sink-validation.
- **DELETE**: `specs/README.md` (pointer-only stub).
- **KEEP**: TESTING, CLOUD_BUILD_TRIGGER_SETUP, UTL_ADOPTION_MATRIX, README, specs/PLANS_ALIGNMENT.

### strategy-service (15)

- **FIX-STALE/REDIRECT**: `STRATEGY_MODES.md` (retired `basis-strategy-v1` name + dead links), `CLI_REFERENCE.md`
  (`batch only` violates batch=live).
- **DELETE**: `BACKTEST_ENGINE.md` (dup of benchmark-fills + backtest-groups).
- **REDIRECT**: BACKTESTS, ARCHITECTURE, GCS_PATHS.
- **KEEP**: archetype_registry_discovery, DEPLOYMENT_GUIDE, CONFIGURATION, CONFIG_SCHEMA, SCHEMA_VALIDATION,
  DEPENDENCIES, TESTING, ERROR_HANDLING, specs/\*, README.

### e2e-testing (21)

- **DELETE**: `defi/UI_DEMO_WALKTHROUGH.md` (Elysium/bankelysium removed-provider creds).
- **FIX-STALE**: `VM_BACKFILL_GUIDE.md` (missing lifecycle_class + gsutil), `sports/ROADMAP.md` (past trial dates →
  migrate to epic).
- **REDIRECT**: defi/PAPER_LIVE_CONVERGENCE, E2E_PIPELINE_GUIDE, architecture.
- **KEEP**: sports/LIVE*ODDS_PROVIDERS, */progress, _/issues, coverage-matrix, _/per-strategy-acceptance,
  \_/smoke-test-baseline.

### Remaining repos (pass-2 audit pending)

- [ ] [DOCS] P2. agent-orchestrator (10), deployment-api (8), client-reporting-api (8), alerting-service (8),
      trading-agent-service (7), ibkr-gateway-infra (4), deployment-ui (3), system-integration-tests (1),
      batch-live-reconciliation-service (1).
- [ ] [DOCS] P3. unified-trading-system-ui (152) — audit only the data/path/contract docs; leave genuine UI docs.
