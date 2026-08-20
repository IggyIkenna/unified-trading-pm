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
    /plans/epics/tradfi_master.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-06-12"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
last_updated: 2026-08-20
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
effort: high
drift_direction: advance-code
context_scope:
  [
    /plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    features-service/features_service/volatility/engine/feature_group_service.py,
    features-service/features_service/volatility/calculators/realized_vol_calculator.py,
    features-service/features_service/volatility/calculators/vix_calculator.py,
  ]
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
      ohlcv_1s. Issue doc: `/plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`. Also
      found: MTDS manifest stores `instrument_id=''` (blank) for CME rows → lookback validation never matches
      `("CME", "ES")` key (dependency_checker.py bug, same issue doc). — features-service@259569d9 | Fix A (bypass
      \_acquire_candles for TRADFI roll-sensitive groups) + Fix B (root extraction via rsplit colon) + Fix C
      (data_type=ohlcv_1m). MDPS process VM launched for 2020-01-01→2026-06-23 (`mdps-backfill-tradfi-20260624-065912`).
      **Sequencing**: process → build-continuous → features (3 VMs in order). See todos below for build-continuous +
      features VM steps.
- [x] ✅ [AGENT] P0. **DONE — CLOSED 2026-07-31 (na-eligibility-audit, tradfi tranche, dispatch agt-6d6eaf).** This
      item's own "New done-when" (fix mismatches (2)+(4), then run MDPS `build-continuous --root ES` and confirm output
      lands) is fully met:
      `/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` is now ARCHIVED,
      `status: resolved`, `resolved_by` citing `market-data-processing-service@62a1255` (mismatch 2,
      chain-bundle-fallback filename fix) + `features-service@65606d26` (mismatch 4, continuous-future read path) + a
      verified `MDPS build-continuous` run (`market-data-processing-service@e9edb39`, ES 2020-01-01..2026-07-25, real
      `timeframe=1d continuous_future` objects confirmed via GCS + parquet-content inspection) + a real
      `features-delta-one-tradfi-20260726-132027` run landing 4 real feature parquets + 5 manifest rows. Both fixes
      predate this doc's own 2026-07-30 marker, which carried forward stale "still unfixed" wording from this item's OWN
      earlier diagnostic text rather than its later resolution. See items below for what remains (full-historical-range
      launch of features-delta-one/features-volatility, not yet done). **BLOCKED-UPSTREAM (re-diagnosed 2026-07-26, was
      stale BLOCKED-OPERATOR-DECISION).** The operator-decision fork itself is resolved — partial fixes shipped
      2026-06-28/29 (`market-data-processing-service@cc63d1b`: MDPS's `TradfiTradesAdapter` now writes
      `data_type=ohlcv_1m`, fixing mismatch (1); `features-service@34a5d4ff`: fixed the blank-`instrument_id`
      manifest-lookup bug; `market-data-processing-service@7d630a3`: unrelated subprocess-per-date regression fix) — but
      re-verified live 2026-07-26 that this did NOT actually unblock the pipeline: **no successful run has ever landed**
      (the `features-tradfi-prd-central-element-323112` bucket has NO `_index/availability_index.parquet` at all — 404,
      not just empty), and mismatches (2) filename format (`panama_core.contract_id_for_expiry` still returns
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
      Follow-up: `/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`.
- [ ] [AGENT] P0. **Run `features-delta-one-service` for tradfi/ES across its calculators**
      (continuous-series + roll-adjusted; `FuturesRollAdjuster` already shipped per epic). **CORRECTED 2026-07-31
      (na-eligibility-audit, tradfi tranche) — blocking premise was stale, real remaining gap restated below; item
      stays open.** Confirm feature
      parquets land with no NaN-blanket placeholders and `available_at` correctly stamped per row (write-time). (Epic
      L245.) The mismatches (2)+(4) fix + build-continuous landing this item was previously gated on are DONE (see the
      closed item above) — this is no longer blocked on MDPS. **Real remaining gap**: only a single-day smoke has ever
      verified-landed (`features-delta-one-tradfi-20260726-132027`, 2024-06-17, `FEATURE_GROUP=futures_basis`, 4/5
      timeframes) — the full historical range (2020-01-01→present, all calculators) has not been run. Done-when: a real
      full-range launch with feature parquets landing clean, no NaN-blanket placeholders, `available_at` correctly
      stamped per row. Follow-up tracker (history):
      `/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`.
- [ ] [AGENT] P0. **Run `features-volatility-service` for tradfi/ES + tradfi/CBOE-VIX**
      (realized-vol + skew; `compute_vix_features()` calculator already shipped per epic — level,
      contango proxy, momentum, vol-of-vol). **CORRECTED 2026-07-31 (na-eligibility-audit, tradfi tranche) —
      blocking premise was stale, real remaining gap restated below; item stays open.** Confirm feature parquets
      land clean. (Epic L247.) The mismatch (2)+(4)
      fix + build-continuous landing this item was previously gated on are DONE (see the closed P0 item above) — this is
      no longer blocked on MDPS. **Real remaining gap**: features-volatility-service has NEVER run even once for tradfi
      (not even a single-day smoke, unlike features-delta-one above) — the launch itself, at any range, has not
      happened. Done-when: a real launch (start with a smoke, then full historical range) with feature parquets landing
      clean, no NaN-blanket placeholders. Issue:
      `/plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` (resolved fork; kept for
      history) + `/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` (the
      live tracker). **VIX sourcing — see the already-RESOLVED ruling below**: VIX cash index was DELETED 2026-06-23;
      VIX exposure = VX futures via XCBF.PITCH (CFE), and VIX FUTURE is now an MVP instrument (`uac@22e6a534`, MVP +409
      expansion). Route `compute_vix_features()` off the existing VX futures OHLCV per the P2 items below. Barchart is a
      retired tradfi source (`CLAUDE.md`: "VIX=VX-futures via XCBF.PITCH, Barchart RETIRED"). **Additionally**:
      `realized_vol` + `vix` calculators exist in features-service but are NOT wired into `FEATURE_GROUPS` or the CLI
      dispatch — wiring gap todo below. **UPDATE 2026-08-15: the `vix` half of the wiring gap is now CLOSED** — see the
      `[x]` P2 item below. `realized_vol` (the general, non-VIX calculator) is untouched, tracked separately in its own
      P2 item. **Real remaining gap for THIS item is now narrower**: features-volatility-service still has never run
      even once for tradfi at any range — see the smoke-verification note below for what has (and hasn't) been proven.

- [ ] [AGENT] P2. **DEFERRED: Wire `realized_vol` feature group into features-volatility CLI dispatch** —
      `compute_realized_vol_features()` in `calculators/realized_vol_calculator.py` exists but is NOT in
      `FEATURE_GROUPS` (parser.py) or `_calculate_features` dispatch (feature_group_service.py). Wiring requires: (1)
      add `"realized_vol"` to `FEATURE_GROUPS` list in parser.py, (2) add OHLCV data-load path to `data_loader.py` for
      tradfi ohlcv_1s (bypassing MDPS candle format), (3) add dispatch branch in
      `feature_group_service._calculate_features`, (4) add unit tests. **CORRECTED 2026-07-31 (na-eligibility-audit,
      tradfi tranche) — "BLOCKED-UPSTREAM: requires MDPS gap fix first" is stale; the MDPS gap (mismatches 2+4) is fixed
      (see the closed P0 item above).** Item stays open on its own genuine remaining scope: the 4 wiring steps above are
      unstarted application-code work, not blocked on anything upstream anymore. Named successor: this item, or a new
      features-service PR. (Provenance: slot-23 investigation 2026-06-24.)

- [x] ✅ [AGENT] P2. **CLOSED 2026-07-27 (na-eligibility-audit) — fully superseded, merged into the successor item
      below.** DEFERRED: CBOE VIX cash index gap — `compute_vix_features()` in `vix_calculator.py` is NOT imported
      anywhere in service non-test code (wiring gap similar to realized_vol). Additionally, VIX cash index (^VIX) is NOT
      in TRADFI IS catalog (only CME venue). CLAUDE.md: VIX 15m sourced from Barchart preload + Yahoo rolling 60d.
      **RESOLVED by prior operator ruling 2026-06-23** — VIX cash index DELETED entirely; VIX exposure = VX futures via
      XCBF.PITCH. See /plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md §VIX. Synced per
      plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md (finding 304). Steps (1)/(2) of the
      original ask are void (no such VIX-index series exists — deleted 2026-06-23); the only live remainder (steps
      (3)/(4)) is carried forward verbatim in the next item, so this one closes rather than sitting open alongside its
      own successor. (Provenance: slot-23 investigation 2026-06-24.)
- [x] ✅ [AGENT] P2. **`vix` half DONE 2026-08-15 (this dispatch); `realized_vol_vix` half NOT DONE — see note.** Live
      sub-todo under the resolved VIX ruling above — steps (1)/(2) in the item above now target the existing VX
      futures_chain IS entry (CBOE venue, XCBF.PITCH, already captured per
      `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md`) instead of a VIX cash-index IS entry /
      Yahoo-Barchart VIX-index OHLCV path (no such series exists — it was deleted 2026-06-23): derive VIX-equivalent
      features from VX futures OHLCV. Steps (3)/(4) originally read "add `vix`/`realized_vol_vix` to `FEATURE_GROUPS` +
      dispatch" — **`vix` is now wired** (all 4 steps from the sibling `realized_vol` item's pattern, applied to `vix`):
      (1) `"vix"` added to `FEATURE_GROUPS` in `cli/parser.py` (+ TRADFI-only validation guard); (2) new
      `VolatilityDataLoader.load_vix_ohlcv_raw()` in `core/data_loader.py` reads the single-instrument
      `venue=CBOE/instrument_type=FUTURE/instrument_id=CBOE:FUTURE:VIX` candle (data_type=`ohlcv_15m` by default — see
      "ohlcv_1m vs ohlcv_15m" finding below); (3) `_load_raw_data`/`_calculate_features` dispatch branches +
      `_calculate_vix_features` added in `engine/feature_group_service.py`; (4) unit tests added to
      `tests/volatility/unit/test_data_loader.py` + `test_orchestration_service.py`. Also registered a new
      `VIX_FEATURES_SCHEMA` in `schemas/output_schemas.py` (was falling back to `OPTIONS_IV_SCHEMA`, whose required
      columns don't match VIX output). **`realized_vol_vix` was NOT built** — no such calculator/feature group exists
      anywhere in the codebase (distinct from the real `realized_vol_calculator.py` tracked in the sibling P2 item
      above, which this dispatch did not touch); this string appears to be aspirational/undefined leftover text, not a
      concrete scope item — flagging rather than silently closing it. **`ohlcv_1m` vs `ohlcv_15m` finding (part of this
      dispatch's mandate — resolve, don't guess)**: UAC `required_inputs.py`'s `vix_features` entry declares BOTH
      `ohlcv_1m` and `ohlcv_15m` as required inputs; `compute_vix_features()`'s signature (`candles_1m` + optional
      `candles_1h`) never mentions 15m. Traced via git archaeology, NOT assumption: the `ohlcv_15m` entry is CORRECT and
      forward-looking — it was added 2026-05-16/06-24 anticipating a real, later-shipped 2026-08-07 decision (source
      doc: `/plans/archive/2026_08/issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`,
      also cited verbatim in MDPS `orchestration_scanner.py`'s `_COARSE_TIMEFRAME_CHAIN_ADMISSIONS` comment: "HAS a real
      downstream consumer for coarse candles (vix_features ohlcv_15m)") that purpose-built a CBOE-scoped
      `ohlcv_15m`/`ohlcv_24h` aggregation specifically so `vix_features` could consume it — live-verified captured
      2026-08-14 (same doc). The declared `ohlcv_1m` requirement, by contrast, corresponds to NO clean read path: CBOE
      VX-futures raw `ohlcv_1m`/`ohlcv_1s` ticks are captured only at the multi-leg `instrument_type=futures_chain`
      grain (no front-month-leg-selection logic exists anywhere in this codebase to turn that into a single clean
      series). No other calculator in `features-volatility-service` was already wired to read a single-instrument OHLCV
      bar series (every wired group reads an options/futures CHAIN snapshot) —
      `realized_vol`/`treasury_yields_calculator.py`/ `dxy_calculator.py` share the identical unwired gap, confirming
      this is a real, previously-unaddressed shape gap in the orchestrator, not specific to VIX. Resolution: wired
      `load_vix_ohlcv_raw()` off `ohlcv_15m` (confirmed available, purpose-built for this exact consumer) rather than
      `ohlcv_1m` (unconfirmed/unusable at a clean grain). `compute_vix_features()` needed ZERO code changes — its
      `candles_1m` parameter name reflects original 1m design intent but is not an enforced cadence; it operates
      correctly on any regularly-spaced OHLCV series. Did NOT touch `required_inputs.py` (`unified-api-contracts`) — its
      `ohlcv_15m` declaration is correct as-is; whether to also correct/remove the `ohlcv_1m` declaration (since the
      shipped wiring never reads it) is a small, separate UAC-repo judgment call left unresolved here — flagging, not
      fixing, since it doesn't block anything else.

      **Shipped**: `features-service@3ed5bed254` (initial wiring). **Live-verified 2026-08-15 against real,
          manifest-captured CBOE data** (`python -m features_service.volatility.cli.main --feature-group vix --asset-group
          TRADFI --start-date 2026-07-20 --end-date 2026-07-20 --instruments VIX --dry-run --force`, real ADC creds, no
          mocks): the first live run surfaced 2 real bugs the mocked unit tests couldn't catch — (a) the initial
          `load_vix_ohlcv_raw()` reused the generic `_candle_blob_candidates`/`{instrument_id}.parquet` path convention,
          but the REAL object (confirmed via direct `list_blobs` on `market-data-tick-tradfi-prd-central-element-323112`)
          sits at a different shape:
          `processed_candles/by_date/day={d}/pipeline_mode=batch_databento/timeframe=15m/data_type=ohlcv_15m/instrument_type=FUTURE/venue=CBOE/underlying=VIX/ticks.parquet`
          (an `underlying=` folder segment + bare `ticks.parquet` leaf — the coarse-timeframe aggregation writer's own
          convention, distinct from the chain/spot/derivative-ticker convention); (b) `_calculate_vix_features` converted
          "timestamp" to an epoch-int64, but `feature_writer._add_timestamp_out` does `pl.col("timestamp") +
          pl.duration(...)`, which requires a temporal dtype — crashed on write. Both fixed + re-verified live. **Fixed +
          shipped**: `features-service@f6c0273421`. **Final live evidence**: `load_vix_ohlcv_raw(2026-07-20)` → 809 real
          rows (`venue=CBOE`, symbol=`VX/V6`, real OHLC); `load_vix_ohlcv_raw(2026-07-21)` → 812 real rows (second date,
          independent confirmation); `_calculate_vix_features` on both → non-NaN-blanket real values (`vix_level=21.82`→
          `18.45` across the two dates; 97.5-99.4% non-null across all 8 feature columns, matching expected rolling-window
          warm-up). **What's still NOT verified**: an actual parquet WRITE to GCS — the write pipeline itself works
          mechanically (schema validates with only a non-fatal dtype warning, write-gate passes) but is suppressed by
          `unified_trading_library.emission_publisher.publish_with_policy`'s STRICT_FAIL default for the unregistered
          `("features-volatility-service", "vix")` pair (any day with rolling-window warm-up NaN — i.e. every day — hits
          this). Root-caused + a fix drafted (add `("features-volatility-service", "vix"): ServiceEmissionPolicy.NAN_FILL`
          to `unified_api_contracts/canonical/crosscutting/service_emission_policy/_policies.py`, mirroring the existing
          `vol_30d` entry's identical rolling-window-warmup rationale) — **NOT shipped**: `unified-api-contracts`'s QG
          failed on 2 pre-existing, topically-unrelated test failures (`test_cassette_orphan_checker.py::
          test_no_unallowlisted_orphans`, `test_execution_service_venue_coverage_cascade_invariant.py::
          ...no_new_regressions`) that block a green tree for an unrelated reason; forcing a UAC ship through a red gate
          for those 2 failures is out of this dispatch's scope. Tracked as its own todo below. features-service's
          `load_vix_ohlcv_raw`/`_calculate_vix_features` code is NOT blocked by this — it's purely the cross-repo
          emission-policy registration.

- [ ] [AGENT] P2. **Follow-up: register a UAC emission policy for `("features-volatility-service", "vix")`** — the pair
      is currently unregistered, so `publish_with_policy` defaults to `STRICT_FAIL`, silently suppressing every `vix`
      feature write (rolling-window momentum/vol-of-vol features always carry SOME per-day warm-up NaN, so
      `completeness_fraction` is never exactly 1.0). Fix: add
      `("features-volatility-service", "vix"): ServiceEmissionPolicy.NAN_FILL` to
      `unified_api_contracts/canonical/crosscutting/service_emission_policy/_policies.py` (mirrors the existing
      `("features-service", "vol_30d"): NAN_FILL` entry — same rolling-window-warmup rationale; ML consumers NaN-fill
      natively). Discovered + drafted 2026-08-15 during this dispatch's live-verification of the `vix` wiring above, but
      NOT shipped: `unified-api-contracts`'s `quality-gates.sh` failed on 2 pre-existing failures unrelated to this
      1-line change (`test_cassette_orphan_checker.py`, `test_execution_service_venue_coverage_cascade_invariant.py`) —
      fixing those is a separate, out-of-scope investigation. Done-when: the entry is added, UAC QG is green (either
      those 2 pre-existing failures are independently fixed, or confirmed unrelated + already-baselined so the gate
      passes), shipped, and a real `vix` parquet write is live-verified landing in GCS (not just dry-run local write).
      **Also worth a side-note for whoever picks this up**: while investigating the emission-policy key, found that the
      3 existing volatility entries (`("features-service", "high_low_24h"/"vol_30d"/"realised_vol_intraday")`) are keyed
      under the bare `"features-service"` service name, but `features_service/volatility/core/feature_writer.py`'s
      `_check_emission_policy` actually calls `publish_with_policy(service=_SERVICE_NAME, ...)` where
      `_SERVICE_NAME = "features-volatility-service"` (a different literal) — those 3 entries may ALSO be silently
      dead/unmatched at runtime. Not confirmed or fixed here (out of scope) — worth a quick live check before assuming
      those 3 groups' NAN_FILL/PARTIAL_OK policies are actually taking effect.

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

## Progress Log

- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **KEEP-NA, stale items CORRECTED (1 closed
  - 3 reworded).** All 8 open todos read end-to-end, plus their two cited blocker docs read in full. **Correcting the
    2026-07-30 marker below**: its claim that mismatches (2)+(4) were "re-confirmed unfixed by direct code read
    2026-07-26/29" was itself stale — both were fixed and independently re-verified on 2026-07-26 (mismatch 2:
    `market-data-processing-service@62a1255`; mismatch 4: `features-service@65606d26`), and a real MDPS build-continuous
    run landed (`market-data-processing-service@e9edb39`) plus a real features-delta-one smoke
    (`features-delta-one-tradfi-20260726-132027`) — the cited tracker doc is now ARCHIVED/resolved, not live. The
    2026-07-30 marker's "unfixed" wording was copied forward from this doc's own opening-diagnosis text rather than its
    later resolution. **Applied**: closed the P0 "New done-when" item (line ~91) citing the archived tracker's
    `resolved_by` evidence. Did NOT close the features-delta-one / features-volatility / realized_vol-wiring items
    (lines ~114/121/144) — their own asks remain genuinely open (only a single-day smoke has ever landed for delta-one;
    features-volatility has never run at all; the wiring steps are unstarted) — reworded their stale "still
    blocked/unfixed on MDPS" premises to state the real current gap instead. **Not RECLASSIFY** despite 114/121
    superficially resembling bounded launch+verify VM tasks: the sibling archived tracker's own history shows landing
    even ONE single-day smoke required finding+fixing 9 distinct real bugs across 2 repos in one long session, and still
    left an un-root-caused sparse-coverage issue — extending to the full historical range on this live-dispatch-adjacent
    TradFi ML chain is real multi-file engineering risk, not a cleanly bounded checkable outcome. Also noting (not
    acting on): `locked_by: live-defi-rollout` textually blocks only archival per `PLAN_FORMAT.md`, not an `assigned_vm`
    frontmatter edit — the prior marker's "reclassification would be a state change on a locked doc" reasoning isn't
    literally supported, though it doesn't change today's verdict (kept NA on the engineering-risk merits above, not the
    lock). Doc stays NA; 7 open todos remain (was 8).
- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid.** All 8 open todos read end-to-end.
  `locked_by: live-defi-rollout` is set (archival blocked; reclassification would be a state change on a locked doc). On
  content: 4 items are self-tagged `BLOCKED-UPSTREAM` with a live, still-unfixed tracker
  (`/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` — mismatches (2) and
  (4) re-confirmed unfixed by direct code read 2026-07-26/29, and the `features-tradfi-prd` bucket has no availability
  index at all), and the 3 P3 backtest items are gated on the master Group-F harness owned by
  `master_to_live_defi_2026_05_23`, not by this plan. Genuinely blocked upstream, not mis-defaulted.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries, trimmed from 7) — dropped 3 archived/pointer-only
  plan refs (parent epic, resolved forks) for 3 real features-service source files (`feature_group_service.py`,
  `realized_vol_calculator.py`, `vix_calculator.py`) the open wiring todos name directly.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-07**: re-verified context_scope (6 entries, unchanged) — the only commit since the last scout
  (`b30fb5267b`) added `effort: high` to frontmatter, no substantive content change; all 6 entries still resolve and
  remain the correct minimal set.
- **na-eligibility-audit 2026-08-07** (tradfi tranche): **KEEP-NA, valid -- re-verified, unchanged.** All 7 open todos
  re-read end-to-end; count reconciled (7/7, matching the 2026-07-31 tally). No content change since that pass -- only
  the frontmatter `effort: high` addition. The 4 BLOCKED-UPSTREAM-turned-GENUINE_WORK items (delta-one full range,
  features-volatility launch, realized_vol wiring, VIX sub-todo) and 3 P3 backtest items (gated on master Group-F
  harness) remain genuinely open engineering/design-risk work, not mis-defaulted NA. `locked_by: live-defi-rollout`
  blocks archival only, not reclassification -- noted, not acted on. Doc stays NA.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, valid -- confirmed via git log
  the only commits since 2026-07-31 are context-scout/frontmatter touches (no content change).** All 7 open todos
  re-read; count reconciled (7/7). One item (realized_vol feature-group CLI wiring -- 4 named concrete steps: registry
  entry, data-load path, dispatch branch, unit tests) reads closer to a bounded application-code task than its siblings
  on independent merits, but the fresh 08-07 marker already itemized and re-affirmed it as genuine, unblocked
  engineering work (only a single-day smoke has ever landed for the sibling P0 items, real multi-file risk) -- not
  overridden this pass. Doc stays NA.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:7c48960176cf7d5f]: **KEEP-NA,
  valid -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08 marker" (git-date fallback), but
  `git diff <08-08-marker-sha>..HEAD` shows the ONLY intervening change is the context-scout line directly above -- zero
  todo/verdict content changed. Reaffirming the 08-08 verdict without a fresh full re-read; see
  `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying false-positive class
  this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:3058e612d8cf6fce]: **KEEP-NA,
  valid -- fresh full read, all 7 todos re-verified.** Todo 3 (realized_vol wiring) again reads as more bounded than its
  siblings on its face and is again flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE, but not promoted -- the established
  reasoning (landing even ONE single-day smoke on this doc's sibling tracker required finding+fixing 9 distinct bugs
  across 2 repos, evidencing real multi-file engineering risk on live-dispatch-adjacent ML machinery) is not overridden
  by this pass either. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid — established ruling not
  re-litigated (5th consecutive pass).** 6 of 7 open todos covered by the standing multi-times-reaffirmed ruling; the
  7th stays flagged, not promoted, same reasoning. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — established ruling
  not re-litigated (6th consecutive pass).** All 7 open todos re-read end-to-end; count reconciled (7/7). No content
  change since the 08-16 marker (only the 08-17 context-scout touch). The 4 P0/P2 feature-pipeline items (delta-one
  full-range launch, features-volatility launch, realized_vol CLI wiring, VIX sub-todo) and 3 P3 backtest items
  (gated on master Group-F harness) remain genuine engineering/design-risk work on live-dispatch-adjacent ML
  machinery, not mis-defaulted NA — the sibling archived tracker's own history (landing even one single-day smoke
  required finding+fixing 9 distinct bugs across 2 repos) is the standing basis, not re-derived this pass.
  `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
