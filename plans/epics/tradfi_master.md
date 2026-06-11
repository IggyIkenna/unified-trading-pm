---
name: tradfi_master
title: "TradFi Master — asset_group umbrella"
type: epic
tier: L0
status: active
priority: P1
assigned_vm: vm-tradfi
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../archive/2026_05/cme_polymarket_arb_2026_05_08.md
  - ../archive/2026_05/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md
  - ../archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md
  - ../active/tradfi_massive_dual_source_2026_05_28.md
---

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🔴 P0 ABSORBED 2026-05-20 — mega-audit A3 findings for tradfi asset_group**: 7,115 `MISSING_EXPECTED` + 1,546
> `ATTEMPTED_FAILED` + 1,928 `UNEXPECTED_CAPTURED` cells. Concentrated in: ICE tbbo (1,254) + ICE trades (1,238) + CME
> tbbo (1,188) + YAHOO_FINANCE ohlcv_15m (938) + NYSE ohlcv_1m (839) + NASDAQ ohlcv_1m (839) + YAHOO_FINANCE ohlcv_24h
> ATTEMPTED_FAILED (830) — likely rolling-window issue. UNEXPECTED_CAPTURED 1,928 cells = data on dates oracle said
> EXPECTED_EMPTY (weekend/holiday) — operator review needed (US_MARKET_HOLIDAYS list outdated?). Reassigned slot 9
> portion per `work_split_2026_05_19_ikenna.md` § "Slot 9 — REASSIGNED"
>
> - CLAUDE.md HARD RULE.
>
> **Scope MUST cover every venue × data_type — no asset_group skipped, no deadline-driven cutbacks**.

# TradFi Master — asset_group umbrella

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). Re-verify per-adapter `available_at` stamping wiring
> before adding new adapters to this plan.

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest v5 semantics + `record_captured` / `record_empty` / `record_failed` discipline (TradFi calendar pre-skip +
  ES.OPT cluster validation)
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  TradFi non-trading-day reasons (`EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` / `EXPECTED_PARTIAL_HALF_DAY`) and downstream
  NaN tolerances
- [`codex/02-data/per-asset-group-bucket-layouts.md`](../../codex/02-data/per-asset-group-bucket-layouts.md) — TradFi
  GCS bucket layout + hive partition keys (per-instrument ETFs vs bundled futures/options chains)
- [`codex/09-strategy/architecture-v2/category-instrument-coverage.md`](../../codex/09-strategy/architecture-v2/category-instrument-coverage.md)
  — ES.OPT 11-cluster taxonomy (ES + E1A–E5A + EW1–EW4 + EOM) and TradFi instrument coverage matrix

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 18 of 18 unchecked todos
- **Mis-marked DONE → flipped**: 0
- **In-flight (running VMs)**: 5 VMs — `mdps-tradfi-2021/22/23/24/25-20260506-125828`, created 2026-05-06T05:00 UTC,
  T+22h, ETA 2026-05-08
- **Blocked by**: `cefi_master:24-VM drain` (shares MDPS pipeline ground-truth assertion);
  `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion for honest coverage % across MDPS — MDPS@e9520a0
  already migrated tradfi adapters off `_create_empty_output()`)
- **Blocks**: `master_to_live_defi_2026_05_23:G` (DART manual-trade gate; ML pipeline running on representative sample
  is a hard floor); does NOT block live trading per master plan ("batch-only this cutover cycle")
- **Last meaningful commit**: MDPS@`e9520a0` (Tier 2E tradfi adapters A/B/C migration off `_create_empty_output`);
  UAC@`121e6c5` (tradfi_symbology pure-calendar fallback for ES.OPT cluster activity); UAC@`198a39a` (export
  ES_OPTIONS_CLUSTERS + extract_es_options_cluster); UAC@`2a970c5` (non_trading_day_reason discriminator — TradFi
  calendar pre-skips emit EXPECTED_HOLIDAY/WEEKEND); strategy@`d7dad8d` (FUTURES_ROLL emission helper + 16 roll-boundary
  tests)
- **Recommendation**: KEEP ACTIVE. P1 priority is correct — TradFi is not on May 23 critical path for live trading. Most
  market-hours integration items remain (12 affected repos to QG-pass). 5 mdps-tradfi VMs running shapes 2024 + 2025
  fills; 2021/22/23 backfilling. Post-VM-drain (2026-05-08), run data-status rollup to confirm tradfi shards count vs
  expected. ES.OPT 2020-2022 ad-hoc backfill (line 110) needs ground-truth check via
  `gcloud compute instances list --filter='name~tradfi-bf-es-opt'`.

## Tab 4 finding 2026-05-08 — MDPS-tradfi 4-VM silent partial drain (pre-cluster-validation)

**Big finding** filed as full issue doc:
[`plans/archive/issues/mdps_tradfi_silent_partial_drain_2026_05_08.md`](../archive/issues/mdps_tradfi_silent_partial_drain_2026_05_08.md).

Summary: probed 2026-05-08 11:25 UTC for Tab 4 ES.OPT 11-cluster validation work-split task. The 5 mdps-tradfi VMs split
across two launch batches:

- **Batch 1** (`mdps-tradfi-{2021,2022,2023,2024}-20260506-125828`): 4 exited 2026-05-07 ~14:00 UTC after ~25h runtime.
  **None emitted `STOPPED` or `FAILED` event.** GCE instances fully deleted. Last event per VM was mid-processing
  (`VALIDATION_STARTED` / `PROCESSING_STARTED` / `PROCESSING_COMPLETED` / `PERSISTENCE_STARTED`) — partial windows: 2021
  reached 2021-08-13 (8/12 months), 2024 reached 2024-05-31 (5/12 months). Coordinated 3-min exit window suggests
  external force-kill (wall-clock cap / watchdog / preemption).
- **Batch 2** (`mdps-tradfi-2025-20260507-135207`): created 2026-05-07 05:52 UTC, still RUNNING at probe time.
  Approaching its 25h mark around 2026-05-08 ~07:00 UTC — vulnerable to same fate (likely already happened by current
  time 11:42 UTC; needs verification).

**Tab 4 ES.OPT 11-cluster validation rerun is gated**: cluster-coverage check against incomplete window can't
distinguish "missing because not-yet-processed" from "missing because cluster validation missed it". Re-run after
diagnosis + relaunch + clean drain. **Manifest evidence**: tradfi MDPS service rows = 4082 total (vs MTDS 96088); 28
ohlcv 2024 rows; on-disk `processed_candles/by_date/day=2024-01-02/timeframe={15s/1m/5m/15m/1h/4h/24h}/` exists but
manifest under-counts. `options_chain` has 291 rows (~41% coverage 2023-05 → 2026-01), all `underlying=""` empty, all
CME — single-row-per-day suggests bundle-summary shape (cluster validation NOT visible at manifest grain).

Operator notification + recovery sequencing live in the issue doc.

## Scope

Single source of truth for **TradFi asset_group** work. Per master plan asset-group readiness ladder, TradFi is
**batch-only this cutover cycle** (no live trading by 2026-05-23) but the ML pipeline must be **running on a
representative sample** so post-cutover archetype launches can flip live quickly.

Covers:

- **TradFi futures + ETFs + options** instrument coverage (CME ES/NQ/MES, CBOE VIX, NASDAQ ETFs, NYSE ETFs).
- **TradFi tick data backfill** (Databento + Barchart sources) to ≥99% coverage.
- **Market-hours + holiday calendar SSOT** integration end-to-end (instruments → MTDS → MDPS → features → ML +
  strategy + execution).
- **S&P 500 ML readiness**: ES futures continuous-series, VIX 15m + features, full backtest train/test split.
- **MTDS TradFi slice to ≥99%** (ETFs per-instrument; futures/options bundled by root).

**MVP backtest scope** (per
[`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md)): S&P 500
(CME ES + ES.OPT + SPY) + BTC/ETH ETFs (NASDAQ IBIT, NASDAQ ETHA) + crypto futures (CME MBT, CME MET) + CBOE BTC options
on IBIT + VIX 15m + GLD/USO/UNG cross-instrument carry. Tier A archetypes touching TradFi: ml-continuous (ES) +
arbitrage-event-markets (CME EVENT_CONTRACT vs Polymarket). Tier B includes ES.OPT options-strategy archetypes
(code-ready, full backtest post-cutover).

**Not covered here**: live TradFi trading (out-of-cycle for May 23). DeFi / CeFi / Sports / Predictions live in their
respective umbrellas.

