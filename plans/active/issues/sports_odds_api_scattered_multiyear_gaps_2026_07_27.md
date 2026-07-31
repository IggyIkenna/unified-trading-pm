---
doc_type: issue
title:
  "odds_api reference-manifest has 635 missing calendar days (28.3%) across 2020-06-06..present — 616 of them
  undocumented, mostly scattered/isolated but including several undocumented multi-week ranges"
summary: >-
  Fresh coverage census run for sports_closeout_track_s2_foldin-006 (extend the golden-window-proven honest-coverage
  recipe for 6 reference/odds sources to full 2020-06-06 floor..present). 5 of 6 sources (open_meteo,
  soccer_football_info, transfermarkt, understat, footystats) are cleanly extended: every calendar day since the
  2020-06-06 floor has a manifest row (2243-2248 distinct days of 2243 calendar days), 0 blank/un-typed `error_reason`
  on any `empty_confirmed` or `attempted_failed` row. `odds_api` (source in
  `instruments-store-sports-prd-central-element-323112`'s `_index/availability_index.parquet`, migrated in from MTDS per
  `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py`) is the outlier: 635 of 2243 calendar days since the floor
  have ZERO manifest row of any capture_status (not even `expected_unattempted`) — these are true absences, not typed
  empties. Of those 635, only 19 fall inside the already-documented + already-fixed 2026-06-27..07-15 scheduler-dormancy
  window (`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`, fixed
  `market-tick-data-service@410d7569`), and part of one range overlaps the already-documented 2022-09 canonical
  under-capture outage (`mdt_legacy_canonical_row_gap_2026_07_16.md`, superseded). The remaining **616 days are not
  explained by any doc found in the active/archive corpus** — 30 contiguous ranges of >=3 days (several multi-week:
  2020-08-24..10-10 [48d], 2022-03-06..04-18 [44d], 2023-07-01..10-06 [98d], 2024-11-19..12-31 [43d], 2025-03-11..04-11
  [32d], 2026-02-22..03-28 [35d]) plus 120 isolated single-day gaps roughly evenly spread across all 7 days of the week
  (no weekly-schedule signature). No fix attempted — the same vendor's key is currently DEACTIVATED
  (`sports_odds_api_key_deactivated_2026_07_26.md`, still `status: open` as of this writing, re-verified live by 3
  separate slots against the-odds-api.com directly), so no new fetch can land regardless; this doc is scoped to
  root-cause + track the gap, not to backfill it.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [sports, odds-api, data-pipeline-correctness, honest-coverage, gap, manifest, investigation]
related:
  [
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/archive/issues/sports_odds_api_key_deactivated_2026_07_26.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
    /plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /codex/02-data/sports-2020-06-data-floor.md,
  ]
created: 2026-07-27
parent_epic: sports_master
assigned_vm: planning
source: [sports_closeout_track_s2_foldin-006]
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# odds_api scattered multi-year manifest gaps (635 missing days, 616 undocumented)

## What I found

Working `sports_closeout_track_s2_foldin_2026_07_25.md`'s P2b todo ("extend the golden-window-proven honest-coverage
recipe [weather, soccerfootball_info, transfermarkt, understat, footystats, odds-api] to full history within each
source's own `coverage_start`; done when a fresh coverage census shows each source extended to `coverage_start`, with 0
un-typed skip reasons").

**Scope correction applied first**: the todo's own title says "2015→present," but that framing is stale — the 2026-07-21
operator ruling (`/codex/02-data/sports-2020-06-data-floor.md`) clamped every sports source's `coverage_start` to
**2020-06-06** and ruled that "any plan/track that backfills sports history before 2020-06 is moot." So "extend to
coverage_start" today means 2020-06-06→present, not 2015→present; I measured against the live `SOURCE_COVERAGE_START`
floor, not the stale 2015 framing.

