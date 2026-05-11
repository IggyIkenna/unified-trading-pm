---
plan_type: code+infra
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: available-at-lookahead-bias-completion-2026-05-08
title: "available_at + lookahead-bias master — SINGLE OWNER for all stamping work"
folds_in:
  - api_football_minimal_flattening_removal_2026_05_07 # Phase 3 stamping wiring scope
  - wave3x_residual_ssots_2026_05_08 # Track E sports stamping helpers
  - sports_master_2026_05_07 # Phase 1-2 per-adapter wiring scope
  # Implicit children (no separate plan): every CeFi/DeFi/TradFi tick adapter that needs
  # tick.timestamp + UAC SOURCE_PRIORITY scrape latency stamping per CLAUDE.md
  # "available_at semantics".
overview: >-
  **SINGLE-OWNER UMBRELLA for all `available_at` stamping work across the workspace** (codified 2026-05-08 per operator
  direction "same with available_at ownership do the same"). Stamping helpers do NOT execute in isolation — the
  source-specific stamping rule (UAC SSOT) + per-adapter `available_at` column write + UTL `record_captured` enforcement
  (`assert_available_at_present`) co-evolve as one atomic unit per asset_group. Audit 2026-05-08 found ~60% chain
  coverage with the gaps being implicit (assumed to roll downhill from one master plan to the next) rather than
  explicitly owned. This plan makes every chain link explicit, references the existing owners where coverage is real,
  and owns the gap items directly. Chain has 11 links: (0) MDPS bar timestamp + available_at semantics, (1)
  per-asset-group adapter stamping, (2) historical parquet backfill, (3) reader propagation, (4) UAC
  FEATURE_REQUIRED_INPUTS expansion, (5) UAC AVAILABILITY_AT_SEMANTICS coverage audit, (6) calculator/writer-boundary
  enforcement (Tab 12), (7) ManifestWriter assert_available_at_present guard, (8) QG static check, (9) e2e integration
  test, (10) honest-empty parquet safeguard. Audit fully detailed in body \xA7 "Audit 2026-05-08".

type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C5
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C2
    deployment: none
    business: none
  - repo: instruments-service
    code: C2
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C1
    deployment: none
    business: none
  - repo: features-sports-service
    code: C4
    deployment: none
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: none
    business: none
  - repo: features-cefi-service
    code: C0
    deployment: none
    business: none
  - repo: features-tradfi-service
    code: C0
    deployment: none
    business: none
  - repo: features-defi-service
    code: C0
    deployment: none
    business: none
  - repo: features-cross-asset-service
    code: C0
    deployment: none
    business: none

depends_on:
  - writegate-honest-coverage-endtoend-2026-05-06
  - features-repo-consolidation-2026-05-08
  - ml-and-features-master-2026-05-07
  - live-pipeline-mtds-mdps-features-2026-05-08

related:
  - defi-master-2026-05-07
  - cefi-master-2026-05-07
  - tradfi-master-2026-05-07
  - sports-master-2026-05-07
  - predictions-master-2026-05-07
  - master-to-live-defi-2026-05-23

isProject: false
---

# `available_at` + Lookahead-Bias Completion — Plan

> **Single SSOT for the end-to-end `available_at` chain.** Each chain link below is either OWNED by an existing plan (in
> which case this plan only cross-references and tracks status) or OWNED HERE directly because no other plan owns it.
> Reviewers reject any new feature/calculator/adapter work that touches `available_at` without reading this plan first.

---

## Audit 2026-05-08

- **Audit run**: 2026-05-08 (post-Tab-12-deferral, parallel-agent pass over UTL + UAC + 7 features-\* services +
  plans/active/)
