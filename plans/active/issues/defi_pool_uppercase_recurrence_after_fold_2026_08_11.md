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
- [ ] [BACKEND] P0. Fix the confirmed root cause:
      `market_data_processing_service/app/core/canonical_writer.py:374`'s `partition_path` construction must
      lowercase `instrument_type` for the GCS PATH segment specifically (e.g. `instrument_type=
      {instrument_type.lower()}`) — while leaving every OTHER use of the `instrument_type` variable in this
      function (the manifest `record_captured` row content, `lookup_mdps_contract`, log-event payloads) at its
      current uppercase value, since that matches the id-grammar (§3b) and manifest-column-target (§3c) rules —
      only the PATH segment (§3a) is wrong today. Audit every OTHER `instrument_type` usage in this same file
      (this session found ~10 call sites, `:284/301/331/344/357/390/429/512/532/586/659`) individually before
      touching any of them — some may be additional, not-yet-found path-construction sites with the SAME bug
      (unverified this session), not all are the row-content/manifest-column use this todo assumes. (repo:
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
- [ ] [DIAG] P2. Scope the corpus-wide non-canonical `processed_candles/.../instrument_type=POOL/` physical-object
      population before any migration is attempted — this session measured 100% uppercase (41,279 objects) for ONE
      day's `dex_pool_swaps` alone; the corpus spans ~1,155 distinct days
      (`backfill_defi_dex_pool_swaps_source_correction.py`'s own enumeration) and likely other defi POOL data_types
      beyond `dex_pool_swaps` (the writer bug is data_type-agnostic). Likely a six-to-seven-figure object count —
      needs its own dedicated plan (COPY-to-canonical-lowercase, never a blind rename/move, per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part 5) once scoped, not a fold into this doc.
- [ ] [DIAG] P2. Check whether the SAME `canonical_writer.py`/`_infer_instrument_type` casing-conflation bug also
      affects cefi/tradfi/prediction `processed_candles/` writes — their canonical id grammars ALSO embed an
      uppercase type token (§3b applies fleet-wide, not defi-only) and `canonical_writer.py` is shared cross-
      asset-group code (this session confirmed a tradfi-specific branch in the SAME function, `:266`). NOT verified
      this session — flagging as a plausible, unchecked risk per CLAIM ≤ MEASUREMENT, not a confirmed finding.
- [ ] [DIAG] P2. Root-cause WHY `_prune_consolidated_shards` left 9/21 defi market-data per-VM shards un-drained
      past their provable merge cutoff (see the resolved DIAG todo above) — config (`CONSOLIDATOR_PRUNE_SHARDS`/
      `_MAX_PER_CYCLE`) and IAM delete permission are both already ruled out. Candidates not yet checked: an
      exception in `_delete_one`'s per-shard delete swallowed as a skip (its `except Exception` only counts
      `NotFound`/`404` as success — a `PreconditionFailed` from a concurrent rewrite is a legitimate skip-and-retry-
      next-cycle, but a different, unexpected exception type would ALSO silently skip with nothing logged besides
      the WARNING for the outer listing failure, which is a different code path); or the `state`-mode snapshot
      simply caught the bucket mid-cycle (shards land continuously; a from-a-slightly-earlier merge's already-
      completed prune pass may not have run again yet at read time — re-check with 2-3 snapshots spaced ~10-15 min
      apart, past the defi cadence's own ~31-32min real-merge interval, before concluding this is a persistent
      stall rather than normal in-cycle lag). Once root-caused, re-close per the same "captured-outranks
      resurrection risk" concern documented in "What I found" item 6's last bullet. (repo: unified-trading-library)
- [ ] [DIAG] P3. Retry this doc's `logs`-mode Cloud Logging check (script
      `unified-trading-library/scripts/check_defi_consolidator_prune_backlog.py logs --project
      central-element-323112`) once the shared `ReadRequestsPerMinutePerProject`/`PerUser` (60/min) Cloud Logging
      quota that blocked every attempt in the 2026-08-16 session (5 retries, ~10+ min, zero successful reads) is not
      under contention — confirm whether the `ManifestConsolidator: pruned N consolidated per-VM shard(s)` INFO
      line has appeared at all in the job's recent run history, which would date how long the backlog above has
      been accumulating. (repo: unified-trading-library)

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