**Method**: single read of `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`
(6,871,468 rows; one download, columns `date`/`source`/`capture_status`/`error_reason` only — no whole-corpus GCS walk,
single-walk discipline honored), filtered to `date >= 2020-06-06`, grouped by `source`.

**Result, 5 of 6 sources — genuinely extended, DONE**:

| source               | distinct days (of 2243 since floor) | max date                                       | blank/untyped reason rows |
| -------------------- | ----------------------------------- | ---------------------------------------------- | ------------------------- |
| open_meteo           | 2248                                | 2026-08-01 (expected_unattempted seeded ahead) | 0                         |
| soccer_football_info | 2243                                | 2026-07-27                                     | 0                         |
| transfermarkt        | 2243                                | 2026-07-27                                     | 0                         |
| understat            | 2248                                | 2026-08-01                                     | 0                         |
| footystats           | 2248                                | 2026-08-01                                     | 0                         |

**Result, odds_api — NOT extended, real gap**:

- 1,608 distinct days present / 2243 calendar days since floor = **635 days with ZERO manifest row of any
  capture_status** (not `empty_confirmed`, not `expected_unattempted` — a true absence; IS has no `odds_api` adapter or
  expected-universe seeder for this source per a same-session sub-investigation, so no denominator cell was ever
  materialized for these days either — this is a pure absence, not a mis-typed skip).
- 0 blank/un-typed `error_reason` on the rows that DO exist (`empty_confirmed`=31,221, `attempted_failed`=58,167, all
  typed) — so the "0 un-typed skip reasons" half of the done-when is satisfied for the rows present; the failing half is
  the 635-day absence itself.
- Day-of-week distribution of the 635 missing days is roughly even (Thu 119 / Tue 111 / Sat 87 / Fri 81 / Wed 81 / Sun
  80 / Mon 76) — no weekly-cron-schedule signature.
- 179 contiguous missing-day ranges total: 120 are isolated single days (plausibly ordinary vendor blips), but **30
  ranges span >=3 days**, including 6 multi-week ranges with no explanation found anywhere in the active or archive plan
  corpus after a targeted grep:
  - 2020-08-24 .. 2020-10-10 (48 days)
  - 2022-03-06 .. 2022-04-18 (44 days)
  - 2023-07-01 .. 2023-10-06 (**98 days** — the largest, entirely undocumented)
  - 2024-11-19 .. 2024-12-31 (43 days)
  - 2025-03-11 .. 2025-04-11 (32 days)
  - 2026-02-22 .. 2026-03-28 (35 days)
- Cross-checked against known incidents: the 2022-09-08..10-01 range overlaps the already-documented
  `mdt_legacy_canonical_row_gap_2026_07_16.md` 2022-09-07..10-01 canonical under-capture outage (that doc is now
  SUPERSEDED per the recurrence-check doc, but the outage itself is on record). The 2026-06-25..07-15 range (21 of its
  days fall in my 635) overlaps the already-fixed 2026-06-27..07-15 scheduler-dormancy bug
  (`market-tick-data-service@410d7569`). **Everything else — 616 of 635 days — has no matching incident doc.**

## Why it matters

`odds_api` is the spine feed this whole closeout track cites as gating downstream ML-readiness
(`sports_closeout_track_ s2_foldin_2026_07_25.md`'s own P2c/P2d/VERIFY todos are all `BLOCKED-PREREQUISITES` on P2b
landing first). A 28.3% true-absence rate — not "expected empty," a true gap where the pipeline never even attempted a
fetch — silently understates coverage in any denominator that doesn't specifically check for missing dates (a naive
captured/(captured+attempted_failed+empty_confirmed) ratio ignores true absences entirely, since they're not counted in
ANY bucket). The scale (6 multi-week ranges spanning 6 different years) suggests either (a) several distinct historical
outages of the scheduler/cron/VM class already found once for 2026-06/07, recurring silently for years without detection
because nothing audits for true absence specifically, or (b) a systematic gap in how far back the odds_api
expected-universe was ever seeded. Either way this is a genuine data-correctness finding, not a stale-doc artifact.