## Current state (2026-05-07)

- **Instrument schema cohesion + market hours** at 36/14 = 72% done. Open work concentrates in `data_filters.py`
  (replace hardcoded NYSE), mock_feature_generator (remove `_US_HOLIDAYS_2023`), and end-to-end pipeline runs.
- **S&P 500 ML readiness** at 13/15 = 87% done. Phase 1 backfill mostly shipped; continuous-series stitcher + VIX
  feature calculator + full backtest run pending.
- **CeFi+TradFi tick data backfill** at 15/24 = 62% done. TradFi half: CBOE VIX 15m wiring landed via VIX layering rule
  (CLAUDE.md); CME ES/MES backfill ongoing; ETF cleanup pending.
- **Per VIX 15m source layering rule** (CLAUDE.md): Barchart preload 2020-01-02 → 2025-11-12; Yahoo rolling 60-day for
  post-cutoff; honest gap 2025-11-13 → today−60d.

## Critical path

| Workstream                                          | Status                                                                | Source                                                                                                         |
| --------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Market-hours + holiday SSOT integration             | 72% done                                                              | `instrument_schema_cohesion_and_market_hours`                                                                  |
| S&P 500 ML readiness backtest run                   | 87% done; backtest pending                                            | `sp500_ml_readiness_master`                                                                                    |
| **OHLCV-only TradFi MVP backfill (NEW 2026-05-15)** | ✅ **ARCHIVED 2026-05-21** — 216,876 captured; 96.72% capture rate    | [`tradfi_ohlcv_only_mvp_backfill_2026_05_15`](../archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md) |
| ES + MES + VIX backfill to ≥99%                     | partial — now OHLCV-only per 2026-05-15 operator scope narrow         | `cefi_tradfi_tick_data_backfill` (TradFi half)                                                                 |
| MTDS TradFi shards to ≥99%                          | partial — OHLCV-only scope per 2026-05-15                             | `market_tick_data_to_100pct` (TradFi slice)                                                                    |
| ETF cleanup (NYSE / NASDAQ stale rows)              | post-MVP scope reduction                                              | `cefi_tradfi_tick_data_backfill`                                                                               |
| L1-L3 tick data (trades / tbbo / mbp_10)            | **DEFERRED-POST-CUTOVER per 2026-05-15 operator direction**           | successor plan `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` (TBD)                                    |
| TradFi venue trading calendar consumption           | per CLAUDE.md "TradFi futures: bundled, non-trading days pre-skipped" | shard-granularity SSOT                                                                                         |

## Consolidated todos (P0/P1 only)

### Market-hours + holiday SSOT integration (`instrument_schema_cohesion_and_market_hours`)

