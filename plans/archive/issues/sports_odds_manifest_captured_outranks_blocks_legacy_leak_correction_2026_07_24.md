---
doc_type: issue
title:
  reprocess_sports_odds.py --force cannot correct a false `captured` manifest row — the reader/consolidator
  captured-outranks-recency tie-break permanently masks the honest attempted_failed/empty_confirmed verdict
summary: |
  sports_closeout_batch1_ao_ready_2026_07_24.md todo 3 ([DATA] P0) asked to run
  `reprocess_sports_odds.py --force` for 2025-12-18/24/31 so the manifest's stale `captured` coarse row (a
  legacy-path capture leak) flips to an honest verdict. The real script DOES correctly reclassify all 3 dates
  as `attempted_failed` (ADAPTER_RETURNED_EMPTY_OUTPUT — raw odds exist but land in the T-12h/T-24h dead-zone,
  §B2) and DOES write that row via `ManifestWriter.record_failed()`. But the write never becomes visible at read
  time: `unified_trading_library.manifest_writer._read_index._merge_shard_frames`'s captured-outranks-recency
  tie-break (shipped `unified-trading-library@17ee38de`, 2026-07-14,
  `sports_index_recency_masked_captured_atoms_2026_07_13.md`) ranks ANY `capture_status='captured'` row above
  ANY non-captured row for the same dedup key, unconditionally, regardless of which one is newer. Since all 3
  dates already carry a `captured` row (dated 2026-07-14T04:1x, both at the coarse per-day key and at 9-11
  per-league T-0 shard keys), the new `attempted_failed` row loses every time. Measured directly: a fast-path
  `lookup()` read taken seconds after the 2025-12-31 write showed `attempted_failed` (fresh); a second read ~15
  minutes later (after the background consolidator's next cycle) showed `captured` again — confirming the flip
  reverts, it isn't just absent. `reprocess_sports_odds.py --force` is therefore NOT the "not a hand-edit"
  compliant mechanism the todo assumed; the codebase's own established precedent for this exact class of
  correction (`instruments-service/scripts/flip_phantom_to_attempted_failed.py`) is a bespoke, reviewed,
  backup-then-write script that edits `_index/availability_index.parquet` directly — a materially different,
  higher-privilege action than "run the real script," and out of this todo's stated scope without a decision.
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-data-processing-service, instruments-service]
scope: [engineer]
tags: [manifest, honest-coverage, sports, dedup, captured-outranks, recency-masking]
related:
  - /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
  - /plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md
  - /plans/archive/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md
created: "2026-07-24"
parent_epic: sports_master
priority: P1
source: sports_closeout_batch1_ao_ready-003 execution (slot 5, 2026-07-24)
assigned_vm: planning
resolved_by: "slot 4, 2026-07-24 — codex §519 paused-consolidator CAS recipe, applied verbatim, holds durably"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **✅ ARCHIVED 2026-07-25** — `status: resolved`, fix applied verbatim and confirmed durable, 0 open todos, unlocked.
> Moved to `plans/archive/issues/` per the issue-doc-lifecycle archival ritual.

# reprocess_sports_odds.py --force cannot correct a false `captured` row (captured-outranks tie-break)

## What I found

Ran `reprocess_sports_odds.py --start-date <D> --end-date <D> --force` for real (no `--dry-run`) against PROD for
2025-12-18, 2025-12-24, and 2025-12-31 (`market-data-tick-sports-prd-central-element-323112` /
`instruments-store-sports-prd-central-element-323112`). All 3 dates read raw odds successfully (26.7k-28.8k rows,
654-702 parquet files) but the `SportsBucketAssignmentAdapter` returned an empty bucketed frame for all 3 — every
observation's `bm_minutes_to_kickoff` falls in the T-12h/T-24h 615-minute structural dead-zone the parent audit's §B2
already root-caused. The script correctly classified this as `ADAPTER_RETURNED_EMPTY_OUTPUT` →
`record_failed(capture_status="attempted_failed")` for all 3 (not the `empty_confirmed` the todo predicted for
2025-12-24 — see "Secondary finding" below) and each run logged a successful manifest write
(`ManifestWriter: updated availability index (... 1 new)`).

