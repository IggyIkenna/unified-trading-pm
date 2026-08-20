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
status: resolved
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
resolved_by: market-tick-data-service@e0cdaff5ee (fold) + purge_confirmed_bare_league_legacy_orphans_2026_08_16.py run (harness task b1t1m4oz5)
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
last_updated: 2026-08-16 # status flipped resolved -- all 3 todos done, 280/280 divergent-content days folded into canonical then purged, 0 open items remain
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
- [x] [DATA] P3. **DONE 2026-08-16 (slot-23) — 280/280 folded then purged, 0 open items remain.** RESCOPED 2026-08-16 (slot-23), root-cause CONFIRMED same session — the 280 `bare_no_league` days
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
- **2026-08-16 (slot-23, continuation 2)** — Regenerated the verify-report per the deferred table's row 1:
  `verify_bare_league_legacy_orphan_content_2026_08_16.py --orphan-report /tmp/classify_report_2026_08_16.jsonl
  --report /tmp/verify_report_2026_08_16.jsonl` (read-only, backgrounded standalone, completed exit 0). **Result:
  280/280 lines, all `disposition=no-migrate-first`** (bare_rows=7,915,337, matched_rows=7,478,332,
  unmatched_rows=437,005) — confirms the population todo 3 targets is unchanged since todo 2's purge. Launched the
  fold script's dry-run (no `--apply`) against this fresh report to measure `rows_added` before writing, rather than
  trusting the `428,933` figure already in todo 3's text (that figure predates this verify-report regen and was not
  re-measured against it).
