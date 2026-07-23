---
doc_type: codex-ssot
title: Readiness Checklist Consolidation — Gap Analysis
summary:
  2026-03-11 Phase-0 read-only gap analysis feeding the v3.0 canonical readiness template — reconciles the
  deployment-service 52-item checklist, the codex enhanced template, and the CR/DR/BR stage model; decides
  data-catalogue items are operational (SSOT in pm/configs) not readiness, and merges the retired batch/ + live/ split
  into per-repo repos/<name>.yaml. Pre-v3.0 planning record.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    deployment-ui,
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [audit, readiness, consolidation, data-catalogue, ssot-audit]
related: [/codex/10-audit/gap-analysis-2026-03-11.md, /codex/10-audit/ssot-reference-mapping.md]
created: 2026-03-27
authoritative_for: [readiness-checklist consolidation gap analysis (pre-v3.0 record)]
referenced_by: [/codex/10-audit/gap-analysis-2026-03-11.md, /codex/10-audit/ssot-reference-mapping.md]
owner:
last_reviewed:
code_refs:
---

# Readiness Checklist Consolidation — Gap Analysis

**Date**: 2026-03-11 **Author**: Stream A (automated) **Purpose**: Phase 0 READ-ONLY analysis before creating v3.0
canonical template

---

## Sources Analysed

| Source                                                       | Description                                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `10-audit/_checklist-template-enhanced.yaml`                 | v2.0 enhanced template (COD-01 through REGULATORY-04) — 38 representative items, 9 sections |
| `10-audit/batch/*.yaml` + `10-audit/live/*.yaml`             | Per-service operational checklists using `baseline_items` dict with validator IDs           |
| `deployment-service/configs/checklist.template.service.yaml` | 52-item 7-phase operational readiness template                                              |
| `unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md`        | CR/DR/BR stage model — the v3.0 source of truth for readiness axes                          |
| `10-audit/ssot-reference-mapping.md`                         | Domain → SSOT authority mapping                                                             |

---

## Gap 1: deployment-service/configs items NOT in CR/DR/BR model

The `checklist.template.service.yaml` in deployment-service contains 52 items organized in 7 phases (Repo Foundation,
Testing, Deployment, Local Validation, Production, Docs, Data Catalogue). The CR/DR/BR model covers most of these but
the following are **not explicitly surfaced** in the CR/DR/BR stage names:

| deployment-service item                                            | Closest CR/DR/BR mapping | Gap                                                                                                                                       |
| ------------------------------------------------------------------ | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1: Repo foundation (README, pyproject, Dockerfile)           | DR1 (infra deployable)   | Dockerfile in DR1 but README/pyproject not explicit                                                                                       |
| Phase 2: Testing — unit + integration + e2e                        | CR2, CR3, CR4            | Covered, no gap                                                                                                                           |
| Phase 3: CI/CD deployment (cloudbuild, Cloud Run)                  | DR1–DR2                  | Covered                                                                                                                                   |
| Phase 4: Local validation (runbooks, smoke routes)                 | DR3                      | Partially — runbook is in DR6, smoke in DR3                                                                                               |
| Phase 5: Production (DISABLE_AUTH check, CVE scan)                 | DR6                      | Covered                                                                                                                                   |
| Phase 6: Docs (CONFIGURATION.md, runbook)                          | DR6                      | Covered                                                                                                                                   |
| Phase 7: Data catalogue (sharding.yaml, expected_start_dates.yaml) | Not in CR/DR/BR          | **GAP** — data catalogue items (ARC-02, BASE-20, BASE-21, BASE-23) exist in v2.0 audit items but are absent from the CR/DR/BR stage model |
| MVP coverage validation (BASE-22, venues.yaml)                     | Not in CR/DR/BR          | **GAP** — MVP data coverage validation is operational/deployment-specific                                                                 |
| PubSub topics subscription list                                    | Not in CR/DR/BR          | **GAP** — operational metadata in deployment-service checklists has no counterpart in readiness stages                                    |
| Data catalogue completion % (stage_1, stage_2)                     | Not in CR/DR/BR          | **GAP** — batch data completeness tracking is operational, not in readiness model                                                         |

**Resolution in v3.0**: Add `code_audit_items` section to REPO_READINESS_CHECKLIST.yaml for automated validator items
(COD-01..REGULATORY-04, ARC-02, BASE-20..BASE-22). Keep data-catalogue operational items in deployment-service/configs/
as SSOT per ssot-reference-mapping.md (they are OPERATIONAL data, not readiness criteria).

---

## Gap 2: batch/live files items NOT in enhanced template

The `10-audit/batch/*.yaml` and `10-audit/live/*.yaml` files use a flat `baseline_items` dict referencing all 110
validator IDs (BASE-01..COD-25, HARDENING-01..06, REGULATORY-01..04, DR-01..03, SECURITY-03..05). The
`_checklist-template-enhanced.yaml` covers only 38 representative items.

**Items in batch/live files but absent from enhanced template (v2.0)**:

