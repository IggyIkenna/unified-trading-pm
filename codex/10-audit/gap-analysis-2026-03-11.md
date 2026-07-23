---
doc_type: codex-ssot
title: "Gap Analysis: Checklist Consolidation — 2026-03-11"
summary:
  2026-03-11 formalised gap list for repo_readiness_semver_hardening — deployment-service checklist items absorbed into
  CR1/DR1/DR6, all v2.0 validator IDs preserved in code_audit_items, batch-vs-live divergent items split per mode;
  concludes zero v2.0 items are uncovered by the v3.0 CR/DR/BR model. Companion to consolidation-gap-analysis.md;
  pre-v3.0 record.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [audit, readiness, consolidation, ssot-audit]
related: [/codex/10-audit/consolidation-gap-analysis.md, /codex/10-audit/ssot-reference-mapping.md]
created: 2026-03-27
authoritative_for: [2026-03-11 checklist-consolidation gap formalisation]
referenced_by: [/codex/10-audit/consolidation-gap-analysis.md]
owner:
last_reviewed:
code_refs:
---

# Gap Analysis: Checklist Consolidation — 2026-03-11

**Purpose**: Phase 0 gap analysis for `p0-audit-existing-checklists` (plan: repo_readiness_semver_hardening_2026_03_11).
**Status**: Complete — v3.0 template already created. This document formalises the gaps identified during Stream A.
**Full analysis**: `unified-trading-pm/codex/10-audit/consolidation-gap-analysis.md`

---

## Section 1: Items in deployment-service checklist NOT in codex enhanced template (v2.0)

The `deployment-service/configs/checklist.template.service.yaml` has 52 items in 7 phases. Key items absent from
`_checklist-template-enhanced.yaml` (v2.0):

| deployment-service item                                                 | Phase   | Gap type                                        | v3.0 resolution                                                                                                                              |
| ----------------------------------------------------------------------- | ------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `item_04d_resource_monitoring` — PerformanceMonitor for CPU/memory/disk | Phase 1 | Not in any v2.0 item                            | Absorbed into CR1 criteria (observability)                                                                                                   |
| `item_04e_graceful_shutdown` — SIGTERM/SIGINT handlers                  | Phase 1 | Not in any v2.0 item                            | Absorbed into CR1 criteria                                                                                                                   |
| `item_04f_utc_datetime_compliance` — all datetime UTC-aware             | Phase 1 | Not explicitly in v2.0                          | Absorbed into CR1 (code quality)                                                                                                             |
| `item_04g_strict_exit_codes` — sys.exit(1) on any failure               | Phase 1 | Not in v2.0                                     | Absorbed into CR1 criteria                                                                                                                   |
| `item_04h_standardized_event_logging`                                   | Phase 1 | Partially covered by OBS-05                     | Maps to BR3 event handling                                                                                                                   |
| `auth_setup` block (local_auth_method, inter_service_auth)              | Phase 1 | No v2.0 equivalent                              | Absorbed into DR1/DR6 criteria                                                                                                               |
| `item_07_data_catalogue_sharding` (sharding.yaml, venues.yaml)          | Phase 7 | ARC-02/BASE-20/BASE-22 in v2.0 audit items only | **Operational-only** — SSOT in `unified-trading-pm/configs/`; symlinked into `deployment-service/configs/`; excluded from readiness template |
| `item_08_expected_start_dates` (expected_start_dates.yaml)              | Phase 7 | BASE-21 in v2.0 only                            | **Operational-only** — excluded from readiness template                                                                                      |
| PubSub topics subscription list                                         | Phase 7 | No equivalent                                   | **Operational-only** — excluded from readiness template                                                                                      |
| Data catalogue completion % (stage_1, stage_2)                          | Phase 7 | No equivalent                                   | **Operational-only** — excluded from readiness template                                                                                      |

**Decision**: Phase 7 (data catalogue) items are **operational metadata**, not readiness criteria. SSOT is
`unified-trading-pm/configs/` (symlinked into `deployment-service/configs/`). This is documented in
`ssot-reference-mapping.md`.

---

## Section 2: Items in codex enhanced template NOT covered by CR/DR/BR model

The v2.0 `_checklist-template-enhanced.yaml` has 38 items in 9 sections. The CR/DR/BR model covers the following gaps:

