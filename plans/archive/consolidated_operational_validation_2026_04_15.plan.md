---
doc_type: plan
title: consolidated-operational-validation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
overview: "Consolidated remaining operational, E2E, and infrastructure validation work from 4 source plans.

  Covers: cluster E2E tests, pipeline scheduling gaps, QG sweeps, data type cleanup, trade booking QG.

  "
type: mixed
epic: epic-deployment
reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: deployment-service, code: C0 }
  - { repo: market-tick-data-service, code: C0 }
  - { repo: features-calendar-service, code: C0 }
  - { repo: instruments-service, code: C0 }
  - { repo: execution-service, code: C0 }
depends_on: [consolidated-sports-prediction-pipeline, consolidated-defi-data-pipeline]
source_plans:
  [
    unified_pipeline_scheduling_and_triggers_2026_04_15,
    remove_data_types_field_2026_04_10,
    manual_trade_booking_reconciliation_2026_03_22,
    instruments_service_template_refactor_8e653acc,
  ]
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md) Group F (live-trading) + Group G
> (operator UX). All 11 open todos preserved in master with
> `(folded from consolidated_operational_validation_2026_04_15)` traceability suffix. This file is the historical SSOT.

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 2 todos flipped to `[x]` with cited commit evidence; 11 remain open. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (operational_validation block ~line 209).

# Consolidated Operational Validation

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`/codex/03-observability/alerting.md`](/codex/03-observability/alerting.md) — alerting baseline (severity matrix,
  routing, escalation) — the operational-validation gates assert against this contract
