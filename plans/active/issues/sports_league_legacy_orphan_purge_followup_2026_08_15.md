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
context_scope:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/sports/purge_league_legacy_objects_2026_08_15.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
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

- [x] ✅ [DATA] P3. **Classify the 1,814 orphan objects: bare/no-`league=` duplicate (safe-to-drop noise) vs. a real
      per-league cell (potentially irreplaceable).** Read the object's own `league=` path segment (bare = empty value) —
      reuse `purge_league_legacy_objects_2026_08_15.py`'s `skipped_no_manifest_twin` counter/report to get the exact
      object list, no new whole-corpus walk. Report the split. (repo: market-tick-data-service) — **DONE
      2026-08-16, live-measured, not sampled**: shipped `classify_league_legacy_orphan_objects_2026_08_16.py`
      (`market-tick-data-service@ae1f27a4af`), which re-derives the manifest-level twin join LIVE (never trusts a
      prior run's counters) then re-lists the exact same candidate-date prefixes
      `purge_league_legacy_objects_2026_08_15.py` already scopes (2,128 candidate dates, one targeted prefix listing
      per date — no new whole-corpus walk) and reads each surviving object's own `league=` path segment. **Result:
      1,814/1,814 orphan objects (100%) are `bare_no_league` — 0 are `per_league_cell`.** Every remaining object's
      `league=` segment is empty (e.g.
      `gs://market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=2020-06-06/pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/instrument_type=/data_type=odds/ticks_migrated_20260505T152043Z.parquet`,
      no `league=` sub-partition at all). Full per-object report (uri/date/league/size/disposition, one JSON line
      each) written this session; not checked in (regeneratable from the script, one-off scratch artifact). **This
      resolves the open question in this doc's own summary**: the population is NOT a mix needing per-pair triage —
      it is uniformly the bare/no-`league=` duplicate class `merge_migrated_odds_into_canonical_2026_07_17.py`'s
      docstring already predicted, consistent with every per-league object that DID have a canonical twin having
      already been purged by the P2 run (a bare row has no `league_id` to key a twin against by construction, so it
      always lands in the orphan set regardless of content). **Consequence for todo 3 below**: with 0 measured
      `per_league_cell` objects, there is no genuine per-league cell to fold via a
      `merge_migrated_odds_into_canonical_2026_07_17.py`-style migration — that todo appears MOOT on this evidence,
      but is left unflipped here (out of this todo's own scope) for its own dispatch to close on this citation. Todo
      2 (content-verify the bare duplicates before any purge) remains the real next step, now scoped to a fully
      enumerated, non-mixed 1,814-object population.
- [x] ✅ [DATA] P3. **For the bare/no-`league=` duplicates**: confirm via content read (row-key comparison against the SAME
      day's other legacy per-league objects, not just filename shape) that they are truly redundant copies before any
      delete — Part 2 of the delete-safety proof still applies even to an apparent duplicate. If confirmed redundant,
      purge via the same §3a fresh-check pattern as `purge_league_legacy_objects_2026_08_15.py`. (repo:
      market-tick-data-service) — **DONE 2026-08-16 (slot-23) — market-tick-data-service@2471d18f (verify) +
      @cbd21be68 (delete-only purge, landed).** Content-verify (row key `(instrument_id, bm_time, price, point)`, live-probed
      against a sample match to confirm exact schema alignment) was run across all 1,814 `bare_no_league` objects,
      comparing every bare row against the live canonical `batch_odds_api` rows for the same day (scoped to only the
      bookmaker venues present in the bare object — no whole-corpus walk). **The original "almost certainly pure
      bookkeeping noise" hypothesis was WRONG for a real fraction**: only **1,534/1,814 days (84.6%) are fully
      redundant** (every row matches canonical exactly); **280/1,814 days (15.4%, 437,005 rows out of 51.0M total)
      carry genuine content NOT present in canonical** — plausibly a different scrape cadence between the legacy
      footystats-sourced migration and the direct odds_api scraper, not yet root-caused. Purged ONLY the 1,534
      confirmed-redundant objects via `gcs_conditional_delete` (§3a fresh check: bucket soft-delete retention =
      604800s, cleared); the 280 divergent-content objects were LEFT UNTOUCHED (Part 2 fails for them —
      `no-migrate-first`). Post-delete verified: 1,534/1,534 objects gone (0 errors). **Lesson for future sessions**:
      the combined verify+delete `--apply` path (`verify_bare_league_legacy_orphan_content_2026_08_16.py`) was
      externally killed 3 consecutive times mid-run (session/background-task-lifecycle related — no zombie process, no
      OOM signal; likely a runtime cap on backgrounded delete-performing scripts specifically, not read-only ones,
      which completed cleanly twice in the same session) — worked around by splitting into a separate delete-only
      script (`purge_confirmed_bare_league_legacy_orphans_2026_08_16.py`) that skips re-verification for
      already-confirmed days and only does the small fixed set of REST calls needed to delete, completing the full
      1,534-object purge in under 90s.
- [ ] [DATA] P3. **RESCOPED 2026-08-16 (slot-23), root-cause CONFIRMED same session** — the 280 `bare_no_league` days
      that FAILED content-verify (real unmatched content, not present in canonical `batch_odds_api`) needed
      investigation + fold-in, not the "genuine per-league cells" framing this todo originally had (todo 1 already
      established 0 `per_league_cell` orphans exist — this is a different population, discovered by todo 2's
      content-verify, not todo 1's structural classification). **Root cause, live-measured 2026-08-16 (slot-23) —
      NOT a key-matching false-negative, NOT a total per-instrument absence: a genuine scrape-cadence/coverage gap.**
      Spot-checked 3 days spanning the full range (2020-06-10 earliest, 2022-02-20 middle, 2026-02-13 latest): in
      every case the unmatched rows' own `instrument_id` IS present in canonical with its earlier ticks matching
      exactly on `(bm_time, price, point)`; only that instrument's LATEST one-to-few ticks for the day are missing
      from canonical. The legacy footystats-sourced migration's capture window ran slightly later than
      `batch_odds_api`'s live capture consistently — real, unique market data, not noise. Unmatched-row distribution
      (bookmaker/league mix, ~0.4%-9.6% of a day's rows) is proportional to each bookmaker/league's overall
      representation, consistent with a small per-instrument tail gap rather than a systematic venue-naming/key bug.
      **Fold-in shipped**: `fold_divergent_bare_league_legacy_orphans_2026_08_16.py`
      (`market-tick-data-service@e0cdaff5ee`) mirrors `merge_migrated_odds_into_canonical_2026_07_17.py`'s
      read-split-merge pattern, targeting the canonical `data_type=odds` cell family (measured live:
      `bookmaker_key := instrument_id[1].lower()`, `league_id := instrument_id[3]` case-matched against the
      existing cell, `fixture_id := ''`, `available_at := bm_time + 5s` — all measured 100% on a live sample, the
      `available_at` rule identical to the July script's). MERGE-never-overwrite with the same row-loss guard.
      3-day dry-run sample confirmed `rows_added` exactly matches each day's `unmatched_rows` from the verify
      report; full 280-day dry-run (pre-ship) confirmed `280/280 no-migrate-first days processed, rows_added=428,933,
      zero errors`. QG green (`QG_EXIT=0`), shipped. **Remaining steps (live status 2026-08-16, slot-23,
      see Progress Log)**: the `--verify-report` input jsonl used for the ship-day dry-run was `/tmp` scratch that
      did not survive to this continuation — regenerated `classify_league_legacy_orphan_objects_2026_08_16.py`
      live (read-only, no new whole-corpus walk, same 2,128 already-scoped candidate dates) at
      `/tmp/classify_report_2026_08_16.jsonl`, confirming **280/280 bare_no_league, 0 per_league_cell** (exactly the
      280 divergent days todo 2 left untouched — proves todo 2's 1,534-object purge is still intact, nothing regrew).
      Still needed before `--apply`: (1) re-run `verify_bare_league_legacy_orphan_content_2026_08_16.py`
      **read-only** (no `--apply`/`--confirm-prod-delete` — that flag pair also deletes, not needed here) against
      `/tmp/classify_report_2026_08_16.jsonl` to regenerate the verify-report all 280 days should again show
      `disposition=no-migrate-first` against; (2) `fold_divergent_bare_league_legacy_orphans_2026_08_16.py --apply
      --verify-report <that path>` (MERGE-only write, row-loss guard, idempotent — safe to re-run); (3) re-verify the
      280 days now resolve `fully_redundant`; (4) purge the newly-redundant bare objects mirroring
      `purge_confirmed_bare_league_legacy_orphans_2026_08_16.py`'s already-proven §3a pattern. (repo:
      market-tick-data-service)

## Progress Log

- **2026-08-15 (slot-11)** — Filed on close of the P2 purge todo. No investigation done yet beyond what the purge
  script's own dry-run/apply reports already surfaced (object count, byte total, exclusion reason).
- **2026-08-16 (slot-27)** — Todo 1 done: shipped + live-ran `classify_league_legacy_orphan_objects_2026_08_16.py`
  (`market-tick-data-service@ae1f27a4af`). Measured split: **1,814/1,814 bare_no_league, 0 per_league_cell** — the
  entire orphan population is the bare/no-`league=` duplicate class, none are genuine irreplaceable per-league cells.
  Todo 3 looks moot on this evidence (nothing to fold); left for its own dispatch to close.
- **2026-08-16 (slot-23)** — Todo 2 done: content-verified all 1,814 `bare_no_league` objects against live canonical
  `batch_odds_api` rows (row key `instrument_id, bm_time, price, point`). Split: 1,534 (84.6%) fully redundant, 280
  (15.4%, 437,005 rows) genuinely divergent — the plan's original "almost certainly noise" hypothesis was wrong for a
  real fraction. Purged the 1,534 confirmed-redundant objects via §3a-gated `gcs_conditional_delete` (bucket
  soft-delete retention 604800s cleared); left the 280 divergent-content objects untouched. Rescoped todo 3 to
  investigate + fold the 280-day divergence (was previously framed around todo 1's "genuine per-league cells" axis,
  which is a different, already-empty population). `market-tick-data-service@2471d18f` (verify script),
  `@cbd21be68` (delete-only purge, built after the combined verify+apply path was externally killed 3× mid-run;
  note this SHA superseded an earlier `4aa781a2` citation after a `git pull --rebase --autostash` rewrote the
  already-committed-but-unpushed purge-script commit, and THAT `caf81cfd` citation was itself superseded a second
  time by `cbd21be68` when Pass-2 quickmerge hit a push-rejection and auto-rebased onto origin's tip before
  landing — recurring pattern: cite a purge-script SHA only after `git rev-list --count origin/<branch>..HEAD`
  confirms it as the actual pushed/ancestor commit, not the pre-push local SHA).
- **context-scout 2026-08-15**: populated context_scope (4 entries).
- **2026-08-16 (slot-23, continuation)** — Shipped `fold_divergent_bare_league_legacy_orphans_2026_08_16.py`
  (`market-tick-data-service@e0cdaff5ee`) after a real (non-queue-artifact) QG run confirmed green
  (`QG_EXIT=0`; the only non-blocking noise was a §5.90 warn-only live/batch parity audit unrelated to this file,
  and a §5.94/5.95 informational ratchet-trend line). **Lesson — don't assume `/tmp` scratch survives a
  session boundary**: the `--verify-report` jsonl the pre-ship dry-run consumed (per todo 2's own text, produced
  by `verify_bare_league_legacy_orphan_content_2026_08_16.py@2471d18f`) was gone by this continuation — only the
  fold script's own 3-line spot-check input (`verify_pick.jsonl`) and its 280-line dry-run *output*
  (`fold_dryrun.jsonl`) had survived, not the verify-report *input*. Confirmed via this doc's own todo-1 text that
  the classify report was **always** documented as "regeneratable from the script, one-off scratch artifact, not
  checked in" — so regenerating (not treating this as data loss) is the correct, already-sanctioned response.
  Regenerated `classify_league_legacy_orphan_objects_2026_08_16.py` live → **280/280 bare_no_league, 0
  per_league_cell** (`/tmp/classify_report_2026_08_16.jsonl`), which also incidentally re-confirms todo 2's
  1,534-object purge is still intact (only the 280 known-divergent days remain in the bucket at all — if the purge
  had partially reverted, this count would exceed 280). Did not have time this session to also regenerate the
  verify-report (needs a full read-only pass over 280 objects' content, not a quick op) or run `--apply` — next
  session's first move is named in the table below.

## Deferred work after 2026-08-16

| Item | State | Blocked on |
| --- | --- | --- |
| Regenerate verify-report: `verify_bare_league_legacy_orphan_content_2026_08_16.py --orphan-report /tmp/classify_report_2026_08_16.jsonl --report /tmp/verify_report_2026_08_16.jsonl` (read-only, **no** `--apply`/`--confirm-prod-delete`) | Not done | Nobody — real work, pick up next |
| `fold_divergent_bare_league_legacy_orphans_2026_08_16.py --apply --verify-report /tmp/verify_report_2026_08_16.jsonl --report /tmp/fold_apply_2026_08_16.jsonl` | Not done | The verify-report regen above |
| Post-apply re-verify the 280 days now resolve `fully_redundant` | Not done | The `--apply` run above |
| Purge the newly-redundant bare objects (mirror `purge_confirmed_bare_league_legacy_orphans_2026_08_16.py`'s §3a pattern: fresh `gcs_bucket_soft_delete_retention_seconds >= 604800` check same-run, `--confirm-prod-delete`) | Not done | The post-apply re-verify above |
| Flip this todo `[x]` with the purge script's SHA + object/byte counts, then archive this doc (last open item) | Not done | The purge above |
| `sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md` todo 1 ("Scope the duplication") | Not done, independently pickup-able | Nothing — unrelated to this chain |

**Recommended next item**: the verify-report regen (row 1) — it's the direct unblock for everything else in this
chain, is read-only (no delete-safety gating needed), and per the lesson above, `--apply`-performing GCS scripts on
this host have been externally killed mid-run before when combined into one process; run it as its own standalone
step and confirm the report file exists with 280 lines before moving to `--apply`.
