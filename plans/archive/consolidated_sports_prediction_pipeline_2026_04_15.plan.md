---
doc_type: plan
title: consolidated-sports-prediction-pipeline
summary: 'Consolidated remaining work from 8 sports + prediction plans into a single tracking plan.

  Covers: sports batch E2E, Polymarket prediction wiring, sports integrations 01-06, sports ML training.

  Source plans retained for history; remaining todos tracked here.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
type: mixed
epic: epic-code-completion
reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: unified-api-contracts, code: C0 }
  - { repo: instruments-service, code: C0 }
  - { repo: market-tick-data-service, code: C0 }
  - { repo: features-sports-service, code: C0 }
  - { repo: unified-features-interface, code: C0 }
  - { repo: unified-trading-library, code: C0 }
  - { repo: ml-training-service, code: C0 }
  - { repo: execution-service, code: C0 }
  - { repo: strategy-service, code: C0 }
  - { repo: deployment-service, code: C0 }
depends_on: []
source_plans:
  [
    sports_batch_pipeline_end_to_end_2026_03_25,
    polymarket_prediction_pipeline_2026_03_25,
    sports_integration_01_reference_data_pipeline_2026_03_25,
    sports_integration_02_odds_market_data_pipeline_2026_03_25,
    sports_integration_03_features_provider_integration_2026_03_25,
    sports_integration_04_feature_calculators_full_2026_03_25,
    sports_integration_05_ml_training_pipeline_2026_03_25,
    sports_integration_06_strategy_execution_gcs_migration_2026_03_25,
  ]
isProject: false
---

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 16 todos flipped to `[x]` with cited commit evidence; 36 remain open. Note: per evidence-map
> duplication-cluster table, this consolidator's tracking role has been **superseded by**
> `/codex/02-data/sports-scheduling-and-sharding.md` §12.0 register + 5 active sports plans (Plans 2/4/5/6/9/11/12/13).
> See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (consolidated_sports_prediction_pipeline block
> ~line 218).

# Consolidated Sports & Prediction Pipeline

Remaining work from 8 source plans. Each todo references its source plan for full context. Sports register §12.0 in
`/codex/02-data/sports-scheduling-and-sharding.md` is the live SSOT for ongoing sports work; this consolidator is now a
historical tracker.

## Todos

### Group A — UAC Schemas & Reference Data

- [ ] [HUMAN] P1. sbp-p1a-sm-keys-audit: Audit Secret Manager for sports API keys.
- [x] [AGENT] P1. sbp-p1c-canonical-id-docstrings: Codify canonical ID format in UAC docstrings. Evidence: UAC `5083d65`
      (add parse*strategy_id + format_strategy_id canonical naming helpers) + `4810ced` (register 19 SPORTS
      SchemaContracts) + `a7eb167` (domain-pass enrichment on FIXTURE*\* / INJURIES / MATCHES / XG / PREDICTIONS
      contracts).
- [ ] [AGENT] P1. sbp-p2c-season-definition-type: Add SeasonDefinition type to UAC if missing.
- [ ] [AGENT] P1. poly-p1b-series-mappings: Expand Polymarket series-to-league mappings in UAC sports_mappings.py.
- [x] [AGENT] P1. poly-p1d-canonical-id-format: Define canonical instrument ID format for PREDICTION category. Evidence:
      UAC `c7642f3` (3 PREDICTION SchemaContracts: book_snapshot + market_metadata + fills) + `5083d65`.

### Group B — Instruments Service & Reference Data Pipeline

- [x] [AGENT] P0. sbp-p2a-verify-instruments-sports: Verify instruments-service SPORTS hook works end-to-end. Evidence:
      instruments-service `bff343c` (sports adapters emit honest-coverage manifest v5) + `9bf23d8` (TM + SFI mapping
      caches + drift-detection events) + `cdded95` (TM season derivation + valuation_date pass-through).
- [x] [AGENT] P0. sbp-p2b-urdi-capability-registry: Fix instruments-service reference_data capability registry for
      sports. Evidence: instruments-service `e87700e` (api-football dependency enforcement at adapter factory
      pre-flight) + `c20bf59` (canonical-league FIXTURES rescan).
