---
doc_type: issue
title: >-
  DeFi manifest `instrument_type=POOL` (uppercase) `dex_pool_swaps` captured rows regrew from 0 (2026-08-05, fold
  verified clean) to 7,930,863 (2026-08-11) — mechanism UNRESOLVED, blocks
  `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2-4
summary: >-
  `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 1 (2026-08-11) freshly measured 7,930,863
  `instrument_type=POOL` (uppercase) captured rows in `data_type=dex_pool_swaps` — directly contradicting
  `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P3 todo, which recorded a full-corpus verified "0
  `instrument_type=POOL` rows remain" on 2026-08-05 after `fold_pool_instrument_type_casing_2026_08_05.py --apply`. A
  slot-31 worker then attempted todo 2's retirement and found the CANONICAL `pool` (lowercase) population is itself
  mixed — ~5.36M of ~8.75M captured rows still carry the full wrapped `VENUE-CHAIN:POOL:id` instrument_id string
  verbatim (only the outer `instrument_type` label was ever casing-fixed, the id string itself was never re-derived to
  bare form) — and correctly refused to retire against an unwrap-based key match that couldn't safely distinguish real
  duplicates from same-string-different-data collisions (0/1,135,962 candidate keys matched, 0 retired — the safety gate
  working as designed, not a bug). This doc adds a SEPARATE, deeper open question this session surfaced while trying to
  root-cause why the uppercase population is back at all: verified NEITHER of the two obvious explanations holds. (1) No
  live writer regression — the only live `record_captured` call site for `dex_pool_swaps` pool-grain rows
  (`market-tick-data-service/cli/handlers/_dex_swaps_queries.py:174-182`, `record_swap_pool_map`) passes
  `instrument_type="pool"` (lowercase literal string) with a bare lowercased pool address, not the uppercase enum. (2)
  Not the manifest rebuild re-emitting stale casing either — `rebuild_defi_manifest.py::parse_hive_path` unconditionally
  `.lower()`s the `instrument_type` it derives from the on-disk hive path segment (comment: "N6a: instrument_type
  lowercased (collapses the pool/POOL case-dup; controlled vocab)"), and that fix shipped 2026-06-18
  (`market-tick-data-service@3f5cc6e4`) — over 6 weeks before the `canonical-migration-defi-rebuild-20260810-093118`
  →`...-204358` VM chain that just completed (per this same plan's todo 1) ran. Neither obvious writer nor the rebuild's
  own path-parsing logic should be able to produce a fresh uppercase `POOL` manifest row today. Yet the population went
  0 → 7.9M in the 6 days between the fold's verification and this reading. **Mechanism not found** — this doc records
  what was ruled out, not a diagnosed root cause, and blocks safe retirement: retiring the 7.9M rows again without
  understanding why they came back risks the exact same "fixed, then silently reverted" cycle the 2026-08-05 fold
  already went through once.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [defi, manifest, pool-casing, dex-pool-swaps, data-correctness, ssot-contradiction, recurrence, root-cause-unresolved]
related:
  [
    /plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/canonical-cutover-register.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-11"
parent_epic: manifest_master
priority: P1
locked_by:
resolved_by:
assigned_vm: planning
author: slot-4 (data_engineering)
source: >-
  Surfaced while working `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2 (dispatched task
  `defi_pool_rate_indices_dex_pool_fees_retirement-de3dd51056c2`); the todo was already NOT-DONE (slot-31 content-verify
  block) — this doc documents a second, independent blocking gap found while researching how to safely resolve the first
  one.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/canonical-cutover-register.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_swaps_queries.py,
  ]
---

# DeFi `instrument_type=POOL` recurrence after a verified fold — root cause unresolved

## What I found

1. **2026-08-05**: `fold_pool_instrument_type_casing_2026_08_05.py --apply --fold-no-twin-cells` ran against prod
   (`market-tick-data-service@87e9e100`). Reported: 1,351 rows retired (twin-exists, `capture_status→attempted_failed`)
   - 1,937,619 rows folded in-place (`POOL→pool`, no twin, id string left untouched). Same-day re-verification (full
     605-row-group / 74,375,757-row scan) confirmed **0** `instrument_type=POOL` rows remained, 8,214,021 canonical
     `pool` rows present. Recorded DONE in `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` P3.
