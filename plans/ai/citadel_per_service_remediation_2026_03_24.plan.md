---
title: "Citadel-Grade Per-Service Remediation Details — 20 Services"
created: 2026-03-24
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-24
priority: P0
parent_plan: citadel_service_remediation_2026_03_24.plan.md
---

# Per-Service Remediation Details

> **Conflict resolution**: This is the EXECUTION plan — agents work from this plan's per-service sections.
> citadel_service_remediation is the STATUS TRACKER (parent). QG sweep lint/ruff fixes (full_qg_sweep plan) should run
> BEFORE structural changes in this plan. structured_error_handling handler logic should run AFTER this plan's
> structural refactoring per service.

Parent plan: `citadel_service_remediation_2026_03_24.plan.md` Reference implementations: instruments-service,
market-tick-data-service

---

## TIER 1 — Quick Wins (1-2 hours each)

---

### 1. batch-live-reconciliation-service (3,934L → ~3,600L)

**Current state:** ServiceBootstrap present, config correct, tests passing. Close to template.

**Structural moves:**

- [ ] [AGENT] P0. Delete `[dependency-groups] dev = [...]` from pyproject.toml (flat-deps violation)
- [ ] [AGENT] P0. Move `batch_live_reconciliation_service/orchestrator.py` →
      `batch_live_reconciliation_service/engine/orchestrator.py`
- [ ] [AGENT] P0. Extract inline `ReconcileHandler` from `cli/main.py` → `cli/handlers/reconcile_handler.py`
- [ ] [AGENT] P0. Add `pre-flight-audit.sh` symlink to scripts/
- [ ] [AGENT] P0. Verify `models/recon_report.py` and `models/deviation_thresholds.py` marked `CORRECT-LOCAL` are
      genuinely service-local (not duplicating UIC types)
- [ ] [AGENT] P0. Run QG, fix any remaining violations

**Mock scenario semantics:** Reconciliation gaps between batch and live positions — phantom fills, missing fills,
timestamp drift, balance mismatch.

---

### 2. pnl-attribution-service (5,617L → ~5,100L)

**Current state:** ServiceBootstrap present (but dual entry-point), health API present.

**Deletions:**

- [ ] [AGENT] P0. Delete `pnl_attribution_service/cli/service_entry.py` (legacy ServiceCLI duplicate)
- [ ] [AGENT] P0. Delete `pnl_attribution_service/main.py` (redundant delegator — `__main__.py` exists)
- [ ] [AGENT] P0. Delete `htmlcov/` directory (committed coverage artifacts)
- [ ] [AGENT] P0. Delete `scripts/setup-workspace.sh` (non-standard)

**Structural moves:**

- [ ] [AGENT] P0. Create `engine/orchestrator.py` wrapping `engine/breakdown.py` + `engine/pnl_input_builder.py` with
      shard-level failure isolation per instrument
- [ ] [AGENT] P0. Verify `engine/types.py` — check if `PnLBreakdown` and `GreeksExposure` duplicate UIC types; if so,
      delete and import from UIC
- [ ] [AGENT] P0. Fix Dockerfile: add `--platform=linux/amd64` to FROM line

**Mock scenario semantics:** PnL attribution with missing price data, zero-volume instruments, extreme position sizes,
Greeks explosion on near-expiry options.

---

### 3. risk-and-exposure-service (12,324L → ~11,000L)

**Current state:** ServiceBootstrap present, health API present.

**Fixes:**

- [ ] [AGENT] P0. Fix Dockerfile: change `us-central1-docker.pkg.dev` → `asia-northeast1-docker.pkg.dev`
- [ ] [AGENT] P0. Wire `RiskLiveHandler` into `_OPERATIONS` dict (currently defined but never dispatched)

**Deletions:**

- [ ] [AGENT] P0. Delete `corporate_actions_backfill_output/`, `corporate_actions_output/`, `data/`, `logs/` (committed
      runtime artifacts)