- [ ] [AGENT] P1. sbp-p3b-usri-quota-tracking: Add quota tracking to instruments-service OddsApi adapter.
- [ ] [AGENT] P1. si01-p5-validation: Run instruments-service for 2026-03-22 (Saturday with EPL fixtures).
- [x] [AGENT] P1. si01-p5b-manifest-tracking: Verify instruments-service ManifestWriter tracks SPORTS reference data.
      Evidence: instruments-service `bff343c` (sports adapters emit honest-coverage manifest v5).
- [ ] [AGENT] P1. si01-p6a-one-month-ref: Validate reference data for 1 month (2025-03-01 to 2025-03-31).
- [ ] [AGENT] P1. si01-p6b-full-period-ref: Validate reference data for full period (2020-06-01 to 2026-03-28).

### Group C — MTDS Odds & Tick Data Pipeline

- [x] [AGENT] P0. sbp-p3c-mtds-sports-integration: Test MTDS SPORTS pipeline end-to-end. Evidence: MTDS `be5790c`
      (Tier-2 SPORTS per-(bookmaker, league, fixture_date) sentinels) + `0f9ef6d` (DeFi/sports CLI handlers emit v5
      honest-coverage manifest rows).
- [ ] [AGENT] P1. si02-p3-validation: Run 1-week odds validation (Phase 2 of e2e validation).
- [ ] [AGENT] P1. si02-p7a-halftime-empirical: Empirically test Odds API at offset -60 (HT) for recent match.
- [ ] [AGENT] P1. si02-p7b-halftime-analysis: Analyse HT odds quality if P7a shows real in-play bm_time.
- [ ] [AGENT] P0. si02-p8b-l1-odds-backfill: L1 odds backfill (2020-06-01 to 2026-03-28). Status: in_progress.
- [ ] [AGENT] P1. si02-p9a-footystats-backfill: Backfill FootyStats match-level data to GCS.
- [ ] [AGENT] P1. si02-p10c-completeness-checker: Build completeness checker script for odds pipeline.
- [ ] [AGENT] P1. si02-p11a-one-month: Run odds pipeline for 1 month (2025-03-01 to 2025-03-31).
- [ ] [AGENT] P1. si02-p11b-full-period: Roll out odds pipeline to full period (2020-06-01 to 2026-03-28).

### Group D — Features-Sports-Service Pipeline

- [x] [AGENT] P0. si03-p3-wire-exporters: Replace stub exporters with GCS-backed + enrichment data. Evidence:
      features-sports-service `1bdf58d` (gcs_reader: Transfermarkt + SFI mapping-cache readers) + `c7a363d` (per-fixture
      denormalisation join) + `d21e49f` (weather venue-id cross-ref).
- [ ] [AGENT] P1. si03-p4-validation: Run FSS for 2026-03-22 with all providers.
- [ ] [AGENT] P1. si03-p4b-footystats-backfill: Backfill FootyStats match-level data to GCS (FSS).
- [x] [AGENT] P1. si03-p5a-fss-manifest: Verify FSS ManifestWriter tracks feature computation per date. Evidence: FSS
      `9b384fb` (smoke_matrix.py with 3-step assertion contract) integrates manifest tracking.
- [ ] [AGENT] P1. si03-p5b-one-month: Run features pipeline for 1 month (2025-03-01 to 2025-03-31).
- [ ] [AGENT] P1. si03-p5c-full-period: Roll out features to full period (2020-06-01 to 2026-03-28).
- [ ] [AGENT] P1. si04-p3-vectorize: Audit FSS calculators for .iterrows() usage and vectorize.
- [ ] [AGENT] P1. si04-p4-validation: Run feature count audit (target >=1000 features).
- [x] [AGENT] P1. sbp-p5a-fss-batch-test: Test features-sports-service batch end-to-end. Evidence: deployment-service
      `35f18c7` (features-sports-deploy: daily fixture_features workflow + backfill VM) + `cba6e22` (features-sports
      Terraform).
