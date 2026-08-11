---
doc_type: plan
title: MDPS+features reduced-artifact tracker — feature-complete candle as the portable unit
summary:
  Coordination tracker for the MDPS+features work that makes the processed candle a self-contained, no-look-ahead,
  MVP-scoped artifact (ticks stay on GCP; candles+features are what move) and smoke-tests honest coverage per
  AG×venue×data_type.
status: archived
nature: design
asset_group: [cefi, defi, tradfi, sports, prediction, cross-cutting]
stage: [data, features, backtest, execution, meta]
repos: [market-data-processing-service, features-service, unified-api-contracts, execution-service, e2e-testing]
scope: [engineer, admin]
tags: [mdps, features, reduced-data, candle, no-look-ahead, mvp, honest-coverage, smoke-test, cost, polars, egress]
related:
  [
    ../epics/mtds_mdps_master.md,
    ../epics/features_and_ml_master.md,
    ../epics/batch_live_symmetry_master.md,
    ../epics/execution_master.md,
  ]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
last_updated: 2026-06-28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [operator request 2026-06-28]
assigned_role: data_engineering
drift_direction: advance-code
---

# MDPS+features reduced-artifact tracker

> **✅ ARCHIVED (archived 2026-07-27)** — pure coordination tracker, 0 own todos. All 9 linked mini-plans confirmed
> archived/complete (Plans 1,2,3,4,5,6,7,8,9 all now in `plans/archive/2026_06/` or `plans/archive/2026_07/`, verified
> by direct file lookup 2026-07-27 — the table above was stale for 4 of the 9 rows, corrected in the same pass). Plan
> 6's `honest_coverage_smoke_harness` spawned one live follow-on issue
> (`/plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md`) which is actively tracked in
> `/plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md` and
> `/plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` — not orphaned. 0 orphaned scope remains.
> Per `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §2.

**Coordination tracker (not dispatched — `execution_scope: local-only`).** Draws the cross-plan DAG and codifies the two
new governing concepts. The actual work lives in the nine dispatched mini-plans below, each small + role-homogeneous +
one-agent-sized per `plans/PLAN_FORMAT.md` ("plans, not phases"). All born `status: draft`; flip the batch to `active`
together to green-light dispatch.

> **Corrected 2026-07-12 (plan-reconciliation findings 183, 188, 189, 190; §A2 B-queue ruling)** — the "all born
> `status: draft`, flip the batch together" framing above is stale for at least 4 of the 9 mini-plans, which
> independently progressed past this gate and reached `status: complete` on real shipped infra, with no trace of a
> coordinated batch-flip ever happening here (this tracker's own `status:` — see frontmatter — was never updated): Plan
> 1 `mdps_book_microstructure_precompute_columns` (complete 2026-07-10, market-data-processing-service@a90669be +
> unified-api-contracts@40e318aa), Plan 5 `tradfi_mdps_passthrough_dependency_gap` (complete 2026-07-10,
> market-data-processing-service@cc63d1b), Plan 7 `mdps_features_full_month_benchmark_binance` (complete 2026-07-10),
> Plan 8 `mdps_polars_engine_cost_sharpening` (complete 2026-07-12, market-data-processing-service@c7e0437 + 4 more
> commits). Plans 2/3/4/6/9 are NOT verified by this pass — their draft/dispatch status in the table below is left
> as-is. (was: "All born `status: draft`; flip the batch to `active` together to green-light dispatch" presented above
> as still-accurate for all nine mini-plans as of this tracker's own `last_updated: 2026-06-28`.) See each named
> mini-plan's own frontmatter `status:` + "Status-flip note" for the underlying evidence. This tracker's own
> `status: draft` / "not dispatched" framing is left unchanged here — that call is for whoever owns closing this
> tracker, not this pass.

> **2026-07-13 (MTDS/MDPS consolidation, `mtds_consolidation_foldin_mapping_2026_07_12.md`, operator ruling "Approve
> all + unlock")** — the 4 mini-plans flagged complete above are now formally **archived** (all 0 open todos): Plan 1
> `mdps_book_microstructure_precompute_columns`, Plan 5 `tradfi_mdps_passthrough_dependency_gap`, and Plan 7
> `mdps_features_full_month_benchmark_binance` moved to `plans/archive/2026_07/` as simple archives (nothing to fold —
> genuinely 0 residual work). Plan 8 `mdps_polars_engine_cost_sharpening` also archived to `plans/archive/2026_07/`,
> with its completion **credit folded into M-2** (`plans/active/mtds_file_size_refactor_2026_06_08.md` Progress Log)
> since it un-deferred M-2's parked Polars seam. This tracker itself is **KEPT** ("Keep as tracker" ruling) — it is a
> live 9-mini-plan coordination tracker spanning 4 parent epics, not a stub; Plans 2/3/4/6/9 (the other 5, living under
> `features_and_ml_master` / `batch_live_symmetry_master` / `execution_master`) are unaffected by this fold and remain
> tracked here as before. Re-visit this tracker's own closure once all 9 mini-plans resolve.

## The thesis (operator framing 2026-06-28)

- **Ticks never leave GCP.** All tick→candle work and feature calculation happen GCP-side. The **portable artifact is
  the MDPS candle output + features** (features are a function of candles, not ticks). AWS — and eventually live — is
  just a downstream consumer of that artifact; the egress saving is a free consequence of shipping candles, not ticks.
  So there is **no single "reduction floor" to pick**: where a product has ticks the candle is rich; where it only has
  candles (TradFi `ohlcv_1m`) or snapshots (DeFi) the candle is whatever the source supports.
- **One base candle, then aggregate UP.** MDPS builds the candle at the **most granular base timeframe the source
  allows** (15s where we have ticks; 1m where the source is already 1m, e.g. TradFi) and aggregates UP to coarser
  timeframes from that base — never down. The base granularity per data_type is a static UAC fact
  (`BASE_GRANULARITY_BY_DATA_TYPE`), not a guess.
- **The candle must be self-contained** — rich enough that no downstream consumer needs to reach back to ticks. The one
  thing that fails on a plain OHLCV bar (the ~100 book-microstructure features + CeFi L2 execution matching) is solved
  by **precomputing intra-bar book summaries into candle columns** (operator decision 2026-06-28), not by shipping book
  ticks.
- **Chain-bundle per-instrument sampling ALREADY exists (verified 2026-06-28).** For `options_chain`/`futures_chain`,
  MDPS already samples each strike/contract individually (keyed by `instrument_key`), dumps NaN + LOCF for empty
  intervals, and writes ONE `ticks.parquet` per underlying — parity with raw MTDS. Plan 1's book-column work must
  PRESERVE this; no rebuild.
- **No look-ahead is the heartbeat.** The job is to **detect whether a producer stamps the LEFT/open edge** (bar start)
  and convert to the RIGHT edge (`t_close` = when the bar actually closed) **only where it does** — if a source already
  stamps the close, there is nothing to adjust (no blind shift). This must hold through **features' RE-aggregation** too
  — when features resample/aggregate again, the result stays right-stamped. (MDPS store + the features resampler are
  already verified right-edge; the remaining audit surface is per-source ingestion edge + rolling windows / PIT joins /
  forward-fill.)

## Two new governing concepts

### MVP-for-MDPS = MVP-for-MDS

MDPS processes exactly the instruments-catalogue MVP capture universe that MDS already uses — **no separate screen**.
"What must MDPS cover" is derivable from the MDS/UAC MVP, not hand-maintained. (Plan 3 states it in UAC.)

### MVP-for-features (new contract — does not exist today)

Not every instrument gets features. Codified in UAC (Plan 3):

- **Options + dated futures → MDPS candles only, NO delta-one features** (delta-one rejects non-linear payoffs; already
  partially enforced via `NON_LINEAR_TYPES` in features-service).
- **Delta-one features computed on the most-liquid PERP representative per base, selected BY VOLUME.** Every MVP base
  has a perp (perp-gate rule), and perps are almost always the most liquid leg (higher OI via leverage) — so the feature
  representative is the highest-**volume** perp across available venues, **NOT spot**. The selector is **currently
  MISSING** (features process whatever venue is in the manifest); Plan 3 builds it on the existing
  `FeatureFamilyUniverseConfig`.
- **A separate most-liquid-SPOT selector (also volume-based) is for EXECUTION, not features** — built from venue volumes
  we already have. Plan 9 (execution) consumes it; Plan 3 exposes both selectors from the one UAC home.

## Honest-coverage smoke-test design (Plan 6 + Plan 7)

- **Discover, don't assume.** Classify every `(asset_group, venue, data_type, instrument)` from the availability
  manifest into **RUNNABLE** (continuous coverage over the required window) / **INSUFFICIENT-HISTORY** (partial window →
  must FAIL, never run partial) / **HONEST-EMPTY** (genuinely no data — handled, not a failure). Rides the existing
  4-state `capture_status` — no new bookkeeping.
- **Window length is product-shaped.** Sports/seasonal needs a long continuous instrument-and-market pipeline across
  seasons; some data types only need max-daily aggregation (a day is enough). The harness carries a
  required-window-per-(AG, data_type).
- **Goal:** one representative RUNNABLE shard per `(AG × venue × data_type)` so the code path is smoke-tested over the
  span it actually needs — and fails loudly where coverage is partial.
- **15s vs 1m fidelity is source-governed:** 15s is computed from raw ticks where we have them; a product with only 1m
  has a 1m floor. UAC declares what is possible; high/low-fidelity execution (Plan 9) chooses accordingly.
- **Timeframe is a PATH partition, so per-timeframe coverage is cheap** (`processed_candles/.../timeframe={tf}/...`) —
  but the availability-manifest **ShardKey does NOT carry `timeframe`** (it keys on AG / venue / instrument_type /
  data_type / instrument). On the raw TradFi side, granularity is encoded in the `data_type` name (`ohlcv_1m`). Plan 6
  reads the path partition for per-timeframe coverage and reconciles that MDPS emits one manifest row per timeframe
  without `timeframe` in the key.
- **Never class a granularity we could never produce as "missing."** UAC already declares the achievable floor
  (`BASE_GRANULARITY_BY_DATA_TYPE` + `get_valid_timeframes_for_data_type`): TradFi `ohlcv_1m` base = 1m, so a missing
  15s for TradFi is EXPECTED-ABSENT, **not** INSUFFICIENT-HISTORY; CeFi base = 15s; DeFi pool_state = 15m. The coverage
  classifier consumes this static UAC fact — finer-than-base timeframes are never gaps.
- **TradFi 1m is a passthrough-then-aggregate-up.** A 1m source becomes the 1m candle by column-reshape to the candle
  schema (right-edge), then aggregation to 5m/15m/1h/24h from that base (Plan 5).

## Cross-plan DAG

```
        ┌─────────────────────────── parallel, no prereqs ───────────────────────────┐
        │                                                                             │
  (1) mdps_book_microstructure_precompute_columns      (3) mvp_for_mdps_and_features_universe_uac
        │            │                                       │        │        │
        │            ▼                                        ▼        │        ▼
        │     (2) features_read_book_columns          (2)             │   (6) honest_coverage_smoke_harness
        │            │                                                 │        │
        ▼            │                                                 ▼        ▼
  (9) execution_fidelity_tiers_uac_governed  ◄──── (3)        (7) mdps_features_full_month_benchmark_binance ◄── (1),(6)
                                                                       ▲
  (4) features_no_lookahead_reaggregation_guard   (independent)        │
  (5) tradfi_mdps_passthrough_dependency_gap      (independent) ───────┘ (unblocks tradfi shards)
  (8) mdps_polars_engine_cost_sharpening          (independent; (7) measures current-vs-Polars)