- [ ] [AGENT] P0. Verify `models.py` `RiskLimits` marked `CORRECT-LOCAL` — confirm not in UIC; if duplicate, delete

**Structural moves:**

- [ ] [AGENT] P0. Create `engine/orchestrator.py` from risk computation logic currently inline in handlers
- [ ] [AGENT] P0. Run QG, fix any remaining violations

**Mock scenario semantics:** Limit breaches, position overflow triggering circuit breaker, margin call thresholds,
correlated position risk spike, missing price feeds for mark-to-market.

---

### 4. ml-inference-service (16,155L → ~13,000L)

**Current state:** ServiceBootstrap present, health API present (but data_freshness hardcoded).

**Fixes:**

- [ ] [AGENT] P0. Wire `_data_freshness()` in `api/main.py` to actual last-inference timestamp (currently returns
      `stale: True` always)
- [ ] [AGENT] P0. Address 6 `type:ignore` on `model.predict()` — create typed Protocol wrapper for sklearn/numpy predict
      interface

**Deletions:**

- [ ] [AGENT] P0. Delete `ml_inference_service/models.py` (self-describes as DEPRECATED, migration to UIC never
      completed)
- [ ] [AGENT] P0. Delete `pytest.ini` (duplicate — use pyproject.toml)
- [ ] [AGENT] P0. Delete `specs/`, `Makefile`, `LICENSE`, `CONTRIBUTING.md` (root clutter)
- [ ] [AGENT] P0. Delete `scripts/data_catalog.py`, `scripts/check-ruff-versions.sh` (non-standard)

**Structural moves:**

- [ ] [AGENT] P0. Move `app/inference/orchestrator.py` → `engine/orchestrator.py`
- [ ] [AGENT] P0. Flatten `app/` into top-level packages (app/core/ → engine/, etc.)
- [ ] [AGENT] P0. Run QG

**Mock scenario semantics:** Stale model (not retrained for 7 days), prediction NaNs, feature drift (input schema
changed), model load failure, inference timeout.

---

### 5. features-commodity-service (7,991L → ~7,800L)

**Current state:** Cleanest of the features services. ServiceBootstrap, health API, 98% coverage, zero violations.

**Structural moves:**

- [ ] [AGENT] P0. Rename `app/sources/` → `adapters/` (6 external API files: baker_hughes, cftc, eia_crude, eia_ng,
      open_meteo, yahoo_finance)
- [ ] [AGENT] P0. Create `engine/orchestrator.py` from `app/engine/signal_composer.py` orchestration logic
- [ ] [AGENT] P0. Flatten `app/` namespace: `app/engine/` → `engine/`, `app/factors/` → `engine/factors/`
- [ ] [AGENT] P0. Consider adding `--asset-group COMMODITY` as fixed default (currently `add_category_arg=False`)
- [ ] [AGENT] P0. Run QG

**Mock scenario semantics:** EIA/CFTC API downtime, stale commodity data (weekends/holidays), extreme price moves (oil
shock), missing seasonal adjustments.

---

### 6. features-multi-timeframe-service (11,218L → ~10,800L)

**Current state:** Cleanest structure overall. Has an orchestrator (at wrong path). 96% coverage, zero violations.

**Critical fix:**

- [ ] [AGENT] P0. **Create Dockerfile** (currently missing — service cannot be deployed). Use instruments-service
      Dockerfile as template.

**Structural moves:**

- [ ] [AGENT] P0. Move `app/engine/orchestrator.py` → `engine/orchestrator.py` (template path)
- [ ] [AGENT] P0. Flatten `app/` namespace into top-level packages
- [ ] [AGENT] P0. Verify `schemas/output_schemas.py` DEPRECATION NOTICE — delete if no imports remain
- [ ] [AGENT] P0. Run QG

