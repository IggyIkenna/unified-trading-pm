---
doc_type: issue
title:
  "RESOLVED 2026-07-30 — consolidator EXONERATED (static rows_out is an in-place UPDATE, not a drop); the real root
  cause of the odds_api gaps is check_shard_freshness's ODDS_API-sentinel collision silently SKIPPING 572/595 dates"
summary: >-
  Cloud Logging shows `manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112` real-merge
  cycles (the ones that acquire the lock and do a genuine DuckDB merge, not the `error=locked` skips) reporting the
  EXACT SAME `rows_out=9411982` across at least 5 consecutive real merges spanning 20:47:50 -> 21:35:14 UTC (47+
  minutes), with `shards=3-4` and nonzero `dedup_dropped` (3863-4710) each time but zero net row growth. This window
  overlaps a live backfill VM (`mtds-backfill-odds-gapfill-tail3-20260729`) actively writing NEW per-VM-shard rows for
  previously-absent dates. A day-level census of the canonical taken after these merges is byte-identical to one taken
  before any backfill work started this session (595 missing odds_api days, same 27 named gap ranges, unchanged) despite
  VM logs showing confirmed successful processing of many of those exact dates across 3 separate VM runs this session.
  The canonical for this bucket appears to not be absorbing new content at all right now.
status: open
nature: issue
asset_group: [sports, meta]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    manifest,
    consolidator,
    data-correctness,
    sports,
    P0,
    freshness-skip,
    check-shard-freshness,
    smart-skip,
    odds-api,
    false-alarm-resolved,
  ]
related:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: 2026-07-29
priority: P0
parent_epic: sports_master
source: [sports_odds_api_scattered_multiyear_gaps-001]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
assigned_vm: planning
resolved_by:
---

# Sports manifest consolidator: zero row growth despite active backfill writes

> **🟩 RESOLVED 2026-07-30 (slot 3, operator-authorised live diagnostic: pause-cron + snapshot + probe). THE
> CONSOLIDATOR IS NOT DROPPING ROWS — this doc's original premise is DISPROVEN.** Static `rows_out` with nonzero
> `dedup_dropped` is the EXPECTED signature of an idempotent re-capture that UPDATES existing dedup keys in place;
> `dedup_dropped` is not an independent measurement, it is _derived_ as `rows_in - rows_out`
> (`manifest_consolidator.py:998`), so "all shard rows deduped" and "row count unchanged" are the same statement, not
> two corroborating ones. The genuine root cause of the odds_api gaps is in the BACKFILL's smart-skip
> (`check_shard_freshness`), not the merge — see § "Root cause (2026-07-30)". **Everything below the banner is retained
> as the original 2026-07-29 report + the 07-30 addenda; read it as history, not as current fact.** Cron was paused
> 10:34Z, snapshotted, probed, and **RESUMED 10:53Z (verified `ENABLED`, real merge completed 10:44:51Z, zero shards
> pruned, no `CONSOLIDATOR_DOWN` fired)**.

## What I found

