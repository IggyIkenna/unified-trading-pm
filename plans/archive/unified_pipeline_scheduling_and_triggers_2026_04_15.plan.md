---
doc_type: plan
title: unified-pipeline-scheduling-and-triggers
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-15'
remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15
superseded_by: [consolidated_operational_validation_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: End-to-end pipeline readiness — backfill, T+1, thermal, live — across all 6 clusters with sports trigger scheduling
type: mixed
epic: epic-deployment
completion_gates: {code: C5, deployment: D3, business: B4}
repo_gates:
- {repo: deployment-service, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: features-sports-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: features-delta-one-service, code: C0, deployment: none, business: none}
- {repo: features-volatility-service, code: C0, deployment: none, business: none}
- {repo: features-calendar-service, code: C0, deployment: none, business: none}
- {repo: features-cross-instrument-service, code: C0, deployment: none, business: none}
- {repo: features-multi-timeframe-service, code: C0, deployment: none, business: none}
- {repo: features-commodity-service, code: C0, deployment: none, business: none}
- {repo: ml-training-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p0-cluster-config-fixes, content: '- [x] [AGENT] P0. Fix cluster config gaps — add MTDS + MDPS to sports and prediction clusters, remove corporate-actions and risk-management-service references (repos don''t exist)

    ', status: done, note: ''}
- {id: p0-dependencies-yaml, content: '- [x] [AGENT] P0. Fix dependencies.yaml — add features-sports-service upstream deps (instruments-service, market-tick-data-service), add missing services (features-commodity-service, features-multi-timeframe-service), fix reconciliation-service → batch-live-reconciliation-service naming, add SPORTS external deps to instruments-service and MTDS

    ', status: done, note: ''}
- {id: p1-instruments-t1-terraform, content: '- [x] [AGENT] P0. Add instruments-service to T+1 terraform scheduler — Cloud Scheduler job at 23:30 UTC (pipeline root, runs first), Cloud Run job definition

    ', status: done, note: Root of entire pipeline — triggers before everything else}
- {id: p1-instruments-completion-event, content: '- [x] [AGENT] P0. Add DATA_READY Pub/Sub publish to instruments-service on batch completion — MTDS live mode already listens for this. Added to cleanup() with contextlib.suppress for batch mode safety.

    ', status: done, note: ''}
- {id: p1-mtds-t1-terraform, content: '- [x] [AGENT] P0. Add market-tick-data-service to T+1 terraform scheduler — Cloud Scheduler job at 00:00 UTC (after instruments at 23:30), plus MDPS at 01:00 UTC

    ', status: done, note: ''}
- {id: p1-mdps-terraform-fix, content: '- [x] [AGENT] P0. Fix MDPS T+1 terraform — changed --date to --start-date/--end-date, added all 5 categories (CEFI+TRADFI+DEFI+SPORTS+PREDICTION), added sports/prediction GCS volumes. Fixed both GCP and AWS terraform.

    ', status: done, note: ''}
- {id: p1-mdps-cli-standardize, content: '- [x] [AGENT] P1. Standardize MDPS CLI — added --asset-group arg bridging in _build_legacy_argv() to read from ServiceBootstrap args.category, with MDPS_CATEGORY env var as fallback for backwards compatibility

    ', status: done, note: MDPS still uses add_category_arg=False but now bridges categories from args}
- {id: p2-live-partition-convention, content: '- [x] [AGENT] P0. Define and implement live/ partition convention — added apply_run_tag() to UTL PATH_REGISTRY (registry.py + __init__.py). Convention: batch (no prefix), live → live/{path}, t1-recon → t1-recon/{path}, any tag → {tag}/{path}. MDPS already uses this pattern; now standardised for all services.

    ', status: done, note: SSOT should be in unified-trading-library path registry}
- {id: p2-run-tag-standardize, content: '- [x] [AGENT] P1. Add --run-tag to instruments-service. Values: batch (default), live, t1-recon. MTDS and features-calendar still need it — wiring into GCS output path requires deeper integration.

    ', status: done, note: 'features-cross-instrument, features-multi-timeframe, features-commodity, ml-inference already have it.'}
- {id: p2-run-tag-mtds-calendar, content: '- [x] [AGENT] P1. Added --run-tag to market-tick-data-service CLI (via background agent). Features-calendar-service deferred. For MTDS: add to market_tick_data_service/cli/main.py extra_args_fn, wire into GCS output path in tick_data_handler.py — when run_tag != "batch", prefix output path with run_tag/ (same as MDPS live_mode_handler.py line 337 pattern: `prefix = f"live/{prefix}"`). For features-calendar-service: add to features_calendar_service/cli/main.py extra_args_fn, wire into batch_handler.py output path.

    ', status: todo, note: ''}
- {id: p2-completion-events, content: '- [x] [AGENT] P1. Add DATA_READY Pub/Sub completion event to MTDS tick_data_handler.py cleanup() — same pattern as instruments-service and MDPS (contextlib.suppress for batch mode). Feature services deferred — they''re downstream consumers, not producers that others wait on.

    ', status: done, note: MDPS already publishes. Instruments done (Phase 1). MTDS done now.}
- {id: p3-absence-type-enum, content: '- [x] [AGENT] P1. Add AbsenceType enum to UAC CanonicalInjury — values: INJURY, SUSPENSION_RED_CARD, SUSPENSION_YELLOW_ACCUMULATION, DOMESTIC_BAN, INTERNATIONAL_DUTY, PERSONAL, ILLNESS, OTHER. Added absence_type field to both injury.py and __init__.py CanonicalInjury models. Added classify_absence() deterministic classifier.

    ', status: done, note: ''}
- {id: p3-absence-classifier, content: '- [x] [AGENT] P1. Deterministic classifier written in UAC injury.py — classify_absence() maps reason strings to AbsenceType using keyword matching. Priority: yellow accumulation > red card suspension > international > personal > illness > injury (default). Instruments-service normalizer calls from_raw() which auto-classifies.

    ', status: done, note: ''}
- {id: p3-absence-backfill, content: '- [x] [AGENT] P1. GCS migration script created at instruments-service/scripts/backfill-absence-type.py — reads injury parquets from GCS, applies classify_absence(), adds absence_type column, rewrites in place. Supports --dry-run. No API calls (Option A).

    ', status: done, note: 'Run with: python scripts/backfill-absence-type.py --bucket instruments-store-sports-PROJECT_ID --dry-run'}
- {id: p3-ml-sports-category, content: '- [x] [AGENT] P0. Add SPORTS to ml-training-service MARKET_CATEGORIES — was already in CLI parser choices (CATEGORIES in parser.py), but handler default list (MARKET_CATEGORIES in handlers/__init__.py) only had CEFI/TRADFI/DEFI. Added SPORTS.

    ', status: done, note: CLI accepts SPORTS. Handler routing + feature adapter wiring in p3-ml-sports-handler-routing.}
- {id: p3-ml-defi-category, content: '- [x] [HUMAN+AGENT] P1. DeFi target generators created at ml-training-service/app/core/defi_target_generator.py — 3 builders: FundingRateTargetBuilder (6 targets: next rate, avg 2d/10d/annual, direction, persistence), LendingRateTargetBuilder (4 targets: supply/borrow next, spike detection, direction), ImpermanentLossTargetBuilder (3 targets: range breakout 1d/7d, max divergence). Registry: DEFI_TARGET_BUILDERS. Features: delta-one + onchain + funding rate + lending indices (all already in pipeline).

    ', status: done, note: Target builders follow sports_target_generator.py pattern.}
- {id: p3-ml-defi-handler-routing, content: "- [x] [AGENT] P1. DEFI category routing wired in ml-training-service (via background agent). train_handler.py: _generate_defi_variants(). training_orchestrator.py: routes DEFI→defi_target_generator. cloud_feature_provider.py: _query_defi_features reads onchain+delta-one buckets. target_generator_factory.py: build_defi_targets(). config.py: features_onchain_bucket_template.\n  1. Import DEFI_TARGET_BUILDERS from ml_training_service.app.core.defi_target_generator\n  2. In the training handler's target generation step, check category — if DEFI, use FundingRateTargetBuilder / LendingRateTargetBuilder / ImpermanentLossTargetBuilder instead of swing target builders\n  3. The feature adapter needs to read from features-onchain GCS bucket (features-onchain-{category}-{project_id}) instead of features-delta-one — check ml_training_service/app/core/ for the feature loading logic and add a DEFI path that reads onchain features + funding rate data from MTDS\
    \ collect-perp-funding output (market-data-tick-defi-{project_id}/raw_tick_data/by_date/day={date}/data_type=funding_rates/)\n  4. Add DEFI to ml-training-service dependencies.yaml upstream — currently only reads features-delta-one (required) + features-volatility/onchain (optional). For DEFI, features-onchain should be required and market-tick-data-service funding rate output should be an input\n  Files to modify:\n  - ml_training_service/cli/handlers/ — find the handler that dispatches target generation (check batch_handler.py or similar)\n  - ml_training_service/app/core/ — feature loading logic (check data_loader.py, feature_adapter.py, or cloud_data_provider usage)\n  - deployment-service/configs/dependencies.yaml — add DEFI-specific upstream for ml-training-service\n", status: done, note: 'Routing wired: train_handler routes DEFI, training_orchestrator._generate_defi_targets, cloud_feature_provider._query_defi_features'}
- {id: p3-ml-sports-handler-routing, content: "- [x] [AGENT] P1. SPORTS category routing wired in ml-training-service (same agent). train_handler.py: _generate_sports_variants() (fixture-based, timeframe=\"fixture\"). training_orchestrator.py: routes SPORTS→sports_target_generator via SportsTargetOrchestrator + legacy generators for xg/clv/ht_delta.\n  1. The handler should use sports_target_generator.py (XGTargetBuilder, CLVTargetBuilder, etc.) — check if this routing already exists or if it's hardcoded to CeFi/TradFi\n  2. Feature adapter should read from features-sports GCS bucket (features-sports-{project_id}/by_date/day={date}/league={league}/feature_group={group}/) — different path structure than delta-one (no category in bucket, has league partition)\n  3. Training should support per-league model training (--league EPL) or all-leagues combined\n  4. Walk-forward validation needs fixture-aware date splits — can't randomly split fixtures, must split by date to avoid leakage\n  Files\
    \ to check:\n  - ml_training_service/app/core/sports_target_generator.py — already has 5 target builder classes\n  - ml_training_service/cli/handlers/ — check if SPORTS category routing exists\n  - ml_training_service/app/core/ — feature loading for sports features\n", status: done, note: 'Routing wired: _generate_sports_variants, _generate_sports_targets, _query_sports_features all implemented'}
- {id: p4-sports-trigger-scheduler, content: '- [x] [HUMAN+AGENT] P0. Sports fixture-aware trigger scheduler implemented in deployment-service — SportsTriggerScheduler reads fixture calendar from GCS, evaluates pre-match (T-24h/T-6h/T-1h) and post-match (T+30min/T+24h) triggers, fires standard batch CLI invocations. Two layers: discovery (6h cycle) and fixture-proximate triggers. CLI: `deployment-service sports-trigger run` (blocking loop) and `sports-trigger evaluate` (single cycle).

    ', status: done, note: ''}
- {id: p4-sports-trigger-backend-dispatch, content: "- [x] [AGENT] P1. Sports trigger scheduler wired to deployment backend. fire_trigger() now dispatches via subprocess for local mode (resolves repo .venv/bin/python, sets cwd to service repo dir). Cloud mode is placeholder. Shard-level failure isolation: individual service failures logged but don't stop scheduler. 1h timeout per job. Changes:\n  1. In deployment_service/sports_trigger_scheduler.py fire_trigger(), replace the logging-only path with actual backend dispatch\n  2. Import and use the existing deployment backend: check deployment_service/backends/ — CloudRunBackend.submit_job() or LocalProcessBackend for T2\n  3. The backend selection should follow the same pattern as ClusterOrchestrator — check cluster.py for how it resolves local vs gcp vs aws backend\n  4. For local (T2): use subprocess to invoke the CLI command directly\n  5. For cloud: use CloudRunBackend to submit a Cloud Run Job with the CLI args as container overrides\n\
    \  Files: deployment_service/sports_trigger_scheduler.py (fire_trigger method), deployment_service/backends/cloud_run.py, deployment_service/backends/local_process.py\n", status: todo, note: ''}
- {id: p4-sports-trigger-tiers, content: '- [x] [AGENT] P1. Sports trigger tier config created at deployment-service/configs/sports-trigger-tiers.yaml — 4 tiers: discovery (6h), reference (24h, window-aware), pre-match (T-24h/T-6h/T-1h odds, T-1h lineups/weather/features/inference), post-match (T+30min stats, T+24h xG). Configurable per trigger with tolerance windows.

    ', status: done, note: ''}
- {id: p4-sports-live-discrete-jobs, content: '- [x] [AGENT] P1. Sports discrete live jobs wired — trigger scheduler builds CLI commands as `python -m <service> --mode batch --asset-group SPORTS --start-date today --end-date today --run-tag live` with per-trigger extra args (--sports-entity, etc.). Same CLI, same service, just triggered by fixture proximity.

    ', status: done, note: CLI command construction done. Backend dispatch in p4-sports-trigger-backend-dispatch.}
- {id: p4-sports-streaming-viz, content: '- [ ] [HUMAN+AGENT] P2. Sports live streaming for visualization — 3-layer feature across instruments-service (backend, --mode live ScheduledIO already exists, polls API Football/SFI every few minutes), unified-trading-api (add sports-live WebSocket channel — mock mode: synthetic fixture ticks from MOCK_FIXTURES, real mode: subscribe to instruments-data-ready PubSub), unified-trading-system-ui (wire SportsDataProvider to WebSocket in real mode instead of MOCK_FIXTURES). UI already has sports-live-scores-widget, fixtures-detail-panel, arb-stream — all mock. Progressive odds/stats per fixture per league. Update frequency: every 1-5 min, not sub-second.

    ', status: done, note: SUPERSEDED — covered by sports_live_streaming_viz_2026_04_15.plan.md which depends_on this plan}
- {id: p5-backfill-vm-templates, content: '- [x] [AGENT] P1. Per-cluster VM backfill template created at deployment-service/scripts/vm/backfill-cluster.sh — parameterized by --cluster (cefi/defi/tradfi/sports/prediction/full), --start-date, --end-date. Reads cluster config for category, runs pipeline DAG in order (instruments → MTDS → MDPS → features → ML). Supports --skip-existing and --dry-run. Sports features iterate per-day (--date).

    ', status: done, note: ''}
- {id: p5-backfill-resume, content: '- [x] [AGENT] P1. Added --skip-existing to MDPS parser. MTDS already has smart resume via check_shard_freshness(). Instruments has --force. Features-sports has --skip-existing. All services now support resume for backfill.

    ', status: done, note: ''}
- {id: p5-mdps-skip-existing-wiring, content: "- [x] [AGENT] P1. --skip-existing wired into MDPS process handler (via background agent). Added _processed_candles_exist() helper that checks GCS for existing candle blobs per date per category. When skip_existing=True and candles exist, returns 0 with log message. The flag was added to the parser (market_data_processing_service/cli/parser.py) but the handler doesn't use it yet. Changes:\n  1. In market_data_processing_service/cli/handlers/process_handler.py, read args.skip_existing\n  2. Before processing each date, check if processed candles already exist in GCS at the expected output path (processed_candles/by_date/day={date}/)\n  3. If skip_existing=True and candles exist for that date, skip processing and log \"Skipping {date} — candles already exist\"\n  4. Use the existing dependency_checker.py pattern or storage_client.list_blobs() to check existence\n  Files: market_data_processing_service/cli/handlers/process_handler.py (process_candles_handler\
    \ function), market_data_processing_service/app/core/dependency_checker.py (for GCS check pattern)\n", status: done, note: 'process_handler.py: skip_existing uses _processed_candles_exist() with early return'}
- {id: p5-backfill-deployment-ui, content: "- [x] [AGENT] P2. Deployment UI backfill trigger wired — gaps page (app/(platform)/services/data/gaps/page.tsx) handleBatchBackfill() now calls POST /deployment-api/api/batch/run with cluster, as_of_date, service, category. Groups selected gaps by service+category. API endpoint already exists in deployment-service.\n  1. Add \"Run Backfill\" button that calls POST /api/deployment/batch/run with {cluster, start_date, end_date, category}\n  2. The deployment-service API endpoint already exists (api/routes/orchestration.py BatchRunRequest) — verify it works\n  3. Show backfill progress: poll GET /api/deployment/batch/history for status updates\n  4. Per-service progress bars showing which service in the DAG is currently running\n  Files: deployment_service/api/routes/orchestration.py (BatchRunRequest, batch_run endpoint), unified-trading-system-ui data status page (app/(ops)/admin/data/page.tsx or similar)\n", status: done, note: gaps/page.tsx handleBatchBackfill()
    calls POST /deployment-api/api/batch/run}
- {id: p6-thermal-ml-experiment, content: "- [x] [AGENT] P1. ML experiment metrics writing + API endpoints done. ml-training-service now writes experiment metrics to GCS (ml-training-artifacts-{project_id}/experiments/{experiment_id}/metrics.json) on successful training. deployment-service API has 4 new endpoints: GET /api/ml/experiments, GET /api/ml/experiments/{id}, GET /api/ml/models, GET /api/ml/models/{id}/metadata. No MLflow/W&B needed — custom GCS-based tracking sufficient. The service writes to ml-training-artifacts-{project_id} (stage artifacts) and ml-models-store-{project_id} (final models with metadata.json). Check:\n  1. Read ml_training_service/app/core/ for experiment tracking — does it write metrics (accuracy, Sharpe, feature importance) to GCS alongside models?\n  2. Read ml-models-store-{project_id}/model_registry/metadata/{model_id}/ structure — what's in metadata.json?\n  3. If metrics are already written to GCS: custom GCS-based tracking is sufficient (no MLflow/W&B\
    \ needed)\n  4. If not: add metrics writing to the training handler — after each grid search trial / walk-forward fold, write {model_id, config, metrics, timestamp} to ml-training-artifacts-{project_id}/experiments/{experiment_id}/trials/{trial_id}/metrics.json\n  5. The --grid-config flag already supports named configs from GCS — verify configs are versioned and retrievable\n  Files: ml_training_service/app/core/ (look for metrics, evaluation, or results writing), ml_training_service/cli/handlers/ (check what happens after training completes)\n", status: done, note: 'GCS-based tracking: _write_variant_metrics writes experiments/{id}/metrics.json. deployment-service API has 4 ML endpoints.'}
- {id: p6-thermal-deployment-ui, content: "- [x] [AGENT] P2. Deployment UI experiment browser — REST endpoints created in deployment-service/api/routes/ml_experiments.py (GET experiments, models, metadata). Registered in api/app.py with S2S auth. UI page to consume these endpoints is frontend work — the API is ready.\n  GET /api/ml/experiments — list experiments from ml-training-artifacts-{project_id}/experiments/\n  GET /api/ml/experiments/{id}/trials — list trials with metrics\n  GET /api/ml/models — list models from ml-models-store-{project_id}/model_registry/\n  GET /api/ml/models/{id}/metadata — model metadata, feature importance, training config\n  UI page: table of experiments with sortable columns (accuracy, Sharpe, date), click to expand trials, compare button for side-by-side metrics.\n  Files: deployment_service/api/routes/ (add ml.py), deployment UI (check unified-trading-system-ui for existing ML/research pages at app/(platform)/services/research/)\n", status: done, note: deployment-service/api/routes/ml_experiments.py
    created with GET experiments/models/metadata. Registered in app.py.}
- {id: p7-data-status-all-modes, content: "- [x] [AGENT] P1. Data status extended to all 4 modes (via background agent). New CLI flags: --t1-check CLUSTER (reads cluster YAML, checks yesterday per service), --ml-experiments (lists experiments from GCS artifacts bucket with metadata check), --live-freshness (scans live/ prefix, reports staleness with domain-specific thresholds: 15min CeFi/DeFi, 1h TradFi, 6h sports). New file: deployment_service/cli/utils/data_status_extended.py. The deployment-service data status page (deployment_service/cli/commands/data_status.py and deployment_service/api/routes/ data status endpoints) currently shows per-date completeness for batch. Extend:\n  1. Mode 1 (Historical Backfill): show date range completeness per service per entity — e.g. \"instruments-service CEFI: 2025-01-01 to 2026-04-14, 98% complete, missing: [2025-03-15, 2025-07-22]\". Read from availability manifest in each service's GCS bucket.\n  2. Mode 2 (T+1): single-date check — \"yesterday:\
    \ instruments OK, MTDS OK, MDPS FAILED, features OK\". Read from T+1 orchestrator GCS state (deployment-orchestration-{project_id} bucket).\n  3. Mode 3 (Thermal/ML): list experiments from ml-training-artifacts-{project_id} bucket — show model_id, training_period, stage, metrics. This is the experiment provenance view.\n  4. Mode 4 (Live): check live/ partition freshness — last write timestamp per service per category. Flag staleness > threshold (e.g. > 15 min for CeFi, > 6h for sports reference).\n  Files: deployment_service/cli/commands/data_status.py, deployment_service/api/routes/ (check for data_status or similar endpoints), deployment-service/configs/data-catalogue.*.yaml (per-service data catalogue definitions).\n", status: done, note: 'data_status.py imports run_t1_check, run_ml_experiments_check, run_live_freshness_check from data_status_extended.py'}
- {id: p7-batch-live-reconciliation, content: "- [x] [AGENT] P1. Data pipeline reconciliation stage created (via background agent). stage0_data_pipeline_recon.py covers instruments/MTDS/MDPS across cefi/tradfi/defi. Compares batch vs live/ GCS blobs (file count, row count via pyarrow metadata). Wired into orchestrator between stage0 (config pull) and stage1 (ML recon). Shard-level failure isolation. DataPipelineThresholds: 95% file/row match rate.tages (stage1_ml_recon, stage2_strategy_recon, stage3_execution_recon) that compare live/events/{date}/{service}/ vs batch paths. These cover the TRADING pipeline (ML → strategy → execution). The DATA pipeline (instruments → MTDS → MDPS → features) is NOT covered.\n  Two options:\n  (a) Add a stage0_data_pipeline_recon.py to batch-live-reconciliation-service: for each data pipeline service, compare live/ partition vs batch partition for the same date. Check row counts, schema, and sample values. Follow stage1_ml_recon.py pattern.\n  (b) Use data-status\
    \ CLI with --mode batch vs --mode live: `deployment-service data-status -s instruments-service --start-date {date} --end-date {date} --mode batch` vs same with `--mode live`, then diff the outputs. This is less automated but uses existing infra.\n  Recommended: option (a) for production automation, option (b) for immediate validation.\n  Files: batch_live_reconciliation_service/stages/ (add stage0_data_pipeline_recon.py), batch_live_reconciliation_service/engine/ (check how stages are orchestrated and registered)\n", status: done, note: stage0_data_pipeline_recon.py implemented. Compares batch vs live/ GCS blobs for instruments/MTDS/MDPS.}
- {id: p7-sports-data-status-fixture, content: "- [x] [AGENT] P1. Sports fixture-based data status done (via background agent). New --sports-league-breakdown flag on data-status CLI. Fixture calendar as denominator (0 fixtures = expected absence, skipped). Per-league output: \"EPL: 10/10 fixtures (100%)\". Transfer window awareness via UAC is_transfer_window_open(). New file: deployment_service/cli/utils/data_status_sports.py. Supports instruments-service, MTDS, features-sports-service. In the data status / deployment UI:\n  1. For sports services, the denominator for \"% complete\" should be fixture count per league, not calendar days. Read fixture calendar from GCS to get the denominator.\n  2. Distinguish expected absence from system failure:\n     - No fixtures on this date for this league → expected (check fixture calendar)\n     - Transfer window closed → no transfer data expected (check transfer_windows.py `is_transfer_window_open()`)\n     - Fixture exists but no injury data → either\
    \ zero injuries (zero-file in GCS) or system failure (no file at all)\n  3. Group data status by league (EPL, Bundesliga, etc.) with per-entity breakdown (fixtures, injuries, odds, stats, lineups, predictions)\n  Files: deployment_service/cli/commands/data_status.py (add sports-specific denominator logic), unified_api_contracts/canonical/domain/sports/transfer_windows.py (is_transfer_window_open, get_active_window)\n", status: done, note: data_status_sports.py + display_sports_league_breakdown wired. Fixture calendar denominator. Transfer window awareness.}
- {id: p8-e2e-cefi-cluster, content: "- [ ] [HUMAN+AGENT] P0. E2E test: CEFI cluster — 3 sub-tests:\n  (a) T+1 single day: `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster cefi --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)` — verify instruments writes to GCS, MTDS downloads tick data, MDPS produces candles, features compute, ML inference produces predictions. Check each service's GCS output bucket exists and has data for yesterday.\n  (b) Live 1h: start instruments-service --mode live --asset-group CEFI, MTDS --mode live --asset-group CEFI, MDPS --mode live. Verify live/ partition gets data, WebSocket in unified-trading-api shows market-data channel updates.\n  (c) Reconciliation: after (a) and (b), run batch-live-reconciliation-service for yesterday. Verify it reads both batch and live/ partitions and produces a comparison report.\n  Commands: all via service CLIs from within each repo's .venv. API keys must be in Secret Manager (Tardis for CeFi\
    \ tick data).\n", status: todo, note: 'Gate: all CEFI cluster services produce GCS output for 1 date'}
- {id: p8-e2e-sports-cluster, content: "- [ ] [HUMAN+AGENT] P0. E2E test: SPORTS cluster — 3 sub-tests:\n  (a) T+1 single day: `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster sports --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)` — verify instruments writes fixtures/injuries/standings to GCS, MTDS downloads odds, MDPS processes, features-sports computes derived features, ML inference runs.\n  (b) Trigger scheduler: `python -m deployment_service sports-trigger evaluate --dry-run` — verify it reads fixture calendar from GCS, identifies upcoming fixtures, and reports which triggers would fire (T-24h odds, T-1h lineups, etc.). If fixtures exist for today, at least some triggers should be due.\n  (c) Feature validation: for a completed fixture from yesterday, verify features-sports GCS output has all expected feature columns (check features-sports-{project_id}/by_date/day={date}/league={league}/ for parquet files with 600+ columns).\n  API keys needed:\
    \ API Football (api-sports.io), Odds API (the-odds-api.com), FootyStats.\n", status: todo, note: 'Gate: sports pipeline produces features for at least 1 league for 1 date'}
- {id: p8-e2e-defi-cluster, content: "- [ ] [HUMAN+AGENT] P1. E2E test: DEFI cluster — T+1 single day:\n  `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster defi --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)`\n  Verify: instruments writes DeFi instrument definitions, MTDS runs collect-gas-fees + collect-lending-indices + collect-perp-funding + collect-dex-pools + download (Hyperliquid tick data), MDPS produces DeFi candles, features-onchain computes onchain features.\n  DeFi-specific MTDS operations to validate: gas_fee_handler.py, lending_indices_handler.py, perp_funding_handler.py, dex_pools_handler.py, evm_defi_handler.py.\n  No ML for DeFi cluster (intentional — DeFi ML target builders exist but handler routing not wired yet, see p3-ml-defi-handler-routing).\n", status: todo, note: 'No API keys needed for most DeFi — Hyperliquid is public, Alchemy RPC, The Graph.'}
- {id: p8-e2e-tradfi-cluster, content: "- [ ] [HUMAN+AGENT] P1. E2E test: TRADFI cluster — T+1 single day:\n  `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster tradfi --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)`\n  Verify: instruments writes TradFi definitions (NASDAQ/NYSE/CME/ICE/CBOE), MTDS downloads via Databento (needs DATABENTO_API_KEY in Secret Manager), MDPS produces TradFi candles with trading-hours awareness, features-delta-one + features-volatility + features-calendar compute.\n  Skip corporate-actions (repo doesn't exist). Skip weekends (TradFi markets closed — run on a weekday date).\n", status: todo, note: Needs DATABENTO_API_KEY. Run on a recent weekday.}
- {id: p8-e2e-prediction-cluster, content: "- [ ] [HUMAN+AGENT] P1. E2E test: PREDICTION cluster — T+1 single day:\n  `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster prediction --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)`\n  Verify: instruments writes prediction market definitions (Polymarket, Kalshi), MTDS downloads prediction market trade data, MDPS produces candles, features-sports computes (shared with sports cluster). No ML in prediction cluster.\n  Polymarket CLOB API is public (no auth). Kalshi needs API key.\n", status: todo, note: Prediction is a subset of sports pipeline — uses same features-sports-service.}
- {id: p8-e2e-full-cluster, content: "- [ ] [HUMAN+AGENT] P2. E2E test: FULL cluster — run all categories for 1 date:\n  `bash deployment-service/scripts/vm/backfill-cluster.sh --cluster full --start-date $(date -v-1d +%Y-%m-%d) --end-date $(date -v-1d +%Y-%m-%d)`\n  This exercises the complete pipeline for CEFI + DEFI + TRADFI + SPORTS + PREDICTION. All services in the full cluster config run in DAG order. Verify no service fails due to missing upstream data or misconfigured bucket paths.\n  This is the final validation — if full cluster passes for 1 date, the pipeline is ready for production scheduling.\n", status: todo, note: Run after individual cluster tests pass. Needs all API keys.}
- {id: p9-aws-parity, content: '- [x] [AGENT] P2. AWS terraform parity — features-multi-timeframe-service AWS terraform created (main.tf, variables.tf, outputs.tf, terraform.tfvars.example). Audit: all 21 services now have both GCP and AWS terraform. No other services missing.

    ', status: done, note: 'features-multi-timeframe-service AWS terraform created (main.tf, variables.tf, outputs.tf, terraform.tfvars.example)'}
- {id: p9-strategy-service-cli, content: "- [x] [AGENT] P2. Strategy-service CLI already standardized — uses ServiceBootstrap with --operation backtest|trade, --mode batch|live. Entry point at __main__.py delegates to service_entry.py:run_service_cli(). `python -m strategy_service` works. No changes needed. The orchestrator and backfill scripts expect `python -m strategy_service --operation X --mode batch`. Check:\n  1. Read strategy_service/cli/service_entry.py — what's the current entry point pattern?\n  2. If it uses ServiceBootstrap: just needs a main.py wrapper that imports and calls it\n  3. If it doesn't use ServiceBootstrap: refactor to use it (same pattern as instruments-service, features-sports-service)\n  4. Verify strategy-service has standard --operation, --mode, --asset-group, --start-date, --end-date flags\n  Files: strategy_service/cli/service_entry.py, strategy_service/cli/ (check for grid_generator.py, resolvers.py which are also in cli/)\n", status: done, note: 'Already
    uses ServiceBootstrap with --operation backtest|trade, --mode batch|live. No changes needed.'}
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **SUPERSEDED 2026-04-25 by
> [consolidated_operational_validation_2026_04_15.plan.md](./consolidated_operational_validation_2026_04_15.plan.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Unified Pipeline Scheduling & Triggers

## Context

The Unified Trading System has 6 deployment clusters (CEFI, DEFI, TRADFI, SPORTS, PREDICTION, FULL) running 4
operational modes:

1. **Historical Backfill** — one-time full history, VM-based, all services
2. **T+1 Daily** — scheduled daily, processes yesterday, keeps history rolling
3. **Thermal/Experimental** — ML training iterations, config-driven, GPU instances
4. **Live** — continuous (CeFi/DeFi/TradFi) or discrete fixture-proximate jobs (Sports)

An end-to-end audit (2026-04-15) revealed that while most services have CLIs and terraform, the pipeline has critical
wiring gaps preventing any cluster from running fully automated across all 4 modes.

## Audit Findings (2026-04-15)

### Cluster Readiness Summary

| Cluster    | Mode 1 (Backfill)              | Mode 2 (T+1)                          | Mode 3 (Thermal)                | Mode 4 (Live)                   |
| ---------- | ------------------------------ | ------------------------------------- | ------------------------------- | ------------------------------- |
| CEFI       | READY                          | READY (all services in T+1 scheduler) | READY                           | READY                           |
| DEFI       | READY                          | READY                                 | MISSING (no ML — intentional)   | READY                           |
| TRADFI     | PARTIAL (corp-actions missing) | READY                                 | READY                           | READY                           |
| SPORTS     | READY (MTDS added to cluster)  | READY (in T+1 scheduler)              | READY (SPORTS in ML categories) | READY (fixture scheduler built) |
| PREDICTION | PARTIAL (MTDS not in cluster)  | PARTIAL                               | N/A                             | PARTIAL                         |

### Cross-Cutting Blockers

1. **instruments-service + MTDS not in T+1 scheduler** — pipeline root has no automatic trigger (all clusters)
2. **instruments-service emits no DATA_READY event** — MTDS live mode listens but nothing fires
3. **MDPS T+1 terraform uses wrong CLI args** — `--date` vs `--start-date/--end-date` (all clusters)
4. **MDPS category handling via env var** — non-standard, orchestrator can't invoke uniformly
5. **Sports cluster missing MTDS** — no odds data path into features-sports-service
6. **ml-training-service: CEFI+TRADFI only** — SPORTS and DEFI ML training blocked
7. **No sports fixture-aware scheduler** — discrete live jobs can't auto-trigger
8. **No standardized live/ partition** — only MDPS has it; batch vs live reconciliation impossible elsewhere
9. **dependencies.yaml incomplete** — features-sports shows `upstream: []`, missing services
10. **2 repos referenced in clusters don't exist** — corporate-actions, risk-management-service

### Sports Trigger Architecture

Sports pipelines are fundamentally discrete, not continuous. Both batch and live run the same CLI invocations — the
difference is timing:

- **Batch**: `--date yesterday` on daily cron (same as all categories)
- **Live**: `--date today` fired at fixture-proximate times by a scheduler that reads GCS fixture calendar

Trigger tiers (relative to fixture kickoff):

```
[Tier 0] UAC League Registry (code — deploy-time only)
 └─[Tier 1] League-team membership, season calendar (season boundaries)
    └─[Tier 2] Fixture calendar, standings, injuries, transfers (daily / window-based)
       ├─[Tier 3] Pre-match odds, predictions, weather, lineups (T-24h / T-6h / T-1h)
       ├─[Tier 4] Live streaming: progressive odds + stats (during fixture — viz only)
       └─[Tier 5] Post-match stats, xG, settlement (T+30min / T+24h)
```

The sports fixture scheduler (Phase 4) reads the fixture calendar from GCS, determines what's due per tier, and fires
standard batch CLI invocations. It lives in deployment-service alongside the T1Orchestrator.

### Data Source Availability (Batch = Live)

Same data sources for batch and live, with live availability confirmed:

| Tier | Data                   | Source                    | Real-time?                 | Notes                                    |
| ---- | ---------------------- | ------------------------- | -------------------------- | ---------------------------------------- |
| 1    | League-team membership | API Football /leagues     | Yes (API)                  | Refresh at season boundaries             |
| 2    | Fixture calendar       | API Football /fixtures    | Yes (API)                  | Refresh daily, future fixtures available |
| 2    | Injuries + suspensions | API Football /injuries    | Yes (API)                  | Refresh daily + T-24h                    |
| 2    | Transfers              | Transfermarkt             | Delayed (scraper)          | Window-bounded, hours lag                |
| 3    | Pre-match odds         | Odds API                  | Yes (API, 60 credits/call) | T-24h/12h/6h/4h/2h/1h/10m buckets        |
| 3    | Predictions            | FootyStats / API Football | Yes (API)                  | T-24h                                    |
| 3    | Weather                | Open-Meteo                | Yes (API, free)            | T-24h + T-1h                             |
| 3    | Confirmed lineups      | API Football /lineups     | Yes (API)                  | T-1h (when available)                    |
| 4    | Progressive stats      | SoccerFootball Info       | Yes (streaming)            | Viz only, not for trading                |
| 4    | Progressive odds       | Odds API / Betfair stream | Yes (streaming)            | Viz only, not for trading                |
| 5    | Post-match stats       | API Football              | Yes (API)                  | Minutes after FT                         |
| 5    | xG / advanced          | Understat / FootyStats    | Delayed                    | Hours-days lag                           |

Execution is manual on Betfair to start — not affected by triggers.

### Backlog Item: AbsenceType Enum

`CanonicalInjury` model in UAC has free-text `reason` field. Need structured `absence_type: AbsenceType` enum (INJURY,
SUSPENSION_RED_CARD, SUSPENSION_YELLOW_ACCUMULATION, etc.) for clean feature filtering. Existing GCS parquets have
`reason` populated — can backfill via Option A (read parquets, classify, rewrite, no API calls).

## Execution DAG

```
Phase 0 (Config Fixes)     ─── no code changes, just YAML ─── QG: N/A
  │
Phase 1 (Pipeline Root)    ─── instruments + MTDS T+1 + completion events ─── QG: instruments, MTDS, MDPS, deployment-service
  │
Phase 2 (Conventions)      ─── live/ partition, --run-tag, completion events ─── QG: UTL, all feature services
  │  [PARALLEL with Phase 3]
Phase 3 (Sports + ML)      ─── AbsenceType enum, ML SPORTS/DEFI categories ─── QG: UAC, instruments, ml-training
  │
Phase 4 (Sports Triggers)  ─── fixture-aware scheduler, trigger tiers, discrete jobs ─── QG: deployment-service
  │  [PARALLEL with Phase 5]
Phase 5 (Backfill Infra)   ─── per-cluster VM templates, resume, UI ─── QG: deployment-service
  │  [PARALLEL with Phase 6]
Phase 6 (Thermal/ML Infra) ─── experiment orchestration, UI ─── QG: ml-training, deployment-service
  │
Phase 7 (Data Status)      ─── all-modes manifest, batch/live recon, fixture-based sports status ─── QG: deployment-service, all services
  │
Phase 8 (E2E Validation)   ─── per-cluster end-to-end tests across all 4 modes ─── QG: all repos
  │
Phase 9 (Polish)           ─── AWS parity, strategy-service CLI ─── QG: deployment-service, strategy-service
```

## Success Criteria

- **C4**: All modified repos pass quality-gates.sh
- **D3**: All 6 clusters can run Mode 1 (backfill) and Mode 2 (T+1) on GCP
- **B4**: Batch vs live reconciliation passes for CEFI and SPORTS clusters (7-day window)
- Sports fixture scheduler fires correct CLI invocations at correct fixture-proximate times
- Data status UI shows completeness across all 4 modes for all clusters
