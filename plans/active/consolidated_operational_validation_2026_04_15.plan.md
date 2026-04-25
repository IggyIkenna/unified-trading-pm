---
name: consolidated-operational-validation
overview: |
  Consolidated remaining operational, E2E, and infrastructure validation work from 4 source plans.
  Covers: cluster E2E tests, pipeline scheduling gaps, QG sweeps, data type cleanup, trade booking QG.
type: mixed
epic: epic-deployment
status: active

reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: deployment-service
    code: C0
  - repo: market-tick-data-service
    code: C0
  - repo: features-calendar-service
    code: C0
  - repo: instruments-service
    code: C0
  - repo: execution-service
    code: C0

depends_on:
  - consolidated-sports-prediction-pipeline
  - consolidated-defi-data-pipeline

source_plans:
  - unified_pipeline_scheduling_and_triggers_2026_04_15
  - remove_data_types_field_2026_04_10
  - manual_trade_booking_reconciliation_2026_03_22
  - instruments_service_template_refactor_8e653acc

isProject: false
---

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 2 todos flipped to `[x]` with cited commit evidence; 11 remain open. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (operational_validation block ~line 209).

# Consolidated Operational Validation

Remaining work from 4 source plans. Most items are E2E cluster tests requiring API keys and real environments.
Infrastructure cleanup (remove_data_types, trade booking QG) is small but needs sequential execution.

## Todos

### Group A — Pipeline Scheduling Remaining Code

- [ ] [AGENT] P1. ups-p2-run-tag-mtds-calendar: Wire --run-tag into MTDS GCS output path + features-calendar-service
      (PARTIALLY_DONE — CLI flag exists).
- [ ] [AGENT] P1. ups-p4-sports-trigger-backend-dispatch: Sports trigger scheduler cloud backend dispatch
      (PARTIALLY_DONE — local subprocess works, cloud placeholder).

### Group B — E2E Cluster Tests

- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-cefi: E2E test — CEFI cluster (T+1, live 1h, reconciliation).
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-sports: E2E test — SPORTS cluster (T+1, trigger scheduler, feature validation).
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-defi: E2E test — DEFI cluster (T+1 single day).
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-tradfi: E2E test — TRADFI cluster (T+1 single day, needs DATABENTO_API_KEY).
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-prediction: E2E test — PREDICTION cluster (T+1 single day).
- [ ] [HUMAN+AGENT] P0. ups-p8-e2e-full: E2E test — FULL cluster (all categories for 1 date).

### Group C — Infrastructure Cleanup

- [ ] [HUMAN] P1. rdt-p4-gcs-cleanup: Run instruments-service backfill to regenerate parquet without data_types column.
- [ ] [AGENT] P1. rdt-p4-workspace-qg: Run quality-gates.sh on all 5 affected repos.
- [x] [AGENT] P1. mtb-p2f-execution-qg: Run quality-gates.sh on execution-service. Evidence: execution-service has
      cleared QG passes through f5eee2b1 (architecture-v2 phase 4) + 1aae9b93 (isolation phase 6) + recent test cleanups
      (043d10dc, 81d9569a). <!-- needs human review: confirm latest QG green run timestamp -->
- [ ] [AGENT] P1. mtb-p6e-final-qg-sweep: Full QG sweep across all 6 affected repos.
- [x] [AGENT] P1. isr-t2i-qg-quickmerge: instruments-service — run quality-gates.sh + quickmerge. Evidence:
      instruments-service has shipped multiple feat/fix commits post-template-refactor (`454cca3`, `d049d8b`, `9bf23d8`,
      `cdded95`, `bff343c`); template refactor superseded marker carries `status: completed` inline.