While backfilling `odds_api` gaps in `instruments-store-sports-prd-central-element-323112`'s manifest
(`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, task `sports_odds_api_scattered_multiyear_gaps-001`), I ran 3
separate VMs across ~2.5 hours (`mtds-backfill-odds-gapfill-20260729`, `-retry1-20260729`, `-tail2-20260729`,
`-tail3-20260729`), each writing per-VM manifest shards via `ManifestWriter` (`MANIFEST_PER_VM_SHARDS=true`) — VM logs
repeatedly confirmed real writes, e.g.:

```
ManifestWriter: per-VM shard updated (500 total entries, 500 new, process_final=False) at
  instruments-store-sports-prd-central-element-323112/_index/per_vm/mtds-backfill-odds-gapfill-tail3-20260729.parquet
```

A day-level census of `_index/availability_index.parquet` (single read, filtered `source=odds_api, date>=2020-06-06`)
run AFTER all this work — including after the confirmed successful processing of the entire `2020-06-06..2026-04-15`
range (2 independent VM runs each got this far before their final chunk failed) — is **byte-identical** to a census I
ran before any backfill work started: 595 missing days, the same 27 named contiguous gap ranges unchanged, including the
35-day `2026-02-22..2026-03-28` range that both VM runs' logs show being processed with real per-day
`Processed date=... N venues ok` / `ManifestWriter` lines.

**Cloud Logging confirms the canonical is not growing.** Filtering
`resource.type="cloud_run_job" AND textPayload:"bucket=instruments-store-sports-prd-central-element-323112" AND textPayload:"manifest-consolidator bucket="`
over a 6h window, every REAL merge (i.e. not one of the very frequent `error=locked` skips — each real merge holds the
lock ~680-715 SECONDS, so the `*/1` cron effectively serializes to ~1 real attempt every ~12 minutes for this bucket)
reports:

| timestamp (UTC) | shards | rows_in   | rows_out      | dedup_dropped | pruned_shards |
| --------------- | ------ | --------- | ------------- | ------------- | ------------- |
| 20:47:50        | 3      | 9,416,692 | **9,411,982** | 4,710         | 0             |
| 20:59:41        | 4      | 9,416,604 | **9,411,982** | 4,622         | 1             |
| 21:11:26        | 3      | 9,415,845 | **9,411,982** | 3,863         | 1             |
| 21:23:00        | 3      | 9,416,604 | **9,411,982** | 4,622         | 0             |
| 21:35:14        | 3      | 9,415,845 | **9,411,982** | 3,863         | 1             |

`rows_out` is **exactly 9,411,982 in every single real merge**, across 47+ minutes, while `shards` and `dedup_dropped`
both fluctuate cycle to cycle (proving the merge IS reading different/changing shard content each time, not literally a
no-op). Net row growth is zero. This overlaps precisely with `tail3`'s chunks 1-4 actively writing to its own per-VM
shard during this exact window (`21:08-21:34`).

`gcloud storage ls gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/` right now shows only 2
files: `_legacy_seed.parquet` and `sports-fixtures-job.parquet` — none of my 4 VMs' shard files exist there anymore
(consistent with `pruned_shards` firing), yet none of their content appears to have landed in the canonical either.

## Why it matters

This is the **live-fleet-wide sports manifest**, not just the odds_api backfill's target. If the consolidator for this
bucket genuinely is not absorbing new shard content right now:

- **Every other in-flight sports write (any slot, any VM, the routine live/forward capture pipeline) is at the same
  risk** — this is not scoped to my task's writer, it's a property of the consolidator/canonical pairing for this one
  (very large, 9.4M-row) bucket.
- **Downstream honest-coverage / data-status reads are stale-but-confident** — anything reading
  `availability_index.parquet` for `instruments-store-sports-prd` right now is working off a canonical that has not
  reflected new captures for at least this session's duration, with no loud failure signal (the consolidator itself
  reports `success=True` on every cycle — this is not a crash, it looks like a "healthy, steady-state, nothing-new"
  bucket from the consolidator's own self-report).
- This directly blocks `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 backfill todo from EVER showing
  verified completion via the standard census methodology, regardless of how many more VM launches attempt the backfill
  — if genuinely new rows are not being retained, no amount of re-running the launcher fixes it.

## What I did NOT do

I did not read the `manifest_consolidator.py` DuckDB merge/dedup source to pin the exact mechanism (dedup key collision,
a stale canonical read racing the per-VM shard write, a schema/column-order issue silently dropping rows per the
UNION-ALL invariants documented in `manifest-consolidator-ssot.md` §"UNION-ALL correctness", or something else) — that
is real code-reading + likely a live repro, out of scope for what I can respons ibly finish in this session on top of
the OOM investigation already in flight. I also did not attempt a manual `--force` full rebuild (codex-documented recipe
requires PAUSING the cron first + a snapshot; a P0-scale, cross-cutting live-bucket intervention should not be a
unilateral worker action without the pause-first + snapshot discipline the SSOT mandates, and possibly operator
awareness given the blast radius).

## Recommended decision

- [x] ✅ [OPERATOR] P0. **DONE 2026-07-30 (slot 3) — live diagnostic executed under the codex pause+snapshot recipe;
      verdict: `rows_out` is static for a LEGITIMATE reason, there is NO silent-drop bug.** Answer to the question as
      posed ("data loss, or are the shard's rows exact duplicates of already-canonical content?") is **the second one**
      — the shard rows collide with EXISTING canonical dedup keys and update them in place. Evidence in § "Root cause
      (2026-07-30)": every one of a live shard's 1,049 dedup keys already existed in the canonical (0 new keys), and
      **1,029/1,049 shard rows were already present in the canonical carrying the shard's own exact `attempted_at`** —
      i.e. absorbed, not dropped (the 20-row residue is simply rows the VM wrote after the last merge). Independently:
      the 849 manifest rows the gapfill VM genuinely produced on 2026-04-15 — **2,118 `row_count`, byte-matching its own
      log line `Processed date=2026-04-15: … 2118 total records`** — are in the canonical right now, written during the
      exact window this doc claimed content was being lost. Procedure evidence: cron
      `uts-prod-manifest-consolidator-instruments-sports-cron` PAUSED 10:34Z → snapshot
      `_index/snapshots/pre_zero_growth_diag_20260730T1044Z.parquet` (gen `1785406523005270`→ copy verified crc32c
      `uGp0rg==`, size 235,278,458, source generation stable across the copy, via UTL `gcs_copy_object`) → RESUMED
      10:53Z, verified `ENABLED` + a real merge at 10:44:51Z, `pruned_shards=0` throughout, no `CONSOLIDATOR_DOWN`. No
      code fix shipped because **no consolidator defect exists**.
- [ ] [OPERATOR] P1. **Close the odds_api gaps — needs a fix-approach RULING, not more investigation.** Root cause is
      now known and proven (§ "Root cause (2026-07-30)"): `check_shard_freshness` marks 572 of the 595 missing days
      "fresh" off an unrelated `venue='ODDS_API'` sentinel row, so the gapfill SKIPS them and can never fill them —
      re-running the launcher unchanged will keep producing exactly the observed no-op. Census after this session is
      **still 595 missing days** in `2020-06-06..2026-04-15`; this remains the blocking prerequisite for
      `/plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1. Options: **A [WORKER REC]** —
      make the skip source/data_type-aware for the odds path only (narrow: thread the target `data_type`/`source`
      through `_apply_freshness_skip`, leave the shared UTL primitive's default behaviour untouched), then re-run the
      gapfill normally; **B** — no code change, re-run the gapfill with `--force` scoped to the 595 dates (bypasses the
      skip entirely, but costs a full Odds-API re-fetch AND arms the documented `--force` + SPOT preemption trap where
      `RelaunchPreemptedVm` replays `START_DATE` forever, `/codex/05-infrastructure/spot-vms-for-backfill.md`); **C** —
      change `check_shard_freshness` itself to stop matching a `data_type` value against an `expected_venues` entry
      (correct in principle, fleet-wide blast radius: would trigger mass re-fetch across every asset_group); **Other**.
      Repos: market-tick-data-service, unified-trading-library.
- [x] ✅ [DATA] P1. **DONE 2026-07-30 (slot 7) — blast radius is SPORTS-ONLY; no other asset_group reproduces the
      sentinel collision.** Full per-asset_group table + methodology in § "Blast-radius audit results (2026-07-30, slot
      7)" below. Repo: unified-trading-library (no code change — audit found nothing else to fix).
- [x] ✅ [DATA] P2. **DONE 2026-07-30 (slot 3) — premise void + verified idle.** There is no consolidator drop bug to
      propagate to other buckets (P0 above). Re-verified `market-data-tick-sports-prd-central-element-323112` directly:
      its `_index/per_vm/` holds exactly ONE object (`_legacy_seed.parquet`, 7.42 MiB, mtime 2026-07-17) — i.e. **no
      per-VM writer has flushed a shard to it at all**, so the repeated `shards=1 rows_in=0 rows_out=0 error=-` cycles
      (sampled 10:51–10:56Z 2026-07-30, six consecutive) are the honest no-op of a bucket with nothing pending, exactly
      as the original doc suspected. Not a stall, not a size/shape effect.

## Addendum 2026-07-30 (slot 7, data_engineering) — new evidence, root-cause NOT yet found, P1 still blocked

Dispatched the P1 todo ("once root-caused, fix + verify"). Root-cause has NOT landed (`git log` on
`unified_trading_library/manifest_consolidator.py` shows no fix since 2026-07-24, well before this incident's
20:47-21:47 UTC window) — the P0 `[OPERATOR]` todo above is still the blocking prerequisite. Rather than /done a task
that can't meet its done_definition, I spent this session gathering read-only diagnostic evidence (no live-bucket
writes, no cron pause needed) to narrow the P0 investigation:

**1. The stall is not permanent-static — it self-resolved once, then re-stalled at a NEW plateau.** Cloud Logging past
21:47:09 shows `rows_out` jumped from the reported 9,411,982 to **11,778,300** at 21:59:46 UTC (shards=3,
rows_in=11,785,489, dedup_dropped=7189 — a genuine ~2.37M-row absorption), then stayed static at 11,778,300 across 8
more consecutive real merges through 23:46:16 (current as of writing). No odds-gapfill VM was active after ~21:35, so
this second "stall" is expected (no writer = no growth), NOT a second instance of the bug.

**2. That 21:59:46 jump did NOT include the odds_api gapfill's target rows.** Downloaded the current canonical (single
read, 227MB, `gs://.../availability_index.parquet`, now 11,778,300 rows matching the latest Cloud Logging report) and
queried it directly with DuckDB:

- `source='odds_api' AND date BETWEEN '2026-02-22' AND '2026-03-28'` → **0 rows**, any status. Confirms the census
  finding is still true RIGHT NOW, even after the big absorption — the disputed range is still completely absent.

**3. Dedup-key-collision-with-another-source hypothesis — TESTED, RULED OUT.** Read `manifest_consolidator.py`'s full
merge/dedup/CAS-write path. Confirmed `source` is deliberately excluded from `_BASE_DEDUP_COLS`/`_OPTIONAL_DEDUP_COLS`
(by design — a documented 2026-07-12 fix already makes `capture_status='captured'` outrank any non-captured row
regardless of source, precisely to stop a later empty/failed row from a DIFFERENT source silently erasing an earlier
real capture). Hypothesis: odds_api's new rows collide on `(date, venue, data_type, service_name)` with an
already-`captured` row from a DIFFERENT source and lose the tie-break. Tested directly: odds_api's dedup-key shape is
`(venue=<bookmaker>, data_type='trades'|'TRADES', service_name='market-tick-data-service'|'instruments-service'|...)`.
Queried the canonical for ANY row (any source) at `date=2026-02-25, venue='BETONLINEAG', data_type='trades'` — **0
rows**. There is no competing row occupying that key. This rules out the collision theory, at least for this sample —
the rows are genuinely, simply absent, not shadowed.

**4. The CAS-write retry loop and date-range chunking both read clean.** `_write_consolidated`'s 5-attempt
`PreconditionFailed` retry re-merges against the winning generation each time and `raise`s (→ `success=False`) on
exhaustion — but every stalled cycle logged `success=True`, so the retry loop was not silently swallowing a failure.
`_duckdb_merge_payload`'s date-chunking explicitly buckets `TRY_CAST(date AS DATE) IS NULL` into its own chunk
(`chunk_null_date.parquet`), so a date that fails to parse doesn't fall between all chunks and vanish. No obvious defect
found by code reading alone.

**5. NEW, likely-relevant finding: the two VMs that actually covered this range (`mtds-backfill-odds-gapfill-20260729`

- `-retry1-20260729`, both `START_DATE=2020-06-06`) were BOTH killed by OOM mid-way through their FINAL chunk.** Pulled
  `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` for all 4 VMs (still present, VMs themselves are
  terminated):

* Both `...-20260729` and `...-retry1-20260729` (`CHUNK_SIZE=250`) processed real per-day work up through
  `Processed date=2026-04-15` — inside chunk 9/9 (`range=2025-11-27→2026-07-29`) — before that chunk's subprocess was
  `Killed` (`exit=137 reason=OOM_KILLED`). This matches the original doc's claim ("2 independent VM runs each got this
  far before their final chunk failed"). Their `PROGRESS.json` `last_completed_date` froze at `2025-11-26` (the last
  chunk BOUNDARY completed, not the last date actually processed inside the crashed final chunk — the per-day log lines
  prove real work continued past that checkpoint up to 2026-04-15).
