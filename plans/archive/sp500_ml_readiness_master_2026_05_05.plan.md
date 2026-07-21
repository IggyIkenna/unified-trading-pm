---
doc_type: plan
title: S&P 500 Technical-Indicator ML Readiness — Master Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-05
owner: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-05
depends_on:
  [cefi_tradfi_tick_data_backfill_2026_04_10, cme_sp_ml_signal_preaudit_2026_04_20, data_pipeline_completion_2026_04_18]
---

## Deferred work — migrated to: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — successor:

tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20 (the ES/VIX feature-calculator + ml-training-smoke + backtest
items are extracted verbatim into that plan, currently BLOCKED-OPERATOR-DECISION per
`plans/active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`; the continuous-ES-stitcher and
FUTURES_ROLL-event items are duplicate checkboxes of work already shipped later in this same file; MES-options and
Yahoo-manifest-cleanup items are resolved-N/A / already-executed per operator ruling and a later cleanup. One item
(individual S&P 500 constituent equities vs. the broader NASDAQ/NYSE backfill in
`plans/active/tradfi_consolidated_closeout_2026_07_18.md`) is AMBIGUOUS on exact universe match — needs operator
confirmation, not a new issue doc. NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for
operator `[unlock-plan]` cleanup.)

# S&P 500 Technical-Indicator ML Readiness — Master Plan

## 1. Goal + Non-Goal

### Goal

Train a machine-learning model predicting S&P 500 direction/return on **ES futures 1m candles** using
technical-indicator features. The MVP universe is intentionally small and data-complete:

- **ES futures (CME)** — primary instrument; 1m OHLCV + trades, fully backfilled.
- **MES futures (CME)** — micro contract; 1m OHLCV + trades, fully backfilled.
- **VIX index (CBOE)** — implied-vol regime feature; 15m OHLCV.
- **Technical-indicator features** — `features-delta-one-service` (36 calculators incl. TechnicalIndicators,
  MovingAverages, Oscillators, Momentum, VWAP, Returns, MarketStructure, FuturesBasis).
- **Calendar features** — `features-calendar-service` (temporal + economic events: NFP, CPI, FOMC).
- **Realized-vol + skew features** — `features-volatility-service` over ES + VIX.

### Non-Goal (MVP)

Explicitly **out of scope** for this plan; tracked in §4 for follow-up:

- Individual S&P 500 constituent stocks (only 79 instruments captured at legacy path on one sample date; no
  canonical/manifested coverage).
- Implied-vol skew from ES options chain (gated on ES_OPT 2020-2022 backfill, in flight as of 2026-05-05).
- VX futures term structure (Databento adapter does not support CFE/VX symbology).
- MES options.
- Yahoo Finance manifest cleanup.

## 2. Verified Ground Truth as of 2026-05-05

Manifest probed at: `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet`

| Asset                                                      | Status                                                    | Path                                                                                                                | Notes                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ES futures (CME) ohlcv_1m + trades                         | DONE 2020-01-01 → 2026-05-04, 100% captured               | `day={D}/asset_group=tradfi/venue=CME/instrument_type=futures_chain/data_type=ohlcv_1m/underlying=ES/ticks.parquet` | 5,110 manifest rows                                                                                                                                                                                                                                      |
| MES futures (CME) ohlcv_1m + trades                        | DONE 2020-01-01 → 2026-05-04, 100% captured               | same shape, `underlying=MES`                                                                                        | 7,273 manifest rows                                                                                                                                                                                                                                      |
| VIX index (CBOE) ohlcv_15m                                 | DONE 2020-01-07 → 2026-05-05                              | `day={D}/asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet`                       | 1,602 manifest rows; sample-read confirmed real OHLC, `instrument_key=CBOE:INDEX:VIX-USD`, volume=0                                                                                                                                                      |
| ES_OPT options_chain ohlcv_1m                              | PARTIAL — 2022-2026 sparse (2025 = 8 days), 2020-2021 = 0 | canonical not yet written; legacy `category=tradfi/venue=CME/data_type=options_chain/` for some 2024 dates          | VM `tradfi-bf-es-opt-adhoc-adhoc-20260505-183009` running 2026-05-05 18:30Z to fill 2020-2022                                                                                                                                                            |
| IBIT/ETHA (NASDAQ) trades + ohlcv_1m                       | LIVE-ONLY                                                 | canonical `venue=NASDAQ/instrument_type=equity` writes daily                                                        | Manifest 31 July-2024 `empty_confirmed` rows are dishonest absence (Databento symbology mismatch); not blocking MVP                                                                                                                                      |
| S&P 500 individual NASDAQ constituents (AAPL, MSFT, AMZN…) | EMPTY PLACEHOLDERS (dishonest absence)                    | `day-{D}/data_type-ohlcv_1m/equities/NASDAQ/{ID}.parquet` (legacy form), 79 instrument files on 2026-01-03 sample   | Sample-read of `NASDAQ:EQUITY:AAPL-USD.parquet` returned 0 rows with header-only schema. CLAUDE.md §"honest absence vs fake placeholders" — those 79 files look populated but are empty. NOT in manifest; NOT being live-captured. Out of scope for MVP. |
| MDPS processed_candles for tradfi                          | UNVERIFIED                                                | `processed_candles/` co-located in tradfi tick bucket                                                               | Per memory 2026-05-01, "5 dep-gated cells (delta-one × 4) wait on MDPS Phase 2 backfill of processed_candles 2024-01-01+"                                                                                                                                |
| VX futures term structure                                  | NOT SUPPORTED                                             | —                                                                                                                   | Databento adapter has no CFE/VX symbology; term structure dead unless added                                                                                                                                                                              |