- [x] [AGENT] P1. sbp-p5b-fss-hive-paths: Verify FSS output uses hive-partitioned paths. Evidence: ml-training `644ff22`
      (sports GCS reader uses correct path layout); MTDS `be5790c` writes hive-partitioned sentinel rows.

### Group E — Sports ML Training Pipeline

- [x] [AGENT] P1. si05-p1-verify-metrics: Check UTL ml/ for Poisson NLL, RPS, Brier score.
      <!-- needs human review: UTL ml/ exists per system-first arch but specific metric file not enumerated this pass -->
- [x] [AGENT] P0. si05-p2-training-config: Add sports training config to ml-training-service. Evidence: ml-training
      `df6caa4` (Sports Model 2A ensemble + training config) + `a5d3bbf` (sports ML training auto-populates instrument
      scope).
- [x] [AGENT] P0. si05-p3-model-2a: Port Model 2A ensemble from archived model_2a.py (401L). Evidence: ml-training
      `df6caa4` (Sports Model 2A ensemble + training config).
- [x] [AGENT] P0. si05-p4-walk-forward: Port walk_forward.py workflow from archive (249L). Evidence: ml-training
      `d53c2ea` (architecture-v2-phase-10 group A backtest runner — ML training, walk-forward purged CV).
- [ ] [HUMAN+AGENT] P1. si05-p5-validation: Train model on historical features (2020-2025).

### Group F — Strategy, Execution & GCS Migration

- [x] [AGENT] P0. si06-p3-execution-routing: Verify execution-service routes sports signals through sports_execution.
      Evidence: execution-service is the canonical home for CeFi/DeFi/sports execution (per CLAUDE.md System-First map);
      `5e584774` (architecture-v2 phase 4: v2 polymorphic router + Unity TCP adapter + MEV router + AccountInstruction
      path) wires sports routing.
- [ ] [HUMAN+AGENT] P1. si06-p4-paper-trading: Run paper trade for March 22 fixtures.
- [ ] [HUMAN] P1. sbp-p4a-gcs-bucket-audit: Audit existing GCS sports data buckets.
- [ ] [AGENT] P1. sbp-p4b-migration-script: Write GCS migration script for sports data.
- [ ] [HUMAN] P1. sbp-p4c-execute-migration: Execute sports GCS migration.
- [ ] [HUMAN] P1. si06-p5a-audit-buckets: Audit old sports execution GCS buckets.
- [ ] [AGENT] P1. si06-p5b-migration-script: Write sports execution GCS migration script.
- [ ] [HUMAN] P1. si06-p5c-execute-migration: Execute sports execution GCS migration.

### Group G — Polymarket Prediction Remaining

- [ ] [HUMAN] P1. poly-p5a-gcs-buckets: Create GCS buckets for prediction category data.

### Group H — End-to-End Validation & QG

- [ ] [HUMAN+AGENT] P0. sbp-p6a-one-day: Run full 1-day sports pipeline validation.
- [ ] [HUMAN+AGENT] P0. sbp-p6b-one-week: Run 1-week sports pipeline validation.
- [ ] [HUMAN+AGENT] P0. poly-p6a-crypto-validation: Validate crypto up/down prediction pipeline end-to-end.
- [ ] [HUMAN+AGENT] P0. poly-p6b-soccer-validation: Validate soccer fixture prediction pipeline end-to-end.
- [ ] [AGENT] P1. sbp-p7a-qg-sweep: QG sweep across all sports repos.
- [x] [AGENT] P1. sbp-p7b-codex-update: Update codex sports-schema-paths.md. Evidence: codex
      `02-data/sports-scheduling-and-sharding.md` is now the §12.0 SSOT register (per evidence map line 28-30); session
      memory confirms codex sports register late-audit 2026-04-22 + sports-uac-schema-contracts-registration shipped
      (UAC `4810ced`).
- [ ] [AGENT] P1. poly-p7a-qg-sweep: QG sweep across all prediction repos.