- **What's solid (no action)**:
  - UTL `LookaheadBiasError`
    ([point_in_time.py:36-37](../../../unified-trading-library/unified_trading_library/point_in_time.py#L36-L37))
  - UTL `PointInTimeEnforcer(as_of, strict=True)`
    ([point_in_time.py:40-96](../../../unified-trading-library/unified_trading_library/point_in_time.py#L40-L96)) —
    operates on scalars + lists
  - UTL `assert_no_lookahead_for_feature_group(feature_group, inputs_df: pl.DataFrame, target_ts, ...)`
    ([point_in_time.py:274-393](../../../unified-trading-library/unified_trading_library/point_in_time.py#L274-L393)) —
    already takes target_ts, gracefully no-ops when feature_group absent / df empty / column missing
  - UTL `assert_available_at_present(df: pd.DataFrame)`
    ([manifest_writer.py:64-94](../../../unified-trading-library/unified_trading_library/manifest_writer.py#L64-L94)) —
    pandas, raises on missing column or null values
  - UAC `FEATURE_REQUIRED_INPUTS` SSOT exists at
    [required_inputs.py](../../../unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py)
    — 10 defi feature_groups registered
  - `ManifestWriter.record_captured()` already calls `assert_available_at_present` — chain link 7 is COVERED
  - features-sports `_enforce_pit_sports()`
    ([data/writer.py:42-72](../../../features-sports-service/features_sports_service/data/writer.py#L42-L72)) —
    production-grade, raises on first future-dated row
- **What's PARTIAL** (assumed downstream-ownership, but unowned):
  - features-onchain `feature_writer.py` imports `LookaheadBiasError` but uses `contextlib.suppress(LookaheadBiasError)`
    — landing-pad only, enforcement disabled
  - 6 other features-\* services (delta-one, cefi, tradfi, defi, cross-asset, plus future consolidated
    `features-service`) have no enforcement
  - DeFi/CeFi/TradFi/Predictions adapters lack explicit per-adapter stamping wiring per `availability_semantics`
  - UAC `FEATURE_REQUIRED_INPUTS` covers 10 of ~90 feature_groups
  - UAC `AVAILABILITY_AT_SEMANTICS` coverage not verified per (asset_group, data_type)
  - **MDPS bar timestamp + `available_at` semantics** are not explicitly owned — bars must close on UTC-midnight-aligned
    boundaries (15s / 1m / 5m / 15m / 1h / 1d), and `available_at` for a bar = the boundary-rounded-up
    last-tick-timestamp (i.e. the moment the bar closed). Today MDPS produces bars but the boundary alignment + per-bar
    `available_at` stamping is not contractual.
- **What's GAP** (no plan owns it):
  - QG static check that every `record_captured(` callsite has an `available_at` stamp on the same code path
  - E2E integration test (1-day backtest, 3 representative asset_groups, assert no silent lookahead)
  - Honest-empty parquet safeguard for non-MDPS adapters (legitimately-empty parquets with no `available_at` column
    should pass the gate)
  - Multi-asset historical backfill reconciler (sports script proven, CeFi/DeFi/TradFi/Predictions equivalent unplanned)
- **Cross-plan blockers**:
  - This plan BLOCKS `master_to_live_defi_2026_05_23` Group F trading prereqs (batch-vs-live reconciliation needs honest
    `available_at` for lookahead-free batch P&L attribution)
  - This plan BLOCKS `strategy_and_dart_master_2026_05_07` strategy-alpha measurement (per writegate audit)
  - Phase 0 (MDPS bar boundary) BLOCKS chain link 1 (adapter stamping) for MDPS-derived data_types — bars must be
    canonical before downstream stamping can stand on them
  - Chain link 1 BLOCKS chain link 6 (Tab 12 wiring) — calculator/writer enforcement is dead code until adapters stamp
  - Tab 12 (chain link 6) is OFFICIALLY DEFERRED per `cf9b9ba1` until chain link 1 ships; do not re-litigate

---

## Chain link status table

| #   | Link                                                     | Status                 | Owning plan                                                           | This plan owns?                                           |
| --- | -------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------- | --------------------------------------------------------- |
| 0   | MDPS bar boundary + per-bar `available_at` stamping      | **GAP**                | none                                                                  | **YES** — Phase 0 here                                    |
| 1   | Per-asset-group adapter stamping at write-time           | **PARTIAL** ~60%       | writegate Phase 2.D + sports_master + ml_and_features_master Phase 2A | Tracks; gap todos in Phase 1 here                         |
| 2   | Historical parquet backfill reconciler                   | **PARTIAL**            | sports_master shipped                                                 | Phase 2 here owns CeFi/DeFi/TradFi/Predictions            |
| 3   | Reader propagation (column survives parquet round-trips) | **COVERED**            | ml_and_features_master Phase 3A + gcs_migration_bundle Phase 5        | Tracks only                                               |
| 4   | UAC `FEATURE_REQUIRED_INPUTS` expansion                  | **PARTIAL** ~10 of ~90 | ml_and_features_master Phase 1A (defi only)                           | Phase 4 here owns sports/cefi/tradfi/prediction expansion |
| 5   | UAC `AVAILABILITY_AT_SEMANTICS` coverage audit           | **PARTIAL**            | writegate Phase 1B + 2.D                                              | Phase 5 here owns the audit                               |
| 6   | Calculator/writer-boundary enforcement (Tab 12)          | **PARTIAL** + DEFERRED | features_repo_consolidation Phase 5.c                                 | Tracks; resumes when chain links 0+1 ship                 |
| 7   | `ManifestWriter.assert_available_at_present` guard       | **COVERED**            | writegate Phase 1A                                                    | Tracks only                                               |
| 8   | QG static check (CI enforcement)                         | **GAP**                | none                                                                  | **YES** — Phase 8 here                                    |
| 9   | E2E integration test                                     | **GAP**                | none                                                                  | **YES** — Phase 9 here                                    |
| 10  | Honest-empty parquet safeguard for non-MDPS adapters     | **GAP**                | only MDPS Phase 2.E covers MDPS                                       | **YES** — Phase 10 here                                   |

---

## Phase 0 — MDPS bar boundary + per-bar `available_at` stamping (P0)

> **Foundational.** All downstream chain links that consume MDPS-derived data_types stand on MDPS bar timestamps. If bar
> boundaries are not UTC-midnight-aligned and `available_at` is not stamped on bar close, every adapter stamping below
> it inherits the inconsistency. **Operator directive 2026-05-08**: candle timestamps must be at the point where data
> became available — last-tick-timestamp rounded UP to the bar's boundary on even UTC midnight-aligned grid. No phase
> shift.

todos:

- [x] [SCRIPT] P0. **UAC SSOT — bar boundary contract** (shipped UAC@5240000 2026-05-11 by `ikenna-available-at-tab`).
      New module `unified_api_contracts/canonical/crosscutting/bar_boundary.py` declares the 4-clause contract:
      (1) closed-set timeframe `BAR_TIMEFRAMES = ('15s', '1m', '5m', '15m', '30m', '1h', '4h', '1d')`;
      (2) `t_close` lies on the UTC-midnight-aligned grid for the timeframe;
      (3) half-open window `[t_open, t_close)` of width `== timeframe`;
      (4) `available_at == t_close` (no leak; replay-idempotent).
      Public helpers: `BarTimeframe` Literal, `BAR_TIMEFRAME_SECONDS`, `BarBoundaryViolationError`,
      `assert_bar_boundary_contract(...)`, `bar_window_for_close(t_close, timeframe)`. Re-exported from
      `canonical/crosscutting/__init__.py` + root `unified_api_contracts` facade. 24 unit tests cover all clauses
      + tz-awareness + idempotency. status: done.

- [x] [SCRIPT] P0. **UTL helper — `compute_bar_close_boundary(last_tick_ts, timeframe) -> tuple[datetime, datetime, datetime]`**
      (shipped UTL@d798fcf3 2026-05-11 by `ikenna-available-at-tab`). Lifted boundary-rounding into
      `unified_trading_library/availability_stamping.py`. Strictly-after ceiling (tick on grid point rolls to NEXT bar
      per half-open window). Integer microsecond arithmetic vs UTC midnight — no float drift, exact for every
      supported timeframe (each divides evenly into 86400s). Round-trips through `assert_bar_boundary_contract` so
      drift is caught at helper-call site. Idempotent under replay (no `datetime.now()`). 20 unit tests covering
      strictly-after rule, every timeframe in closed set, idempotency under repeated calls, tz-aware UTC gating
      (naive + non-UTC both rejected), and no-DST-drift sanity for US spring-forward + EU fall-back. status: done.

- [ ] [SCRIPT] P0. **MDPS audit + fix — bar boundary alignment**. Walk every `MDPS` calculator that emits OHLCV or
      aggregate bars. For each: (a) verify `t_open` / `t_close` are computed via `compute_bar_close_boundary` (no inline
      rounding); (b) verify `available_at = t_close` on every emitted row; (c) reject any code path that produces a bar
      with `available_at = t_open` (early-leak), `available_at = wall_clock_now` (replay-non-idempotent), or unaligned
      boundary. Likely affected files: `mdps/engine/orchestrator.py`, `mdps/calculators/ohlcv_*.py`, `mdps/writers/*.py`
      (verify via grep at implementation time).

- [ ] [SCRIPT] P0. **Reconciler — historical MDPS parquets without `available_at` or with misaligned boundaries**. Walk
      `gs://{pid}-mdps/` parquets, for each shard with missing/wrong `available_at`: re-stamp via
      `compute_bar_close_boundary(last_observed_tick_ts_in_bar, timeframe)`. Treat malformed bars (boundary-unaligned,
      NaT timestamps) as `attempted_failed` with typed error_reason `MALFORMED_BAR_BOUNDARY`. Mirror the shape of
      `instruments-service/scripts/reconcile_expected_absence_reasons.py`.

- [ ] [SCRIPT] P0. **MDPS write-gate enforcement — bar boundary + `available_at`**. Extend
      `ManifestWriter.record_captured` validation (or MDPS-side wrapper) to reject any bar whose
      `(t_open, t_close, available_at)` triple violates the UTC-midnight-aligned + `available_at == t_close` contract.
      Typed error: `BarBoundaryViolationError`.

- [ ] [SCRIPT] P0. **QG static check — MDPS bar emission**. AST-walk MDPS calculators that write parquets. Assert: every
      bar-emitting code path calls `compute_bar_close_boundary` (or imports the UTL helper); no inline
      `pd.Timestamp.floor` / `pd.Timestamp.round` / `dt.replace(...)` patterns that bypass the SSOT. Mirror writegate
      STEP 5.64 (cluster validation static check).

---

## Phase 1 — Per-asset-group adapter stamping (P0; tracks + gap todos)

> Adapter stamping for **sports** and **partial defi-onchain** ships in upstream plans. CeFi / DeFi (non-onchain
> adapters) / TradFi / Predictions are unowned. Without per-adapter stamping, chain links 6+7 (the gates) are dead code.

todos:

- [ ] [TRACKED] P0. **TRACK — writegate Phase 2.D adapter stamping helpers shipped**. UTL `availability_stamping.py` 5
      helpers exist (`stamp_available_at_lineups` / `_event_time` / `_post_match` / `_offset` / `_explicit`).
      `assert_available_at_present` already wired into `ManifestWriter.record_captured()`. **Owned by
      `writegate_honest_coverage_endtoend_2026_05_06`** — flip when shipped.

- [ ] [TRACKED] P0. **TRACK — sports adapter stamping**. fixture_lineups, fixture_player_stats, fixture_stats,
      fixture_events, injuries, odds snapshots, weather, reference-tables — owned by `sports_master_2026_05_07` Phase
      1-2. Phase 2.C stub wiring **BLOCKED-ON amendment prerequisite**; Phase 2.D schema bumps **DEFERRED to Stage 2**.
      Flip when shipped.

- [ ] [SCRIPT] P0. **DeFi (non-onchain) adapter stamping**. Per-adapter `available_at` stamping for: DefiLlama TVL, AAVE
      lending rates, Pyth Solana price feeds (re-added 2026-05-06 for LST-yield Solana coverage), Chainlink (EVM
      oracle), staking-yield aggregators (jitoSOL / mSOL / bSOL), perp-funding adapters (Hyperliquid, Lighter, Pacifica,
      Aster). Each gets a stamping call before `record_captured`. Add as Phase-2-equivalent todos to
      `defi_master_2026_05_07` referencing this plan. **Coordinator:** this plan tracks completion; ship in
      `defi_master`.

- [x] [SCRIPT] P0. **CeFi adapter stamping**. Per-adapter `available_at` stamping for: Bybit, Binance, OKX, Deribit,
      Bitfinex, Bitget, Coinbase, Hyperliquid, Kraken, Aster — across ohlcv*\*, trades, funding_rate, perp*\*,
      options_chain, futures_chain. For tick-level: `available_at = tick_timestamp + source_priority_scrape_latency` per
      UAC `SOURCE_PRIORITY`. For bar data: depends on Phase 0 (MDPS-side stamping). Add Phase-2-equivalent todos to
      `cefi_master_2026_05_07` referencing this plan. Shipped MTDS@4a00bd5 + UAC@e197173 + UTL@29555212. Per the F2
      issue doc reshape (per-callsite at writer boundary, NOT 10 per-venue files), MTDS today routes cefi tick data
      through `PartitionedTickWriter` (not direct UTL `record_captured` callsites), so the right wiring lives at
      `engine/orchestrator.py` write-chunk time. `PartitionedTickWriter.write_chunk` now stamps
      `available_at = timestamp + emission_latency_ms_for_source(primary_source)` via
      `stamp_available_at_cefi_tick(...)` when asset_group=="cefi" and the df lacks the column. Primary source resolved
      per UAC `SOURCE_PRIORITY[("cefi", data_type)]` (Tardis = 50ms canonical CeFi tick source). Bar-data stamping still
      depends on Phase 0 MDPS bar-boundary contract. Already-stamped dfs preserved; unregistered (cefi, data_type)
      skipped silently. 5 unit tests at
      `market-tick-data-service/tests/unit/test_partitioned_writer_cefi_available_at.py`. Issue doc resolved:
      `plans/archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md`. status: done

- [ ] [SCRIPT] P0. **TradFi adapter stamping**. Per-adapter `available_at` stamping for: Databento (futures + ETFs +
      options), Polygon, Yahoo Finance (VIX 15m fallback), Barchart historical preload. CME options chain + ES.OPT
      11-cluster bundles need per-cluster `available_at` (= cluster bar close time). Add Phase-2-equivalent todos to
      `tradfi_master_2026_05_07` referencing this plan.

- [ ] [SCRIPT] P0. **Predictions lifecycle-bounded `available_at`**. Per `predictions_master_2026_05_07` Phase 2
      (BLOCKED-ON Phase 1 lifecycle ingestion shipping): each prediction-market tick must have
      `available_at = max(tick_ts, market_created_at)` and must NOT carry rows past `market_settlement_time`.
      instruments-service MARKET_LIFECYCLE writer is the gate — track + flip when ships.

- [ ] [TRACKED] P0. **TRACK — features-onchain `suppress(LookaheadBiasError)` removal**. Today landing-pad with
      enforcement disabled. Once chain link 1 ships for onchain adapters AND chain link 4 (`FEATURE_REQUIRED_INPUTS`)
      covers the relevant feature_groups, remove the `contextlib.suppress` and let it raise. Owned by
      `ml_and_features_master_2026_05_07` Phase 2A.

---

## Phase 2 — Historical parquet backfill (P1)

> Multi-asset reconciler. Sports script proven; generalize.

todos:

- [ ] [SCRIPT] P1. **Generalize `migrate_sports_available_at_column.py` → `migrate_available_at_column.py`** with
      `--asset-group {cefi|defi|tradfi|predictions|sports}`. Walks GCS parquets, for each missing `available_at`:
      re-stamp per UAC `AVAILABILITY_AT_SEMANTICS` rule. Honest-empty parquets pass through (Phase 10 safeguard). Output
      CSV audit + RECONCILER\_\* events. Default scan-only; `--apply` requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`
      per workspace concurrency rule.

- [ ] [SCRIPT] P1. **Per-asset-group reconciler runs**. After Phase 1 ships per asset_group, run the reconciler
      scan-mode → review CSV → apply-mode on a same-region GCE VM. Order: sports (already done) → tradfi → cefi → defi →
      predictions.

---

## Phase 3 — Reader propagation (TRACKED, no action here)

todos:

- [ ] [TRACKED] P1. **TRACK — reader column propagation**. `available_at` survives every parquet round-trip; no reader
      drops it. Owned by `ml_and_features_master_2026_05_07` Phase 3A + `gcs_migration_bundle_pipeline_mode_2026_05_08`
      Phase 5. Flip when both ship.

---

## Phase 4 — UAC `FEATURE_REQUIRED_INPUTS` expansion (P0)

> Today: 10 defi feature_groups. Target: ~90 across all asset_groups. Each missing feature_group makes
> `assert_no_lookahead_for_feature_group` silently no-op for that group.

todos:

- [ ] [SCRIPT] P0. **Sports feature_groups → UAC**. ~60 sports feature_groups (form, league_strength, fixture_xg,
      lineup_quality, market_consensus, etc.) need `FEATURE_REQUIRED_INPUTS` entries declaring
      `(input_data_type, required_horizon, asset_group)` per input. Source-of-truth:
      `features-sports-service/features_sports_service/calculators/` calculator metadata. Add as Phase-1-equivalent todo
      to `sports_master_2026_05_07` OR ship here directly.

- [ ] [SCRIPT] P0. **CeFi feature_groups → UAC**. ~5 cefi feature_groups (volatility, liquidity, microstructure,
      perp_basis, options_iv). Add to `cefi_master_2026_05_07` OR here.

- [ ] [SCRIPT] P0. **TradFi feature_groups → UAC**. ~8 tradfi feature_groups (term_structure, butterfly,
      calendar_spread, vix_basis, etc.). Add to `tradfi_master_2026_05_07` OR here.

- [ ] [SCRIPT] P0. **Predictions feature_groups → UAC**. Per-canonical_question_group + per-binary-outcome features. Add
      to `predictions_master_2026_05_07` OR here.

- [ ] [SCRIPT] P0. **DeFi non-defi-yield feature_groups → UAC**. The 10 currently-registered cover defi yields;
      cross-protocol carry, bridge-flow, MEV-leakage, gas-fee bands etc. likely need additions. Audit
      `features-defi-service/` + `features-onchain-service/` calculators.

---

## Phase 5 — UAC `AVAILABILITY_AT_SEMANTICS` coverage audit (P1)

todos:

- [ ] [SCRIPT] P1. **Audit `AVAILABILITY_AT_SEMANTICS` coverage**. Grep every `record_captured` callsite across the
      workspace. Extract `(asset_group, data_type)` pairs. For each pair, verify entry exists in UAC
      `availability_semantics.py` registry. Output: list of (asset_group, data_type) pairs with no entry → fix-list
      ticket per pair. Estimated 2-4h spike on a workspace-clone.

- [ ] [SCRIPT] P1. **Add missing entries**. For each pair from the audit, add an `AvailabilitySemantic` literal + entry
      to the registry. Sports + writegate Phase 2.D-A-E already cover some; close the residual gap.

---

## Phase 6 — Calculator/writer-boundary enforcement (Tab 12) — DEFERRED (TRACKED)

todos:

- [ ] [TRACKED] P0. **TRACK — Tab 12 deferral status**. Officially deferred per PM@cf9b9ba1 —
      features_repo_consolidation Phase 5.c will lift `LookaheadBiasError` gate into UTL once chain links 0+1 ship.
      Resume Tab 12 wiring (8 services) at writer boundary (mirroring features-sports `_enforce_pit_sports`), NOT
      calculator boundary (avoids pd↔pl gymnastics). Flip when chain links 0+1 cleared AND features_repo_consolidation
      Phase 5.c ships.

- [ ] [SCRIPT] P0. **features-onchain `suppress()` removal**. Single-line edit at
      `features-onchain-service/features_onchain_service/app/core/feature_writer.py` once chain link 1 ships for onchain
      adapters. Replace `with contextlib.suppress(LookaheadBiasError):` with direct call; let it raise. Verifies the
      gate is live.

---

## Phase 7 — `assert_available_at_present` (TRACKED, no action)

todos:

- [ ] [TRACKED] P0. **TRACK — `ManifestWriter.record_captured` calls `assert_available_at_present`**. Already shipped in
      writegate Phase 1A. Fires only when adapters stamp (i.e. dependent on Phase 1 here). Flip on writegate Phase 1A
      close.

---

## Phase 8 — QG static check (P2)

todos:

- [ ] [SCRIPT] P2. **`quality-gates.sh` STEP 5.67 — `record_captured` must be preceded by stamping**. AST-walk every
      `record_captured(` callsite across the workspace. Assert: on the same code path, a stamping helper call
      (`stamp_available_at_*` OR `compute_bar_close_boundary` for bars) precedes it. Mirror writegate STEP 5.64 (cluster
      validation static check). Fail-loud at CI; no warnings.

- [ ] [SCRIPT] P2. **`quality-gates.sh` STEP 5.68 — feature-compute callsites must call
      `assert_no_lookahead_for_feature_group`**. AST-walk every `record_captured(` in features-\* services (or
      post-consolidation, the consolidated `features-service`). Assert: writer-boundary call precedes the record. Pairs
      with Phase 6 above.

---

## Phase 9 — E2E integration test (P1)

todos:

- [ ] [SCRIPT] P1. **E2E lookahead-free backtest test**. 1-day window, 3 representative asset_groups (sports + cefi +
      tradfi). Run full pipeline: instruments → MTDS → MDPS → features-\* → writer-boundary enforcement. Assert: zero
      `LookaheadBiasError` raises in normal path; injected lookahead (manually shifted `available_at` past target_ts)
      raises within first 100 rows. Fold into writegate Phase 5 ratchet as mandatory acceptance gate.

---

## Phase 10 — Honest-empty parquet safeguard (P1)

todos:

- [ ] [SCRIPT] P1. **Generalize MDPS Phase 2.E A/B/C/D empty-output decision to all adapters**. Today only MDPS
      distinguishes legitimately-empty (record_empty + reason) from missing (record_failed). Other adapters' reaction to
      "source returned 0 rows" is unwired. UTL helper
      `classify_empty_response(asset_group, data_type, rows, expected) -> EmptyDecision` lifts the logic. Each adapter
      calls it before write.

- [ ] [SCRIPT] P1. **`assert_available_at_present` exception for legitimately-empty parquets**. Today the guard raises
      if column missing OR any null. For empty parquets (zero rows), the column-presence check should be skipped (no
      rows, no available_at to check) — but the column must still be declared in the schema so downstream readers don't
      fail. Add: `if df.empty and "available_at" not in df.columns: log_warning(); return` to
      `assert_available_at_present`. Coordinate with writegate Phase 1A owner.

---

## Cross-plan coordination banners

This plan is a **coordinator**. Banners must be added to:

- [ ] [SCRIPT] P0. **Banner — `defi_master_2026_05_07`**. Top-of-file:
      `> 🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping owned coordinated by available_at_lookahead_bias_completion_2026_05_08 Phase 1. Re-verify per-DeFi-adapter stamping wiring before adding new defi adapters.`
- [ ] [SCRIPT] P0. **Banner — `cefi_master_2026_05_07`**. Same shape, Phase 1 reference.
- [ ] [SCRIPT] P0. **Banner — `tradfi_master_2026_05_07`**. Same shape, Phase 1 reference.
- [ ] [SCRIPT] P0. **Banner — `predictions_master_2026_05_07`**. Phase 1 + lifecycle-bounded clip.
- [ ] [SCRIPT] P0. **Banner — `sports_master_2026_05_07`**. Phase 1 partial-shipped pointer + Phase 4 expansion pointer.
- [ ] [SCRIPT] P0. **Banner — `ml_and_features_master_2026_05_07`**. Tab 12 (Phase 6) + FEATURE_REQUIRED_INPUTS
      expansion (Phase 4) reference.
- [ ] [SCRIPT] P0. **Banner — `features_repo_consolidation_2026_05_08`**. Tab 12 wiring (Phase 5.c) sequenced after this
      plan's Phase 0+1.
- [ ] [SCRIPT] P0. **Banner — `live_pipeline_mtds_mdps_features_2026_05_08`**. MDPS bar boundary contract (Phase 0 here)
      is foundational.
- [ ] [SCRIPT] P0. **Banner — `master_to_live_defi_2026_05_23`**. Group F batch-vs-live reconciliation needs honest
      `available_at` — this plan unblocks.

---

## Deferred work after 2026-05-11 ikenna-available-at-tab session

The 2026-05-11 `ikenna-available-at-tab` session shipped Phase 0.1 (UAC bar_boundary SSOT — UAC@5240000) + Phase 0.2
(UTL `compute_bar_close_boundary` helper — UTL@d798fcf3). Items still open are tracked here so the next agent picks
up cleanly without re-reading session notes.

| Phase / item                                             | Status as of 2026-05-11                                      | Successor / blocker                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0.1 — UAC bar_boundary SSOT                        | `done` (UAC@5240000 shipped)                                 | —                                                                                                                                                                                                                                                                                                         |
| Phase 0.2 — UTL `compute_bar_close_boundary` helper      | `done` (UTL@d798fcf3 shipped)                                | —                                                                                                                                                                                                                                                                                                         |
| Phase 0.3 — MDPS audit + fix (bar boundary alignment)    | `todo` (checkbox `- [ ]`)                                    | DEFERRED-AFTER-`features_repo_consolidation_2026_05_08.md` Phase 7 (consolidated features-service deployable) AND `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4-5 (MDPS streaming aggregator design) — both gate MDPS calculator rework. Harsh slot 4 to pick up per-adapter wiring once unblocked. |
| Phase 0.4 — Historical MDPS parquet reconciler           | `todo` (checkbox `- [ ]`)                                    | DEFERRED-AFTER-Phase 0.3 (need fixed MDPS first so reconciler stamps via the same UTL helper).                                                                                                                                                                                                            |
| Phase 0.5 — MDPS write-gate enforcement                  | `todo` (checkbox `- [ ]`)                                    | DEFERRED-AFTER-Phase 0.3. `BarBoundaryViolationError` is already importable from UAC; wiring lives at MDPS `ManifestWriter.record_captured` invocation in the orchestrator path. The validator (`assert_bar_boundary_contract`) is the gate primitive.                                                    |
| Phase 0.6 — QG static check for MDPS bar emission        | `todo` (checkbox `- [ ]`)                                    | DEFERRED-AFTER-Phase 0.3. Mirrors writegate STEP 5.64 AST-walk: every bar-emitting code path must call `compute_bar_close_boundary` (or import the UTL helper); ban inline `pd.Timestamp.floor` / `dt.replace(...)` bypasses.                                                                              |
| Phase 1 (DeFi / TradFi / Predictions adapter stamping)   | `todo` (checkbox `- [ ]` × 3)                                | Owned by respective asset_group master plans (defi_master / tradfi_master / predictions_master). Harsh slot 4 picks up per-adapter wiring once Phase 0 lands at MDPS level.                                                                                                                              |
| Phase 4 — FEATURE_REQUIRED_INPUTS expansion              | `todo` (checkbox `- [ ]` × 5)                                | This session's next work item; tracked in slot 3 todo list.                                                                                                                                                                                                                                              |
| Phase 5 — AVAILABILITY_AT_SEMANTICS workspace-wide audit | `todo` (checkbox `- [ ]` × 2)                                | This session's next work item; tracked in slot 3 todo list.                                                                                                                                                                                                                                              |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **MDPS streaming aggregator design** (consumes Phase 0.1/0.2 contract): open in
  [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4. Ikenna
  slot 4 owns the design-ahead this cycle.
- **Per-adapter `available_at` stamping wiring (CeFi tick / TradFi / Predictions / DeFi)**: Harsh slot 4 scope. Cross-side
  ping landed in `plans/active/_agent_pings.md` on Phase 0.1/0.2 close so Harsh slot 4 unblocks.
- **features-onchain `suppress(LookaheadBiasError)` removal**: open in `ml_and_features_master_2026_05_07` Phase 2A; gated
  on chain link 1 (per-adapter stamping) shipping for onchain adapters.

---

## Temporary states + their canonical follow-up plans

- **UAC `FEATURE_REQUIRED_INPUTS` registers 10 of ~90 feature_groups.** Successor: Phase 4 of THIS plan
  (cross-asset-group expansion).
- **features-onchain `feature_writer.py` uses `contextlib.suppress(LookaheadBiasError)`.** Successor: Phase 6 of THIS
  plan (suppress() removal once chain links 0+1 ship).
- **MDPS bar boundary alignment is convention, not contract.** Successor: Phase 0 of THIS plan; UAC + UTL halves shipped
  2026-05-11 (UAC@5240000 + UTL@d798fcf3); MDPS-side audit + reconciler + write-gate + QG check open per the
  deferred-work scoreboard above.
- **`AVAILABILITY_AT_SEMANTICS` registry coverage not audited per (asset_group, data_type).** Successor: Phase 5 of THIS
  plan.

---

## Success criteria

- **C5 across all repos in `repo_gates`**: every `record_captured` callsite stamps `available_at` per UAC SSOT; QG STEP
  5.67 enforces statically; e2e test passes.
- **D2 (CI smoke)**: full features-\* pipeline computes feature rows for 1-day window with strict-mode
  `LookaheadBiasError` enabled; zero raises; injected lookahead raises within first 100 rows.
- **B-gates**: none (infrastructure plan; downstream business plans gate on this).

---

## Notes for executing agents

- **Phase 0 is foundational.** Do not start Phase 1 work for MDPS-derived data_types until Phase 0 ships.
- **Phase 6 (Tab 12) is officially deferred — do not re-litigate.** PM@cf9b9ba1 closed this. Resume only after Phase 0+1
  ship.
- **Adapter stamping wires belong at the WRITER boundary**, not the calculator boundary. features-sports
  `_enforce_pit_sports` is the canonical precedent; mirror its shape. Avoids the pd↔pl conversion that motivated Tab
  12's pd|pl lift discussion.
- **`assert_no_lookahead_for_feature_group` already takes `pl.DataFrame` + `target_ts`** — both are in scope at the
  writer boundary. No UTL contract change needed.
- **Cross-plan coordination banners** are part of every plan-touch in this epic; add them as you go.

---

## DONE-2026-05-10 — mtds-utl-completion-tab session

| Item                                                            | Status                        | Commits                                                                             |
| --------------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------- |
| Phase 1 P0 — CeFi adapter stamping                              | `done` (writer-boundary path) | market-tick-data-service@4a00bd5 (writer stamping + 5 tests); plan-flip PM@2372071b |
| F2 issue doc resolution (cefi_available_at structural mismatch) | `done`                        | PM@2372071b (resolved-banner added at top of issue doc)                             |

This session shipped the cefi half of Phase 1 P0; DeFi/TradFi/Predictions/Sports adapter stamping items in Phase 1
remain `- [ ]`. Phases 0/2/4/5/6/7/8/9/10 untouched this session.

## Audit-2026-05-10 finding — post-cutover Phase: lift `available_at` to schema-level invariant

**Source**:
[`plans/archive/issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md`](../archive/issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md)

- sibling [`block_b_audit_findings`](../archive/issues/codex_vs_citadel_block_b_audit_findings_2026_05_10.md) Block B5.

**Finding**: today's two-layer enforcement is (1) opt-in stamping helpers in
[`unified_trading_library/availability_stamping.py`](../../../unified-trading-library/unified_trading_library/availability_stamping.py)
(330 lines) + (2) runtime gate `manifest_writer.assert_available_at_present` (line 72) that raises `LookaheadBiasError`
for missing/null. **Gap**: gate catches missing-stamp at write time, not at row-construction time; **worse**, an adapter
that stamps with the WRONG rule (e.g. `event_time` for a post-match stat that should use `match_end_time`) never fails —
silent lookahead bias. This is the single highest-priority Block-B item per the audit (direct alpha-relevance — every
minute of lookahead = phantom alpha).

**Recommended post-cutover Phase to file** (NEW phase under this plan, post-May-23):

- [ ] [SCRIPT] P1. **NEW** UAC `availability_rule.py` — `AvailabilityRule` Protocol + per-source implementations lifted
      from `availability_stamping.py`.
- [ ] [SCRIPT] P1. **NEW** row base class in UAC requires `available_at: datetime` field; pydantic validator on every
      row class invokes the row's source's `AvailabilityRule.stamp(row)` automatically.
- [ ] [SCRIPT] P1. **MIGRATE** per-source row classes inherit from the base; `stamp_available_at_*` opt-in helpers
      become unnecessary (auto-applied via validator).
- [ ] [SCRIPT] P1. **DELETE** 330 lines of `availability_stamping.py` collapse to ~50 lines (per-source rule impls
      only).
- [ ] [SCRIPT] P1. **REDUCE** cross-referenced CLAUDE.md + codex doc surface for `available_at` rules collapses to one
      canonical UAC reference.

**Cost**: ~2-3 AI-days. **Saved cost**: lookahead-bias incident class becomes type-level unrepresentable; ~1 week of
fire-fight per surfaced incident saved. **Composes with**: Block B1 ADT lift (the `Captured(...)` ADT variant takes a
row collection that's already stamped) + monorepo migration (Block A1 DECIDED-YES). Timing: post-cutover; ride with
those structural changes as one architectural slice.

**Plan status**: this annotation is FYI for plan owner — NEW phase not yet wired into the phased DAG above. Plan owner
decides whether to fold into Phase 11+ here OR file standalone post-cutover.