```

**Dispatch-ready immediately (no prereqs):** 1, 3, 4, 5, 8 (parallel agents). **Gated:** 2 (←1,3), 6 (←3), 9 (←1,3), 7
(←1,6; capstone). Gating is via task-level `prereqs`, not `depends_on` (which only documents ordering + gates archival).

## The mini-plans

| #   | Plan                                        | Repo(s)          | Role          | Model                         | Parent epic                | Status (2026-07-13)                                                                                                                                                            |
| --- | ------------------------------------------- | ---------------- | ------------- | ----------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | mdps_book_microstructure_precompute_columns | MDPS, UAC        | data-pipeline | **Opus/xhigh**                | mtds_mdps_master           | ✅ ARCHIVED (simple, 0 open) → `plans/archive/2026_07/`                                                                                                                        |
| 2   | features_read_book_columns_not_snapshots    | features         | data-pipeline | Sonnet                        | features_and_ml_master     | ✅ ARCHIVED (complete, 0 open) → `plans/archive/2026_07/`                                                                                                                      |
| 3   | mvp_for_mdps_and_features_universe_uac      | UAC              | backend       | **Opus**                      | features_and_ml_master     | ✅ ARCHIVED (complete, 6/6 shipped uac@6bcff215) → `plans/archive/2026_06/`                                                                                                    |
| 4   | features_no_lookahead_reaggregation_guard   | features         | data-pipeline | Sonnet                        | batch_live_symmetry_master | ✅ ARCHIVED (complete, 0 open) → `plans/archive/2026_07/`                                                                                                                      |
| 5   | tradfi_mdps_passthrough_dependency_gap      | MDPS             | data-pipeline | Sonnet                        | mtds_mdps_master           | ✅ ARCHIVED (simple, 0 open) → `plans/archive/2026_07/`                                                                                                                        |
| 6   | honest_coverage_smoke_harness               | e2e-testing, UAC | data-pipeline | **Opus** design / Sonnet impl | batch_live_symmetry_master | ✅ ARCHIVED (complete, 0 open) → `plans/archive/2026_07/`; live follow-on tracked separately in `/plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` |
| 7   | mdps_features_full_month_benchmark_binance  | MDPS, features   | data-pipeline | Sonnet run / Opus analysis    | mtds_mdps_master           | ✅ ARCHIVED (simple, 0 open) → `plans/archive/2026_07/`                                                                                                                        |
| 8   | mdps_polars_engine_cost_sharpening          | MDPS             | data-pipeline | **Opus/xhigh**                | mtds_mdps_master           | ✅ ARCHIVED, credit folded → M-2 `mtds_file_size_refactor_2026_06_08.md`                                                                                                       |
| 9   | execution_fidelity_tiers_uac_governed       | execution, UAC   | backend       | **Opus**                      | execution_master           | ✅ ARCHIVED (complete, 6/6 done) → `plans/archive/2026_07/` (frontmatter `status:` field stale, left as-is — content-verified)                                                 |

**Verified 2026-07-27 (`/plan-vintage-audit` archival pass)**: all 9 mini-plans confirmed archived/complete or actively
tracked elsewhere (Plan 6's live-verify residual). 0 orphaned scope remains — tracker archived, see banner below.

## Prior art folded in (do not re-derive)

- **MDPS efficiency + engine audits (2026-05-28)** — pure-Polars beats current Polars→Pandas→Polars **3× wall / 5× peak
  RSS / 7.8× retention**; ~15 GB arena leak on multi-day runs. Powers Plan 8.
  (`plans/audit/results/mdps_*_2026_05_28.md`)
- **`mtds_file_size_refactor_2026_06_08.md` (M-2, DEFERRED)** — holds the pandas→polars seam Plan 8 un-defers.
- **`bar_edge_left_vs_right_remediation_2026_06_08.md`** — right-edge `t_close` invariant + the features resampler fix
  (`closed/label="right"`); Plan 4 extends the guard surface.
- **Issue `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` (P0)** — Plan 5 closes it.
- **UAC `mvp_scope.py` v10 + `features_mvp_universe.py`** — Plan 3 builds the most-liquid-spot selector on top.
- **`/codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`** — egress $ inputs for Plan 7's cost model.