Verifying via `ManifestWriter.lookup()` (the exact API `reprocess_sports_odds.py`'s own pre-flight uses) immediately
after each write showed:

- 2025-12-18 → still `captured` (2026-07-14T04:17:31, unchanged)
- 2025-12-24 → still `captured` (2026-07-14T04:17:53, unchanged)
- 2025-12-31 → `attempted_failed` (2026-07-24T19:26:31, fresh) — briefly

A raw (un-deduped) read of the merged index for all 3 dates found the OLD `captured` rows still present at BOTH the
coarse per-day key (`league_id`/`timeframe` null, `row_count` 51/63/62) AND 9-11 per-league `T-0` shard keys (e.g.
`soccer_japan_j_league`, `soccer_usa_mls`, ...), all dated 2026-07-14T04:1x:xx — no trace of my new `attempted_failed`
rows appeared in that read at all.

Re-running the `lookup()` check ~15 minutes later showed **2025-12-31 had reverted to `captured`** too — all 3 dates now
read identically to their pre-run state. This rules out "just hasn't propagated yet": the fresh row existed, was read
once, and was then masked/lost, matching `_merge_shard_frames`'s documented behavior exactly ("within one dedup-key
group, `capture_status='captured'` always beats any non-captured row ... regardless of recency" —
`unified_trading_library/manifest_writer/_read_index.py:1184-1191`, shipped `unified-trading-library@17ee38de` per
`sports_index_recency_masked_captured_atoms_2026_07_13.md`).

## Why it matters

This todo's premise — "run the real script (not a hand-edit) so the stale `captured` state flips to the honest verdict"
— cannot succeed through `reprocess_sports_odds.py --force` alone, for ANY atom that already carries a `captured` row,
because the manifest's own reader-side (and, per the referenced issue doc, consolidator-side) dedup logic is DESIGNED to
make `captured` win unconditionally. That protection exists for a good reason (prevent a stray later empty/failure stamp
from masking a real capture — the 2026-07-13 oscillation), but it has no way to distinguish "this later attempt is a
deliberate correction of a KNOWN-false capture" from "this later attempt is routine noise." The effect: the legacy-path
capture leak this todo set out to fix is **structurally un-fixable** via the sanctioned "run the real script" path — the
same blocker would hit ANY future attempt to correct a false `captured` atom anywhere in the sports (or likely any)
manifest, not just these 3 dates.

The codebase already has a precedent for this exact correction direction —
`instruments-service/scripts/flip_phantom_to_attempted_failed.py` (backup-then-write directly against
`_index/availability_index.parquet`, used to re-flip 100,431 phantom-captured rows to `attempted_failed`) — but
building/running an equivalent one-off script is a materially different, higher-privilege action than what this todo
described ("not a hand-edit"), and touches a shared, deliberately-guarded mechanism, so it needs sign-off before a
data_engineering worker does it under this todo's scope.

## Secondary finding (lower priority)

The todo's predicted per-date verdict split (`attempted_failed` for 18/31, `empty_confirmed` for 24) does not match what
the real script actually determines: **all 3 dates classify as `attempted_failed`** (`ADAPTER_RETURNED_EMPTY_OUTPUT`),
including 2025-12-24. The parent audit's own §B2 root-cause called 2025-12-24 "genuine honest-absence (0 in-window)" — a
semantic judgment that the raw ticks exist but zero land in any Tier-1 horizon window — but `reprocess_date()`'s
honest-absence classification only awards `empty_confirmed` when `_read_raw_odds` returns a genuinely-empty DataFrame
(zero raw bytes anywhere for the date); a non-empty raw frame that the adapter filters to zero rows is always
`attempted_failed`/`ADAPTER_RETURNED_EMPTY_OUTPUT`, by design, per the 2026-06-22 honest-absence hardening rule (a real
fetch found data, so a clean-empty proof would be false). The code doesn't currently distinguish "the dead-zone ate
every observation" from any other adapter-empty cause. This overlaps the parent plan's own still-open Track O
`[DIAG] P2` todo ("corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h/T-24h
dead-zone ... consider adding a T-18h horizon") — no new todo needed here, just noting the discrepancy so whoever picks
up that DIAG item has this data point.

## Recommended decision

- **Option A (recommended)**: build a scoped, reviewed, backup-then-write correction script mirroring
  `flip_phantom_to_attempted_failed.py`'s pattern — read `_index/availability_index.parquet` from
  `instruments-store-sports-prd-{project}`, snapshot it, re-stamp the coarse + per-league/T-0 rows for these 3 dates
  (identified above) from `captured` to `attempted_failed`, write back. Small, targeted, precedented; single
  data_engineering todo.
- **Option B**: leave the manifest as-is for now (my correct `attempted_failed` writes remain in the raw per-VM shard
  data as evidence, even though currently masked at read time); file a new backlog todo for Option A's script rather
  than building it under this todo; this todo stays not-fully-completable as literally scoped.
- **Option C**: revisit `_merge_shard_frames`'s tie-break itself to support a marked, deliberate override (e.g. a
  `correction=True` flag that beats `captured` for a specific, human-reviewed re-stamp) — a bigger, cross-cutting design
  change affecting every asset_group's manifest, not sports-specific; too large for this todo, flagged for awareness
  only.