2. **2026-08-11**: `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 1 (post-rebuild stability check,
   3 queries 17:37-17:43 UTC, identical each time) found **7,930,863** `instrument_type=POOL` captured rows in
   `data_type=dex_pool_swaps` alone. Canonical `pool` captured count is now ~8.75M (up from 8.21M — consistent with ~6
   days of ordinary new-capture growth, not itself suspicious).
3. **Ruled out as the mechanism** (this session, direct code reads, not inference):
   - **Live writer regression**: `_dex_swaps_queries.py:162-182` (`record_swap_pool_map`, the only live
     `record_captured` call site for `dex_pool_swaps` pool-grain rows) passes `instrument_type="pool"` (lowercase
     literal) and `instrument_id=pool_id_lower` (bare, `.lower()`'d pool address) — not the uppercase enum, not a
     wrapped id. Every other `InstrumentType.POOL` usage found repo-wide (`_dex_pools_subgraph.py:596`,
     `orca_whirlpool_state_handler.py:453`, `raydium_classic_amm_handler.py:319`) is a `write_defi_rows(...)` GCS-write
     call (`data_type="dex_pool_state"`, a DIFFERENT data_type from `dex_pool_swaps`), which internally lowercases both
     the GCS path segment (`unified_api_contracts/canonical/partition_paths.py:184`) and the row-content column — not a
     `record_captured` call, and not this data_type.
   - **Manifest rebuild**: `rebuild_defi_manifest.py::parse_hive_path` (both the canonical-layout and legacy-fallback
     branches) unconditionally does `instrument_type=p["itype"].lower()` — comment: "N6a: instrument_type lowercased
     (collapses the pool/POOL case-dup; controlled vocab)". This fix shipped 2026-06-18
     (`market-tick-data-service@3f5cc6e4`, confirmed via `git log -S`), more than 6 weeks before the
     `canonical-migration-defi-rebuild-20260810-093118`→`...-204358` VM chain (the one this same plan's todo 1 verified
     reached terminal SUCCESS) ran. A rebuild using this code cannot emit a literal uppercase `POOL` row from what it
     scans on disk.
4. **What I did NOT verify** (ran out of bounded-investigation budget for this task — flagging rather than guessing):
   - ~~Whether the completed rebuild VM actually ran the current `HEAD` code or a stale pre-N6a tarball snapshot~~ —
     **RESOLVED 2026-08-12 (slot 5, data_engineering), RULED OUT.** `-204358` (the VM that reached terminal SUCCESS) had
     `MTDS_TARBALL_SHA` FLOATING in its `TARBALL_PINS.json` (no exact resolved commit_sha recorded — a genuine
     observability gap in `create-code-tarballs.sh`'s floating-pin path, flagged as a follow-up but not fixed here,
     infra-craft scope). Bounded it instead:
     `git log 3f5cc6e4..HEAD -- market_tick_data_service/scripts/rebuild_defi_manifest.py` shows 12 commits touching
     this file between the N6a fix (2026-06-18) and the current tarball HEAD (`market-tick-data-service@859405a1`,
     2026-08-11T23:00:56Z), none reverting the `parse_hive_path` lowercasing; confirmed both call sites
     (`instrument_type=p["itype"].lower()`, lines 370 + 395) intact at HEAD. A floating tarball is built from whatever
     HEAD is checked out when `create-code-tarballs.sh` last ran, so no snapshot in that window could have shipped
     pre-N6a code. Full evidence: `/plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`
     Progress Log, 2026-08-12 entry.
   - ~~Whether the rebuild is a full index REPLACE or an UPSERT-onto-existing-index~~ — **RESOLVED 2026-08-12 (slot 32,
     data_engineering): UPSERT-onto-existing-index, NOT full-replace.** The rebuild's only index write is a per-VM shard
     (`_build_manifest_writer()` → `ManifestWriter(per_vm_shards=True)` → `_index/per_vm/{instance}.parquet`); the
     consolidator merges shards into the canonical `_index/availability_index.parquet` asynchronously (last-attempted-
     write wins per dedup key — UTL `_writer.py` + `_read_index.py::_read_and_merge_per_vm_shards`). The rebuild never
     deletes/rewrites rows its scan doesn't touch and `parse_hive_path` lowercases `instrument_type`, so the 7.9M
     uppercase rows were PRESENT pre-rebuild (by 2026-08-10) and passed through untouched — narrowing the recurrence
     window to the 08-05→08-10 pre-rebuild gap. Full evidence: the plan's Progress Log, 2026-08-12 entry.
   - Whether physical GCS objects with a genuinely uppercase `instrument_type=POOL/` path segment exist on disk at all
     (a `gcs_describe_object`/`list_blobs` sample under that literal prefix would settle this directly).

## Why it matters

`defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2's stated done-when is "0 remaining captured rows
with `instrument_type=POOL`" — but the 2026-08-05 fold already reached that state once and it did not hold. Any
retirement now, even setting aside slot-31's separate content-verify blocker on the wrapped-id matching scheme, risks
being silently reverted again by whatever mechanism produced this recurrence — which is not yet understood. Retiring
into an unknown-recurring population is not a safe basis for closing todos 2-4.

## Recommended decision

Before todo 2 (or 3/4) attempts another retirement:

1. Confirm the rebuild VM's actual deployed code content (`cloudbuild`/tarball manifest `commit_sha`, per the pattern
   `defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md` already used) — rule in/out a stale snapshot.
2. Confirm whether the rebuild is full-replace or upsert-onto-existing (read `rebuild_defi_manifest.py`'s top-level
   `main()`/index-write path, not yet read this session).
3. Sample a handful of the 7,930,863 uppercase rows' underlying GCS objects directly (`gcs_describe_object`/`list_blobs`
   under `instrument_type=POOL/`) to settle whether they're a manifest-column-only artifact (as the 2026-08-05 fold
   assumed) or genuinely reflect physical objects at an uppercase path — the latter would mean this needs the Part-5
   "legacy COPIED not MOVED" migration treatment (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part
   5), not a manifest-only patch.
4. Only once the recurrence mechanism is understood, decide whether todo 2 retires safely (recommend: yes, once (1)-(3)
   land and content-verify from the sibling blocker also clears) or whether the underlying pipeline needs a durable fix
   first so this doesn't recur a third time.

No irreversible action taken or proposed here — this is a manifest-status-flip-adjacent investigation gap, not a GCS
delete, but the same evidentiary bar applies given real financial data is at stake.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (5 entries)
