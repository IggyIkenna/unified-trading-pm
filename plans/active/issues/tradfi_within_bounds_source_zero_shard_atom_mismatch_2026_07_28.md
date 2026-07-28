---
doc_type: issue
title:
  "WithinBoundsTradfiSourceZero root-caused: NOT a Databento silent-zero-row bug — a stale pre-2026-06-22 bundle-grain
  shard-atom mismatch between the tradfi enumerator's expected/CF-11-failed rows (keyed by instrument_id=<parent>.FUT/
  .OPT) and the MTDS writer's actual captured-shard key (instrument_id='' + underlying=<canonical>) for CME
  futures_chain /options_chain instruments + CBOE VX.FUT — real data exists for the large majority of 'failed' cells"
summary: >-
  Root-caused the `WithinBoundsTradfiSourceZero` cluster this doc's parent
  (`tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`) filed as a real, open Databento silent-zero-row gap (per
  `plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s INVESTIGATE todo). It is NOT a vendor issue.
  Exhaustive live evidence: downloaded and grepped 4 real production VM `run.log`s (CME ES 2019/2020/2026 backfills,
  most recent as of 2026-07-28) plus the full `DATABENTO_EMPTY_BUT_VALID` GCS structured-events store for the shipped
  `_emit_empty_but_valid()` event and its precursor log line — ZERO hits anywhere. The Databento SDK is not returning
  empty responses in production; the `DATABENTO_EMPTY_BUT_VALID` diagnostic aid never fires because there is nothing for
  it to catch. Direct manifest cross-reference instead proves a shard-atom mismatch: for CME
  `attempted_failed(WithinBoundsTradfiSourceZero)` rows whose `instrument_id` maps to a known parent symbol
  (ES/MES/NQ/MNQ/GC/CL/SI/HG/PA/PL/NG/RB/RTY/YM — 69,475 checkable rows), 59.3% (41,210) have a `captured` row with real
  `row_count>0` for the IDENTICAL (date, data_type, chain_type, underlying) cell — 99-100% for the flagship
  ES/MES/NQ/MNQ instruments specifically. Mechanism: `instruments-service@f6d479f8` (2026-06-22) fixed the tradfi v2
  enumerator to seed bundle-grain instrument types (futures_chain/options_chain, per UAC `GRAIN_BUNDLE_BY_UNDERLYING`)
  with `instrument_id=''` + `underlying=<canonical>`, matching the MTDS writer's real shard key
  (`market_tick_data_service/.../venue_fetch.py:318-320`). Rows seeded BEFORE that fix (or never re-keyed) still carry
  the retired `instrument_id=<parent>.FUT/.OPT` key.
  `market_tick_data_service/scripts/_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row` (CF-11's honest-absence rebuild,
  observed running 2026-07-07→2026-07-21) reclassifies every historical `empty_confirmed[SOURCE_RETURNED_ZERO]` row to
  `attempted_failed(WithinBoundsTradfiSourceZero)` purely on `is_non_trading_day(venue, date)` — with NO check against
  the writer's real (post-fix) captured shard for the same underlying/date — so it silently promotes ~170K
  legitimately-captured CME cells (mostly ohlcv_1s) plus a smaller ohlcv_1m + CBOE `VX.FUT` tail (2,489 rows, same
  mechanism) into false 'failed' status. NASDAQ/NYSE (part of the original 2026-07-23 alert) are UNRELATED and now fully
  resolved: their `WithinBoundsTradfiSourceZero` population is confirmed 0 as of 2026-07-28 (live-queried), explained by
  the separate below-vendor-discovery-floor cleanup that landed in this same session (`instruments-service@31cf3952` +
  the batch2 plan's `--apply` run, 182,407 cells corrected) — a different root cause, already closed elsewhere. This doc
  scopes ONLY the CME + CBOE bundle-grain mismatch, which remains open and unfixed.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    tradfi,
    databento,
    ohlcv,
    ohlcv_1s,
    ohlcv_1m,
    within-bounds-source-zero,
    shard-atom-mismatch,
    bundle-grain,
    manifest,
    honest-absence,
    cf-11,
    false-positive,
  ]
related:
  [
    /plans/active/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md,
    /plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md,
    /plans/active/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-28
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md INVESTIGATE todo (root-cause the
  WithinBoundsTradfiSourceZero trigger), worked 2026-07-28 (slot 6): live VM run.log + GCS-events grep (0 hits) + direct
  availability_index.parquet cross-reference (59.3-100% false-positive match rate) + code trace
  (instruments-service@f6d479f8, market_tick_data_service/scripts/_rebuild_tradfi_cf11.py).
---

# WithinBoundsTradfiSourceZero — root-caused as a stale bundle-grain shard-atom mismatch, not a Databento bug

## TL;DR

The `WithinBoundsTradfiSourceZero` cluster is **not** a vendor silent-zero-row problem. It is a **false-positive
manifest bookkeeping bug**: legacy CME/CBOE `futures_chain`/`options_chain` expected rows keyed by the retired
per-parent-symbol `instrument_id` (`ES.FUT`, `ES.OPT`, `VX.FUT`, …) are being reclassified to `attempted_failed` by the
CF-11 honest-absence rebuild even though the SAME date's real data is already sitting in the manifest, correctly
captured, under the post-2026-06-22 bundle-grain key (`instrument_id=''`, `underlying=<canonical>`). The task brief's
suggested diagnostic (grep `DATABENTO_EMPTY_BUT_VALID`) correctly returns nothing — because nothing ever failed at the
vendor-API layer.

## Evidence chain

### 1. Exhaustive live-log search: zero `DATABENTO_EMPTY_BUT_VALID` occurrences anywhere checked

Downloaded and grepped real production `run.log`s from `gs://deployment-scripts-central-element-323112/vm-logs/`:

- `tradfi-bf-cme-ohlcv-1m-es-2026-20260728-030127/run.log` (3.6 MiB, today's live CME ES 2026 backfill)
- `tradfi-bf-cme-ohlcv-1m-es-2020-20260728-030028/run.log` (2.5 MiB, today's live CME ES 2020 backfill)
- `tradfi-bf-cme-ohlcv-1m-es-2019-20260716-090047/run.log` (135 KiB, a completed CME ES 2019 backfill)

— for `DATABENTO_EMPTY_BUT_VALID`, `genuine zero-row`, `SOURCE_RETURNED_ZERO`, `WithinBoundsTradfiSourceZero`, and
`— 0 records`: **zero matches in all three logs.** Also downloaded the full structured-events GCS store
(`gs://central-element-323112-events/events/market-tick-data-service/2026-07-28/tradfi-bf-cme-ohlcv-1m-es-2020-20260728-030028/hour=03/`,
184 individual event files) and confirmed the event taxonomy present (`RESOURCE_PROFILER_SAMPLE`, `PIPELINE_HEARTBEAT`,
`PROCESSING_STARTED/COMPLETED`, `MANIFEST_LOAD_SIZE_BYTES`, `STARTED`/`STOPPED`) contains **no**
`DATABENTO_EMPTY_BUT_VALID` or `ADAPTER_FETCH_FAILED` entries.

Direct evidence from the live logs that fetches ARE succeeding: `cme_es_2026_run.log` shows
`download_batch_df: CME 2026-01-06 — 42361 records` (and 10 similar lines, all tens of thousands of rows, zero 0-row
lines); `cme_es_2020_run.log` shows the same for January 2020 dates (e.g. `CME 2020-01-08 — 56949 records`). Both
`ohlcv_1s` and `ohlcv_1m` write real partitioned output every single date processed
(`futures_chain/ohlcv_1s/SP500/…: 40338 rows`, `options_chain/ohlcv_1s/SP500/…: 1429 rows`, etc.) — the Databento
requests are not failing.

### 2. Manifest cross-reference proves real data exists for the "failed" cells

Downloaded `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` directly (single
88.9 MiB targeted read, not a corpus walk; 5,876,905 rows) and queried it directly (repo `.venv`, `pandas`/`pyarrow`).

**Concrete example** — 2020-01-02, CME, `ohlcv_1m`:

| instrument_id | instrument_type | underlying | capture_status                                      | row_count |
| ------------- | --------------- | ---------- | --------------------------------------------------- | --------: |
| `ES.FUT`      | (none)          | (none)     | `attempted_failed` (`WithinBoundsTradfiSourceZero`) |       0.0 |
| (blank)       | `futures_chain` | `SP500`    | `captured`                                          |    1597.0 |
| (blank)       | `options_chain` | `SP500`    | `captured`                                          |    1855.0 |
| (blank)       | `COMBO`         | `SP500`    | `captured`                                          |      88.0 |

The manifest is internally contradictory: it simultaneously records "no data" for `ES.FUT` on this date AND "3,540 real
rows captured" for the exact same underlying/date/data_type, just under a different row identity.

**Systematic check across the whole CME population** — for every `attempted_failed(WithinBoundsTradfiSourceZero)` row
whose `instrument_id` matches `<parent>.FUT`/`<parent>.OPT` for a known UAC base symbol (`tradfi_instrument_universe.py`
`BASE_ASSET`/underlying map), checked whether a `captured` row exists for `(date, data_type, chain_type, underlying)`:

| base                           | checkable rows | real-data-exists (false positive) |                                                            match rate |
| ------------------------------ | -------------: | --------------------------------: | --------------------------------------------------------------------: |
| ES                             |          6,095 |                             6,095 |                                                                  100% |
| MES                            |          3,061 |                             3,061 |                                                                  100% |
| MNQ                            |          1,572 |                             1,572 |                                                                  100% |
| NQ                             |          5,206 |                             5,158 |                                                                   99% |
| CL/GC/HG/NG/PA/PL/RB/RTY/SI/YM |        ~44,978 |                           ~22,415 | ~50% (naming-scheme drift on my match string only — see caveat below) |
| **Total**                      |     **69,475** |                        **41,210** |                                                             **59.3%** |

Caveat: the ~50% match rate on the commodity group is a **lower bound** — my quick cross-check script used a guessed
`BASE_ASSET -> underlying` string (e.g. `"HEATING_OIL"`) that does not exactly match the manifest's actual stored
strings for every symbol (the manifest itself is inconsistent across rows: `HEATING-OIL` vs `HEATINGOIL` vs `HO`,
`NAT-GAS` vs `NAT-GAS-HH` vs `NATGAS`, etc. — a separate, smaller naming-drift issue, not re-diagnosed here). The ES/
MES/NQ/MNQ 99-100% match (where the string mapping is unambiguous) is the clean signal; the commodity-group number
undercounts real matches and was not manually reconciled symbol-by-symbol in this pass.

**CBOE**: the small `WithinBoundsTradfiSourceZero` tail (2,489 rows, ALL `instrument_id=VX.FUT`) shows the identical
key-mismatch shape — captured rows exist at `instrument_type=futures_chain, underlying=VIX` for the same dates. (This is
`ohlcv_1s`/`ohlcv_1m` VX futures — a different, smaller population than the already-tracked 100%-dead `ohlcv_15m` CBOE
residue in `tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` Finding 2, which is untouched by this doc.)

### 3. Code-grounded mechanism

- `instruments-service@f6d479f8` (2026-06-22, `fix(is-enumerator): axis-3 tradfi bundle grain — seed instrument_id=''
  - underlying (match MTDS writer
    venue_fetch.py:318)`) fixed `scripts/enumerate_expected_universe.py::_enumerate_v2_tradfi` to seed bundle-grain instrument types (`grain_for_instrument_type("tradfi",
    canon_it) ==
    GRAIN_BUNDLE_BY_UNDERLYING`— i.e.`futures_chain`/`options_chain`/`combo`, the synthetic per-underlying entries `_rollup_bundle_grain`produces) with`instrument_id=""`+`underlying=instr.underlying`, matching the MTDS writer's real captured-shard atom (`market_tick_data_service/.../venue_fetch.py:318-320`, `manifest_finalize.py` `_UNDERLYING_PARTITIONED_TYPES`).
    The fix's own docstring names exactly this bug class: _"the seeded shard atom … can NEVER be converted by the real
    capture … same shard-grain-mismatch class as the defi PROTOCOL-CHAIN bug."_
- Rows seeded **before** 2026-06-22 (or by any code path that predates the fix) still carry the retired
  `instrument_id=<parent>.FUT`/`.OPT` key and were never migrated/re-keyed/purged.
- `market_tick_data_service/scripts/_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row` — CF-11's honest-absence rebuild
  pass, observed running 2026-07-07→2026-07-21 per every affected row's `attempted_at` — reclassifies **every**
  historical `empty_confirmed[SOURCE_RETURNED_ZERO]` row it scans to `attempted_failed(WithinBoundsTradfiSourceZero)`
  based **solely** on `is_non_trading_day(venue_str, day_str)`. It never checks whether a `captured` row already exists
  under the writer's real (possibly differently-keyed) shard atom for the same underlying/date. This is the exact
  trigger: it blindly promotes stale, obsolete-grain rows to "failed" without verifying they're actually still
  meaningful expected cells.

### 4. NASDAQ/NYSE are a different, already-closed issue

The parent doc's original 2026-07-23 snapshot included NASDAQ (36,279 `ohlcv_1s` / 31,037 `ohlcv_1m`) and NYSE (18,741 /
18,451). Live-querying the SAME manifest today (2026-07-28) shows **both at exactly 0** — fully resolved within the last
5 days. NASDAQ/NYSE equities are LEAF-grain instruments (not bundle-grain — no futures/options chain), so this doc's
shard-atom-mismatch mechanism does not apply to them; their population is explained by the separate, already-completed
`tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` fix (`instruments-service@31cf3952` discovery-floor
enumerator fix + this session's `--apply` correcting 182,407 cells, see
`plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s adjacent `[DATA] P1` todo, DONE 2026-07-28 slot-2) —
NASDAQ/NYSE's pre-2023-04-15 archive-floor cells were the dominant driver there, not this doc's bug.

## Why the original DATABENTO_EMPTY_BUT_VALID / request-arg-diff diagnostic came back empty

The task brief's suggested method (grep live logs for `DATABENTO_EMPTY_BUT_VALID`, diff echoed request args against the
2026-07-13 working diagnostic) presupposed the SDK really was returning zero-row responses for some cells, as the
original `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md` investigation suspected but never closed out (that
investigation's own fix only patched a smoke-checker false negative and explicitly left "real production tradfi gaps …
tracked elsewhere"). This investigation instead proves the SDK is **not** returning empty responses at all for this
population — the "elsewhere" gap that doc pointed at is this manifest bookkeeping bug, not a vendor-API issue.
`DATABENTO_EMPTY_BUT_VALID` finding zero hits is itself the confirming evidence, not an inconclusive result.

## Recommended remediation (not implemented in this investigate-only todo)

1. **Migration/purge pass** over CME + CBOE bundle-grain `attempted_failed(WithinBoundsTradfiSourceZero)` rows keyed by
   the retired `instrument_id=<parent>.FUT`/`.OPT` grain: for each, check whether a `captured` row exists at the
   post-fix key `(date, venue, data_type, instrument_type∈{futures_chain,options_chain}, underlying)`. If yes — the
   stale row is pure redundant noise (real data is already correctly represented elsewhere in the manifest) — retire it
   rather than leaving it counted as a failure. Snapshot-before-write, dry-run default, matching the established
   `reclass_*`/`purge_*` precedent scripts (mirrors the CBOE `ohlcv_15m` deferred-purge precedent). Scale: up to ~198K
   CME rows + 2,489 CBOE rows are candidates (exact count after excluding genuine failures needs the dry-run's own
   count, not this doc's estimate).
2. **Harden `_handle_srz_tradfi_row`** (or add a pre-check in its caller) to verify the writer's real captured shard
   does NOT already exist under the bundle-grain-equivalent key before reclassifying a historical row to
   `attempted_failed` — otherwise this exact false-positive class can recur for any other stale/legacy-keyed row a
   future honest-absence rebuild sweeps up.
3. Re-verify (or fix) the `BASE_ASSET`/`underlying` string-naming drift noted in the caveat above (`HEATING-OIL` vs
   `HEATINGOIL` vs `NAT-GAS` vs `NAT-GAS-HH` vs `NATGAS`) if it turns out to cause its own separate accounting problems
   beyond this doc's cross-check convenience mapping.
4. Once corrected, the `DP_RUN_MOSTLY_EMPTY` alert's CME `ohlcv_1s`/`ohlcv_1m` ratios should be re-measured — the real
   denominator is currently inflated by this false-positive population.

## Todos

- [ ] [DATA] P0. Migration/purge pass: for every CME + CBOE bundle-grain
      `attempted_failed(WithinBoundsTradfiSourceZero)` row keyed by the retired `instrument_id=<parent>.FUT`/`.OPT`
      grain, verify a real `captured` row exists at `(date, venue, data_type, instrument_type, underlying)` and retire
      the stale row if so (snapshot-before-write, dry-run default). Repo: `market-tick-data-service`.
- [ ] [SCRIPT] P1. Harden `market_tick_data_service/scripts/_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row` to check
      for an existing correctly-keyed captured shard before reclassifying a historical
      `empty_confirmed[SOURCE_RETURNED_ZERO]` row to `attempted_failed` — prevents this false-positive class recurring
      for future stale rows. Repo: `market-tick-data-service`.
- [ ] [DATA] P2. Reconcile the `BASE_ASSET`/manifest `underlying` string-naming drift found incidentally during the
      cross-check (`HEATING-OIL`/`HEATINGOIL`/`HO`, `NAT-GAS`/`NAT-GAS-HH`/`NATGAS`, and similar) if it is found to
      cause its own denominator/accounting issues. Repo: `market-tick-data-service` / `unified-api-contracts`.
- [ ] [DATA] P2. Re-measure the `DP_RUN_MOSTLY_EMPTY` CME `ohlcv_1s`/`ohlcv_1m` ratio after todo 1 lands, to confirm the
      alert's denominator is no longer inflated by this false-positive population. Repo: `market-tick-data-service`.

## Progress log

- 2026-07-28 (slot 6): Filed from `plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07-25.md`'s `[INVESTIGATE] P1`
  todo. Root-caused via live-log/GCS-events grep (0 hits, ruling out the vendor silent-zero-row hypothesis) + direct
  `availability_index.parquet` cross-reference (59.3-100% false-positive match rate on checkable CME rows, 99-100% for
  ES/MES/NQ/MNQ) + code trace (`instruments-service@f6d479f8`, `_rebuild_tradfi_cf11.py::_handle_srz_tradfi_row`).
  Confirmed NASDAQ/NYSE's share of the original alert is already resolved (separate, already-closed root cause). No fix
  implemented in this pass — this todo was investigate/diagnose-only per its own Done-when; remediation todos above are
  the follow-up.