## Todos

- [x] [DATA] P1. Implement Option A (or whichever the operator/main picks): a one-off backup-then-write script
      re-stamping the 2025-12-18/24/31 coarse + per-league T-0 `captured` rows in
      `instruments-store-sports-prd-{project}/_index/availability_index.parquet` to `attempted_failed`, mirroring
      `instruments-service/scripts/flip_phantom_to_attempted_failed.py`'s snapshot-then-write pattern. Verify via
      `ManifestWriter.lookup()` immediately AND after >=2 consolidator cycles (per the 2026-07-14 adjudication's own
      verification recipe) so a transient read isn't mistaken for a durable fix. Repo: instruments-service or
      unified-trading-library (whichever owns the correction-script home per
      `/codex/06-coding-standards/script-homes.md`). — instruments-service@139d10b5 (script shipped, QG-clean). Live
      PROD run applied 2026-07-24 ~20:27 UTC (30 rows flipped, backup at
      `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.20260724-202648.bak.parquet`),
      immediate `ManifestWriter.lookup()` verified `attempted_failed` for all 3 dates — **but the durability check
      after >=2 consolidator cycles (5 min later) found ALL 31 rows reverted back to `captured` with the ORIGINAL
      2026-07-14 `attempted_at`/blank `error_reason`** (see "Critical new finding" below). The fix as scoped does NOT
      survive — same failure mode as the original `reprocess_sports_odds.py --force` attempt, now proven to also defeat
      a direct canonical hand-edit. Checked off because the SCRIPT (the todo's literal deliverable) shipped and was
      proven correctly targeted (see the scoping fix below) — but the underlying manifest is NOT yet durably corrected;
      see the new todo below for the follow-up.
- [x] [DATA] P0. Land Option A2/B2/C2 (whichever the operator/main picks, see "Critical new finding" below) so the
      already-shipped `flip_sports_odds_captured_leak_to_attempted_failed.py --apply` survives >=2 consolidator cycles
      without reverting. Re-run `--dry-run` first to confirm scope is still exactly the 31 target rows (no drift). Repo:
      instruments-service (script) + deployment-service or infra (if Option A2's cron-pause is picked). — RESOLVED,
      Option A2, instruments-service@d5e80b32 (script hardened to the codex §519 paused-consolidator CAS recipe).
      Sequence: (1) paused `uts-prod-manifest-consolidator-instruments-sports-cron` via Cloud Scheduler API, (2) found +
      waited out 2 ALREADY-IN-FLIGHT overlapping executions (one ran 7m47s — matches the documented sports slow-cycle
      class) since pausing the scheduler doesn't kill a running execution, (3) re-ran `--dry-run` (still exactly 31
      rows, confirming no drift), (4) `--apply --i-have-paused-the-consolidator-cron`: snapshotted generation to
      `_index/snapshots/pre_sports_odds_captured_leak_20260724-205611.parquet`, Arrow-schema-preserving edit, CAS write
      (generation 1784926487218742 -> 1784926602209245) — succeeded first try, (5) `consolidate(bucket, force=True)` to
      re-stamp the `consolidator_content_write_at`/`consolidator_run_at` markers the CAS write can't carry — first
      attempt hit a local DuckDB OOM (this sandbox's `/tmp` is a 2GB tmpfs; unrelated to PROD, the CAS write itself
      already lands before the merge step), retried with `TMPDIR` on the 99GB-free root disk — succeeded (5,526,420 rows
      in = 5,526,420 rows out, both markers confirmed stamped via direct GCS metadata REST read), (6) resumed the cron
      (confirmed ENABLED), (7) waited 8 min (>=2 real cycles — generation advanced from normal cron activity in that
      window), **final check: all 31 rows still `attempted_failed`, both via `ManifestWriter.lookup()` and a direct
      raw-index read.** DURABLE. Root cause was a genuine read-modify-write race with the live consolidator (not a
      mystery third source) — main's parallel diagnostic framing (see
      `sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`) is answered: the codex §519
      paused-CAS recipe, applied verbatim, HOLDS.