**Mock scenario semantics:** Upstream timeframe gaps (1h bars missing for 3 hours), NaN propagation through multi-TF
alignment, schema drift between timeframes.

---

## TIER 2 — Moderate (half-day each)

---

### 7. features-calendar-service (11,055L → ~9,000L)

**Current state:** No ServiceBootstrap — uses Click directly. `app/` vs `engine/` split-brain.

**Critical restructure:**

- [ ] [AGENT] P1. Replace Click entry point with ServiceBootstrap in `cli/main.py`
- [ ] [AGENT] P1. Consolidate `app/calculators/` → `engine/calculators/`, delete empty `app/core/`
- [ ] [AGENT] P1. Move `conftest.py` from repo root → `tests/conftest.py`

**Deletions:**

- [ ] [AGENT] P1. Delete `pip.conf` (committed with `{project_id}` placeholder)
- [ ] [AGENT] P1. Delete `REVIEW_2026-02-09.md`, `CODEX_VIOLATIONS_MANIFEST.md`, `DEPLOYMENT_COMMAND_REFERENCE.md` (root
      artifacts)
- [ ] [AGENT] P1. Delete `scripts/check-ruff-versions.sh`, `scripts/setup-workspace.sh` (non-standard)
- [ ] [AGENT] P1. Run QG, fix type:ignore (4) + Any (1) + os.getenv (3)

**Mock scenario semantics:** Corporate action on processing date, earnings surprise during market hours, exchange
holiday not in calendar, stale economic indicator feed.

---

### 8. features-sports-service (19,614L → ~14,000L)

**Current state:** ServiceBootstrap present, health API present. Large tracking registry bloat.

**Critical restructure:**

- [ ] [AGENT] P1. Move `tracking/` registry (9 files, ~1,500L of fixture data) to URDI or UIC testing/scenarios
- [ ] [AGENT] P1. Delete `schemas/output_schemas.py` (dual-SSOT violation — column lists mirror UIC TypedDict)
- [ ] [AGENT] P1. Rename `engine/sports_engine.py` → `engine/orchestrator.py`
- [ ] [AGENT] P1. Evaluate `arb/` (arbitrage calc) — belongs in UTL or domain-client, not the service
- [ ] [AGENT] P1. Evaluate `etl/` — orphan ETL state management with no clear pipeline owner

**Deletions:**

- [ ] [AGENT] P1. Delete `scripts/batch_fetch.sh`, `QUALITY_GATE_BYPASS_AUDIT.md`, `pyproject.tmp`
- [ ] [AGENT] P1. Fix type:ignore (2) + Any (2)
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Match postponement, walkover, live odds spike (10x in 30 seconds), stale fixture feed,
missing result for settled market.

---

### 9. features-volatility-service (15,049L → ~11,500L)

**Current state:** Orchestrator split across `app/core/`. Root dir clutter.

**Critical restructure:**

- [ ] [AGENT] P1. Consolidate `app/core/orchestration_service.py` + `app/core/volatility_orchestration.py` →
      `engine/orchestrator.py`
- [ ] [AGENT] P1. Flatten `app/` namespace
- [ ] [AGENT] P1. Delete `schemas/output_schemas.py` (dual-SSOT)

**Deletions:**

- [ ] [AGENT] P1. Delete `Makefile`, `LICENSE`, `CONTRIBUTING.md`, `CHANGES_2026-02-09.md` (root boilerplate)
- [ ] [AGENT] P1. Delete `stubs/scipy` (use upstream type stubs)
- [ ] [AGENT] P1. Delete `specs/` (design docs belong in PM)
- [ ] [AGENT] P1. Delete `scripts/data_catalog.py`, `scripts/check-ruff-versions.sh`
- [ ] [AGENT] P1. Fix Any (2)
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** VIX spike (>80), vol surface inversion, missing implied vol for illiquid strikes, term
structure kink, realized vs implied divergence.

---

### 10. features-cross-instrument-service (12,675L → ~12,200L)