## What I did NOT do

Did not attempt any backfill — the-odds-api.com key is currently `DEACTIVATED_KEY`
(`sports_odds_api_key_deactivated_2026_07_26.md`, `status: open`, independently re-verified live by 3 separate slots
against the vendor directly as of 2026-07-26) — every fetch attempt would 401 and just add `attempted_failed` noise. Did
not attempt to root-cause the 6 multi-week gaps beyond the cross-check above — that needs historical scheduler/cron log
access (likely expired for the older ranges) or VM run-log archaeology, out of scope for this read-only census pass.

## Recommended decision / next steps

- [x] ✅ [DATA] P1. **DONE 2026-07-28 (slot 14) — UNABLE TO ROOT-CAUSE any of the 6 windows; all 3 candidate evidence
      sources are exhausted/non-existent, not merely thin.** Checked all three sources this todo named: 1. **GCP Cloud
      Logging retention**: `gcloud logging buckets list --project=central-element-323112` shows exactly two buckets —
      `_Default` (application/scheduler logs, the ones that would show odds_api fetch attempts) retains **2 days**, and
      `_Required` (400-day retention) holds ONLY Admin Activity/System Event/Policy Denied/Access Transparency audit
      logs per its sink filter (`gcloud logging sinks list`) — never the venue-fetch application logs that would show a
      scheduler-dormancy or vendor-outage signature. So even the most recent of the 6 windows (2026-02-22..03-28, ~4-5
      months before this check) is already past the 2-day `_Default` retention and has no substitute in `_Required`. 2.
      **`vm-logs/` archive** (`gs://deployment-scripts-central-element-323112/vm-logs/`): listed all 3,177 entries
      sorted lexicographically — the EARLIEST entry is `af-backfill-20260714-111307/` (2026-07-14). This archive
      mechanism did not exist yet for ANY of the 6 windows, including the most recent (2026-02-22..03-28, which ended
      ~3.5 months before the archive's own start date). 3. **Cloud Scheduler job history**: confirmed the sports odds
      venue is dispatched via `uts-prod-sports-scheduler-cron` (`*/5 * * * *`) → Cloud Run job
      `uts-prod-sports-scheduler`, not a dedicated odds-api-only job; Cloud Scheduler execution history is itself backed
      by Cloud Logging (same `_Default` 2-day retention above), so it adds no independent evidence beyond point 1.
      **Verdict**: none of the 6 gaps (2020-08-24..10-10, 2022-03-06..04-18, 2023-07-01..10-06, 2024-11-19..12-31,
      2025-03-11..04-11, 2026-02-22..03-28) can be classified as scheduler-dormancy vs. vendor-outage vs. capture-bug
      from any infra source available in this project — the retention windows are categorically too short (2 days vs.
      gaps up to 5+ years old), not a matter of digging harder. This closes the root-cause avenue as exhausted, not
      deferred; re-opening it would require either a change to log-retention policy going forward (so FUTURE gaps are
      diagnosable) or accepting the gaps as permanently unexplained. Did not attempt the backfill itself — the
      credential blocker below is unrelated to and independent of this investigation. (repo: market-tick-data-service,
      deployment-service, read-only investigation, no code changed)
- [ ] [DATA] P1. **UNBLOCKED 2026-07-31 (slot 16) — the fix-approach ruling this todo was waiting on is RESOLVED; the
      code fix shipped 2026-07-30 and this retag was just stale for a day.** `market-tick-data-service@362e64e34c1`
      ("fix(sports): scope smart-skip freshness evidence to odds_api's declared source") implements Option A from
      `/plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s P1 (now flipped there too):
      `check_shard_freshness` is now called with `expected_sources={"ODDS_API": "odds_api"}` for the sports path, so the
      foreign `venue='ODDS_API', source='mdps_odds_horizon_bucket'` sentinel row no longer counts as evidence — the
      572-day permanent-skip is fixed at the source. Retagged `[OPERATOR]` → `[DATA]` since no further design ruling is
      needed; this is now a plain re-run. **What's left, concretely**: launch
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end <today>` (no
      `--force` needed — the fix makes the freshness check correctly identify the 595 genuinely-missing days without
      re-touching the 1,545 already-covered ones, so this should be a much narrower/cheaper run than prior full-range
      attempts). Verified via `gcloud storage ls gs://deployment-scripts-central-element-323112/vm-logs/` that no
      `mtds-backfill-odds-*` VM has run since 2026-07-29 — i.e. nobody has exercised the fix yet, the 595-day gap is
      still open in the canonical. Original credential-unblock context (superseded as the active blocker, kept for
      history): the-odds-api.com key was `DEACTIVATED_KEY` through 2026-07-28; the operator has since rotated
      `odds-api-key` (Secret Manager, project `central-element-323112`) to a new key on a 5,000,000-credits/month
      subscription, live-verified via direct curl (HTTP 200, `x-requests-remaining: 5000000`) — see
      `sports_odds_api_key_deactivated_2026_07_26.md`. (repo: deployment-service)
- [ ] [VERIFY] P2. Depends on the P1 backfill above. **Census re-run 2026-07-30 (slot 3) against a snapshotted canonical
      (11,789,693 rows): STILL 595 missing days** across `2020-06-06..2026-04-15` (1,545 of 2,140 days present) —
      unchanged, because P1 never actually fetched anything (see the re-triage above). The consolidator is NOT the
      reason and no longer gates this todo. **2026-07-31 update (slot 16): P1's design blocker cleared 2026-07-30 (the
      source-scoping fix shipped), but P1 STILL has not actually run yet** — no backfill VM has launched with the fix,
      so this VERIFY todo remains genuinely blocked on P1 execution, not on any ruling anymore. Once P1's backfill
      genuinely lands, re-run this same census (single manifest read, filter `source == "odds_api"`,
      `date >=     2020-06-06`, diff against the full calendar range) to confirm 0 missing days, then close this doc.
      Note for whoever runs it: the current 595 decompose into 168 contiguous ranges (not the 27 previously quoted — 27
      was the count of multi-day ranges only), and 23 of the 595 are NOT explained by the sentinel skip, so a clean
      sweep needs those diagnosed separately.