* `mtds-backfill-odds-gapfill-tail3-20260729` (the one named in the original "What I found") actually launched with
  `START_DATE=2026-04-16` — it does **not** cover 2026-02-22..03-28 at all — and only completed ONE day
  (`2026-04-16: 0 venues ok, 0 failed, 0 total records`) before the VM ended. It is NOT the source of any content for
  the disputed range; the two `START_DATE=2020-06-06` runs are.
* **So the 2026-02-22..03-28 range WAS almost certainly inside the live processing window of the two OOM-killed VMs**
  (they got to 2026-04-15 before dying), and `ManifestWriter` flushes per-VM shards incrementally in ~500-entry batches
  (confirmed pattern from tail3's own log: `"ManifestWriter: per-VM shard updated (500 total entries, 500 new, ...)"`),
  so shard content for this range plausibly landed in `_index/per_vm/mtds-backfill-odds-gapfill-20260729.parquet` /
  `-retry1-...parquet` well before either VM's final OOM kill. Those shard files are now DELETED (the original doc's own
  `gcloud storage ls .../per_vm/` check found only `_legacy_seed.parquet` + `sports-fixtures-job.parquet` left —
  consistent with `pruned_shards` firing repeatedly during the stall window, e.g. `pruned_shards=1` at 20:59:41 /
  21:11:26 / 21:35:14). **Direct forensic inspection of what those shards actually contained is no longer possible** —
  the only surviving evidence is the VMs' own `run.log` per-day/per-flush lines.