**Current state:** No Dockerfile, local domain types in sports_bridge.py.

**Critical fixes:**

- [ ] [AGENT] P1. **Create Dockerfile** (P0 — service cannot be deployed)
- [ ] [AGENT] P1. Move `sports_bridge.py` types (`SportsBridgeSignal`, `SportsBridgeConfig`) to UIC, delete local file

**Structural moves:**

- [ ] [AGENT] P1. Create `engine/orchestrator.py` from handler-embedded dispatch of 17 calculator files in
      `app/calculators/`
- [ ] [AGENT] P1. Verify `schemas/output_schemas.py` DEPRECATION NOTICE — delete if no imports
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Cross-asset correlation breakdown (crypto-equity decouple), missing instrument in pair,
stale correlation matrix, regime change mid-window.

---

### 11. features-onchain-service (14,592L → ~12,500L)

**Current state:** 8 adapters (good), but redundant compute_handler layer + io/ below adapters.

**Critical restructure:**

- [ ] [AGENT] P1. Delete `cli/compute_handler.py` (204L redundant dispatch layer) — wire BatchHandler/LiveHandler
      directly in main.py
- [ ] [AGENT] P1. Flatten `io/` into `adapters/` (OnChainWriter absorbed into adapters/onchain_writer.py)
- [ ] [AGENT] P1. Move `app/core/onchain_orchestration.py` → `engine/orchestrator.py`

**Deletions:**

- [ ] [AGENT] P1. Delete `pip.conf` (placeholder `{project_id}`), `coverage_new.xml`, `chatgpt_instructions.md`,
      `Makefile`, `LICENSE`
- [ ] [AGENT] P1. Delete `CODEX_VIOLATIONS_MANIFEST.md`
- [ ] [AGENT] P1. Delete `DATA_SOURCES_REFERENCE.py` (384L dict masquerading as Python — move to docs/ as markdown)
- [ ] [AGENT] P1. Delete `models.py` (thin re-export shim — verify no callers)
- [ ] [AGENT] P1. Delete `scripts/check-ruff-versions.sh`, `scripts/data_catalog.py`, `scripts/test_defillama.py`
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** RPC node timeout, empty mempool, flash loan revert, gas price spike (100x), stale block (no
new blocks for 5 min), chain reorganization.

---

### 12. position-balance-monitor-service (13,031L → ~11,500L)

**Current state:** ServiceBootstrap present, health API present. Shadow package at root.

**Critical deletions:**

- [ ] [AGENT] P1. Delete `position_monitor/` shadow package at repo root (orphaned duplicate of
      position_balance_monitor_service/storage/)
- [ ] [AGENT] P1. Delete `position_monitor.db` (52KB SQLite committed to git)
- [ ] [AGENT] P1. Delete `scripts/demo.sh` (non-standard)

**Structural moves:**

