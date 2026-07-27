---
doc_type: issue
title: COINBASE-FUTURES 2026-07-25 — 354 manifest rows with null instrument_type despite well-formed instrument_id
summary: >-
  Surfaced while verifying the ⑧ IS cefi REFERENCE-UNIVERSE closure in data_completion_cefi_2026_07_15.md — a direct
  read of market-data-tick-cefi-prd's _index/availability_index.parquet found 0 blank/UNKNOWN-venue rows (that item's
  original ~650-row pollution is resolved) but a NEW, distinct, single-day gap: 354 COINBASE-FUTURES rows dated
  2026-07-25 have instrument_type=null while instrument_id/venue/data_type are all well-formed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, manifest, coinbase-futures, instrument_type, data-correctness]
related: [/plans/active/data_completion_cefi_2026_07_15.md]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: stable
depends_on: []
source: ["surfaced 2026-07-27 while closing data_completion_cefi_2026_07_15.md item ⑧ (slot-4 live manifest read)"]
resolved_by:
locked_by:
locked_since:
---

# COINBASE-FUTURES 2026-07-25 blank instrument_type — 354 rows

## What I found

A direct read of `market-data-tick-cefi-prd-central-element-323112`'s `_index/availability_index.parquet` (8,764,263
rows total, read via `unified_trading_library.cf_manifest_audit._cp` + `pd.read_parquet`, columns
`date,venue,instrument_type,instrument_id,data_type,capture_status`) found:

- 0 rows with blank/null `venue`
- 0 rows with `venue == "UNKNOWN"`
- 0 rows with `instrument_id` ending in `F0`
- **354 rows with null `instrument_type`** — ALL dated `date=2026-07-25`, ALL `venue=COINBASE-FUTURES`,
  `data_type=book_snapshot_5`, `capture_status` split 301 `empty_confirmed` / 53 `attempted_failed`.

Sample instrument_ids (all well-formed, PERPETUAL-shaped): `COINBASE-FUTURES:PERPETUAL:1000BONK-USD@LIN`,
`COINBASE-FUTURES:PERPETUAL:AAPL-USD@LIN`, `COINBASE-FUTURES:PERPETUAL:AMZN-USD@LIN`, etc.

This is NOT the venue-pollution class tracked by `data_completion_cefi_2026_07_15.md` item ⑧ sub-part (4) (that was
blank-venue/UNKNOWN-venue rows, now confirmed at 0). It is a narrower, single-day writer gap: the venue and
instrument_id resolved correctly but `instrument_type` didn't get populated for this one date's COINBASE-FUTURES
book_snapshot_5 shard.

## Why it matters

`instrument_type` is a coverage-denominator field for some downstream honest-coverage / CF-checks (schema presence
checks read the column even when not filtering on it). A one-day gap for one venue is low-blast-radius but is a genuine
writer defect worth root-causing — if it's a transient race (e.g. instrument-type resolution timing out against a stale
reference-universe cache on that date) it could recur on future dates/venues.

## Recommended decision

- [ ] [DATA] P3. Root-cause why `market_tick_data_service`'s manifest writer left `instrument_type=null` for these 354
      COINBASE-FUTURES `book_snapshot_5` rows on `date=2026-07-25` — check whether the reference-universe/catalog lookup
      COINBASE-FUTURES instrument-type resolution path 5xx'd or timed out around that write, or whether it's a one-off
      partial-write artifact. Repo: market-tick-data-service. If a real resolver gap, backfill/patch just these 354 rows
      (small, targeted — not a corpus walk).