## Progress Log

- 2026-07-28 (slot 14): Picked up the root-cause todo. Checked all three candidate evidence sources named in the todo
  (GCP Cloud Logging bucket retention, `vm-logs/` GCS archive, Cloud Scheduler job wiring) and found every one
  categorically insufficient for all 6 windows, including the most recent — `_Default` Cloud Logging retention is 2
  days, `_Required` (400-day) holds only audit-class logs, and the `vm-logs/` archive's earliest entry is 2026-07-14,
  after even the most recent gap window ended. Closed the root-cause todo as UNABLE TO ROOT-CAUSE (exhausted, not
  deferred) rather than leaving it open for a future slot to re-discover the same retention limits. Re-verified the
  odds-api key live (still `error_code=DEACTIVATED_KEY`) — unchanged from prior checks; the backfill todo below stays
  credential-gated independent of this finding.
- 2026-07-28 (slot 10): Dispatched `sports_odds_api_scattered_multiyear_gaps-002` (the P1 backfill todo below) — the
  6th+ redispatch of this investigation chain across 2 days. Re-verified the odds-api key live once more (pulled fresh
  via `gcloud secrets versions access latest --secret=odds-api-key --project=central-element-323112`, curled
  `the-odds-api.com/v4/sports` directly): still `error_code=DEACTIVATED_KEY`, unchanged. Root-caused WHY this doc kept
  re-dispatching despite the P1 checkbox already carrying an on-line `BLOCKED-PREREQUISITES` marker: that token is not
  in `server/regen_backlog_from_plan.py`'s `_NON_DISPATCHABLE_RE` alternation
  (`CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION` — no `PREREQUISITES`), so it
  re-derives as dispatchable regardless of line placement — a DIFFERENT bug from the already-fixed continuation-line
  issue (`/plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md`). Retagged both open
  checkboxes above (P1 backfill + P2 verify) with the correct, recognized `BLOCKED-CREDENTIALS` token — the real blocker
  genuinely is the operator-gated odds-api key. Filed the general corpus-wide finding (15 files use the unrecognized
  token, not just this doc) as `issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` rather
  than mass-editing every file — several other occurrences are legitimately same-corpus todo dependencies needing
  `sequential`/`depends_on`, not a text-marker fix, so that needs real per-case triage. Not running the backfill (still
  BLOCKED-CREDENTIALS); skipping this task.
