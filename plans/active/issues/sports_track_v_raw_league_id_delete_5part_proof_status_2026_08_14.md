---
doc_type: issue
title:
  Track V raw-keyed league_id GCS delete — Parts 3/2026-07-22-tooling done; fresh object-level dry-run found a real
  769-object coverage gap, full-mode delete BLOCKED pending remediation
summary: >-
  /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md's Track V todo (execute the
  5-part-proof-gated DELETE of old raw-keyed league_id GCS objects) cited a 2026-07-22 checklist where Part 3 (no live
  writer to the old shape) FAILED, and the active plan's own "UNBLOCKED 2026-07-28" note incorrectly attributed the
  unblock to Track C's K1/K2 casing-revert landing — a DIFFERENT axis (instrument_type/data_type casing, not league_id
  shape) with no logical bearing on this population. A fresh, direct, live re-verification (2026-08-14) of the manifest
  across the full 2026-07-22..2026-08-13 window (the entire gap since the last confirmed index walk) found ZERO trades
  rows with a true raw (non-canonical) league_id value across 19,797 rows / 5 dates individually probed + a
  2026-07-22..08-08 range probe — Part 3 now genuinely passes. Parts 1/2/5 were last verified with hard numbers on
  2026-07-22 (275,136/275,136 objects, zero collisions, stale_remaining=0) and were NOT re-verified at the object level
  this session — the todo's own text requires "its own fresh candidate-list re-verify before running", which is real,
  unstarted engineering work (mirroring the K1/K2 casing-revert trio: candidate-list generator, content-verify report,
  CAS-delete executor), not something to skip on the strength of the retention check alone. Per finding T
  (`task_template.md`) and the K1/K2 sibling incident
  (`plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`), §3a reversibility alone never
  supplies the five-part proof — it only waives `[OPERATOR]` once that proof independently holds. No delete was executed
  that session. **Update 2026-08-15 (slot 7)**: the list->verify dry-run trio built that session was run full-range
  (`2020-06-06..2026-08-13`, zero GCS writes) and Parts 1/2/5 do NOT cleanly pass — 769/144,276 (0.53%) candidate
  objects fail content-verify, concentrated on `day=2025-09-18` `SOCCER_UEFA_CHAMPS_LEAGUE` -> `UCL` across >=11 venues.
  This is a genuine data-correctness gap the trio caught as designed (not a script defect); the P3 full-mode delete is
  now explicitly blocked on a new P1 remediation todo, not just on operator re-authorization. No delete was executed
  this session either (dry mode only).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [delete-safety, league-id, sports, gcs, data-correctness, track-v]
related:
  [
    /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/task_template.md,
  ]
created: 2026-08-14
parent_epic: sports_master
priority: P1
source:
  "/plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md Track V todo, dispatched to slot 10,
  2026-08-14"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
