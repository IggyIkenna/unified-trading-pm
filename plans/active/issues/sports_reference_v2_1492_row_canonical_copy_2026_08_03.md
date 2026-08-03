---
doc_type: issue
title: Copy 1,492 pre-floor-only sports_reference_v2/by_date/ rows to canonical storage before the by_date cull
summary: >-
  Operator ruling (plan_reconcile_parked_operator_decisions_2026_08_02.md § 1b, option B, confirmed 2026-08-03 over a
  conflicting concurrent-session ruling of option A): before the two sports_reference_v2/by_date/ delete todos can
  revert to self-justified, the 1,492 rows sports_satellite_ao_dispatch_batch5_2026_07_26.md proved are the SOLE
  surviving copy of real pre-floor data (no canonical twin) must be copied to canonical storage.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, delete-safety, canonical-copy, data-migration]
related:
  [
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: []
resolved_by:
  "Operator ruling 2026-08-03 ('agreed'): wipe instead of copy, per
  sports_v2_1492_row_copy_contradicts_floor_wipe_2026_08_03.md's recommendation. Executed via
  deployment-service/scripts/wipe_pre_floor_sports_2026_07_21.py against
  instruments-store-sports-prd-central-element-323112/sports_reference_v2/by_date/ -- 1,528/1,528 objects deleted, 0
  errors, post-delete verification shows 0 pre-floor day dirs remain."
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md § 1b, option B, 2026-08-03."
context_scope:
  [
    /plans/active/issues/sports_v2_1492_row_copy_contradicts_floor_wipe_2026_08_03.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
---

# Copy the 1,492 sole-surviving-copy sports_reference_v2/by_date/ rows to canonical storage

## Why this doc exists

`sports_satellite_ao_dispatch_batch5_2026_07_26.md:184-217` proved 1,492 rows under `sports_reference_v2/by_date/` are
the SOLE surviving copy of real pre-floor data with no canonical twin. The two open `sports_reference_v2/by_date/` cull
todos in `sports_consolidated_closeout_2026_07_19.md:552-553` and
`sports_consolidated_native_ao_extract_2026_07_25.md:204-210` are currently `[OPERATOR]`-gated + delete-safety §3a-cited
pending exactly this migration.

## Todos

- [x] ✅ [DATA] P1. Identify the exact 1,492 rows (re-run the census from
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md` to confirm the count is still current — the corpus has moved
      since 2026-07-26). **DONE 2026-08-03 — count is NOT current: corrected to 764 distinct rows** (down from the cited
      1,492; see Progress Log for full methodology + evidence). Durable artifact:
      `gs://instruments-store-sports-prd-central-element-323112/_index/audit/sports_reference_v2_prefloor_census_2026_08_03.parquet`
      (764 rows, one per (day, entity) cell) — this is the exact row list todo 2 should consume.
- [x] ✅ [OPERATOR] P1. **SUPERSEDED 2026-08-03 — operator agreed with the wipe recommendation over the copy.** Todo 2
      as originally worded ("copy to canonical") is retired; see the new todo 2 below for what actually shipped.
- [x] ✅ [DATA] P1. **Wipe the 764 confirmed pre-floor cells instead of copying** (per operator ruling on
      `sports_v2_1492_row_copy_contradicts_floor_wipe_2026_08_03.md`, "agreed"). Executed
      `deployment-service/scripts/wipe_pre_floor_sports_2026_07_21.py --bucket     instruments-store-sports-prd-central-element-323112 --root-prefix sports_reference_v2/by_date --apply`
      — census-first (mandatory, this bucket has soft-delete=0): 382 pre-floor day dirs, 1,528 objects (764 cells × 2
      physical copies each, bare + `pipeline_mode=`-tagged — matches the census exactly). Applied:
      `{'DELETED': 1528, 'ERROR': 0}`. Post-delete verification re-run: 0 pre-floor day dirs remain, 16 post-floor day
      dirs (2024-12-24..2026-04-20) untouched. Snapshots (pre-apply + apply + verify) preserved in this session's
      scratchpad as the recovery record (soft-delete=0 means the snapshot is the only one).
- [x] ✅ [VERIFY] P1. **Post-delete listing confirms 0 pre-floor objects remain** — see above, folded into the same
      verification pass (a separate "canonical-twin check" no longer applies since nothing was copied).
- [x] ✅ [OPERATOR] P2. **Retag the two `sports_reference_v2/by_date/` cull todos** — done in
      `sports_consolidated_closeout_2026_07_19.md` and `sports_consolidated_native_ao_extract_2026_07_25.md`: the
      764-row sole-surviving-copy carve-out that blocked them is resolved (wiped, not orphaned), so both revert toward
      self-justified. Full cull of the REMAINING 16 post-floor day dirs still needs its own reader-check first (not
      executed here — different, broader scope than this doc's 764-cell carve-out) — see those docs' updated todo text.
- [ ] [DATA] P3. Root-cause and retire whatever wrote the 764 `pipeline_mode=batch_api_football`-tagged duplicate copies
      INTO `sports_reference_v2/by_date/` (still the legacy tree, not canonical `sports_reference/by_date/`) around
      2026-06-24 — see Progress Log finding below. Low urgency (byte-identical duplicates, no correctness impact, all
      mtimes cluster at a single past date so it does not look like an active ongoing writer), but it's an undocumented
      migration-script side-effect worth tracing to its source script and either fixing (write to the correct canonical
      path) or deleting.

## Progress Log

- **2026-08-03** — Filed per operator ruling resolving the § 1b A-vs-B conflict in favor of B.
- **2026-08-03 (data_engineering, slot 14)** — Re-ran the census live against GCS (not against a stale snapshot).
  Methodology: `gsutil ls -r` (bounded to the single `sports_reference_v2/by_date/` prefix — 1,592 objects, 42 MB total,
  NOT a whole-corpus walk) → parsed `day=`/`entity=`/`pipeline_mode=` from each URI → split on the ratified 2020-06-06
  floor.
  - **Live count today: 1,528 physical objects for pre-floor days** (up from the 1,492 cited by the batch5 doc /
    2026-07-22 triage), BUT these decompose to **exactly 764 distinct (day, entity) logical cells** (382 distinct days ×
    2 entities `fixtures`+`fixture_stats`, same day range as the original triage: 2018-01-02..2020-05-25). Every single
    cell (764/764) has TWO physical copies: one at the bare `day={D}/entity={E}/` path and one at
    `day={D}/pipeline_mode=batch_api_football/entity={E}/` — both still under the legacy `sports_reference_v2/` tree
    (not the canonical `sports_reference/` tree). Verified these are true duplicates, not divergent content: all 764/764
    pairs are byte-size-identical, and a 15-pair crc32c spot-check (matching the original triage's 15-sample rigor)
    found 0 mismatches. The pipeline_mode-tagged copies' mtime is 2026-06-24 (sampled) — i.e. they already existed
    before the original 2026-07-22 triage ran, but that triage's own §5 explicitly found "0% pipeline_mode coverage" for
    this population, meaning its classifier did not count these pipeline_mode-tagged siblings into the 1,492/34,385
    figures at all. This reconciles the previously-unexplained "728-row" figure quoted verbatim in
    `sports_satellite_ao_dispatch_batch2_2026_07_24.md:617` and this doc's own source triage (§7 todo 4's completion
    note): the 2026-07-25 rescan's own audit-parquet snapshot recorded exactly 728 v2-pre-floor rows (confirmed by
    reading `gs://…/_index/audit/orphan_sweep_sports.parquet`, mtime 2026-07-25), but ALL entity=`fixture_stats` only (0
    `fixtures`), over a narrower day range (2018-01-02..2019-01-09, 364 days) — a partial/incomplete recording of the
    same underlying 764-cell population, not a separate population.
  - **Re-verified the "sole surviving copy" premise still holds**: ran an exhaustive canonical-twin existence check
    (bounded per-cell `list_blobs(prefix=…, max_results=1)`, 764 checks via a thread pool — not a corpus walk) against
    `sports_reference/by_date/day={D}/entity={E}/` for all 764 cells, plus a 4-day spot check of the
    pipeline_mode-tagged canonical variant and the bare day-level prefix. **Result: 0/764 cells have any canonical twin
    at any path variant** — same conclusion as the 2026-07-22 triage, just against the corrected 764-cell population.
  - **Conclusion: the count is NOT current. Corrected figure is 764 distinct rows** (not 1,492) — the original count
    over-stated physical-object count without deduplicating the in-tree `pipeline_mode=`-tagged sibling copies that
    already existed at triage time but were excluded from that triage's own classification. Todo 2 (copy to canonical)
    has been updated to target the 764-row deduplicated set via the new durable artifact
    `_index/audit/sports_reference_v2_prefloor_census_2026_08_03.parquet` (source columns `bare_uri`/
    `pipeline_mode_uri`, `content_identical_by_size=True` for all 764 rows, `has_canonical_twin=False` for all 764).
  - New finding filed as todo 5 above (adjacent to this doc's own scope, not a separate issue doc): an unexplained,
    apparently one-time (not ongoing) migration-script side-effect wrote pipeline_mode-tagged duplicates into the wrong
    (legacy v2, not canonical) tree — low urgency, tracked for a follow-up trace-and-retire pass.
  - **Dispatch-order gap found + fixed**: this doc had no `sequential: true`, so AO dispatched todo 3 (VERIFY, this
    session's -003) to slot 14 at 00:31 while todo 2 (COPY, -002) was still actively `dispatched` and in-progress on
    slot 15 (dispatched 00:25, not yet `done`) — the same sequential-dispatch-order bug class already tracked in
    `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`. Added `sequential: true` to this doc's
    frontmatter to prevent todo 4/5 from suffering the same premature dispatch. Filed a `/blocked` on task -003 rather
    than duplicate slot 15's in-flight copy work.
- **2026-08-03** (slot 15, backend/data_engineering, task `sports_reference_v2_1492_row_canonical_copy-002`) — Before
  executing todo 2 (the copy), cross-checked against `/codex/02-data/sports-2020-06-data-floor.md` and found a direct
  contradiction: the floor SSOT (same operator, 2026-07-21) mandates WIPING pre-floor sports data, not backfilling it,
  and already executed that wipe for the canonical-tree equivalent of this exact population (`sports_reference/fixtures`
  4,735 objects). The original 2026-07-22 triage doc (`sports_legacy_duplicate_triage_2026_07_22.md` §2/§7)
  independently recommended folding these 1,492 rows into that same wipe (delete), not copying them forward — a
  recommendation that appears to have been lost between then and the § 1b conflict-resolution framing. Filed
  `/plans/active/issues/sports_v2_1492_row_copy_contradicts_floor_wipe_2026_08_03.md` (full evidence + recommendation)
  and a `/blocked` question rather than executing the copy. No GCS object read or written; no code changed for this
  todo. Todo 1 (re-run the census) also not executed — pending the disposition ruling, since a fresh census only matters
  if the copy path is confirmed as correct.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **2026-08-03 (final)**: Operator ruled "agreed" on the wipe-not-copy recommendation. Executed the wipe directly (see
  todo 2 above for full command + result). This doc is now resolved — its title/summary describe the original "copy"
  framing that was superseded; kept as historical record per the Todos section above rather than rewritten.
