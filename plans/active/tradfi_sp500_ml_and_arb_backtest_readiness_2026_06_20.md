---
doc_type: plan
title: TradFi S&P ML + price-arb backtest readiness (ES feature runs + data-clean slice)
summary:
  Run ES feature calculations and ML training smoke test, and complete the full S&P 500 backtest for price-arb and
  prediction strategies.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [tradfi, sp500, ml, backtest, features, es, vix, arb]
related:
  [
    ../epics/tradfi_master.md,
    ./data_completion_tradfi_2026_07_15.md,
    ./tradfi_v9_stage1_finish_2026_07_06.md,
    ../archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-06-12"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-20
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **Provenance**: extracted 2026-06-20 from the inline `tradfi_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas had accumulated stale May-07/08 inline todos the backlog regen never scanned —
> `regen_backlog_from_plan.py` reads `plans/active/*.md`, never `plans/epics/`). This plan carries the **TradFi-owned,
> net-new** slice of the two folded May-23 deliverables (S&P prediction "deliverable A" + price-arbitrage "deliverable
> B"): the ES/VIX feature-calculator runs, the ml-training ES smoke, and the full S&P backtest run — the parts that are
> genuinely TradFi-data work and were never dispatched.
>
> **POINTERS, NOT extractions (do NOT duplicate):**
>
> - The **2-year backtest harness / matching-engine fidelity** (master plan Group F items 17 + 18) overlaps
>   `master_to_live_defi_2026_05_23` Group F + strategy-service + the archived
>   `trading_agent_service_architecture_unlock_2026_05_22` — that work and the **cutover gating** stay in master Group
>   F; this plan only RUNS the TradFi backtest against it once the data + features are clean.
> - The **strategy catalogue completeness** (S&P + price-arb archetypes × venue combos) is a cross-cutting concern owned
>   by master Group F's strategy-catalogue dependency, not here.
> - **Instrument / MTDS / MDPS data-clean** for ES/MES/BTC futures + S&P spot + ETFs (the "End-state at May 23"
>   data-clean criteria) — the v9 manifest canonicalisation + pipeline_mode + honest-absence work is **DONE** (executed
>   in [`tradfi_v9_stage1_finish_2026_07_06`](./tradfi_v9_stage1_finish_2026_07_06.md); tracked/reconciled in
>   [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md)). The former
>   `tradfi_manifest_canonicalisation_2026_06_01` owner doc was ARCHIVED 2026-07-13 (folded into
>   `data_completion_tradfi_2026_07_15`). The former `tradfi_massive_dual_source_2026_05_28` "Massive/Databento source
>   column" premise is dead — Massive was removed as a tradfi source 2026-07-19 (operator: Databento = batch SoT, Yahoo
>   = daily); that plan is now `status: superseded`. This plan READS clean canonical data; it does not re-do the
>   canonicalisation walk.

## Context

The `sp_prediction_may_23_2026.epic` (deliverable A) and `price_arbitrage_may_23_2026.epic` (deliverable B) were folded
into `tradfi_master` 2026-05-08. Their design open-questions are all RESOLVED (C5 LightGBM model shape; daily retrain;
FOMC+NFP+CPI calendar features; hourly BTC features). What remained OPEN as inline epic todos — and was never dispatched
because the backlog regen does not scan `plans/epics/` — is the actual TradFi-data execution: run the feature
calculators for tradfi/ES + tradfi/CBOE-VIX, smoke the ES ml-training window, and run the full 2020→2026 S&P backtest.

Per master plan asset-group readiness, **TradFi is batch-only this cutover cycle** (no live trading by 2026-05-23) but
the ML pipeline must be running on a representative sample so a post-cutover archetype launch can flip live quickly.

## P0 — ES / VIX feature-calculator data-clean runs

- [x] [AGENT] P0. **BLOCKED-UPSTREAM** Diagnose + resolve features-delta-one-tradfi MDPS dependency gap before
      re-running. ✅ Three VMs attempted (20260624-055637, 20260624-061207, 20260624-061841); third bypassed preflight
      with `SKIP_DEPENDENCY_CHECK=1` but failed with "No upstream MDPS data for CME:FUTURES:ES (data_type=trades)" on
      every date — features-service expects MDPS processed-candle layer (trades→ohlcv aggregation) but tradfi MTDS
      stores raw ohlcv_1s/ohlcv_1m directly. Either (a) the features-service needs a tradfi-specific ohlcv read path
      bypassing the MDPS trades→candle step, OR (b) an MDPS run is required first to build the candle layer from MTDS
      ohlcv_1s. Issue doc: `plans/active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`. Also
      found: MTDS manifest stores `instrument_id=''` (blank) for CME rows → lookback validation never matches
      `("CME", "ES")` key (dependency_checker.py bug, same issue doc). — features-service@259569d9 | Fix A (bypass
      \_acquire_candles for TRADFI roll-sensitive groups) + Fix B (root extraction via rsplit colon) + Fix C
      (data_type=ohlcv_1m). MDPS process VM launched for 2020-01-01→2026-06-23 (`mdps-backfill-tradfi-20260624-065912`).
      **Sequencing**: process → build-continuous → features (3 VMs in order). See todos below for build-continuous +
      features VM steps.
- [ ] [AGENT] P0. **BLOCKED-UPSTREAM (re-diagnosed 2026-07-26, was stale BLOCKED-OPERATOR-DECISION).** The
      operator-decision fork itself is resolved — partial fixes shipped 2026-06-28/29
      (`market-data-processing-service@cc63d1b`: MDPS's `TradfiTradesAdapter` now writes `data_type=ohlcv_1m`, fixing
      mismatch (1); `features-service@34a5d4ff`: fixed the blank-`instrument_id` manifest-lookup bug;
      `market-data-processing-service@7d630a3`: unrelated subprocess-per-date regression fix) — but re-verified live
      2026-07-26 that this did NOT actually unblock the pipeline: **no successful run has ever landed** (the
      `features-tradfi-prd-central-element-323112` bucket has NO `_index/availability_index.parquet` at all — 404, not
      just empty), and mismatches (2) filename format (`panama_core.contract_id_for_expiry` still returns
      `CME:FUTURE:{root}-{expiry}` Databento-date format; MDPS's canonical output is still the short-symbol
      `CME:FUTURES:{root}{month}{year}.parquet` form — unchanged) and (4) build-continuous output path vs
      features-service read path (`_DERIVATIVE_DATA_TYPES = {"options_chain", "futures_chain"}` in
      `features_service/delta_one/app/core/data_loader.py:650` still has no `continuous_future` entry) are BOTH
      confirmed still unfixed by direct code read. Also: the archived
      `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`'s own "RESOLVED via Option A (direct raw-MTDS read,
      bypass MDPS)" summary does not match what actually shipped — `TRADFI_DATA_TYPE_FALLBACKS` /
      `_try_one_tradfi_fallback` in `data_loader.py` still calls `self.load_candles(...)` (the SAME MDPS
      `processed_candles/` path with a different `data_type`), not a raw-MTDS bypass; this looks like a partial
      Option-B-direction fix instead, flagged as its own discrepancy in the follow-up issue doc below (not resolved here
      — a documentation-provenance question, not a code blocker). **New done-when**: fix mismatches (2)+(4) (or make and
      implement a definitive Option A/B call), THEN run MDPS `--operation build-continuous --root ES` and confirm output
      actually lands at
      `processed_candles/by_date/day={D}/timeframe={tf}/data_type=ohlcv_1m/instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet`.
      Follow-up: `plans/active/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`.
- [ ] [AGENT] P0. **BLOCKED-UPSTREAM (re-diagnosed 2026-07-26)** Run `features-delta-one-service` for **tradfi/ES**
      across its calculators (continuous-series + roll-adjusted; `FuturesRollAdjuster` already shipped per epic).
      Confirm feature parquets land with no NaN-blanket placeholders and `available_at` correctly stamped per row
      (write-time). (Epic L245.) Same re-diagnosis as P0 item above: the operator-decision fork is resolved but the
      underlying pipeline is still unverified working — gated on the SAME mismatches (2)+(4) fix + build-continuous run
      above landing real `continuous_future` parquets for `underlying=ES` before this can run (and succeed rather than
      repeat the 3 prior failed VM attempts).
- [ ] [AGENT] P0. Run `features-volatility-service` for **tradfi/ES + tradfi/CBOE-VIX** (realized-vol + skew;
      `compute_vix_features()` calculator already shipped per epic — level, contango proxy, momentum, vol-of-vol).
      Confirm feature parquets land clean. (Epic L247.) **BLOCKED-UPSTREAM**: features-volatility-service reads
      `futures_chain` + `options_chain` data_types from the MDPS processed-candle layer (data_loader.py:51–55). TRADFI
      MTDS bucket has only `ohlcv_1s`/`ohlcv_1m` — confirmed identical blocker as delta-one (slot-23, 2026-06-24). VM
      launch deferred until MDPS gap resolved. Issue:
      `plans/active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`. **VIX sourcing — see the
      already-RESOLVED ruling below**: VIX cash index was DELETED 2026-06-23; VIX exposure = VX futures via XCBF.PITCH
      (CFE), and VIX FUTURE is now an MVP instrument (`uac@22e6a534`, MVP +409 expansion). Route
      `compute_vix_features()` off the existing VX futures OHLCV per the P2 items below. Barchart is a retired tradfi
      source (`CLAUDE.md`: "VIX=VX-futures via XCBF.PITCH, Barchart RETIRED"). **Additionally**: `realized_vol` + `vix`
      calculators exist in features-service but are NOT wired into `FEATURE_GROUPS` or the CLI dispatch — wiring gap
      todo below.

- [ ] [AGENT] P2. **DEFERRED: Wire `realized_vol` feature group into features-volatility CLI dispatch** —
      `compute_realized_vol_features()` in `calculators/realized_vol_calculator.py` exists but is NOT in
      `FEATURE_GROUPS` (parser.py) or `_calculate_features` dispatch (feature_group_service.py). Wiring requires: (1)
      add `"realized_vol"` to `FEATURE_GROUPS` list in parser.py, (2) add OHLCV data-load path to `data_loader.py` for
      tradfi ohlcv_1s (bypassing MDPS candle format), (3) add dispatch branch in
      `feature_group_service._calculate_features`, (4) add unit tests. **BLOCKED-UPSTREAM**: requires MDPS gap fix first
      for TRADFI, or a direct-ohlcv read path. Named successor: this item, or a new features-service PR once MDPS gap
      resolution is decided. (Provenance: slot-23 investigation 2026-06-24.)

- [ ] [AGENT] P2. **DEFERRED: CBOE VIX cash index gap** — `compute_vix_features()` in `vix_calculator.py` is NOT
      imported anywhere in service non-test code (wiring gap similar to realized_vol). Additionally, VIX cash index
      (^VIX) is NOT in TRADFI IS catalog (only CME venue). CLAUDE.md: VIX 15m sourced from Barchart preload + Yahoo
      rolling 60d. Wiring `compute_vix_features()` requires: (1) add VIX IS entry or a special-case static instrument,
      (2) add a Yahoo/Barchart VIX OHLCV load path to `data_loader.py`, (3) add `"realized_vol_vix"` or `"vix"` to
      `FEATURE_GROUPS`, (4) dispatch in `feature_group_service._calculate_features`. (was: "Blocked on operator
      decision: route VIX through existing Barchart/Yahoo MTDS path or add a new VIX-specific data source. Status:
      **BLOCKED-OPERATOR-DECISION**.") **RESOLVED by prior operator ruling 2026-06-23** — VIX cash index DELETED
      entirely; VIX exposure = VX futures via XCBF.PITCH. See tradfi_multisource_backfill_2026_06_22.md §VIX. Synced per
      plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md (finding 304). (Provenance: slot-23
      investigation 2026-06-24.)
- [ ] [AGENT] P2. **Live sub-todo under the resolved VIX ruling above** — steps (1)/(2) in the item above now target the
      existing VX futures_chain IS entry (CBOE venue, XCBF.PITCH, already captured per
      `tradfi_multisource_backfill_2026_06_22.md`) instead of a VIX cash-index IS entry / Yahoo-Barchart VIX-index OHLCV
      path (no such series exists — it was deleted 2026-06-23): derive VIX-equivalent features from VX futures OHLCV.
      Steps (3)/(4) (add `"vix"`/`"realized_vol_vix"` to `FEATURE_GROUPS` + dispatch in
      `feature_group_service._calculate_features`) are unchanged and still open.

## P3 — S&P ML + arb backtest exploration (gated on data-clean above)

- [ ] [AGENT] P3. Smoke `ml-training-service` on a 1-month ES window; confirm features land in the feature store and the
      C5 LightGBM model shape trains end-to-end (no skipped windows, no silent NaN-substitution). (Epic L303.)
- [ ] [AGENT] P3. Full S&P swing-high/low backtest **2020-01-01 → 2024-12-31 (train) / 2025-01-01 → 2026-05-05 (test)**.
      Report OOS Sharpe + max drawdown + top-20 feature importance. Run against the master Group F backtest harness
      (item 18) — do NOT build a TradFi-specific backtest engine (batch=live, one path). (Epic L305.)
- [ ] [AGENT] P3. Price-arb backtest readiness against the master Group F harness (item 17 fidelity): CME
      same-day-expiry arb (ES/MES/micros + BTC-futures variants), ETF↔future arb (SPY/IVV/VOO vs ES), cross-venue ETF
      arb. This plan supplies the **TradFi data + ES features**; the matching-engine / fee / microstructure fidelity +
      the cutover gating live in `master_to_live_defi_2026_05_23` Group F. Capture P&L variance per config dimension.
      (Epic deliverable-B L632-634.)

## Success criteria

- tradfi/ES + tradfi/CBOE-VIX feature parquets are clean (no NaN-blanket, `available_at` stamped, LookaheadBiasError
  strict-mode passes) on real GCS feature-store data — verified, not assumed.
- The C5 S&P ML model trains end-to-end on the representative window via the existing ml-training pipeline.
- The S&P + price-arb backtests RUN against the master Group F harness (no new asset-group backtest engine); OOS metrics
  captured.
- `bash scripts/quality-gates.sh` green on any `features-service` / `ml-training-service` change before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the feature-calculator runs + the
backtest execute on real infra against real data and produce verified parquets / metrics — code-shipped is not
operationally- shipped. The backtest-harness fidelity + the May-23 cutover decision are gated in master Group F, not
here.