## 3. Phased Execution DAG

```
Phase 0 (verify foundations) — PARALLEL, no blockers
        |
        v
Phase 1 (backfill blockers) — PARALLEL after Phase 0
        |
        v
Phase 2 (ML pipeline pre-reqs) — SEQUENTIAL after Phase 1
        |
        v
Phase 3 (feature wiring) — PARALLEL after Phase 2
        |
        v
Phase 4 (ML training MVP) — SEQUENTIAL after Phase 3
```

Each phase concludes with a QG gate; downstream phase cannot begin until the upstream phase's success criteria (§5) are
all green.

### Phase 0 — Verify Foundations (PARALLEL)

No dependencies between these probes; run as four parallel sub-agents.

- [x] [AGENT] P0. Sample-read 5 random ES futures `ohlcv_1m` parquets spanning 2020 / 2022 / 2024 / 2025 / 2026. Assert
      OHLC populated (no all-NaN rows), assert ≥390 bars per RTH day, assert `ts_event` monotonic. Same incident class
      as the 2026-05-05 MDPS empty-placeholder bug — counting rows is not validation; populate validation is. **Verified
      2026-05-05**: 2020-06-15 = 2,929 rows + 2022-06-15 = 2,952 rows + 2026-04-15 = 1,624 rows all OHLC-populated with
      sane open ranges [2918-3098, 3724-3852, 6992-7150]; 2024-06-15 NO-OBJECT (Saturday — no trading, correct);
      2025-06-15 = 247 rows (Sunday Globex evening session, correct partial). No silent placeholders surfaced.
- [x] [AGENT] P0. Sample-read 3 random VIX 15m parquets across distinct years. Assert `ts_event` monotonic + OHLC
      populated; volume=0 is expected for an index. **Verified 2026-05-05**: 2020-06-15 = 51 rows open[34.56-44.09]
      (post-COVID elevated), 2023-06-15 = 53 rows open[13.86-14.50] (calm), 2026-04-29 = 52 rows open[17.83-18.89]. All
      `instrument_key=CBOE:INDEX:VIX-USD`, volume=0 as expected.
- [x] [AGENT] P0. Confirm ES_OPT VM `tradfi-bf-es-opt-adhoc-adhoc-20260505-183009` is emitting hourly progress events
      with row counts to `gs://{pid}-events/events/...`. If no progress event in any hour partition, kill and diagnose
      per CLAUDE.md fire-and-forget rule. **Verified 2026-05-05 18:51Z**: VM RUNNING; hour=17 + hour=18 partitions
      exist; 515+ events including `RESOURCE_PROFILER_SAMPLE` heartbeats. Continue passive monitoring; re-check hour=19
      partition by 19:30Z to confirm forward progression.
- [x] [AGENT] P0. Probe `processed_candles/` for tradfi: list
      `gs://market-data-tick-tradfi-.../processed_candles/by_date/day=2024-06-15/asset_group=tradfi/...` across 5 sample
      dates (2020-06-15, 2022-06-15, 2024-06-15, 2025-06-15, 2026-04-15). Report whether ES candles exist per timeframe
      (1m / 5m / 15m / 1h / 1d); gate downstream feature work on this finding. **Verified 2026-05-05**:
      `processed_candles/` does NOT exist anywhere — neither under tradfi tick bucket nor in any standalone bucket
      (`gcloud storage buckets list --filter='name~processed'` returned nothing). UAC `canonical/gcs_paths.py` has no
      processed-candles entry. **Phase 1 MDPS backfill is now confirmed-required, not conditional.**

### Phase 0 verdict (2026-05-05)

ES futures OHLCV ✅ real, VIX 15m ✅ real, ES_OPT 2020-2022 fill VM ✅ healthy, MDPS processed_candles ❌ does not exist
for tradfi. Phase 1 MDPS backfill todo (P1) is hard-triggered. Phases 2-4 still gated on Phase 1 completion.

### Phase 1 — Backfill Blockers (PARALLEL)

Triggered conditionally on Phase 0 findings; sub-tasks within Phase 1 have no inter-dep and run in parallel.

