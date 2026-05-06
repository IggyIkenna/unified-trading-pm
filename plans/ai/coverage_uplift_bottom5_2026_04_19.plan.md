---
title: Coverage Uplift — Bottom 5 Repos (to 80%)
owner: iggy
created: 2026-04-19
status: active
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-04-19
---

# Coverage Uplift — Bottom 5 Repos

## Context

The [coverage ratchet sweep (2026-04-19)](coverage_ratchet_policy_2026_04_19.plan.md) identified five repos whose
current coverage is far enough below the 80% workspace target that ratchet-only (+2/sprint) would take a year+ to close.
These are the highest-risk hot paths (trade execution, market-data ingestion, on-chain feature calculation), so they get
explicit file-level test plans.

The file-level breakdowns come from each repo's `coverage.xml`, ranked by "most uncovered lines" =
`(1 − line_rate) × lines_valid`. Targets below are the files that will move the repo's floor the most per test written.

**Rule of engagement:** no coverage-stuffing. Every test either (a) asserts a contract (input → expected output/state),
(b) verifies a recovery path (error handling / shard-level failure isolation / degraded mode), or (c) locks in a
regression that was manually found. Tests that execute a function just to hit the lines do not qualify.

## Per-repo uplift plans

### 1. market-tick-data-service — 47.8 → 80 (+32.2)

Biggest absolute gap. 5,743 valid lines × 52.2% uncovered = **~3,000 lines to cover**. CLI handlers + migration scripts
carry most of the gap, and they drive the DeFi/sports/prediction ingestion pipelines — production-critical.

- [ ] [AGENT] P0. `scripts/migrate_sports_canonical.py` (292L, 0%). Add unit tests that mirror
      `test_migrate_tradfi_canonical.py`: classify-row, group-row, dry-run plan, end-to-end with in-memory GCS stub.
- [ ] [AGENT] P0. `scripts/migrate_prediction_canonical.py` (269L, 0%). Same test shape as tradfi/sports migrators.
- [ ] [AGENT] P0. `cli/handlers/data_manifest_handler.py` (229L, 0%). Unit tests for each `--operation` variant with a
      mock `ManifestReader`.
- [ ] [AGENT] P0. DeFi handler family (5 handlers, 24–35% covered, ~890L gap total):
  - `cli/handlers/dex_pools_handler.py` (253L, 24.5%)
  - `cli/handlers/dex_swaps_handler.py` (243L, 28.0%)
  - `cli/handlers/gas_fee_handler.py` (282L, 34.8%)
  - `cli/handlers/lending_indices_handler.py` (231L, 24.7%)
  - `cli/handlers/liquidations_handler.py` (236L, 29.2%) All follow the same shape: happy-path ingest, empty result,
    TheGraph error, invalid instrument_id → shard-isolated failure.
- [ ] [AGENT] P1. `cli/handlers/perp_funding_handler.py` (315L, 48.2%).
- [ ] [AGENT] P1. `scripts/migrate_polymarket_canonical.py` (331L, 56.8%).
- [ ] [SCRIPT] C2/C4 gate — each landed test PR must bump `MIN_COVERAGE` by the realised delta. Target floor by end of
      uplift: **80**.

### 2. trading-agent-service — 57.9 → 80 (+22.1)

Small repo (1,124L), but the uncovered surface is concentrated in adapters + the main orchestration loop — which is
literally the trade decision path. ~250 lines to cover.

- [ ] [AGENT] P0. `adapters/execution_adapter.py` (82L, 0%). Mock `execution-service` HTTP client; test
      submit/cancel/status happy path + 503 retry + timeout.
- [ ] [AGENT] P0. `adapters/risk_adapter.py` (30L, 0%). Mock `risk-and-exposure-service`; test allow/deny/resize paths
      against the 4-layer gate contract.
- [ ] [AGENT] P0. `adapters/features_adapter.py` (27L, 0%). Mock features-service; test vector fetch + staleness
      detection.
- [ ] [AGENT] P0. `cli/handlers/agent_handler.py` (65L, 0%). End-to-end run of the agent handler CLI with stubbed
      adapters.
- [ ] [AGENT] P1. `engine/mock_data_provider.py` (79L, 0%). Mock-mode unit tests (data-seed generation, deterministic
      output per-seed).
- [ ] [AGENT] P1. `config_reloaders.py` (56L, 0%). Test reloader wiring + typed-config path; smoke against
      `test_config.py` harness.
- [ ] [AGENT] P1. `app/loops/l3_trade_decision.py` (107L, 68.2%). Cover the untested branches (reject/resize paths,
      kill-switch active path).
- [ ] [SCRIPT] C4 — target floor: **80**.

### 3. execution-service — 59.6 → 80 (+20.4)

Largest repo (50,888L). Even 20% uplift = ~10,000 lines to cover — realistic over multiple sprints. Focus: venue
adapters + execution algorithms, both directly responsible for live-trading correctness.

- [ ] [AGENT] P0. **Venue adapters (3 files, ~780L gap):**
  - `trade_execution/adapters/binance_ccxt.py` (375L, 12.3%)
  - `trade_execution/adapters/okx_ccxt.py` (248L, 16.1%)
  - `trade_execution/ws_feeds.py` (268L, 20.9%) Tests: place-order happy path, partial-fill, cancel-ack, rejected-order,
    WS disconnect/reconnect, rate-limit 429 backoff. Use the `responses` library for REST; a `MockWebSocketFeed` for WS
    (already exists in MTDS — copy the pattern).