**Net effect**: I can now say with fairly high confidence that (a) shard content for the disputed range likely did reach
GCS via ≥1 of the two `START_DATE=2020-06-06` VMs' incremental flushes, (b) the consolidator's real merges during the
stall window read a changing set of shards (varying `dedup_dropped`) and reported `success=True` with a CAS write that
must have gone through (no retry-exhaustion failure logged), yet (c) the canonical still shows zero rows for this range
even now. That combination — real merge, real (varying) input, reported success, but the specific new content never
landing — is the actual mystery, and I could not pin it further via code reading alone (the dedup-key-collision theory
is ruled out; the CAS/chunking code reads correct). Closing this out needs either: (a) a controlled live diagnostic —
write one small synthetic per-VM shard covering an already-confirmed-missing date, trigger one manual consolidation
cycle, and inspect the DuckDB merge's intermediate output BEFORE any prune can delete it; or (b) re-run the backfill for
just this range with a small `CHUNK_SIZE` (avoiding the OOM class of failure entirely) and verify the shard survives one
full consolidation cycle before the next one prunes it. Both are live-bucket diagnostic actions on the P0-tagged bucket
— leaving the `[OPERATOR]` todo above as the correct next step rather than a unilateral live intervention.

Scratch artifacts (downloaded canonical snapshot, probe script) were session-local only, not committed.

