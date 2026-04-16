---
name: consolidated-sports-prediction-pipeline
overview: |
  Consolidated remaining work from 8 sports + prediction plans into a single tracking plan.
  Covers: sports batch E2E, Polymarket prediction wiring, sports integrations 01-06, sports ML training.
  Source plans retained for history; remaining todos tracked here.
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
  - repo: instruments-service
    code: C0
  - repo: market-tick-data-service
    code: C0
  - repo: features-sports-service
    code: C0
  - repo: unified-features-interface
    code: C0
  - repo: unified-trading-library
    code: C0
  - repo: ml-training-service
    code: C0
  - repo: execution-service
    code: C0
  - repo: strategy-service
    code: C0
  - repo: deployment-service
    code: C0

depends_on: []

source_plans:
  - sports_batch_pipeline_end_to_end_2026_03_25
  - polymarket_prediction_pipeline_2026_03_25
  - sports_integration_01_reference_data_pipeline_2026_03_25
  - sports_integration_02_odds_market_data_pipeline_2026_03_25
  - sports_integration_03_features_provider_integration_2026_03_25
  - sports_integration_04_feature_calculators_full_2026_03_25
  - sports_integration_05_ml_training_pipeline_2026_03_25
  - sports_integration_06_strategy_execution_gcs_migration_2026_03_25