- [~] [AGENT] P1. **IF** Phase 0 shows MDPS `processed_candles` missing for tradfi: launch MDPS backfill VM for ES +
  MES + VIX over 2020-01-01 → 2026-05-05. Pair the launch with active event-stream verification (90s STARTED check,
  hourly progress-event check, STOPPED on shutdown) per CLAUDE.md no-fire-and-forget rule. **Launched 2026-05-05
  19:39Z**: 7 sharded VMs via `bash launch-mdps-sharded-backfill.sh tradfi` —
  `mdps-tradfi-{2020,2021,2022,2023,2024,2025,2026}-20260505-203928`, e2-standard-8 each in asia-northeast1-c,
  auto-shutdown on completion. All 7 verified RUNNING with `hour=19` event partitions emitting STARTED at the 90s check
  ✓. Each VM ~3-12h wallclock. Re-check at 2026-05-05 22:00Z for hourly progress events and at auto-shutdown for
  STOPPED + row counts. Post-completion: run
  `rebuild_manifest_from_canonical_paths('market-data-tick-tradfi-central-element-323112',      service_name='market-data-processing-service', prefix='processed_candles/by_date')`
  for manifest reconciliation.
- [~] [AGENT] P1. Tradfi phantom-audit + manifest-rebuild. Port the CeFi 2026-05-04 pattern: invoke
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` first; surface
  uncatalogued legacy `category=tradfi` rows. Then a non-dry-run pass. Goal: drift < 1%. **Laptop run killed 2026-05-05
  20:49Z** after DNS resolution failures + 18× slow cross-region listing per CLAUDE.md. **Relaunched 2026-05-05 20:43Z
  on same-region VM**: `tradfi-audit-aggregate-20260505-204345` in asia-northeast1-c, e2-standard-8, custom startup
  script. Bundled task: phantom-audit dry-run + aggregate_legacy_es_opt_trades.py dry-run smoke (5 days) + full
  2020-2022 aggregation. Auto-shutdown on completion. Watchdog dict updated (deployment-service a682e23) with
  `tradfi-audit-aggregate-` prefix. VM emitting events at hour=20.
- [x] [AGENT] P1. Launcher hardening — make `VM_FORCE_WINDOW` configurable in
      `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` (currently hardcoded ~line 196). Add a
      `--no-force-window` flag and a top-of-file comment block pointing at this plan. **Shipped 2026-05-05**
      (uncommitted): `FORCE_WINDOW=true` default + `--no-force-window` arg-parser case + usage string update + comment
      block referencing this plan; `bash -n` syntax-clean.
- [~] [AGENT] P1. **ES options legacy-trades aggregation** — **DRAFTED 2026-05-05** (uncommitted) at
  `instruments-service/scripts/aggregate_legacy_es_opt_trades.py`, ~334 lines, syntax-clean. Awaiting same-region VM
  run + post-write sample-read validation. The script walks
  `gs://market-data-tick-tradfi-{pid}/raw_tick_data/by_date/day=*/category=tradfi/venue=CME/instrument_type=future/data_type=trades/`
  across 2020-01-01 → 2022-12-31 (~939 day partitions, ~503 per-strike files/day, ~470K files total). For each day,
  group per-strike `*.parquet` by chain root via Databento parent-symbology (E1A*,E2A*,E3A*,E4A*,E5A* → EW1*..EW5*; EW*
  → EW; ES*,EOM* via expiry-week mapping), concat the per-strike Databento-trade rows, write chain-bundled to canonical
  `day={D}/asset_group=tradfi/venue=CME/instrument_type=options_chain/data_type=trades/underlying={ROOT}/ticks.parquet`,
  then `record_captured(...)`. Path correction matters: legacy is path-misclassified as `instrument_type=future` — must
  rewrite to `options_chain`. Aggregation, not re-fetch — Databento trades-for-options quota was the original reason
  this data was skipped; it has now been paid for and just needs re-shape. Estimate: 1 day to write + test, 2-4 hours to
  run on a same-region asia-northeast1-c VM. **Same script handles ohlcv_1m legacy migration** for the 2024 dates where
  per-strike `E1AG4_C4800_migrated_*.parquet` files exist at `instrument_type=future/data_type=ohlcv_1m/` — those should
  aggregate to `instrument_type=options_chain/data_type=ohlcv_1m/underlying={ROOT}/ticks.parquet`. Sample-read
  post-aggregation: assert single `ticks.parquet` per shard, assert OHLC populated (ohlcv) or trade-rows populated
  (trades) — applied per honest-absence rule.

### Phase 2 — ML Pipeline Pre-Reqs (SEQUENTIAL after Phase 1)

These three items must land in order — continuous-series stitcher feeds ML CLI registration which feeds the
`FUTURES_ROLL` event hook.

- [x] [AGENT] P2. Register ES + MES + VIX in `ml-training-service` `cli/parser.py`. Currently only SPY is wired (per
      `cme_sp_ml_signal_preaudit_2026_04_20.md` B3). Add CLI `--symbol ES`, `--symbol MES`, `--symbol VIX` and the
      corresponding reference-data lookups. **Shipped 2026-05-05 (a21e9ed)**: ES + ES_FRONT + SPY were already
      registered; added MES (`CME:FUTURE:MES-20260619`), MES_FRONT (`CME:CONTINUOUS:MES`), VIX (`CBOE:INDEX:VIX-USD`) to
      `INSTRUMENTS["TRADFI"]` + `INSTRUMENT_ID_MAP` + `ALL_INSTRUMENTS`. Added `CBOE` prefix to
      `get_asset_group_for_instrument` so canonical VIX ids resolve to TRADFI. Smoke-tested via in-process import.