| v2.0 Item                             | Section            | CR/DR/BR coverage      | Gap                                          |
| ------------------------------------- | ------------------ | ---------------------- | -------------------------------------------- |
| COD-01 (UnifiedCloudConfig)           | Configuration      | CR1 + CR4              | Fully covered via code_audit_items cross-ref |
| COD-02 (no hardcoded domain config)   | Configuration      | CR1                    | Fully covered                                |
| COD-03 (CONFIGURATION.md)             | Configuration      | DR6 criteria           | Covered — docs required for prod-ready       |
| COD-20 (no hardcoded project IDs)     | Configuration      | CR4 (security scan)    | Fully covered                                |
| OBS-01 (setup_cloud_logging)          | Observability      | CR1                    | Covered                                      |
| OBS-05 (lifecycle events)             | Observability      | BR3                    | Covered                                      |
| OBS-06 (test_event_logging.py)        | Observability      | CR2 + BR3              | Covered                                      |
| DAT-01 (schema-first)                 | Data validation    | CR1                    | Covered                                      |
| DAT-02 (pre-upload schema validation) | Data validation    | DR4                    | Covered — SIT validates data quality         |
| DAT-03 (timestamp-date alignment)     | Data validation    | DR4                    | Covered                                      |
| COD-04 (error handling decorators)    | Error handling     | CR1                    | Covered                                      |
| COD-05 (no bare except)               | Error handling     | CR4 (ruff)             | Covered                                      |
| SEC-01..SEC-05                        | Security           | CR4 + DR6              | Covered via code_audit_items                 |
| INF-04 (Dockerfile)                   | Infrastructure     | DR1                    | Covered                                      |
| INF-05 (cloud-agnostic)               | Infrastructure     | CR4                    | Covered                                      |
| INF-08 (cloudbuild.yaml)              | Infrastructure     | DR1                    | Covered                                      |
| ARC-02 (sharding config)              | Architecture       | code_audit_items       | Covered — tracks sharding.yaml presence      |
| ARC-11 (batch-live symmetry)          | Architecture       | BR6                    | Covered                                      |
| BASE-19 (service classification)      | MVP/Classification | code_audit_items       | Covered                                      |
| BASE-22 (MVP coverage)                | MVP/Classification | code_audit_items       | Covered                                      |
| REGULATORY-01..04                     | Regulatory         | DR6 + code_audit_items | Covered                                      |
| HARDENING-01..06                      | Hardening          | CR1 + CR4              | Covered — fail-loud patterns feed into CR    |

**Net gap**: Zero items from v2.0 are uncovered by the v3.0 CR/DR/BR model. All v2.0 validator IDs are preserved in the
`code_audit_items` section of `REPO_READINESS_CHECKLIST.yaml`.

---

## Section 3: Batch-specific vs live-specific items requiring separate tracking

Items that genuinely differ between batch and live modes:

| Item                           | Batch-specific                               | Live-specific                           | Resolution                                          |
| ------------------------------ | -------------------------------------------- | --------------------------------------- | --------------------------------------------------- |
| DR1 infra                      | GCS buckets, batch Cloud Build trigger       | WebSocket connections, live Cloud Run   | Separate dr1_infra in batch: and live: sub-sections |
| DR3 feature env                | Batch job executes successfully              | Live service health/readiness endpoints | Separate dr3_feature_env                            |
| DR5 load/perf                  | Throughput (records/sec), batch duration     | P99 latency (ms), connection stability  | Separate dr5_load_perf SLA fields                   |
| BR4 PnL targets                | Data completeness ≥ 99.9%; backfill accuracy | Real-time accuracy, fill rate, slippage | Separate br4_pnl_targets per mode                   |
| BR5 PnL optimization           | Backtest on historical data                  | Paper trading / forward test            | Separate br5_pnl_optimization                       |
| BR6 batch-vs-live              | Only applicable when BOTH modes exist        | Only applicable when BOTH modes exist   | na_reason if single-mode repo                       |
| DAT-02 (pre-upload validation) | Yes — Parquet upload gate                    | No — stream validation different        | ARC-11 + BR6 handle the symmetry check              |

**Repos with BOTH modes** (require separate batch and live DR/BR sections in `repos/*.yaml`): execution-service,
strategy-service, features-\* (6 services), instruments-service, market-data-processing-service,
market-tick-data-service, ml-inference-service, ml-training-service, pnl-attribution-service,
position-balance-monitor-service, risk-and-exposure-service (15 repos total).

---

## Section 4: Merge decisions for each gap

