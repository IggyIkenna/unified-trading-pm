---
doc_type: issue
title:
  "1,814 legacy `league=` sports raw-tick GCS objects (539 manifest-orphan pairs) have no canonical twin — purge left
  them untouched, disposition undetermined"
summary: >-
  sports_taxonomy_p2_migration_2026_08_08.md's P2 purge todo removed 15,154/16,968 legacy
  `pipeline_mode=batch_footystats`/`venue=ODDS_API` raw-tick sports objects whose content already had a live-confirmed
  canonical `batch_odds_api` twin (market-tick-data-service@8a772b3180). The remaining 1,814 objects
  (2020-06-01..2026-04-14, ~248.8 MB) were correctly excluded by the five-part delete-safety proof — no canonical twin
  exists at their (date, league_id) key, so Part 1 fails and they are `no-migrate-first`, not a delete candidate as
  shipped. Disposition per pair is not yet determined: genuinely irreplaceable legacy-only content (needs a
  migrate-then-delete, mirroring merge_migrated_odds_into_canonical_2026_07_17.py) vs. safe-to-drop bookkeeping residue
  (that script's own docstring documents a 2x bare/no-`league=` duplicate-object pattern in this same population, which
  would never carry a `league_id=`-keyed twin by construction and may be pure noise).
status: open
assigned_vm: planning
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, delete-safety, gcs, manifest-orphan, follow-up]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
parent_epic: sports_master
priority: P3
resolved_by:
locked_by:
created: 2026-08-15
author: slot-11
source: ["sports_taxonomy_p2_migration_2026_08_08.md P2 purge todo, executed 2026-08-15"]
---

# 1,814 orphan legacy `league=` objects — disposition follow-up

## What I found

`purge_league_legacy_objects_2026_08_15.py` (market-tick-data-service, script + full delete-safety-proof docstring at
`scripts/sports/purge_league_legacy_objects_2026_08_15.py`) purged the legacy `league=`
(`batch_footystats`/`venue=ODDS_API`) raw-tick sports population down to exactly the set the census script
(`census_league_vs_league_id_partition_duplication_2026_08_15.py`) had already flagged as lacking a canonical twin:
1,814 objects across the 539 `(date, league_id)` pairs with no `batch_odds_api` counterpart at the same key, confirmed
both via a manifest-level join and a live `list_blobs` re-check on this run. A post-purge fresh re-run confirms exactly
this set remains — 0 further purgeable objects.

Some fraction of these 1,814 are almost certainly the "bare" (no `league=` sub-partition) duplicate objects that
`merge_migrated_odds_into_canonical_2026_07_17.py`'s own module docstring documents: "The migrated population is
internally 2x duplicated — the bare object repeats the 16 league objects with `league_id` NULL." A bare object has no
`league_id` to key a twin against by construction, so it would always land in this orphan set regardless of whether its
underlying content is duplicated elsewhere. The remainder may be genuinely irreplaceable legacy-only data (a real
`(date, league)` cell whose only copy is the legacy path) that never got folded during the 2026-07-17 merge, for reasons
not yet investigated (out of scope for that day's run, a later addition to the population, or a merge-script edge case).

## Why it matters

Per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` Part 1 (twin must RESOLVE via fetch, never constructed),
these objects are `no-migrate-first` as-is — nobody deletes them until either a canonical twin is created (migrate
first) or they're confirmed to be pure bookkeeping noise safe to drop on their own. Left uninvestigated, this is genuine
open scope silently stranded outside every active todo (the P2 purge todo that found them is now closed).

## Recommended decision

Split the 1,814 objects into the two classes above and resolve each:

- [ ] [DATA] P3. **Classify the 1,814 orphan objects: bare/no-`league=` duplicate (safe-to-drop noise) vs. a real
      per-league cell (potentially irreplaceable).** Read the object's own `league=` path segment (bare = empty value) —
      reuse `purge_league_legacy_objects_2026_08_15.py`'s `skipped_no_manifest_twin` counter/report to get the exact
      object list, no new whole-corpus walk. Report the split. (repo: market-tick-data-service)
- [ ] [DATA] P3. **For the bare/no-`league=` duplicates**: confirm via content read (row-key comparison against the SAME
      day's other legacy per-league objects, not just filename shape) that they are truly redundant copies before any
      delete — Part 2 of the delete-safety proof still applies even to an apparent duplicate. If confirmed redundant,
      purge via the same §3a fresh-check pattern as `purge_league_legacy_objects_2026_08_15.py`. (repo:
      market-tick-data-service)
- [ ] [DATA] P3. **For genuine per-league cells with no canonical twin**: run the same read-split-merge migration
      `merge_migrated_odds_into_canonical_2026_07_17.py` used (or a scoped re-run of that script limited to these 539
      pairs) to fold them into canonical, then re-verify a twin now resolves before considering a follow-up delete.
      (repo: market-tick-data-service)

## Progress Log

- **2026-08-15 (slot-11)** — Filed on close of the P2 purge todo. No investigation done yet beyond what the purge
  script's own dry-run/apply reports already surfaced (object count, byte total, exclusion reason).
