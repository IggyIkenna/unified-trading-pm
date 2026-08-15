---
doc_type: issue
title:
  vault_share_price_handler.py's manifest record_captured call never stamps instrument_id (per-(protocol,chain)
  aggregate, not per-instrument grain)
summary: >-
  Discovered while verifying the defi_venue_pipeline_to_live_ao_build_2026_07_30.md todo-3 backfill and building todo
  4's catalogue-registration script. `vault_share_price_handler.py::_record_shard_captured` calls
  `recorder.record_captured(venue=protocol, chain=chain, ...)` once per (protocol, chain) group, summing `rows_written`
  across every instrument shard in that group, but never passes `instrument_id=` — every vault_share_price manifest row
  (MAKER/sDAI, YEARN_V3's 3 vaults, ETHENA, FRAX, MORPHO_VAULTS' 2 vaults) has a null instrument_id. Confirmed directly
  (not guessed): a fresh, correctly-written MAKER/sDAI row for 2026-07-30 has `instrument_id=None` in both the per-VM
  shard and the live-merged manifest read, even though the underlying GCS object
  (`.../data_type=vault_share_price/MAKER-ETHEREUM:YIELD_BEARING:sDAI.parquet`) itself carries a well-formed
  `instrument_id` column value. `lst_rates_handler.py`'s sibling `_write_single_lst_group` already has the fix for this
  exact shape (per-instrument-shard `record_captured` calls with `instrument_id=` derived from each shard's own data)
  per its own docstring citing `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "per-instrument manifest grain" fix —
  `vault_share_price_handler.py` was apparently never given the same treatment.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, vault-share-price, manifest, instrument-id, per-instrument-grain]
related:
  [
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md,
  ]
created: "2026-07-31"
author: unknown
last_updated: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >-
  Found by slot-16 (data_engineering craft) while verifying/registering the 6-venue MAKER-ETHEREUM vault_share_price
  backfill for defi_venue_pipeline_to_live_ao_build_2026_07_30.md todo 3/4. Not fixed inline — fixing it would require a
  re-backfill (freshness-skip means the already-captured 90-day window won't re-run just because the code changed) which
  is out of scope for a "register the catalogue" todo; the catalogue registration script instead read instrument
  identity directly from real written GCS objects, sidestepping this gap rather than depending on it.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_lst_rates_write.py,
    /plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md,
  ]
---

# vault_share_price_handler.py manifest instrument_id gap

## What I found

`market_tick_data_service/cli/handlers/vault_share_price_handler.py::_write_group_shard` calls `write_defi_rows(...)`
which correctly splits a (protocol, chain) group into one parquet shard PER instrument (e.g. YEARN_V3/ETHEREUM → 3
shards: yvUSDC-1, yvDAI-1, yvWETH-1), and each written shard's filename/content DOES carry a well-formed `instrument_id`
(confirmed: `MAKER-ETHEREUM:YIELD_BEARING:sDAI`). But `_record_shard_captured` — called once per group, not once per
shard — records a SINGLE manifest row per (protocol, chain) with `rows_written` summed across every shard, and never
passes `instrument_id=` to `recorder.record_captured(...)`. Every manifest row this handler writes therefore has
`instrument_id=None`.

Compare `lst_rates_handler.py`'s `_lst_rates_write._write_single_lst_group`, which already loops each written shard and
calls `recorder.record_captured(..., instrument_id=instrument_id, ...)` per shard — the correct, already-proven pattern
for this exact multi-instrument-per-group shape.

## Why it matters

- Per-instrument honest-coverage (`expected_unattempted` reconciliation, catalogue-residual empty-marking via
  `catalogue_pool_ids_for_shard`) depends on a real `instrument_id` per manifest row. A null `instrument_id` means any
  downstream per-instrument reconciliation for vault_share_price venues silently can't match manifest rows to catalogue
  entries — the exact class of gap `defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md` (cited in
  `_lst_rates_write.py`'s own docstring) already fixed for `lst_rates`.
- Blast radius: every vault_share_price venue (MAKER, YEARN_V3, ETHENA, FRAX, MORPHO_VAULTS), not just MAKER — MAKER is
  simply the venue this session happened to be verifying.

## Todos

- [x] ✅ [DATA] P2. Fix `vault_share_price_handler.py::_write_group_shard`/`_record_shard_captured` to record ONE
      `record_captured` call PER WRITTEN SHARD (mirroring `_lst_rates_write._write_single_lst_group`'s loop), each with
      its own shard's real `instrument_id`, instead of one aggregate call per (protocol, chain) group. After shipping,
      re-run (or wait for the next natural cron cycle to organically produce) at least one day of fresh
      vault_share_price data per venue and confirm the manifest row now carries a non-null `instrument_id` matching the
      written GCS object's own `instrument_id` column. Does NOT require re-backfilling the already-captured 90-day
      window from `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` todo 3 — that data stays valid
      (source=onchain_rpc correctly tagged, capture_status=captured correctly recorded); only the `instrument_id` field
      on NEW/future rows needs the fix. (repo: market-tick-data-service) — market-tick-data-service@b0909a5e. Loop now
      mirrors `_write_single_lst_group`: one `record_captured` per written instrument shard with that shard's own
      lowercased `instrument_id`. Regression test added (`test_process_record_captured_stamps_instrument_id_per_shard`)
      asserting `record_captured` fires once per registry vault with a distinct non-blank `instrument_id`. Verification
      of the next NATURAL fresh capture (cron-produced manifest row with non-null `instrument_id`) is still outstanding
      — not yet observed live, since this fix only affects rows written going forward.

## Progress Log

- **2026-07-31 (slot-16, data_engineering craft)**: filed after discovering the gap while verifying/registering todo 3/4
  of `defi_venue_pipeline_to_live_ao_build_2026_07_30.md`. Not fixed inline (see `source:` above for why).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries) — swapped in the actual handler being fixed
  (`vault_share_price_handler.py`) plus the sibling file with the already-proven fix pattern (`_lst_rates_write.py`),
  dropped the archived origin plan (context now redundant with the body).
- **2026-08-04 (slot-6, data_engineering craft)**: shipped the fix — `market-tick-data-service@b0909a5e`.
  `_write_group_shard`/`_record_shard_captured` now loop each written instrument shard (same shape
  `_lst_rates_write._write_single_lst_group` already proved) and call `record_captured` once per shard with that shard's
  own lowercased `instrument_id`, instead of one aggregate (protocol, chain) call with a blank `instrument_id`. Added
  `test_process_record_captured_stamps_instrument_id_per_shard` asserting `record_captured` fires once per registry
  vault, each with a distinct non-blank `instrument_id`. Pass-1 `quality-gates.sh` green (sentinel = `b0909a5e`),
  shipped via `quickmerge --agent`, verified on `origin/live-defi-rollout`. Does NOT include the todo's live
  confirmation step (waiting for a natural fresh capture / next cron cycle to show a non-null `instrument_id` manifest
  row) — that observation is still outstanding since it only affects rows written going forward; leaving `status: open`
  until someone confirms a live post-fix manifest row.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **2026-08-15 (slot-19, data_engineering craft)**: read the live-merged availability manifest
  (`market-data-tick-defi-prd-central-element-323112`) for `data_type=vault_share_price`, `date>2026-08-04`, filtered to
  MAKER/YEARN_V3/ETHENA/FRAX/MORPHO_VAULTS. 4/5 venues confirmed: every `capture_status=captured` row carries a
  non-null, well-formed `instrument_id` (e.g. MAKER 2026-08-14 → `maker-ethereum:yield_bearing:sdai`), proving
  `market-tick-data-service@b0909a5e`'s fix landed correctly. MORPHO_VAULTS returned zero rows in the entire post-08-04
  window (a second, wider history query for MORPHO_VAULTS alone was memory-capped/killed — the `venue=` predicate
  doesn't row-group-prune the ~27M-row DeFi index the way a `date` predicate does; not retried with a larger cap per the
  shared-host memory-bounding rule). Filed the MORPHO_VAULTS zero-capture gap as a new Follow-up todo above — it is a
  distinct issue from this doc's instrument_id fix, not a fix-verification failure. Status stays `open` (not all 5
  venues confirmed); flip to resolved once MORPHO_VAULTS's gap is diagnosed and either fixed or found to be an
  intentional pause.

## Follow-ups

- [x] ✅ [DATA] P3. Confirm a live post-fix vault_share_price manifest row carries a non-null instrument_id (observe the
      next natural cron capture after market-tick-data-service@b0909a5e). — 4/5 venues confirmed 2026-08-15 (slot-19):
      MAKER (26 rows, 26 non-null incl. `maker-ethereum:yield_bearing:sdai` captured 2026-08-14), YEARN_V3 (45 rows, 45
      non-null across all 3 vaults), ETHENA (15 rows, 15 non-null), FRAX (15 rows, 15 non-null) — all post-08-04
      `capture_status=captured` rows carry a well-formed lowercased `instrument_id`. MORPHO_VAULTS has ZERO
      vault_share_price manifest rows of any kind after 2026-08-04 — not a fix-verification failure, a separate capture
      gap (see new follow-up below).
- [ ] [DATA] P3. **MORPHO_VAULTS vault_share_price has captured zero manifest rows since 2026-08-04** — diagnose whether
      the cron/handler is failing silently for this venue specifically (permission error, catalogue lookup gap, RPC
      failure) or the venue was deliberately paused; the other 4 vault_share_price venues (MAKER/YEARN_V3/ ETHENA/FRAX)
      are all capturing normally in the same window. (repo: market-tick-data-service)

> **2026-08-06 archive-candidate audit**: Fix shipped at b0909a5e but Progress Log explicitly leaves status open:
> 'Verification of the next NATURAL fresh capture ... is still outstanding' — live post-fix manifest-row confirmation
> not yet observed.