todos:
  # ══════════════════════════════════════════════════════════════
  # GROUP A — UAC Schemas & Reference Data (from sports_batch + polymarket)
  # ══════════════════════════════════════════════════════════════
  - id: sbp-p1a-sm-keys-audit
    content: "Audit Secret Manager for sports API keys"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p1c-canonical-id-docstrings
    content: "Codify canonical ID format in UAC docstrings"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p2c-season-definition-type
    content: "Add SeasonDefinition type to UAC if missing"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: poly-p1b-series-mappings
    content: "Expand Polymarket series-to-league mappings in UAC sports_mappings.py"
    status: todo
    source: polymarket_prediction_pipeline
  - id: poly-p1d-canonical-id-format
    content: "Define canonical instrument ID format for PREDICTION category"
    status: todo
    source: polymarket_prediction_pipeline

  # ══════════════════════════════════════════════════════════════
  # GROUP B — Instruments Service & Reference Data Pipeline
  # ══════════════════════════════════════════════════════════════
  - id: sbp-p2a-verify-instruments-sports
    content: "Verify instruments-service SPORTS hook works end-to-end"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p2b-urdi-capability-registry
    content: "Fix instruments-service reference_data capability registry for sports"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p3b-usri-quota-tracking
    content: "Add quota tracking to instruments-service OddsApi adapter"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: si01-p5-validation
    content: "Run instruments-service for 2026-03-22 (Saturday with EPL fixtures)"
    status: todo
    source: sports_integration_01
  - id: si01-p5b-manifest-tracking
    content: "Verify instruments-service ManifestWriter tracks SPORTS reference data"
    status: todo
    source: sports_integration_01
  - id: si01-p6a-one-month-ref
    content: "Validate reference data for 1 month (2025-03-01 to 2025-03-31)"
    status: todo
    source: sports_integration_01
  - id: si01-p6b-full-period-ref
    content: "Validate reference data for full period (2020-06-01 to 2026-03-28)"
    status: todo
    source: sports_integration_01

  # ══════════════════════════════════════════════════════════════
  # GROUP C — MTDS Odds & Tick Data Pipeline
  # ══════════════════════════════════════════════════════════════
  - id: sbp-p3c-mtds-sports-integration
    content: "Test MTDS SPORTS pipeline end-to-end"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: si02-p3-validation
    content: "Run 1-week odds validation (Phase 2 of e2e validation)"
    status: todo
    source: sports_integration_02
  - id: si02-p7a-halftime-empirical
    content: "Empirically test Odds API at offset -60 (HT) for recent match"
    status: todo
    source: sports_integration_02
  - id: si02-p7b-halftime-analysis
    content: "Analyse HT odds quality if P7a shows real in-play bm_time"
    status: todo
    source: sports_integration_02
  - id: si02-p8b-l1-odds-backfill
    content: "L1 odds backfill (2020-06-01 to 2026-03-28)"
    status: in_progress
    source: sports_integration_02
  - id: si02-p9a-footystats-backfill
    content: "Backfill FootyStats match-level data to GCS"
    status: todo
    source: sports_integration_02
  - id: si02-p10c-completeness-checker
    content: "Build completeness checker script for odds pipeline"
    status: todo
    source: sports_integration_02
  - id: si02-p11a-one-month
    content: "Run odds pipeline for 1 month (2025-03-01 to 2025-03-31)"
    status: todo
    source: sports_integration_02
  - id: si02-p11b-full-period
    content: "Roll out odds pipeline to full period (2020-06-01 to 2026-03-28)"
    status: todo
    source: sports_integration_02

  # ══════════════════════════════════════════════════════════════
  # GROUP D — Features-Sports-Service Pipeline
  # ══════════════════════════════════════════════════════════════
  - id: si03-p3-wire-exporters
    content: "Replace stub exporters with GCS-backed + enrichment data"
    status: todo
    source: sports_integration_03
  - id: si03-p4-validation
    content: "Run FSS for 2026-03-22 with all providers"
    status: todo
    source: sports_integration_03
  - id: si03-p4b-footystats-backfill
    content: "Backfill FootyStats match-level data to GCS (FSS)"
    status: todo
    source: sports_integration_03
  - id: si03-p5a-fss-manifest
    content: "Verify FSS ManifestWriter tracks feature computation per date"
    status: todo
    source: sports_integration_03
  - id: si03-p5b-one-month
    content: "Run features pipeline for 1 month (2025-03-01 to 2025-03-31)"
    status: todo
    source: sports_integration_03
  - id: si03-p5c-full-period
    content: "Roll out features to full period (2020-06-01 to 2026-03-28)"
    status: todo
    source: sports_integration_03
  - id: si04-p3-vectorize
    content: "Audit FSS calculators for .iterrows() usage and vectorize"
    status: todo
    source: sports_integration_04
  - id: si04-p4-validation
    content: "Run feature count audit (target >=1000 features)"
    status: todo
    source: sports_integration_04
  - id: sbp-p5a-fss-batch-test
    content: "Test features-sports-service batch end-to-end"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p5b-fss-hive-paths
    content: "Verify FSS output uses hive-partitioned paths"
    status: todo
    source: sports_batch_pipeline_end_to_end

  # ══════════════════════════════════════════════════════════════
  # GROUP E — Sports ML Training Pipeline
  # ══════════════════════════════════════════════════════════════
  - id: si05-p1-verify-metrics
    content: "Check UTL ml/ for Poisson NLL, RPS, Brier score"
    status: todo
    source: sports_integration_05
  - id: si05-p2-training-config
    content: "Add sports training config to ml-training-service"
    status: todo
    source: sports_integration_05
  - id: si05-p3-model-2a
    content: "Port Model 2A ensemble from archived model_2a.py (401L)"
    status: todo
    source: sports_integration_05
  - id: si05-p4-walk-forward
    content: "Port walk_forward.py workflow from archive (249L)"
    status: todo
    source: sports_integration_05
  - id: si05-p5-validation
    content: "Train model on historical features (2020-2025)"
    status: todo
    source: sports_integration_05

  # ══════════════════════════════════════════════════════════════
  # GROUP F — Strategy, Execution & GCS Migration
  # ══════════════════════════════════════════════════════════════
  - id: si06-p3-execution-routing
    content: "Verify execution-service routes sports signals through sports_execution"
    status: todo
    source: sports_integration_06
  - id: si06-p4-paper-trading
    content: "Run paper trade for March 22 fixtures"
    status: todo
    source: sports_integration_06
  - id: sbp-p4a-gcs-bucket-audit
    content: "[HUMAN] Audit existing GCS sports data buckets"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p4b-migration-script
    content: "Write GCS migration script for sports data"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p4c-execute-migration
    content: "[HUMAN] Execute sports GCS migration"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: si06-p5a-audit-buckets
    content: "[HUMAN] Audit old sports execution GCS buckets"
    status: todo
    source: sports_integration_06
  - id: si06-p5b-migration-script
    content: "Write sports execution GCS migration script"
    status: todo
    source: sports_integration_06
  - id: si06-p5c-execute-migration
    content: "[HUMAN] Execute sports execution GCS migration"
    status: todo
    source: sports_integration_06

  # ══════════════════════════════════════════════════════════════
  # GROUP G — Polymarket Prediction Remaining
  # ══════════════════════════════════════════════════════════════
  - id: poly-p5a-gcs-buckets
    content: "[HUMAN] Create GCS buckets for prediction category data"
    status: todo
    source: polymarket_prediction_pipeline

  # ══════════════════════════════════════════════════════════════
  # GROUP H — End-to-End Validation & QG
  # ══════════════════════════════════════════════════════════════
  - id: sbp-p6a-one-day
    content: "Run full 1-day sports pipeline validation"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p6b-one-week
    content: "Run 1-week sports pipeline validation"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: poly-p6a-crypto-validation
    content: "Validate crypto up/down prediction pipeline end-to-end"
    status: todo
    source: polymarket_prediction_pipeline
  - id: poly-p6b-soccer-validation
    content: "Validate soccer fixture prediction pipeline end-to-end"
    status: todo
    source: polymarket_prediction_pipeline
  - id: sbp-p7a-qg-sweep
    content: "QG sweep across all sports repos"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: sbp-p7b-codex-update
    content: "Update codex sports-schema-paths.md"
    status: todo
    source: sports_batch_pipeline_end_to_end
  - id: poly-p7a-qg-sweep
    content: "QG sweep across all prediction repos"
    status: todo
    source: polymarket_prediction_pipeline

isProject: false
---

# Consolidated Sports & Prediction Pipeline

Remaining work from 8 source plans. Each todo references its source plan for full context.
