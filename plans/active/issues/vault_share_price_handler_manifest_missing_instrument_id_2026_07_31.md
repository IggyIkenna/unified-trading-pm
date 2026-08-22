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
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
  # 2026-08-21 (archival sweep): dropped defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20 (archived to
  # plans/archive/issues/, fully resolved — the systemic write-path fix landed market-tick-data-service@4ca2640d).
  # 2026-08-21 (QG fix, escalation agt-b4a8e9): that drop left this doc orphaned from its AG-closeout family
  # (ratchet regression, ag_closeout_linkage_baseline.yaml orphan_count=0) — re-linked to defi's closeout.
created: "2026-07-31"
author: unknown
last_updated: "2026-07-31"
parent_epic: security_and_cross_cutting_master
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
    market-tick-data-service/scripts/rename_vault_venue_canonical.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# vault_share_price_handler.py manifest instrument_id gap

> Originating build plan (resolved, archived — cited here as historical evidence, per the archive-safety ratchet,
> operator ruling 2026-08-17): `/plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md`.

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
- [x] ✅ [DATA] P3. **MORPHO_VAULTS vault_share_price has captured zero manifest rows since 2026-08-04** — diagnose whether
      the cron/handler is failing silently for this venue specifically (permission error, catalogue lookup gap, RPC
      failure) or the venue was deliberately paused; the other 4 vault_share_price venues (MAKER/YEARN_V3/ ETHENA/FRAX)
      are all capturing normally in the same window. (repo: market-tick-data-service) —
      market-tick-data-service@1a4db09a9d. Root-caused 2026-08-16 (slot-24): NOT a capture failure. The handler writes
      real, correct parquet objects to GCS every day (confirmed 2026-08-01 through 08-14, 2 objects/day under
      `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=MORPHO_VAULTS/...`), but
      `"MORPHO_VAULTS"` (underscore) is a registered UAC `DEPRECATED_DEFI_GHOST_VENUE_NAMES` entry, superseded by
      canonical `"MORPHOVAULTS"` (no underscore) — the manifest consolidator silently drops its rows at merge time, so
      the venue read as "never capturing" even though it ran successfully every day. The sibling YEARN_V3 spelling was
      already canonical (kept its underscore); MORPHO_VAULTS was the one gap. Fixed both `_VAULTS` entries
      (`steakUSDC`, `GTUSDCP`) in `vault_share_price_handler.py` to `protocol="MORPHOVAULTS"`, corrected the misleading
      comment above `_VAULTS` that had implied both were already canonical, and added a regression test
      (`test_no_vault_protocol_uses_a_deprecated_ghost_venue_name`) asserting no `_VAULTS` entry uses a
      `DEPRECATED_DEFI_GHOST_VENUE_NAMES` token. Only affects rows written going forward under the new spelling; the
      historical GCS objects/manifest rows under the old `MORPHO_VAULTS` spelling (2026-05-01 onward) are untouched by
      this commit — see new Follow-up below for that migration.

## Follow-ups (new)

- [ ] [DATA] P3. **Migrate historical MORPHO_VAULTS-spelled GCS objects + manifest rows to canonical MORPHOVAULTS**
      (2026-05-01 through 2026-08-16, ~3.5 months) — the existing
      `market-tick-data-service/scripts/rename_vault_venue_canonical.py` "Phase 1.5a-3" one-off only rewrites the
      manifest `venue` COLUMN in `_index/availability_index.parquet`; it does NOT touch the underlying GCS object
      paths/content (which still embed `venue=MORPHO_VAULTS` in the path and filename). A correct fix needs a proper
      path+content+manifest migration (copy/rewrite objects under the new venue segment, then update or regenerate the
      manifest rows), not just the manifest-only rename. Follow delete-safety protocol for any old-path object removal
      once the new-path copies are verified. (repo: market-tick-data-service)

> **2026-08-06 archive-candidate audit**: Fix shipped at b0909a5e but Progress Log explicitly leaves status open:
> 'Verification of the next NATURAL fresh capture ... is still outstanding' — live post-fix manifest-row confirmation
> not yet observed.

- **2026-08-16 (slot-24, data_engineering craft)**: root-caused and fixed the MORPHO_VAULTS zero-capture follow-up
  (task `vault_share_price_handler_manifest_missing_instrument_id-f27451ef0961`). Initial investigation used a GCS
  prefix missing the `pipeline_mode=batch_onchain_rpc/` path segment (sits between `day=` and `asset_group=` in the
  canonical layout) and produced a false "0 objects" read, which briefly pointed the investigation at the wrong
  hypothesis (RPC/write/schema layers — all independently verified healthy). Corrected the prefix and confirmed real
  parquet objects exist for every day 2026-08-01 through 08-14. Actual cause: `"MORPHO_VAULTS"` is a UAC
  `DEPRECATED_DEFI_GHOST_VENUE_NAMES` entry, silently dropped by the manifest consolidator at merge time — a
  venue-canonicalization gap in the writer, not a capture/scheduling/credential failure. Shipped
  `market-tick-data-service@1a4db09a9d` (code fix + comment fix + regression test), Pass-1 `quality-gates.sh` green,
  ancestry-verified on `origin/live-defi-rollout`. Push was delayed ~15+ min by sustained multi-slot QG-governor
  contention on this repo (sentinel invalidated repeatedly by peer pushes, `market-tick-data-service` sub-cap 1
  queued 500+s more than once) — resolved by retrying once contention eased rather than force-pushing or bypassing
  the gate. Filed the historical GCS-path+manifest migration (the pre-fix `MORPHO_VAULTS`-spelled backlog,
  2026-05-01 onward) as a new, distinct Follow-up above — the existing `rename_vault_venue_canonical.py` script is
  manifest-column-only and insufficient alone. Status stays `open` pending that follow-up.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) — swapped in the pending migration script
  (`rename_vault_venue_canonical.py`) and the delete-safety codex doc it must follow, dropped `_lst_rates_write.py`
  (its pattern-reference is now stale — the instrument_id fix it modeled is already shipped and verified).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)