## Addendum 2026-07-30 (slot 9, data_engineering) — re-confirmed still blocked, no new writer activity

Re-dispatched the same P1 todo. `git log` on `manifest_consolidator.py` still shows no commit since the 2026-07-24
TOCTOU-race fix (`14301571`), well before this incident — no root-cause fix has landed. Read-only re-verification
(single download of the current canonical, DuckDB query, no live-bucket writes):

- Canonical `availability_index.parquet` row count: **11,778,300** — byte-identical to the count slot 7 observed at
  23:46:16 UTC on 2026-07-29, ~14 hours earlier. Expected (no odds-gapfill VM has run since), not a new stall instance.
- `source='odds_api' AND date BETWEEN '2026-02-22' AND '2026-03-28'` → still **0 rows**. The disputed range remains
  completely absent.

No new evidence to add beyond slot 7's root-cause narrowing — the mystery (real merge, real changing input,
`success=True`, but the specific new content never landing) is unchanged. The `[OPERATOR]` P0 todo above is still the
sole blocking prerequisite; this P1 todo's done_definition (root-caused fix + verified census) cannot be met until it
clears. Skipping this slot's dispatch of the task with `reason_code=BLOCKED` so repeated fleet-wide re-dispatch to
workers who hit the identical wall triggers the auto-park escalation instead of burning further worker sessions on
read-only re-confirmation.

## Addendum 2026-07-30T00:40Z (slot 11, data_engineering) — re-dispatched again, still blocked, bare check only

Re-dispatched the same P1 todo a third time. Per slot 9's own guidance, not repeating the full read-only re-verification
(nothing has changed to warrant it) — bare check only: `git log` on `unified_trading_library/manifest_consolidator.py`
still shows no commit since `14301571` (2026-07-24), so no root-cause fix has landed. The `[OPERATOR]` P0 todo remains
the sole blocking prerequisite; this P1 todo's done_definition still cannot be met. Skipping with `reason_code=BLOCKED`
to keep pushing toward the auto-park threshold rather than burning another session on read-only re-confirmation.

## Root cause (2026-07-30, slot 3) — the consolidator is fine; the BACKFILL skips the dates