- [ ] [AGENT] P0. `defi_execution/protocols/aave.py` (365L, 21.6%). 13-error-code revert-classification matrix — one
      test per `DefiErrorCode`. Flash-loan happy path + insufficient-collateral revert.
- [ ] [AGENT] P0. `sports_execution/adapters/exchanges/betfair.py` (324L, 23.2%). Place-bet, cancel, fill-report
      parsing, back/lay side normalisation.
- [ ] [AGENT] P1. **Execution algorithms (4 files, ~870L gap):**
  - `algorithms/impl/almgren_chriss.py` (351L, 30.8%)
  - `algorithms/impl/pov_dynamic.py` (321L, 33.6%)
  - `algorithms/impl/vwap_execution.py` (355L, 40.6%)
  - `algorithms/impl/passive_aggressive_execution.py` (300L, 31.3%) Tests: slice-size computation under deterministic
    price paths, no-op when market-impact exceeds budget, correct fill-time distribution.
- [ ] [AGENT] P1. `engine/backtest/actors/signal_driven_v3_handlers.py` (339L, 38.9%).
- [ ] [SCRIPT] C4 — ratchet every sprint by realised delta. Target: **80** (estimated 4-6 sprints at sustained
      test-writing pace).

### 4. features-sports-service — 64.6 → 80 (+15.4)

7,651L. ~1,180 lines to cover. Gap concentrated in exporters + calculators — the read+transform path that feeds
strategy-service.

- [ ] [AGENT] P0. `exporters/derived_features_exporter.py` (535L, 9.5%). ~480 lines uncovered. Test each derived-feature
      family: form, xG, lineups, manager. Assert per-column schema contract hit.
- [ ] [AGENT] P0. `data/gcs_reader.py` (484L, 7.2%). Mock GCS; test date-range reads, missing-file fallback,
      corrupt-parquet isolation.
- [ ] [AGENT] P0. `calculators/odds_calculator.py` (516L, 20.7%). This is the bookmaker-agnostic fair-odds computation —
      highest business value. Test per-market-type (1x2, O/U, BTTS, handicap) + per-bookmaker overround.
- [ ] [AGENT] P1. `exporters/odds_features_exporter.py` (230L, 43.5%).
- [ ] [AGENT] P1. `calculators/transfer_window_calculator.py` (248L, 59.3%).
- [ ] [AGENT] P1. `calculators/team_form.py` (251L, 64.5%).
- [ ] [AGENT] P1. `calculators/replacement_model_calculator.py` (115L, 23.5%).
- [ ] [SCRIPT] C4 — target floor: **80**.

### 5. features-onchain-service — 66.9 → 80 (+13.1)

3,115L. ~410 lines to cover. Small enough for 2-3 focused sprints.

- [ ] [AGENT] P0. `engine/mock_data_provider.py` (171L, 0%). Mock-seeded feature generation — mirror
      `ml-training-service/mock_data_provider` tests.
- [ ] [AGENT] P0. `app/core/data_loader.py` (243L, 34.2%). GCS reader tests; missing-date fallback; schema-contract
      validation.
- [ ] [AGENT] P0. `engine/orchestrator.py` (332L, 59.3%). Cover the per-chain shard-isolation paths — this is the
      on-chain equivalent of MTDS's venue shard isolation.
- [ ] [AGENT] P1. `cli/main.py` (123L, 21.9%). CLI operation/mode/category axes.
- [ ] [AGENT] P1. `app/calculators/eigen_rewards_calculator.py` (114L, 26.3%).
- [ ] [AGENT] P1. `app/core/feature_writer.py` (118L, 42.4%).
- [ ] [AGENT] P1. `app/calculators/aave_rate_impact_calculator.py` (75L, 34.7%).
- [ ] [AGENT] P1. `config_reloaders.py` (42L, 0%).
- [ ] [SCRIPT] C4 — target floor: **80**.

## Cross-cutting infrastructure (all 5 repos)

- [ ] Use existing test harnesses, don't reinvent: `MockWebSocketFeed` lives in
      `market-tick-data-service/tests/market_interface/fixtures/mock_ws_server.py`; `tenderly_fork` fixtures live in
      `execution-service/tests/integration/conftest.py`; the `responses` library is already a workspace dep for REST
      mocking; `@mock_aws` (moto) for AWS; local GCS/pubsub emulators auto-detected via env vars per
      `unified-trading-pm/codex/08-workflows/local-dev.md`.
- [ ] Every new test file follows the "real tests only" rule from
      [coverage_ratchet_policy_2026_04_19.plan.md](coverage_ratchet_policy_2026_04_19.plan.md).
- [ ] Per-repo floor is ratcheted on each merged PR (not batch at the end), so the gain is locked in incrementally.

## Readiness

- [ ] C1 — first PR per repo lands P0 items
- [ ] C2 — full P0 wave passes QG
- [ ] C3 — lint + codex clean on all new test files
- [ ] C4 — each repo's `MIN_COVERAGE` hits **80**
- [ ] B1 — uplift tests include at least one per-handler assertion against the Citadel "shard-level failure isolation"
      contract (no raise inside per-venue/per-shard loops)

## References

- [coverage_ratchet_policy_2026_04_19.plan.md](coverage_ratchet_policy_2026_04_19.plan.md) — the ratchet policy +
  middle/high-tier plan
- [PLAN_FORMAT.md](../PLAN_FORMAT.md)
- Per-repo CLAUDE.md files carry test-harness instructions specific to each service.