## Critical new finding (2026-07-24, post-Option-A-authorization)

**The captured-outranks-recency tie-break is not the only thing standing between a correction write and durability —
there is also a live read-modify-write RACE between any one-off direct-editor of `_index/availability_index.parquet` and
the always-running `*/1 * * * *` consolidator cron (`uts-prod-manifest-consolidator-instruments-sports`).**

Evidence, in order:

1. A dry-run of the Option A script (venue=ODDS_API, data_type=odds_horizon_bucket, date in the 3 target dates,
   capture_status='captured') matched **87 rows**, not the ~31 expected. Investigation found 56 of them were written by
   **`market-tick-data-service`** (2026-07-13T06:1x, uppercase `league_id`, blank `timeframe`, `instrument_count=1`) and
   **`instruments-service`** (2026-07-13T23:4x-23:5x, uppercase `league_id`, literal-string `timeframe='None'`,
   `instrument_count=1`) — a day EARLIER, for an unrelated purpose, sharing the same
   `(venue, data_type, date, league_id)` key space by coincidence. The script was narrowed to also filter
   `service_name == "market-data-processing-service"` (matching `reprocess_sports_odds.py`'s own `_SERVICE_NAME`), which
   correctly narrowed the match to exactly 31 rows, all dated 2026-07-14T04:1x:xx. **This scoping bug would have
   silently corrupted 56 unrelated, presumably-correct manifest rows belonging to two other services had it shipped as
   originally drafted — flagging in case the same key-space collision affects any other
   venue=ODDS_API/data_type=odds_horizon_bucket tooling.**
2. Applying the (correctly-scoped) fix at ~20:27:18 UTC flipped 30 rows (the 31st, the 2025-12-18 coarse row, was
   already independently `attempted_failed` at read time — apparently a concurrent process, possibly another agent, had
   already re-run `reprocess_sports_odds.py --force` for that date at 20:25:31 UTC). Immediate `ManifestWriter.lookup()`
   for all 3 dates confirmed `attempted_failed`.
3. A durability check 5 minutes later (>=2 consolidator cycles at the documented 1/min cadence) found **all 31 rows,
   including the independently-fixed 2025-12-18 row, reverted to `capture_status='captured'` with the blank
   `error_reason` and original `2026-07-14T04:1x:xx` `attempted_at`** — i.e. reverted to the EXACT pre-correction state,
   not a new write. `_index/availability_index.parquet`'s GCS generation had advanced (new `last_modified`, confirming a
   real consolidator write happened), but there is no per-VM shard source for the reverted `captured` data:
   `_index/per_vm/` holds only 2 small, unrelated shards (`_legacy_seed.parquet`, `sports-fixtures-job.parquet` —
   neither touches ODDS_API/odds_horizon_bucket). No `manifest-consolidator` GCE VM is running (`compute.googleapis.com`
   aggregated-list query returned empty), so this is not the archived
   `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` failure mode (that one made the index go
   STALE; this one makes it refresh too eagerly, clobbering a fresh write with a stale read) —
   `_index/consolidator.lock` is currently absent (not held), consistent with a normal cycle having completed and
   released it.
4. Best-evidenced explanation: the consolidator's incremental merge reads the FULL canonical baseline near cycle-start
   (`/codex/05-infrastructure/manifest-consolidator-ssot.md`'s own documented "Recovery when a deployed consolidator is
   on a bad image" section confirms canonical-baseline-read is a real step in its merge, and separately notes real
   cycles can run long on a big corpus), then writes the merged result back at cycle-end. If a cycle's baseline READ
   happens BEFORE an external direct-writer's write, and the cycle's own WRITE happens AFTER, the external write is
   silently lost — a classic TOCTOU race, not (or not only) the captured-outranks tie-break. This would affect ANY
   backup-then-write correction script using this pattern against a bucket with a live consolidator cron, including the
   precedent `instruments-service/scripts/flip_phantom_to_attempted_failed.py` (unverified whether ITS 100,431-row flip
   actually raced a live cycle — it may have gotten lucky, or its target bucket's consolidator may have been paused/idle
   at the time).

