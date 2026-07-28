---
doc_type: issue
title:
  cefi rebuild_cefi_manifest false-phantom rate is ~8.6% (490,639/5.68M rows) — itype/underlying column drift, NOT
  DERIBIT-chain-only
summary: >-
  Re-ran rebuild_cefi_manifest --dry-run over the full corpus (2019-01-01..2026-07-28) per the plan's multi-year dry-run
  phantom spot-check todo. unparseable=0 and dropped_malformed_captured are clean, but phantom_to_failed=490,639 (~8.6%
  of the 5,677,228-row prior index) fails the "small + DERIBIT-chain-style only" acceptance gate. Root cause confirmed
  live via 3 independent GCS spot-checks (100% false-phantom hit rate): the CF-11 covered-keys dedup compares the prior
  manifest's stored instrument_type/underlying columns against the live object scan's parsed path, and several venues'
  actual GCS layout has drifted from what the manifest recorded historically (OKX-FUTURES future->perpetual, BYBIT-SPOT
  spot_pair->perpetual, ASTER underlying column set vs blank live path) — the objects are genuinely present, so this is
  a false-phantom bug, not real orphans. Blocks the "NEXT SESSION — execute the migration" P0 todo in
  data_completion_cefi_2026_07_15.md until fixed + re-validated.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, manifest, honest-coverage, false-phantom, cf-11, data-correctness]
related: [../data_completion_cefi_2026_07_15.md]
created: "2026-07-28"
source: data_completion_cefi_2026_07_15.md todo re-run (slot-12, data_engineering)
resolved_by:
locked_by:
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

## What I found

Re-ran `market_tick_data_service.scripts.rebuild_cefi_manifest --dry-run` over the FULL corpus
(`--start-date 2019-01-01 --end-date 2026-07-28`, per the plan's "multi-year dry-run phantom spot-check" todo) against
`gs://market-data-tick-cefi-prd-central-element-323112`. First attempt required an env fix: `GCP_PROJECT_ID` must be
exported for the CF-11 pass's direct-consolidated-index read to succeed — without it, `get_project_id()` raises and the
pass silently falls back to `read_availability_index`, which itself found nothing and logged "prior _index is
empty/missing" (a **false-negative** result: it looked clean only because the CF-11 pass never actually ran against real
data). Re-ran with `GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp` exported.

Final summary (elapsed 753.2s):

```
total_shards: 4,545,458   unparseable: 0   distinct_venues: 26   distinct_dates: 2,675
reemit_attempted_failed: 942,674
reemit_empty_confirmed: 755,445
reclassified_to_failed: 218,705
phantom_to_failed: 490,639          <-- the gate this todo exists to check
dropped_malformed_captured: 25,413
reemit_skipped_covered: 3,244,340
reemit_out_of_range: 0
```

Prior-index total ≈ 5,677,228 rows. **`phantom_to_failed` = 490,639 = ~8.6% of the entire historical manifest** — the
plan's acceptance criterion ("`phantom_to_failed` stays small + well-formed, DERIBIT-chain-style true phantoms only") is
**NOT met**. Per-venue phantom volume is spread across nearly every major venue, not concentrated in DERIBIT
options/futures chains: OKX-FUTURES, HYPERLIQUID, ASTER, BYBIT-SPOT, OKX-SWAP, BINANCE-FUTURES, COINBASE-FUTURES,
BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES all show large counts (partial sample before completion: OKX-FUTURES
113,750 / HYPERLIQUID 95,577 / ASTER 77,230 / BYBIT-SPOT 52,388 phantom lines — the DERIBIT count in the same partial
sample was only 5,429, i.e. DERIBIT is a small minority of the total, not the dominant class the acceptance criterion
anticipated).

**Root cause confirmed live (not a hypothesis) — 3 independent spot-checks, 100% false-phantom hit rate:**