- [ ] [AGENT] P2. Build continuous-series stitcher for ES (rolled futures) at
      `market-tick-data-service/scripts/build_continuous_es.py` plus unit tests. Required for any training window > 90
      days (single contract = ~3 month lifespan). Operator-input gated on the contract-roll method (see §7 Q1). Same
      scaffold applies to MES.
- [ ] [AGENT] P2. Add `FUTURES_ROLL` event emission in `strategy-service` ML engine whenever the continuous series rolls
      to the next contract (per `cme_sp_ml_signal_preaudit_2026_04_20.md` B5). Event schema lives in UAC
      `unified_api_contracts.events`; do not local-define.

### Phase 3 — Feature Wiring (PARALLEL after Phase 2)

Four independent feature streams; run as four parallel sub-agents. Each stream emits manifest rows with
`capture_status=captured` and validates via sample-read.

- [~] [AGENT] P3. Run `features-calendar-service` for tradfi over 2020-01-01 → 2026-05-05. Asset-group-agnostic — no
  candle dependency. Output: temporal + economic_events (NFP / CPI / FOMC). Validate: at least one row per RTH day with
  non-empty `event_type` set. **Launched 2026-05-05** (3rd attempt): VMs v1 + v2
  (`features-calendar-tradfi-backfill-2026050{5-213713,5-214105}`) crashed with FRED API 500 on `release_id=10` (CPI)
  because the FRED retry/fallback had a bug — `httpx.HTTPStatusError` was not in the catch-tuple, so 5xx propagated
  unhandled. Fixed by features-calendar-service `5e5aa05`: 3-retry exponential backoff in `_request_fred_release` +
  `httpx.HTTPError` added to outer except so service falls back to schedule-based dates on persistent FRED failure. VM
  v3 `features-calendar-tradfi-backfill-20260505-215632` RUNNING with `PROCESSING_STARTED` on `time_features` calculator
  at 20:58:56Z — past the FRED step. Tarball refreshed pre-launch.
- [ ] [AGENT] P3. Run `features-delta-one-service` for tradfi/ES across all 36 calculators (TechnicalIndicators,
      MovingAverages, Oscillators, Momentum, VWAP, Returns, MarketStructure, FuturesBasis, etc.). Validate: each
      calculator's output parquet sample-read shows populated values, not NaN-everywhere.
- [ ] [AGENT] P3. Run `features-volatility-service` for tradfi/ES + tradfi/CBOE-VIX — realized-vol + skew calculators
      against ES OHLCV. Validate: realized-vol values in a sane range (annualized 5–60%) on a sample week.
- [ ] [AGENT] P3. Write VIX-specific feature calculator (level, contango proxy via VIX 1m vs 1h reconstruction,
      vol-of-vol). Net-new — not in any existing calculator class. Land in `features-volatility-service`
      (volatility-themed). Add unit tests and a feature-catalog entry per the runtime catalog SSOT (NOT the stale YAML —
      see 2026-05-05 features-sports memory).

### Phase 4 — ML Training MVP (SEQUENTIAL after Phase 3)

- [ ] [AGENT] P4. Smoke `ml-training-service` against a 1-month ES window. Confirm features land in the feature store
      and the model trains end-to-end without errors. This is the first integration check that Phases 0-3 hang together.
- [ ] [AGENT] P4. Run full backtest 2020-01-01 → 2024-12-31 (train) / 2025-01-01 → 2026-05-05 (test). Use the existing
      `strategy-service` Group B runner. Operator decides walk-forward vs single split (§7 Q2).
- [ ] [AGENT] P4. Inspect outputs: train/test split sizes, feature importance ranking (top 20), OOS Sharpe, max
      drawdown, hit rate. Write summary into the plan as a §8 "Results" appendix.

## 4. Out-of-Scope for MVP, Captured for Later

These are deliberately deferred. Each has a gating condition; do not add to MVP scope.

- [ ] [DEFERRED] Implied-vol skew from ES_OPT chain — gated on Phase 0 ES_OPT 2020-2022 backfill completion AND ES
      options ohlcv_1m landing at the canonical `instrument_type=options_chain` path.
- [ ] [DEFERRED] VX futures term structure — gated on Databento adding CFE/VX support OR sourcing direct CBOE feed.
- [ ] [DEFERRED] Individual S&P 500 constituent stocks — gated on canonical NASDAQ + NYSE equity backfill at scale (need
      full 500 + canonical-path migration; 79 instruments at legacy path is partial).
- [ ] [DEFERRED] MES options — gated on Databento providing MES options or accepting it's not in MVP scope.
- [ ] [DEFERRED] Yahoo Finance manifest cleanup — 2,211 abandoned `empty_confirmed` rows under `venue=YAHOO_FINANCE`.
      Low-priority noise.

## 5. Success Criteria (per phase)

### Phase 0 complete

- All four bullets in §3 Phase 0 marked `- [x]`.
- No silent-empty parquets surfaced; if found, raise to Phase 1 immediately and treat as a 2026-05-05-class incident
  (manifest says `captured`, parquet is garbage).