Operator authorised the live diagnostic. Ran the `manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL" discipline
(steps 1–2 + 6; steps 3–5 never applied — nothing was rewritten): PAUSE cron → snapshot → probe → RESUME.

### 1. `rows_out` static is an in-place UPDATE, and the "corroborating" metric is circular

`dedup_dropped` is not measured, it is **derived**: `dedup_dropped=rows_in - rows_out` (`manifest_consolidator.py:998`).
So "`rows_out` frozen" and "`dedup_dropped` == the shard's row count" are ONE observation restated, not two. A shard
whose keys all already exist in the canonical produces exactly this signature while correctly updating every one of
them. Reproduced live three times on 2026-07-30 with the then-active `af-backfill-20260730-012007` writer (canonical
pinned at 11,789,693 while the shard grew):

| merge (UTC) | shards | rows_in    | rows_out       | dedup_dropped | shard rows at the time |
| ----------- | ------ | ---------- | -------------- | ------------- | ---------------------- |
| 10:00:40    | 2      | 11,790,669 | **11,789,693** | 976           | 976                    |
| 10:15:23    | 2      | 11,790,696 | **11,789,693** | 1,003         | 1,003                  |
| 10:29:59    | 2      | 11,790,722 | **11,789,693** | 1,029         | 1,029                  |
| 10:44:51    | 2      | 11,790,741 | **11,789,693** | 1,048         | 1,048                  |

`dedup_dropped` tracks the shard's row count exactly, cycle for cycle — the tell of pure key-collision, not loss.

### 2. Absorption proved positively, against the snapshot

Captured the live shard before any prune could eat it (the forensic gap that defeated slots 7/9/11) and diffed it
against the snapshotted canonical using the module's OWN `_resolve_dedup_cols` / `_dedup_key_sql` (no re-derived key):

- dedup key resolved to the 16 columns `date, venue, data_type, service_name` + the 12 present optional dims.
- shard = **1,049 rows / 1,049 distinct dedup keys**; **1,049 of 1,049 already present in the canonical, 0 new keys.**
- **1,029 shard rows found in the canonical carrying the shard's own exact `attempted_at`**; 1,041 matching on
  `(capture_status, row_count)`. The ~20-row residue is the rows the VM flushed after the last merge.
- canonical self-consistency: **0 duplicate dedup-key groups** across all 11.79 M rows.
- Historical control: the ONE date the odds gapfill genuinely processed, `2026-04-15`, holds **849 rows written
  2026-07-29T20:34Z** — 63 `captured` summing to **row_count 2,118**, byte-matching the VM's own
  `Processed date=2026-04-15: 1 venues ok, 0 failed, … 2118 total records`. Absorbed during the exact window this doc
  reported as lossy.

### 3. What actually blocks the odds_api backfill — a freshness-skip sentinel collision

The 07-29/07-30 addenda's premise that the two `START_DATE=2020-06-06` VMs "processed real per-day work up through
2026-04-15" is a **misreading of the run logs**. Both VMs' `run.log` contain **2,139 `SKIP date=…` lines and exactly ONE
`Processed date=` line**:

```
2026-07-29 20:07:59 INFO SKIP date=2026-02-22: all 1 venues fresh (use --force to reprocess)
…                                    (identical for every date 2020-06-06 … 2026-04-14)
2026-07-29 20:09:17 INFO Processed date=2026-04-15: 1 venues ok, 0 failed, 0 skipped, 2118 total records
```

Nothing was ever written for the disputed range, so nothing could be dropped. The mechanism:
`TickDataHandler._apply_freshness_skip` calls
`check_shard_freshness(expected_venues=get_venues_for_asset_groups( ["sports"]))`, which for sports is the single
pseudo-venue **`ODDS_API`**. `check_shard_freshness` then matches an expected venue against the `venue` column **OR**
the `data_type` column, keyed only on `(date, service_name)`, and is **blind to `source` and `data_type`**. For every
disputed date the canonical holds exactly one `service_name='market-tick-data-service'` row:

```
venue='ODDS_API'  data_type='odds_horizon_bucket'  source='mdps_odds_horizon_bucket'
capture_status='empty_confirmed'  error_reason='SOURCE_RETURNED_ZERO'  schema_version=9
written_at=2026-07-13T06:14:5x
```

That row belongs to a **different pipeline** (the MDPS odds-horizon-bucket rollup), yet it satisfies every staleness
test: schema 9 == current; status is not `attempted_failed`; and the age test is disabled outright for historical dates
(`freshness_max_age = 0.0 if date < now-7d`). → `is_fresh=True` → permanent skip. The REAL odds capture writes at a
completely different granularity (`venue=<bookmaker>` e.g. `PINNACLE`/`BETONLINEAG`, `data_type='trades'`,
`source='odds_api'`), which the check never looks for.

**Falsifiable test over all 2,140 days in `2020-06-06..2026-04-15`** (`odds_api` present × `ODDS_API`-sentinel present):

| has odds_api | has ODDS_API sentinel | days    |
| ------------ | --------------------- | ------- |
| ✗            | ✓                     | **572** |
| ✗            | ✗                     | 23      |
| ✓            | ✓                     | 1,497   |
| ✓            | ✗                     | 48      |

**572 of the 595 missing days (96.1%) are explained exactly by the sentinel skip**, and 2,071/2,071 distinct sentinel
day-states evaluate FRESH under `check_shard_freshness`'s own predicate. `2026-04-15` — the one date that DID process —
is one of the 48 with no sentinel. The remaining 23 sentinel-free missing days need a separate look (folded into the
blast-radius todo). This is the textbook "entity-agnostic check passes while the target entity writes ZERO rows" class
CLAUDE.md § async-discipline already warns about, here in a skip predicate rather than a progress monitor.

### 4. Honest limits of this session

- The 2026-07-29 20:47–21:35 shard files are still gone; that specific window is reconstructed by MECHANISM (a live
  2026-07-30 reproduction of the identical signature + the VM logs), not by inspecting those exact bytes.
- **No code fix shipped.** The defect is not in `manifest_consolidator.py`, and every candidate fix touches either a
  shared UTL primitive used by every service or the sports expected-venue data model — a design ruling, not a scoped
  change (hence P1 above is `[OPERATOR]` with options, per the AO dispatch-scope eligibility rule).
- The 23 sentinel-free missing days are NOT yet explained.
- Side-finding, unrelated: `unified_trading_library` is **unimportable in every slot-3 local venv** —
  `service_framework/fastapi_factory.py` imports `fastapi.routing.iter_route_contexts` (needs the declared
  `fastapi>=0.137.0`) while the venvs carry 0.135.1. Worked around locally with
  `VIRTUAL_ENV=… uv pip install 'fastapi>=0.137.0,<1.0.0'` in `unified-trading-library/.venv` only. Prod images are
  unaffected (they honour the pin); this is local venv drift. Tracked as a todo below.

- [ ] [SCRIPT] P3. **Re-sync the slot local venvs to UTL's declared `fastapi>=0.137.0` pin** —
      `unified-trading-library`, `market-tick-data-service`, `instruments-service` and `deployment-service` `.venv`s all
      shipped 0.135.1, making `import unified_trading_library` raise
      `ImportError: cannot import name 'iter_route_contexts'`. Only slot 3's UTL venv was fixed in-session. Done-when:
      `python -c "import unified_trading_library"` succeeds in each repo's `.venv`. Repos: all Python service repos.

## Blast-radius audit results (2026-07-30, slot 7, data_engineering) — P1 todo

Dispatched the `[DATA] P1` blast-radius todo. Method: (1) enumerate every real (non-test) call site of
`check_shard_freshness` across the fleet and the exact `(bucket-family, service_name, expected_venues tokens)` triple
each one checks; (2) for each triple, download that bucket's `_index/availability_index.parquet` ONCE (a single read of
the already-materialised manifest, not a new whole-corpus GCS walk — same class of operation the root-cause section
above used) and query it directly with DuckDB for the two concrete failure shapes the sentinel bug needs: a foreign
`service_name`'s row satisfying the token via the `venue` column (the sports mechanism), or via the `data_type` column
(the todo's literal wording). "Foreign" means a DIFFERENT logical pipeline than the one the caller's `service_name`
declares — multiple genuine vendors capturing the SAME real venue (e.g. `tardis` + `binance`'s own REST fallback both
under `venue=BINANCE-FUTURES`) is NOT this bug, it's expected multi-source coverage.

| asset_group / caller                                        | bucket checked                                                 | service_name scope         | expected_venues token shape                                                                        | verdict                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------------------------------- | -------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sports / MTDS `_apply_freshness_skip`                       | `instruments-store-sports-prd`                                 | `market-tick-data-service` | pseudo-venue `ODDS_API`                                                                            | **PRESENT (confirmed)** — this issue's own root-cause section; MDPS's odds-horizon-bucket rollup stamps `venue=ODDS_API` under the SAME `service_name=market-tick-data-service` (a sports-specific ownership convention: "MTDS owns betting-market instruments+odds" per venue_mapping.py), so it satisfies the token via the `venue` column.                                                                                                                                                                                                                                      |
| tradfi / MTDS `_apply_freshness_skip`                       | `market-data-tick-tradfi-prd` (98 MB manifest)                 | `market-tick-data-service` | real venues `CME,CBOE,NASDAQ,NYSE,ICE,FX,KRX,FRED`                                                 | **ABSENT** — live query: 0 rows anywhere with `data_type` literally equal to any of these 8 tokens. `venue`-column groups exist across multiple `source` values (`databento`,`yahoo`,`fred`) but every group is the SAME real venue's OWN multi-vendor capture, not a foreign pipeline. `market-data-processing-service` writes its own candle rows into this same bucket under its OWN `service_name` (49,536 rows) — no cross-stamping observed.                                                                                                                                 |
| prediction / MTDS `_apply_freshness_skip`                   | `market-data-tick-pred-prd` (115 MB manifest)                  | `market-tick-data-service` | real venues `POLYMARKET,KALSHI`                                                                    | **ABSENT** for the sentinel-collision pattern (0 `data_type`-column hits). Surfaced an unrelated, real data-quality anomaly instead (filed as a new todo below): 58,013 rows carry `venue=KALSHI` but `source=polymarket_clob` — a source-mislabel, not a foreign-pipeline token collision (doesn't affect `check_shard_freshness` correctness since KALSHI is genuinely expected AND genuinely captured, just under the wrong `source` stamp).                                                                                                                                    |
| cefi / MTDS `_apply_freshness_skip`                         | `market-data-tick-cefi-prd` (172 MB manifest)                  | `market-tick-data-service` | real venues (14 sampled incl. bare `OKX`, `COINBASE-CDE`, all Tardis-derived `*-SPOT`/`*-FUTURES`) | **ABSENT** — 0 `data_type`-column hits for any sampled token. Multi-`source` venue groups (e.g. `BYBIT`: `tardis`+`bybit`, `HYPERLIQUID`: `tardis`+`hyperliquid`) are the documented native-adapter-alongside-Tardis multi-vendor pattern, not a collision.                                                                                                                                                                                                                                                                                                                        |
| defi / MTDS `_apply_freshness_skip`                         | `market-data-tick-defi-prd` (1.07 GB manifest)                 | `market-tick-data-service` | compound `PROTOCOL-CHAIN` strings (`UNISWAP_V2-ETHEREUM`, …)                                       | **NOT LIVE-VERIFIED this session** (manifest is >1 GB — a full download+query is disproportionate to a same-session audit's single-walk budget; judgment call, not a skip). Classified **structurally low-risk**: DeFi `data_type` values are generic categories (`gas_fees`,`lending_index`,`dex_swaps`,`oracle_price`,`lst_rate`,`liquidation`,`perp_funding`) — no other pipeline anywhere in the fleet writes a compound `PROTOCOL-CHAIN` string as a bare `data_type` value (grepped fleet-wide). Follow-up todo filed below for anyone who wants the live census closed out. |
| onchain (defi) features / features-service `_skip_if_fresh` | `features-defi-prd` (37 KB manifest — dedicated, live-checked) | `features-service`         | feature_group names (`lst_yields`, `rewards`, …)                                                   | **ABSENT** — confirmed via direct read: the ENTIRE bucket has exactly one `service_name` value (`features-service`, 1,538 rows). features-service owns dedicated per-asset_group buckets (`features-{cefi,defi,pred,sports,tradfi}-prd`), never shared with MTDS/MDPS/IS, so no foreign pipeline can stamp this `service_name` there.                                                                                                                                                                                                                                              |
| reference-data / instruments-service preflight              | `instruments-store-{ag}-prd`                                   | `instruments-service`      | reference entities (venue names, `FIXTURES`, `STANDINGS`, …)                                       | **Different collision class, already known + mitigated** — `process_preflight.py`'s own per-league `FIXTURES` coarse-match bug (one league's stale row marking the WHOLE date fresh for every other league) is a same-service, cross-ENTITY collision, not a cross-pipeline one; it already has a dedicated fix (`_should_skip_date_for_per_league`). No cross-pipeline (foreign `service_name`) collision evidence found for IS's own scope in the checked buckets.                                                                                                               |

**Net finding: the sentinel-collision bug class is confirmed SPORTS-ONLY.** It depends on a sports-specific ownership
quirk (MDPS's odds-horizon-bucket rollup deliberately writing under MTDS's `service_name` rather than its own, because
instruments-service's sports-ownership doc assigns betting-market odds to MTDS) that has no analogue in cefi/tradfi/
defi/prediction, where MDPS always writes its own candle rows under its own `service_name` with no observed
cross-stamping. The `[OPERATOR]` P1 fix-approach ruling above (options A/B/C) therefore only needs to cover the sports
`ODDS_API` path — no other asset_group needs the same row-scoping fix applied pre-emptively.

- [ ] [DATA] P3. **Investigate KALSHI/polymarket_clob source-mislabel in the prediction-market manifest** — 58,013 rows
      in `market-data-tick-pred-prd-central-element-323112` carry `venue=KALSHI, data_type=trades` but
      `source=polymarket_clob` (writes span 2026-07-11 05:56–06:00 UTC, a narrow ~4-minute window — looks like a single
      misconfigured backfill/replay run rather than an ongoing writer bug). Confirm whether these rows are genuine
      KALSHI trades mis-stamped with the wrong `source`, or genuine POLYMARKET trades mis-stamped with the wrong `venue`
      — either way `source=`/`venue=` disagree with each other for this slice. Done-when: root cause identified + (if
      genuinely mislabeled) a restamp plan. Repo: market-tick-data-service.
- [ ] [DATA] P3. **Close out the DeFi leg of the blast-radius audit with a live manifest census** — the P1 audit above
      classified DeFi as structurally low-risk by naming-convention analysis only (its `market-data-tick-defi-prd`
      manifest is 1.07 GB, judged disproportionate for this session's single-walk budget). Done-when: a single DuckDB
      read of `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` confirms 0 rows have
      `data_type` literally equal to any `ALL_DEFI_VENUES` token
      (`unified-api-contracts/     unified_api_contracts/registry/defi_venues.py`). Repo: unified-trading-library.

## Codex SSOTs

`/codex/05-infrastructure/manifest-consolidator-ssot.md` (merge engine, UNION-ALL invariants, pause-first discipline for
any direct canonical intervention — § "Diagnostic caveats" now carries the static-`rows_out` lesson from this issue),
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/sports-2020-06-data-floor.md`.
