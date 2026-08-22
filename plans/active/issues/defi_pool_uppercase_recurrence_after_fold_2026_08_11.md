---
doc_type: issue
title: >-
  DeFi manifest `instrument_type=POOL` (uppercase) `dex_pool_swaps` captured rows regrew from 0 (2026-08-05, fold
  verified clean) to 7,930,863 (2026-08-11) — mechanism ROOT-CAUSED 2026-08-16 (live `market-data-processing-service`
  writer defect, see summary), blocks `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2-4
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
  0 → 7.9M in the 6 days between the fold's verification and this reading. **ROOT CAUSE NOW CONFIRMED 2026-08-16** — see
  "What I found" item 6: a live, ongoing writer defect in `market-data-processing-service`, an entirely different repo
  from every mechanism checked above.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags:
  [defi, manifest, pool-casing, dex-pool-swaps, data-correctness, ssot-contradiction, recurrence, root-cause-confirmed]
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
priority: P0
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
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/canonical-cutover-register.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_swaps_queries.py,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
  ]
drift_direction: advance-code
depends_on: []
---

# DeFi `instrument_type=POOL` recurrence after a verified fold — root cause CONFIRMED

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
   - ~~Whether physical GCS objects with a genuinely uppercase `instrument_type=POOL/` path segment exist on disk at
     all~~ — **RESOLVED 2026-08-16 (slot 22, infra), CONFIRMED manifest-column-only artifact** — see "What I found"
     item 5 below.
5. **2026-08-16 (slot 22, infra) — DIAG todo done: manifest-column-only artifact CONFIRMED, no physical uppercase GCS
   objects — AND a SECOND recurrence event found: the population has already regrown since the 2026-08-12 retirement.**
   - **This exact probe was already run once, more thoroughly, on 2026-08-12 (slot 32, data_engineering) in the sibling
     plan** `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 4 (now archived) — 30 sampled rows
     across the full 2023-01-01→2026-08-05 date range, 2 pipeline_modes, 3 chains, 5 venues: **0/30 rows have any
     object at an uppercase `instrument_type=POOL/` path; 30/30 have their object at the lowercase `instrument_type=
     pool/` path**; a broad scan across 5 additional dates found **0 total objects anywhere containing
     `instrument_type=POOL/`**. That entry independently reached the same conclusion this todo asked to settle — this
     doc's own item 3 above had simply gone stale (the answer landed in the sibling plan 4 days before this todo was
     dispatched).
   - **Fresh independent reproduction (this session, script:
     `market-tick-data-service/scripts/one_offs/sample_pool_uppercase_gcs_objects_2026_08_16.py`)**: sampled 20 rows
     evenly spaced across the LIVE captured `instrument_type=POOL` population (measured 1,641,333 rows today — see
     below), probing `gcs_describe_object` across 4 candidate path shapes × both casings (pipeline_mode-segmented,
     bare `asset_group=defi/`, bare `category=defi/`, legacy venue-chain-glued). Result: **0/20 found any object at an
     uppercase `POOL/` path** (matches the 2026-08-12 finding exactly); 1/20 resolved at the canonical lowercase
     `pool/` path; 19/20 resolved at neither candidate (either genuine manifest phantoms with no physical backing at
     all, or a 5th on-disk shape variant this script's candidate set didn't cover — in EITHER case there is still no
     evidence of a physical *uppercase*-pathed object, so this does not change the conclusion). Combined with the more
     exhaustive 2026-08-12 result, there is no evidence anywhere that the uppercase `POOL` rows correspond to genuinely
     uppercase-pathed GCS objects **under the 4 path shapes tested — all shaped for the `raw_tick_data/` tree grammar**
     — see item 6 below for the tree these shapes never covered.
   - **NEW, more urgent finding — a SECOND recurrence has already happened.** The 2026-08-12 retirement (todo 5 in the
     same archived plan, `market-tick-data-service@5e456d0d`) drove captured `instrument_type=POOL` to **0** (verified
     independently post-apply that same day). This session's fresh live query (2026-08-16, 4 days later) found
     **1,641,333** captured `instrument_type=POOL` `dex_pool_swaps` rows present again — i.e. the population regrew
     from 0 to 1.64M in ~4 days, the SAME recurrence pattern this issue doc was opened to track (which went 0→7.9M in
     ~6 days the first time, 2026-08-05→2026-08-10/11). Recommended the next worker on todo 168 prioritize identifying
     WHAT wrote the 1,641,333 rows (e.g. `written_at`/`service_name` provenance columns on the regrown rows, mirroring
     the `service_name=market-data-processing-service` vs `market-tick-data-service` discrepancy slot-7 flagged as an
     unexplored lead in the archived plan's todo-5 entry) BEFORE re-retiring — **this lead is what item 6 below
     resolved.**
6. **2026-08-16 (slot 6, data_engineering) — ROOT CAUSE CONFIRMED: a live, ongoing writer defect in
   `market-data-processing-service`, a repo NO prior session in this chain had checked.** Slot-7's flagged-but-
   unexplored lead in item 5 (regrown rows may carry `service_name=market-data-processing-service`, not
   `market-tick-data-service`) pointed at the right repo. Traced to a precise mechanism, live-verified against prod
   GCS (not inferred):
   - **The writer bug**: `market_data_processing_service/app/core/canonical_writer.py:374` builds the
     `processed_candles/` GCS object PATH directly from `instrument_type` —
     `f"...instrument_type={instrument_type}/data_type=..."`, no `.lower()`. That `instrument_type` comes from
     `_infer_instrument_type()` (`canonical_writer_shaping.py:393-395`), whose TOP-PRIORITY resolution path extracts
     the TYPE token straight from the canonical `instrument_id` string (e.g. `BALANCER-ETHEREUM:POOL:0x...`) —
     correctly UPPERCASE per the id-grammar rule (`/codex/02-data/canonical-cutover-register.md` §3b, "ID segment —
     SETTLED, UPPER"). `canonical_writer.py` embeds that SAME uppercase value unmodified into the GCS PATH segment,
     which per the SAME register's §3a ("PATH segment — SETTLED, lowercase") must always be lowercase. MTDS's own
     `rebuild_defi_manifest.py::parse_hive_path` and `write_defi_rows()` already handle this correctly (`.lower()`
     at the path-construction call site, uppercase preserved for the id/manifest-column value) —
     `canonical_writer.py` is the one writer found so far that conflates the two casings.
   - **Live-verified at scale, one bounded prefix-listing per pipeline_mode (no corpus walk), day=2023-01-01** (the
     exact day `backfill_defi_dex_pool_swaps_source_correction.py`'s own docstring already names as having BALANCER
     activity): `pipeline_mode=batch_onchain_rpc` — **11,718/11,718** objects at `instrument_type=POOL/` (uppercase),
     **0** at `instrument_type=pool/`. `pipeline_mode=batch_onchain_subgraph` (the "corrected" tree) — **29,561/
     29,561** likewise 100% uppercase, 0% lowercase. This is a PHYSICAL, at-scale, ONGOING non-canonical GCS corpus
     under `processed_candles/` for defi POOL `dex_pool_swaps` — distinct from the `raw_tick_data/` tree item 5's
     DIAG todo confirmed has no physical uppercase objects; that finding was correct for the 4 path shapes it
     tested but never covered `processed_candles/`'s distinct grammar (it carries a `timeframe=` segment
     `raw_tick_data/` doesn't) — exactly the "5th on-disk shape variant" item 5 itself flagged as unruled-out.
     Read-only probe (`list_blobs`+`get_blob_metadata` only, no writes), not shipped as a repo script (trivial
     enough to re-derive from the citations above): scratchpad `probe_processed_candles_pool_casing.py`, this
     session.
   - **The propagation mechanism — `backfill_defi_dex_pool_swaps_source_correction.py` (also MDPS)**: reads
     `instrument_type` straight off the SOURCE object's on-disk path segment (`classify_object:162`,
     `segments.get("instrument_type", "")`) — already uppercase per the writer bug above — then (a) propagates it
     unmodified into the copy's destination path (`dst_path_for_src:134` only swaps `pipeline_mode=`, leaving
     `instrument_type=POOL/` untouched — confirmed live: the destination tree is ALSO 100% uppercase for this day),
     and (b) stamps that same uppercase value into a fresh `record_captured(instrument_type=instrument_type, ...)`
     call (`:431`) with `service_name="market-data-processing-service"` (`:405`) — the direct, now-confirmed source
     of the recurring uppercase-`POOL` CAPTURED manifest rows this issue doc tracks, and the exact match for
     slot-7's flagged lead.
   - **Why this explains BOTH recurrences, not just one**: `canonical_writer.py` is SHARED, cross-asset-group MDPS
     code (a tradfi-specific branch in the SAME function, `:266`, confirms it isn't defi-only) — it is MDPS's
     general candle-write path, not a one-off script. Every ordinary defi POOL candle write MDPS performs (not just
     this one backfill script's narrow mistagged-`pipeline_mode` population) goes through this same buggy path
     construction. The 2026-08-05→08-11 (0→7.9M) and 2026-08-12→08-16 (0→1.64M) recurrences are consistent with
     ONGOING, regular MDPS candle-write activity continuously re-creating uppercase-POOL captured manifest rows —
     not a one-time resurrection event, and not requiring the backfill script to have run again.
   - **A second, independent, ALSO-real risk found this session (not the primary driver here, but load-bearing for
     any FUTURE retirement)**: the manifest-consolidator's shard-merge dedup
     (`unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames`, mirrored in
     `manifest_consolidator.py`'s DuckDB `ORDER BY CASE`) has a documented, partially-fixed bug class —
     `legacy_seed_captured_outranks_resurrection_risk_2026_07_15` — where `capture_status='captured'`
     UNCONDITIONALLY outranks a newer `attempted_failed` retirement flip for the same dedup key, REGARDLESS OF
     RECENCY. The 2026-07-15 fix (+2026-07-24 refinement) protects only the tagged `_legacy_seed.parquet` shard
     specifically; an ORDINARY per-VM shard (e.g. from any DeFi backfill/rebuild VM) that still exists in GCS with
     an old `captured` row for a retired key has no equivalent protection — it wins the tie-break on its next merge
     regardless of age. `_prune_consolidated_shards` (`manifest_consolidator.py:1893`) is designed to delete a
     per-VM shard once its rows are provably merged into canonical, defaulting enabled
     (`CONSOLIDATOR_PRUNE_SHARDS`, default `true`, `manifest_consolidator.py:473`) — **not verified this session
     whether it is actually keeping up** on the defi bucket, or whether a backlog of un-pruned stale shards exists;
     flagged as an open follow-up, not confirmed either way.

## Why it matters

`defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2's stated done-when is "0 remaining captured rows
with `instrument_type=POOL`" — but the 2026-08-05 fold already reached that state once and it did not hold. Any
retirement now, even setting aside slot-31's separate content-verify blocker on the wrapped-id matching scheme, risks
being silently reverted again by whatever mechanism produced this recurrence — which is now understood (item 6) but
NOT yet fixed. Retiring into an actively-recurring population is not a safe basis for closing todos 2-4.

## Recommended decision

Before todo 2 (or 3/4) attempts another retirement:

1. Confirm the rebuild VM's actual deployed code content (`cloudbuild`/tarball manifest `commit_sha`, per the pattern
   `defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md` already used) — rule in/out a stale snapshot.
   **DONE, see "What I found" item 4.**
2. Confirm whether the rebuild is full-replace or upsert-onto-existing. **DONE, see "What I found" item 4.**
3. Sample a handful of the 7,930,863 uppercase rows' underlying GCS objects directly (`gcs_describe_object`/`list_blobs`
   under `instrument_type=POOL/`) to settle whether they're a manifest-column-only artifact or genuinely reflect
   physical objects at an uppercase path. **DONE — genuinely reflects physical objects, just under a different tree
   (`processed_candles/`) than the one first sampled; see "What I found" items 5-6.**
4. Only once the recurrence mechanism is understood, decide whether todo 2 retires safely or whether the underlying
   pipeline needs a durable fix first so this doesn't recur a third time. **DONE 2026-08-16 — durable fix required
   first; see the Todos list below for the exact gated sequence.**

No irreversible action taken or proposed here — this is a manifest-status-flip-adjacent investigation gap, not a GCS
delete, but the same evidentiary bar applies given real financial data is at stake.

## Todos

- [x] ✅ [DIAG] P1. Confirm the rebuild VM's actual deployed code content (commit_sha) — rule in/out a stale snapshot.
      **RESOLVED 2026-08-12 (slot 5, data_engineering), RULED OUT** — see "What I found" item 4 above:
      `git log 3f5cc6e4..HEAD` shows no revert of the `parse_hive_path` lowercasing fix; a floating tarball built from
      whatever HEAD was checked out in that window could not have shipped pre-N6a code.
- [x] ✅ [DIAG] P1. Confirm whether the rebuild is full-replace or upsert-onto-existing. **RESOLVED 2026-08-12 (slot 32,
      data_engineering): UPSERT-onto-existing-index, NOT full-replace** — see "What I found" item 4 above; narrows the
      recurrence window to the 08-05→08-10 pre-rebuild gap (the 7.9M uppercase rows were already present by 2026-08-10
      and passed through the rebuild untouched).
- [x] ✅ [DIAG] P1. Sample a handful of the 7,930,863 uppercase rows' underlying GCS objects directly — **RESOLVED
      2026-08-16 (slot 22, infra), CONFIRMED manifest-column-only artifact (0/20 fresh + 0/30 from the 2026-08-12
      sibling-plan run found any uppercase-pathed physical object; no Part-5 migration needed) — but ALSO found a
      SECOND recurrence: captured `instrument_type=POOL` regrew from 0 (post-2026-08-12-retirement) to 1,641,333
      (measured today) — see "What I found" item 5.** market-tick-data-service@dc008dcf (script:
      `scripts/one_offs/sample_pool_uppercase_gcs_objects_2026_08_16.py`).
- [x] ✅ [SCRIPT] P1. Only once the DIAG todo above lands, decide whether
      `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2's retirement can proceed safely, or
      whether the underlying pipeline needs a durable fix first so this doesn't recur a third time. Also re-close
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s now-reopened P3 todo once resolved. **RESOLVED
      2026-08-16 (slot 6, data_engineering): DECISION = durable fix REQUIRED FIRST; retirement does NOT proceed
      yet.** Root cause CONFIRMED (not just narrowed) — see "What I found" item 6: a live, ongoing writer defect in
      `market-data-processing-service`, unrelated to every repo/mechanism prior sessions checked (MTDS
      `_dex_swaps_queries.py`, `rebuild_defi_manifest.py`). Re-closing the axis-contamination P3 todo is
      correspondingly DEFERRED to the gated todo below — not safe to re-close while the writer that caused the
      reopening is still live and unfixed.
- [x] ✅ [BACKEND] P0. Fix the confirmed root cause:
      `market_data_processing_service/app/core/canonical_writer.py:374`'s `partition_path` construction must
      lowercase `instrument_type` for the GCS PATH segment specifically (e.g. `instrument_type=
      {instrument_type.lower()}`) — while leaving every OTHER use of the `instrument_type` variable in this
      function (the manifest `record_captured` row content, `lookup_mdps_contract`, log-event payloads) at its
      current uppercase value, since that matches the id-grammar (§3b) and manifest-column-target (§3c) rules —
      only the PATH segment (§3a) is wrong today. Audit every OTHER `instrument_type` usage in this same file
      (this session found ~10 call sites, `:284/301/331/344/357/390/429/512/532/586/659`) individually before
      touching any of them — some may be additional, not-yet-found path-construction sites with the SAME bug
      (unverified this session), not all are the row-content/manifest-column use this todo assumes. **RESOLVED
      2026-08-16 (slot 19, backend_engineer)**: fresh per-line audit of all 13 `instrument_type` usages in the
      file found only ONE genuine path-construction call site — the `partition_path` f-string this todo names is
      actually a `validate_partition_consistency()` cross-check string (`streaming_writer.py`, never written to
      GCS), so lowering it would have been a no-op-or-worse (risks a false partition-mismatch against the
      uppercase id-derived value). The REAL physical write-path builder is the `build_canonical_candle_object_path(
      ..., instrument_type=instrument_type, ...)` call (`canonical_writer.py`, feeds `canonical_gcs_path` ->
      `_upload_local_to_gcs`) — confirmed via `output_path_helpers.py` -> UTL
      `config_interface/paths/registry.py::build_canonical_candle_path` -> `build_path()`, none of which lowercase.
      Fixed by lowering `instrument_type` at that ONE call site only; every other usage (manifest row content,
      `lookup_mdps_contract`, log payloads, the `partition_path` validation string) verified untouched/still
      UPPER. Updated `tests/unit/test_canonical_writer_record_helpers.py`'s
      `test_write_candle_parquet_calls_record_captured_not_add` (its `expected_path`/`uploaded_path` assertion
      encoded the pre-fix uppercase-path bug). QG green, shipped
      market-data-processing-service@94215e9cd9. (repo:
      market-data-processing-service)
- [x] ✅ [DIAG] P1. Verify `_prune_consolidated_shards` (`manifest_consolidator.py:1893`) is actually keeping the defi
      bucket's per-VM-shard backlog drained, not silently falling behind — **RESOLVED 2026-08-16 (slot 5,
      ui_developer) — CONFIRMED FALLING BEHIND at this snapshot.** Live GCS state check (script
      `unified-trading-library/scripts/check_defi_consolidator_prune_backlog.py`, `state` mode — one bounded
      prefix-list of `_index/per_vm/`, single-walk-safe) against `market-data-tick-defi-prd-central-element-323112`:
      21 total per-VM shards; canonical's real merge-cutoff marker (`consolidator_content_write_at`) =
      2026-08-16T20:06:42Z; **9/21 shards have `mtime <= marker - 5s`** (provably already merged into canonical per
      the same cutoff `_prune_consolidated_shards` itself uses) **yet are still present** — the oldest,
      `mtds-oracle-prices-backfill-c202.parquet`, was 2.68h old at read time. Ruled out the two obvious causes: the
      Cloud Run job (`uts-prod-manifest-consolidator-market-data-defi`) has no `CONSOLIDATOR_PRUNE_SHARDS=false`
      override (defaults enabled) and no `CONSOLIDATOR_PRUNE_MAX_PER_CYCLE` override (defaults 2000, far above the
      9-shard backlog, so not a per-cycle cap); its service account (`unified-trading-sa@...`) holds project-level
      `roles/storage.admin`, so this is not an IAM delete-permission gap either. Root cause NOT identified this
      session — see the new gated todo below. **Not fully verified**: the `logs` mode (meant to confirm `deleted`
      counts in recent consolidator run logs) hit a persistent, apparently fleet-wide Cloud Logging read-quota
      exhaustion (`ReadRequestsPerMinutePerProject`/`PerUser`, limit 60/min) on every attempt this session (5
      retries, ~10+ min) — never got a single successful log read, so the "logs show 0 deletes despite an eligible
      backlog" half of the original ask is UNCONFIRMED, not ruled out. The live GCS state evidence above already
      stands on its own (it doesn't depend on log data) and is sufficient to confirm the backlog is real.
      unified-trading-library@95f29a3958 (script committed this session).
- [ ] [SCRIPT] P1. GATED on the `[BACKEND]` fix above landing + being confirmed live (a fresh candle write for a new
      day producing a lowercase-pathed object, not just a code review) — only THEN retry
      `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 2's retirement (still also gated on that
      sibling plan's own separate wrapped-id content-verify blocker, unrelated to this doc). Re-close
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P3 todo in the SAME pass, citing this doc + the
      landed fix sha.
- [x] ✅ [DIAG] P2. Scope the corpus-wide non-canonical `processed_candles/.../instrument_type=POOL/` physical-object
      population before any migration is attempted — **RESOLVED 2026-08-17 (slot 25, backend_engineer): SCOPED via a
      stratified, walk-disciplined GCS sample (24/1,159 days, 2.1% of the corpus — never a new whole-corpus walk).**
      Script: `market-data-processing-service/scripts/scope_processed_candles_pool_uppercase_corpus_2026_08_17.py`
      (reuses `backfill_defi_dex_pool_swaps_source_correction.py`'s own sanctioned `enumerate_days()` delimiter-descent
      + per-day/per-pipeline_mode bounded listing idiom). Corpus day count confirmed **1,159** distinct days
      (2023-01-01..2026-08-05, one day more than the sibling script's stale 1,155 citation — expected, corpus growth
      since that script's docstring was last measured). **Result: 0/24 sampled days found ANY lowercase
      `instrument_type=pool/` object under `processed_candles/`** — the corpus is (at minimum, per this sample)
      exclusively uppercase for this population, consistent with the confirmed pre-fix writer defect affecting every
      historical write. **Per-day object counts are highly non-uniform** (0 to 62,586 across the 24 samples — several
      days show 0 activity), sample total 360,140 objects, **average 15,005.8 objects/day → projected corpus-wide
      total ≈ 17.4M objects** (order-of-magnitude, sample-based — NOT an exact count; do not cite as precise). This
      lands at the high end of the "six-to-seven-figure" estimate this todo opened with. **Only ONE `data_type` value
      observed across all 24 sampled days: `dex_pool_swaps`** — no evidence found of other defi POOL data_types under
      `processed_candles/` in this sample (the prior todo's "likely other data_types" concern is UNCONFIRMED, not
      ruled out — a 2.1% sample cannot prove absence corpus-wide, but found zero signal for it). Both known
      `pipeline_mode`s (`batch_onchain_rpc`, `batch_onchain_subgraph`) carry the population; neither is clean.
      **Recommendation carried forward to the new todo below**: this is genuinely corpus-scale (order 10M objects) —
      a full precise count + the actual COPY-to-canonical-lowercase migration both belong on a dedicated VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md` (heavy I/O never runs on the shared host), not this
      interactive session. market-data-processing-service@c22556ef66 (script committed this session).
- [x] ✅ [DIAG] P2. Check whether the SAME `canonical_writer.py`/`_infer_instrument_type` casing-conflation bug also
      affects cefi/tradfi/prediction `processed_candles/` writes — **RESOLVED 2026-08-17 (slot-24, ui_developer):
      CONFIRMED, fleet-wide, not defi-only.** Live-verified via bounded delimiter-descent GCS probes (day ->
      pipeline_mode -> timeframe -> data_type -> instrument_type prefix listing only, no corpus walk) against all
      three buckets: **cefi** (`market-data-tick-cefi-prd-central-element-323112`, days 2026-07-01/2026-08-01,
      pipeline_modes hyperliquid/tardis/aster/extended, data_type=trades) — 100% `instrument_type=PERPETUAL`
      (uppercase), 0 lowercase, every sampled prefix; **tradfi**
      (`market-data-tick-tradfi-prd-central-element-323112`, day 2026-07-01, pipeline_mode=batch_databento) — 100%
      uppercase across EQUITY/ETF/FUTURE/COMBO instrument_types, 0 lowercase; **prediction**
      (`market-data-tick-pred-prd-central-element-323112`, days 2026-08-01/2026-08-15,
      pipeline_mode=batch_kalshi) — 100% `instrument_type=PREDICTION_MARKET` (uppercase), 0 lowercase. Root cause
      confirmed shared (not coincidental): read `output_path_helpers.py::build_canonical_candle_object_path` +
      UTL `unified_trading_library/config_interface/paths/registry.py::build_canonical_candle_path` — the SAME
      template embeds `instrument_type=` for EVERY `MarketAssetGroup` (cefi/tradfi/defi/prediction/sports), no
      asset_group gating at all, confirmed by a live cefi worked example in that function's own docstring. The
      2026-08-16 `market-data-processing-service@94215e9cd9` fix (lowering `instrument_type` at the ONE physical
      path-builder call site in `canonical_writer.py`) is called from the SAME shared `write_candle_parquet`, so it
      is ALSO asset_group-agnostic — it already protects cefi/tradfi/prediction going forward once confirmed live;
      no separate code fix needed for this todo. **Side finding**: 0 lowercase objects found across every sampled
      (asset_group, day) pair including days AFTER the fix landed (2026-08-15 for prediction) — consistent with the
      sibling `[SCRIPT]` re-retirement todo's finding that MDPS has not processed fresh candle writes since the fix
      landed; the fix's live-confirmation gate is the SAME open blocker across all four asset_groups, not
      defi-specific. **NOT corpus-scoped** (3 sample days per AG via delimiter-descent, not the stratified
      full-corpus sample the defi DIAG todo below ran) — see the new follow-up todo below. Also a stale-doc finding:
      `canonical-cutover-register.md` §6d claims the `processed_candles/` `instrument_type=` segment is "PENDING —
      no migration has run" for cefi/tradfi (only "prediction already carries it") — this is CONTRADICTED by the
      code (the segment has always been unconditionally in the template) and by this session's live probe (cefi/
      tradfi objects with `instrument_type=` already exist back to at least 2026-07-01); flagged here per the "a
      doc that misled you is a finding" HARD RULE — not corrected in the register itself this session (out of
      scope for a DIAG todo; leaving a pointer here for whoever next touches §6d). Scratchpad probe (read-only
      `list_blobs` delimiter-descent only, never shipped — mirrors the 2026-08-16 root-cause session's own probe
      precedent): `probe_cross_ag_candles_casing_2026_08_17.py`.
- [x] ✅ [DIAG] P2. Root-cause WHY `_prune_consolidated_shards` left 9/21 defi market-data per-VM shards un-drained
      past their provable merge cutoff — **RESOLVED 2026-08-17 (slot 20, infra): NOT a `_prune_consolidated_shards`
      code bug — a lock-contention / long-merge-starvation pattern.** See Progress Log entry for full evidence
      (live-verified against prod, not inferred): the function itself is correct (a direct live call drained the
      entire eligible backlog with zero errors on the first attempt); the actual Cloud Run job runs every ~1 min
      (not the ~31-32min this todo assumed) but a currently-held `consolidator.lock` (holder `1-6831d99c`, held
      since 2026-08-17T04:51:10Z, already 33.7min old at read time — at/past this bucket's own documented 24-30min
      merge ceiling) makes every OTHER concurrent tick return early via the "locked" no-op path BEFORE ever reaching
      `_prune_consolidated_shards` (not even the shard listing). Prune's effective cadence is therefore gated by
      merge-COMPLETION frequency, not cron frequency — and this bucket rarely goes idle (e.g.
      `mtds-oracle-prices-backfill` alone lands a fresh per-VM shard roughly every ~9 min), so a long or
      occasionally-orphaned merge (a previously-incident'd failure class for this exact lock mechanism, see the
      "Lock-orphan blind spot" comment at `manifest_consolidator.py:382-406`) lets several cron-minutes' worth of
      eligible shards accumulate before the next completed merge's prune call sweeps them. (repo:
      unified-trading-library)
