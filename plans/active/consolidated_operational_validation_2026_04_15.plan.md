---
name: consolidated-operational-validation
overview: |
  Consolidated remaining operational, E2E, and infrastructure validation work from 4 source plans.
  Covers: cluster E2E tests, pipeline scheduling gaps, QG sweeps, data type cleanup, trade booking QG.
type: mixed
epic: epic-deployment
status: active

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

todos:
  # ══════════════════════════════════════════════════════════════
  # GROUP A — Pipeline Scheduling Remaining Code
  # ══════════════════════════════════════════════════════════════
  - id: ups-p2-run-tag-mtds-calendar
    content: "Wire --run-tag into MTDS GCS output path + features-calendar-service (PARTIALLY_DONE — CLI flag exists)"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p4-sports-trigger-backend-dispatch
    content:
      "Sports trigger scheduler cloud backend dispatch (PARTIALLY_DONE — local subprocess works, cloud placeholder)"
    status: todo
    source: unified_pipeline_scheduling_and_triggers

  # ══════════════════════════════════════════════════════════════
  # GROUP B — E2E Cluster Tests
  # ══════════════════════════════════════════════════════════════
  - id: ups-p8-e2e-cefi
    content: "[HUMAN+AGENT] E2E test: CEFI cluster — T+1, live 1h, reconciliation"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p8-e2e-sports
    content: "[HUMAN+AGENT] E2E test: SPORTS cluster — T+1, trigger scheduler, feature validation"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p8-e2e-defi
    content: "[HUMAN+AGENT] E2E test: DEFI cluster — T+1 single day"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p8-e2e-tradfi
    content: "[HUMAN+AGENT] E2E test: TRADFI cluster — T+1 single day (needs DATABENTO_API_KEY)"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p8-e2e-prediction
    content: "[HUMAN+AGENT] E2E test: PREDICTION cluster — T+1 single day"
    status: todo
    source: unified_pipeline_scheduling_and_triggers
  - id: ups-p8-e2e-full
    content: "[HUMAN+AGENT] E2E test: FULL cluster — all categories for 1 date"
    status: todo
    source: unified_pipeline_scheduling_and_triggers

  # ══════════════════════════════════════════════════════════════
  # GROUP C — Infrastructure Cleanup
  # ══════════════════════════════════════════════════════════════
  - id: rdt-p4-gcs-cleanup
    content: "[HUMAN] Run instruments-service backfill to regenerate parquet without data_types column"
    status: todo
    source: remove_data_types_field
  - id: rdt-p4-workspace-qg
    content: "Run quality-gates.sh on all 5 affected repos"
    status: todo
    source: remove_data_types_field
  - id: mtb-p2f-execution-qg
    content: "Run quality-gates.sh on execution-service"
    status: todo
    source: manual_trade_booking_reconciliation
  - id: mtb-p6e-final-qg-sweep
    content: "Full QG sweep across all 6 affected repos"
    status: todo
    source: manual_trade_booking_reconciliation
  - id: isr-t2i-qg-quickmerge
    content: "instruments-service: run quality-gates.sh + quickmerge"
    status: in_progress
    source: instruments_service_template_refactor

isProject: false
---

# Consolidated Operational Validation

Remaining work from 4 source plans. Most items are E2E cluster tests requiring API keys and real environments.
Infrastructure cleanup (remove_data_types, trade booking QG) is small but needs sequential execution.