- [ ] [AGENT] P1. Create `engine/orchestrator.py` from reconciliation logic currently in `cli/main.py`
- [ ] [AGENT] P1. Audit `models.py` — mixed-concern file importing from UIC; split or absorb
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Phantom positions (exchange reports position service doesn't know about), balance mismatch
(exchange balance ≠ computed balance), reconciliation timeout, stale balance (exchange API returns cached data).

---

### 13. ml-training-service (36,614L → ~28,000L)

**Current state:** ServiceBootstrap present, 86% coverage. Tests inside source tree.

**Critical fixes:**

- [ ] [AGENT] P1. Move `ml_training_service/ml/tests/` → `tests/unit/ml/` (tests inside source package)
- [ ] [AGENT] P1. Wire `_data_freshness()` in `api/main.py` to last training run timestamp from model registry
- [ ] [AGENT] P1. Create `adapters/` directory for GCS feature loaders (currently scattered in app/core/)

**Deletions:**

- [ ] [AGENT] P1. Delete `run_smoke_test.sh` (root-level orphan), `pytest.ini`, `stubs/`, `data/`, `examples/`
- [ ] [AGENT] P1. Delete `AUDIT_REPORT_2026-02-09.md`, `CODEX_VIOLATIONS_MANIFEST.md`, `QUALITY_GATE_BYPASS_AUDIT.md`
- [ ] [AGENT] P1. Delete `scripts/e2e_mock_pipeline.py`, `scripts/etl_gcs_to_bigquery.py`,
      `scripts/seed_mock_features_to_gcs.py`, `scripts/data_catalog.py`, `scripts/check-ruff-versions.sh`

**Structural moves:**

- [ ] [AGENT] P1. Consolidate `app/training/` (10 files) → `engine/orchestrator.py` entry point
- [ ] [AGENT] P1. Fix type:ignore (5 — model.predict interop)
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Feature drift (schema changed since last training), stale model (>7 days), training data
gap, model performance degradation (accuracy below threshold), GPU OOM during training.

---

### 14. trading-agent-service (5,908L → ~5,800L)

**Current state:** No CLI/ServiceBootstrap, no health API (we added the api/main.py file earlier but no CLI wiring), no
adapters/.

**Critical restructure:**

- [ ] [AGENT] P1. Create `cli/main.py` with ServiceBootstrap (replace raw `__main__.py` asyncio.run)
- [ ] [AGENT] P1. Create `cli/handlers/agent_handler.py` with UnifiedServiceHandler wrapping the loop orchestration
- [ ] [AGENT] P1. Create `adapters/` package — extract HTTP calls from `app/loops/l*.py` into discrete adapters
      (execution_adapter.py, features_adapter.py, risk_adapter.py)
- [ ] [AGENT] P1. Move `app/orchestrator.py` → `engine/orchestrator.py`
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Downstream service timeout (execution-service unreachable for 30s), config hot-reload race
(strategy config changes mid-loop), loop panic (unhandled exception in L3), cascading loop failure (L1 failure → L2-L8
stall).

---

## TIER 3 — Major Restructuring (dedicated sessions)

---

### 15. alerting-service (10,867L → ~8,500L)

**Current state:** Dockerfile broken (copies wrong module name). No ServiceBootstrap. Monolith main.py.

**Critical fixes:**

- [ ] [AGENT] P1. Fix Dockerfile: `COPY alerting_system/` → `COPY alerting_service/` (build currently fails)
- [ ] [AGENT] P1. Create `cli/main.py` with ServiceBootstrap (replace raw argparse in main.py)
- [ ] [AGENT] P1. Create `cli/handlers/alert_handler.py` from logic in monolith main.py (~200L)
- [ ] [AGENT] P1. Create `adapters/` for notifier HTTP calls (currently direct in `notifiers/`)
- [ ] [AGENT] P1. Create `engine/orchestrator.py` for alert evaluation + dispatch pipeline

**Deletions:**

- [ ] [AGENT] P1. Delete `htmlcov/`, `config/default_rules.yaml` (inline), `scripts/setup-workspace.sh`, `specs/`
- [ ] [AGENT] P1. Fix type:ignore (1) + Any (1) + os.getenv (3)
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Alert storm (100+ alerts/sec), dead notification channel (Telegram/Slack unreachable),
alert deduplication under burst, threshold oscillation (alert fires → clears → fires in rapid succession).

---

### 16. features-delta-one-service (38,268L → ~22,000L)

**Current state:** Ghost shadow package, massive root doc dump, lowest coverage for its size.

**Critical deletions (biggest single cleanup):**

- [ ] [AGENT] P1. Delete entire `features_service/` ghost package (~4,352L shadow calculators from old layout)
- [ ] [AGENT] P1. Delete 12+ root-level session docs: AUDIT_REPORT, CALIBRATION_FIXES, DUAL_DASHBOARD_GUIDE,
      FIX_PORT_3001, COMPREHENSIVE_TEST_VALIDATION, DATA_SHIFTING_VERIFICATION, FINAL_TEST_VERIFICATION,
      GMM_EXPLANATION, GMM_VS_TREE_MODELS_ANALYSIS, INSTALLATION, INSTRUMENT_ID_FORMAT_ANALYSIS, PHASE4_COMPLETE,
      QUICK_START_REAL_DATA, TEST_QUALITY_ANALYSIS
- [ ] [AGENT] P1. Delete 3 root HTML files: combined_demo.html, oscillators_demo.html, volatility_demo.html
- [ ] [AGENT] P1. Delete `htmlcov/` (28 committed files), `data/mock/`, `examples/` (4 scripts)
- [ ] [AGENT] P1. Delete `scripts/comprehensive_profiling.py`, `scripts/coverage-report.sh`, `scripts/data_catalog.py`,
      `scripts/run_local.sh`

**Structural moves:**

- [ ] [AGENT] P1. Delete deprecated `schemas/output_schemas.py` (self-labelled DEPRECATED)
- [ ] [AGENT] P1. Move `app/core/orchestration_service.py` → `engine/orchestrator.py`
- [ ] [AGENT] P1. Resolve `models.py` — `ProcessingMode` and `FeatureGroup` to UIC or parser.py
- [ ] [AGENT] P1. Raise coverage floor from 71% → 80%
- [ ] [AGENT] P1. Fix type:ignore (6 — if present in prod source)
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Feature calculation with missing upstream candles, NaN propagation through 42 calculators,
schema drift between calculator outputs, extreme delta (>5 sigma move in underlying).

---

### 17. market-data-processing-service (39,594L → ~28,000L)

**Current state:** 20 `Any` violations, local domain types, committed htmlcov.

**Critical type fixes:**

- [ ] [AGENT] P1. Fix 20 `Any` violations (concentrated in candle_metadata_helpers.py, orchestration_scheduling.py) —
      replace `dict[str, Any]` with typed UIC/UAC TypedDicts
- [ ] [AGENT] P1. Move `MarketCategory`, `CandleAggregationConfig`, `MarketStateConfig` from local `config.py` to UIC

**Deletions:**

- [ ] [AGENT] P1. Delete `htmlcov/`, `data/samples/`, `examples/`, `issues/`, `spec/` (committed artifacts)
- [ ] [AGENT] P1. Delete `pytest.ini` (use pyproject.toml)
- [ ] [AGENT] P1. Delete `AUDIT_REPORT_2026-02-09.md`, `CODEX_VIOLATIONS_MANIFEST.md`, `EMBEDDING_GUIDE.md`,
      `TEST_CHECKLIST_2024-07-01.md`, `QUALITY_GATE_BYPASS_AUDIT.md`
- [ ] [AGENT] P1. Delete `scripts/run_local.sh`, `scripts/verify_setup.sh`, `scripts/check-ruff-versions.sh`,
      `scripts/data_catalog.py`, `scripts/migrate_processed_candles_structure.py`, `scripts/fix_other_to_futures.py`

**Structural moves:**

- [ ] [AGENT] P1. Move `app/core/` orchestration → `engine/orchestrator.py`
- [ ] [AGENT] P1. Run QG

**Mock scenario semantics:** Candle gap (missing 15-min bars), tick burst (10x normal rate), stale feed (same timestamp
repeated), schema violation in upstream tick data, timezone drift in candle alignment.

---

### 18. deployment-service (77,673L → ~45,000L)

**Current state:** Dual CLI entry points, duplicate orchestrator, 50+ script graveyard. Largest single cleanup.

**Critical restructure:**

- [ ] [AGENT] P2. Delete `deployment_service/cli.py` (497L Click-based) — keep only `deployment_service/cli/main.py`
- [ ] [AGENT] P2. Delete `deployment_service/cli_commands/` (empty stub) and `deployment_service/cli_modules/`
      (redundant)
- [ ] [AGENT] P2. Merge `deployment_service/orchestrator.py` (flat file) + `deployment_service/orchestrator/`
      (sub-package) — keep one canonical path
- [ ] [AGENT] P2. Migrate from Click to ServiceBootstrap in cli/main.py

**Deletions:**

- [ ] [AGENT] P2. Delete `deploy.py` and `cleanup_old_instruments_parquet.py` at repo root
- [ ] [AGENT] P2. Delete ~35 orphaned scripts: `migrate_*.py`, `reorganize_gcs*.py`, `delete_old_gcs_structure.sh`,
      `cleanup-*.sh`, `setup-billing-alerts.sh`, `setup-branch-protection.sh`, etc.
- [ ] [AGENT] P2. Delete `.basedpyright-baseline.json.bak`
- [ ] [AGENT] P2. Evaluate `infra/`, `terraform/`, `grafana/` — move to dedicated infra repo or PM
- [ ] [AGENT] P2. Fix type:ignore (9) + Any (2) + os.getenv (5)
- [ ] [AGENT] P2. Run QG

**Mock scenario semantics:** Shard failure during deployment, partial rollout (3 of 5 shards healthy), rollback trigger,
version mismatch between shards, Cloud Build timeout.

---

### 19. strategy-service (60,787L → ~35,000L)

**Current state:** Dual engine tree (`engine/` + `engine/core/`), massive script sprawl, deprecated schemas.

**Critical restructure:**

- [ ] [AGENT] P2. Merge `engine/strategies/` and `engine/core/strategies/` — pick one canonical path, delete the other
- [ ] [AGENT] P2. Merge `engine/backtest/` and `engine/core/backtest/` — same
- [ ] [AGENT] P2. Delete deprecated `schemas/output_schemas.py` (self-labelled, superseded by models.output_schemas)

**Deletions:**

- [ ] [AGENT] P2. Delete 12 orphaned scripts: `run_cefi_backtest.py`, `run_defi_backtest.py`, `run_tradfi_backtest.py`,
      `run_sports_arb_backtest.py`, `run_parallel_backtests.sh`, `run_portable_backtests.sh`, `run_local.sh`,
      `check-ruff-versions.sh`, `frontend.sh`, `data_catalog.py`, `export_strategy_csvs.py`, `README_FRONTEND.md`
- [ ] [AGENT] P2. Delete `data/`, `artifacts/`, `logs/`, `examples/`, `presentation/`, `strategy_analysis_presentation/`
      (committed output)
- [ ] [AGENT] P2. Delete 18 root-level markdown files (AUDIT_REPORT, CALIBRATION_FIXES, etc.)
- [ ] [AGENT] P2. Evaluate `signal_generation/` — appears to be alpha testing scaffolding; audit for active use
- [ ] [AGENT] P2. Fix type:ignore (6)
- [ ] [AGENT] P2. Run QG

**Mock scenario semantics:** Signal inversion (all signals flip sign), extreme conviction (100% allocation to one
instrument), missing features for 50% of universe, strategy config hot-reload mid-backtest, position limit breach during
signal generation.

---

### 20. execution-service (166,656L → ~110,000L) — THE FINAL BOSS

**Current state:** 153 `Any` types (worst in workspace). 40+ orphan scripts. mypy + basedpyright conflict.

**Critical type fixes (biggest single effort):**

- [ ] [AGENT] P2. Remove `[tool.mypy]` from pyproject.toml (conflicts with basedpyright — not the workspace standard)
- [ ] [AGENT] P2. Fix 153 `Any` type usages systematically — this requires:
  - Identify which `Any` are in hot paths (engine/, adapters/) vs. cold paths (scripts/, models/)
  - Replace `dict[str, Any]` with typed UIC/UAC TypedDicts
  - Replace `Callable[..., Any]` with typed Protocols
  - Replace `list[Any]` with concrete types
  - This is 10-20 files × 7-10 fixes each — estimated 2-3 hours

**Deletions:**

- [ ] [AGENT] P2. Delete `test_borrow_lend_stake_5min.py`, `verify_and_test_backtest.py` at repo root
- [ ] [AGENT] P2. Delete ~35 orphaned scripts in `scripts/`: `analyze_backtest_legs.py`, `check_tradfi_data_*.py`,
      `debug_check_*.py`, `generate_*.py`, `migrate_*.py`, `split_algorithms.py`, `upload_*.py`,
      `write_config_snapshot.py`, `run_backtest_with_log.*`, and all files under `runners/`, `demos/`,
      `benchmark_runners/`, `config_generation/`, `instruction_generation/`, `migrations/`
- [ ] [AGENT] P2. Delete `.env` at repo root, `.cache/nautilus/`
- [ ] [AGENT] P2. Fix type:ignore (2) + os.getenv (9)
- [ ] [AGENT] P2. Run QG

**Mock scenario semantics:** Order rejection (insufficient margin), partial fill (50% filled then venue down), execution
timeout (no fill after 30s), venue maintenance window, slippage beyond limit, simultaneous multi-venue execution race
condition.

---

## Summary Matrix

| #   | Service             | Tier | Lines       | Post-Cleanup | Key Blocker           | Mock Theme         |
| --- | ------------------- | ---- | ----------- | ------------ | --------------------- | ------------------ |
| 1   | batch-live-recon    | T1   | 3,934       | 3,600        | [dependency-groups]   | Recon gaps         |
| 2   | pnl-attribution     | T1   | 5,617       | 5,100        | Dual entry-point      | Missing prices     |
| 3   | risk-and-exposure   | T1   | 12,324      | 11,000       | Dockerfile region     | Limit breaches     |
| 4   | ml-inference        | T1   | 16,155      | 13,000       | Hardcoded freshness   | Model staleness    |
| 5   | features-commodity  | T1   | 7,991       | 7,800        | No adapters/ dir      | API downtime       |
| 6   | features-multi-tf   | T1   | 11,218      | 10,800       | No Dockerfile         | Timeframe gaps     |
| 7   | features-calendar   | T2   | 11,055      | 9,000        | No ServiceBootstrap   | Corp actions       |
| 8   | features-sports     | T2   | 19,614      | 14,000       | Tracking registry     | Match postponement |
| 9   | features-volatility | T2   | 15,049      | 11,500       | Split orchestrator    | VIX spike          |
| 10  | features-cross-inst | T2   | 12,675      | 12,200       | No Dockerfile         | Correlation break  |
| 11  | features-onchain    | T2   | 14,592      | 12,500       | Redundant layers      | RPC timeout        |
| 12  | position-monitor    | T2   | 13,031      | 11,500       | Shadow package        | Phantom positions  |
| 13  | ml-training         | T2   | 36,614      | 28,000       | Tests in source       | Feature drift      |
| 14  | trading-agent       | T2   | 5,908       | 5,800        | No CLI at all         | Loop failure       |
| 15  | alerting            | T3   | 10,867      | 8,500        | Broken Dockerfile     | Alert storm        |
| 16  | features-delta-one  | T3   | 38,268      | 22,000       | Ghost package         | NaN propagation    |
| 17  | market-data-proc    | T3   | 39,594      | 28,000       | 20 Any types          | Candle gaps        |
| 18  | deployment          | T3   | 77,673      | 45,000       | Dual CLI + 50 scripts | Shard failure      |
| 19  | strategy            | T3   | 60,787      | 35,000       | Dual engine tree      | Signal inversion   |
| 20  | execution           | T3   | 166,656     | 110,000      | **153 Any types**     | Order rejection    |
|     | **TOTAL**           |      | **563,620** | **~404,300** |                       |                    |