- **2026-08-16 (slot-23, continuation 3)** — Dry-run confirmed sane (`rows_added=428,933`, `cells_created=0`,
  zero errors across 280/280 days — matches the pre-verify-report-regen figure exactly). Launched the real
  `--apply` write standalone in the background (`--verify-report /tmp/verify_report_2026_08_16.jsonl --report
  /tmp/fold_apply_2026_08_16.jsonl`, PID 3435671). **Lesson — a backgrounded `nohup … &` process can still die
  silently with no attributable cause**: this run progressed cleanly to 89/280 (`created=0` holding on every row,
  matching the dry-run's per-row behavior exactly) then the process vanished — no Python traceback in its log, no
  OOM entry in `journalctl -k` for the window, host uptime showed no reboot since 2026-08-09, `free -h` and `df -h`
  both healthy at time of discovery. Root cause **undetermined** (possibly an external kill from another session
  sharing this slot's checkout, per the earlier SLOT COLLISION WARNING this session saw — not confirmed). Since the
  script is MERGE-only/idempotent by design (existing canonical rows always win on key collision, row-loss guard
  refuses a would-shrink write), the safe response was to just relaunch the identical `--apply` command fresh
  (`--report /tmp/fold_apply_2026_08_16_run2.jsonl` to avoid conflating with run1's partial 89-line output; PID
  3600518) rather than attempt a partial-resume. **Idempotency confirmed in practice, not just by design**: run2's
  re-processing of the same early days run1 had already completed showed `rows_added=0`/`written=0` for each
  (their rows were already present in canonical from run1's landed writes before it died) — proof run1's partial
  progress persisted correctly to GCS despite the unexplained kill. Run2 is the live, authoritative apply attempt
  going forward; run1's partial report/log are superseded, not needed for anything further.
- **2026-08-16 (slot-23, continuation 4) — root cause CORRECTED, was "undetermined"**: run2 also died silently, at
  113/280 (`journalctl` confirmed `orphan_reap sweep: slot 23 pid 3600518 age=318s KILLED`). This is the documented
  `nohup <cmd> & echo PID` anti-pattern from
  `/plans/archive/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` — both run1 and run2
  were launched as `nohup … > log 2>&1 &` inside a plain Bash call, which detaches the real process from the tracked
  session tree; the orphan_reap sweep then SIGKILLs it ~300-355s after it reparents to init. Run1's "undetermined"
  verdict in the prior entry is corrected: it was almost certainly this same mechanism (89/280 took ~5:51 ≈ 351s,
  inside the documented band), not an external/slot-collision kill. **Fix applied**: relaunched a third time
  (`--report /tmp/fold_apply_2026_08_16_run3.jsonl`) using the harness's native `run_in_background: true` Bash
  parameter directly on the long-running command — no `nohup`/`&` wrapper — which keeps the process correctly
  parented and exempt from the orphan sweep, per that doc's already-shipped `worker.md` guidance (which this session
  should have followed from the start). Idempotency (proven safe twice now) again makes the relaunch zero-cost.
- **2026-08-16 (slot-23, continuation 5) — run3 completed 280/280, exit 0** (harness task `bz44854ny`, native
  `run_in_background: true`, never touched by `orphan_reap`). Own totals: `cells_written=13331,
  cells_skipped_no_new_keys=21342, cells_created=0, rows_added=356092`. **Sanity-check against the dry-run baseline**:
  summed `rows_added` across all three runs' report jsonls (run1 89 days=49,293 + run2 113 days=22,486 + run3 280
  days=356,092) = **427,871 cumulative, vs the dry-run's 428,933** — a 1,062-row (0.25%) gap. Checked for a real
  problem: zero WARN/ERROR/guard-refusal lines in run3's log, zero `error`/`skipped`/non-ok `status` fields in any of
  the three report jsonls, `rows_added` computed by the identical code path (`rep.rows_added += new_keys`) in dry-run
  and apply — ruled out a script defect. Most plausible explanation: canonical `batch_odds_api` continued receiving
  normal live writes in the ~40min between the dry-run and run3 finishing, so a small number of keys that were "new"
  at dry-run time had already landed in canonical by apply time and were correctly skipped
  (`cells_skipped_no_new_keys`) rather than double-written — this is the merge-never-overwrite guarantee working as
  designed, not data loss. `cells_created=0` throughout confirms no spurious new objects. Proceeding on this basis.
  Launched the post-apply re-verify (read-only) as harness task `bt03cyvxr`, same native `run_in_background: true`
  pattern: `verify_bare_league_legacy_orphan_content_2026_08_16.py --orphan-report
  /tmp/classify_report_2026_08_16.jsonl --report /tmp/verify_report_2026_08_16_postfold.jsonl` (new report filename,
  distinct from the pre-fold baseline at `/tmp/verify_report_2026_08_16.jsonl` — that file is left untouched as the
  dry-run-time record).
- **2026-08-16 (slot-23, continuation 6) — post-apply re-verify confirmed 280/280 `fully_redundant`, purge launched
  and completed. TODO 3 DONE, ISSUE RESOLVED.** Task `bt03cyvxr` completed exit 0:
  `/tmp/verify_report_2026_08_16_postfold.jsonl` shows **`disposition_fully_redundant=280`, `unmatched_rows=0`,
  `bare_rows=7,915,337` all matched** — the fold fully closed the divergence for every one of the 280 days, confirming
  run3's writes (and the two partial predecessor runs) landed correctly. Log noise was 6 benign `WARNING Connection
  pool is full, discarding connection: oauth2.googleapis.com` lines (gRPC/oauth connection churn under load), not real
  errors. Launched the delete-only purge standalone (never combined with verify, per the established sequencing
  lesson) via the harness's native `run_in_background: true` (no `nohup`):
  `purge_confirmed_bare_league_legacy_orphans_2026_08_16.py --verify-report
  /tmp/verify_report_2026_08_16_postfold.jsonl --apply --confirm-prod-delete` → harness task `b1t1m4oz5`, completed
  exit 0: `§3a fresh soft-delete-retention check: 604800s`, `fully_redundant objects loaded: 280`, **`TOTALS over 280
  objects (apply=True): deleted: 280`** — every one of the 280 now-redundant bare legacy objects removed, matching
  the verify population exactly. Combined with todo 2's earlier 1,534-object purge, the entire 1,814-object
  `bare_no_league` legacy population (100%) is now resolved: 1,534 were pure duplicates (purged 2026-08-16 without a
  fold), 280 had genuinely unique tail-of-day content (folded into canonical, then purged once redundant). 0
  `per_league_cell` orphans ever existed (todo 1). All three todos in this doc are now closed with 0 open items —
  flipping doc to `status: resolved` and archiving.

## Deferred work after 2026-08-16 (CLOSED — all items resolved, doc archived same commit)

| Item | State | Blocked on |
| --- | --- | --- |
| Regenerate verify-report: `verify_bare_league_legacy_orphan_content_2026_08_16.py --orphan-report /tmp/classify_report_2026_08_16.jsonl --report /tmp/verify_report_2026_08_16.jsonl` (read-only, **no** `--apply`/`--confirm-prod-delete`) | **Done 2026-08-16 (slot-23)** — 280/280 lines, all `disposition=no-migrate-first` (matched_rows=7,478,332, unmatched_rows=437,005, bare_rows=7,915,337) | — |
| `fold_divergent_bare_league_legacy_orphans_2026_08_16.py --apply --verify-report /tmp/verify_report_2026_08_16.jsonl --report /tmp/fold_apply_2026_08_16_run3.jsonl` | **Done 2026-08-16 (slot-23)** — run3 (harness task `bz44854ny`) reached 280/280, exit 0. Cumulative `rows_added` across all 3 runs = 427,871 vs dry-run baseline 428,933 (0.25% gap, reconciled — see Progress Log, explained by ongoing live canonical writes between dry-run and apply, no errors/guard-refusals). | — |
| Post-apply re-verify the 280 days now resolve `fully_redundant` | **Done 2026-08-16 (slot-23)** — harness task `bt03cyvxr`, exit 0. All 280/280 days `disposition=fully_redundant`, `unmatched_rows=0`. | — |
| Purge the newly-redundant bare objects | **Done 2026-08-16 (slot-23)** — harness task `b1t1m4oz5`, exit 0. `deleted: 280` / `fully_redundant objects loaded: 280` — 100% of the population purged, §3a retention check passed at 604800s. | — |
| Flip this todo `[x]` with the purge script's SHA + object/byte counts, then archive this doc (last open item) | **Done 2026-08-16 (slot-23)** — todo 3 flipped above; doc frontmatter set `status: resolved`, `resolved_by:` cites the fold commit + purge task; `git mv` to `plans/archive/issues/` in the same commit as this edit. | — |
| `sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md` todo 1 ("Scope the duplication") | Not done, independently pickup-able | Nothing — unrelated to this now-closed chain |

**This issue is fully resolved — no further action needed on it.** The unrelated
`sports_canonical_batch_odds_api_duplicate_rows_2026_08_16.md` todo remains open and independently pickup-able by any
future session; it is not part of this chain.