The CF-11 covered-keys dedup (`_rebuild_cefi_cf11.py:311-336`) builds the prior-row key as
`(day_str, venue_str, itype_str, dtype_str, iid_str, underlying_str)` where `itype_str` and `underlying_str` are read
**directly from the prior manifest's stored columns** (`row.get("instrument_type")`, `row.get("underlying")`), then
compared for exact-tuple membership in `covered_keys` (built from the live object scan's parsed path). When the prior
manifest's stored `instrument_type`/`underlying` values don't match what the CURRENT GCS path structure encodes for the
identical physical object, the row is falsely declared phantom (`PHANTOM_CAPTURED_NO_OBJECT`) even though the parquet is
sitting right there. Confirmed via live `bucket.list_blobs()`:

1. **OKX-FUTURES, date=2022-08-15, `derivative_ticker`, `OKX-FUTURES:FUTURE:ETH-USDT@LIN-20220930`** — flagged phantom.
   Object EXISTS at
   `raw_tick_data/by_date/day=2022-08-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=OKX-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/OKX-FUTURES:FUTURE:ETH-USDT@LIN-20220930.parquet`.
   The instrument_id embeds the literal token `FUTURE`, and the prior manifest apparently stamped
   `instrument_type=future` from this (or from an earlier writer generation) — but the CURRENT GCS path segment is
   `instrument_type=perpetual`. Exact-tuple compare fails on `itype`.
2. **ASTER, date=2024-01-10, `trades`, `ASTER:PERPETUAL:ARB-USDT@LIN`** — flagged phantom (prior row's `underlying`
   column = `ARBUSDT`). Object EXISTS at
   `raw_tick_data/by_date/day=2024-01-10/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/instrument_type=perpetual/data_type=trades/ASTER:PERPETUAL:ARB-USDT@LIN.parquet`
   — a per-instrument (non-bundled) path, so the object scan derives `underlying=""` for this cell (per
   `rebuild_cefi_manifest.py`'s per-instrument branch), but the prior manifest recorded a non-blank `underlying` value
   for the same physical row. Exact-tuple compare fails on `underlying`.
3. **BYBIT-SPOT, date=2022-01-02, `book_snapshot_5`, `BYBIT-SPOT:SPOT_PAIR:BOBA-USDT`** — flagged phantom. Object EXISTS
   at
   `raw_tick_data/by_date/day=2022-01-02/pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT-SPOT/instrument_type=perpetual/data_type=book_snapshot_5/BYBIT-SPOT:SPOT_PAIR:BOBA-USDT.parquet`
   — same pattern as (1): instrument_id embeds `SPOT_PAIR`, prior manifest likely stamped `instrument_type=spot_pair`,
   current GCS path is `instrument_type=perpetual`. Exact-tuple compare fails on `itype`.

This is the SAME BUG CLASS as the already-fixed `spot`→`spot_pair` `_ITYPE_SYNONYMS` entry (2026-06-11) and the
already-fixed slash-symbol stem regex (2026-06-04, "1187 false phantoms") — but it is **not covered** by either existing
fix. It looks like most/all non-bundled CeFi venues' actual GCS folder structure has settled on
`instrument_type=perpetual` regardless of what the instrument_id token or an older manifest-writer generation recorded,
and the CF-11 exact-tuple key match never accounts for this drift.

`unparseable=0` (criterion met) and `dropped_malformed_captured=25,413` (~0.45% of the prior index; the malformed
predicate — blank venue/dtype, literal `"ticks"` id, or fully-blank id+underlying — reads as junk-only, consistent with
the plan's expectation) look fine. **`phantom_to_failed` is the criterion that fails, and by a wide margin.**

## Why it matters

The next plan todo ("NEXT SESSION — execute the migration") is explicitly gated on this dry-run "validating perf" before
running the REAL (non-dry-run) rebuild, which would `record_failed(error="PHANTOM_CAPTURED_NO_OBJECT")` on every one of
these ~490K rows for real. That would corrupt ~8.6% of the historical manifest — silently downgrading genuinely
captured, present data to `attempted_failed`, which would then (a) misreport historical coverage as incomplete when it
is not, and (b) likely trigger unnecessary re-fetch/backfill attempts against venues that already have the data, wasting
real compute/API-quota cost for no data gain. This is a data-pipeline-correctness HARD RULE matter — the fix must land
and a clean re-run must confirm before the migration proceeds.

## Recommended decision

1. **BLOCK** `data_completion_cefi_2026_07_15.md`'s "NEXT SESSION — execute the migration" P0 todo from running until
   this is fixed and re-validated (added as a blocking note on that todo in the same commit as this issue doc).
2. **Fix** (AO-eligible, scoped, data_engineering craft, repo `market-tick-data-service`): extend the CF-11 covered-keys
   comparison in `_rebuild_cefi_cf11.py` (`reemit_cefi_honest_absence_rows`, lines ~311-336) so a prior captured row is
   NOT treated as phantom purely because its stored `instrument_type`/`underlying` columns differ from the live path's
   encoding, when a matching object genuinely exists under the SAME (date, venue, data_type, instrument_id) ignoring
   `instrument_type`/`underlying` — mirroring the existing N1/F3-shadow suppression already used for blank-itype rows
   (`covered_keys_no_itype`, lines 270-272, 340-342), generalized to also ignore `underlying`. A worker taking this
   should NOT simply widen `_ITYPE_SYNONYMS` per-venue (that only chases one venue at a time and this spans ~9+ venues)
   — the shadow-suppression generalization is the systemic fix.
3. **Re-run** this same full-corpus `--dry-run` after the fix lands; `phantom_to_failed` should drop by roughly the 490K
   false-phantom volume, leaving a small DERIBIT-chain-style residual (true phantoms — a captured row genuinely missing
   its backing parquet, e.g. deleted/moved objects). Re-flip this issue + the plan todo once confirmed.

## Todos

- [ ] [DATA] P0. Generalize the CF-11 covered-keys shadow-suppression in
      `market-tick-data-service/market_tick_data_service/scripts/_rebuild_cefi_cf11.py`
      (`reemit_cefi_honest_absence_rows`) to also ignore `instrument_type`/`underlying` drift between the prior
      manifest's stored columns and the live object scan's parsed path — confirmed false-phantom repro: OKX-FUTURES
      `future`→`perpetual`, BYBIT-SPOT `spot_pair`→`perpetual` (itype drift), ASTER non-blank `underlying` column vs
      live path's blank `underlying` for a per-instrument shard (underlying drift). Add regression tests mirroring
      `test_wellformed_captured_no_object_still_phantom` (must still catch a TRUE phantom) alongside new tests for each
      drift case (must NOT phantom-demote when the object genuinely exists). (repo: market-tick-data-service)
- [ ] [DATA] P1. After the fix lands, re-run the full-corpus `rebuild_cefi_manifest --dry-run` (2019-01-01..present) and
      confirm `phantom_to_failed` drops to a small DERIBIT-chain-style residual; update this issue doc + unblock
      `data_completion_cefi_2026_07_15.md`'s "NEXT SESSION — execute the migration" todo. (repo:
      market-tick-data-service)