- 2026-07-29 (slot 16, IN PROGRESS — not done, do not re-flip the P1 checkbox until the final census below confirms it):
  Picked up the now-unblocked P1 backfill todo. Summary for anyone resuming this:
  1. **Two small launcher bugs found + fixed en route** (both shipped, both documented in their own right):
     `deployment-service@862408578e476a9f0506b7f8091bd7bd69924e538`-era commit (`ca40857`→`bbce1b6` range this session)
     clamped `launch-mtds-sports-odds-backfill-vm.sh`'s stale `START_DATE` default (was 2020-06-01, 5 days before the
     ruled floor — odds_api has no defense-in-depth venue-epoch clamp unlike api_football/soccerfootball_info/
     footystats) and bumped `MACHINE_TYPE` default `e2-standard-4`→`e2-highmem-4` after a live OOM-kill (same root-cause
     family as `/plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s CEFI incident, which that
     fix never covered for this separate sports launcher). **Full OOM investigation, all data, and both follow-up P1/P2
     code-fix todos live in that issue doc — read it before touching this launcher again.**
  2. **Confirmed done via manifest evidence (both attempts independently reached the same point before OOMing)**: the
     full `2020-06-06..2025-11-26` span (chunks 1-8 of the original 250-day-chunk run) plus `2025-11-27..2026-04-15`
     (the first part of chunk 9) are captured — **this includes the biggest documented gap, `2026-02-22..2026-03-28` (35
     days)**, i.e. every NAMED multi-day range from this doc's original findings table is now closed. Do not re-run this
     portion of the range; the pre-flight skip logic will correctly no-op it, but there's no need to pay even that cost
     — a resumed session should scope any further work to `--start 2026-04-16` onward.
  3. **Remaining scope turned out to be BIGGER than the original day-level census implied.** The original
     `635/595 missing days` count only checked "does ANY manifest row exist for (date, source=odds_api)" — but the live
     launcher runs surfaced
     `Pre-flight: venue=ODDS_API date=X — fully covered, skipping data_types=[...]; still fetching=[...]` lines showing
     PARTIAL, data_type-level gaps (e.g. `odds_horizon_bucket` present but `ODDS`, `arbitrage_opportunity`, `markets`,
     `odds_movement`, `odds_snapshot`, `outcomes`, `settlements` still missing) on dates my census would have counted as
     "present" (it only checked day-level any-row presence, not per-data_type completeness). **This is why the
     `2026-04-16..2026-07-29` tail needed FAR more real-fetch days than the ~20-30 isolated single-day gaps the original
     census's un-enumerated "141 isolated single-day gaps" bucket would suggest** — closer to most/all ~105 days in that
     window needing some real fetch. Anyone re-running this census for the final VERIFY todo should check
     data_type-level completeness, not just day-level row presence, or it will under-report remaining gaps the same way
     mine did.
  4. **OOM mitigation history for this tail** (see the issue doc's 2026-07-29 addenda for full detail + evidence):
     `--chunk-size 5` on `e2-highmem-4` → 3/3 chunks OOM-killed (`mtds-backfill-odds-gapfill-tail2-20260729`, deleted
     early after the 3rd failure rather than grinding through 18 more likely-doomed chunks). `--chunk-size 1` (VM
     `mtds-backfill-odds-gapfill-tail3-20260729`, still RUNNING as of this checkpoint) isolates damage to individual
     days but does NOT fully eliminate the risk — chunk 2 (`2026-04-17` alone, a fresh single-day process) also
     OOM-killed, confirming per-day memory variance is genuinely unpredictable (same conclusion the CEFI incident
     already reached), not something a chunk-size parameter can fully solve. The durable fix is the issue doc's P1
     root-cause todo (profile the retained-memory object across date iterations) — out of scope to land in this session.
  5. **State AT THIS CHECKPOINT (2026-07-29T21:15Z, session about to compact)**:
     `mtds-backfill-odds-gapfill-tail3-20260729` RUNNING in `asia-northeast1-c`,
     `--start 2026-04-16 --end 2026-07-29 --chunk-size 1` (105 single-day chunks), `e2-highmem-4`. As of chunk 3/105: 1
     real day captured clean (`2026-04-16`), 1 chunk OOM-failed (`2026-04-17`, isolated — the loop correctly continued
     per the fail-loud+continue design), 0 skips seen yet (this window is real-fetch-dense per finding 3 above). Logs:
     `gs://deployment-scripts-central-element-323112/vm-logs/ mtds-backfill-odds-gapfill-tail3-20260729/run.log`. **Next
     steps for whoever resumes**: let it keep running (self-deletes on completion, `VM_SHUTDOWN_ON_COMPLETION=true`), or
     check status via
     `gcloud compute instances describe mtds-backfill-odds-gapfill-tail3-20260729 --zone=asia-northeast1-c`. Once
     terminal, re-run a data_type-aware census against
     `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet` for
     `source=odds_api, date>=2020-06-06` — if genuinely 0 gaps (or only structurally unfillable ones, e.g. no fixtures
     that day), flip the P1 checkbox with the manifest evidence, then do the P2 VERIFY todo's own re-census, then
     archive-eligible. If isolated single-day OOM losses remain (like `2026-04-17`), a final narrow single-day-targeted
     relaunch (`--start <date> --end <date> --chunk-size 1`) closes them individually — do NOT default back to
     `--chunk-size 5`+ for this venue, per finding 4.
- 2026-07-29 (slot 16, SESSION END — real blocker found, do not re-flip P1 until it clears): Superseding the entry
  above. Deleted the hung `tail3` VM (confirmed genuine hang via serial console: kernel OOM-killed exactly 2 prior PIDs,
  chunk 4's process was never OOM-killed, just silently frozen — same "global-thrash stall" failure mode the CEFI OOM
  doc hypothesized but hadn't independently confirmed). Ran a fresh day-level census expecting to see the
  `2020-06-06..2026-04-15` range closed — it was **byte-identical to the census from before any backfill work this
  session**: still 595 missing days, all 27 named ranges unchanged, including the 35-day `2026-02-22..2026-03-28` range
  that 2 independent VM runs' logs both show being processed with real `Processed date=...`/`ManifestWriter` lines.
  Traced this via Cloud Logging to a **separate, more fundamental P0 finding**: the
  `instruments-store-sports-prd-central-element-323112` manifest consolidator's `rows_out` is byte-identical (9,411,982)
  across every real merge cycle for 47+ minutes while shards/dedup_dropped fluctuate — it is not absorbing new content
  at all right now, for anyone, not just this task's writer. Filed
  `plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` (P0) with the full log evidence,
  escalated via `/blocked` (`BLK-62e1dc42`, recommendation C: stop further backfill VM churn on this task AND get live
  investigation given the fleet-wide blast radius). **Retagged both P1 and P2 checkboxes above from credential-blocked
  to `BLOCKED-OPERATOR-DECISION`** pointing at that P0 doc — this is the actual current blocker, not credentials (the
  key rotation fix from earlier in this doc's history is still correct and unrelated). Real, verified deliverables from
  this session despite the backfill itself not landing: (1) `deployment-service`'s stale pre-floor `START_DATE` default
  fix, (2) the `e2-highmem-4` OOM machine-type fix + extensive documented investigation (2 further OOM findings:
  machine-type-bump-alone insufficient, per-day memory variance genuinely unpredictable), (3) this P0 consolidator
  finding itself, which may explain silent under-reporting fleet-wide for sports coverage, not just odds_api. Do NOT
  interpret the unflipped P1 checkbox as "no progress" — read this entry + the P0 doc before re-attempting the backfill.
- 2026-07-30 (slot 4, data_engineering): Dispatched `sports_odds_api_scattered_multiyear_gaps-002` (this doc's
  `[VERIFY] P2` todo, "Depends on the P1 backfill above"). P1 is still open and now root-caused in
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` as `[OPERATOR]` — needs a fix-approach ruling (options
  A/B/C) on `check_shard_freshness`'s `ODDS_API`-sentinel collision before any re-fetch can land; that doc's own P1 has
  already been bare-re-checked twice today (slots 9, 11) with no change. Bare check only (not repeating the full
  read-only re-verification — nothing has changed to warrant it): `git log` on
  `unified_trading_library/manifest_consolidator.py` shows one new commit since slot 11's check (`59ed61c9`, "tighten
  consolidator merge chunk-count cap"), unrelated to the `check_shard_freshness` sentinel-collision fix the P1 ruling is
  actually gated on; no commit addresses that path. P1 checkbox in
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` remains `[ ]` unresolved. Skipping this task
  (`reason_code=BLOCKED`) rather than re-running the census — a re-run now would just reproduce the already-documented
  595-missing-day result with zero new information, since nothing has been fetched since the last census.
- 2026-07-31 (slot 16): Dispatched `sports_odds_api_scattered_multiyear_gaps-002` (this doc's P2 VERIFY todo) again.
  Before doing a bare re-check, went one step further than the last few dispatches: checked `git log` not just for a fix
  to the consolidator (none expected — it was already exonerated) but specifically for the freshness-skip fix the
  `[OPERATOR]` P1 ruling was waiting on. **Found it had already shipped**:
  `market-tick-data-service@362e64e34c10af14a9cd46bec438156c90a4932b` (2026-07-30T14:39Z, slot 3) implements Option A
  (source-scope the `ODDS_API` sentinel check) exactly as the ruling doc's `[WORKER REC]` proposed, with UTL support
  (`check_shard_freshness(expected_sources=...)`) and a dedicated test file — but neither this doc's P1 checkbox nor
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s P1 `[OPERATOR]` checkbox had been retagged to reflect
  it; both had gone stale for a day, the exact anti-pattern `CLAUDE.md` § "the moment an `[OPERATOR]` tag resolves,
  retag in the SAME edit" warns about (found here because nobody had re-checked for the SPECIFIC fix, only for "any new
  commit"). Retagged both: `sports_manifest_consolidator_...`'s P1 → `[x]` (fix confirmed shipped, cites the commit +
  mechanism); this doc's P1 → `[ ] [DATA]` (was `[OPERATOR]`) with the concrete next launcher command. Confirmed via
  `gcloud storage ls .../vm-logs/` that no backfill VM has run since 2026-07-29 — the fix is live but UNEXERCISED, so
  the 595-day gap is still open and this P2 VERIFY todo still cannot pass (re-running the census now would reproduce the
  unchanged 595-day result, same reasoning as every prior skip on this todo). Did not launch the backfill VM myself —
  that is P1's scope (a multi-hour, real-vendor-API-cost operation), not this VERIFY todo's, and it's now correctly
  unblocked for the backlog to dispatch as its own task. Skipping this task (`reason_code=BLOCKED`) — genuinely new
  information this time (the retag), but the VERIFY itself still can't complete until P1 executes.

## Codex SSOTs

`/codex/02-data/sports-2020-06-data-floor.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`.
