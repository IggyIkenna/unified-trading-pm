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
last_updated: 2026-08-15
supersedes:
superseded_by:
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
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
      (`scripts/sports/league_id_relocation/{list_stale_raw_league_id_candidates_2026_08_14.py,     verify_stale_raw_league_id_content_2026_08_14.py, delete_stale_raw_league_id_2026_08_14.py}` +
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
      `SOCCER_UEFA_CHAMPS_LEAGUE` source's own schema) and a human-readable `sport_key` value
      `"UEFA Champions     League"` (title-case, spaced) instead of the odds-api slug `"soccer_uefa_champs_league"` that
      `SPORTKEY_CANON` actually maps. A later, different writer (consistent with an af_fixture/footystats
      fixture-matching enrichment pass, timing matches the K1/K2 uppercase-casing window 2026-07-22..07-27 —
      `scripts/sports/k1k2_casing_revert_2026_07_27/`) wrote directly to the canonical `UCL` path for this day using its
      own vocabulary and OVERWROTE (did not merge with) Track V's originally-correct merged content — the
      `"UEFA Champions League"` sport_key value is genuinely absent from `SPORTKEY_CANON`, so re-running Track V's own
      migration tool against this unit correctly QUARANTINES those rows (never guesses) rather than silently
      re-classifying them, and — separately from that quarantine — its CAS `merge_expected()` still safely folds the
      missing raw rows in alongside the existing (differently-sourced) target content with zero loss on either side.
      **Fix executed**: a PROD DATA write via the already-authorized, unmodified
      `migrate_sports_league_id_casing_     2026_07_21.py --apply-prod --confirm-prod-write --unit day=2025-09-18,venue=<V>`
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
- [ ] [DATA] P1. Recover the FULL remaining FAIL scope: re-run `sports-league-id-delete` `dry` mode (list+verify only,
      zero GCS writes) over the FULL `2020-06-06..2026-08-13` range — this time pull `league-id-work/verify_report.json`
      off the VM (or write it directly to GCS/a durable path) BEFORE it self-deletes — to get the complete FAIL list (up
      to 757 remaining beyond the 12 fixed above for `day=2025-09-18`). For each remaining FAIL, apply the SAME
      diagnostic (does the target's `last_modified` postdate 2026-07-21/22? does its schema/sport_key vocabulary differ
      from the raw source's?) before assuming the same fix applies blindly — a different root cause elsewhere in the
      6-year population is possible. Only once the full-range dry-run shows 0 FAIL is Parts 1/2/5 of the 5-part proof
      genuinely clean.
- [ ] [DATA] P2. Fix the false-negative bug in `migrate_sports_league_id_casing_2026_07_21.py`'s
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
- [ ] [DATA] P3. BLOCKED on the two new P1 todos above (Parts 1/2/5 must show 0 FAIL fleet-wide, not just for
      `day=2025-09-18`). ONLY after that: get explicit re-authorization (this is a NEW gate, not automatic) and launch
      the SAME `sports-league-id-delete` category in `full` mode (`--apply-prod --confirm-prod-write`) to execute the
      actual delete, per finding T's carve-out — re-query `gcs_bucket_soft_delete_retention_seconds()` fresh at
      execution time, cite the value inline.
- [x] [DOC] P2. ✅ Corrected the stale "UNBLOCKED 2026-07-28: Track C's lowercase-revert" citation in
      `/plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md`'s Track V todo (same session, same
      commit) — see that plan's Progress Log / todo annotation.
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
