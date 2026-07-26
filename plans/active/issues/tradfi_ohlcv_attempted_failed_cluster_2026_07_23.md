---
doc_type: issue
title:
  "TradFi DP_RUN_MOSTLY_EMPTY cluster (2026-07-22 23:46-48Z, ohlcv_1s 25.7% / ohlcv_1m 11.3% / ohlcv_15m 100.0%) — THREE
  distinct verdicts: ohlcv_1s/ohlcv_1m are a real, large, still-open Databento silent-zero-row gap
  (WithinBoundsTradfiSourceZero, CME-dominant); ohlcv_15m is 100% dead CBOE residue frozen since 2026-07-07, already
  diagnosed + deliberately deferred, re-firing only because the 2026-07-15 re-nag cooldown is working as designed"
summary: >-
  Investigated a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` CRITICAL batch (window 2026-07-22 23:46-48Z) against
  `market-data-tick-tradfi-prd-central-element-323112`: `ohlcv_1s` (224,204/871,498 attempted_failed, 25.7%), `ohlcv_1m`
  (81,220/721,535, 11.3%), `ohlcv_15m` (1,242/1,242, 100.0%). Live-queried the manifest index directly (single-file
  read, not a corpus walk) and confirmed all three counts match the alert EXACTLY. Two distinct root causes, not one:
  (1) `ohlcv_1s`/`ohlcv_1m` are 99.9% `error_reason=WithinBoundsTradfiSourceZero` — a real, intentional classification
  (not a bug) applied by the tradfi manifest rebuild's CF-11 honest-absence pass when a historical
  `empty_confirmed[SOURCE_RETURNED_ZERO]` row falls on a genuine trading day: Databento's OHLCV fetch silently returned
  zero rows for a real trading day, so the row is honestly surfaced as a failure instead of papered over. Concentrated
  in CME (75% of the ohlcv_1s population) / NASDAQ / NYSE, small CBOE tail; every row has a DISTINCT `attempted_at`
  spanning 2026-07-07 to 2026-07-21 (this is CF-11 rebuild-run time, not necessarily original fetch time). This exact
  silent-zero-row phenomenon was independently investigated in `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`,
  which ruled out every local guard and confirmed via a live Databento diagnostic that real data DOES exist for at least
  one sampled (venue, date) when queried with the registry's exact parent-symbol shape — but that investigation's actual
  fix only closed a SMOKE-CHECKER false negative (`--instrument-ids` filter bug), explicitly leaving the real production
  gap "tracked elsewhere" and never actually root-caused at the per-request level. Comparing to a 2026-07-07 snapshot
  (`tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`: ohlcv_1s attempted_failed=227,148, ohlcv_1m=91,547)
  the population has shrunk only modestly (-1.3% / -11.3%) in 16 days — real but slow progress, bulk still open. This is
  the genuine, still-unresolved, P1 data gap. (2) `ohlcv_15m` is a DIFFERENT, DEAD cell: 100% venue=CBOE, 100%
  `WithinBoundsTradfiSourceZero`, and EVERY one of the 1,242 rows shares `attempted_at` inside the exact
  2026-07-07T06:40:00Z-07:29:16Z single-batch window with zero newer activity in the 16 days since. This is the SAME
  1,242-row CBOE residue already fully diagnosed in
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`: CBOE's `ohlcv_15m`
  expected-coverage entry was stale drift from a since-removed Yahoo VIX-cash-index path, narrowed out of expected
  coverage 2026-07-15 (`unified-api-contracts@78b9e899`) to stop new attempts, but the 1,242 historical rows were
  explicitly left un-purged as a deferred follow-up. The alert keeps re-firing not because anything is newly broken, but
  because `check_high_attempted_failed` counts the WHOLE manifest history for the cell with no recency window, and the
  shipped re-nag cooldown (`DP_RUN_MOSTLY_EMPTY: 1800s`, `alerting-service@fe76ded3`, 2026-07-15) is deliberately
  designed to keep re-paging every 30 minutes while a cell stays "high" — which a dead, never-purged cell will do
  forever. Not a new incident.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service, alerting-service]
scope: [engineer, admin]
tags:
  [
    tradfi,
    databento,
    ohlcv,
    ohlcv_1s,
    ohlcv_1m,
    ohlcv_15m,
    dp_run_mostly_empty,
    data-pipeline-alerts,
    silent-zero-rows,
    honest-coverage,
    within-bounds-source-zero,
    alert-renag,
    manifest,
  ]