| Gap                                                                                  | Decision                                                            | Rationale                                                                                                                                           |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 7 operational data (sharding, venues, data-catalogue)                          | **Excluded from readiness template**                                | SSOT in `unified-trading-pm/configs/` (symlinked into `deployment-service/configs/`); they track WHAT data exists, not WHETHER the service is ready |
| deployment-service `item_04d/e/f/g` (resource monitoring, shutdown, UTC, exit codes) | **Absorbed into CR1 criteria text**                                 | These are code quality requirements that gate CR1 (functionality complete)                                                                          |
| deployment-service `auth_setup` block                                                | **Absorbed into DR1/DR6 criteria**                                  | Auth wiring is an infra/deployment concern                                                                                                          |
| v2.0 validator IDs not in CR/DR/BR stages                                            | **Preserved in `code_audit_items` section**                         | Automation checks feed into CR1/CR4; the section cross-references stage mapping                                                                     |
| batch/ and live/ duplicate files                                                     | **Merged into single `repos/{repo}.yaml`** with batch/live sub-keys | Eliminates drift; batch and live sections are nullable                                                                                              |
| `DR-01..DR-03` validator IDs (disaster recovery)                                     | **Preserved in `code_audit_items`** (different from DR1–DR6 stages) | Naming collision noted in template comments                                                                                                         |

---

## Section 5: Recommended schema structure (implemented in v3.0)

The v3.0 schema in `REPO_READINESS_CHECKLIST.yaml` implements the following structure:

```
schema_version: "3.0"
repo: "{REPO_NAME}"
repo_type: library-t0|library-t1|library-t2|library-t3|service|api|ui|infra
arch_tier: 0|1|2|3|service|api|ui|infra
deployment_modes: null | ["batch"] | ["live"] | ["batch","live"]
business_modes: null | ["batch"] | ["live"] | ["batch","live"]

code_readiness:
  current_stage: CR0..CR5
  cr1_functionality: { status, criteria, evidence, notes }
  cr2_unit_tests: { status, coverage_pct, coverage_floor_pct, evidence }
  cr3_integration_tests: { status, manifest_dep_count, manifest_deps_covered, manifest_deps_missing, evidence }
  cr4_quality_gate: { status, last_run_date, basedpyright_errors, ruff_errors, evidence }
  cr5_quickmerge: { status, branch, ci_url, merged_to_main, evidence }

deployment_readiness:
  current_stage: DR0..DR6
  na_reason: null | "library; wheel published to AR, not deployed as Cloud Run service"
  batch: null | { dr1_infra..dr6_prod_ready }  # null if deployment_modes excludes batch
  live:  null | { dr1_infra..dr6_prod_ready }  # null if deployment_modes excludes live

business_readiness:
  current_stage: BR0..BR8
  batch: null | { br1_acceptance_criteria..br8_user_approved }
  live:  null | { br1_acceptance_criteria..br8_user_approved }

code_audit_items:
  # All validator IDs from _checklist-template-enhanced.yaml
  # COD-01..COD-25, OBS-01..OBS-13, DAT-01..DAT-23
  # SEC-01..SEC-05, SECURITY-03..SECURITY-05
  # INF-04..INF-15, ARC-02, ARC-11
  # BASE-13..BASE-32, HARDENING-01..06
  # REGULATORY-01..04, DR-01..03
```

**Key design decisions confirmed**:

- `unified-trading-pm/configs/` is SSOT for **operational data** (sharding configs, venues.yaml, data-catalogue,
  expected_start_dates.yaml). `deployment-service/configs/` has symlinks to PM. These are NOT in the readiness template.
- `code_audit_items` is a complementary automation cross-reference, NOT a replacement for CR/DR/BR.
- `DR-01..DR-03` (disaster recovery validator IDs) are distinct from `DR1–DR6` (deployment readiness stages).
- Libraries set `deployment_modes: null` and `na_reason: "library; wheel published to AR"` on deployment_readiness.

---

## Status at 2026-03-11

- `REPO_READINESS_CHECKLIST.yaml` — **EXISTS at v3.0** (created by Stream A). All gaps above are resolved.
- `consolidation-gap-analysis.md` — full detailed analysis (supersedes this file for historical detail).
- `batch/` and `live/` directories — **do not exist** (were never populated in this workspace; no archive needed).
- Per-repo `repos/*.yaml` files — being created by p1b (separate stream).