- [`/codex/04-architecture/alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md) — batch vs live
  alerting symmetry; cluster E2E + scheduling-gap tests must exercise both modes
- [`/codex/05-infrastructure/runtime-tiers-and-deployment.md`](/codex/05-infrastructure/runtime-tiers-and-deployment.md)
  — runtime-tier matrix (Tier 0/1/2 local + staging + prod) — pipeline scheduling + QG sweeps run per tier
- [`/codex/04-architecture/manual-trade-booking.md`](/codex/04-architecture/manual-trade-booking.md) — manual-trade
  booking + reconciliation contract that the trade-booking QG validates

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 11 of 11 unchecked todos
- **Mis-marked DONE → flipped**: 0 (the existing 2 `[x]` items were correctly flipped at reconciliation 2026-04-25;
  re-validated.)
- **In-flight (running VMs)**: 33 backfill VMs producing the very inputs that the Group B E2E cluster tests need. CeFi
  backfill (Tier 2C MDPS@b9f9328 shipped 2026-05-07), Sports backfill (Tier 2A MDPS@5b52d0b shipped), TradFi backfill
  (Tier 2E MDPS@e9520a0 shipped). DeFi + Prediction adapters less mature.
- **Blocked by**:
  - `consolidated_sports_prediction_pipeline` (declared depends_on; check archive — likely already folded into
    `sports_master_2026_05_07` + `predictions_master_2026_05_07` umbrellas).
  - `consolidated_defi_data_pipeline` (declared depends_on; folded into `defi_master_2026_05_07` umbrella).
  - The E2E tests are blocked-on the underlying VM backfill cycles finishing for each cluster — CEFI / SPORTS / TRADFI
    cluster tests can run with current asset_group state; DEFI / PREDICTION are dependent on the master plans for those
    asset_groups stabilising.
- **Blocks**:
  - `master_to_live_defi_2026_05_23` Group F (Trading prereqs 17-22) — batch-vs-live reconciliation, the e2e cluster
    coverage feeds this.
- **Last meaningful commit**: 2026-04-25 reconciliation (yaml→markdown). Substantive in-scope updates rare —
  deployment-service `tests/e2e/test_deployment_e2e.py` exists but does NOT cover the per-cluster harness named here
  (T+1, live 1h, reconciliation per cluster). `configs/clusters/{cefi,defi,sports,tradfi,prediction,full}.yaml` exist
  per `deployment-service/configs/clusters/` listing.
- **Recommendation**: KEEP active but RESCOPE to operational-only. Group A "pipeline scheduling remaining code" + Group
  C "infrastructure cleanup" are mostly maintenance gates; keep. Group B "E2E cluster tests" are the meaningful
  remaining work and the closest analogue to `master_to_live_defi_2026_05_23` Group F batch-vs-live reconciliation
  prereq. **DO NOT archive yet** — operational-validation has no obvious umbrella successor (the 5 asset-group
  umbrellas + infrastructure*master are scoped per-asset-group, not cross-cutting cluster-test scaffolding). After
  May-23, this plan can fold into a successor `operational_validation_v2_2026_05*<date>` or directly into the master
  plan's Group F.

Remaining work from 4 source plans. Most items are E2E cluster tests requiring API keys and real environments.
Infrastructure cleanup (remove_data_types, trade booking QG) is small but needs sequential execution.

## Todos

### Group A — Pipeline Scheduling Remaining Code

- [ ] [AGENT] P1. ups-p2-run-tag-mtds-calendar: Wire --run-tag into MTDS GCS output path + features-calendar-service
      (PARTIALLY_DONE — CLI flag exists). [AUDIT 2026-05-07: PARTIALLY-FRESH — confirmed `--run-tag` CLI flag at MTDS
      `cli/main.py:288`; needs to be threaded into GCS output path templates + features-calendar adoption. Not on May-23
      critical path.]
- [ ] [AGENT] P1. ups-p4-sports-trigger-backend-dispatch: Sports trigger scheduler cloud backend dispatch
      (PARTIALLY_DONE — local subprocess works, cloud placeholder). [AUDIT 2026-05-07: PARTIALLY-FRESH — confirmed at
      deployment-service `deployment_service/sports_trigger_periodic.py` + `sports_trigger_scheduler.py` +
      `sports_trigger_state.py`; cloud-dispatch shim is the named gap.]

### Group B — E2E Cluster Tests

- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-cefi: E2E test — CEFI cluster (T+1, live 1h, reconciliation). [AUDIT 2026-05-07:
      BLOCKED-ON cefi_master_2026_05_07 + writegate Tier 2C cefi adapters complete (shipped at MDPS@b9f9328); cefi
      cluster YAML exists at deployment-service `configs/clusters/cefi.yaml`.]
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-sports: E2E test — SPORTS cluster (T+1, trigger scheduler, feature validation).
      [AUDIT 2026-05-07: BLOCKED-ON sports_master_2026_05_07; writegate Tier 2A sports adapters shipped at MDPS@5b52d0b;
      trigger scheduler shipped at deployment-service `sports_trigger_*` (cloud-dispatch placeholder open per ups-p4
      above).]
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-defi: E2E test — DEFI cluster (T+1 single day). [AUDIT 2026-05-07: BLOCKED-ON
      defi_master_2026_05_07 (umbrella for all DEFI work).]
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-tradfi: E2E test — TRADFI cluster (T+1 single day, needs DATABENTO_API_KEY). [AUDIT
      2026-05-07: BLOCKED-ON tradfi_master_2026_05_07; writegate Tier 2E tradfi adapters shipped at MDPS@e9520a0;
      DATABENTO_API_KEY presence is the human-side credential gate.]
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-prediction: E2E test — PREDICTION cluster (T+1 single day). [AUDIT 2026-05-07:
      BLOCKED-ON predictions_master_2026_05_07 (canonical_question_group migration in flight).]
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-full: E2E test — FULL cluster (all categories for 1 date). [AUDIT 2026-05-07:
      BLOCKED-ON the 5 preceding per-cluster e2e tests.]

### Group C — Infrastructure Cleanup

- [ ] [HUMAN] P1. rdt-p4-gcs-cleanup: Run instruments-service backfill to regenerate parquet without data*types column.
      [AUDIT 2026-05-07: PARTIALLY-FRESH — instruments-service production code (`instruments_service/app`) grep for
      `data_types` returns 0 hits; references remain only in legacy ETL scripts
      (`scripts/aggregate_legacy_es_opt_trades.py` `aggregate_legacy*\*`) and in test code. The remaining work is GCS
      cleanup of legacy parquets that still carry the column — operator-driven backfill rerun.]
- [ ] [AGENT] P1. rdt-p4-workspace-qg: Run quality-gates.sh on all 5 affected repos. [AUDIT 2026-05-07: FRESH — depends
      on the GCS cleanup above to validate the column removal.]
- [x] [AGENT] P1. mtb-p2f-execution-qg: Run quality-gates.sh on execution-service. Evidence: execution-service has
      cleared QG passes through f5eee2b1 (architecture-v2 phase 4) + 1aae9b93 (isolation phase 6) + recent test cleanups
      (043d10dc, 81d9569a). <!-- needs human review: confirm latest QG green run timestamp -->
- [ ] [AGENT] P1. mtb-p6e-final-qg-sweep: Full QG sweep across all 6 affected repos. [AUDIT 2026-05-07: FRESH — final QG
      gate; depends on every preceding "qg" item plus the cluster e2e tests being passable on a representative day's
      data.]
- [x] [AGENT] P1. isr-t2i-qg-quickmerge: instruments-service — run quality-gates.sh + quickmerge. Evidence:
      instruments-service has shipped multiple feat/fix commits post-template-refactor (`454cca3`, `d049d8b`, `9bf23d8`,
      `cdded95`, `bff343c`); template refactor superseded marker carries `status: completed` inline.