related:
  [
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/archive/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md,
    /plans/archive/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md,
    ../../archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md,
    ../../archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    ../data_pipeline_alerts_batch_remediation_2026_07_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-23
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  operator-reported #data-pipeline-alerts DP_RUN_MOSTLY_EMPTY CRITICAL batch, window 2026-07-22 23:46-48Z, triaged
  2026-07-23 (read-only investigation, no changes made).
---

# TradFi DP_RUN_MOSTLY_EMPTY cluster — ohlcv_1s / ohlcv_1m (real, open) vs ohlcv_15m (dead, already-tracked)

## Ground truth (live-queried 2026-07-23)

Downloaded `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` directly (a
single 88.9 MiB targeted read of the already-consolidated index — NOT a corpus walk; 5,858,026 total rows) and filtered
to the three alerted `data_type`s. All three counts reproduce the alert **exactly**:

| data_type   | captured | attempted_failed | attempted_total (captured+attempted_failed) |  ratio | alert value     |
| ----------- | -------: | ---------------: | ------------------------------------------: | -----: | --------------- |
| `ohlcv_1s`  |  647,294 |          224,204 |                                     871,498 |  25.7% | 224204/871498 ✓ |
| `ohlcv_1m`  |  640,315 |           81,220 |                                     721,535 |  11.3% | 81220/721535 ✓  |
| `ohlcv_15m` |        0 |            1,242 |                                       1,242 | 100.0% | 1242/1242 ✓     |

## Finding 1 — `ohlcv_1s` / `ohlcv_1m`: a real, large, still-open data gap (P1)

`error_reason` breakdown for both `attempted_failed` populations is dominated by a single value:

| data_type  | `WithinBoundsTradfiSourceZero` | `UNCLASSIFIED:BrokenPipeError` (transient network) |
| ---------- | -----------------------------: | -------------------------------------------------: |
| `ohlcv_1s` |               224,119 (99.96%) |                                                 85 |
| `ohlcv_1m` |                81,135 (99.90%) |                                                 85 |

Venue breakdown (both data_types, CME-dominant):

| venue  | ohlcv_1s attempted_failed | ohlcv_1m attempted_failed |
| ------ | ------------------------: | ------------------------: |
| CME    |                   167,945 |                    30,482 |
| NASDAQ |                    36,279 |                    31,037 |
| NYSE   |                    18,741 |                    18,451 |
| CBOE   |                     1,239 |                     1,250 |

`attempted_at` spans **2026-07-07 to 2026-07-21** for both data_types, with as many DISTINCT timestamps as rows (224,204
distinct values for 224,204 ohlcv_1s rows) — i.e. genuinely spread activity, not a single frozen batch.

### What `WithinBoundsTradfiSourceZero` actually means (read from source, not assumed)

This is **not a bug label** — it is a real, intentional classification emitted by
`market_tick_data_service/scripts/_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row()` (part of
`rebuild_tradfi_manifest.py`'s CF-11 honest-absence completeness pass). The logic: when the rebuild re-emits a
historical `empty_confirmed[SOURCE_RETURNED_ZERO]` row, it checks `is_non_trading_day(venue, date)` — if the day IS a
real trading day (weekday, not a venue holiday) the row is reclassified `attempted_failed(WithinBoundsTradfiSourceZero)`
("masked failure" per the script's own docstring) rather than staying honest-absence; only genuine weekend/holiday
empties are preserved as `empty_confirmed`. **This means every one of these 224,204 / 81,220 rows is a real trading-day
OHLCV request where Databento's own API silently returned zero rows** — the classification correctly surfaces a real gap
rather than hiding it.

Because `record_failed(row_key=..., error="WithinBoundsTradfiSourceZero", ...)` at this call site does not pass an
explicit `attempted_at=`, UTL's `ManifestWriter` defaults it to the write call's own `datetime.now(UTC)` — so the
2026-07-07→2026-07-21 spread reflects when the CF-11 rebuild scan **processed** each row (this script has evidently been
re-run multiple times across those 16 days, consistent with its own "safe to re-run" docstring and the ongoing
`tradfi_master` v9-canonicalization effort), not necessarily when the original silent-zero fetch happened. This is a
DIFFERENT mechanism from the sports `attempted_at` corruption bug (Finding 2 in the companion sports issue doc) — here
the reclassification itself is correct and intentional; only the interpretation of "when did this fail" needs this
caveat, not the classification's validity.

### This is the same gap a prior investigation flagged but did not close

`tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md` (archived, `status: resolved`) investigated the identical
symptom — CME/CBOE/NYSE/NASDAQ `ohlcv_1s`/`ohlcv_1m` returning a clean 0-record success with no error anywhere in the
pipeline. It:

- Ruled out every local guard (billing/lookback allowlist, schema allowlist, instrument-preflight, `IS_TEST_RUN`,
  degraded API key) via direct code trace.
- Ran a live diagnostic: `client.symbology.resolve(...)` for CME `ES.FUT` on 2026-07-09 returned a full real mapping (39
  instrument_ids, `not_found: []`), and `client.timeseries.get_range(...)` with the exact production call shape returned
  **1,628 real rows** for that same day — proving real data exists and is fetchable via the registry's own declared
  symbol form, ruling out both the entitlement and symbol-resolution hypotheses.
- But its **actual shipped fix** (`market-tick-data-service@69d226dc`) only resolved a SMOKE-CHECKER false negative:
  `pipeline_e2e_check.py` was passing raw dated-contract symbols (`"ESM26"`) that `_apply_instrument_filter` couldn't
  match against curated parent symbols (`"ES.FUT"`), collapsing the request to zero instruments BEFORE any SDK call — a
  diagnostic-tool bug, not a production bug (production backfills pass no `--instrument-ids`, so this filter never
  engaged them).
- Its own closing note: **"real production tradfi gaps are tracked elsewhere (OOM completion run, fleet drain)"** — this
  investigation did not find a dedicated tracking doc for that "elsewhere" (grepped `plans/` for "OOM completion run" /
  "fleet drain" against tradfi context, no hit beyond this doc itself); it is very likely this exact
  `WithinBoundsTradfiSourceZero` population. **The real root cause (why Databento silently returns 0 rows for some
  in-bounds CME/NASDAQ/NYSE requests) remains genuinely unresolved.**

A shipped diagnostic aid exists for whoever picks this up: `_emit_empty_but_valid()` in `databento_fetch.py` fires a
structured `DATABENTO_EMPTY_BUT_VALID` event (logging `DBNStore.metadata` — mapped-symbol count, echoed start/end,
partial/not_found) whenever a real SDK call returns zero rows without erroring. Grepping live logs for this event on CME
shards should make the actual production request args visible without new instrumentation, and would settle whether this
is a symbol-mapping edge (e.g. a specific contract roll date), a per-venue date-window edge, or something else entirely.

### Trend — real but slow progress, bulk still open

A 2026-07-07 snapshot (`tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`, CF-4 table) shows
`ohlcv_1s attempted_failed=227,148` and `ohlcv_1m attempted_failed=91,547` at that point (16 days before today's 224,204
/ 81,220). The population has shrunk only modestly (**-1.3%** ohlcv_1s, **-11.3%** ohlcv_1m) — some cells are being
resolved (via real backfill retries or CF-11 further narrowing), but the large majority remains outstanding. This is the
genuine, currently-open, MVP-scoped data completeness gap (CME/NASDAQ/NYSE ohlcv_1s/1m are the Databento-first,
actively-relied-on TradFi OHLCV backbone per `/codex/02-data/tradfi-databento-sourcing-ssot.md`) — not stale residue,
and not a classification bug. **Filed P1 per this investigation's own instructions: a real gap in core trading data.**

## Finding 2 — `ohlcv_15m`: 100% dead CBOE residue, already diagnosed, deliberately deferred (not new)

All 1,242 `attempted_failed` rows: `venue=CBOE` (100%), `error_reason=WithinBoundsTradfiSourceZero` (100%), and —
critically — **every row's `attempted_at` falls inside the exact `2026-07-07T06:40:00.845783Z` –
`2026-07-07T07:29:16.510922Z` window** (a single ~49-minute batch pass) with **zero rows newer than 2026-07-07** in the
16 days since. `captured=0` for this cell — no CBOE `ohlcv_15m` capture has EVER succeeded in the current manifest,
matching the alert's literal 100.0%.

This is the SAME 1,242-row population already fully root-caused in
`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s "Verification addendum" section
(live-queried 2026-07-15: `ohlcv_15m` attempted_failed breakdown `NYSE 1,397 / CBOE 1,242 / KRX 743 / NASDAQ 207`,
sum=3,589 — the NYSE/KRX/NASDAQ portions carried `error_reason=EXPECTED_SOURCE_NOT_AVAILABLE` and were reclassified to
`empty_confirmed` by the separate misclassification fix
(`tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`, verified today: those three venues no longer
appear under `ohlcv_15m` `attempted_failed` at all), leaving CBOE's 1,242 as the sole survivor — exactly matching
today's count). Root cause: CBOE's `ohlcv_15m` `VENUE_DATA_TYPE_CAPABILITIES`/`expected_coverage.py` entry was stale
drift left over from a Yahoo VIX-cash-index `ohlcv_15m` fetch path that was removed 2026-06-25/26 — after removal, any
`(CBOE, ohlcv_15m)` request fell through to the Databento path, which doesn't serve a 15m schema at all, guaranteeing
100% failure. **Fixed going forward** 2026-07-15 (`unified-api-contracts@78b9e899` narrows CBOE's expected coverage,
matching the KRX/ICE precedent) — no new `ohlcv_15m` attempts have been made for CBOE since, which is exactly why 100%
of the 1,242 rows are frozen at the single 2026-07-07 timestamp.

**The 1,242 historical rows were explicitly left un-purged** — the 07-15 doc's own words: _"purge/reclassify the stale
rows across all 3 cells in one pass... Not fixed here... flagging as a single unified follow-up candidate"_ — this was
never executed. **This is why the alert re-fired 2026-07-22 23:46-48Z**: not a regression, but the already-shipped
re-nag cooldown (`DP_RUN_MOSTLY_EMPTY: 1800.0s`, `alerting-service@fe76ded3`, verified live in
`dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`) doing exactly what it was built to do — re-page every 30 minutes
for a cell that is still measured `high` by `check_high_attempted_failed`'s whole-manifest-history, no-recency-window
count (`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py`). A dead cell with a stale
count > the flat `ATTEMPTED_FAILED_ABS_THRESHOLD` (500) pages forever until someone actually purges or reclassifies the
rows.

## Why these are filed together but are NOT the same root cause

Both share `error_reason=WithinBoundsTradfiSourceZero` (coincidence of the same reclassification code path having
processed both populations), but the shape is opposite: `ohlcv_1s`/`ohlcv_1m` are ACTIVE (16-day spread of distinct
`attempted_at`, real captured cells too, slowly shrinking — a genuine open gap); `ohlcv_15m` is DEAD (single 49-minute
frozen batch from 2026-07-07, zero captures ever, zero activity since, already root-caused and intentionally deferred).
Filed as one cluster doc since they alerted in the same window and share a bucket + venue overlap, but the recommended
actions are different (see Todos).

## Todos

- [ ] [INVESTIGATE] P1. Root-cause the actual `WithinBoundsTradfiSourceZero` trigger for the live, active
      `ohlcv_1s`/`ohlcv_1m` CME/NASDAQ/NYSE population — grep live logs for the already-shipped
      `DATABENTO_EMPTY_BUT_VALID` structured event on a sample of affected (venue, date, instrument) cells and diff the
      echoed request args against the 2026-07-13 working diagnostic in
      `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`. Repo: `market-tick-data-service`.
- [ ] [DATA] P2. Purge or reclassify the 1,242 dead CBOE `ohlcv_15m` rows (frozen since 2026-07-07, already narrowed out
      of expected coverage) — mirrors the deferred cleanup recommendation already on record in
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`. Snapshot-before-write,
      dry-run default, matching the established `reclass_*`/`purge_*` precedent scripts. Repo:
      `market-tick-data-service`.
- [x] [DESIGN] P2. ✅ **DONE 2026-07-26 (batch-3 todo 8) — `deployment-service@01414fc`.** New
      `known_dead_cells_registry.py` — a
      `(asset_group, data_type) -> KnownDeadCell(narrowed_at, venue, narrowed_by,     note)` registry, consulted
      per-cell in `_read_attempted_failed_cells` via the cell's MAX `attempted_at` among its current `attempted_failed`
      rows (`is_known_dead_for_series`); suppresses only while zero activity is newer than `narrowed_at`, any new
      `attempted_at` clears it and resumes paging. Keys on `(asset_group, data_type)` — matching
      `check_high_attempted_failed`'s existing alert granularity (no venue dimension); `venue` stored as provenance
      only. CBOE `ohlcv_15m` is the first populated instance (`narrowed_at=2026-07-15`, citing
      `unified-api-contracts@78b9e899`); `mbp_10`/`corporate_action_confirmed`/`earnings_result` are explicitly NOT
      added yet — each needs its own narrowing-date + zero-new-activity verification before joining (noted as the
      follow-up in the registry module's own docstring). 10 tests (3 integration + 7 unit); `quality-gates.sh` green.
      Source: `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md` todo 8.