- Documented finding for `processed_candles` tradfi coverage written into this plan.

### Phase 1 complete

- MDPS `processed_candles` for ES populated 2020-2026 (or determined to be unnecessary for tradfi if Phase 0 shows
  existing coverage).
- Tradfi phantom audit shows < 1% drift after reconciliation pass.
- `launch-tradfi-backfill-vm.sh` accepts `--no-force-window` flag; merged on `live-defi-rollout`; QG green on
  `deployment-service`.
- ES options legacy trades aggregation complete: one chain-bundled `ticks.parquet` per (date, chain root) at canonical
  `instrument_type=options_chain/data_type=trades/underlying={ROOT}/` for 2020-01-01 → 2022-12-31; manifest rows
  recorded; sample-read validates populated trade rows. Same pass aggregates legacy 2024 per-strike ohlcv_1m files at
  the wrong `instrument_type=future` path into canonical chain shape.

### Phase 2 complete

- `ml-training-service` CLI accepts `--symbol ES` / `--symbol MES` / `--symbol VIX`; unit tests cover all three.
- Continuous ES series file exists at the agreed canonical location with ≥ 1,500 trading days; `FUTURES_ROLL` events
  emit cleanly on roll boundaries.
- QG green on `ml-training-service`, `market-tick-data-service`, `strategy-service`.

### Phase 3 complete

- `features-calendar`, `features-delta-one`, `features-volatility` all have manifest rows `capture_status=captured` for
  tradfi/ES/CBOE-VIX.
- Sample-read validation (NOT row count) shows populated values per calculator — applied at every shard boundary per the
  honest-absence rule.
- VIX-specific calculator merged with unit tests and feature-catalog entry.

### Phase 4 complete

- Model trains end-to-end on 1-month smoke window with no errors.
- Full 2020-2024 train / 2025-2026 test backtest produces OOS metrics.
- Results appendix added to this plan with feature-importance top-20, OOS Sharpe, max drawdown, hit rate.
- Workspace-wide QG run on every affected repo (`market-tick-data-service`, `features-delta-one-service`,
  `features-calendar-service`, `features-volatility-service`, `ml-training-service`, `strategy-service`,
  `deployment-service`, `instruments-service`) all green.

## 6. Cross-References

- `cefi_tradfi_tick_data_backfill_2026_04_10.md` — parent: backfill operations and VM launcher patterns.
- `cme_sp_ml_signal_preaudit_2026_04_20.md` — parent: ML preaudit findings; B2 / B3 / B5 are pulled into Phase 2 here.
- `data_pipeline_completion_2026_04_18.md` — parent: MDPS Phase 5b `processed_candles` backfill scope.
- `instruments_and_market_tick_data_completion_2026_05_01.md` — parent: instrument scope decisions including ES / MES /
  VIX universe membership.

## 7. Open Questions for Operator

Decisions Iggy needs to make before Phase 4 kicks off:

1. **Continuous-series stitcher**: contract-roll method — **DECIDED 2026-05-05: back-adjust (Panama Canal)**. At each
   roll, compute spread = `front_new_close − front_old_close`, subtract that spread from ALL historical front_old
   prices. Returns/log-returns/vol calcs stay correct; level becomes hypothetical. Industry standard.
2. **Train/test split**: walk-forward with monthly rebalance, or single 80/20?
3. **Target variable**: next-1m return, next-15m return, or next-day directional?
4. **Acceptable feature lag**: 1 bar (1m) or larger (5m / 15m) to reduce noise?
5. **Universe**: ES alone, ES + MES (cross-contract beta), or ES + IBIT + VIX (mixed-instrument feature blend)?

## 8. Q4 — How does this work LIVE? (architecture)

Answers the "how do we account for the roll, sustainably for live + backtest" question. The architecture has FOUR layers
cleanly separated; the roll is handled at the strategy translation layer, not in the ML signal.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER A — TRAINING / SIGNAL (offline + live)                              │
│   Input:   continuous_es.parquet (back-adjusted, derived from MDPS)       │
│   Output:  generic signal — "long/short S&P exposure"                     │
│   Knows:   nothing about specific contracts                                │
│   Owner:   ml-training-service (offline) + ml-inference-service (live)    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER B — STRATEGY-SERVICE (translation)                                  │
│   Maps "long S&P" → "long {current front-month ES contract}"              │
│   Reads SSOT: `processed_candles/_continuous/ES/_meta/active_contracts`    │
│       — date → (active_contract_id, roll_spread, prev_contract_id)        │
│   Emits FuturesRollInstruction on roll boundaries                         │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER C — EXECUTION-SERVICE                                               │
│   Live:     real fills on ACTUAL contract (e.g. ESM6)                     │
│   Backtest: matching engine reads ACTUAL contract OHLCV (NOT adjusted)    │
│   On FUTURES_ROLL: close old + open new = calendar-spread trade           │
│       Real cost: ~1-3 ticks slippage on the spread × $12.50/tick × Nlots  │
│   Same code path for batch + live (CLAUDE.md "Batch = Live" rule)         │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER D — POSITION-BALANCE-MONITOR                                        │
│   Tracks per-CONTRACT positions: ESH6: +5, ESM6: 0                        │
│   After roll: ESH6: 0, ESM6: +5; reconciles with broker                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Where back-adjust lives**: NOT in MDPS (MDPS is a per-contract candle generator), NOT in features-\* (those consume
continuous data). Cleanest fit: extend MDPS with a `--operation build-continuous` mode that runs AFTER standard candle
generation. Output at canonical path:

```
processed_candles/by_date/day={D}/timeframe={tf}/data_type={dt}/
    instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet
```

Plus a sidecar mapping `(date → active_contract_id, roll_spread, prev_contract_id)` at:

```
processed_candles/_continuous/{ROOT}/_meta/active_contracts.parquet
```

This SSOT is read by both strategy-service (to translate signals to actual contracts) AND execution-service's matching
engine (to charge the calendar-spread roll cost on the right dates).

**Three failure modes if this is wired wrong** (must be guarded by tests):

| Failure mode                                                                                           | Test that catches it                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backtest uses back-adjusted price for fills (P&L is fictional, includes phantom roll spread as profit) | matching-engine integration test: simulate a 6-month strategy across one roll, assert backtest P&L matches sum-of-contract P&L within 1bp                           |
| Backtest forgets calendar-spread roll cost (strategy looks ~10-30bp/yr more profitable than reality)   | matching-engine unit test: on FUTURES_ROLL, assert at least N ticks slippage on the spread leg                                                                      |
| Live system uses back-adjusted price as execution reference (orders fill at wrong levels)              | strategy-service integration test: mock continuous series + active_contracts SSOT, assert order venue/symbol = active_contract_id, not the continuous-series symbol |

**What's done vs pending**:

| Component                                                       | Status                                  | Where                                                                       |
| --------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------- |
| `FuturesRollInstruction` schema in UAC                          | ✅ exists                               | `unified_api_contracts/internal/domain/strategy_service/instruction.py:803` |
| `FUTURES_ROLL` enum in InstructionType                          | ✅ exists                               | `unified_api_contracts/canonical/domain/reference/__init__.py:28`           |
| Continuous-series builder (back-adjust) + active_contracts SSOT | ❌ Phase 1.6 todo (this plan)           |                                                                             |
| MDPS `--operation build-continuous` mode                        | ❌ Phase 1.6 todo (this plan)           |                                                                             |
| Strategy-service emits FUTURES_ROLL on roll                     | ❌ Phase 2.3 todo                       |                                                                             |
| Execution-service matching engine charges roll cost             | ❓ Phase 1.7 audit todo (this plan)     |                                                                             |
| Position-balance-monitor per-contract tracking                  | ✅ already does this for crypto futures | structurally same for ES                                                    |

## 9. New Phase 1 todos (back-adjust + chain-bundle + tests + migrations)

Surfaced from Q4 architecture review and operator request 2026-05-05. All gated on Phase 0 completion (which is done)
but parallel-able among themselves.

- [x] [AGENT] **P1.5 ES options chain-bundle MDPS output** — **SHIPPED 2026-05-05**: New shared helper
      `market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py` exposes
      `is_chain_bundle_data_type(data_type)` +
      `build_processed_candle_path(prefix, venue, instrument_id, data_type, underlying)`. Wired into all 5 MDPS write
      paths: `candle_write_mixin._build_candle_output_path`, `data_sink._build_candle_output_path`,
      `output_writer_service._build_candle_output_path`, `orchestration_writer._resolve_output_path`,
      `io/writer.write_candles`. SSOT chain-types frozenset re-exported via UAC facade
      `unified_api_contracts.gcs_paths.CEFI_CHAIN_INSTRUMENT_TYPES` (`{"options_chain", "futures_chain"}`). When
      `data_type ∈ chain types`, the per-strike `_process_chain_timeframe`-aggregated candles_df now lands at
      `…/underlying={ROOT}/ticks.parquet` (one bundle per date+root) instead of being mis-named after the FIRST strike's
      instrument_id. 17 unit tests cover the rule including UAC contract parity, idempotency across strike ids,
      no-strike-leak. Existing 27 path-related tests still pass — no regressions.
- [~] [AGENT] **P1.5b Migrate existing per-strike processed_candles to chain-bundle** — Script ready. After P1.5 lands,
  write `instruments-service/scripts/aggregate_processed_options_to_chain_bundle.py` that walks
  `gs://market-data-tick-{cefi,tradfi}-{pid}/processed_candles/by_date/day=*/timeframe=*/data_type=*/venue=*/CME:OPTION:*.parquet`
  groups by chain root + (date, timeframe, data_type), writes bundled at canonical path, `record_captured` via
  ManifestWriter. Idempotent. Same skip-if-exists pattern as the raw-tick aggregator.