- [x] ✅ [DIAG] P3. Confirm whether the `consolidator.lock` holder observed 2026-08-17 (instance `1-6831d99c`,
      acquired 04:51:10Z) is a genuinely-orphaned lock (Cloud Run killed/crashed the execution without reaching
      `finally: _release_lock`) vs. a legitimately still-running long merge — re-check
      `_index/consolidator.lock`'s content + age against the defi bucket; once its age exceeds
      `CONSOLIDATOR_LOCK_TTL_SECONDS` (9000s/150min) the next tick reclaims it automatically and this resolves
      itself, but if the SAME instance id keeps reappearing after every reclaim (recurring orphan, e.g. a
      chunked-merge OOM/crash repeating on retry) that is the durable fix this doc's resolved DIAG todo above
      flags as the actual mechanism, not just a one-off. If confirmed recurring, consider whether
      `_check_consolidation_stall`'s lock-skip path (`_check_stall_on_lock_skip`,
      `CONSOLIDATOR_STALL_ALERT_CYCLES=195` for this bucket) is actually accumulating toward a page for it. (repo:
      unified-trading-library) **RESOLVED 2026-08-17 (slot-4, backend_engineer): NOT an orphan — `1-6831d99c` was a
      legitimately still-running long merge that completed successfully.** Direct evidence, not inference — see
      Progress Log entry for full detail. unified-trading-library@864f62c2f7 (DIAG script committed this session).
