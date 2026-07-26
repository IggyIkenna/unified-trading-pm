---
doc_type: issue
title: batch_footystats "copy+swap" todo names the wrong script — real fix is the unrun 2026-07-17 merge
summary: >-
  sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id casing migration todo describes the remaining
  batch_footystats step (16,970 objects) as "the same casing-migration script re-run/extended". Investigated instead of
  assuming: the live batch_footystats objects are NOT the path shape migrate_sports_league_id_casing_2026_07_21.py
  handles at all — they are the older mis-stamped population from
  issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md (now archived, but the DATA fix was never
  actually applied), whose purpose-built merge script (merge_migrated_odds_into_canonical_2026_07_17.py) was written and
  pilot-verified but never run to completion — its expected output shard (_index/per_vm/odds-restamp-20260717.parquet)
  does not exist. Same population (16,969 vs 16,970 — rounding/count- drift only), described two different ways by two
  docs that have drifted apart.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, league-id, footystats, migration, plan-drift]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md,
    /plans/active/issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md,
  ]
created: 2026-07-25
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P1
estimate_class: infra
source: sports_satellite_ao_dispatch_batch2_2026_07_24.md, league_id casing migration todo, batch_footystats sub-step
resolved_by:
  sports_satellite_ao_dispatch_batch5_2026_07_26.md (verification), corroborated by
  sports_satellite_ao_dispatch_batch2_2026_07_24.md step-4 CORRECTED addendum + orphan-delete-staging doc's manifest
  census
locked_by:
drift_direction: advance-code
depends_on: []
---

# batch_footystats "copy+swap" todo names the wrong script

## What I found (2026-07-25, slot 11, data_engineering)

