---
doc_type: issue
title: TradFi equity/ETF manifest writer emits legacy bare-symbol ids LIVE — actively growing, not just historical debt
summary:
  The currently-running TradFi equity/ETF backfill fleet writes canonical GCS object paths/filenames but NON-canonical
  manifest rows (lowercase instrument_type, bare-symbol instrument_id) for the same capture — a live writer/manifest
  divergence, not a one-time historical migration gap. Measured 856,872 bad rows written on 2026-07-21 alone, growing
  continuously while backfill VMs run.
status: open
nature: record
asset_group: tradfi
created: 2026-07-21
tags: [tradfi, manifest, canonical, writer-bug, data-correctness, backfill]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    data_pipeline_reconciliation_tradfi_2026_07_21,
    tradfi_manifest_row_loss_regression_2026_07_12,
  ]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: fix-code
depends_on: []
source:
  main session direct GCS/manifest read, 2026-07-21T16:04Z, cross-checked against a parallel content-migration
  root-cause investigation agent
locked_by:
resolved_by:
---

# TradFi manifest writer — live legacy-id regression (not historical debt)

## What's actually true (measured live, 2026-07-21T16:00-16:04Z)

Read the live TradFi manifest (`_index/availability_index.parquet` in
`market-data-tick-tradfi-prd-central-element-323112`) directly, filtered to `asset_group=tradfi`,
`capture_status=captured`, single-instrument rows (`underlying` null), `instrument_type` in `{equity, etf, spot_pair}`
case-insensitive:

| Population | Count   | `instrument_type`                      | `instrument_id` shape                                    | `written_at`                                                        |
| ---------- | ------- | -------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| Canonical  | 352,423 | UPPERCASE (`EQUITY`/`ETF`/`SPOT_PAIR`) | colon-shaped (`NASDAQ:EQUITY:AAPL-USD`)                  | **ALL exactly 2026-07-18**                                          |
| Legacy     | 858,165 | lowercase (`equity`/`etf`/`spot_pair`) | bare ticker (`IDXX`, `HON`, `ISRG`, `GOOG`, `META`, ...) | **856,872 written TODAY (2026-07-21)**, 1,258 on 07-19, 35 on 07-20 |

The canonical population is frozen at a single timestamp — it is entirely the one-time output of
`market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas` (a historical
repair script). **Nothing new has been written in canonical form since.** The legacy population is overwhelmingly fresh
— written TODAY by the currently-running TradFi equity/ETF backfill fleet (`tradfi-bf-nasdaq-*` / `tradfi-bf-nyse-*`
VMs, part of this session's MVP backfill drive).

**Cross-check — the GCS object path/filename for the SAME live capture IS canonical**: sampled
`NASDAQ:EQUITY:AAPL-USD.parquet`, GCS creation time `2026-07-21T00:55Z` (written by today's active backfill). So **the
same writer, same capture event, produces a canonical file path but a non-canonical manifest row** — two code paths for
one event are out of sync, violating the shard-atom-identity invariant (path / manifest / content must agree —
`codex/02-data/availability-manifest-and-data-status.md`).

## Why this matters more than a normal migration gap

This was initially assumed (by an earlier `/data-pipeline-reconciliation` run on 2026-07-21 and this session's own prior
claims) to be **historical debt** — legacy 2020-2022 data that a content-migration pass needs to clean up once. It is
not (or not only) that. **The writer itself is currently emitting non-canonical manifest rows for BRAND NEW captures,
right now, continuously, at a rate of ~850K rows/day while the backfill fleet runs.** Any content-migration/cleanup pass
run before this writer bug is fixed will be immediately re-polluted by the next backfill cycle — exactly what happened
to the 2026-07-18 fix, whose output has sat frozen and un-repeated for 3 days while ~858K fresh bad rows piled up around
it.

This also means the tradfi id-form canonical percentage (measured 30.8% on 2026-07-21 morning) is **not stable** — it
will continue to fall as the backfill fleet keeps running, not just stay flat pending cleanup.

## Root cause (under investigation)

A parallel investigation (this session) found:
`market_tick_data_service/market_interface/adapters/tradfi/tradfi_shared.py` around line 603 already derives the
canonical id correctly (`derive_tradfi_row_instrument_id(...)`) for the **file-path/filename** write. The **manifest**
`record_captured(...)` call site for the tradfi equity/ETF OHLCV backfill path is a _different_ piece of code that is
NOT using that same derived value — exact file:line + fix TBD (dispatched to a background agent; check this doc's
Progress Log / the plan's Progress Log for the outcome before re-investigating from scratch).

## Recommended sequencing (do not skip ahead)

1. **Fix the writer** (root-cause code fix, not a data migration) — the manifest record call must use the same canonical
   `instrument_id` + UPPERCASE `instrument_type` enum that the file-path derivation already computes.
2. Only THEN does a historical content-migration/cleanup pass (the parallel root-cause investigation's proposed
   two-track design — manifest track via a corrected/extended
   `migrate_tradfi_manifest_usd_lin_2026_07_18.py --in-place-cas`, and a new parquet-content read-modify-write track for
   the raw tick objects) make sense to run and actually hold.
3. Re-measure the canonical % after both the writer fix AND the backfill fleet has drained, not before — an in-flight
   measurement will keep moving.

## Safety precedent to respect when touching the manifest

`tradfi_manifest_row_loss_regression_2026_07_12.md` (RESOLVED but real): a 1,017,024-row silent manifest loss from an
unguarded read-modify-write racing the manifest consolidator. Any manifest write here MUST use the CAS
(`if_generation_match`) pattern already shipped in `migrate_tradfi_manifest_usd_lin_2026_07_18.py` — never a naive
download-rewrite-upload. The writer-code fix itself (append-only `record_captured` calls, not a bulk rewrite) does not
carry this risk; the follow-up historical cleanup pass does.

## Progress Log

- **2026-07-21T16:04Z (main session)** — finding measured + written up; dispatched a background agent to locate the
  exact `record_captured` call site, diagnose the divergence, and ship a scoped fix if safe (agent authorized to ship
  directly if the fix is small/well-tested; told to stop and report a design instead if it's not confident). Also
  flagged to the operator in-chat per the workspace's big-finding rule.