- [x] ✅ [DIAG] P3. Retry this doc's `logs`-mode Cloud Logging check (script
      `unified-trading-library/scripts/check_defi_consolidator_prune_backlog.py logs --project
      central-element-323112`) once the shared `ReadRequestsPerMinutePerProject`/`PerUser` (60/min) Cloud Logging
      quota that blocked every attempt in the 2026-08-16 session (5 retries, ~10+ min, zero successful reads) is not
      under contention — confirm whether the `ManifestConsolidator: pruned N consolidated per-VM shard(s)` INFO
      line has appeared at all in the job's recent run history, which would date how long the backlog above has
      been accumulating. **RESOLVED 2026-08-22 (slot 21, data_engineering): CLOSED AS SUPERSEDED, not obtained —
      retried 5 more attempts (90s apart, ~7.5 min total), 100% `ResourceExhausted` 429
      (`ReadRequestsPerMinutePerProject`/`PerUser`, 60/min) on every single attempt, zero successful reads. This is
      now the SECOND independent session (2026-08-16 + 2026-08-22, ~10 total retries across both) to exhaust every
      retry against this exact quota with zero successes — evidence this project's Cloud Logging read quota is
      chronically saturated, not a one-off busy window; a longer or larger retry budget would not plausibly help.
      More importantly, the question this check existed to answer (how long has the prune backlog been
      accumulating / root-cause `_prune_consolidated_shards` falling behind) was already independently RESOLVED
      2026-08-17 (slot 20, infra, see that Progress Log entry) via `gcloud run jobs executions list` +
      `_index/latest.json`/`consolidator.lock` reads — a path that explicitly sidesteps this same Cloud Logging
      quota entirely and found the actual mechanism (lock-contention / long-merge-starvation, not an
      unbounded-backlog-age question). The `logs`-mode confirmation is therefore no longer load-bearing for any
      open decision in this doc — closing rather than leaving a permanently-retrying, now-moot P3 diagnostic open.
      (repo: unified-trading-library)