While the MDPS `odds_horizon_bucket` reprocess VMs (per
`issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`) ran, investigated the parent todo's
`batch_footystats` sub-step (16,970 objects, described as "the same casing-migration script re-run/extended, using the
already-verified classification map") rather than executing it blind against PROD.

1. **Path shape mismatch.** `migrate_sports_league_id_casing_2026_07_21.py`'s `RAW_RE` only matches
   `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_odds_api/asset_group=sports/venue=<V>/league_id=<RAW>/instrument_type=odds/data_type=trades/ticks.parquet`.
   Confirmed via `gcloud storage ls -r` on a live sample day (2024-01-15) that the actual
   `pipeline_mode=batch_footystats` objects are:
   `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/instrument_type=/data_type=odds/league=<RAW>/ticks_migrated_<ts>.parquet`
   — a completely different shape (`league=` not `league_id=`, `instrument_type=` empty, filename pattern
   `ticks_migrated_*` not `ticks`). The casing script's regex would not match a single one of these objects; there is no
   sense in which it can be "extended" to this shape without becoming a different script.
2. **This is the known, already-scoped, never-completed 2026-07-17 migration.** These are the exact objects described in
   `issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` (archived — the ISSUE doc is closed out of
   the active corpus, but that closure evidently tracked the analysis/script being written, not the DATA actually being
   fixed). The purpose-built executor is
   `market-tick-data-service/scripts/merge_migrated_odds_into_canonical_2026_07_17.py` — a read-split-merge with
   measured family-A/B schema coercion, tick-key de-dup, and a MERGE-never-overwrite invariant, pilot-verified
   2026-07-17 on real data (83,732/5,626/83,916/184/78,290 exact reproduction cited in its own docstring).
3. **It was never actually run.** The script's own manifest shard path,
   `market-data-tick-sports-prd-central-element-323112/_index/per_vm/odds-restamp-20260717.parquet`, does not exist
   (confirmed via `gcloud storage ls`). Its docstring's lifecycle marker
   (`Delete-when: after the 199 derive-gain days are merged + verified and .../mistamped_footystats_2026_07_16.md archives`)
   shows the issue doc was archived without that gate being satisfied — the issue closed on the analysis being complete,
   not the fix landing.
4. **Object count matches.** The merge script's docstring cites "16,969 canonical objects carry
   `pipeline_mode=batch_footystats`"; this plan's todo cites "16,970 objects" for the same population. Close enough
   (likely a few objects' drift since 07-17) to be confident this is the same corpus, not a coincidence.

## Why this matters

If a future worker follows the current todo text literally ("extend the casing script to that shape"), they will either
burn time reverse-engineering a regex extension for a shape the script was never designed for, or worse, force-fit
output that produces wrong `league_id`/`venue`/schema-family values on a PROD write path — the exact class of
silent-corruption bug this whole plan's league_id-namespace work exists to eliminate.

## What still needs doing (not done here — see below for why)

1. Reconstruct the days-file the merge script needs (`--days-file`, one `YYYY-MM-DD` per line) — likely: every day under
   `pipeline_mode=batch_footystats/` that has a `_migrated_` object. This is a listing scoped to one prefix, not a new
   whole-corpus walk.
2. Run `merge_migrated_odds_into_canonical_2026_07_17.py` (default dry-run) first to re-verify its measured invariants
   still hold — data may have changed since 2026-07-17 (nearly 2 weeks).
3. `--apply` once the dry-run numbers look sane vs. the docstring's pilot baseline; use `--report`+`--shard-path` per
   its own manifest-safety guidance (flush after every day, never end-of-run-only).
4. **THEN** — separately — check whether the merged cells' `league_id` values are already canonical or still need a
   `migrate_sports_league_id_casing_2026_07_21.py` follow-up pass. Do not assume either way; check by content. This is a
   genuine 2-step sequence, not the 1-step "extend the casing script" the current todo text implies.

## Why not executed here

This session was concurrently monitoring 4 sharded MDPS `odds_horizon_bucket` reprocess VMs (the plan's own P0 priority
for this todo) and did not want to reconstruct an untracked days-file and run a PROD merge write blind under split
attention. The investigation above (read-only: `gcloud storage ls`, docstring/regex reading) is safe and narrows the
next worker's path considerably — no re-investigation needed, go straight to step 1 above.

## Resolution (2026-07-26, slot-6, `data_engineering`)

**SUPERSEDED — the merge this doc calls for already happened, on the same day this doc was filed.** This doc's own "What
still needs doing" section (above) was written 2026-07-25 without checking whether the merge had already run elsewhere;
it had, one day earlier.

- `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s step (4) "batch_footystats copy+swap" section carries a
  "CORRECTED 2026-07-25 (slot 7)" addendum citing `market-tick-data-service@75f226e8` ("feat(sports): read-split-merge
  the mis-stamped batch_footystats odds population into canonical") — 0 rows lost, acceptance-tested. **Verified here**:
  `75f226e8` exists in `market-tick-data-service` history and its commit body matches this doc's exact "purpose-built
  read-split-merge, `merge_migrated_odds_into_canonical_2026_07_17.py`" description (1,815 days probed, 199 genuine-gain
  days merged, 1,336 pure-duplicate days, 280 add-keys-but-zero-derive days deferred).
- `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` independently re-verified the
  post-merge state via a full exhaustive re-census (2,139-day calendar superset, 0 missing days): the manifest carries
  **zero** rows for `pipeline_mode=batch_footystats AND source(case-insens)=ODDS_API` — the mis-stamped population is
  gone from the manifest; only orphaned GCS bytes remain (human-gated PROD delete, tracked there).
- **Re-verified fresh here** (not just re-citing): (a) `75f226e8` confirmed present in `market-tick-data-service` git
  history via `git log`/`git show`, touching exactly the merge path described. (b) Re-ran the manifest census directly
  (`read_availability_index` on `market-data-tick-sports-prd-...`, live, 2026-07-26): 42,476 rows carry
  `pipeline_mode=batch_footystats`, **0** of them have `source(case-insens)=ODDS_API` (all 42,476 now carry
  `source=footystats`) — confirms the orphan-delete-staging doc's finding still holds today, not stale.

This doc's 3 open todos are therefore moot: todo 1+2 (reconstruct days-file, run/apply the merge) are already done
(`75f226e8`); todo 3 (correct batch2's todo text) is unnecessary because batch2's own "CORRECTED 2026-07-25" addendum
already supersedes its original wording in place — editing it again would just be a duplicate touch on a file another
slot already fixed. The sole remaining work is the human-gated orphan-object PROD delete tracked in
`issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` — not script-extension work.

## Todos

- [x] ✅ SUPERSEDED 2026-07-26 (slot-6). Reconstruct the `batch_footystats` days-file and run
      `merge_migrated_odds_into_canonical_2026_07_17.py` dry-run — already done as `market-tick-data-service@75f226e8`
      (2026-07-17, re-applied/confirmed 2026-07-25). See Resolution above.
- [x] ✅ SUPERSEDED 2026-07-26 (slot-6). `--apply` the merge + check league_id casing follow-up — already done in the
      same commit; the orphan-delete-staging doc's fresh census confirms the post-merge manifest state holds. See
      Resolution above.
- [x] ✅ SUPERSEDED 2026-07-26 (slot-6). Correct batch2's todo text — unnecessary; batch2 already self-corrected via its
      own "CORRECTED 2026-07-25" addendum. See Resolution above.