- [x] [AGENT] **P1.5d OOM remediation SHIPPED 2026-05-06 09:30 UTC** — full hybrid plan executed: - **Step 1**:
      deployment-service `3c55fc7` made `MACHINE_TYPE` configurable on the launcher; killed the 5 still- OOM-bound
      e2-standard-8 VMs (work preserved by skip-if-exists) and relaunched 7 fresh shards on `e2-highmem-8` (64GB) →
      unblocked Phase 1 progress immediately. - **Step 2 (helper)**: market-data-processing-service `918f66a` added
      `_iter_chain_symbol_dfs` (lazy per-symbol streamer via Polars predicate pushdown against tmpfile) + hardened
      `_read_tick_data` with `low_memory=True` + explicit `del pl_df` (~30-50% peak reduction even on the eager path). -
      **Step 3 (wiring)**: market-data-processing-service `1dfae3b` wired the streamer into `_process_instrument_file`
      via `_chain_bundle_likely_from_path` path-only detector + `_maybe_dispatch_chain_streaming`. The new
      `_process_chain_bundle_streaming` orchestrates per-symbol dispatch, accumulates per-tf candles across symbols,
      writes ONE `ticks.parquet` per timeframe via the P1.5 chain-bundle path helper. Peak memory ≈ largest
      single-symbol slice + per-tf accumulator (small), NOT the whole bundle. 11 unit tests cover yield count, slice
      purity, auto-detect priority, fallback paths, single-download invariant, tmpfile cleanup, path-only detection.
      Refactored 4 helpers to keep both `_process_chain_bundle_streaming` and `_process_instrument_file` under ruff C901
      complexity ≤ 15. - **Step 4**: refreshed TRADFI tarball at 08:26 UTC with the streaming code; killed the 7
      e2-highmem-8 VMs; relaunched 7 fresh shards on default `e2-standard-8` (32GB) at 09:29 UTC as
      `mdps-tradfi-{2020..2026}-20260506-092945`. Cost back to default. Verification scheduled at +10min.
- [ ] [AGENT] **P1.5d-original (legacy framing — kept for context)** — **2026-05-06 06:00-08:00 UTC**: of the 7 sharded
      VMs `mdps-tradfi-{2020..2026}-20260506-005356`, **2 OOM'd** during legacy options-chain processing: -
      `mdps-tradfi-2026`: exit=137 (SIGKILL/OOM) at 00:27 UTC after 18/126 days (14% YTD). - `mdps-tradfi-2020`: dead at
      06:35 UTC after 31/365 days (8%); final event `MEMORY_THRESHOLD_REACHED`; no EXIT_STATUS file (killed before
      vm-exec finalised). - Last log before death: `Detected legacy ticks.parquet bundle: 4053 symbols in ticks.parquet`
      → MDPS loads entire bundle into one Polars DataFrame → 32GB RAM (e2-standard-8) exhausted.

      **Live VMs at 07:42 UTC** (2021-2025) have done 12-22% each; likely heading for same OOM as they reach
              options-heavy days (2024 ES_OPT chain especially).

              **Remediation options** (next-session decision-gate, BEFORE Phase 2.3/3/4 work):
              1. **Bigger VM**: e2-highmem-8 (64GB) or e2-standard-16 (64GB). Cheaper engineering, 2× cost, may still OOM
                 on the heaviest days. Edit `launch-mdps-sharded-backfill.sh` `MACHINE_TYPE`.
              2. **MDPS streaming refactor**: split the legacy-bundle reader to process per-symbol, never holding the
                 whole bundle. Cleaner long-term, ~1-2 day engineering effort. SSOT: MDPS
                 `app/core/live_workers.py::_process_chain_timeframe_by_symbol` already iterates per-symbol — but the
                 upstream `_read_tick_data` loads the whole parquet first. Fix the read to lazy-stream via Polars
                 `scan_parquet`.
              3. **Hybrid**: fix #2 for legacy bundles, ship now on e2-highmem-8 to unblock backfill in parallel.

              **Phase 1 success-gate is NOT met** until processed_candles populated for ≥95% of 2020-2026 trading days.
              Phase 2.3 / Phase 3 / Phase 4 are HARD-BLOCKED until then.

- [x] [AGENT] **P1.5c Re-launch MDPS tradfi backfill with chain-bundle fix** — **DONE 2026-05-06**: 7 zombie
      `mdps-tradfi-{2020..2026}-20260505-203928` VMs killed (silently zombied 6+h after 2026-05-05 23:06 UTC last event
      — exactly the no-fire-and-forget pattern from CLAUDE.md). Refreshed tarball
      `bash scripts/vm/create-code-tarballs.sh --asset-group TRADFI` (used `/opt/homebrew/bin/bash` for bash 5; shipped
      `mdps`/`mtds`/`uac`/`utl` tarballs at 23:14Z bundling chain-bundle fix e5ee88e). Relaunched 7 fresh sharded VMs
      `mdps-tradfi-{2020..2026}-20260506-001446` (run-ts=20260506-001446). All 7 RUNNING per
      `gcloud compute instances list --filter="labels.run-ts=20260506-001446"` at 00:16 UTC. Decision: pre-stalled VMs
      were <2% done (only 2024 had legacy migrated output, 2020/2026 nothing) — kill-and-relaunch was strictly faster
      than letting them resume.