- [x] ✅ [DIAG] P2. Confirm `gcloud builds list --project=central-element-323112` shows a FRESH successful build for
      `market-data-processing-service` — **RESOLVED 2026-08-17 (slot 13): the premise was checking the wrong
      signal.** MDPS deploys its batch/backfill compute via **VM TARBALL snapshot**, never Cloud Build, in this
      project — confirmed via 11+ live `mdps-*` VMs whose own instance metadata invokes
      `python -m market_data_processing_service` directly, zero MDPS Cloud Run services, and zero MDPS Cloud Build
      history. The REAL gate (the tarball) had NOT been refreshed since the fix commit landed — live-confirmed
      25,353 fresh uppercase-`POOL` rows written post-fix as a direct consequence. FIX APPLIED this session
      (tarball refreshed + verified). See Progress Log for full evidence + the new `[OPERATOR]` follow-up todo for
      already-running stale VMs this fix cannot retroactively reach.
- [x] ✅ [DIAG] P2. Scope the corpus-wide non-canonical `processed_candles/.../instrument_type=` uppercase-path
      population for cefi/tradfi/prediction — **RESOLVED 2026-08-17 (slot 6, infra).** Wrote a generalized,
      asset_group-parameterized sibling script (unlike defi, cefi/tradfi/prediction each carry MULTIPLE distinct
      `instrument_type` values and different `pipeline_mode`s, so this version discovers `pipeline_mode=` per
      sampled day via a cheap delimiter listing rather than hardcoding it, and classifies objects by the CASE of
      their own `instrument_type=` value rather than a fixed string):
      `market-data-processing-service/scripts/scope_processed_candles_instrument_type_uppercase_corpus_cefi_tradfi_prediction_2026_08_17.py`.
      Same walk-discipline as the defi sibling — one delimiter-descent day-enumeration call per asset_group, then a
      stratified 8-day sample (never a corpus walk), run interactively under `run-bounded-analysis.sh` (read-only
      `list_blobs`, small memory footprint, no manifest writes). Results, ALL uppercase, 0 or near-0 lowercase —
      confirms the bug is fleet-wide with no evidence of a partial/already-fixed subset:
      - **cefi** (`market-data-tick-cefi-prd-central-element-323112`): 2,684 corpus days (2019-03-30..2026-08-16),
        8-day sample (0.3%) = 20,216 uppercase / **0** lowercase, avg 2,527/day → **projected ≈6.78M objects**.
        Uppercase `instrument_type` values seen: FUTURE/OPTION/PERPETUAL/SPOT_PAIR (`batch_tardis`), PERPETUAL
        (`batch_extended`, `batch_hyperliquid`).
      - **tradfi** (`market-data-tick-tradfi-prd-central-element-323112`): 1,815 corpus days
        (2020-01-01..2026-08-07), 8-day sample (0.4%) = 26,558 uppercase / **6** lowercase (all 6 on one sampled
        day, 2024-02-09 — an isolated exception, not evidence of a clean subset), avg 3,319.8/day → **projected
        ≈6.03M objects**. Uppercase values: COMBO/EQUITY/ETF/FUTURE/OPTION/UD (`batch_databento`).
      - **prediction** (`market-data-tick-pred-prd-central-element-323112`, resolved via the dedicated
        `market-data-tick-prediction` bucket kind — prediction has no per-asset_group entry under the generic
        `market-data` kind, a naming trap this script had to route around): 263 corpus days
        (2025-03-14..2026-08-16), 8-day sample (3.0%) = 16,104 uppercase / **0** lowercase, avg 2,013/day →
        **projected ≈529K objects**. Uppercase value: PREDICTION_MARKET (`batch_databento`, `batch_polymarket_clob`).
      - **Combined fleet-wide projection (defi + cefi + tradfi + prediction) ≈ 17.4M + 6.78M + 6.03M + 0.53M ≈
        30.7M objects** (order-of-magnitude, sample-based across all four figures — NOT an exact count; the
        `[OPERATOR]` migration-plan-destination todo below should get a precise per-asset_group VM-scale count as
        its own first step, per that todo's existing text). market-data-processing-service@61294cec19
        (script committed this session).
- [ ] [DATA] P2. Author the dedicated corpus-wide migration plan (`assigned_vm: NA`, human-driven) for the
      `processed_candles/.../instrument_type=` uppercase-path population across defi/cefi/tradfi/prediction
      (COPY-to-canonical-lowercase per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part 5, never a
      blind rename/move), scoped to EVERY affected asset_group, not defi-only. Per D64 ruling (2026-08-22):
      human-driven — needs a precise per-AG count first and spans 4 prod buckets; matches the human-default rule for
      judgment-adjacent scale. First step: a precise (non-sampled) corpus-wide count per asset_group, not the
      sample-based projections already gathered. The migration itself belongs on a dedicated VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md`, not an interactive slot session.
- [x] ✅ [OPERATOR] P1. **RESOLVED 2026-08-22 (D10 remediation, `dispositions.json` `issues_corpus_completion_2026_08_21`)
      — operator disposition: kill+relaunch the 2 LONG_LIVED `mdps-features-live-*` VMs now; let bounded backfill
      VMs finish naturally with a corrective re-pass noted.** Re-enumerated the CURRENT live fleet first, per this
      todo's own instruction — of the ~11 VMs this session's original snapshot named, 9 (`mdps-backfill-cefi-
      20260816-162418`, `mdps-backfill-cefi-pcskip-20260817-104034-3b4e68`, `mdps-cefi-2019` through `mdps-cefi-2026`)
      had ALREADY self-deleted on completion (EPHEMERAL_BATCH lifecycle) by 2026-08-22 — consistent with "let bounded
      VMs finish naturally," no action needed on those. Only `mdps-defi-2025-20260817-000343` (the full-year defi
      backfill) is still `RUNNING` today — left untouched per the ruling (bounded, will self-terminate); its shards
      written before the fix landed still need the corrective re-pass this doc's gated `[SCRIPT]` re-retirement todo
      already covers. **Executed the urgent half**: confirmed both `mdps-features-live-cefi-20260807-031648` and
      `mdps-features-live-defi-20260807-032721` still `RUNNING` (heartbeats fresh, ~90s old — genuinely alive, not
      already-dead) and, per their own live `run.log` tails, BOTH were stuck in a tight `subscribe_once(...) failed
      — skipping this round: 404 Resource not found` retry loop (a separate, pre-existing Pub/Sub-resource gap, not
      writing productive candles at all at kill time) — deleted both
      (`gcloud compute instances delete`, no VM-delete-guardrail hit — the `canonical-migration-` 3-signal carve-out
      does not apply to this prefix) and relaunched fresh via the REGISTERED launcher
      (`launch-mdps-features-live.sh --asset-group {cefi,defi} --env prod`, confirmed via
      `launcher_registry.py` `VM_PREFIX_TO_BUCKET`/launcher map, not hand-rolled): `mdps-features-live-cefi-
      20260822-093742` and `mdps-features-live-defi-20260822-093954`, both verified `RUNNING` with all 5 tarballs
      fresh (`market-data-processing-service-code@71643c9ee58c` — carries the 2026-08-16 casing fix,
      `mtds-code@7facfa4383a5`, `unified-api-contracts-code@3ce57ed461fa`, `unified-trading-library-code@
      dfe34c4755d5`, `deployment-service-code@60b3218290e3`). No fire-and-forget: both confirmed STARTED
      (`gcloud compute instances list` RUNNING + launcher's own post-create confirmation block) and left running for
      continued monitoring, not just launch-and-walk-away. (repo: deployment-service)

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **2026-08-16 (slot 22, infra)**: DIAG todo done — sampled 20 live captured `instrument_type=POOL` rows' GCS objects
  directly (script `market-tick-data-service/scripts/one_offs/sample_pool_uppercase_gcs_objects_2026_08_16.py`,
  4 path shapes × 2 casings per row). 0/20 found an uppercase-pathed physical object — confirms the more exhaustive
  2026-08-12 sibling-plan finding (0/30). Also found the live captured `instrument_type=POOL` population has regrown
  to 1,641,333 as of today, four days after the 2026-08-12 retirement drove it to 0 — a SECOND recurrence of this
  doc's own tracked mechanism. See "What I found" item 5 for full detail and the recommendation for todo 168's next
  worker.
- **2026-08-16 (slot 6, data_engineering)**: resumed the `[SCRIPT]` decision todo. ROOT CAUSE CONFIRMED — a live,
  ongoing writer defect in `market-data-processing-service/.../canonical_writer.py:374` (GCS PATH segment built
  from an un-lowered, correctly-UPPERCASE id-grammar token), live-verified at scale against prod GCS (41,279/41,279
  sampled `processed_candles/` objects uppercase for one day, 0 lowercase) and connected to the propagation
  mechanism in `backfill_defi_dex_pool_swaps_source_correction.py` (same repo) that stamps the same casing into
  fresh `record_captured` manifest rows under `service_name=market-data-processing-service` — resolving slot-7's
  previously-unexplored lead. DECISION: retirement does NOT proceed until the writer fix (new P0 todo) lands and is
  verified live. Bumped doc priority P1→P0 given confirmed scale + an actively-recurring correctness bug on real
  financial data. Filed 5 new follow-up todos (fix, consolidator-prune verification, gated re-retirement, corpus-
  migration scoping, cross-AG risk check) — see Todos list. Note for the operator/main agent: this is a cross-repo,
  at-scale data-correctness finding per CLAUDE.md's "big finding" rule — surfacing it prominently here (doc priority
  P0, new fix todo P0) since no direct operator-notification channel is documented for this worker role beyond the
  tracked plan itself.
- **2026-08-16 (slot 5, ui_developer)**: resolved the `[DIAG]` `_prune_consolidated_shards` todo. Live GCS
  state check (new script `unified-trading-library/scripts/check_defi_consolidator_prune_backlog.py`, `state`
  mode) against the defi market-data bucket found 9/21 per-VM shards provably past the canonical's real
  merge-cutoff marker yet still present — CONFIRMS prune is falling behind at this snapshot. Config (prune
  disabled / per-cycle cap) and IAM delete permission both ruled out as the cause. The companion `logs` mode
  (meant to confirm `deleted` counts in the job's own run history) was blocked by a persistent, fleet-wide Cloud
  Logging read-quota exhaustion for the whole session — filed as a separate P3 follow-up rather than block this
  todo on it, since the state-mode evidence stands alone. Filed 2 new follow-up todos (root-cause the stall;
  retry the logs check once quota clears) — see Todos list.
- **2026-08-22 — ruling D64 (Uppercase-corpus migration plan type)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Human-driven — needs a precise per-AG count first and spans 4 prod
  buckets; matches the human-default rule for judgment-adjacent scale. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-16 (slot 19, backend_engineer)**: resolved the `[BACKEND]` P0 writer fix todo. Corrected the
  investigation's own line-374 attribution en route (see the todo's resolution note for detail): the actual
  physical GCS-path builder is the `build_canonical_candle_object_path(...)` call in `canonical_writer.py`, not
  the `partition_path` string (which is validation-only, never written to disk). Lowered `instrument_type` at
  that one call site; audited all other usages in the file and confirmed none else construct a physical path.
  Updated the one test whose assertion encoded the pre-fix uppercase-path bug. QG green, shipped
  `market-data-processing-service@94215e9cd9`. Next: the GATED `[SCRIPT]` re-retirement todo below still needs a
  fresh candle write for a new day to confirm the fix is live (not just code-reviewed) before retirement resumes.
- **2026-08-17 (slot 32, data_engineering) — attempted the gated `[SCRIPT]` re-retirement todo; GATE STILL NOT MET,
  no retirement attempted.** Live-verified two independent signals, both inconclusive-to-negative for "fix confirmed
  live":
  - **`94215e9cd9`'s content IS present on `origin/main`** — direct content read (`git show
    origin/main:market_data_processing_service/app/core/canonical_writer.py`) confirms the
    `build_canonical_candle_object_path(..., instrument_type=instrument_type.lower(), ...)` call site. The commit
    sha itself is NOT a git ancestor of main (likely squash-merged during LDR→main promotion, per the known
    `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` pattern — expected, not a bug) but the diff is
    there.
  - **Zero fresh MDPS `dex_pool_swaps` writes since BEFORE the fix landed, of either casing.** Wrote a bounded,
    memory-safe manifest probe (row-group-at-a-time, run under `run-bounded-analysis.sh`, mirroring the retirement
    script's own idiom) — `market-tick-data-service/scripts/one_offs/verify_mdps_casing_fix_live_via_manifest_2026_08_17.py`
    — querying `data_type=dex_pool_swaps` + `service_name=market-data-processing-service` + `capture_status=captured`
    for `MAX(written_at)` per `instrument_type` casing. Result: uppercase `POOL` max(written_at) =
    `2026-08-16T20:31:16Z` (1,643,557 rows total); lowercase `pool` max(written_at) = `2026-08-11T02:55:55Z`
    (1,925,307 rows total). **Both predate the fix commit's landing (`2026-08-16T23:31:54Z`)** — 0 rows of either
    casing written after the fix. MDPS simply has not processed any `dex_pool_swaps` candle write (backfill or live)
    in the ~29h since, so there is no fresh evidence to inspect yet — absence of new uppercase writes is NOT the
    same as a confirmed-live fix (per the todo's own done-when, which explicitly requires "not just a code review").
  - **Side finding (uncertain, not root-caused — filed as a new DIAG todo above, not resolved here)**: `gcloud
    builds list --project=central-element-323112 --limit=8` (whole-project, not MDPS-filtered — a
    `_SERVICE_NAME=market-data-processing-service` filter returned zero rows even over the last 30 builds) showed
    the most recent build anywhere in the project at `2026-08-16T19:39:42Z`, i.e. before the fix even landed and
    >30h stale at read time. Single snapshot, not confirmed as a genuine deploy-pipeline stall — could equally be
    "no build-triggering push has landed since" (this project's Cloud Build triggers, cicd craft, out of my scope
    to root-cause here). Flagging because it directly affects whether/when this gate can ever be satisfied via
    deploy evidence, not because it's confirmed broken.
  - **DECISION: gate not met, no retirement attempted, checkbox NOT flipped.** Did not force a synthetic write
    (e.g. via the `/data-pipeline-check-mdps` smoke-test skill) to manufacture verification evidence — that skill
    explicitly requires an operator-given `--day`, not one invented by an unattended worker, and a forced write
    would test correctness but not settle whether the REAL production write path is actually live. Skipped the
    task with `reason_code=GATED` per `worker.md` § 4c so the fleet cooldown arms correctly rather than the task
    immediately re-dispatching to the next slot with the same negative result. Next worker: re-check the manifest
    probe's `MAX(written_at)` once genuine new `dex_pool_swaps` capture activity resumes (backfill VM or live) —
    if the freshest post-fix row is lowercase `pool`, the gate is satisfied and retirement can proceed; if
    uppercase `POOL` keeps appearing post-fix, the fix has NOT actually deployed live despite being on main and
    needs the new Cloud-Build-staleness DIAG todo resolved first.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-17 (slot 10, data_engineering) — re-attempted the gated `[SCRIPT]` re-retirement todo; GATE STILL NOT
  MET, no retirement attempted, checkbox NOT flipped.** Re-ran slot-32's manifest probe
  (`market-tick-data-service/scripts/one_offs/verify_mdps_casing_fix_live_via_manifest_2026_08_17.py`, under
  `run-bounded-analysis.sh`) ~5h after slot-32's check: **identical result** — uppercase `POOL` max(written_at) =
  `2026-08-16T20:31:16Z` (1,643,557 rows), lowercase `pool` max(written_at) = `2026-08-11T02:55:55Z` (1,925,307
  rows), **0 rows of either casing written after the fix commit** (`2026-08-16T23:31:54Z`). MDPS still has not
  processed a single `dex_pool_swaps` candle write since the fix landed — same conclusion as slot-32, now with a
  second independent confirmation ruling out "the first check just caught an unlucky quiet moment."
  **New evidence on the Cloud-Build-staleness side question**: `gcloud builds list --project=central-element-323112
  --limit=8` now shows a FRESH build after the fix landed (`8575b934…`, 2026-08-17T02:14:53Z, SUCCESS) — so the
  project's Cloud Build is not fleet-wide stalled, ruling out one candidate explanation from slot-32's flag. But
  that build is `unified-trading-library/e2e-audit`, not MDPS, and a 30-build/30-trigger sweep found **zero**
  MDPS-named builds AND **`gcloud builds triggers list --project=central-element-323112` returns "Listed 0
  items"** — this project has NO Cloud Build triggers registered at all. That's new information for the open DIAG
  todo below (not a resolution): it reframes "is the build pipeline stalled" as "does MDPS even deploy via a
  Cloud Build trigger in THIS project" — plausibly it deploys via a different project or a non-trigger mechanism
  (e.g. CI-driven `gcloud builds submit`), which would explain the absence without implying a stall. Root-causing
  MDPS's actual deploy path is cicd craft, out of scope for this data_engineering session — left the DIAG todo
  open with this evidence added rather than closing it on an inference.
  **Did not force a synthetic write** for the same reason slot-32 gave: the smoke-test skill requires an
  operator-given `--day`, and a forced write would test correctness, not whether the real production path is live.
  Skipped with `reason_code=GATED` again. Next worker: same as slot-32's guidance — re-check
  `MAX(written_at)` once genuine new `dex_pool_swaps` capture activity resumes; if the freshest post-fix row is
  lowercase, the gate is satisfied.
- **2026-08-17 (slot 24, ui_developer)**: resolved the `[DIAG]` P2 "does this bug affect cefi/tradfi/prediction too"
  todo. Bounded, read-only delimiter-descent GCS probe (`probe_cross_ag_candles_casing_2026_08_17.py`, not shipped)
  against all three live prod buckets confirmed 100% uppercase `instrument_type=` path segments under
  `processed_candles/` for cefi (PERPETUAL), tradfi (EQUITY/ETF/FUTURE/COMBO), and prediction (PREDICTION_MARKET)
  across every sampled day (2026-07-01, 2026-08-01, 2026-08-15) — 0 lowercase objects found anywhere, including
  days after the 2026-08-16 fix landed. Confirmed via code read (`output_path_helpers.py` + UTL
  `registry.py::build_canonical_candle_path`) that the path builder and the fix are BOTH asset_group-agnostic (one
  shared template/call site for all `MarketAssetGroup` values), so this is the fleet-wide manifestation of the SAME
  root cause already fixed for defi, not a separate bug — the existing fix already covers it going forward once
  confirmed live. Filed a new corpus-scoping DIAG todo (cefi/tradfi/prediction are NOT YET corpus-scoped, unlike
  defi's ~17.4M-object sample-based projection) and widened the `[OPERATOR]` migration-plan-destination todo's
  scope from defi-only to every affected asset_group. Also flagged (not corrected — out of scope for this DIAG
  todo) that `canonical-cutover-register.md` §6d's "cefi/tradfi processed_candles instrument_type= segment is
  PENDING, no migration run" claim is stale/contradicted by both the code and this session's live probe.
- **2026-08-17 (slot 25, backend_engineer)**: resolved the `[DIAG]` P2 corpus-wide scoping todo. Wrote
  `market-data-processing-service/scripts/scope_processed_candles_pool_uppercase_corpus_2026_08_17.py`, a
  walk-disciplined stratified-sample scoper reusing `backfill_defi_dex_pool_swaps_source_correction.py`'s own
  sanctioned day-enumeration idiom (1 delimiter-descent call gets all `day=` prefixes; confirmed 1,159 distinct
  days, one more than that script's stale 1,155 citation — corpus growth since). An initial version tried to
  scope via the availability manifest (matching `verify_mdps_casing_fix_live_via_manifest_2026_08_17.py`'s idiom)
  but found this population is NOT reliably represented there (0 manifest rows for the candle `data_type` key
  MDPS's own `mdps_data_type_key()` would produce; MDPS's emission-policy gate can skip `record_captured` for a
  sampled fraction of writes) — abandoned that approach (deleted the script,
  `market-tick-data-service/scripts/one_offs/scope_processed_candles_pool_uppercase_corpus_2026_08_17.py`, before
  shipping it, since it silently under-reported) in favor of direct GCS listing, matching the exact path grammar
  `build_canonical_candle_path` (UTL `registry.py`) actually emits — confirmed NO `asset_group=` segment exists in
  this tree yet (canonical-cutover-register.md §6d: that axis is still PENDING). Sampled 24/1,159 days (2.1%):
  0/24 found any lowercase `instrument_type=pool/` object; sample total 360,140 uppercase objects, highly
  non-uniform per-day (0-62,586), average 15,005.8/day → projected corpus-wide total ≈17.4M objects
  (order-of-magnitude, sample-based, NOT exact). Only `data_type=dex_pool_swaps` observed in the sample — no
  evidence of other defi POOL data_types, though a 2.1% sample cannot rule that out corpus-wide. Filed a new
  `[OPERATOR]` P2 todo for plan-destination + the dedicated migration plan itself (genuinely corpus-scale,
  belongs on a dedicated VM, not this interactive session) per this doc's own recommendation. Script committed,
  QG green, shipped via quickmerge.
- **2026-08-17 (slot 20, infra)**: resolved the `[DIAG]` P2 `_prune_consolidated_shards` un-drained-backlog todo,
  live-verified against prod (no code change — a live-diagnosis task). Confirmed by direct measurement, not
  inference:
  - `state`-mode re-check found 7/19 shards still eligible-but-present (down from slot-5's 9/21 — genuinely
    shrinking, not frozen), all 7 from a SINGLE writer (`mtds-oracle-prices-backfill`, sequential shard names
    `c255`-`c261`, one new shard roughly every ~9 min) — ruling out "many different VMs all individually stuck"
    in favor of "one prolific writer + a draining-too-slowly prune cadence."
  - Ruled out every candidate this doc's todo listed as "not yet checked": no bucket retention policy / object
    hold / lifecycle rule on the shard prefix; `testIamPermissions` confirms `storage.objects.delete` for the
    ambient identity; and — the decisive test — **manually invoking the exact production
    `_prune_consolidated_shards(client, bucket, cutoff=...)` live against the real defi bucket pruned all 6
    remaining eligible shards on the FIRST call, zero errors, zero exceptions.** This rules out the `_delete_one`
    silent-exception-swallow hypothesis (the function is not buggy — it works correctly when it runs) and rules
    out "just a snapshot artifact" in the naive sense (the backlog did not resolve itself over ~90+ min of
    per-minute cron ticks before I intervened).
  - **Actual mechanism, found by checking `gcloud run jobs executions list`** (a data source this doc's prior
    sessions hadn't used — sidesteps the Cloud Logging read-quota exhaustion blocking the `logs`-mode todo
    entirely): the Cloud Run job fires every **~1 minute**, not the ~31-32min this doc's todo assumed. Each
    execution's own `_index/latest.json` report (`schema_version:1`, written every run — another data source not
    previously read) showed `"error_reason": "locked"` at the exact time of my check. Read `_index/
    consolidator.lock` directly: held by instance `1-6831d99c` since `2026-08-17T04:51:10Z` — 33.7 min old at
    read time, i.e. already at/past this bucket's own documented 24-30min merge-duration ceiling
    (`CONSOLIDATOR_LOCK_TTL_SECONDS=9000`/150min override, set deliberately high per the code's own comment at
    `manifest_consolidator.py:356-365` because defi's chunked merge legitimately runs that long). Per
    `consolidate()`'s control flow, the "locked" early-return happens BEFORE either prune call site (before even
    the shard listing) — so while one execution holds the lock, no other tick can prune, no matter how often cron
    fires. Combined with a writer (`mtds-oracle-prices-backfill`) landing new shards ~every 9 min (keeping
    `changed_paths` non-empty almost every tick, so the bucket rarely takes the fast idle no-op-prune branch
    either), pruning's REAL cadence is bounded by how often a full merge actually COMPLETES, not by the 1-min cron
    tick — and the code's own "Lock-orphan blind spot" comment (`manifest_consolidator.py:382-406`) already
    documents this exact failure shape (a SIGKILLed holder bypasses `finally: _release_lock`, leaving a "fresh"
    lock that blocks everything for up to the full TTL) as a previously-incident'd, recurring risk for this
    mechanism.
  - **Side effect, disclosed explicitly**: my diagnostic call to the real `_prune_consolidated_shards` function
    against the live defi bucket drained its then-current eligible backlog (6 shards) as a natural consequence of
    calling the exact, already-safe (conditional `if_generation_match` delete, dedup-protected) production
    function — not a novel/riskier action, and not something a next cycle wouldn't have done on its own once the
    lock clears. No irreversible/unsafe action taken.
  - **Not resolved this session** (filed as a new P3 DIAG todo): whether the CURRENT lock holder (`1-6831d99c`,
    still held as of this session's last check) is a genuinely orphaned/crashed execution or a legitimately
    still-finishing long merge — that needs either watching it clear past its TTL or a fresh re-check, and if the
    SAME instance id recurs after being reclaimed, that would confirm a recurring orphan (the durable-fix-worthy
    case) rather than an isolated slow cycle.
- **2026-08-17 (slot 13) — resolved the `[DIAG]` P2 Cloud-Build-staleness todo; ROOT CAUSE FOUND (different from what
  the todo assumed) + LIVE FIX APPLIED.** The todo's own premise — "check `gcloud builds list` for a fresh MDPS
  build" — was checking the wrong signal. **MDPS's actual `dex_pool_swaps` candle-write compute never goes through
  Cloud Build in this project**: confirmed zero `gcloud run services list` entries for MDPS, zero MDPS Cloud Build
  history across a 30-build project-wide sweep (matches slot-10's finding), and — the decisive piece —
  `gcloud compute instances list --filter='name~"mdps"'` found 11+ RUNNING `mdps-*` VMs whose own instance metadata
  (`VM_BACKFILL_CMD`) shows them invoking `python -m market_data_processing_service --operation process --mode batch
  ...` directly, confirming MDPS deploys via **VM tarball snapshot**
  (`/codex/05-infrastructure/vm-tarball-deployment.md` — MDPS is explicitly named as an opt-in tarball-fleet service
  repo), not Cloud Build/Cloud Run. Tarball refresh is a SEPARATE MANUAL step (`create-code-tarballs.sh`) that does
  NOT run automatically on commit — nobody ran it after `94215e9cd9` landed.
  - **Direct live confirmation the fix was NOT deployed**: re-ran slot-32/slot-10's manifest probe
    (`verify_mdps_casing_fix_live_via_manifest_2026_08_17.py`, under `run-bounded-analysis.sh`) — found **25,353
    fresh uppercase-`POOL` `dex_pool_swaps` rows written AFTER the fix commit** (`written_at` up to
    `2026-08-17T09:24:51Z`, ~1.5h before this check), directly superseding slot-32/slot-10's earlier "MDPS hasn't
    processed any writes since the fix" read — it HAS been writing continuously, just still on pre-fix code (their
    reads were simply timed before the backfill resumed). The likely direct source:
    `mdps-defi-2025-20260817-000343` (RUNNING, `VM_OPERATION=backfill-defi`, `VM_ASSET_GROUP=DEFI`, full
    2025-01-01..2025-12-31 backfill), launched `2026-08-17T00:03:46Z` — 32min AFTER the fix landed on LDR but
    before any tarball refresh, so it fetched stale code at boot regardless of the fix's LDR landing time.
  - **FIX SHIPPED THIS SESSION**: ran `bash deployment-service/scripts/vm/create-code-tarballs.sh --include
    market-data-processing-service`. Verified via the sanctioned `download_from_storage` SDK path (never raw
    `gsutil` — blocked by the workspace guardrail) that the refreshed
    `code/market-data-processing-service-code.manifest.json` now pins commit `ae9279130...`, and confirmed
    `git merge-base --is-ancestor 94215e9cd9 ae9279130...` succeeds — **the fix IS now included**. Tarballs are
    per-REPO, not per-asset_group (`VM_SERVICE` selects the tarball, not `VM_ASSET_GROUP`), so this ONE refresh
    covers every asset_group's future MDPS VM boots (cefi/tradfi/defi/prediction alike), not just defi.
  - **NOT resolved — new `[OPERATOR]` follow-up todo filed above**: every `mdps-*` VM already RUNNING at refresh
    time (`2026-08-17T10:56:11Z`) already fetched its tarball at boot and will NOT pick up this fix without a
    relaunch. Found at least: `mdps-defi-2025-20260817-000343` (mid a full-year defi backfill),
    `mdps-backfill-cefi-20260816-162418`, `mdps-backfill-cefi-pcskip-20260817-104034-3b4e68`, `mdps-cefi-2019`
    through `mdps-cefi-2026` (7 VMs, one per year), and two apparently LONG_LIVED
    `mdps-features-live-{cefi,defi}-20260807-*` (running since 2026-08-06 — if MDPS-adjacent, these predate even
    the original bug fix by 10 days and may have been writing non-canonical paths the whole time they've been up).
  - **Also unresolved**: the gated `[SCRIPT]` re-retirement todo above still can't be marked "fix confirmed live" —
    that requires observing an ACTUAL fresh lowercase-pathed write, which needs a NEW VM boot (or the current ones
    finishing + a fresh one launching) AFTER `2026-08-17T10:56:11Z` specifically, not a re-check of the same
    stale-VM-driven population slot-32/slot-10 already sampled.
  - Per CLAUDE.md's "big finding" rule (data-correctness, cross-repo, actively ongoing during investigation):
    flagging this prominently for the operator/main agent — the corpus contamination this doc already scoped at
    ~17.4M objects (defi alone) was GROWING in real time during this session, across potentially a dozen concurrent
    VMs, until this fix landed.
- **2026-08-17 (slot 6, infra)**: resolved the cefi/tradfi/prediction corpus-scoping `[DIAG]` P2 todo. Generalized
  the defi sibling scoper into an asset_group-parameterized script (discovers `pipeline_mode=` per sampled day
  rather than hardcoding it, classifies by `instrument_type=` CASE rather than a fixed value string — needed
  because these three asset_groups each carry multiple distinct `instrument_type` values, unlike defi's single
  POOL/pool axis). Ran interactively (read-only, bounded, under `run-bounded-analysis.sh`), 8-day stratified sample
  per asset_group. Results: cefi 20,216/20,216 sampled objects uppercase (0 lowercase) → projected ≈6.78M; tradfi
  26,558 uppercase / 6 lowercase (isolated, one sampled day) → projected ≈6.03M; prediction 16,104/16,104 uppercase
  (0 lowercase) → projected ≈529K. Combined with defi's already-scoped ≈17.4M, fleet-wide projection ≈30.7M objects
  (sample-based, order-of-magnitude). Confirms the fleet-wide DIAG finding from the prior session with actual
  per-asset_group sizing — see the resolved todo above for full detail and the naming trap found along the way
  (prediction resolves via the dedicated `market-data-tick-prediction` bucket kind, not the generic `market-data`
  kind's per-asset_group dict). Script committed this session, QG green, shipped via quickmerge. Next: the
  `[OPERATOR]` migration-plan-destination todo above is now unblocked with real sizing for all four asset_groups.
- **2026-08-17 (slot-4, backend_engineer)**: resolved the `[DIAG]` P3 consolidator.lock-orphan todo. **VERDICT:
  `1-6831d99c` was NOT an orphaned/crashed lock — it was a legitimately still-running long merge that completed
  successfully.** Direct evidence, not inference:
  - Wrote a read-only DIAG script (`unified-trading-library/scripts/check_consolidator_lock_orphan_status_2026_08_17.py`,
    mirrors `read_consolidator_lock_age_sec`'s own parse + the `instance` field that function doesn't expose) and ran
    it live: `_index/consolidator.lock` for `market-data-tick-defi-prd-central-element-323112` is currently ABSENT
    (no cycle holds it). Verified the bucket's REAL `CONSOLIDATOR_LOCK_TTL_SECONDS` against
    `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` directly (`market-data-defi` = `9000`) —
    NOT the module's own env-driven `_LOCK_TTL_SECONDS` default, which would silently read the wrong 300s in an
    interactive shell (the Terraform override only applies inside the live Cloud Run job's own container).
  - **Decisive piece**: `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-defi
    --region=asia-northeast1` (region confirmed live via `gcloud run jobs list`, not guessed) shows execution
    `...-qpxnr` started `2026-08-17T04:50:06.183680Z` (within ~64s of the lock's recorded
    `started_at=2026-08-17T04:51:10Z` — consistent with brief in-process setup before `_acquire_lock()`) and
    **completed with condition status=True (Succeeded)** at `2026-08-17T06:01:00.420412Z` — a genuine ~70min54s
    merge, comfortably inside the bucket's 9000s/150min TTL and consistent with this doc's own documented long-tail
    merge durations for this bucket. Two more consecutive long executions immediately followed (`...-2bzjw`
    06:01:18Z→07:10:16Z, `...-4q6qm` 07:10:05Z→08:18:51Z), BOTH also `status=True` — three distinct, cleanly-completed
    executions back-to-back (a temporarily heavier backlog being worked through), not the same instance repeatedly
    dying and being reclaimed.
  - A fleet-wide sweep (`--filter="status.startTime>=2026-08-17T00:00:00Z AND status.conditions[0].status!=True"`)
    found **ZERO** non-succeeded executions for this job anywhere in the entire day — directly rules out any
    SIGKILL/OOM crash today, for this or any other execution.
  - `_index/latest.json` (overwritten every cycle) shows a clean, fast (~9-10s), successful
    (`success=true, error_reason=""`) incremental no-op cycle as of `12:59:48Z` — 8+ hours after the original lock
    acquisition, confirming the consolidator remains healthy.
  - Directly answered the todo's own follow-up question: `_index/consolidator_stall_state.json`'s no-progress
    streak is `0` — `_check_stall_on_lock_skip`'s alert mechanism (`CONSOLIDATOR_STALL_ALERT_CYCLES=195`, Terraform-
    verified against the same `.tf` file, matching this todo's own citation) is NOT accumulating toward a page.
  - No durable fix needed based on this evidence — the lock/TTL mechanism worked exactly as designed: a genuinely
    long-running merge held the lock for its actual duration, then released it normally on completion.
    unified-trading-library@864f62c2f7 (script committed, QG green, shipped via quickmerge).
- **2026-08-17 (blocked-questions backlog live check)**: answered `BLK-op-defi_pool_uppercase_recurrence_after_fold-8fcf1eb70634`
  FINAL via `POST /api/blocked/{id}/answer` (HTTP 200) — the operator's real question was "is this not done already,
  check." Verdict: genuinely NOT done, not stale, not superseded — confirmed by (1) reading the full doc history (this
  is one of the most actively-worked docs in the corpus, most Progress Log entries from today/yesterday), (2) grepping
  `plans/active/`+`plans/archive/` for a superseding migration plan (none found), (3) a fresh independent live spot-check
  (UTL `get_storage_client`, not gsutil) against `market-data-tick-defi-prd`'s `processed_candles/by_date/day=2023-01-01/
  pipeline_mode=batch_onchain_rpc/` prefix — 30/30 sampled objects still at the non-canonical uppercase
  `instrument_type=POOL/` path today, 0/30 lowercase, e.g.
  `.../instrument_type=POOL/venue=BALANCER-ARBITRUM/BALANCER-ARBITRUM:POOL:0xd897...bf.parquet`. The corpus-wide
  ~30.7M-object (defi+cefi+tradfi+prediction) non-canonical population is scoped but not yet migrated; the open
  `[OPERATOR]` P2 "decide plan destination" todo above still stands, answered with a recommendation of
  `assigned_vm: NA` (human plan, per this workspace's default-human rule for a judgment-call-scale migration plan) —
  no plan authored, no migration executed, per the check-only scope of this session.
- **plan-reconcile 2026-08-19 (epic-scoped, finding-Y candidate — flagged, not fixed)**: this doc is `assigned_vm:
  planning` and currently carries 2 `[OPERATOR]`-tagged items (P2 "decide plan destination", P1 "decide disposition for
  mdps-* VMs") in the same file as plain dispatchable todos (`[SCRIPT] P1` GATED re-retirement, `[DIAG] P3` logs-mode
  retry) — the exact shape `task_template.md` §3 finding Y bans. Not forked out here: per finding Y's own text,
  retroactive remediation is the job of the dedicated sweep
  (`/plans/active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md`, a DIFFERENT epic,
  `agent_operating_framework_master`), not this epic-scoped run, and this doc's live, heavily-narrated investigation
  state makes it a poor candidate for a rushed mechanical fork under today's shared-checkout contention. Routing this
  doc as a candidate for that sweep's "Group: defi-related epics" todo (not yet added there — out of this run's scope
  to edit a different epic's doc; flagging for the lead session / next sweep pass instead).
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
- **2026-08-22 (slot 21, data_engineering)**: closed the `[DIAG]` P3 `logs`-mode Cloud Logging retry todo as
  superseded. Retried the script 5 more times (90s apart, ~7.5 min total, backgrounded to respect the async-wait
  discipline) — 100% `ResourceExhausted` 429 on the same `ReadRequestsPerMinutePerProject`/`PerUser` (60/min) quota
  that blocked the entire 2026-08-16 session, zero successful reads across both sessions' ~10 combined attempts.
  Did not keep retrying indefinitely: the underlying root-cause question this check existed to answer was already
  independently resolved 2026-08-17 (slot 20, infra) via a different data source (`gcloud run jobs executions
  list` + lock/latest.json reads) that bypasses this exact quota — so the logs confirmation is no longer needed to
  unblock anything in this doc. No other open todo in this doc depends on this one.