- `BASE-01..BASE-18`: Core baseline items (referenced in batch/live but not defined in enhanced template)
- `OBS-02..OBS-04`, `OBS-07..OBS-13`: Additional observability items
- `DAT-04..DAT-12`, `DAT-13`, `DAT-16`, `DAT-18..DAT-21`, `DAT-23`: Extended data quality items
- `COD-06..COD-09`, `COD-11..COD-13`, `COD-15`, `COD-17..COD-19`, `COD-22..COD-25`: Additional coding standards
- `INF-01..INF-03`, `INF-06..INF-07`, `INF-09..INF-15`: Additional infrastructure items
- `SEC-03..SEC-04`: Additional security items
- `SECURITY-03..SECURITY-05`: Extended security validator IDs
- `HARDENING-01..HARDENING-06`: Fail-loud hardening items
- `BASE-13..BASE-15`, `BASE-24..BASE-32`: Extended baseline items
- `REGULATORY-01..REGULATORY-04`: Regulatory compliance items
- `DR-01..DR-03`: Disaster recovery items (different from the DR1–DR6 deployment readiness stages!)

**Resolution in v3.0**: The `code_audit_items` section in the v3.0 template will carry all validator IDs as
`automation_checks`. The CR/DR/BR sections carry the human-readable readiness stage status. These are complementary —
automation items feed into CR1/CR4 criteria.

---

## Gap 3: batch/live split structure

The existing `10-audit/batch/` and `10-audit/live/` directories contain per-service files. The same service appears in
BOTH directories if it supports both modes (e.g. execution-service, features-service (calendar family)). This
duplication is intentional for the old schema but creates drift risk.

**Repos with entries in BOTH batch and live directories**:

- execution-service, features-service (calendar family), features-service (delta-one family), features-service (onchain
  family), features-service (sports family), features-service (volatility family), instruments-service,
  market-data-processing-service, market-tick-data-service, ml-inference-service, ml-training-service,
  pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service, strategy-service

**Repos in batch/ only**: alerting-system, backtest-ui, batch-audit-ui, client-reporting-ui, cross-service,
exchange-interface-library, live-health-monitor-ui, logs-dashboard-ui, ml-deployment-ui (corporate actions are owned by
`features-service (calendar family)`, not a standalone repo; the legacy `corporate-actions` label referred to archived
paths, not a separate repository)

**Repos in live/ only**: cross-service (also in batch)

**Resolution in v3.0**: Single `repos/{repo-name}.yaml` file per repo with `batch:` and `live:` sub-sections within each
of the DR/BR sections. Eliminates duplication. Old batch/ and live/ directories move to `_archive/`.

---

## Gap 4: Readiness stage model vs. validator IDs

The v2.0 enhanced template uses item IDs like `COD-01`, `OBS-05` etc. tied to automated validators. The CR/DR/BR model
uses human readiness stages (CR1–CR5, DR1–DR6, BR1–BR8). These need to be unified:

| CR/DR/BR Stage          | Maps to Validator IDs                          |
| ----------------------- | ---------------------------------------------- |
| CR1 (functionality)     | HARDENING-01..06, COD-04..05, BASE-01..03      |
| CR2 (unit tests)        | COD-10, COD-14, COD-16                         |
| CR3 (integration tests) | COD-11..13                                     |
| CR4 (QG passing)        | COD-14, COD-16, COD-21, SEC-01..05, INF-04..08 |
| CR5 (quickmerge)        | No validator — CI outcome                      |
| DR1 (infra)             | INF-04, INF-08, ARC-02                         |
| DR2 (CI smoke)          | COD-14, COD-16                                 |
| DR3 (feature env)       | INF-01..03                                     |
| DR4 (staging SIT)       | DAT-01..23, ARC-11                             |
| DR5 (load/perf)         | No specific validator                          |
| DR6 (prod-ready)        | SEC-01..05, REGULATORY-01..04                  |
| BR2 (circuit breaker)   | ARC-08                                         |
| BR3 (events)            | OBS-05, OBS-06                                 |
| BR4 (perf targets)      | BASE-22, DAT-16                                |

**Resolution in v3.0**: `code_audit_items` section preserves all validator IDs. CR/DR/BR sections reference them via
`criteria` text and the audit cross-reference table.

---

## Summary: What v3.0 Must Do

1. **Single file per repo** — replace batch/ + live/ split with `repos/{repo}.yaml` containing batch/live sub-keys
2. **CR/DR/BR as primary schema** — the human readiness model is the top-level structure
3. **`code_audit_items` sub-section** — preserves all automated validator IDs (COD-01..REGULATORY-04)
4. **NA rules codified in YAML** — libraries: all DR items NA; UIs: BR2+BR5 NA; non-revenue: BR5 NA
5. **unified-trading-pm/configs/** is SSOT for sharding, venues, data-catalogue operational data (symlinked into
   `deployment-service/configs/`)
6. **Archive old batch/live** — `_archive/batch/` and `_archive/live/`
7. **README declares SSOT** — `10-audit/` becomes canonical for all repo readiness state