- [x] [AGENT] **P1.6 Continuous-series builder (back-adjust)** — **SHIPPED 2026-05-05 market-tick-data-service
      `133cfb4`**: `scripts/build_continuous_es.py` + `tests/unit/scripts/test_build_continuous_es.py` with 10 passing
      unit tests covering: business-day shift, roll-date pairing, active-contracts table, reverse-walk shift
      accumulation, 2-contract Panama-canal correctness (returns continuous, no phantom jump), idempotency, roll
      metadata persistence, volume-not-adjusted, canonical contract-id format, honest-absence on missing roll-day data.
      Pure-function core (no GCS) so testable without infra. CLI wrapper writes per-day continuous parquet + sidecar
      SSOT for strategy-service / execution-service. NOTE: Implemented as a one-off script in
      `market-tick-data-service/scripts/` rather than MDPS `--operation build-continuous` mode — same correctness, can
      be promoted to MDPS native operation later when scope allows. Future agents: also add MDPS
      `--operation     build-continuous` mode that wraps this script's core for canonical pipeline integration.
- [ ] [AGENT] **P1.6-original Continuous-series builder (back-adjust) — superseded by above** — Add MDPS
      `--operation build-continuous` mode that reads per-contract processed_candles + roll calendar from
      `instruments-service`, applies Panama-canal back-adjust, writes: -
      `processed_candles/by_date/day={D}/timeframe={tf}/data_type={dt}/instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet` -
      sidecar SSOT `processed_candles/_continuous/ES/_meta/active_contracts.parquet` mapping
      `(date →       active_contract_id, roll_spread, prev_contract_id)` - Same shape for MES. - Unit tests: (a) two
      contracts with known cross-day spread → assert post-adjust returns are continuous, no jump on roll day; (b)
      `roll_spread` correctly computed and persisted; (c) idempotent — re-running on same data produces byte-identical
      output.
- [x] [AGENT] **P1.7 Matching-engine roll-cost audit** — **SHIPPED 2026-05-05**: Audit verdict — handler at
      `execution-service/execution_service/engine/handlers/futures_handler.py` correctly charges 3bps calendar-spread
      slippage on roll execution AND a 2-leg trading fee (close near + open far). Fills come from
      `instruction.benchmark_price` directly — back-adjust translation is the strategy/Layer-B caller's responsibility,
      NOT the matching engine's (architecturally clean per Q4 §8). Added: `DEFAULT_ROLL_SPREAD_BPS = 3` +
      `ROLL_SPREAD_BPS_BY_VENUE` per-venue table (CME/ICE = 3bps, BINANCE/BYBIT/OKX/DERIBIT = 8bps) +
      `_resolve_roll_spread_bps(venue)` helper. 4 new regression tests in `test_instruction_handlers.py`: (a) CME ES
      roll asserts slippage > 1 ES tick (0.25 pts); (b) 2-leg fee assertion; (c) crypto > CME slippage; (d) handler
      price-source-agnosticism (same bps applied at any benchmark_price). All 7 FuturesRollHandler tests pass.
- [x] [AGENT] **P1.8 Tests for the FUTURES_ROLL emission path (Phase 2.3 prereq)** — **SHIPPED 2026-05-05**: New
      `strategy-service/strategy_service/engine/futures/roll_emitter.py` — pure-function Layer-B helper. Reads the
      `active_contracts.parquet` SSOT (rows shaped per `build_continuous_es.attach_roll_metadata`) and decides whether
      to emit a `FuturesRollInstruction`. API: `is_roll_boundary(row)` → bool;
      `evaluate_roll(row, current_amount,     current_direction)` → `RollDecision`;
      `build_roll_instruction(decision, strategy_id, timestamp, venue)` → UAC `FuturesRollInstruction`. 16 unit tests in
      `tests/unit/test_roll_emitter.py` cover: pre-roll/on-roll/post-roll boundary detection, FLAT-position no-op,
      SHORT-position roll with absolute amount, time-series sweeps with one and two roll boundaries asserting EXACTLY
      ONE FuturesRollInstruction per boundary, UAC instruction construction with correct prev/new contract ids,
      defensive guards on partial RollDecision.
- [x] [AGENT] **P1.9 Workspace-wide QG sweep after P1.5-P1.8 land** — **DONE 2026-05-05**: Per-repo QG sweep on
      `market-data-processing-service` (P1.5, P1.6), `execution-service` (P1.7), `strategy-service` (P1.8),
      `ml-training-service` (P2.2), `unified-api-contracts` (CEFI_CHAIN_INSTRUMENT_TYPES facade re-export). All affected
      code lint-clean + typecheck-clean + codex-tolerant + new-tests-pass. Pre-existing failures NOT in scope: MDPS
      `test_force_flag_bypasses_manifest_lookup_skip` TypeError on stash-checked baseline (sports odds reprocess),
      ml-training E501 in unrelated parser/config/validator lines, UAC E501 in unrelated venue_mapping em-dash
      docstring, PM validator broken-link in unrelated `sports_predictions_e2e_2026_05_05.md` — pre-existing on stashed
      baseline.
