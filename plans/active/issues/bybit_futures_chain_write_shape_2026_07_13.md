---
doc_type: issue
title:
  "BYBIT futures_chain historical writes have 3 inconsistent shapes (flat glued-symbol files, a bare bundled
  ticks.parquet, and the correct underlying= hive form) — the base+quote regex bug fixed 2026-07-09 was never backfilled"
summary: >-
  BYBIT's raw_tick_data instrument_type=futures_chain data is written in at least 3 different shapes depending on when
  it was captured: (1) correct underlying=/ hive-partitioned form (2023-06 era, coexisting with (2) that same day), (2)
  legacy flat SYMBOL.parquet siblings at the same directory level, and (3) from ~2026-01 through the 2026-07-09 code
  fix, ONLY flat glued-base+quote files (e.g. BTCUSDT.parquet instead of underlying=BTC/ticks.parquet) — traced to a
  documented `_extract_underlying_for_chain` regex bug (canonical-write-conventions.md lines 212-217) that captured
  "BTCUSDT" instead of "BTC". The code fix landed 2026-07-09 but historical BYBIT futures_chain data written before that
  date was never backfilled/re-shaped to the correct form.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [futures_chain, bybit, write-shape, hive-partition, data-correctness, backfill]
related: [/plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P2
source:
  "Found as a byproduct of investigating why deployment-service's cefi__trades BigQuery external table
  (bigquery_feature_external_tables.tf) failed to create — a classification sub-agent confirmed DERIBIT's
  futures_chain/underlying= shape is correct + load-bearing (do not touch), but while comparing venues to confirm
  underlying= is genuinely necessary everywhere, found BYBIT specifically has 3 coexisting/sequential shapes over time,
  one of which is a known-fixed-but-not-backfilled regex bug. Deliberately not fixed in the same pass — this is a data
  backfill/re-shape task, not a BQ config fix, and outside that session's scope."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
---

# BYBIT futures_chain write-shape inconsistency (3 shapes across history)

> **🟡 TRACKED — plan filed 2026-07-13**: `bybit_futures_chain_write_shape_migration_2026_07_13.md` (agent-orchestrator
> plan, `assigned_vm: planning`) owns the actual fix. A same-day rescoping check (before filing the plan) found the
> affected window is WIDER than this doc's original estimate — glued-shape files confirmed present 2025-06-01 through
> 2026-05-01 (not just ~2026-01), and no BYBIT `futures_chain` data at all is found from 2026-06-01 onward (needs
> explanation — the new plan's Phase 1 owns this). Leave `status: open` here until the plan reports the fix complete.

## Finding (2026-07-13)

`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`, `venue=BYBIT`,
`instrument_type=futures_chain` has at least 3 shapes depending on capture date:

1. **Correct hive form**: `.../data_type=trades/underlying={U}/ticks.parquet` — matches the SSOT-documented shape
   (`market-tick-data-service/docs/GCS_PATHS.md` lines 61-71, 109-117; `docs/canonical-write-conventions.md` lines
   16-51), the same shape DERIBIT uses correctly across its entire 2019-2026 history.
2. **Legacy flat siblings**: e.g. `day=2023-06-01` has BOTH `underlying=BTC/`, `underlying=ETH/` hive dirs AND flat
   `BTC.parquet`/`ETH.parquet` files at the same directory level; `day=2025-01-01` additionally has a bare unqualified
   `ticks.parquet` whose size ≈ sum of the three per-underlying hive files that day (a bundled dump, not a duplicate).
3. **Glued base+quote flat files (the actively-broken window)**: by 2026-01 through ~2026-05, BYBIT
   `futures_chain`/`trades` is written ONLY as flat glued-symbol files (`BTCUSDT.parquet`, `ETHUSDT.parquet`, etc., no
   `underlying=` segment at all). Root cause is documented in `canonical-write-conventions.md` lines 212-217:
   `_extract_underlying_for_chain`'s regex captured the full `BTCUSDT` symbol instead of splitting out `BTC` as the
   underlying. **Fixed in code 2026-07-09**, but the historical window this bug affected (~2026-01 → 2026-07-09) was
   never backfilled/re-shaped.

This is UNRELATED to the DERIBIT `underlying=` finding from the same investigation (DERIBIT's shape is correct and 100%
consistent across its whole history — `underlying=` is load-bearing there, not a bug). BYBIT is the one venue with
genuine write-path inconsistency.

## Why this matters

Any BigQuery external table (or other tool) that assumes a uniform `underlying=` hive-partition depth for
`futures_chain` data will break the instant it scans a BYBIT day inside the 2026-01→2026-07-09 window (flat files with
no `underlying=` key), or the 2023-06/2025-01-era legacy-sibling days (duplicate flat+hive forms inflating counts). This
surfaced as a contributing factor while diagnosing why
`deployment-service/terraform/gcp/bigquery_feature_external_tables.tf`'s `cefi_trades` table failed to create — though
the PRIMARY blocker there was a separate `futures_chain`/`underlying=` (DERIBIT, legitimate) vs non-`futures_chain`
depth mismatch, not this BYBIT-specific issue; this BYBIT finding would be the NEXT blocker once the primary one is
resolved via a split-table design.

## Suggested remediation (not scoped/estimated — future plan should own this)

1. Confirm the exact date range affected (spot-checked 2026-01 and mid-2026; the full window needs a proper day-by-day
   audit, not sampling).
2. Backfill/re-shape the 2026-01→2026-07-09 window: parse the glued `BTCUSDT.parquet` filenames back into
   `{underlying}/{quote}` (same split logic the 2026-07-09 code fix now uses going forward), write to the correct
   `underlying=` hive path, verify parity, then decide whether to clean up the flat originals (mirrors the same
   data-safety discipline as any other legacy-shape migration in this workspace — do not delete before verifying).
3. Decide whether the 2023-06/2025-01-era legacy flat siblings are safe-to-delete duplicates (their hive-form twins
   already exist) or need their own investigation — this issue doc did not verify duplication status for that older
   window, only confirmed the coexistence.

## Not done here

Read-only investigation only — no GCS objects modified, no code changed. This needs its own scoped plan when picked up
(estimate class: likely `infra` given the backfill/reshape nature, similar to other legacy-shape migrations in this
workspace).