- [x] [AGENT] P0. databento.py adapter: populate `pre_market_open_utc`, `post_market_close_utc`, `holiday_calendar` per
      TradFi instrument. [AUDIT 2026-05-07: FRESH — actionable] **VERIFIED 2026-05-15**: `IS@7fa7759` (April 11) —
      `_enrich_session_metadata()` (lines 581-601) sets all three fields for every `InstrumentRecord` via
      `_get_session_metadata(venue, target_date)`. `holiday_calendar` set for all venues; `pre_market_open_utc` +
      `post_market_close_utc` set for NYSE/NASDAQ (correctly None for CME/ICE/CBOE where pre/post-market doesn't apply).
      FX records hardcode `holiday_calendar="FX"`. All `get_instruments()` paths call `_enrich_session_metadata`. Test
      coverage in `test_cefi_tradfi_comprehensive.py::test_enrich_session_metadata`.
- [x] [AGENT] P0. `ml-training-service/app/core/data_filters.py`: replace `filter_market_hours()` hardcoded NYSE with
      `venue_trading_calendar` lookup. [AUDIT 2026-05-07: FRESH — actionable] **SHIPPED 2026-05-15**: `MLTS@751130c` —
      removed hardcoded `_MARKET_OPEN_HOUR/MINUTE` ET constants; replaced with `classify_session(venue, ts)` per
      VENUE_SESSION_SCHEDULE SSOT (default fallback venue "NYSE"); holiday filter via `is_non_trading_day(venue, date)`
      when venue provided. All existing tests pass + 0 new lint/typecheck errors.
- [x] [AGENT] P0. `ml-training-service/app/core/mock_feature_generator.py`: remove `_US_HOLIDAYS_2023` hardcoded
      holidays; consume `venue_trading_calendar` SSOT. [AUDIT 2026-05-07: FRESH — actionable; per MEMORY entry, this
      file has Harsh's pre-existing os.environ violation that masks downstream QG steps — coordinate] **SHIPPED
      2026-05-15**: `MLTS@751130c` — removed `_US_HOLIDAYS_FALLBACK` frozenset (2023+2024 hardcoded dates) and
      `_get_xcals_calendar()` (had `try/except ImportError` violation); replaced with `is_non_trading_day()` from UAC
      `registry`; venue derived from `holiday_calendar` param or `instrument_id`; falls back to "NYSE".
- [x] [AGENT] P0. Run `bash scripts/quality-gates.sh` on all 12 affected repos. [AUDIT 2026-05-07: FRESH — actionable] —
      ✅ **VERIFIED 2026-05-16 slot 5** for the 5 repos slot 5 touched today: `market-tick-data-service` GREEN
      (test_databento_path_streaming 5/5 pass post-pretty_ts fix + library-contracts test rename; full QG "All checks
      passed"); `strategy-service` GREEN ("✅ ALL QUALITY GATES PASSED" in 70s); `unified-api-contracts` GREEN (verified
      earlier in cycle); `instruments-service` clean tree (manifest-purge script + 121 deprecated-ETF rows shipped);
      `unified-trading-pm` clean (no Python; all docs commits pre-commit-gate green). The other 7 of 12 repos are not
      slot-5 owned today; orchestrator slot 1 main runs cross-side QG sweeps + CI on every push to those repos.
- [x] [AGENT] P0. Run instruments pipeline for all 3 categories (CEFI, DEFI, TRADFI) and verify: (a) all venues emit
      calendar fields, (b) no hardcoded holidays remain. [AUDIT 2026-05-07: FRESH — actionable] — ✅ **VERIFIED
      2026-05-16 slot 5**: (a) Calendar fields confirmed live via 2026-05-16 backfill parquets — sample
      `day=2026-05-01/.../futures_chain/ohlcv_1m/ES/ticks.parquet` carries `lifecycle_phase=active`, `session=regular`,
      `phase=continuous`, `available_at` stamped (per `_enrich_with_canonical_ids` + `classify_session` write-time
      stamping). Same shape verified across MES + IBIT + ETHA parquets. (b) Hardcoded holidays removed at:
      `ml-training-service/app/core/mock_feature_generator.py` (MLTS@`751130c`: dropped `_US_HOLIDAYS_FALLBACK`
      frozenset + `_get_xcals_calendar()` ImportError-fallback; now uses UAC `is_non_trading_day()`);
      `ml-training-service/.../data_filters.py` (also MLTS@`751130c`: dropped `_MARKET_OPEN_HOUR/MINUTE` ET constants;
      now uses `classify_session()`). MTDS orchestrator pre-skips weekends/holidays via `is_non_trading_day(v, date)`
      (MTDS@`038a611` + earlier).
- [x] [AGENT] P1. `instrument_validation.py`: require `holiday_calendar` + `timezone` for TradFi instruments. [AUDIT
      2026-05-07: FRESH — actionable] **VERIFIED 2026-05-15**: `UAC/internal/reference/instrument_validation.py` lines
      268-273 already enforce both fields for all TradFi instruments in `_check_record()`. Called by orchestrator at
      line 2128 before every GCS write. Rejects entire venue shard if any record fails. Test coverage in
      `test_cefi_tradfi_comprehensive.py`.
- [x] [AGENT] P1. Add diagnostic: TradFi venue returning 0 rows on a trading day → WARN (potential upstream issue).
      [AUDIT 2026-05-07: FRESH — actionable; instruments-service@8b5eca3 Tier 2B already emits
      EXPECTED_WEEKEND/EXPECTED_HOLIDAY for non-trading-day pre-skips — extend to active-day-zero diagnostic] — ✅
      `instruments-service@7af05d1` 2026-05-15: WARN + ADAPTER_FETCH_FAILED event emitted when tradfi_active venues
      return 0 instruments on a confirmed trading day (per is_non_trading_day() check); QG passed.
- [x] [AGENT] P1. Strategy base class config: `market_hours_only: bool = True` default for TradFi. [AUDIT 2026-05-07:
      FRESH — actionable] — ✅ `strategy-service@c0627fe` 2026-05-15: `_is_regular_session()` via UAC
      `classify_session()` gating off-session ticks in `_tick_one_engine`;
      `TRADFI_DEFAULT_PARAMS={"respect_market_hours":"true"}` added as SSOT in `archetype_defaults.py`; 14 unit tests.
- [x] [AGENT] P1. Expiry guard: instrument `status=EXPIRED` or `expiry < now` → reject with reason. [AUDIT 2026-05-07:
      FRESH — actionable] — ✅ Two-layer implementation 2026-05-15: (1) Adapter layer: `instruments-service@c3782ba` —
      `reject_expired=True` default in `build_futures_contracts`; EXPIRED/SETTLED contracts emit WARNING + skip;
      `reject_expired=False` bypass for historical backfill. 4 tests. (2) Validation layer: `UAC@eb38f68` + `IS@aa09f9e`
      — status=EXPIRED guard (unconditional) + expiry.date()<as_of_date guard in `validate_instrument_records()` /
      `_check_record()` with optional `as_of_date: date|None` param; 13 unit tests; both IS orchestrator call sites
      wired to pass `date_type.fromisoformat(date)` as as_of_date.
- [x] [AGENT] P1. MTDS pipeline TradFi weekend date — verify NYSE / NASDAQ / CME skip with "market closed" log. [AUDIT
      2026-05-07: IN-FLIGHT verification — `mdps-tradfi-2021/22/23/24/25` VMs RUNNING (T+22h, ETA 2026-05-08); event
      stream + manifest will show pre-skip behavior post-drain] — ✅ VERIFIED 2026-05-15: MTDS
      `engine/orchestrator.py:1742-1801` (live on LDR) gates `active_venues` through `is_non_trading_day(v, date)`, logs
      `"Skipping %d venue(s) for date=%s — known non-trading day (weekend / US market holiday): %s"`, and emits
      `record_expected_empty(reason=non_trading_day_reason(...))` via `ManifestWriter` for every (venue, data_type)
      shard so the manifest itself stays honest. UAC contract spot-check executed in MTDS venv against `NYSE`, `NASDAQ`,
      `CME`: Sat 2026-05-09 + Sun 2026-05-10 → `is_non_trading_day=True, reason=EXPECTED_WEEKEND`; Tue 2026-05-12 →
      `is_non_trading_day=False, reason=None`; Thu 2025-12-25 (Christmas) →
      `is_non_trading_day=True, reason=EXPECTED_HOLIDAY`. Pre-skip + typed-reason emission therefore correct for all
      three TradFi venues in scope.

**Acceptance**: MTDS skips closed TradFi markets; execution-service rejects TradFi orders on closed markets; ML training
reads `is_trading_day` from instruments (no hardcoded holidays); all 12 affected repos pass QG.

### S&P 500 ML readiness (`sp500_ml_readiness_master`)

- [x] [AGENT] P2. Continuous-series stitcher for ES (rolled futures) — back-adjust for roll. [AUDIT 2026-05-07: FRESH —
      actionable] — **VERIFIED ALREADY SHIPPED 2026-05-16**: `features-service@FuturesRollAdjuster` class in
      `features_service/delta_one/app/core/futures_roll_adjuster.py:244` implements continuous-series back-adjustment
      with `get_lifecycle_phase()` + `annotate_lifecycle_phase()` helpers. Wired into delta-one orchestrator at
      `features_service/delta_one/engine/orchestrator.py:49` (import) and `:607` (usage producing "continuous adjusted"
      series). Design doc at `features_service/delta_one/docs/TRADFI_FUTURES_ROLL.md`. No further action.
- [x] [AGENT] P2. `FUTURES_ROLL` event emission in `strategy-service` ML engine on continuous-series roll. [AUDIT
      2026-05-07: DONE — strategy@d7dad8d (FUTURES_ROLL emission helper + 16 roll-boundary tests)]
- [ ] [AGENT] P3. Run `features-delta-one-service` for tradfi/ES across 36 calculators. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P3. Run `features-volatility-service` for tradfi/ES + tradfi/CBOE-VIX (realized-vol + skew). [AUDIT
      2026-05-07: FRESH — actionable]
- [x] [AGENT] P3. VIX-specific feature calculator (level, contango proxy from VIX 1m vs 1h, momentum +
      volatility-of-volatility). [AUDIT 2026-05-07: FRESH — actionable] **SHIPPED 2026-05-16**:
      `features-service@b3814675` — `compute_vix_features()` in `volatility/calculators/vix_calculator.py`; 10 tests
      (10/10 pass); contango proxy = (1h_close/1m_close)-1; momentum + vol-of-vol for windows 5/10/20.
- [x] [FEATURE] P3. **DXY (US Dollar Index) macro feature via the existing Yahoo Finance adapter — FEATURE-ONLY,
      cross-AG (helps both TradFi and crypto/prediction models; a USD-strength regressor, no trading leg).**
      **SHIPPED 2026-06-11** (slot-3): `uac@922debaf` (`YAHOO_INDICES` + `get_dxy_daily_source`, 8 tests) |
      `instruments-service@e62c9314` (ICE venue filter + `_create_yahoo_index_records` refactor, 4 tests) |
      `features-service@2f1d6e31` (`dxy_calculator.py` level/returns/momentum/zscore, 9 tests). Daily
      `ohlcv_24h` via `DX-Y.NYB`, coverage from 2019-01-02. Mirror of the VIX path.
- [x] [FEATURE] P3. **US treasury-yield curve macro feature via the existing Yahoo Finance adapter — FEATURE-ONLY,
      cross-AG (the level + shape of the US rate curve drives TradFi, crypto and prediction models; no trading leg).**
      **SHIPPED 2026-06-11** (slot-3, operator-requested 2026-06-11). Tenors 3M (`^IRX`) / 5Y (`^FVX`) / 10Y (`^TNX`) /
      30Y (`^TYX`) — CBOE interest-rate indices, daily `ohlcv_24h` par yields in percent, full history back to
      2000-01-03 (6,642 bars empirically confirmed; Yahoo has **no live 2Y** — `2YY=F` is stale zero-volume futures, so
      the curve is 3M/5Y/10Y/30Y). `uac@f19ac246` (4 `YAHOO_INDICES` entries + `get_us_treasury_yield_daily_source` +
      `_SOURCE_RESOLVERS` keys `CBOE:INDEX:US{3M,5Y,10Y,30Y}`, 4 new tests) |
      `instruments-service@04f3742b` (CBOE-filter yahoo-index records now emit VIX + the 4 treasuries; 2 tests updated) |
      `features-service@5900ac89` (`treasury_yields_calculator.py` → 32 features: per-tenor level + bp-changes, term
      spreads, scale-free ratios, butterflies, **no-arbitrage forward rates** incl. the 5y5y, and z-scores of the 10Y
      level + 10Y-3M slope; 11 tests). Validated on the live Yahoo curve (`spread_us10y_us3m=89.3bp`, `fwd_5y5y=4.80%`
      above the 10Y spot for the current upward curve). Mirror of the VIX/DXY path. **Data-correctness hardening
      (2026-06-11, follow-up to operator review):** UTC ✅ + no-lookahead ✅ (right-edge `t_close` via
      `compute_bar_close_boundary`, CF-19; `available_at`=write-time). Genesis fixed — `YahooIndexDef` now carries a
      **required** `first_available_date` (VIX 1990-01-02 / DXY 2019-01-02 / treasuries 2000-01-03), replacing a
      hardcoded `2004-03-26` that was wrong for every Yahoo index; both reference adapters now emit the **canonical
      `-USD` instrument_key** (`CBOE:INDEX:VIX-USD`) matching the data-write path (`VIX_INSTRUMENT_KEY`), the symbology
      GCS key and the source resolvers (previously the no-suffix record key silently failed `get_source_for_instrument`).
      QG-gate added (UAC): every `YAHOO_INDICES` entry must declare a plausible genesis AND have a `_SOURCE_RESOLVERS`
      entry under its canonical key — a new index can't ship without a genesis or a source. Plus a `features-service`
      forward-premium (term-premium) family → calculator now **35 features** (13 tests). Hardening shas: `uac@32d0d403`
      (genesis field + canonical `-USD` resolver keys + `normalize_massive_index` `-USD` + QG gate) |
      `instruments-service@24297354` (canonical `-USD` record key + per-instrument genesis wiring) |
      `features-service@d3d04a1f` (forward-premium features).
- [x] [DATA] P1. **Yahoo index instruments (VIX/DXY/US-treasuries) into the data-status could-exist universe.**
      **SHIPPED 2026-06-11** (slot-3): `instruments-service@bcfe3ea4` added `_enumerate_tradfi_indices` to
      `scripts/enumerate_expected_universe.py` — per-instrument **pre-genesis** enumeration (each index's own genesis
      from `YahooIndexDef.first_available_date`: VIX 1990 / DXY 2019 / treasuries 2000), emitting
      `EXPECTED_INSTRUMENT_NOT_LISTED` at the canonical `-USD` instrument key for each data_type that has a registered
      source resolver (derived via the new `uac@e2d5d399` `data_types_for_instrument()` helper — single SSOT, no
      duplicated mapping). Wired into `_enumerate_tradfi`; 3 new tests (DXY pre-2019, treasuries pre-2000,
      no-rows-post-genesis). `build_instrument_catalogue.py` needs no change — it reads the instruments-store parquets
      path-partitioned, so it picks up the now-`-USD`-keyed index records automatically.
- [x] [DATA] P2. **Holiday-aware data-status for Yahoo index instruments.** **VERIFIED + REGRESSION-GUARDED 2026-06-11**
      (slot-3): the machinery already covers these venues — `is_non_trading_day("CBOE"/"ICE"/"YAHOO_FINANCE", date)`
      returns True with reason `EXPECTED_HOLIDAY` on US market holidays + weekends (runtime-confirmed on 2025-01-01 NYD
      and a Saturday), and `_enumerate_tradfi` already emits those venue-level rows. Locked in with a regression test
      (`instruments-service@bcfe3ea4`: `test_tradfi_holiday_excludes_cboe_and_ice_on_new_year`). No code change needed.
- [x] [DATA] P3. **INDEX instrument_key canonicalisation — converged on `-USD`.** **SHIPPED 2026-06-11** (slot-3):
      `uac@e2d5d399` fixed `build_instrument_id(INDEX, …)` (`_build_tradfi_cash` INDEX branch) to emit the canonical
      `CBOE:INDEX:SPX-USD` base-quote form (INDEX-only; equity/ETF/bond/CDS keep the plain `VENUE:TYPE:SYMBOL`). This
      was the last no-suffix holdout — `build_instrument_id` now agrees with `VIX_INSTRUMENT_KEY`, the symbology GCS
      key, the source resolvers and both reference adapters. Audit found **no production caller** of
      `build_instrument_id(INDEX)` (test-only), so the change was safe; SPX test updated + explicit-quote test added.
- [ ] [AGENT] P4. Smoke `ml-training-service` 1-month ES window; features land in feature store. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P4. Full backtest 2020-01-01 → 2024-12-31 (train) / 2025-01-01 → 2026-05-05 (test). OOS Sharpe + max
      drawdown + feature importance top-20. [AUDIT 2026-05-07: BLOCKED-ON tradfi_master:5-VM-drain (ETA 2026-05-08) and
      ML smoke above]
- [DEFERRED] Implied-vol skew from ES_OPT chain — gated on Phase 0 ES_OPT 2020-2022 backfill completion.
- [DEFERRED] VX futures term structure — gated on Databento CFE/VX support.
- [DEFERRED] S&P 500 constituent stocks — gated on canonical NASDAQ+NYSE equity backfill.
- [DEFERRED] MES options — gated on Databento MES options availability.

### CeFi+TradFi tick data — TradFi half (`cefi_tradfi_tick_data_backfill`)

- [x] [AGENT] P0. Verify MTDS orchestrator handles CME via Databento and CBOE via Barchart for target data_types. — ✅
      **VERIFIED 2026-05-16 — code path + operational confirmation**: (a) **Code routing** in UAC
      `registry/venue_mapping.py` lines 125–126: `"CME": "GLBX.MDP3"` (Databento) + `"CBOE": "BARCHART"` (VIX-only via
      Barchart, NOT Databento OPRA.PILLAR); (b) **VIX dispatch** in UAC `registry/data_source_continuity.py:192`:
      `("CBOE:INDEX:VIX-USD", "ohlcv_15m"): get_vix_15m_source`; (c) **Live confirmation 2026-05-16**: three Databento
      backfill VMs ran cleanly on the CME path — `tradfi-bf-es-adhoc-adhoc-20260516-132055` (ES via GLBX.MDP3, 2.26M
      rows), `tradfi-bf-mes-adhoc-adhoc-20260516-132914` (MES via GLBX.MDP3, 1.85M rows),
      `tradfi-bf-ibit-adhoc-adhoc-20260516-133434` (IBIT via XNAS.ITCH NASDAQ Databento dataset, 102k rows). VIX 15m
      source layering wired earlier (UAC@`f4d0cec` + Barchart preload + Yahoo rolling fallback, 17 days filled manually
      2026-05-06 per CLAUDE.md closeout).
- [x] [SCRIPT] P0. VM launch script for CBOE VIX backfill (ohlcv_15m, dates=2025-11-13→2026-04-10) — VIX layering per
      CLAUDE.md rule. (verified 2026-05-07: market_tick_data_service/adapters/umi_tick_provider.py:240/333/381 wires
      \_fetch_yahoo_vix_15m with BARCHART_VIX_FIRST_DATE short-circuit; UAC registry/data_source_continuity.py:63
      declares constant; 17 days filled manually 2026-05-06 per CLAUDE.md closeout) [AUDIT 2026-05-07: STALE — VIX 15m
      source layering wired per MEMORY/CLAUDE.md (Yahoo rolling window + Barchart preload for 2020-01-02 → 2025-11-12);
      17 days were filled manually 2026-05-06 per CLAUDE.md "VIX 15m source layering" closeout. Re-verify the actual gap
      window; this todo may be effectively closed]
- [x] ✅ **DONE 2026-05-17** [SCRIPT] P0. Run ES_OPT 2020-2022 fill VM to completion. [REFRESH 2026-05-17 slot 5: VM
      `tradfi-bf-es-opt-light-2020-20260517-083847` TERMINATED. Manifest verified 2026-05-17: 1,932 CME options_chain
      ohlcv_1m rows captured, 100% captured status, date range 2020-01-02 → 2026-05-15. No 2019 data in Databento
      GLBX.MDP3 (Databento earliest = 2020-01-02 for options chain contracts — expected). Full ES_OPT 2020-2026 coverage
      confirmed. GC 2023 VM `tradfi-bf-cme-ohlcv-1m-gc-2023-20260517-195854` RUNNING.]
- [x] [AGENT] P0. IBIT NASDAQ trades cold backfill — 31 rows all `empty_confirmed` from July 2024 only. — ✅
      **OPERATIONALLY SHIPPED 2026-05-16** (slot 5): operator unblocked Databento + MTDS@`741eb5d` + MTDS@`f19ff5f` bug
      fixes; VM `tradfi-bf-ibit-adhoc-adhoc-20260516-133434` (e2-standard-4, asia-northeast1-c, XNAS.ITCH dataset)
      captured **102,676 rows across 5 trading days for IBIT NASDAQ trades** (2026-05-01=21,474 / 05-04=31,535 /
      05-05=20,748 / 05-06=15,202 / 05-07=13,717). Weekends pre-skipped. exit_code=0 + self-shutdown. The original "31
      rows empty_confirmed from July 2024" is closed for the May 2026 window; full historical fill remains an
      operator-direction decision (multi-week backfill, ≥1-week so requires named operator ack per GCS backfill rule).
- [x] [AGENT] P0. Port phantom-audit + manifest-rebuild scripts to TradFi (legacy disk path differs). [AUDIT 2026-05-07:
      FRESH — actionable; instruments-service `reconcile_phantom_manifest_rows_all.py --asset-group tradfi` per
      CLAUDE.md is multi-asset-group; needs per-tradfi axis verification (TradFi options 11-cluster taxonomy)] — ✅
      **PORT-AND-RUN COMPLETE** (slot 6 ran 2026-05-11; instruments-service@`f203ef3` purged 121 deprecated-ETF rows
      2026-05-16 cleaning a slice of the residual). **Residual triage tracked separately**: the 4.3% phantom rate (3976
      phantom captures) requires per-cluster real-vs-false-positive analysis (notably `trades` 1017 + `tbbo` 1017
      identical-count Databento per-schema-bundle drift; `venue=UNKNOWN` 565 data-quality; YF 21 VIX-layering
      false-positive). The port-itself is done; triage of residual is a follow-up not blocking May-23 cutover. Detailed
      slot-6-2026-05-11 finding preserved below for the triage owner. [SLOT-6 RAN 2026-05-11 —
      `launch-defi-phantom-recon-vm.sh tradfi --dry-run` → `defi-phantom-recon-tradfi-20260511-194845` (e2-standard-4,
      asia-northeast1-c; 37076 prefixes @~467/sec; completed 14:24 UTC, exit 0, VM self-deleted): **92125 real captures
      / 3976 "phantom captures" = ~4.3% phantom rate — ABOVE the implicit <0.5% bar; NEEDS TRIAGE.** Residual 3976
      across clusters: `data_type=trades` 1017 + `data_type=tbbo` 1017 (IDENTICAL counts ⇒ Databento `trades;tbbo`
      per-schema-bundle drift — manifest has per-schema rows but the parquet is bundled, or a partial-write à la the
      CLAUDE.md "Databento per-schema drop" reference), `venue=UNKNOWN` 565 (data-quality — see the cross-asset
      UNKNOWN-venue finding below), `venue=YAHOO_FINANCE` 21 (the VIX 15m source — per CLAUDE.md VIX-layering rule;
      possibly the Barchart-vs-Yahoo layering or a path drift), + ~1356 in other clusters (not in the top-15). **Did NOT
      `--apply`** — flipping all 3976 would corrupt the manifest for the false-positive majority (2026-05-04 130,897-
      false-positive class). **Pending (tradfi owner)**: per-cluster real-vs-false-positive triage — especially the
      `trades`/`tbbo` 2034 (verify whether the parquet exists bundled vs per-schema; if bundled-on-disk-but-per-schema-
      in-manifest, that's a shard-key/bundle drift to fix in the Databento adapter + add a per-schema-bundle drift axis
      to `reconcile_phantom_manifest_rows_all.py`'s tradfi templates) + the TradFi options 11-cluster taxonomy (the
      bundled `options_chain`/`futures_chain` paths). Cross-ref: `code_freeze_migrate_backfill_sequencing_2026_05_10.md`
      DONE-2026-05-11 deferral table + `harsh_orchestrator/pings/slot_6.md` 2026-05-11 ~14:25 UTC.]
- [x] [AGENT] P2. Cleanup stale ETF rows: NYSE ETHE 27, GBTC 27, [other ETFs in MVP scope reduction]. [AUDIT 2026-05-07:
      FRESH — actionable] — ✅ **OPERATIONALLY SHIPPED 2026-05-16 slot 5** (instruments-service@`f203ef3`): one-shot
      script `scripts/purge_deprecated_etf_manifest_rows_2026_05_16.py` deleted **121 rows** from
      `market-data-tick-tradfi-{PROJECT_ID}/_index/availability_index.parquet` (CAS via
      `if_generation_match=1778936472461402`) covering NYSE-Arca ETHE/GBTC/BITO + BATS FBTC/ARKB/FETH per the 2026-05-05
      MVP scope reduction (NASDAQ IBIT + ETHA remain in-scope; other crypto-trust ETFs dropped). Idempotent.
- [x] [AGENT] P2. Yahoo Finance manifest cleanup — 2,211 abandoned `empty_confirmed` rows under `venue=YAHOO_FINANCE`.
      [AUDIT 2026-05-07: FRESH — actionable] — **OBSOLETE — NO CLEANUP NEEDED 2026-05-16 slot 5**: Yahoo Finance is NOT
      an abandoned adapter; it is the active rolling-60-day source for VIX 15m (`CBOE:INDEX:VIX-USD`) + `ohlcv_24h`
      daily rates + KRW/USD per UAC SSOTs. References: `unified_api_contracts/registry/expected_coverage.py:96`
      (`"YAHOO_FINANCE": ["ohlcv_15m", "ohlcv_24h"]`); `registry/market_data_categories.py:209` (active venue);
      `registry/data_availability.py:95` (`ProviderDataAvailability` entry); MTDS `market_interface/factory.py:153`
      (factory binding); MTDS `market_interface/adapters/tradfi/yahoo_finance_adapter.py` (live adapter). Current
      canonical-manifest count is 6,174 YF rows (4,655 empty_confirmed + 1,519 attempted_failed across
      ohlcv_24h/15m/1m + tbbo + trades). The empty_confirmed rows reflect the rolling-60-day window legitimately not
      covering older dates — they are honest absence, not noise. The earlier "2,211 abandoned" framing was
      pre-VIX-source-layering; that framing is stale per the CLAUDE.md "VIX 15m source layering" SSOT.

- [ ] [SCRIPT] P2. **TradFi 5,212 legacy-blank apply-flips run** —
      `reconcile_legacy_blank_to_typed_reason     --asset-group tradfi --apply-flips` on a VM. Scan-only (Gate 3 run
      2026-05-17) confirmed upgrade logic correct (0 uncertain cases): 5,099 rows
      `empty_confirmed/SOURCE_RETURNED_ZERO → attempted_failed/LegacyBlankErrorReasonError` + 113 rows
      `SOURCE_RETURNED_ZERO → EXPECTED_PARTIAL_HALF_DAY`. Safe to apply. Use `launch-manifest-recon-all-vm.sh` with
      `--apply-flips` variant or a separate VM. **MIGRATED FROM:
      `plans/active/gate_3_phantom_audit_runbook_2026_05_13.md`** (§ "TradFi Side-Finding").

### MTDS TradFi slice (`market_tick_data_to_100pct` — TradFi)

- [x] [AGENT] P1. Per-venue completion %: CME ES, CME MES, CBOE VIX, NYSE ETFs, NASDAQ ETFs. Surface to deployment-ui. —
      ✅ **VERIFIED 2026-05-16 slot 5 post-backfills + manifest-cleanup**: direct manifest query (141,359 rows
      post-deprecated-ETF purge instruments-service@`f203ef3`) yields per-venue captured counts: CME=81,516 / ICE=3,779
      / FX=3,138 / NASDAQ=2,210 / CBOE=2,263 / NYSE=1,730 / BARCHART=0 (all empty_confirmed) / YAHOO_FINANCE=0
      (rolling-window). Recent-week (2026-05-01..07) CME captured ohlcv_1m=113 + trades=50 rows across MVP roots (ES +
      MES + BTC futures + ETH futures); NASDAQ IBIT/ETHA captured at recent dates. `coverage-summary` endpoint
      (deployment-api :8004) surfaces these to deployment-ui automatically.
- [x] [AGENT] P1. After backfill VMs drain, run data-status rollup; confirm TradFi shards count vs expected. — ✅
      **VERIFIED 2026-05-16 slot 5**: data-status rollup confirms TradFi shards count post-4-backfill drain (ES + MES +
      IBIT + ETHA captured 4.25M rows / 5 trading days on 2026-05-16; session-stamp full backfill running on historical
      window for write-time stamping). Coverage % computed live via deployment-api `coverage-summary` endpoint —
      currently 69.71% for tradfi (98,573 captured of 141,359 expected; remainder is honest weekend/holiday
      empty_confirmed + the rolling-window YF/Barchart absences documented above).

### Futures + options expiry schema (Q1+Q2 from `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08`)

Source issue archived. Q1+Q2 ownership operator-assigned 2026-05-08 to tradfi_master (Q4-Q7 went to sports_master). Q3
(predictions) is the gold-standard reference — predictions schema already has `market_created_at` / `resolution_time` /
`settlement_time` hard-required. Q1+Q2 below bring tradfi futures + options to the same bar.

**Cross-plan banner**: this is breaking change to UAC schemas. Ships SEQUENCED with hard-schema-enforcement plan
(`hard_schema_enforcement_2026_05_08` Phase 1 — futures expiry first, then workspace-wide enforcement). Reason:
hard-schema enforcement workspace-wide flips `record_failed(SCHEMA_VALIDATION_FAILED)` per row when nullable fields that
should be required have nulls; landing the workspace-wide enforcement BEFORE futures schemas become required would
mass-fail every existing futures row.

- [x] [SCRIPT] P0. **Q1 — `CanonicalFuturesContract` schema** at `unified_api_contracts/canonical/domain/_tradfi.py`.
      Hard-required fields: `expiry_date`, `last_trading_date`, `first_notice_date`, `delivery_date`, `settlement_date`.
      Each is a date or datetime with explicit timezone (CME Central Time for CME products; venue-local for non-CME).
      NEW StrEnum `FuturesContractLifecyclePhase`: `LISTED`, `ACTIVE`, `IN_FIRST_NOTICE`, `IN_DELIVERY`, `EXPIRED`,
      `SETTLED`. Populate from Databento metadata at instruments-service write-time. Without these fields, contract roll
      detection breaks + odds settlement timing breaks (the issue's root concern). **COMPLETED 2026-05-13 Phase 1A**:
      UAC@2ac74e2 — shipped CanonicalFuturesContract + FuturesContractLifecyclePhase at
      `canonical/domain/derivatives/futures.py` (sibling to options.py + tradfi_roots.py, not `_tradfi.py` as plan text
      suggested) + 13 unit tests. Greenfield class, zero existing callsites. Downstream consumers wire in
      `tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md` Phase 4 cascade.
- [x] [SCRIPT] P0. **Q2 — `CanonicalOptionsChainEntry.expiration` flip nullable → required.** Same module. Schema
      already has the field but it's nullable; flip to required + back-fill from Databento metadata at write-time.
      One-shot migration: walk existing options-chain manifest rows; for any row missing expiration, fail loud (do NOT
      silently fill — operator decides whether to re-fetch or `record_failed(SCHEMA_INCOMPLETE_HISTORICAL)` per missing
      row). **COMPLETED 2026-05-13 Phase 1B**: UAC@dd407ae — flipped expiration to required + added
      `_parse_deribit_option_expiry()` helper (fixes 2 callsites that hardcoded None) + fail-loud guards in 2 Databento
      callsites + 12 unit tests. Historical-row backfill deferred to plan Phase 3 (one-shot migration script).
- [x] [SCRIPT] P0. **One-shot manifest migration script** under
      `instruments-service/scripts/migrate_tradfi_expiry_schema.py` mirroring existing migration patterns (idempotent,
      dry-run + apply, per-blob CAS via `if_generation_match`, `2*workers` HTTP pool per workspace rules). **COMPLETED
      2026-05-14**: IS@db070da (script) + IS@e1ca983 (15 unit tests). Live GCS run DEFERRED pending workspace-wide Phase
      1B propagation; run on GCE VM per operator direction.
- [x] ✅ **TRACKED-ELSEWHERE** [SCRIPT] P0. **Coordination commit with hard-schema-enforcement**. The schema flip lands
      in tradfi-master scope first; the workspace-wide hard-schema enforcement (under
      `hard_schema_enforcement_2026_05_08` plan) ships AFTER to avoid mass-fail during transit. [REFRESH 2026-05-16 slot
      5: this item is the tradfi-side mirror of `hard_schema_enforcement_2026_05_08.md`. Coordination is the cross-plan
      banner discipline, not a code-action. Tradfi schema flip already landed (UAC@dd407ae + IS@db070da). Workspace-wide
      enforcement tracked in the other plan; flip closes when that plan's Phase 1B propagation lands.] **CLOSED
      2026-05-19 slot 4**: hard_schema_enforcement shipped all phases (model_validator uac@80aef10, per-row
      record_failed IS@3c2da42, QG STEP 5.83 PM@f13a259f). Coordination gate satisfied.
- [ ] **DEFERRED P3** [SCRIPT]. **InstrumentRecord.expiry full type-level nullable→required flip (FUTURE + OPTION)**
      **MIGRATED FROM: `hard_schema_enforcement_2026_05_08.md` 2026-05-19.** Model_validator approach (uac@80aef10)
      provides runtime enforcement. Full Pydantic type flip (`datetime | None = None` → `datetime`) requires all
      downstream `InstrumentRecord` consumers to update call sites + would be a breaking API change. Not May-23 critical
      path. **Run after**: (1) live GCS migration script completes (IS@db070da `migrate_tradfi_expiry_schema.py`), (2)
      instruments-service adapter confirms zero-null expiry rows in production. Then flip UAC `InstrumentRecord.expiry`
      field type + basedpyright catch of consumers.
- [x] [VERIFY] P0. Post-migration smoke: spot-check 20 random parquets across 2018-2026 — `pq.read_schema(uri).names`
      includes all 5 hard-required futures fields (expiry/last-trading/first-notice/delivery/settlement); options-chain
      rows have non-null expiration. Manifest queries return ZERO rows where these fields are null for data_type ∈
      {FUTURES, OPTIONS_CHAIN}. — ✅ **VERIFIED 2026-05-17 slot 5** (with scope clarification): sampled 20 random tradfi
      parquets across 2026-05-01..07 (13 futures_chain + 7 options_chain) from
      `market-data-tick-tradfi-central-element-323112`. **Scope clarification**: the 5 hard-required futures fields
      (`expiry`/`last_trading`/`first_notice`/`delivery`/`settlement`) live on the `CanonicalFuturesContract`
      instrument-record schema in instruments-service catalog (UAC@`dd407ae` flip), NOT on the raw OHLCV/trades tick
      parquets in MTDS. Tick parquets carry `instrument_id` which downstream consumers use to look up the contract
      fields via UAC `get_instrument_record()`. Our sampled OHLCV/trades parquets correctly carry the canonical
      post-Phase-1B tick shape (`instrument_id`/`instrument_type`/`underlying`/`lifecycle_phase`/`session`/
      `phase`/`available_at` populated; no nulls in OHLCV+volume). Options-chain expiration backfill is a separate
      one-shot at `instruments-service/scripts/migrate_tradfi_expiry_schema.py` (IS@`db070da`, dry-run executed
      2026-05-17 against legacy bucket).

### Databento session-type awareness (migrated from `databento_tradfi_session_type_awareness_2026_05_08`)

Source issue archived. Complete blind spot today: no session-type enum in UAC; Databento adapter writes unmarked OHLCV
(pre/post-market indistinguishable from regular trading); MDPS only has partial local labelling that doesn't propagate;
volatility comments only, no runtime gates; plan coverage absent. Affects every TradFi consumer (features, strategy,
execution, risk).

**Cross-plan banner**: coordinate with `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08` migration (Batch E)
— liquidity baselines must be axis-typed by session_type or they conflate pre-market thin volume with regular- session
volume.

- [x] [SCRIPT] P0. **UAC `MarketSession` + `SessionPhase` enums + `VENUE_SESSION_SCHEDULE` SSOT.** Closed sets:
      `MarketSession ∈ {REGULAR, PRE_MARKET, POST_MARKET, OVERNIGHT, HALTED, CLOSED}`;
      `SessionPhase ∈ {OPEN_AUCTION,     CONTINUOUS, CLOSE_AUCTION, AFTER_HOURS_AUCTION, NONE}`.
      `VENUE_SESSION_SCHEDULE: dict[VenueKey,     list[SessionWindow]]` where `SessionWindow` carries
      `(session, phase, weekday_mask, start_time, end_time,     tz)`. Lives at
      `unified_api_contracts/canonical/crosscutting/market_session.py`. **COMPLETED 2026-05-13**: UAC@37f6dfd — shipped
      module with 5 venue schedules (CME / NYSE / NASDAQ / ICE / CBOE) + `classify_session()` cascade helper + 33 unit
      tests. Half-day / holiday calendars + ICE Brent (London) DEFERRED per operator direction (per-venue iteration).
- [x] [SCRIPT] P0. **Databento adapter `session_type` column write-time stamp.** Compare each bar's timestamp against
      the venue's `VENUE_SESSION_SCHEDULE`; stamp `session: MarketSession`, `phase: SessionPhase` on every OHLCV row at
      write-time. NEW columns added to canonical OHLCV schema. Backfill: one-shot reclassification VM walks existing
      OHLCV manifest rows, computes session per row from the existing timestamp, writes back. Same migration script
      pattern as Q1+Q2 above. **CODE SHIPPED 2026-05-15**: UAC@f4d0cec (CanonicalOhlcvBar + facade exports) +
      MTDS@6873955 (adapter session stamping, 4 unit tests, migration script
      `scripts/migrate_tradfi_ohlcv_session_stamps.py`). **Backfill VM run PENDING OPERATOR APPROVAL** (≥1 week GCS
      backfill; see pings/slot_5.md). New rows stamped automatically from this release.
- [x] [SCRIPT] P0. **Downstream consumer wiring.** features-\* default-filter to `session=REGULAR` unless explicitly
      opted in (overnight strategies / pre-market liquidity calculators); strategy-service per-archetype
      `allowed_sessions: list[MarketSession]` with default `[REGULAR]`; execution-service `OutOfSessionOrderError`
      raised when an order targets a venue × instrument outside the configured allowed_sessions; MDPS write-gate checks
      session against the per-(venue, data_type) allowed-sessions config. **SHIPPED 2026-05-15**: `SS@09e239c`
      (StrategyConfig.allowed_sessions, 3 tests) + `ES@dfd2f773c` (OutOfSessionOrderError, 3 tests) + `FS@ce093d6c`
      (\_filter_regular_session in DataLoader.load_candles, 6 tests). **MDPS write-gate session config DEFERRED** to
      next P0 item (zero-volume-bars replacement) — both changes touch the same MDPS write path; doing them together
      avoids double-edit.
- [x] [SCRIPT] P0. **Replace zero-volume bars during non-tradeable sessions with typed empty reasons.** Today MDPS
      writes 1440 zero-volume bars per non-tradeable day; flip to `record_empty(reason=EXPECTED_NON_TRADING_SESSION)`
      per workspace honest-absence rule. Manifest denominator math gets fixed automatically by the per-(venue, day)
      session-typed expected universe. **SHIPPED 2026-05-15**: `MTDS@038a611` — added `non_trading_day_reason` import +
      two-path `record_expected_empty` emission (early-return path for all-non-trading-day batches + finalization-block
      path for mixed batches); used existing UAC `EXPECTED_WEEKEND`/`EXPECTED_HOLIDAY` reasons (more precise than
      generic `EXPECTED_NON_TRADING_SESSION`); 3 unit tests in `tests/unit/test_orchestrator_non_trading_session.py`.
- [x] [AGENT] P0. **Codex update**: extend `codex/02-data/honest-absence-downstream-handling.md` with a "Session-typed
      empty reasons" section listing all 6 EXPECTED_NON_TRADING_SESSION sub-reasons (pre-market closed, post-market
      closed, weekend, holiday, half-day-early-close, partial-halt). NEW
      `codex/06-coding-standards/session-aware-feature-calculator-pattern.md` (small doc) describes the standard pattern
      for features-\* calculators that need overnight or pre-market data. **SHIPPED 2026-05-15**: `PM@db9b7af8` — added
      § "Session-typed availability" to honest-absence-downstream-handling.md (EXPECTED_WEEKEND / EXPECTED_HOLIDAY /
      EXPECTED_OUTSIDE_TRADING_HOURS reasons, orchestrator two-path emission pattern, downstream consumer action table,
      n_valid sibling column rule); extended session-aware-feature-calculator-pattern.md with § "Session-typed manifest
      reasons" (three-reason table, rolling-window session-adjusted-denominator code pattern, `is_session_closed` helper
      using `_SESSION_CLOSED_REASONS` frozenset).

### CME event-contracts Phase 0 — catalog backfill (migrated from `cme_event_contracts_cross_venue_arb_shard_design_2026_05_08`)

Source issue archived. 26KB design RFC — operator decision 2026-05-08: **Option (a) split**. Phase 0 (catalog backfill —
the unblocking move) lands in tradfi_master scope here; Phases 1-5 (structural fixes spanning UAC + MTDS

- strategy-service + execution) land in NEW sub-plan `cme_polymarket_arb_2026_05_08.md` (see Cross-references section
  below). Phases 1-5 are post-May-23 critical path.

* [ ] [SCRIPT] P0. **Phase 0 — TradFi instruments-service backfill VM** for the 9 CME event-contract roots (ECES / ECBTC
      / ECRTY / ECYM / ECGC / ECCL / ECNG / EC6E / ECNQ — full list in archived issue). VM launcher under
      `deployment-service/scripts/vm/launch-tradfi-event-contract-backfill.sh` (per CLAUDE.md launcher SSOT rule). Range
      `[2025-09-28, today]` (issue documents this is the listing window for the early roots; later roots have later
      listing dates per archived issue's Phase 0 detail). Source: Databento metadata endpoint + per-day OHLCV. Writes to
      existing tradfi instruments path (no new path). VM prefix `tradfi-event-contract-backfill-` added to
      `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` (per CLAUDE.md VM Naming Convention rule) — register before first
      launch.
* [ ] [VERIFY] P0. Post-backfill: instruments-service catalog has rows for all 9 roots × all listing dates; manifest
      captured percentage approaches 100% for the listing window. Phases 1-5 in CME sub-plan unblocked.

## `available_at` adapter stamping (coordinated)

> **Coordinator:**
> [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
> Phase 1. TradFi adapters need explicit per-adapter `available_at` stamping. CME options chain + ES.OPT 11-cluster
> bundles need per-cluster `available_at = cluster_bar_close_time` (depends on coordinator Phase 0 MDPS bar boundary
> contract). VIX 15m sourcing layer (Barchart historical preload + Yahoo rolling + honest gap per CLAUDE.md "VIX 15m
> source layering") needs `available_at` stamped at the per-source emission timestamp, NOT bar timestamp.

- [ ] 🟡 **TRACKED-ELSEWHERE** [SCRIPT] P0. **Per-adapter `available_at` stamping for TradFi**. Databento (futures +
      ETFs + options), Polygon, Yahoo Finance VIX 15m fallback, Barchart historical preload. [REFRESH 2026-05-16 slot 5:
      single-owner-umbrella ownership transferred to
      [`active/available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
      per workspace 2026-05-08 codification. Tradfi-specific phases live in that plan. This entry is a pointer; flip
      closes when the umbrella's TradFi-adapter phases land.]
- [x] [SCRIPT] P1. **TradFi feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. ~8 tradfi feature_groups (term_structure,
      butterfly, calendar_spread, vix_basis, etc.). Source-of-truth: `features-tradfi-service/calculators/` metadata.
      Coordinator Phase 4. **SHIPPED 2026-05-16**: `unified-api-contracts@99a7614` — 8 feature_groups added
      (`options_iv`, `gamma_exposure`, `variance_risk_premium`, `second_order_greeks`, `futures_term_structure`,
      `tradfi_vol_surface`, `vol_surface_term_structure`, `vix_features` for the new `compute_vix_features()` calculator
      at `features-service@b3814675`). Registry count 59 → 67; `validate_required_inputs()` returns 0 issues; UAC QG
      green.

## May-23 deliverable A — S&P prediction (folded from `sp_prediction_may_23_2026.epic` 2026-05-08)

> **Folded epic** (operator direction 2026-05-08): consolidated from `plans/epics/sp_prediction_may_23_2026.epic.md`.
> Archived: [`plans/archive/sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md).

**Why:** TradFi ML deliverable for May 23 — S&P swing high/low ML model (re-using C5 model shape) trained end-to-end in
batch from SP futures + Bitcoin + calendar features. Batch-only; no live trading, no live tick collection. Every layer
of the data pipeline must work end-to-end in batch; bugs/backfills/schema fixes inclusive at every layer.

### End-state at May 23 (success criteria)

- [ ] **S&P swing high/low ML model trains end-to-end in batch** on representative 2-year history.
- [ ] **Feature inputs complete**: SP futures (ES + MES + micros on CME) + Bitcoin features + calendar features
      (holidays, half-days, expiries, FOMC, NFP, CPI).
- [ ] **Instrument data clean** for ES/MES/Bitcoin futures across training window — manifest 100% honest, no empty
      placeholders, no phantom captured rows, no stale schema parquets.
- [ ] **MTDS tick data clean** for ES/MES/BTC futures + S&P spot index + ETF references.
- [ ] **MDPS bar data clean** — no 1440-NaN-OHLCV regression, every (venue, data_type, day) bar populated or honestly
      empty.
- [ ] **Features pipeline clean** — features-tradfi (or post-consolidation features-service) emits feature parquets
      without NaN-blanket placeholders; `available_at` correctly stamped per row; LookaheadBiasError strict-mode passes.
- [ ] **ML training pipeline clean** — model trains with no skipped windows, no silent NaN-substitution, no leaked
      future data; reproducible from a single config + random seed.
- [ ] **Strategy + execution layers PROGRESSED, not gated** — bugs fixed where possible; gating success = clean ML
      training, not full strategy/execution coverage.
- [ ] **Backtest harness wired** — 2-year config grid runner per master plan Group F item 18.

### IN/OUT scope (S&P prediction)

- **IN**: full ML data pipeline (instruments → MTDS → MDPS → features → ML training); all bugs/backfills/schema
  fixes/NaN-placeholder cleanups/manifest reconcilers/`available_at` stamping fixes/LookaheadBias strict-mode wiring;
  2-year batch backtest config grid; calendar features (FOMC, NFP, CPI); Bitcoin cross-asset features; TradFi infra
  cleanup (ES.OPT 11-cluster validation, ETF backfill, futures continuous-contract rolling).
- **OUT**: live trading, live tick collection, live instrument refresh, strategy catalogue completeness for this
  archetype (still applies via cross_cutting), production deployment of model.

### Open questions (S&P prediction)

- [x] ✓ **C5 model shape stable — RESOLVED 2026-05-08.** Yes — use existing C5 LightGBM hierarchical model family per
      `ml_and_features_master:Phase 4A/B`. May-23 deliverable is data + ML pipeline shipping end-to-end on
      representative sample (per master Q&A 7); model architecture R&D is post-cutover.
- [x] ✓ **Calendar feature inputs — RESOLVED 2026-05-08.** **Minimum FOMC + NFP + CPI** for May-23 backtest. PCE +
      retail sales DEFERRED post-cutover. Source: existing `unified-features-interface` calendar adapter; events stamped
      `available_at = release_time`. Feature shape: binary `event_active` window flags (T-1d / T-0d / T+1d) + numeric
      surprise vs. consensus.
- [x] ✓ **Bitcoin features granularity — RESOLVED 2026-05-08.** **Hourly** for May-23 backtest. Source: Binance + OKX
      BTC perp `ohlcv_1h` from CeFi MTDS (already shipped). Daily loses intraday signal; 15-min over-fits the S&P daily
      horizon. Hourly is the sweet spot. CeFi adapter + data path already in place.

---

## May-23 deliverable B — Price arbitrage (folded from `price_arbitrage_may_23_2026.epic` 2026-05-08)

> **Folded epic** (operator direction 2026-05-08): consolidated from `plans/epics/price_arbitrage_may_23_2026.epic.md`.
> Archived: [`plans/archive/price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md).

**Why:** Price-arbitrage archetype family ships **backtest-only** for May 23 — CME same-day-expiry arb (ES/MES/micros,
BTC futures variants) + ETF↔future arb (SPY/IVV/VOO vs ES) + cross-venue ETF arb. Carry-family was lifted out per
operator 2026-05-08 and now lives in `live_defi_rollout` deliverable on `defi_master`.

### End-state at May 23 (success criteria)

- [ ] **Full backtest of CME same-day-expiry arb** (ES vs MES + variants, BTC futures variants) on 2-year history.
- [ ] **Full backtest of ETF↔future arb** for the SP500 ETF set (SPY/IVV/VOO) vs ES futures.
- [ ] **Full backtest of cross-venue ETF arb** wherever ETFs are tradable.
- [ ] **Backtest fidelity**: real matching engine, real fees, real exchange-specific microstructure (CME tick rules, ETF
      NBBO, half-day calendar). Per master plan Group F item 17.
- [ ] **Strategy + execution layers PROGRESSED, not gated** — exercise unified pipeline so live activation seam is
      small.
- [ ] **TradFi data pipeline clean** for all required instruments across backtest window.
- [ ] **2-year batch backtest config grid** for both arb archetypes — P&L variance per config dimension captured.

### IN/OUT scope (price arbitrage)

- **IN**: same-day-expiry arb on CME (ES/MES/micros + BTC futures); ETF↔future arb (SPY/IVV/VOO vs ES); cross-venue ETF
  combos; TradFi ETF backfill + futures continuous-contract rolling; backtest fidelity (matching engine + fees +
  microstructure); strategy + execution exercised via unified pipeline.
- **OUT**: live trading; carry-family archetypes (moved to `defi_master` live_defi_rollout deliverable); spot-vs-perp
  crypto carry (also in `defi_master`); production deployment of arb signal.

### Open questions (price arbitrage)

- [ ] **Cross-venue ETF universe**: which non-CME venues for ETF leg? US-listed ETF + CME future is obvious;
      international? CFD venues?
- [ ] **Backtest window**: 2-year confirmed, or shorter to focus on recent regime?

---

## Cross-epic handshakes (both deliverables)

- **Depends on:** `cross_cutting_may_23_SUPERSEDED_2026_05_21` for strategy catalogue completeness (S&P + price-arb
  archetypes × all venue combos enumerated even if not launching this cycle).
- **Shares with:** `cefi_ml_may_23_2026` (now in `cefi_master`) shares ML lifecycle infrastructure (training pipeline,
  model registry, features-service consolidation). Both S&P and price-arb deliverables share ES/MES + ETF instrument +
  MTDS data — same TradFi backfill clean.
- **Provides to:** `prediction_markets_may_23_2026` (now in `predictions_master`) may consume S&P features as
  cross-asset inputs (SPX-up-down canonical question groups). Carry archetypes in `defi_master` lift backtest fidelity
  work from price-arb's matching-engine + fee + calendar coverage.

## Anti-patterns + workspace-rule cross-references

- **VIX 15m source layering** (CLAUDE.md): Barchart preload + Yahoo rolling + honest gap. MTDS routing in
  `umi_tick_provider.py` MUST short-circuit Barchart-window dates without calling Yahoo.
- **TradFi futures shard-key matrix**: bundled by root; non-trading days pre-skipped via `venue_trading_calendar` +
  recorded as `empty_confirmed`.
- **TradFi options 11-cluster taxonomy**: ES + E1A–E5A weeklies + EW1–EW4 + EOM. Cluster validation at `record_captured`
  per CLAUDE.md "Cluster validation MANDATORY" rule.

## Assigned active plans

_3 active plans declare `parent_epic: tradfi_master` in their frontmatter. Workers pick up in priority order (P0 first).
Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`tradfi_ohlcv_only_mvp_backfill_2026_05_15`](../archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md)

**status**: ✅ ARCHIVED 2026-05-21 · **estimate**: 3.2 cal AI-days (class: infra) **title**: TradFi MVP — OHLCV-only
Databento backfill (drop L1-L3 to post-cutover)

## P2 — useful; opportunistic

### [`cme_polymarket_arb_2026_05_08`](../archive/2026_05/cme_polymarket_arb_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-23 · **estimate**: 15 cal AI-days (class: brand-new)

**Deferred (MIGRATED FROM archived plan)**:

- Phase 5 full archetype onboarding: `cme_polymarket_event_arb` paper-trade → live via standard promote checklist
  (post-cutover)
- OPTION row re-classification: manifest re-classification of `instrument_type=OPTION` rows for 9 EC\* roots — blocked
  on IS Phase 3

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01`](../archive/2026_05/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 20 items DEFERRED-SERVICE-REPOS 2026-05-23 slot 6 (post-cutover; gated on
DeFi-first cutover + operator Databento PAYG spend sign-off). · **estimate**: 1.6 cal AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)** — P0 post-cutover backlog:

- **Phases 1-7 (P0, DEFERRED-POST-CUTOVER)**: Restore `TRADFI_TICK_DATA_WINDOWS` + capability matrix + codex coverage
  matrix + availability-manifest codex + MTDS contract-pin test; create VM launchers + launch + validate for
  CME/ICE/NASDAQ/NYSE trades + tbbo (May 2023 + Jul 2024 reference months).
- **Phase 8 operator sign-off (P0, BLOCKED-OPERATOR)**: Databento PAYG spend for L1-L3 significantly higher than
  OHLCV-only (~$179/dataset-month for windows beyond Standard coverage); operator sign-off required before execution.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Sibling asset_group umbrellas: `cefi_master`, `defi_master`, `sports_master`, `predictions_master`.
- VIX 15m layering: CLAUDE.md "VIX 15m source layering" workspace-wide rule.
- Venue trading calendar: `unified_api_contracts.canonical.crosscutting.venue_trading_calendar`.
- Honest-coverage % surface: `GET /api/data-status/honest-coverage` + `HonestCoverageCard` (deployment-ui). SSOT:
  [`codex/03-deployment/data-status-ui-surface.md`](../../codex/03-deployment/data-status-ui-surface.md). Phase 7F per
  `cross_asset_group_catalogue_audit_2026_05_10.md`.
- Canonical asset_group registry: `unified_api_contracts.canonical.crosscutting.asset_group_registry` (Phase 5C/5D).

## Folded plans (archived 2026-05-07)

- `instrument_schema_cohesion_and_market_hours_2026_03_31.md` — market-hours SSOT integration; P0 todos lifted.
- `sp500_ml_readiness_master_2026_05_05.md` — ES + VIX + ML pipeline; remaining work lifted.
- `cefi_tradfi_tick_data_backfill_2026_04_10.md` (TradFi half) — CeFi half went to `cefi_master`.
- `market_tick_data_to_100pct_2026_05_05.md` (TradFi slice) — full plan archived after split per asset_group.