last_updated: 2026-08-20
supersedes:
superseded_by:
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
context_scope:
  [
    /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
---

## What I found

Dispatched todo asked me to execute the 5-part-proof-gated DELETE of old raw-keyed `league_id` GCS objects in
`market-data-tick-sports-prd-central-element-323112` (the manifest COPY+SWAP already ran 2026-07-21/22,
`mtds@b2a49317`). The active plan's own text claimed this was "**UNBLOCKED 2026-07-28**: Track C's lowercase-revert (the
prerequisite) has landed" — **that citation is stale/wrong**: Track C's lowercase-revert is the K1/K2
`instrument_type`/`data_type` CASING migration, a structurally different population from this todo's raw-keyed
`league_id` axis (the plan's own text says as much one sentence later: "the population is a DIFFERENT one from K1/K2's
own casing"). Landing an unrelated fix cannot unblock this one; the actual blocker (per the 2026-07-22 checklist folded
into `plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md` line ~325) was **Part 3 of the 5-part
proof: `venue_fetch.py`'s `_build_sports_shard_path` call site was still constructing paths from
`league_str = league_raw` (whatever the fetcher's `league_id` column held), unverified as canonical as of that date.**

**Fresh live re-verification (2026-08-14, this session)** — read-only manifest probes (`read_availability_index`,
bounded via `run-bounded-analysis.sh`, no corpus walk, filtered by `date` for row-group pruning per
`mtds_backfill_vm_startup_oom_rc137_2026_07_14`'s documented mechanism):

- Per-date probe, `data_type=trades`, dates 2026-08-09..2026-08-13 (5,012 rows, all `pipeline_mode=batch_odds_api`): 0
  true-raw-noncanonical `league_id` values in ANY `capture_status` (`attempted_failed` 2,979 / `captured` 662 /
  `empty_confirmed` 1,371). One false-positive worth noting for future re-runs: `league_id="MLS"` matches a RAW KEY in
  `ODDS_API_DISPLAY_TO_CANONICAL` (`"MLS": "MLS"`, an identity mapping) — it is genuinely canonical, not a live-writer
  regression.
- Range probe covering the entire gap since the last confirmed index walk, `2026-07-22..2026-08-08`, `data_type=trades`:
  14,785 rows, 35 distinct `league_id` values, **0 true-raw-noncanonical hits.**
- Combined: the full 2026-07-22..2026-08-13 window (23 days) has zero evidence of a live writer emitting the old
  raw-keyed shape. **Part 3 now passes**, correcting the 2026-07-22 FAIL verdict — this is real, dated, evidenced
  progress on the actual blocker, not the stale Track-C citation the plan currently carries.

**What I did NOT do**: re-verify Parts 1/2/5 at the object level (the actual ~275,136-object candidate population).
Those were last confirmed with hard numbers on 2026-07-22 (`275,136/275,136` target objects `gcs_describe_object`-
verified, manifest ADD/REMOVE swap `stale_remaining=0`) — plausible they still hold given no contradicting evidence
surfaced, but the todo's own text explicitly demands "its own fresh candidate-list re-verify before running", and I did
not build or run that. Doing so requires the same three-script pattern the (successfully executed) K1/K2 casing-revert
used — a candidate-list generator, a content-verify report generator, and a generation-matched CAS-delete executor —
which is genuine, unstarted engineering + VM-scale execution work, not a five-minute check.

## Why it matters

This todo cited the §3a soft-delete-retention carve-out (finding T) as sufficient to skip `[OPERATOR]`. Finding T's own
text is explicit that §3a "only waives the `[OPERATOR]` requirement once the full five-part proof already holds — it
does not itself supply that proof." The sibling K1/K2 delete
(`plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`) was the confirmed negative example
of exactly this reasoning gap — a dispatched todo assumed §3a alone was authorization, and investigation before
executing found ~27.5% of the target population had no twin at all. That doc's 2026-07-28 review pass declared the
underlying pattern ("assuming §3a suffices without confirming the rest of the proof") a permanent hard-stop for
recurrence. This todo, as currently worded in the active plan, has the same shape: a stale "unblocked" citation standing
in for genuine proof. Executing a 275K-object prod delete on that basis would repeat the exact near-miss this workspace
already caught once.

## Recommended decision

- [x] [CODE] P1. ✅ Built the candidate-list generator + content-verify report + generation-matched CAS-delete executor
      trio for the raw-keyed `league_id` GCS population — `market-tick-data-service@c3b188a1`
      (`scripts/sports/league_id_relocation/{list_stale_raw_league_id_candidates_2026_08_14.py, verify_stale_raw_league_id_content_2026_08_14.py, delete_stale_raw_league_id_2026_08_14.py}` +
      29 unit tests in
      `tests/unit/scripts/test_{list_stale_raw_league_id_candidates,verify_stale_raw_league_id_content,delete_stale_raw_league_id}_2026_08_14.py`,
      `quality-gates.sh` full pass). Mirrors the K1/K2 trio's pattern (verify existing canonical twin + delete legacy
      raw-keyed source, never copy), generalized for this population's non-1:1 shape: candidate listing is path-only
      (`classification.json`-driven, raw != canon and not "unknown"), but content-verify re-derives each row's REAL
      canonical target from `sport_key` -> `SPORTKEY_CANON` (not `classification.json`'s coarser per-raw label) since a
      raw league_id's rows can split across >=2 canonical targets — union-of-targets natural-key coverage must be
      complete before a row group is trusted. Delete executor re-verifies fresh (source + all recorded targets
      re-described/re-read, not reused from the verify-report) immediately before a generation-matched
      (`if_generation_match`) conditional delete, closing the verify-then-delete race. Still needed before Parts 1/2/5
      can be re-run: no further engineering — the trio is dry-run-capable now via `list_...` -> `verify_...` ->
      `delete_...` (no `--apply-prod`).
- [x] [DATA] P2. ✅ Launched the DRY-RUN VM (`sports-league-id-delete` category, `launch-canonical-migration-vm.sh`,
      `dry` mode — list+verify only, ZERO GCS writes; confirmed via the printed command in `run.log`: only `list_...`
      and `verify_...` ran, no `delete_...` step) over the full `2020-06-06..2026-08-13` window (2,260 days) —
      `canonical-migration-sports-league-id-delete-20260815-045149` (asia-northeast1-c, self-deleted on completion per
      `VM_SHUTDOWN_ON_COMPLETION=true`). **Result: Parts 1/2/5 do NOT cleanly pass** — see the new P1 todo below and the
      Progress Log for full numbers. Candidate count (144,276) does not match the 2026-07-22 baseline of 275,136 cited
      above — that baseline was the July manifest-swap's ADD/REMOVE row count, a different metric/operation from this
      trio's object-level delete-candidate population, not a contradiction; not reconciled further this session (out of
      scope for the dry-run itself).
- [x] [DATA] P1. ✅ Root-caused + fixed the `day=2025-09-18` `SOCCER_UEFA_CHAMPS_LEAGUE` -> `UCL` natural-key coverage
      gap for all 12 affected venues (BETFAIR_EX_UK, BETONLINEAG, BETVICTOR, CORAL, DRAFTKINGS, FANDUEL, MATCHBOOK,
      PADDYPOWER, PINNACLE, SKYBET, UNIBET_UK, WILLIAMHILL). **Root cause** (confirmed via `get_blob_metadata` + content
      diff, not guessed): the canonical `UCL` target for this (day, venue) population was NOT last-written by Track V's
      own 2026-07-21/22 migration — `last_modified` on the affected targets is 2026-07-27..07-29 (days AFTER Track V
      ran), and the current target content carries a DIFFERENT schema (`fixture_id`/`af_fixture_id`/
      `af_fixture_match_status` present, `venue`/`data_source`/`instrument_type` absent — the inverse of the raw
      `SOCCER_UEFA_CHAMPS_LEAGUE` source's own schema) and a human-readable `sport_key` value `"UEFA Champions League"`
      (title-case, spaced) instead of the odds-api slug `"soccer_uefa_champs_league"` that `SPORTKEY_CANON` actually
      maps. A later, different writer (consistent with an af_fixture/footystats fixture-matching enrichment pass, timing
      matches the K1/K2 uppercase-casing window 2026-07-22..07-27 — `scripts/sports/k1k2_casing_revert_2026_07_27/`)
      wrote directly to the canonical `UCL` path for this day using its own vocabulary and OVERWROTE (did not merge
      with) Track V's originally-correct merged content — the `"UEFA Champions League"` sport_key value is genuinely
      absent from `SPORTKEY_CANON`, so re-running Track V's own migration tool against this unit correctly QUARANTINES
      those rows (never guesses) rather than silently re-classifying them, and — separately from that quarantine — its
      CAS `merge_expected()` still safely folds the missing raw rows in alongside the existing (differently-sourced)
      target content with zero loss on either side. **Fix executed**: a PROD DATA write via the already-authorized,
      unmodified
      `migrate_sports_league_id_casing_ 2026_07_21.py --apply-prod --confirm-prod-write --unit day=2025-09-18,venue=<V>`
      for all 12 units (plan-mode previewed first, no code changes) — no repo commit, evidence is the tool's own run
      output: `verify=PASS` (content-fingerprint match) on all 12; e.g. WILLIAMHILL existing=80 + src=30 -> target=110
      (strict superset, additive CAS merge, matches the tool's proven no-clobber design already used for the
      275,136-object 2026-07-21/22 run). **Verification** (the authoritative natural-key check, not the flawed
      diagnostic below): `list_stale_raw_league_id_candidates_2026_08_14.py` +
      `verify_stale_raw_league_id_content_2026_08_14.py` re-run scoped to `day=2025-09-18` alone -> **392 PASS / 0
      FAIL** (was 12 FAIL); re-run over the neighboring 30-day window `2025-09-04..2025-10-03` -> **4,207 PASS / 0
      FAIL**, confirming the gap does NOT recur on other matchdays in that window (answers the todo's "one sample day is
      not proof" requirement for this window). **Caveat — this fixes ONLY the 12 objects for this exact day; 769 total
      FAILs were found in the 2026-08-15 full-range dry-run vs. 12 fixed here, leaving up to 757 FAIL objects of
      unconfirmed scope (other dates/leagues, not scanned by the 30-day window above) — P3 stays correctly blocked until
      a full-range re-verify shows 0 FAIL fleet-wide.** See the new P1/P2 todos below for the two follow-ups this
      surfaced.
- [x] [DATA] P1. ✅ Recovered the FULL remaining FAIL scope + applied the diagnostic — but the diagnostic surfaced a
      DIFFERENT (not yet safe-to-fix) root cause than `day=2025-09-18`; see the new P1 investigation todo below. A
      concurrent full-range `dry`-mode run (`canonical-migration-sports-league-id-delete-20260815-091724`, launched by
      an earlier turn of this same slot-10 session, completed cleanly before this turn started: `EXIT_STATUS=1`,
      `run.log` confirms `=== VERIFY DONE rc=1 ===`) uploaded the complete report to
      `gs://deployment-scripts-central-element-323112/canonical-migration-sports-league-id-delete/20260815-091724/verify_report.json`
      (73.5MB, 144,276 targets) — the durable-report fix (`deployment-service@f41f56d9`) worked as designed. **757 FAIL
      / 143,519 PASS**, exactly matching the doc's own "up to 757 remaining beyond the 12 fixed for `day=2025-09-18`"
      expectation (769 total − 12 fixed = 757). Note: this session ALSO redundantly launched two more copies of the same
      full-range run (`...-104309`, likely a SPOT-preemption auto-relaunch of `...-091724`, and `...-105755`, this
      turn's own now-unnecessary manual launch which self-deleted within ~2min, presumably refused/errored on a
      concurrent-category conflict) — no harm done (dry mode, zero GCS writes either way), but flagging so a future
      session doesn't assume "VM launched" without first checking for an already-completed sibling run's report.
      Diagnostic applied to a random 15-object sample of the 757 FAILs: unlike `day=2025-09-18` (root cause: a
      2026-07-27..07-29 fixture-enrichment overwrite), EVERY sampled canon-target's `last_modified` is `2026-08-15`
      TODAY, clustered 10:12-10:42 UTC — squarely inside this session's own VM-launch window, but AFTER `...-091724`'s
      own VERIFY completed (10:00:26) and BEFORE `...-104309` started (10:43:09), so neither known VM run explains the
      write. Re-`gcs_describe_object`'d one sample object ~15min after the first check: **generation unchanged**
      (`1786790328407356` both times) — ruling out an actively-mid-write race at read time, but not explaining who wrote
      it once, minutes before either check. All 757 FAILs share the identical reason string ("does not fully cover the
      raw group's rows (natural-key subset check failed)") and each is a DISTINCT (day, venue, raw) triple across 19
      days (2026-04-18..2026-05-31), 21 venues, 7 raw league labels — notably `SUPER_LEAGUE` maps to BOTH
      `GREEK_SUPER_LEAGUE` and `SWISS_SUPER_LEAGUE` depending on (day, venue), confirming genuine raw-label ambiguity is
      at least a contributing factor, not just a coincidence. **Because the root-cause mechanism here is unconfirmed and
      unlike the already-diagnosed `day=2025-09-18` case, no fix was attempted this session** — applying the
      day=2025-09-18 remediation blindly here would repeat exactly the "assumed-identical, unverified" mistake finding T
      already flagged as a permanent hard-stop pattern. See the new P1 todo below.
- [x] [DATA] P1. ✅ **Resolved 2026-08-15 (this session)**: completed all three remaining steps the slot-22 narrowing
      left open — and found the 757-FAIL population is **already remediated**, no prod write needed this session. (1)
      Content-read 3 diverse-day `SUPER_LEAGUE` split-target sample units
      (`day=2026-05-02/05-03/05-09, venue=BETFAIR_EX_EU`): for every sample, both `GREEK_SUPER_LEAGUE` and
      `SWISS_SUPER_LEAGUE` targets' natural-key sets FULLY contain the raw source's per-canon row groups
      (`missing_from_target=0` in all 6 target checks across the 3 units) — confirms the content root cause is genuine
      under-coverage (never a missing/foreign target), matching slot-22's hypothesis, not a new clobber. (2) **No
      migrate-tool run was needed**: the coverage gap these 3 samples would have shown is ALREADY CLOSED as of this
      session's read — see (3). (3) Fresh `list_.../verify_...` re-run scoped to `2026-04-18..2026-05-31` (44 days, a
      superset of the reported 19 affected days): 4,736 candidates re-scanned, **0 FAIL** (was 757 FAIL in the
      `...-091724` report). Since the 44-day window fully covers the previously-known-FAIL day range, this confirms
      Parts 1/2/5 now pass cleanly for the ENTIRE population that report flagged. Most likely explanation: the
      still-unidentified 2026-08-15 10:11-10:42 UTC write burst (see slot-22's Progress Log entry) already performed the
      exact additive-fold fix `migrate_sports_league_id_casing_2026_07_21.py` would have — the `...-091724` run's VERIFY
      step completed at 10:00:26, BEFORE that burst, so its 757-FAIL report is now stale evidence of a since-closed gap,
      not a live one. The writer's identity remains genuinely unresolved (no Data Access audit logging on this bucket —
      a real, separately-tracked gap, not fixed this session) but is no longer load-bearing for Parts 1/2/5's pass/fail
      verdict. **Before authorizing P3's full-mode delete**, still recommended: one fresh full-range
      (`2020-06-06..2026-08-13`) dry-run VM re-verify for a definitive fleet-wide 0-FAIL confirmation — this session's
      44-day targeted re-verify is strong evidence but does not itself re-scan the ~139,540 objects outside that window
      (those were last confirmed clean by the `...-091724` run itself, 143,519 PASS, with no evidence of regression). No
      repo code changes were needed this session (investigation + read-only GCS content checks only, via
      `run-bounded-analysis.sh`-wrapped ad-hoc scripts, never committed — the existing trio's tools were used as-is).
- [x] [DATA] P2. ✅ Fix the false-negative bug in `migrate_sports_league_id_casing_2026_07_21.py`'s
      `no_clobber_all_sources_present` diagnostic (`process_unit`, `by_src`/`present` computation): it computed
      `by_src`'s per-source row hashes from `body` (the raw-source-only column schema) BEFORE the merge with `existing`,
      then compares those hashes against `rb_keys` computed AFTER the union-schema merge (`expected` / readback both
      include any columns unique to `existing`, e.g. `fixture_id`/`af_fixture_id`, NaN-padded onto the source rows) — a
      schema mismatch makes `_row_hashes` differ even when the row's real content is byte-identical, so
      `no_clobber_all_sources_present` reads `False` for EVERY source whenever source/target column sets differ
      (measured: 12/12 `False` on this session's fix, despite independently-confirmed `verify=PASS` AND 0-FAIL
      natural-key re-verification proving no data was lost). This is a real trust gap in a delete-safety diagnostic — a
      genuine future clobber would be indistinguishable from this false positive. Fix: recompute `by_src`'s hashes from
      rows reindexed to `expected`'s final column set (post-union) before hashing, or switch the presence check to the
      same natural-key-subset method `verify_stale_raw_league_id_content_2026_08_14.py` already uses. Add a regression
      test with mismatched source/existing schemas (mirrors this session's real case).
- [x] N. ✅ [DATA][OPERATOR] P3. **EXECUTED 2026-08-19 (interactive session, Harsh — explicit live go-ahead in chat, resolving the contradiction flagged below).**
      See Progress Log entry below for full evidence. Historical text preserved: **CONTRADICTION FLAGGED (`/plan-reconcile sports_master` 2026-08-19) — this todo's own "AUTHORIZED 2026-08-16" header is NOT corroborated by this doc's own Progress Log below and must NOT be read as a live go-ahead to fire `--apply-prod` on this ~144K-275K-object prod GCS delete.** The 2026-08-16 (slot 30) Progress Log entry states verbatim: "Did NOT launch the `full`-mode delete ... filing a `/blocked` question to the operator for that explicit go-ahead rather than treating this 0-FAIL result as authorization by itself." The 2026-08-17 (slot 27) entry reconfirms: "Did NOT execute the delete — that stays gated on the separate `[OPERATOR]` re-authorization slot-30 already filed a `/blocked` question for." No Progress Log entry anywhere in this doc records the operator actually answering that `/blocked` question. **Before dispatching this todo, first check the live escalation-queue/`/blocked`-question state for a genuine operator answer — do not treat the bold "AUTHORIZED" text alone as sufficient.** Re-tagged `[OPERATOR]` as a safety measure pending that confirmation.
      Once genuine operator authorization is confirmed (not assumed from this header): the fresh full-range
      (`2020-06-06..2026-08-16`) `dry`-mode re-verify (144,276/144,276 PASS, 0 FAIL — see Progress Log entry below)
      cleared the 5-part-proof gating-evidence condition. **Before firing `--apply-prod`, the dispatched worker must
      first confirm the re-verified 144,276 count covers the FULL 275,136-object candidate population this todo
      targets** (the two numbers don't match 1:1 as recorded — resolve whether 144,276 is a subset, a different unit
      of count, or the population itself shrank since the original 2026-07-22 275,136 figure, and say which before
      proceeding). Once that's confirmed, launch the same `sports-league-id-delete` category in `full` mode
      (`--apply-prod --confirm-prod-write`) per finding T's carve-out — re-query
      `gcs_bucket_soft_delete_retention_seconds()` fresh at execution time, cite the value inline.
- [x] [DOC] P2. ✅ Corrected the stale "UNBLOCKED 2026-07-28: Track C's lowercase-revert" citation in
      `/plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md`'s Track V todo (same session, same
      commit) — see that plan's Progress Log / todo annotation.
- [ ] [DATA] P2. **New 2026-08-19**: characterize + resolve the 606-object (543 skipped + 63 failed) residual from
      the 2026-08-19 delete execution (see Progress Log below) — their canonical targets vanished sometime during
      that run's own ~1h45m window despite a fresh VERIFY confirming them 0-FAIL only ~38-100 minutes earlier.
      Run a narrowly-scoped LIST+VERIFY re-pass over `2025-07-31..2025-08-13` (the sampled date range) to recover
      the full object list (only a 5-item sample survives in the console log; no detailed report was uploaded for
      the DELETE step) and confirm whether the targets are genuinely gone or were transiently touched. If
      genuinely gone, this is a Track-V coverage gap needing the same additive-CAS-merge remediation the doc's
      earlier `day=2025-09-18` fix used — NOT a re-run of this delete (the raw sources are safe/untouched, not
      urgent). Not the same root-cause class as the already-diagnosed `day=2025-09-18` (foreign-writer overwrite)
      or `SUPER_LEAGUE`-family (latent under-coverage) incidents — different date range, different raw labels.
- [x] [CODE] P2. ✅ Added the `sports-league-id-delete` launcher category to `deployment-service`'s
      `scripts/vm/launch-canonical-migration-vm.sh` (5 call sites: usage string, dispatch case block,
      `MIGRATION_EXTRA_ARGS` suppression, asset-group tag, `STALL_PROGRESS_REGEX`), mirroring
      `sports-k1k2-uppercase-delete`'s structure but as a 3-step chain (list -> verify -> delete, gated on each step's
      clean exit) since this population is not 1:1. `dry` mode runs list+verify ONLY (no GCS writes) — this is the mode
      authorized for the next-session re-verification above; `full` mode additionally chains the delete step but stays
      unauthorized until the new P3 gate above is explicitly cleared — `deployment-service@1c7cd3ca`.

## Progress Log

- **2026-08-15 (this session)**: Dispatched todo 2 ("launch the on-demand delete VM ... execute per finding T's
  carve-out"). Before touching the shared, multi-category `launch-canonical-migration-vm.sh` or executing a
  275,136-object prod delete, filed `BLK-0cb22dbc` flagging that (a) this todo's own citation of §3a soft-delete
  retention as sufficient authorization is the exact reasoning shape the K1/K2 sibling incident already flagged as a
  confirmed near-miss, and (b) Parts 1/2/5 of the 5-part proof have not been re-verified at the object level since
  2026-07-22. Operator answered **C**: do NOT launch the delete VM this session; re-verify Parts 1/2/5 via the
  list->verify dry-run trio (no GCS writes) first, and leave the `--apply-prod` launch for a follow-up
  explicitly-authorized task. Added the launcher category (code-only, reversible, shipped this session) so the dry-run
  re-verification is one command away next session — did NOT launch the VM itself. Split the original P2 todo into two:
  a P2 dry-run-only re-verification and a NEW P3 `[OPERATOR]`-gated full-run todo, so the delete step requires a fresh,
  explicit go-ahead rather than inheriting the original todo's stale authorization. Sanity-checked the trio's
  `list_stale_raw_league_id_candidates_2026_08_14.py` script locally (bounded, `.venv`, single-day scope, 2026-08-13 and
  2021-06-15) — ran clean, 0 candidates on both sampled days. This is NOT evidence Parts 1/2/5 hold (two arbitrary
  single days out of a 6-year/275K-object population is not a re-verification) — the real re-verification is the
  full-range VM dry-run in the P2 todo above, still open.
- **2026-08-15 (slot 7, this session)**: Executed the operator-authorized dry-run re-verification (BLK-0cb22dbc answer
  C). Launched `canonical-migration-sports-league-id-delete-20260815-045149` (asia-northeast1-c) in `dry` mode over the
  full `2020-06-06..2026-08-13` window; verified via `run.log`'s own printed command that only `list_...` and
  `verify_...` ran (no `delete_...` step, zero GCS writes) before launch was trusted. Monitored to completion via a
  bounded log-tail poll (background-bash monitoring was unreliable in this session — got killed twice by something
  outside this agent's control — fell back to short foreground polling loops instead; VM itself ran unaffected either
  way).
  - **LIST step** (104.4s, 2,260 days scanned): `candidate` (stale-raw, delete-eligible pending content-verify)
    **144,276**; `already_canonical` (raw == canon, left alone) 142,795; `unknown` (not in `classification.json`, left
    alone) 119,420.
  - **VERIFY step** (2,528.2s / ~42min, content re-derives each row's real canonical target via `sport_key` ->
    `SPORTKEY_CANON` + union-of-targets natural-key coverage check): **143,507 PASS / 769 FAIL (99.47% pass rate)**,
    `rc=1` (non-zero is the script correctly reporting FAILs found, not a script defect — the LIST step's own `rc=0` and
    the VERIFY step's clean PASS/FAIL tally with no exceptions/tracebacks confirm the trio ran to completion as
    designed).
  - All 10 stdout-sampled FAIL reasons share ONE root cause: `day=2025-09-18`, `league_id=SOCCER_UEFA_CHAMPS_LEAGUE` raw
    rows are NOT fully covered by the `league_id=UCL` canonical target ("target ... does not fully cover the raw group's
    rows (natural-key subset check failed)"), recurring across >=11 venues (BETFAIR_EX_UK, BETONLINEAG, BETVICTOR,
    CORAL, DRAFTKINGS, FANDUEL, MATCHBOOK, PADDYPOWER, PINNACLE, SKYBET, +≥1 more implied by the 769 total vs. the
    10-row sample). The VM self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`) immediately after `VERIFY DONE rc=1` —
    confirmed gone via `gcloud compute instances describe` (`was not found`) before the full
    `league-id-work/verify_report.json` could be pulled off-VM, so only this 10-row `run.log` sample survives; the full
    769-row list needs a re-run (scoped, not full-range) to recover.
  - **Verdict: Parts 1/2/5 do NOT cleanly pass as of this fresh object-level re-verification.** 769/144,276 (0.53%)
    candidate objects have no safe canonical twin under the current mapping — a `full`-mode delete today would be a
    real, provable data-loss event for at least the `2025-09-18` Champions-League population found here. Filed as a new
    P1 todo above (must resolve before P3's full-mode delete can be authorized) rather than silently proceeding — this
    is exactly the class of near-miss finding T (`sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`) already
    flagged as a permanent hard-stop pattern; the trio's own content-verify caught it as designed, so no delete was ever
    at risk this session (dry mode never writes).
  - Candidate count (144,276) vs. the 2026-07-22 baseline (275,136) cited in this doc's frontmatter/summary is a metric
    mismatch, not a contradiction: 275,136 was the July 21/22 manifest COPY+SWAP's ADD/REMOVE row count (a different
    operation), not this trio's object-level delete-candidate population — not reconciled further this session, flagging
    for whoever picks up the P1 todo in case it matters for scoping.
- **2026-08-15 (slot 27, this session)**: Picked up the P1 root-cause+fix todo. Recovered the full `day=2025-09-18` FAIL
  list first (`list_...`/`verify_...` scoped to that single day, ~3s total): 12 FAILs, all
  `SOCCER_UEFA_CHAMPS_LEAGUE -> UCL`, venues
  BETFAIR_EX_UK/BETONLINEAG/BETVICTOR/CORAL/DRAFTKINGS/FANDUEL/MATCHBOOK/PADDYPOWER/PINNACLE/SKYBET/
  UNIBET_UK/WILLIAMHILL. Root-caused via `get_blob_metadata` (generation/`last_modified`) + a direct content diff
  against the raw source, NOT by guessing: every affected `UCL` target's `last_modified` postdates Track V's own
  2026-07-21/22 migration (2026-07-27..07-29) and carries a schema/vocabulary Track V's migration never produces
  (`fixture_id`/`af_fixture_id`/`af_fixture_match_status` columns, human-readable `sport_key="UEFA Champions League"`
  instead of the odds-api slug `soccer_uefa_champs_league"` `SPORTKEY_CANON` maps) — full detail + the fix + the 0-FAIL
  re-verification are recorded on the todo itself above (not duplicated here). Also confirmed via a 30-day
  neighboring-window re-verify (`2025-09-04..2025-10-03`, 4,207 candidates) that this exact gap pattern does NOT recur
  elsewhere in that window — the remaining up-to-757 FAILs from the 2026-08-15 full-range dry-run are of UNKNOWN scope
  (other dates/leagues not covered by this session's window) and are now a separate tracked P1 todo rather than
  assumed-identical or silently left unscoped. Did not touch the `no_clobber_all_sources_present` false- negative bug
  discovered along the way beyond filing it as a P2 todo — fixing a delete-safety diagnostic without its own dedicated
  test coverage in the same pass this session's actual data fix depended on felt like the wrong trade-off; verification
  for THIS session's fix relied on the independently-correct natural-key content-verify script instead (0 FAIL,
  confirmed twice).
- **2026-08-15 (slot 10, this session)**: Picked up the P2 `no_clobber_all_sources_present` false-negative todo. Root
  cause confirmed as described: `by_src`'s per-source hashes were computed from `body` (source-only columns, pre-merge)
  while `rb_keys` were computed on the post-merge union schema — a byte-identical row hashes differently across a
  mismatched column set, so the check read `False` for every source whenever the existing target carried columns the
  source lacked (e.g. `fixture_id`/`af_fixture_id`). Extracted the check into a new
  `_no_clobber_present(body, src_of, expected_columns, rb_keys)` helper and reindexed the source rows onto `expected`'s
  FINAL (post-merge) column set before hashing, matching the todo's own suggested fix. Added 5 unit tests directly
  against the extracted helper (schema-match baseline, extra-existing-columns case mirroring the real `day=2025-09-18`
  finding, a genuine-clobber-still-caught case, a mixed-source case, and the empty-columns edge case) in
  `tests/unit/scripts/test_migrate_sports_league_id_casing_2026_07_21.py` — `market-tick-data-service` had no prior test
  file for this script. `quality-gates.sh` full pass (10804 passed, 0 failed) — took 6 attempts on a heavily contended
  shared host (multiple concurrent slots' QG/quickmerge runs; 4 background QG runs and 3 background quickmerge runs were
  externally killed mid-run before host load eased enough for a clean pass; no failure was ever due to this change,
  tests were green every time they ran to completion). Shipped via quickmerge (foreground, after 3 backgrounded attempts
  were also killed early) — `market-tick-data-service@ec715e509c`, verified as an ancestor of
  `origin/live-defi-rollout`.

- **2026-08-15 (slot 10, this session, continued)**: Picked up the "recover the FULL remaining FAIL scope" P1 todo.
  Found a full-range `dry`-mode run had already completed cleanly earlier this session
  (`canonical-migration-sports-league-id-delete-20260815-091724`, `EXIT_STATUS=1`, report uploaded to GCS via the
  already-shipped `deployment-service@f41f56d9` durable-report fix) — recovered its `verify_report.json` (73.5MB,
  144,276 targets, 757 FAIL / 143,519 PASS, matching the doc's own up-to-757 expectation) directly rather than
  re-launching (a redundant manual launch this turn, `...-105755`, self-deleted within ~2min without producing a report
  — harmless, dry mode, but wasted; a SPOT-preemption auto-relaunch `...-104309` was also independently in-flight, since
  abandoned in favor of the already-complete `...-091724` report). Applied the todo's own diagnostic to a 15-object
  random sample of the 757 FAILs via `gcs_describe_object`: all sampled canon-targets' `last_modified` fall on
  2026-08-15 (today), NOT the 2026-07-27..07-29 window that explained `day=2025-09-18` — a materially different,
  unconfirmed root cause. Re-described one sample object ~15min after the first check: generation unchanged, ruling out
  an active mid-write race but not identifying the one-time writer. Did NOT attempt any fix this session (unlike
  `day=2025-09-18`, the mechanism here is unconfirmed — blindly reapplying that fix would be exactly the
  "assumed-identical-without-verifying" pattern finding T already flagged as a hard-stop). Flipped this todo done
  (recovery + diagnostic-application both genuinely complete) and filed a new, narrower P1 todo for the
  writer-identification + per-unit fix work, keeping P3's full-mode delete correctly blocked. No code shipped this turn
  (read-only GCS investigation + doc updates only).

- **2026-08-15 (slot 22, this session)**: Picked up the "identify the writer" P1 todo. Recovered the full 757-row FAIL
  list from the preserved `verify_report.json` (73.5MB, streamed via `gcs_read_object_range` under
  `run-bounded-analysis.sh`, no re-launch) rather than re-deriving it. Worked through all three named candidates and
  ruled out each with hard evidence, then found the actual content root cause via direct schema/vocabulary inspection —
  full detail below; NO prod write was made this session (read-only investigation only).
  - **Candidate (1) — scheduled/cron gap-fill recapturing recent-past days**: read `sports-trigger-tiers.yaml` in full.
    Discovery tier's rolling window is `lookback_days=1` only; pre/post-match tiers are fixture-proximate (offsets
    relative to a specific fixture's kickoff/final-whistle, not a historical date sweep). Nothing in the live scheduler
    touches arbitrary days 2.5-4 months in the past. **Ruled out** — no code path exists that would sweep
    2026-04-18..2026-05-31 today.
  - **Candidate (2) — another `--apply-prod` invocation in the window**: queried the durable `run_ledger` BigQuery table
    (`central-element-323112.deployment_operational_data.run_ledger`) for ALL rows (every asset_group, not just sports)
    with `completed_at BETWEEN 2026-08-15 10:12:00 AND 10:42:00` — zero rows mention sports/league/footystats. Widened
    to `asset_group=sports` since 2026-08-14 — only the already-known dry-run VMs and `sports-forward-poll` show up,
    none inside the window (in fact `sports-forward-poll`/`footystats-fwd` shows a ~20h gap with nothing between 08-14
    13:29 and 08-15 09:10, and nothing again until after 11:00). Confirmed the `list_.../verify_...` trio itself (which
    WAS running mid-window per the doc above) is provably read-only — grepped
    `verify_stale_raw_league_id_content_2026_08_14.py` for every write-shaped call; the only `upload_*` call uploads the
    trio's OWN report, never a target object. Checked two other same-day sports migrations for timing overlap:
    `merge_exchange_fixed_odds_content_2026_08_14.py --confirm` executed **2026-08-14** (slot-28, per
    `sports_taxonomy_p2_migration_2026_08_08.md`'s own Progress Log) — a full day before the anomaly, and although its
    own additive-union design (`pd.concat([tgt_df, to_add_df])`, never removes rows, write-verified via readback) means
    it could never have CAUSED a coverage loss even if timing had overlapped.
    `canonical-migration-sport-residue-blank-venue-purge` ran 2026-08-15 **01:40-01:41 UTC**, 9h before the window
    (`run_ledger` confirmed). Checked `gcloud run jobs executions list` for the sports/instruments Cloud Run Jobs — only
    the routine every-1-min manifest-consolidator + every-5-min sports-scheduler executions appear (background noise
    present at all times, not a signal); none of these write parquet CONTENT (manifest-consolidator only rewrites
    manifest index rows per its own SSOT). Checked Cloud Logging for GCS Data Access audit entries on one sample
    object's exact path for the window — **zero results**: Data Access audit logging does not appear to be enabled on
    `market-data-tick-sports-prd-central-element-323112`, so the one authoritative "who wrote this object" signal is
    unavailable for this incident (flagging as a real gap, not fixed this session — enabling it would only help FUTURE
    incidents, not this one retroactively). Checked two other 2026-08-15-dated sports plans
    (`sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`,
    `sports_odds_api_data_type_casing_standardization_2026_08_15.md`) for same-day execution — both are still
    code-only/not-yet-shipped or explicitly gated behind operator approval; neither has executed a prod content rewrite
    yet. **Net: exhausted every readily-available forensic surface; the specific writer/process remains unidentified.**
  - **Candidate (3) — content-diff + NEW finding (root cause of the 757 FAILs)**: downloaded a 6-day-spread sample of
    canon targets + their raw sources directly (`pyarrow`, bounded). Two findings:
    1. **Timing, at full 757-object scale**: `gcs_describe_object`'d ALL 757 canon targets (not just a sample) — 100%
       show `last_modified=2026-08-15`, clustered in an unbroken, steadily-paced sequence from 10:11 to 10:42 UTC
       (roughly 15-45 objects/minute throughout, no gaps/bursts) — this is the signature of ONE continuous ~31-minute
       process, not several independent triggers. This window sits entirely BETWEEN the two known dry-run VMs' active
       periods (`...-091724`'s VERIFY completed 10:00:26 and self-deleted; the SPOT-relaunch `...-104309` started
       10:43:09) — neither VM's own code path writes target content (confirmed above), so this remains an unexplained
       gap even with the fuller picture.
    2. **Root-cause mechanism is DIFFERENT from `day=2025-09-18`, not the same pattern re-occurring**: for
       `day=2025-09-18` the canon target carried a genuinely FOREIGN vocabulary (`sport_key="UEFA Champions League"`
       title-case vs the odds-api slug `SPORTKEY_CANON` maps) and a foreign schema shape. For this session's 6-day
       sample, canon and raw BOTH carry the same odds-api human-readable `sport_key` convention (e.g. canon
       `'Brazil Série A'` / raw `{'Serie A - Italy', 'Brazil Série A'}` for the `SERIE_A`→`BRASILEIRAO` unit) — no
       foreign vocabulary, no foreign schema (the `af_fixture_id`/`af_fixture_match_status` extra columns are present on
       BOTH src and canon in most samples, not canon-only as in the `day=2025-09-18` case). Full breakdown of all 757
       FAILs by (raw, canon) pair: `SERIE_A`→`BRASILEIRAO` (188), `PREMIERSHIP`→`SCOTTISH_PREMIERSHIP` (140),
       `SUPER_LEAGUE`→`GREEK_SUPER_LEAGUE`/`SWISS_SUPER_LEAGUE` (125/35, the ONE split-target label), `PRIMERA_DIVISION`
       →`ARGENTINA_PRIMERA` (118), `SUPERLIGA`→`DANISH_SUPERLIGA` (104), `BUNDESLIGA`→`AUSTRIAN_BUNDESLIGA` (37),
       `FIRST_DIVISION_A`→`JUPILER_PRO` (10) — every single one of the 7 raw labels is a GENERICALLY-NAMED league string
       that collides with a same-named league in another country (Italian vs Brazilian Serie A, Danish vs Turkish
       Superliga, Scottish vs lower-tier English Premiership, German vs Austrian Bundesliga, Greek vs Swiss Super
       League, Belgian Jupiler First Division A vs others). The 188/140/118/104/37/10 counts for the 6 single-target
       labels, plus the 125+35 split for the one genuinely dual-target label, is exactly the signature
       `sport_key`→`SPORTKEY_CANON`-derived-target coverage would produce if Track V's 2026-07-21/22 original migration
       simply never achieved 100% coverage for this ambiguous-raw-label subset (a LATENT gap from July, not a new
       clobber) — consistent with this being the first-ever full-range object-level re-verification since that run.
  - **Conclusion / recommendation**: the "who touched `last_modified` today" question stays open (real gap: no Data
    Access audit logging on this bucket) but is very likely NOT load-bearing for the fix — see the narrowed todo above.
    Recommended next step is a small-sample content-partition check on the one split-target label (`SUPER_LEAGUE`), then
    treat this as a Track V union-of-targets coverage gap (additive fold, same proven tool) — materially different from,
    and simpler than, the `day=2025-09-18` foreign-writer quarantine case. Not flipping this todo `[x]` since positive
    writer identification (the todo's literal ask) was not achieved despite exhausting every available lead; narrowed it
    instead to reflect what IS now known and the concrete next step.

- **2026-08-15 (slot 30, this session)**: Picked up the narrowed writer-identity/content-fix P1 todo. Downloaded the
  preserved `verify_report.json` (73.5MB, 144,276 targets, 757 FAIL) via `run-bounded-analysis.sh`-wrapped ad-hoc
  scripts (2G RSS-poll cap; no re-launch). Confirmed raw-label breakdown matches the doc exactly:
  `SERIE_A`(188)/`PREMIERSHIP` (140)/`SUPER_LEAGUE`(160, split
  GREEK/SWISS)/`PRIMERA_DIVISION`(118)/`SUPERLIGA`(104)/`BUNDESLIGA`(37)/ `FIRST_DIVISION_A`(10). Content-read 3
  diverse-day `SUPER_LEAGUE` sample units (`2026-05-02`/`2026-05-03`/`2026-05-09`, all `venue=BETFAIR_EX_EU`): for each,
  both split targets (`GREEK_SUPER_LEAGUE`, `SWISS_SUPER_LEAGUE`) already contain 100% of the raw source's per-canon
  natural keys (`missing_from_target=0` on all 6 checks) — confirms genuine under-coverage (not a missing target), AND
  that the gap is already closed as of this read. Then ran a fresh `list_stale_raw_league_id_candidates_2026_08_14.py` +
  `verify_stale_raw_league_id_content_2026_08_14.py` pass scoped to `2026-04-18..2026-05-31` (44 days, superset of the
  reported 19 affected days, read-only, no `--apply-prod`): 4,736 candidates, **0 FAIL** (was 757 FAIL in the
  `...-091724` report). No prod write was made or needed this session — the population this todo was gating P3's delete
  on now verifies clean. Flipped the todo `[x]`; left P3 (`[OPERATOR]`-gated full-mode delete) untouched pending a
  recommended fresh full-range re-verify + explicit re-authorization, per the doc's own standing gate. No repo code
  changes; ad-hoc analysis scripts stayed in the session scratchpad, never committed (the existing trio's tools were
  reused as-is, unmodified).

- **2026-08-16 (slot 30, this session)**: Picked up the P3 todo. Checked for a live/concurrent VM in this category
  first (`gcloud compute instances list --filter="name~'canonical-migration-sports-league-id-delete'"` — none
  running), then launched a fresh full-range `dry`-mode re-verify:
  `canonical-migration-sports-league-id-delete-20260816-020358` (asia-northeast1-c, e2-standard-8, SPOT,
  `2020-06-06..2026-08-16`, launched 02:03:58Z). Confirmed genuine boot via the VM's heartbeat blob
  (`vm-heartbeat/<vm>.txt` reading `running`, not just launcher exit code), then bounded-polled
  (background, 180s interval, 55min cap) for the durable `verify_report.json` upload rather than busy-polling in
  the foreground. Report landed at 02:48:27Z (~44min run, consistent with the 2026-08-15 precedent) —
  `gs://deployment-scripts-central-element-323112/canonical-migration-sports-league-id-delete/20260816-020358/verify_report.json`
  (73.4MB). Downloaded + tallied via a `run-bounded-analysis.sh`-wrapped ad-hoc script (4G RSS-poll cap; the
  report's schema is `{"targets": [{"day","venue","raw","source","canon_targets","verify","reason"}, ...]}`, not
  the `status`/`result` field names guessed on the first pass — corrected after inspecting one sample item).
  **Result: 144,276/144,276 `verify=PASS`, 0 FAIL** — a clean sweep across the entire population, zero FAILs
  found anywhere (not just the previously-known `day=2025-09-18` and `SUPER_LEAGUE`-split clusters, both already
  fixed in earlier sessions). This is the definitive fleet-wide 0-FAIL confirmation the P3 todo's own text
  required before authorizing the full-mode delete. **Did NOT launch the `full`-mode delete** — the todo's own
  gate requires a SEPARATE, explicit re-authorization beyond the retention-safety carve-out (finding T /
  the K1/K2 sibling near-miss precedent), which this session does not have; filing a `/blocked` question to the
  operator for that explicit go-ahead rather than treating this 0-FAIL result as authorization by itself. No
  repo code changes this session (read-only GCS + VM launch only); ad-hoc analysis script stayed in the session
  scratchpad, never committed.

- **2026-08-17 (slot 27, this session)**: Picked up `sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md`'s
  P1 todo — run a FRESH live-writer check on THIS population specifically, given
  `sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md` →
  `sports_legacy_league_vocab_recontamination_2026_08_10.md` found a live writer re-contaminating a DIFFERENT
  league-vocabulary population (`instruments-store-sports-prd`, `SEGUNDA_DIVISION`) as recently as 2026-08-10, so this
  bug class was confirmed active in this codebase at the same time the 2026-08-14/16 checks above were running.
  **Result: Part 3 confirmed clean, more robustly than before.** Ran the existing
  `list_stale_raw_league_id_candidates_2026_08_14.py` (read-only, path-only classification, zero GCS writes) scoped to
  `2026-08-14..2026-08-17` — the exact gap since the 2026-08-16 full-range dry-run's own end date — and found **0
  candidates / 0 already_canonical / 0 unknown for every one of the 4 days**, i.e. literally zero objects of ANY kind
  exist under the raw-shaped `.../pipeline_mode=batch_odds_api/.../instrument_type=odds/data_type=trades/ticks.parquet`
  path for this window, not merely zero non-canonical ones. Sanity-checked the script itself still has live GCS access
  and a correct regex by re-running it against `--day 2025-09-18` (a known non-zero baseline from the 2026-08-15
  session): got back the identical `392 candidates / 183 already_canonical / 151 unknown` the earlier session recorded
  — confirms the zero result above is a genuine absence, not a broken probe.
  **Root cause of the zero result, confirmed via direct code read (not assumed)**: `venue_fetch.py`'s
  `_build_sports_shard_path()` no longer emits `data_type=trades` at all — as of `market-tick-data-service@28e2eb36` +
  `@83a1abbdbf` (2026-08-16, `/plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phases
  0-1, both independently confirmed complete in that plan with live evidence), the writer emits `data_type=odds`
  exclusively, and the redeployed live VM (`mtds-live-sports-odds-api-odds-20260816-145019`) is independently verified
  writing real ticks with zero `data_type=trades` writes since. **This is a stronger Part-3 pass than the 2026-08-14
  finding**: that check showed "no raw-keyed VALUES observed in live rows"; this check shows the entire `data_type=trades`
  shape this population lives under is now write-frozen fleet-wide — no object, raw-keyed OR canonical-keyed, can land
  there anymore by any code path.
  **Confirmed this is a DIFFERENT, unrelated mechanism from the sibling recontamination** (read
  `sports_legacy_league_vocab_recontamination_2026_08_10.md` in full): that bug was `instruments-service`'s
  `api_football_reference.py:165` building a league key via raw `build_league_id(country, name)` instead of a
  registry-resolve step, on a completely separate bucket (`instruments-store-sports-prd`) and write path
  (reference-data adapters, not the odds-tick fetcher). Track V's own writer
  (`odds_api_adapter.py`'s `_canonical_league_id()`, in `market-tick-data-service`) already resolves via the numeric
  `api_football_id` → `LEAGUE_REGISTRY` slug — the correct pattern the sibling bug lacked — and is now moot for this
  population regardless, since the whole `data_type=trades` write path is retired.
  **Combined verdict**: Parts 1/2/5 already confirmed clean 144,276/144,276 0-FAIL as of 2026-08-16 (see above); Part 3
  is now confirmed clean for the full `2026-07-22..2026-08-17` window (23+4 days), on stronger evidence than before.
  All five parts of the delete-safety proof hold as of this session. **Did NOT execute the delete** — that stays gated
  on the separate `[OPERATOR]` re-authorization slot-30 already filed a `/blocked` question for on 2026-08-16 (P3 todo
  above); this task's scope was the live-writer pre-check only, per
  `sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md`. No repo code changes this session (read-only
  script re-runs only, no new script written).
- **2026-08-19 (interactive session, Harsh, via /ao-watchdog chat)**: Picked up the P3 `[OPERATOR]`-gated todo.
  Presented the full contradiction + count-mismatch context to Harsh live; he explicitly authorized proceeding
  ("for the 144276 sports related entries please delete them, and be careful that you delete only those ones"),
  resolving both the missing-authorization gap the 2026-08-19 plan-reconcile flagged AND the 144,276-vs-275,136
  ambiguity (accepted 144,276 — this trio's own object-level delete-candidate population — as the correct scope,
  not the July manifest-swap's unrelated 275,136 row-count metric).
  **Pre-flight (all fresh, not assumed from prior runs)**: confirmed no concurrent VM in this category
  (`gcloud compute instances list`, 0 matches); confirmed `deployment-service` local checkout clean and exactly
  at `origin/live-defi-rollout` HEAD (0 ahead/0 behind) before letting the launcher auto-republish its stale
  tarball; queried `gcs_bucket_soft_delete_retention_seconds('market-data-tick-sports-prd-central-element-323112')`
  fresh — **604,800s (exactly 7 days)**, qualifies for the §3a reversibility carve-out.
  **Launched** via the existing, unmodified launcher (no ad-hoc delete code):
  `GCP_PROJECT_ID=central-element-323112 bash scripts/vm/launch-canonical-migration-vm.sh sports-league-id-delete 2020-06-06 2026-08-19 full`
  → `canonical-migration-sports-league-id-delete-20260819-100257` (asia-northeast1-c, e2-standard-8, SPOT).
  **Result** (from the durable off-VM `run.log`, not the VM's own transient serial console — the VM self-deleted
  per `VM_SHUTDOWN_ON_COMPLETION=true` once the chain exited):
  - LIST (123.0s, 2266 days): 144,276 candidates — **exact match to the 2026-08-16 baseline**, confirming the
    population is genuinely frozen (consistent with the `data_type=trades` write path retirement on 2026-08-16).
  - VERIFY (2281.5s / ~38min, fully fresh re-derivation, not reused from any prior report): **144,276 PASS, 0
    FAIL** — the current-moment safety proof held clean, same as 2026-08-16's finding.
  - DELETE (3979.0s / ~66min): `deleted: 143,670`, `skipped_target_missing: 543`, `failed: 63` (a distinct
    code path, same underlying symptom — a 404 on the pre-delete re-verify GET), all other skip categories 0.
    **143,670 + 543 + 63 = 144,276 — fully reconciled, nothing double-counted or unaccounted for.**
    `DELETE DONE rc=1` (non-zero, correctly signaling "not fully clean" rather than silently succeeding).
  - **99.58% of the population (143,670 objects) deleted successfully.** The remaining 606 (543 + 63) were
    **NOT deleted — their raw sources are untouched and safe** — because the delete script's own
    immediately-before-delete re-verification (re-describes/re-reads source + all recorded targets fresh,
    never reusing the VERIFY report's cached content) found their recorded canonical target **no longer
    present**, despite VERIFY having confirmed those exact same targets existed and passed content-verify only
    ~38-100 minutes earlier in this SAME run. This is the delete-safety design working exactly as intended
    (source-only deletion, gated on a live target re-check, never a blind trust of a stale report) — **no data
    was lost or incorrectly deleted this run.**
  - **New, unresolved finding**: something removed or altered 606 canonical target objects during this run's
    own ~1h45m execution window (04:39-06:24 UTC) — a live-writer-shaped mystery, same unresolved-root-cause
    class as the doc's own 2026-08-15 "unidentified 10:11-10:42 UTC write burst" finding (same known gap: no
    GCS Data Access audit logging enabled on this bucket, so the actual writer/process cannot be identified
    after the fact). The console log only samples 5 example paths per category (not the full 606 — no separate
    detailed report was uploaded for the DELETE step, only `verify_report.json` for VERIFY), but the sample is
    concentrated on `day=2025-07-31` (7 of 10 sampled) plus `2025-08-05/08-12/08-13`, all `SOCCER_ITALY_SERIE_A`
    and `SOCCER_GERMANY_BUNDESLIGA` raw labels folding into `SERIE_A`/`BUNDESLIGA` canonical targets — a
    different date range and raw-label pair than the prior `day=2025-09-18` (UEFA Champions League) and
    `SUPER_LEAGUE`-family incidents, so likely a new occurrence of the same class of issue, not a recurrence of
    either previously-diagnosed one.
  - **Not yet done, left as an open follow-up** (the remaining 606 raw sources are safe/untouched, so this is
    not urgent): a fresh, narrowly-scoped LIST+VERIFY re-run over just `2025-07-31..2025-08-13` to characterize
    the full 606-object set (not just the 10 sampled) and confirm whether their canonical targets have
    genuinely vanished for good or were transiently touched by something that already finished; if genuinely
    gone, this becomes a Track-V coverage gap needing the same remediation pattern the doc's earlier
    `day=2025-09-18` fix used (additive CAS-merge fold), not a repeat of this delete.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- added
  `/plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md` on a confirmed evidence fingerprint match: this
  doc's Part-3 pass and that batch's todo 5 independently cite the identical live-VM literal
  `mtds-live-sports-odds-api-odds-20260816-145019` as verification the odds_api writer-flip cutover is clean -- same
  underlying incident, different investigations (found while scouting the batch15 doc; appended after this same
  day's earlier context-scout pass above).


## Context scout

- **context-scout 2026-08-15**: populated context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
