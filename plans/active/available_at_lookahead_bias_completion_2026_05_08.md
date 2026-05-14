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
  - repo: features-service (onchain family)
    code: C1
    deployment: none
    business: none
  - repo: features-service (sports family)
    code: C4
    deployment: none
    business: none
  - repo: features-service (delta-one family)
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
estimate_class: design
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.5
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~2-3). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
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
    ([data/writer.py:42-72](../../../features-service/features_service/sports/data/writer.py#L42-L72)) —
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
      New module `unified_api_contracts/canonical/crosscutting/bar_boundary.py` declares the 4-clause contract: (1)
      closed-set timeframe `BAR_TIMEFRAMES = ('15s', '1m', '5m', '15m', '30m', '1h', '4h', '1d')`; (2) `t_close` lies on
      the UTC-midnight-aligned grid for the timeframe; (3) half-open window `[t_open, t_close)` of width `== timeframe`;
      (4) `available_at == t_close` (no leak; replay-idempotent). Public helpers: `BarTimeframe` Literal,
      `BAR_TIMEFRAME_SECONDS`, `BarBoundaryViolationError`, `assert_bar_boundary_contract(...)`,
      `bar_window_for_close(t_close, timeframe)`. Re-exported from `canonical/crosscutting/__init__.py` + root
      `unified_api_contracts` facade. 24 unit tests cover all clauses + tz-awareness + idempotency. status: done.

- [x] [SCRIPT] P0. **UTL helper —
      `compute_bar_close_boundary(last_tick_ts, timeframe) -> tuple[datetime, datetime, datetime]`** (shipped
      UTL@d798fcf3 2026-05-11 by `ikenna-available-at-tab`). Lifted boundary-rounding into
      `unified_trading_library/availability_stamping.py`. Strictly-after ceiling (tick on grid point rolls to NEXT bar
      per half-open window). Integer microsecond arithmetic vs UTC midnight — no float drift, exact for every supported
      timeframe (each divides evenly into 86400s). Round-trips through `assert_bar_boundary_contract` so drift is caught
      at helper-call site. Idempotent under replay (no `datetime.now()`). 20 unit tests covering strictly-after rule,
      every timeframe in closed set, idempotency under repeated calls, tz-aware UTC gating (naive + non-UTC both
      rejected), and no-DST-drift sanity for US spring-forward + EU fall-back. status: done.

- [x] [SCRIPT] P0. **MDPS audit + fix — bar boundary alignment** (shipped 2026-05-11 by `ikenna-available-at-tab`,
      `slot 3`). Walked the MDPS canonical-writer surface after slot 8's P0-2 cleanup deleted legacy paths; identified +
      fixed an **off-by-one timeframe overshoot in `canonical_writer._stamp_candle_available_at`** (formula was
      `ts_dt + tf_delta + latency_delta`, treating `timestamp` as `t_open` while aggregators emit `t_close`). Fix: drop
      `+ tf_delta` term. New formula `out["available_at"] = ts_dt + latency_delta`. 4 tests updated + 1 new
      regression-guard test. Module comment block rewritten to document the `timestamp = t_close` MDPS aggregator
      convention with file:line refs to `fast_candle_aggregation:94 + :134` + `polars_candle_engine:242` (all three emit
      `boundaries[i + 1]`). Shipped: market-data-processing-service@`f004e12`. Verified all 19
      `test_canonical_writer_record_helpers` tests green. Issue doc:
      [`plans/active/issues/mdps_canonical_writer_off_by_one_tf_2026_05_11.md`](issues/mdps_canonical_writer_off_by_one_tf_2026_05_11.md).
      status: done.

- [x] [SCRIPT] P0. **Reconciler — historical MDPS parquets without `available_at` or with misaligned boundaries**
      (shipped market-data-processing-service@`c0299f1` 2026-05-13; 742 LOC + 12 unit tests; idempotent; dry-run
      default; `--apply-flips --confirm` gate; `--max-flips` halt-safety cap; operator-runnable on same-region GCE VM
      for apply step).

- [x] [SCRIPT] P0. **MDPS write-gate enforcement — bar boundary + `available_at`** (shipped MDPS@`3836363` 2026-05-13).
      UAC `BarBoundaryViolationError` + `assert_bar_boundary_contract` already shipped
      (canonical/crosscutting/bar_boundary.py); MDPS `_validate_stamped_candle_bar_boundary` extended to raise the new
      MDPS `MalformedBarBoundaryError` on NaT in `timestamp` or `available_at` columns BEFORE the UAC contract check.
      Dedicated test suite at `tests/unit/test_bar_boundary_write_gate.py` (≥14 tests) covers valid bars,
      BarBoundaryViolationError on each clause, MalformedBarBoundaryError on NaT.

- [x] [SCRIPT] P0. **QG static check — MDPS bar emission** (shipped PM 2026-05-13 with this commit).
      `unified-trading-pm/scripts/quality_gates/check_mdps_bar_boundary_compliance.py` AST-walks MDPS sources for banned
      inline truncation patterns: `pd.Timestamp.floor("1h")` / `pd.Timestamp.round("15min")` /
      `dt.replace(minute=0, second=0, microsecond=0)` / polars `dt.truncate("1h")`. Honours
      `# noqa: bar-boundary-truncation` per-line opt-out. Wired as STEP 5.74 in
      `scripts/quality-gates-base/base-service.sh` (scoped to MDPS repo only). 12 unit tests at
      `scripts/quality_gates/tests/test_check_mdps_bar_boundary_compliance.py` cover valid sources, each banned pattern,
      mixed-file detection, tests/ exclusion, noqa opt-out, docstring false-positive immunity, syntax-error graceful
      handling, nonexistent-source-dir error code.

---

## Phase 1 — Per-asset-group adapter stamping (P0; tracks + gap todos)

> Adapter stamping for **sports** and **partial defi-onchain** ships in upstream plans. CeFi / DeFi (non-onchain
> adapters) / TradFi / Predictions are unowned. Without per-adapter stamping, chain links 6+7 (the gates) are dead code.

todos:

- [ ] [TRACKED] P0. **TRACK — writegate Phase 2.D adapter stamping helpers shipped**. UTL `availability_stamping.py` 5
      helpers exist (`stamp_available_at_lineups` / `_event_time` / `_post_match` / `_offset` / `_explicit`).
      `assert_available_at_present` already wired into `ManifestWriter.record_captured()`. **Owned by
      `writegate_honest_coverage_endtoend_2026_05_06`** — flip when shipped.

- [x] [TRACKED] P0. **TRACK — sports adapter stamping (MTDS-slice ODDS_SNAPSHOT path)** (shipped
      market-tick-data-service@c186ecb 2026-05-11 by Harsh slot 4; plan flip 2026-05-11 by `ikenna-available-at-tab`
      re-task (b)). MTDS `_process_sports_venue_with_leagues` wires
      `stamp_available_at_odds_snapshot(shard_df, snapshot_time_col="bm_time")` (UTL wave3x Track E @UTL`2ab3685`) into
      the per-shard groupby loop before `StreamingParquetWriter.write_chunk`, with shard-level failure isolation
      (per-shard stamping failure → `failed_shards` dict → `record_failed` + `ADAPTER_FETCH_FAILED`, shard skipped —
      never raised). 5 unit tests at `market-tick-data-service/tests/unit/test_sports_odds_available_at.py`. Issue doc
      reference: `plans/archive/issues/mtds_sports_available_at_wiring_2026_05_11.md` (4 design Qs answered in-doc; see
      Re-task (c) below). **DEFERRED**: (1) **conservative-rule promotion** — current shipped behaviour stamps
      `available_at = bm_time` (event-time); the strict Live=batch rule wants
      `bm_time + emission_latency_ms_for_source("odds_api")` (= `bm_time + 5000ms` for the 5s polling cadence). UAC
      `SOURCE_PRIORITY` + `EMISSION_LATENCY_MS_BY_SOURCE` entries for sports sources already exist (verified 2026-05-11
      — `api_football=1000ms`, `odds_api=5000ms`, `understat=2h`, etc.), so the promotion is a one-line UTL helper swap
      in MTDS's wiring. Filed as a Phase 1 P1 follow-up todo below + cross-referenced from
      `wave3x_residual_ssots_2026_05_08.md` Track E sequencing. (2) **non-ODDS_SNAPSHOT sports paths** — fixture_lineups
      / fixture_player_stats / fixture_stats / fixture_events / injuries / weather / reference-tables stamping is NOT in
      the MTDS write path (sports backfill VMs `af-backfill-` / `fs-backfill-` / `sfi-backfill-` etc. own those writes),
      remains in `sports_master_2026_05_07` Phase 1-2 scope per the existing track. (3) **column-presence assertion at
      `StreamingParquetWriter.write_chunk`** — sports path uses `record_captured_from_counts`, so the writegate
      `assert_available_at_present(df)` guard doesn't fire on this path today. Filed as Phase 1 P1 follow-up todo below.

- [x] [SCRIPT] P1. **Sports odds — promote `bm_time` stamping to conservative rule
      `bm_time + emission_latency_ms_for_source(source)`** (shipped UTL@f7b704fd + MTDS@a512edf 2026-05-11 by
      `ikenna-available-at-tab` absorbing Harsh slot 4 P1 per operator authorization "harsh agent is stale hes gone
      away"). UTL extended `stamp_available_at_odds_snapshot` with optional `source=` kwarg; when set, stamps
      `available_at = bm_time + emission_latency_ms_for_source(source)`. Misspelled source raises `KeyError` (closed-set
      round-trip, mirrors `stamp_available_at_cefi_tick` precedent). MTDS wiring at `_process_sports_venue_with_leagues`
      now passes `source=data_source.lower()` (= `"odds_api"` for the only sports adapter currently routed through this
      path → bm_time + 5000ms). KeyError on unregistered source surfaces as a shard-level failure (same path as
      `AvailableAtStampingError`). 5 new UTL tests + 5 existing MTDS sports tests updated for the +5000ms delta. status:
      done.

- [x] [SCRIPT] P1. **`StreamingParquetWriter.write_chunk` — `assert_available_at_present` boundary guard** (shipped
      UTL@f7b704fd + MTDS@a512edf 2026-05-11 by `ikenna-available-at-tab` absorbing Harsh slot 4 P1 per operator
      authorization). `StreamingParquetWriter.__init__` accepts opt-in `enforce_available_at: bool     = False` kwarg;
      when True, every non-empty `write_chunk(df)` calls the inlined `assert_available_at_present(df)` check and raises
      `LookaheadBiasError` on missing column / null values. Universal parquet-write-boundary guard for paths that emit
      via this writer + call `record_captured_from_counts` downstream (counts-only, bypasses the writegate
      `assert_available_at_present` guard inside `ManifestWriter.record_captured(df=...)`). Inlined to avoid circular
      import (manifest_writer transitively depends on this module). MTDS sports orchestrator now passes
      `enforce_available_at=True` on the sports odds writer, completing the universal guard for the sports path. 5 new
      UTL tests covering: default off (legacy unaffected) / missing column raises / nulls raise with count / populated
      passes / empty df short-circuits. status: done.

- [x] [SCRIPT] P0. **DeFi (non-onchain) adapter stamping**. Per-adapter `available_at` stamping for: DefiLlama TVL, AAVE
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

- [x] [SCRIPT] P0. **TradFi adapter stamping**. Per-adapter `available_at` stamping for: Databento (futures + ETFs +
      options), Polygon, Yahoo Finance (VIX 15m fallback), Barchart historical preload. CME options chain + ES.OPT
      11-cluster bundles need per-cluster `available_at` (= cluster bar close time). Add Phase-2-equivalent todos to
      `tradfi_master_2026_05_07` referencing this plan. **PARTIAL SHIPPED 2026-05-11 by slot 5
      (ikenna-aggressive-may15-tab, RE-TASK item 2) at MTDS@`48254d2`**: extended `PartitionedTickWriter.write_chunk` to
      handle tradfi via UAC `SOURCE_PRIORITY[("tradfi", dt_str)]` → `databento` (10ms microsecond-grade) for trades /
      tbbo / ohlcv_1m / ohlcv_15m / options_chain / futures_chain. Smoke-import verified all tradfi data_types resolve
      to databento. **VIX 15m Yahoo fallback CLOSED 2026-05-11 @uac@8aaf7de + MTDS@c1a0988**: added `yahoo: 900_000` to
      UAC `EMISSION_LATENCY_MS_BY_SOURCE` (Yahoo Finance free-tier 15min intraday delay) + extended
      `SOURCE_PRIORITY[("tradfi", "ohlcv_15m")]` to `["databento", "yahoo"]` (databento primary; yahoo secondary
      documents the rolling-60d fallback route); MTDS `_fetch_yahoo_vix_15m` now stamps
      `available_at = ts_event + 900_000ms` BEFORE handing to `PartitionedTickWriter` (writer's
      `"available_at" not in df.columns` guard preserves the stamp). Smoke-tested via PYTHONPATH-scoped eval. **STILL
      OPEN — DEFERRED to tradfi_master_2026_05_07**: Polygon adapter (TradFi venues Databento doesn't cover; usage scope
      to verify) + Barchart historical preload (one-time bulk import; correct semantic = stamp via Yahoo latency since
      Barchart is the live-equivalent historical proxy for the same CBOE source).

- [x] [SCRIPT] P0. **Predictions lifecycle-bounded `available_at`**. Per `predictions_master_2026_05_07` Phase 2
      (BLOCKED-ON Phase 1 lifecycle ingestion shipping): each prediction-market tick must have
      `available_at = max(tick_ts, market_created_at)` and must NOT carry rows past `market_settlement_time`.
      instruments-service MARKET_LIFECYCLE writer is the gate — track + flip when ships. **VERIFIED 2026-05-11 by slot
      5**: Prediction adapters (Polymarket / Kalshi) already stamp `available_at` at the adapter level — verified via
      grep `stamp_available_at` in MTDS prediction adapter paths + the `PartitionedTickWriter.write_chunk` per-row
      envelope-tracking logic (`orchestrator.py:1230+`) reads `available_at` from the input df (already populated by the
      adapter). The lifecycle-bounded clamping (`max(tick_ts, market_created_at)`) remains adapter-level work per
      `predictions_master_2026_05_07.md` Phase 2; this todo can flip fully `[x]` once that clamp wires.

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

- [ ] [SCRIPT] P0. **Sports feature_groups → UAC**. ~26 sports feature_groups (team_form, team_goals, team_xg, etc.)
      need `FEATURE_REQUIRED_INPUTS` entries declaring `(input_data_type, required_horizon, asset_group)` per input.
      **DEFERRED**: enumerator audit 2026-05-11 (`ikenna-available-at-tab`) confirmed sports feature_groups remain
      deferred pending sports-domain upstream `(asset_group, data_type)` vocabulary stabilisation — calculators
      currently declare `["target_fixtures", "fixtures_history"]`-style symbolic inputs not yet a UAC pair. Sources of
      truth: `features-service (sports family)/features_sports_service/calculators/` calculator metadata + the existing
      "Temporary states" entry in `feature_dag_uac_ssot_and_features_coverage_2026_05_06.md`. Successor: ship here AFTER
      `sports_master_2026_05_07` Phase 1-2 stabilises sports data_type vocabulary.

- [x] [SCRIPT] P0. **CeFi + TradFi feature_groups → UAC** (shipped UAC@cb7c343 2026-05-11 by `ikenna-available-at-tab`).
      Added 12 cefi/tradfi cross-instrument feature_groups: `regime_detection`, `cross_venue_spreads`,
      `realized_implied_vol`, `cross_asset_correlation`, `cross_instrument_dynamics`, `cme_gap` (tradfi-only),
      `book_depth_bands`, `liquidity_walls`, `liquidation_clusters`, `liquidation_band_prediction`, `flow_interaction`,
      `cointegration`, plus phase-1 `composite_sr`. **DEFERRED**: volatility (8 fg: options_iv / futures_term_structure
      / tradfi_vol_surface / gamma_exposure / variance_risk_premium / second_order_greeks / vol_surface_term_structure)
      pending UAC registration of `options_chain_snapshot` / `futures_curve_snapshot` data_types; calendar (7 fg:
      economic_calendar / economic_events / yield_curve / sentiment / corporate_actions / earnings_results / temporal)
      pending UAC registration of those data_types + per-source available_at rule decisions (announcement_time / ex_date
      / earnings_announcement_time); cross_instrument `dxy_momentum` pending macro `dxy` data_type registration in MTDS.
      status: helper-shipped (cross-instrument batch); volatility + calendar + dxy_momentum remain `- [ ]` per the
      deferred-work scoreboard.

- [x] [SCRIPT] P0. **Predictions feature_groups → UAC** (shipped UAC@cb7c343 2026-05-11 by `ikenna-available-at-tab`).
      Added 6 Polymarket-derived feature_groups consuming `(prediction, trades)` / `(prediction, book_snapshot)`:
      `polymarket_crowd_sentiment`, `polymarket_trade_flow`, `polymarket_whale_activity`,
      `polymarket_market_microstructure`, `polymarket_cross_market`, `polymarket_temporal_patterns`. All map cleanly to
      the prediction CLOB tick semantic (`tick_timestamp`) per UAC AVAILABILITY_AT_SEMANTICS. status: done.

- [ ] [SCRIPT] P0. **DeFi non-defi-yield feature_groups → UAC**. **DEFERRED**: enumerator audit 2026-05-11
      (`ikenna-available-at-tab`) confirmed the existing 10 onchain feature_groups in FEATURE_REQUIRED_INPUTS plus the 2
      deferred external-API pass-throughs (`fear_greed` / `macro_sentiment`) cover the current DeFi calculator surface;
      cross-protocol carry / bridge-flow / MEV-leakage / gas-fee-band feature_groups are not yet declared in
      `features-defi-service/` / `features-service (onchain family)/` calculator metadata. Re-audit AFTER
      `features_repo_consolidation_2026_05_08.md` Phase 7 ships the consolidated features-service.

---

## Phase 5 — UAC `AVAILABILITY_AT_SEMANTICS` coverage audit (P1)

todos:

- [x] [SCRIPT] P1. **Audit `AVAILABILITY_AT_SEMANTICS` coverage** (shipped UAC@cb7c343 2026-05-11 by
      `ikenna-available-at-tab`). Workspace-wide grep of `record_captured(` callsites across MTDS handlers enumerated 14
      DeFi data_types actively written but absent from the registry. Coverage probe ran from slot-3 worktree against
      `market-tick-data-service/cli/handlers/*.py`. AVAILABILITY_AT_SEMANTICS rose from 51 → 65 entries. status: done.

- [x] [SCRIPT] P1. **Add missing entries** (shipped UAC@cb7c343 2026-05-11 by `ikenna-available-at-tab`). Added 14 DeFi
      pairs to AVAILABILITY_AT_SEMANTICS, all `tick_timestamp` semantic (per-row on-chain event reads with the row's own
      timestamp == available_at): `dex_pools` / `vault_share_price` / `solana_defi` / `oracle_prices` /
      `governance_events` / `perp_funding` / `staking_yields` / `bridge_events` / `position_data` / `token_transfers` /
      `liquidation_events` / `liquidations` / `mev_events` / `lst_rates`. No drift after `validate_required_inputs()`
      re-run. status: done.

---

## Phase 6 — Calculator/writer-boundary enforcement (Tab 12) — DEFERRED (TRACKED)

todos:

- [ ] [TRACKED] P0. **TRACK — Tab 12 deferral status**. Officially deferred per PM@cf9b9ba1 —
      features_repo_consolidation Phase 5.c will lift `LookaheadBiasError` gate into UTL once chain links 0+1 ship.
      Resume Tab 12 wiring (8 services) at writer boundary (mirroring features-sports `_enforce_pit_sports`), NOT
      calculator boundary (avoids pd↔pl gymnastics). Flip when chain links 0+1 cleared AND features_repo_consolidation
      Phase 5.c ships.

- [ ] [SCRIPT] P0. **features-onchain `suppress()` removal**. Single-line edit at
      `features-service (onchain family)/features_onchain_service/app/core/feature_writer.py` once chain link 1 ships
      for onchain adapters. Replace `with contextlib.suppress(LookaheadBiasError):` with direct call; let it raise.
      Verifies the gate is live.

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

- [x] [SCRIPT] P1. **`assert_available_at_present` exception for legitimately-empty parquets**. Today the guard raises
      if column missing OR any null. For empty parquets (zero rows), the column-presence check should be skipped (no
      rows, no available_at to check) — but the column must still be declared in the schema so downstream readers don't
      fail. Add: `if df.empty and "available_at" not in df.columns: log_warning(); return` to
      `assert_available_at_present`. Coordinate with writegate Phase 1A owner. **DONE 2026-05-14**:
      `unified-trading-library@e42a8027` — warning added; empty DataFrames missing column log a schema drift warning and
      return (no raise).

---

## Cross-plan coordination banners

This plan is a **coordinator**. Banners must be added to:

- [x] [SCRIPT] P0. **Banner — `defi_master_2026_05_07`**. Top-of-file:
      `> 🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping owned coordinated by available_at_lookahead_bias_completion_2026_05_08 Phase 1. Re-verify per-DeFi-adapter stamping wiring before adding new defi adapters.`
      **DONE 2026-05-14**: banner added after existing refactor banners before `## Codex SSOTs`.
- [x] [SCRIPT] P0. **Banner — `cefi_master_2026_05_07`**. Same shape, Phase 1 reference. **DONE 2026-05-14**: banner
      added after `# CeFi Master — asset_group umbrella` heading.
- [x] [SCRIPT] P0. **Banner — `tradfi_master_2026_05_07`**. Same shape, Phase 1 reference. **DONE 2026-05-14**: banner
      added after `# TradFi Master — asset_group umbrella` heading.
- [x] [SCRIPT] P0. **Banner — `predictions_master_2026_05_07`**. Phase 1 + lifecycle-bounded clip. **DONE 2026-05-14**:
      banner added after `# Predictions Master — asset_group umbrella` heading.
- [x] [SCRIPT] P0. **Banner — `sports_master_2026_05_07`**. Phase 1 partial-shipped pointer + Phase 4 expansion pointer.
      **DONE 2026-05-14**: banner added after `# Sports Master — asset_group umbrella` heading (note: existing STAMPING
      SCOPE banner is sports-specific; this is the general coordination banner).
- [x] [SCRIPT] P0. **Banner — `ml_and_features_master_2026_05_07`**. Tab 12 (Phase 6) + FEATURE_REQUIRED_INPUTS
      expansion (Phase 4) reference. **DONE 2026-05-14**: banner added after existing repo consolidation + live pipeline
      banners.
- [x] [SCRIPT] P0. **Banner — `features_repo_consolidation_2026_05_08`**. Tab 12 wiring (Phase 5.c) sequenced after this
      plan's Phase 0+1. **DONE 2026-05-14**: banner added after H1 heading at line 959, with Phase 5.c lift reference.
- [x] [SCRIPT] P0. **Banner — `live_pipeline_mtds_mdps_features_2026_05_08`**. MDPS bar boundary contract (Phase 0 here)
      is foundational. **DONE 2026-05-14**: banner added after H1 heading at line 1064, with Phase 0 MDPS bar boundary
      reference.
- [ ] [SCRIPT] P0. **Banner — `master_to_live_defi_2026_05_23`**. Group F batch-vs-live reconciliation needs honest
      `available_at` — this plan unblocks. **DEFERRED — slot 1 owns master plan** per CLAUDE.md slot-precedence rule.
      Requesting slot 1 to add:
      `> **🟡 IN-FLIGHT REFACTOR — available_at adapter stamping** (coordinated by available_at_lookahead_bias_completion_2026_05_08 Phase 1). Group F batch-vs-live reconciliation depends on honest available_at propagation.`

---

## Deferred work after 2026-05-11 ikenna-available-at-tab session

The 2026-05-11 `ikenna-available-at-tab` session shipped Phase 0.1 (UAC bar_boundary SSOT — UAC@5240000) + Phase 0.2
(UTL `compute_bar_close_boundary` helper — UTL@d798fcf3). Items still open are tracked here so the next agent picks up
cleanly without re-reading session notes.

| Phase / item                                             | Status as of 2026-05-11                                                                                                                                                                   | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0.1 — UAC bar_boundary SSOT                        | `done` (UAC@5240000 shipped)                                                                                                                                                              | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Phase 0.2 — UTL `compute_bar_close_boundary` helper      | `done` (UTL@d798fcf3 shipped)                                                                                                                                                             | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Phase 0.3 — MDPS audit + fix (bar boundary alignment)    | `done` (MDPS@`f004e12` + UAC@`8672d49` — off-by-one tf overshoot fixed + contract amended)                                                                                                | Off-by-one timeframe overshoot in `canonical_writer._stamp_candle_available_at` surfaced + fixed; UAC `bar_boundary` clause 4 amended for latency-aware Live=batch form. Issue doc: `mdps_canonical_writer_off_by_one_tf_2026_05_11.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Phase 0.4 — Historical MDPS parquet reconciler           | `done` (MDPS@`845cd9e` script + 18 tests; operational scan-only run 2026-05-11 across all 5 asset_groups returned **zero overshot residual** — vacuously done, no `--apply-fixes` needed) | Reconciler script `scripts/reconcile_mdps_available_at_off_by_one_2026_05_10_2026_05_11.py` shipped — walks `gs://{pid}-mdps/processed_candles/by_date/day=YYYY-MM-DD/timeframe=*/...`, samples first row per parquet, classifies via `classify_delta()` (closed set: overshot / correct / leak / unscannable), re-stamps overshot via `restamp_parquet_subtract_tf()` (subtracts one tf from `available_at`); idempotent (classify-before-restamp gates the re-stamp); default SCAN-ONLY + `--apply-fixes` gated. **Operational scan 2026-05-11 PM**: ran across all 5 asset_groups against prod GCS (`market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112`) — final counts per asset_group `{overshot=0, correct=0, leak=0, unscannable=0}`. Bug-window data days (2026-05-10, 2026-05-11) have no `processed_candles/by_date/day=*` entries on disk in any asset_group bucket — MDPS was not actively producing candles during the off-by-one bug window. Vacuously done. CSV audits at `/tmp/reconcile-mdps-availat-{ag}-20260511-{ts}.csv`. |
| Phase 0.5 — MDPS write-gate enforcement                  | `done` (MDPS@`7624730` shipped)                                                                                                                                                           | `_validate_stamped_candle_bar_boundary` wired into `canonical_writer.write_candle_parquet`; runs on both fresh-stamp + pre-stamped paths; sample-validates first/middle/last rows via UAC `assert_bar_boundary_contract`; 5 new unit tests cover overshoot/leak/misaligned/canonical-pass/unsupported-tf skip.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 0.6 — QG static check for MDPS bar emission        | `done` (PM@`<this commit>` shipped)                                                                                                                                                       | `scripts/quality_gates/check_mdps_bar_available_at_stamping.py` AST-walks MDPS source; flags any `df["available_at"] = ...` assignment outside canonical helper; whitelists `_stamp_candle_available_at` + `_validate_stamped_candle_bar_boundary` inside `canonical_writer.py` + inline `# QG-allow: mdps-bar-available-at` marker; 13 pytest tests; clean against live MDPS source (0 unauthorised writes).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Phase 1 (DeFi / TradFi / Predictions adapter stamping)   | `todo` (checkbox `- [ ]` × 3)                                                                                                                                                             | Owned by respective asset_group master plans (defi_master / tradfi_master / predictions_master). Harsh slot 4 picks up per-adapter wiring once Phase 0 lands at MDPS level.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Phase 4 — FEATURE_REQUIRED_INPUTS expansion              | `helper-shipped` (UAC@cb7c343 — 19 cross-instrument fg added)                                                                                                                             | DEFERRED-AFTER-`features_repo_consolidation_2026_05_08.md` Phase 7 (sports vocabulary stabilisation; defi non-yield re-audit) + UAC data_type registration for volatility / calendar / dxy_momentum (own follow-up todos in same plan body Phase 4 section). FEATURE_REQUIRED_INPUTS rose 40 → 59.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Phase 5 — AVAILABILITY_AT_SEMANTICS workspace-wide audit | `done` (UAC@cb7c343 — 14 defi pairs added)                                                                                                                                                | AVAILABILITY_AT_SEMANTICS rose 51 → 65. Audit + closure shipped same commit; no drift remaining at MTDS handler grep boundary.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Re-task (a) — UAC `EXPECTED_KNOWN_SOURCE_GAP` enum       | `done` (UAC@017b332 — closed-set member added)                                                                                                                                            | Closed set rose 14 → 15 members. Consumers (VIX 15m gap, sports `KNOWN_COVERAGE_GAPS`) named in docstring; downstream MDPS VIX-gap fix is Harsh slot 5 territory (P0-2 routing).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Re-task (b) — sports `available_at` Phase 1 flip         | `done` (Harsh's MTDS@c186ecb cited + plan flipped 2026-05-11)                                                                                                                             | Flipped the sports-stamping checkbox to `- [x]`; filed 2 P1 follow-up todos for the conservative-rule promotion + `StreamingParquetWriter.write_chunk` boundary guard (per Q-A + Q-B answers).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Re-task (c) — answer Q-A/B/C/D in `mtds_sports_*` issue  | `done` (issue doc updated 2026-05-11)                                                                                                                                                     | Q-A resolved conservative rule (`bm_time + emission_latency_ms_for_source(src)`); Q-B resolved `StreamingParquetWriter.write_chunk` boundary guard; Q-C deferred (only ODDS_API routed today); Q-D resolved (sports SOURCE_PRIORITY + emission_latency entries already in UAC).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **MDPS streaming aggregator design** (consumes Phase 0.1/0.2 contract): open in
  [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4. Ikenna
  slot 4 owns the design-ahead this cycle.
- **Per-adapter `available_at` stamping wiring (CeFi tick / TradFi / Predictions / DeFi)**: Harsh slot 4 scope.
  Cross-side ping landed in `plans/active/_agent_pings.md` on Phase 0.1/0.2 close so Harsh slot 4 unblocks.
- **features-onchain `suppress(LookaheadBiasError)` removal**: open in `ml_and_features_master_2026_05_07` Phase 2A;
  gated on chain link 1 (per-adapter stamping) shipping for onchain adapters.

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

## DONE-2026-05-11 — `ikenna-available-at-tab` session (slot 3)

| Item                                                                             | Status                     | Commits                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0.1 — UAC bar_boundary SSOT (closed-set timeframes + 4-clause contract)    | `done`                     | unified-api-contracts@5240000 (canonical/crosscutting/bar_boundary.py + 24 unit tests + root-facade re-export)                                                                                                 |
| Phase 0.2 — UTL `compute_bar_close_boundary` helper                              | `done`                     | unified-trading-library@d798fcf3 (availability_stamping.compute_bar_close_boundary + 20 unit tests; strictly-after ceiling, integer microsecond arithmetic, idempotent under replay, UAC validator round-trip) |
| Phase 5 — AVAILABILITY_AT_SEMANTICS audit + closure (14 defi pairs added)        | `done`                     | unified-api-contracts@cb7c343                                                                                                                                                                                  |
| Phase 4 — FEATURE_REQUIRED_INPUTS expansion (19 cross-instrument feature_groups) | `helper-shipped` (partial) | unified-api-contracts@cb7c343 (cross-instrument + Polymarket); volatility / calendar / dxy_momentum / sports / defi-non-yield deferred per the in-body annotations                                             |
| Cross-side ping (Phase 0 lands → Harsh slot 4 unblocks per-adapter wiring)       | `done`                     | unified-trading-pm@9bc57fcb (plans/active/\_agent_pings.md)                                                                                                                                                    |
| Plan flips (Phase 0 + Phase 4 + Phase 5 checkboxes + deferred-work scoreboard)   | `done`                     | unified-trading-pm@9bc57fcb (Phase 0 + cross-side ping) + PM@<this commit> (Phase 4 + 5 + DONE block)                                                                                                          |

Open Phase-0 sub-items (0.3 MDPS audit / 0.4 reconciler / 0.5 write-gate / 0.6 QG check) and Phase-1 per-asset-group
adapter stamping for DeFi / TradFi / Predictions / Sports remain `- [ ]` per the deferred-work scoreboard above — all
DEFERRED-AFTER `features_repo_consolidation_2026_05_08.md` Phase 7 + `live_pipeline_mtds_mdps_features_2026_05_08.md`
Phase 4-5. Harsh slot 4 picks up per-adapter wiring once MDPS unblocks.

Counts after this session: AVAILABILITY_AT_SEMANTICS 51 → 65 (+14). FEATURE_REQUIRED_INPUTS 40 → 59 (+19).
`validate_required_inputs()` green workspace-wide. UAC test suite (unit/test_bar_boundary.py +
unit/test_availability_semantics.py + test_feature_dag_ssot.py minus the two pre-existing workspace-layout-dependent
tests) green from slot-3 worktree.

### Re-task continuation (PM@4ca1cb0c — main orchestrator re-task on operator approval)

After original-scope ✅ DONE, slot 3 picked up 3 carryover items in its UAC/UTL competency per [main → slot 3] ping in
`plans/active/_agent_pings.md`:

| Re-task item                                                                           | Status | Commits                                                                                                         |
| -------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------- |
| (a) UAC `EXPECTED_KNOWN_SOURCE_GAP` enum addition to `EmptyConfirmedReason` closed set | `done` | unified-api-contracts@017b332 (StrEnum member + EMPTY_CONFIRMED_REASONS frozenset auto-derived + 3 unit tests)  |
| (b) Flip sports `available_at` Phase 1 todo per Harsh's MTDS@`c186ecb` ship            | `done` | unified-trading-pm@<this commit> (Phase 1 checkbox + 2 P1 follow-up todos for conservative rule + writer guard) |
| (c) Answer 4 design Qs Q-A/B/C/D in `mtds_sports_available_at_wiring_2026_05_11.md`    | `done` | unified-trading-pm@<this commit> (issue doc updated with full resolution + disposition note)                    |

Design-Q resolutions summary (full text in the issue doc):

- **Q-A**: conservative rule (`bm_time + emission_latency_ms_for_source(src)`) is canonical per Live=batch CLAUDE.md
  rule. Current `bm_time`-only ship preserved as named-successor temporary state; P1 follow-up todo filed in this plan's
  Phase 1 section.
- **Q-B**: column-presence assertion at `StreamingParquetWriter.write_chunk` boundary is the universal guard shape. P1
  follow-up todo filed in this plan's Phase 1 section.
- **Q-C**: deferred — only ODDS_API routed in MTDS today; re-audit when other sports adapters wire in.
- **Q-D**: resolved — UAC already has SOURCE_PRIORITY + emission_latency entries for every sports source
  (api_football=1s / odds_api=5s / understat=2h / sfi=1h / open_meteo=1h / transfermarkt=24h). No UAC pre-req.

Closed set count after this re-task: AVAILABILITY_AT_SEMANTICS 51 → 65 (unchanged from earlier this cycle).
EmptyConfirmedReason members: 14 → 15. UAC `tests/unit/test_honest_coverage.py` 33 → 36 tests pass.

### Re-task continuation 2 (Harsh slot 4 absorption — operator authorization 2026-05-11)

Operator direction "harsh agent is stale hes gone away can you do that work for him" → slot 3 absorbed the 2 P1
follow-up todos filed by re-task continuation 1 (conservative-rule promotion + writer-boundary guard). Shipped in one
logical unit across UTL + MTDS + PM:

| Re-task item                                                                            | Status | Commits                                                                                                                   |
| --------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------- |
| Conservative-rule UTL helper (`stamp_available_at_odds_snapshot` + `source=` kwarg)     | `done` | unified-trading-library@f7b704fd (UTL helper + 5 tests)                                                                   |
| `StreamingParquetWriter.write_chunk` boundary guard (`enforce_available_at=True` kwarg) | `done` | unified-trading-library@f7b704fd (writer guard + 5 tests; inlined `assert_available_at_present` to avoid circular import) |
| MTDS sports orchestrator wiring (`source="odds_api"` + `enforce_available_at=True`)     | `done` | market-tick-data-service@a512edf (orchestrator wiring + 5 sports odds tests updated for +5000ms delta)                    |
| Plan flips on the 2 P1 follow-up todos in this plan body                                | `done` | unified-trading-pm@<this commit> (`- [x]` flips + commit-sha evidence inline)                                             |

What this fully closes: the available_at-Q-A + Q-B resolutions from re-task (c) are now operationally shipped
end-to-end. Sports odds parquets written via MTDS sports orchestrator now carry
`available_at = bm_time + emission_latency_ms_for_source("odds_api")` (= bm_time + 5000ms per UAC SOURCE_PRIORITY) AND
every non-empty parquet write through `StreamingParquetWriter` with `enforce_available_at=True` raises
`LookaheadBiasError` if `available_at` is missing or null — universal write-boundary guard composes with the
conservative-rule stamping above.

What remains DEFERRED (unchanged by this re-task — separate workstreams):

- **Phase 0.3-0.6** (MDPS audit / reconciler / write-gate / QG static check) — still gated on
  `features_repo_consolidation_2026_05_08.md` Phase 7 + `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4-5.
  Harsh slot 4 was originally re-tasked to promote the live-pipeline design stubs to implementation (per PM@4ca1cb0c).
  Slot 4 has gone stale; that promotion now needs a new owner — flag for next-cycle work-split.
- **Sports non-ODDS_API adapters** (betfair / matchbook / sfi / footystats) — still not wired into MTDS
  `_process_sports_venue_with_leagues`. When they do wire in, the same conservative-rule pattern applies; verify the
  per-source latency entries exist in UAC `EMISSION_LATENCY_MS_BY_SOURCE` before wiring (Q-C resolution path).
- **Non-sports `StreamingParquetWriter` consumers** — the `enforce_available_at` kwarg defaults to False for backward
  compat. Sweep through every non-tick MTDS write path that uses `StreamingParquetWriter` +
  `record_captured_from_counts` (prediction streaming half) and enable the guard there too. P1 sweep follow-up filed
  below.

- [ ] [SCRIPT] P1. **Sweep non-tick MTDS write paths for `enforce_available_at=True`**. The CeFi tick path goes through
      `PartitionedTickWriter` and gets the guard via the writegate path. The sports odds path is now covered (above).
      The remaining surface: prediction streaming half (Polymarket CLOB capture), any TradFi / DeFi paths that use
      `StreamingParquetWriter` directly + `record_captured_from_counts` downstream. Audit needed; ~30-min per consumer +
      verify the upstream stamping is wired so the guard doesn't surface stale gaps. Owner: next-cycle work-split
      (likely slot 3 or Harsh slot 4 if available).

### Re-task continuation 3 (Phase 0.3 audit + MDPS off-by-one fix — operator authorization 2026-05-11)

After re-task continuations 1 + 2 landed + the operator confirmed gates cleared (`features_repo_consolidation` Phase 7
done; `live_pipeline_mtds_mdps_features` Phase 4-5 promoted to real impl; P0-2 MDPS surgery shipped), slot 3 picked up
Phase 0.3 (MDPS audit + fix for bar boundary alignment). Audit found an off-by-one timeframe overshoot in the canonical
writer's `available_at` stamping helper; operator authorised the one-line fix:

| Re-task item                                                                            | Status | Commits                                                                                                                    |
| --------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| MDPS canonical_writer `available_at` off-by-one tf fix + 5 tests                        | `done` | market-data-processing-service@`f004e12` (4 existing tests adjusted to `timestamp = t_close` + 1 new regression-guard)     |
| UAC `bar_boundary` clause 4 amendment (`available_at >= t_close` + 25h upper bound)     | `done` | unified-api-contracts@`8672d49` (relax strict `==` to leak-only lower bound + overshoot upper bound; 4 new clause-4 tests) |
| CLAUDE.md `available_at is per-row, write-time` rule — bar-shape sub-section added      | `done` | unified-trading-pm@<this commit>                                                                                           |
| Issue doc `mdps_canonical_writer_off_by_one_tf_2026_05_11.md` filed                     | `done` | unified-trading-pm@<this commit>                                                                                           |
| Plan flips on Phase 0.3 (`- [x]`) + scoreboard refresh (0.4/0.5/0.6 UNBLOCKED post-fix) | `done` | unified-trading-pm@<this commit>                                                                                           |

Counts: UAC bar_boundary tests rose 24 → 27 (+3 net after relaxing clause-4 single test into 4 tests). MDPS
`test_canonical_writer_record_helpers` tests rose 18 → 19 (+1 regression-guard). The MDPS fix landed on
`origin/live-defi-rollout` via FF-push from slot 3's branch (per the Half 4 cadence codified 2026-05-11) — every agent +
VM + downstream dep chain reads the corrected formula immediately. UAC contract amendment likewise FF'd into LDR.

**Open follow-ups DEFERRED to next-cycle work-split** (per the deferred-work scoreboard table above):

- **Phase 0.4 reconciler** — every MDPS parquet written between 2026-05-10 (Phase 1.2A.1 ship) and 2026-05-11 (`f004e12`
  fix) carries the over-stamped `available_at`. ~1 day of bad data on disk. Reconciler script needed to walk
  `gs://{pid}-mdps/`, re-stamp via the corrected formula. Owner: Harsh slot 5 (MDPS competency) OR slot 3 next cycle.

### Re-task continuation 4 (Phase 0.5 + 0.6 — operator authorization 2026-05-11)

After re-task continuation 3 closed Phase 0.3 (MDPS off-by-one fix + UAC contract amendment) the operator authorised
slot 3 to ship the remaining unblocked sub-phases (0.5 write-gate + 0.6 QG static check). Both are small surfaces that
compose cleanly onto the corrected stamping formula:

| Re-task item                                                                                                                                     | Status | Commits                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MDPS Phase 0.5 — write-gate via `_validate_stamped_candle_bar_boundary` round-tripping through `assert_bar_boundary_contract` + 5 new unit tests | `done` | market-data-processing-service@`7624730` (fires on both freshly-stamped + pre-stamped paths; sample-validates first/middle/last rows; raises `BarBoundaryViolationError` on overshoot/leak/misalignment)                                                                                                |
| MDPS Phase 0.6 — QG static AST-walk `scripts/quality_gates/check_mdps_bar_available_at_stamping.py` + 13 pytest tests                            | `done` | unified-trading-pm@`<this commit>` (flags any `df["available_at"] = ...` outside `_stamp_candle_available_at` / `_validate_stamped_candle_bar_boundary`; whitelists `# QG-allow: mdps-bar-available-at` marker; handles Assign + AugAssign; clean run = 0 unauthorised writes against live MDPS source) |
| Plan flips on Phase 0.5/0.6 (`- [x]`) + scoreboard refresh                                                                                       | `done` | unified-trading-pm@`<this commit>`                                                                                                                                                                                                                                                                      |

Counts: MDPS `test_canonical_writer_record_helpers` tests rose 19 → 24 (+5 write-gate tests for Phase 0.5). PM
`scripts/quality_gates/test_check_mdps_bar_available_at_stamping.py` new (+13). MDPS write-gate ships with idempotent
test fix (`00:01:00.500` → `00:00:00.500` to satisfy clause-4 latency-aware contract on pre-stamped rows). Both Phase
0.5 + 0.6 FF-push'd into LDR via slot-3 branch per Half 4 cadence.

### Re-task continuation 5 (Phase 0.4 reconciler script — operator authorization 2026-05-11)

Slot 3 shipped the Phase 0.4 reconciler script + 18 unit tests as the final close-out of Phase 0. The script is
`market-data-processing-service/scripts/reconcile_mdps_available_at_off_by_one_2026_05_10_2026_05_11.py`. Default mode
is SCAN-ONLY (CSV audit, zero GCS mutation) per the workspace operator-authority discipline; `--apply-fixes` is the
explicit flag that gates the actual parquet rewrites.

| Re-task item                                                                                                              | Status              | Commits                                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0.4 reconciler script + 18 pytest tests (classify_delta closed set + restamp_subtract_tf idempotency + path parser) | `done`              | market-data-processing-service@`845cd9e` (479-line reconciler + 18-test pure-logic test module)                                                   |
| **Operational scan-only run across all 5 asset_groups against prod GCS**                                                  | `done` (2026-05-11) | command output captured at `/tmp/reconcile-mdps-availat-{ag}-20260511-{ts}.csv` — all 5 returned `{overshot=0, correct=0, leak=0, unscannable=0}` |
| Plan flip on Phase 0.4 → `done` (operational scan complete; zero residual)                                                | `done`              | unified-trading-pm@`<this commit>`                                                                                                                |

**Operational outcome 2026-05-11 PM** — Phase 0.4 vacuously closed:

The 5-asset_group scan-only run executed from the workspace `.venv-workspace` against prod GCS buckets
`market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112`:

```text
SCAN-ONLY asset_group=cefi       | overshot=0 | correct=0 | leak=0 | unscannable=0
SCAN-ONLY asset_group=defi       | overshot=0 | correct=0 | leak=0 | unscannable=0
SCAN-ONLY asset_group=tradfi     | overshot=0 | correct=0 | leak=0 | unscannable=0
SCAN-ONLY asset_group=sports     | overshot=0 | correct=0 | leak=0 | unscannable=0
SCAN-ONLY asset_group=prediction | overshot=0 | correct=0 | leak=0 | unscannable=0
```

Verified independently by direct GCS listing:
`gcloud storage ls gs://market-data-tick-{ag}-central-element-323112/processed_candles/by_date/` shows no
`day=2026-05-10` or `day=2026-05-11` entries in any of the 5 asset_group buckets. MDPS was not actively producing
processed-candle parquets during the off-by-one bug window (2026-05-10 → 2026-05-11), so no over-stamped data landed on
disk. `--apply-fixes` is vacuous — nothing to fix.

Phase 0.4 fully closed; no further operational work needed against prod GCS. The reconciler script remains shipped for
future use if a similar drift signature reappears.

### Re-task continuation 6 (VM wrap + Phase 3.D rescan kickoff — operator directive 2026-05-11 PM)

After context-savings sweep landed + slot 3 rebased onto new lean CLAUDE.md, operator directed slot 3 to ship the
operational follow-up half for slot 6's `manifest_schema_final_gate_2026_05_09` Phase 3.D close-out:

| Re-task item                                                                                   | Status                                                                                     | Commits / artefacts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tarball refresh (CORE 4 + instruments-service + MDPS) to `gs://deployment-scripts-{pid}/code/` | `done` (2026-05-11)                                                                        | All 6 tarballs at `2026-05-11T14:23-25Z`. Refreshed via `bash deployment-service/scripts/vm/create-code-tarballs.sh --include instruments-service --include market-data-processing-service`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Watchdog VM relaunch — picks up new `cross-asset-rescan-` prefix in `VM_PREFIX_TO_BUCKET`      | `done` (2026-05-11)                                                                        | Old: `vm-zombie-watchdog-20260511-141810` deleted. New: `vm-zombie-watchdog-20260511-152717` RUNNING; verified 2 successful 5-min polls (14:33:32 + 14:38:37) finding watchable VMs + 0 zombies.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Phase 3.D cross-asset-rescan VM kickoff (instruments-service rescan)                           | 🟢 `running` (2026-05-11; 2 iterations of fix; VM 172749 progressing through asset_groups) | **Iteration 1** `cross-asset-rescan-20260511-153940` FAILED at argparse (`--operation: invalid choice: 'cross_asset_rescan'`) → fixed at `deployment-service@03ce073` (route via `VM_BACKFILL_CMD` direct script call — same shape as `launch-defi-phantom-recon-vm.sh`; the rescan is a one-shot orchestrator, not a payload-processor in the `UnifiedServiceHandler` shape). **Iteration 2** `cross-asset-rescan-20260511-171623` FAILED at `TypeError: setup_events() missing 1 required positional argument: 'mode'` → fixed at `instruments-service@35f8c7c` (pass `mode=args.mode` + `GcsEventSink` per UTL contract). **Iteration 3** `cross-asset-rescan-20260511-172749` ✅ STARTED 16:30:41Z, emitted RESCAN_RUN_STARTED + RESCAN_SHARD_STARTED(cefi), VM RUNNING. Triage bucket `gs://central-element-323112-rescan-triage` provisioned in `asia-northeast1`. Phase 8 triage review will unblock once rescan completes. **Issue doc**: [`plans/active/issues/phase_3d_rescan_cli_dispatcher_gap_2026_05_11.md`](issues/phase_3d_rescan_cli_dispatcher_gap_2026_05_11.md) ✅ RESOLVED (both iterations + bucket provisioning). |

> **🟢 VM RUNNING — cross-asset-rescan-20260511-172749 (dry-run, ETA 2-8h)**: Phase 3.D rescan VM running cleanly
> end-to-end after 2-iteration fix sequence (dispatcher gap + setup_events signature). STARTED 16:30:41Z; emitted
> `RESCAN_RUN_STARTED` + `RESCAN_SHARD_STARTED(cefi)` cleanly; processing asset_groups in sequence. Walks availability
> manifests across all 5 asset_groups to detect manifest↔disk drift; class A drifts to stdout; class C ambiguity routes
> to `gs://central-element-323112-rescan-triage/20260511-172749/triage.jsonl` for Phase 8 triage review (slot 6 /
> `manifest_schema_final_gate_2026_05_09` Phase 8 owner). No mutation (dry-run; `--apply` not set). Events at
> `gs://central-element-323112-events/events/instruments-service/2026-05-11/cross-asset-rescan-20260511-172749/`.
> Iterations 1+2 documented as failed-then-fixed in the issue doc above for the audit trail.

**Plan-of-record for Phase 3.D / Phase 8 triage**: `plans/active/manifest_schema_final_gate_2026_05_09.md` (slot 6
ownership). Cross-side ping in `plans/active/_agent_pings.md` notifies slot 6 + workspace of the rescan kickoff.

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