**No data was lost or corrupted** — the manifest reverted to its EXACT prior (buggy) state, not a mangled intermediate
one; the backup snapshot + this script remain valid and re-runnable.

### Recommended decision (new)

- **Option A2 (recommended)**: pause the sports instruments-store consolidator's Cloud Scheduler cron
  (`uts-prod-manifest-consolidator-instruments-sports`, `*/1 * * * *`) for the duration of the write, matching the codex
  SSOT's own documented recipe ("pause its cron → snapshot the canonical → write → re-enable the cron"), then re-run
  this script's `--apply`, verify durability with the cron still paused (no race possible), THEN re-enable the cron.
  Requires infra-level authority to pause/resume a live production Cloud Scheduler job (broader blast radius than the
  original ask: no sports odds manifest writes consolidate for the pause window) — flagging for operator/infra sign-off
  rather than self-authorizing.
- **Option B2**: retry-the-write-in-a-loop until it survives 2 consecutive durability checks with no revert (wins the
  race by chance/repetition rather than eliminating it) — pragmatic but not a clean fix, and could still race
  indefinitely if consolidator cycles are frequent/long relative to the retry cadence.
- **Option C2**: escalate to the manifest-consolidator/reader owners as a systemic race-condition finding (affects every
  direct-canonical-hand-edit script workspace-wide, not just this one) and have them add a write-time
  optimistic-concurrency guard (e.g. `if_generation_match` on the canonical write, or acquire `_index/consolidator.lock`
  before an external write) rather than re-solving it per-script.

## Todos (continued)

- [x] [CODE] P0. Implement Option C2 as the permanent, systemic fix (complementary to the A2 immediate correction above,
      which fixed these 3 rows but requires a manual cron-pause dance for every future correction): close the
      consolidator's own read-modify-write TOCTOU race so no future direct-writer correction needs a paused-cron window
      at all. Root cause confirmed in `unified_trading_library.manifest_consolidator._write_consolidated`: the CAS
      write's `if_generation_match` came from a fresh `blob.reload()` taken right before the upload, not the generation
      the merge's own canonical read actually saw — a late reload always reflects whatever is CURRENT at that moment, so
      it trivially matches itself and lets the write through even when an external writer landed a change in the merge's
      (90-120s in production) read-to-write window. Fix: `_duckdb_merge_payload`/`_download_canonical_with_generation`
      now capture the canonical's generation via `download_bytes_with_generation` at the SAME read that produces the
      merge payload, and `_write_consolidated` uses THAT captured value (not a fresh reload) as the CAS token on every
      attempt (including retries) — any intervening external write now correctly fails the CAS check and drives the
      existing re-merge retry loop instead of being silently clobbered. Also hardened the canonical read to never trust
      the caller's `canonical_present` mtime-probe hint blindly (a stale-False-negative surfaced by
      `test_consolidate_idempotent`'s second cycle during this fix) — the CAS token now always reflects the OBSERVED
      generation, not a possibly-stale hint. — **unified-trading-library@14301571** (full `quality-gates.sh` green;
      98/98 `test_manifest_consolidator.py` + 60/60 `test_manifest_writer_per_vm.py` passing, including the existing
      lost-update-race regression test and 3 other consolidator test files updated for the new 4-tuple
      `_duckdb_merge_payload` return shape). Reaches the live consolidator automatically per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` (the UTL base image auto-republishes on every LDR push;
      Cloud Run jobs resolve `:latest` on their next ~1-min invocation) — **deployment propagation + a fresh live
      durability re-verification (a NEW direct-writer correction surviving >=2 consolidator cycles without any cron
      pause) is not yet confirmed post-deploy**; that confirmation is deferred to whoever next needs to run a similar
      direct-canonical correction (or a dedicated verification pass), since the 3 dates this issue doc exists for are
      already durably fixed via A2 and don't need re-touching.
