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
    /plans/archive/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
    /plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /codex/02-data/sports-2020-06-data-floor.md,
  ]
created: 2026-07-27
author: unknown
parent_epic: sports_master
assigned_vm: planning
source: [sports_closeout_track_s2_foldin-006]
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
    deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh,
  ]
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
- [ ] [DATA] P1. **RETAGGED 2026-08-07 (autonomous session, sports_all_vendor_honest_coverage_convergence_2026_08_07) —
      the credential block is now STALE, clearing it.** The credit top-up landed 2026-08-03 (per the resolved
      `plans/archive/issues/odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md`); live-reverified
      again today (curl against `/v4/sports`, `unified-trading-sa` identity): `x-requests-remaining: 14475834`,
      `x-requests-used: 524166` (sums to 15,000,000 = 5M/month + 10M top-up, consistent with the 2026-08-03
      verification). No `mtds-backfill-odds-*` VM has run since `mtds-backfill-odds-smallchunk2-20260731` (still true as
      of this check). **Not launching the backfill this same tick** — this launcher has a documented history of
      preemptions/silent freezes/undiscovered-parallel-launches in this exact doc's own Progress Log, and a rushed
      relaunch is exactly the pattern that caused the original quota exhaustion; a proper single-VM, guard-respecting
      launch (`odds-api-concurrency-guard.sh` now caps concurrent VMs at 1 by default, added 2026-08-03 specifically
      because of this doc's history) deserves its own dedicated tick rather than being squeezed in at the end of an
      already-dense one. **What's left, concretely, unchanged from the 2026-07-31 analysis below**: launch
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end <today>`, no
      `--force`, single VM, verify it actually reaches a clean terminal state this time (every prior attempt didn't).
      ~~Credential-blocked 2026-08-02 (slot 14, data_engineering, task `-004`) — the-odds-api.com account is OUT OF
      USAGE CREDITS (a NEW, DIFFERENT blocker than the July `DEACTIVATED_KEY` one below; see the 2026-08-02 Progress Log
      entry for full detail).~~ Live-verified via direct curl: `x-requests-used: 5000772` against the 5,000,000/month
      subscription (`x-requests-remaining: -772`), `error_code=OUT_OF_USAGE_CREDITS` on the `/v4/historical/...`
      endpoint specifically (the live `/v4/sports` endpoint still returns 200 — only historical-data calls are gated by
      this quota). This is an operator-gated billing decision (wait for the monthly reset vs. purchase additional
      credits) — do NOT relaunch any backfill VM or run further real-fetch profiling until it clears; every further
      historical call will just 401 and add noise. **Operator decision 2026-08-02 (answering `BLK-6728ec9a`): Option B —
      purchase additional credits / upgrade the plan now.** Stayed credential-blocked until the operator confirms the
      top-up has landed (re-verify live via the same curl check before relaunching anything — do not assume the purchase
      is instant); **confirmed landed + re-verified live 2026-08-07, see retag above.** **UNBLOCKED 2026-07-31 (slot 16)
      — the fix-approach ruling this todo was waiting on is RESOLVED; the code fix shipped 2026-07-30 and this retag was
      just stale for a day.** `market-tick-data-service@362e64e34c1` ("fix(sports): scope smart-skip freshness evidence
      to odds_api's declared source") implements Option A from
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

      **2026-07-31 (slot 16) — LAUNCHED, in progress, NOT flipping yet.** `mtds-backfill-odds-sentinel-fix-20260731`
                                                                                                                                                                                                                                                                              (`asia-northeast1-c`, `e2-highmem-4`, SPOT, `--start 2020-06-06 --end 2026-07-31`, no `--force`), confirmed
                                                                                                                                                                                                                                                                              `RUNNING` at T+~2min (log not yet populated — normal boot lag, tarball fetch + startup script still running).
                                                                                                                                                                                                                                                                              MTDS + UTL tarballs (the repos carrying the actual fix) confirmed fresh at launch; `unified-api-contracts` +
                                                                                                                                                                                                                                                                              `deployment-service` tarballs were stale per the launcher's freshness check but the fix lives entirely in
                                                                                                                                                                                                                                                                              MTDS/UTL, not those two, so proceeded rather than blocking on an unrelated staleness warning. Self-deletes on
                                                                                                                                                                                                                                                                              completion (`VM_SHUTDOWN_ON_COMPLETION=true`). **Next steps for whoever resumes**: check
                                                                                                                                                                                                                                                                              `gcloud compute instances describe mtds-backfill-odds-sentinel-fix-20260731 --zone=asia-northeast1-c` (absence =
                                                                                                                                                                                                                                                                              terminal) and tail
                                                                                                                                                                                                                                                                              `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-sentinel-fix-20260731/run.log`; once
                                                                                                                                                                                                                                                                              terminal, re-run the data_type-aware census (per this doc's own earlier finding — day-level presence alone
                                                                                                                                                                                                                                                                              under-reports; check data_type completeness too) against
                                                                                                                                                                                                                                                                              `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` for
                                                                                                                                                                                                                                                                              `source=odds_api, date>=2020-06-06` — if genuinely 0 gaps (or only structurally unfillable ones), flip this
                                                                                                                                                                                                                                                                              checkbox with the manifest evidence, then do the P2 VERIFY todo's own re-census.

                                                                                                                                                                                                                                                                          **2026-07-31 (slot 5) — `mtds-backfill-odds-sentinel-fix-20260731` reached terminal, but NOT via a clean
                                                                                                                                                                                                                                                                          completion: nearly every chunk OOM-killed (self-deleted after ~1.5h of VM time with minimal net progress).**
                                                                                                                                                                                                                                                                          Confirmed absent via `gcloud compute instances describe` (terminal); `run.log` shows chunks 1-6 of 9 all
                                                                                                                                                                                                                                                                          ending `CHUNK_FAILED: ... exit=137 reason=OOM_KILLED` (chunk 7's log cuts off mid-run at 04:12:11Z with no
                                                                                                                                                                                                                                                                          further lines — the same "silent freeze" signature `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`
                                                                                                                                                                                                                                                                          already documented). Fresh data_type-aware census (single read, `source=odds_api, date>=2020-06-06..
                                                                                                                                                                                                                                                                          2026-07-31`): **590 of 2247 calendar days still missing** (was 595 before this run — only ~5 days of net
                                                                                                                                                                                                                                                                          progress from 1.5h of `e2-highmem-4` SPOT compute). The previously-claimed-closed `2026-02-22..2026-03-28`
                                                                                                                                                                                                                                                                          (35-day) range is confirmed STILL missing — consistent with
                                                                                                                                                                                                                                                                          `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s own later correction that the earlier
                                                                                                                                                                                                                                                                          "closed" claim was a misread of SKIP-vs-Processed log lines (0 real `Processed` lines for that range, not
                                                                                                                                                                                                                                                                          data loss). **New, more severe evidence for the OOM root-cause**: this run used the launcher's DEFAULT
                                                                                                                                                                                                                                                                          `--chunk-size 250` (not the validated `--chunk-size 5` tail mitigation), and OOM-killed on `e2-highmem-4`
                                                                                                                                                                                                                                                                          (32GB) even though chunks 1-6 were mostly `SKIP` days (only 7 `Processed date=` lines across the whole
                                                                                                                                                                                                                                                                          visible log) — the machine-type bump alone is no longer sufficient even for SKIP-dense older history, a
                                                                                                                                                                                                                                                                          worse severity than the sibling doc's "cross-day accumulation" finding (which was scoped to the dense
                                                                                                                                                                                                                                                                          recent tail). Filed as new evidence in that doc. **Mitigation applied**: relaunched as
                                                                                                                                                                                                                                                                          `mtds-backfill-odds-smallchunk-20260731` (`--start 2020-06-06 --end 2026-07-31 --chunk-size 5`, same
                                                                                                                                                                                                                                                                          `e2-highmem-4`, SPOT) — the best validated workaround per the sibling doc, though not guaranteed (that
                                                                                                                                                                                                                                                                          doc's own conclusion: "no reliable workaround identified"; chunk-size 5 was 0/3 successful on the tail's
                                                                                                                                                                                                                                                                          dense real-fetch window previously). Verified STARTED (`RUNNING` within seconds of `gcloud compute
                                                                                                                                                                                                                                                                          instances create`). **Still open, NOT flipping**: the underlying OOM defect is an unresolved P1 in the
                                                                                                                                                                                                                                                                          sibling doc ("root-cause the actual retained-memory object(s)") — this backfill cannot be reliably
                                                                                                                                                                                                                                                                          completed until that lands or until this small-chunk relaunch is confirmed to finish clean. That first
                                                                                                                                                                                                                                                                          relaunch (`mtds-backfill-odds-smallchunk-20260731`) was itself preempted ~55s after insert (confirmed
                                                                                                                                                                                                                                                                          via `gcloud compute operations list` → `compute.instances.preempted` — genuine SPOT capacity
                                                                                                                                                                                                                                                                          preemption, unrelated to the OOM bug; zero progress lost, no chunk had started). Retried as
                                                                                                                                                                                                                                                                          **`mtds-backfill-odds-smallchunk2-20260731`** (identical params) — this second launch needed an
                                                                                                                                                                                                                                                                          explicit `--account=github-actions-deploy@central-element-323112.iam.gserviceaccount.com` override
                                                                                                                                                                                                                                                                          (the ambient `gcloud` active account had drifted to a different, lower-privilege identity mid-session,
                                                                                                                                                                                                                                                                          most likely shared-host config state from another slot's concurrent gcloud usage, not a genuine IAM gap
                                                                                                                                                                                                                                                                          on this task's identity — resolved via account selection, no role grant needed). **This was a MANUAL
                                                                                                                                                                                                                                                                          relaunch by this same task/slot, not an automated recovery** — see the correction below (a later
                                                                                                                                                                                                                                                                          dispatch of the P2 VERIFY todo misread this as an automated PROGRESS-checkpoint auto-resume; the
                                                                                                                                                                                                                                                                          `gcloud compute operations list` insert for `smallchunk2` is stamped by the same
                                                                                                                                                                                                                                                                          `github-actions-deploy@...` account this session explicitly passed via `--account`, not a distinct
                                                                                                                                                                                                                                                                          automation identity). **Confirmed genuinely healthy, not just started**: at chunk 18/450 (`--chunk-size
                                                                                                                                                                                                                                                                          5` over the full `2020-06-06..2026-07-31` range), real fetch days processing cleanly (e.g. `Processed
                                                                                                                                                                                                                                                                          date=2020-08-27`/`2020-08-31`, real `ManifestWriter` per-VM shard writes), peak RSS ~13.8GB of the
                                                                                                                                                                                                                                                                          32GB `e2-highmem-4` ceiling — well bounded, no OOM signature after 18 chunks including real-fetch ones.
                                                                                                                                                                                                                                                                          At ~70-90s/chunk this is a genuine multi-hour run (~450 chunks), not completable within a single
                                                                                                                                                                                                                                                                          dispatch. **Next steps for whoever resumes**: check `gcloud compute instances describe
                                                                                                                                                                                                                                                                          mtds-backfill-odds-smallchunk2-20260731 --zone=asia-northeast1-c` (absence = terminal, self-deletes on
                                                                                                                                                                                                                                                                          completion; if preempted again, check `compute.instances.preempted` via operations list before
                                                                                                                                                                                                                                                                          assuming an OOM — and relaunch it MANUALLY, there is no confirmed automated recovery for this
                                                                                                                                                                                                                                                                          launcher) and tail
                                                                                                                                                                                                                                                                          `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-smallchunk2-20260731/run.log`
                                                                                                                                                                                                                                                                          for any `CHUNK_FAILED` lines; once terminal, re-run this same data_type-aware census — if genuinely 0
                                                                                                                                                                                                                                                                          gaps (or only structurally unfillable ones), flip this checkbox with the manifest evidence, then do the
                                                                                                                                                                                                                                                                          P2 VERIFY todo's own re-census. If chunks are still genuinely failing (not just preempting) even at
                                                                                                                                                                                                                                                                          `--chunk-size 5`, this todo is blocked on the sibling doc's P1 root-cause fix landing — do not keep
                                                                                                                                                                                                                                                                          relaunching with the same parameters expecting a different result; escalate via that doc instead.

                                                                                                                                                                                                                                                                          **2026-07-31 (slot 7, data_pipeline_failure escalation, DP_VM_STALL) — `smallchunk2` reached exactly
                                                                                                                                                                                                                                                                          that "genuinely failing even at `--chunk-size 5`" condition; STOPPED per the instruction above, NOT
                                                                                                                                                                                                                                                                          relaunched.** Full evidence in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s new
                                                                                                                                                                                                                                                                          "fifth recurrence" section. Summary: 4 more `CHUNK_FAILED ... OOM_KILLED` events (chunks 18, 26, 32,
                                                                                                                                                                                                                                                                          74 — self-recovered each time) followed by a fifth, unrecovered silent freeze partway through chunk 75
                                                                                                                                                                                                                                                                          (no serial-console OOM line this time, matching the CEFI "global OOM thrashing stalls the whole box"
                                                                                                                                                                                                                                                                          signature). Confirmed NOT a SPOT preemption (`status=RUNNING` at time of stall). Last durable
                                                                                                                                                                                                                                                                          checkpoint: `2021-06-11` (chunk 75/450 partial) — chunks 1-73 clean, chunk 74 recovered. VM deleted
                                                                                                                                                                                                                                                                          (`gcloud compute instances delete`) to end billing waste; no data lost, a future relaunch's
                                                                                                                                                                                                                                                                          skip-if-fresh logic resumes from here. **Did not relaunch a sixth attempt** — per this todo's own
                                                                                                                                                                                                                                                                          instruction, escalated to the sibling doc instead. This todo remains blocked on that doc's P1
                                                                                                                                                                                                                                                                          root-cause fix; whoever resumes should check that P1 first rather than trying yet another chunk-size
                                                                                                                                                                                                                                                                          value.

                                                                                                                                                      **ag-closeout-audit sports 2026-08-09 — STALE, doc-hygiene note (not re-launching, not flipping):** this
                                                                                                                                                      checkbox's own text above ("No `mtds-backfill-odds-*` VM has run since `smallchunk2-20260731`") is now stale —
                                                                                                                                                      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` launched the guard-respecting single-VM run the
                                                                                                                                                      same day this note was written (2026-08-07T11:0XZ, `mtds-backfill-odds-1`) and has since relaunched it through
                                                                                                                                                      the silent-hang bug 9 times (`smallchunk`→`smallchunk9`); as of 2026-08-09T04:13Z it is LIVE at chunk 26/451,
                                                                                                                                                      heartbeat healthy. **Do not launch another VM from this todo** — `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`
                                                                                                                                                      is now the live tracker for this exact backfill; leave this checkbox `[ ]` until that doc's chain reaches a
                                                                                                                                                      genuine 0-gap terminal state, then flip both together citing its final census.

- [ ] [VERIFY] P2. **Census 2026-08-11T18:19Z (slot 26 re-verify): GENUINE PROGRESS — 277 missing (↓14 from 291),
      1981/2258d present.** `smallchunk23` (RUNNING, created ~16:27:02Z) has moved PAST the easy early range this fleet
      has stalled at every prior reading: `PROGRESS.json` `last_completed_date=2020-08-14` (up from 2020-07-05 at slot
      31's 17:12Z reading), `run.log` shows real dense-tail fetch activity (`Odds API batch complete: date=2020-08-18`,
      per-VM manifest shard writes, `SHARD_INCOMPLETE`/partial-manifest shard-isolation lines for a couple of 0-row days
      — expected pattern, not a new defect). Fresh census confirms real capture, not just liveness: 150 contiguous
      ranges (20 >=3d, unchanged largest `2024-11-21..12-31` [41d] and `2026-03-06..03-27` [22d]; the prior 21d
      `2026-06-25..07-15` range is now split into `2026-06-25..07-02` [8d] + `2026-07-07..07-10` [4d] — days in between
      newly captured), 0 blank/untyped `error_reason`. VERDICT still "gaps remain — P1 backfill NOT complete" — do NOT
      flip yet. No new VM launched (standing instruction: relaunch is
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s scope). Census:
      `census_odds_api_gap_verify_2026_08_02.py` (read-only, single manifest read).

## Progress Log

- **2026-08-11T21:56Z (slot 6, P2 VERIFY, full re-census — fleet now EMPTY): UNCHANGED — 277 missing days (1981/2258d
  present), 150 ranges (20 >=3d, unchanged from slot 26's 18:19Z reading), 0 blank/untyped `error_reason`.** Re-ran the
  full census (not a bare check) because the fleet state changed since the last reading:
  `mtds-backfill-odds-smallchunk23-20260811` (RUNNING at every reading since 16:27Z) is now GONE —
  `gcloud compute instances list --filter="name~mtds-backfill-odds"` returns 0 rows, no successor VM. Ran
  `census_odds_api_gap_verify_2026_08_02.py` wrapped in `run-bounded-analysis.sh` (`ANALYSIS_MEM_CAP=12G`, RSS-poll
  fallback — the default 4G cap was too tight for this read, killed at 4.58GB RSS; bumped after confirming 26GB free on
  the host) per RULES.md §1's heavy-subprocess memory-bounding rule. Census result is byte-identical to slot 26's
  genuine-progress reading (277/1981/150/20/0) — `smallchunk23` apparently terminated without landing further net
  progress before disappearing. VERDICT unchanged: gaps remain — P1 backfill NOT complete, do NOT flip. No new VM
  launched (standing instruction: relaunch is `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s scope —
  that doc's own chain owns relaunching, not this VERIFY todo). Skipping `GATED` (est 180) — genuinely new information
  this dispatch (fleet went from RUNNING to empty with no net gap-closing progress), but the VERIFY still cannot pass
  until the backfill chain reaches a genuine 0-gap terminal state.

- **2026-08-11T18:34Z (slot 20, P2 VERIFY, bare check): UNCHANGED since slot 26's 18:19Z census (15 min prior) — same VM
  (`mtds-backfill-odds-smallchunk23-20260811`) still `RUNNING` (confirmed via `gcloud compute instances list`,
  `asia-northeast1-c`, created 2026-08-11T16:27:02Z, unchanged), no new/successor VM, no terminal state reached.
  Re-running the full manifest census 15 min after slot 26's fresh read would reproduce the same 277-missing-days result
  with no new information — same reasoning as prior bare-check dispatches (e.g. slot 22/25/16 above). VERDICT unchanged:
  gaps remain — P1 backfill NOT complete, do NOT flip. No new VM launched (standing instruction: relaunch is
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s scope). Skip `GATED` (est 180).

- **2026-08-11T18:19Z (slot 26, P2 VERIFY): census GENUINE PROGRESS — 277 missing days (1981/2258 present, ↓14 from slot
  31's 291), 150 ranges (20 >=3d), 0 blank error_reason.** `smallchunk23` RUNNING has advanced past the early-range
  stall point every prior reading found (`last_completed_date` 2020-07-05 → 2020-08-14), with real dense-tail fetches
  landing in the manifest (not just liveness) — the fleet is no longer stuck at the same easy stage. P1 backfill still
  NOT terminal (VERDICT: gaps remain). No new VM launched (standing instruction). Skip `GATED` (est 180).

- **2026-08-11T17:15Z (slot 31, P2 VERIFY `-6a03c8e26855`): census not re-run — no new progress to measure.**
  `smallchunk22` (RUNNING at the 16:03Z reading) died quickly: `run.log` shows only chunk 1/452 (5 SKIP days,
  `2020-06-06..2020-06-10`) before going silent, no `CHUNK_FAILED`/OOM line visible — same unexplained silent-hang
  recurrence documented in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`. Fleet not empty:
  `mtds-backfill-odds-smallchunk23-20260811` RUNNING (created ~16:27:02Z), `PROGRESS.json`
  `last_completed_date=2020-07-05` at chunk 7/452 (17:12:43Z) — still entirely in the easy already-captured early range,
  same stage every prior relaunch has died at. No new VM launched (standing instruction: relaunch is
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s scope). Skip `GATED` (est 180).**

- **2026-08-11T12:15Z (slot 16, P2 VERIFY `-5f2143d1a647`): census UNCHANGED — 291 missing (1967/2258d), matches slot 25
  exactly. Fleet CHANGED: 0 `mtds-backfill-odds-*` instances (was `smallchunk21` RUNNING at 08:58Z) — terminated, no
  successor; consistent with the live tracker's own already-flagged stall pattern. No new VM (standing instruction).
  Skip `GATED` (est 180).**

- **2026-08-11T08:58Z (slot 25, P2 VERIFY `-5f2143d1a647`): re-census UNCHANGED — 291 missing days (1,967/2,258
  present), 153 ranges (19 >=3d: largest 2024-11-21..12-31 [41d], 2026-03-06..03-27 [22d], 2026-06-25..07-15 [21d]), 0
  blank error_reason — matches slot 22's 08:52Z and slot 30's 08:19Z readings exactly.
  `mtds-backfill-odds-smallchunk21-20260811` RUNNING (asia-northeast1-c, created ~08:30Z). NO new VM launched from this
  slot. VERIFY cannot flip (P1 not terminal). Skip `GATED` (est 180). Census: census_odds_api_gap_verify_2026_08_02.py
  (read-only, single manifest read).**

- **2026-08-11T08:52Z (slot 22, P2 VERIFY `-7ecc23747971`): re-census UNCHANGED — 291 missing days (1,967/2,258
  present), 153 ranges (19 >=3d: largest 2024-11-21..12-31 [41d], 2026-03-06..03-27 [22d], 2026-06-25..07-15 [21d]), 0
  blank error_reason — matches slot 30's 08:19Z reading exactly. Fleet NOT empty:
  `mtds-backfill-odds-smallchunk21-20260811` RUNNING (asia-northeast1-c) — P1 backfill chain active past occurrence #13;
  NO new VM launched from this slot. VERIFY cannot flip (P1 not terminal). Skip `GATED` (est 180). Census:
  census_odds_api_gap_verify_2026_08_02.py (read-only, single manifest read).**

- **2026-08-11T08:19Z (slot 30, P2 VERIFY `-0b21bc7d0f7e`): census 291 missing (↓550), 1967/2258d present, two largest
  named ranges CLOSED, fleet 0 VMs (last VM silent-hang #13 ~06:19Z). Updated checkbox. Skip `GATED` (est 180).**

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
- 2026-07-29 (slot 16): Picked up unblocked P1 backfill. Shipped two launcher fixes (`deployment-service`: stale
  `START_DATE` default clamp to 2020-06-06 floor + `e2-standard-4`→`e2-highmem-4` bump after OOM). Backfill ran chunks
  1-8 clean (full `2020-06-06..2025-11-26` span captured incl. 2026-02-22..03-28 [35d]), then OOM-killed on the dense
  2026-04-16+ tail — `--chunk-size 5` 3/3 OOM, `--chunk-size 1` also OOM on individual dates. Key finding: day-level
  presence census under-reports gaps vs data_type-level completeness. Ran `tail3` VM (`--chunk-size 1`, 105 chunks)
  through `2026-07-29T21:15Z` checkpoint (3/105, 1 captured + 1 OOM), then SESSION END — discovered manifest
  consolidator byte-identical for 47+ min, filed P0 `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`. Full
  OOM detail + launcher fixes: `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`.
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
- 2026-07-31 (slot 5, data_engineering, task `sports_odds_api_scattered_multiyear_gaps-004`, resumed): Picked up the P1
  backfill todo, resuming from where the prior dispatch left `mtds-backfill-odds-sentinel-fix-20260731` running.
  Confirmed the VM had reached terminal (self-deleted); `run.log` showed nearly every chunk (1-6 of 9 confirmed, chunk 7
  log cuts off with no completion line) `CHUNK_FAILED: ... exit=137 reason=OOM_KILLED` — the launcher used its DEFAULT
  `--chunk-size 250`, not the validated small-chunk mitigation. Ran a fresh data_type-aware census (single manifest
  read, `source=odds_api, date>=2020-06-06..2026-07-31`): 590/2247 days still missing, essentially unchanged from the
  pre-run 595 (only ~5 days of real progress from 1.5h of `e2-highmem-4` SPOT compute). This also resolved an apparent
  contradiction with the 2026-07-29 slot-16 Progress Log entry claiming the `2026-02-22..2026-03-28` range was closed —
  cross-checked against `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s own later root-cause section,
  which already corrected that claim as a misread of SKIP-vs-Processed log lines (0 real fetches ever landed for that
  range before the sentinel fix shipped) — not a new regression, just confirming the doc's own later correction is the
  accurate state. Read `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` in full (the tracked P1 root-cause for
  this OOM class) — its root-cause todo ("profile the retained-memory object across date iterations") is still `[ ]`
  open; no fix has landed. Relaunched with the doc's best-validated mitigation (`--chunk-size 5`, same `e2-highmem-4`,
  full remaining range) as `mtds-backfill-odds-smallchunk-20260731`; verified STARTED (`RUNNING` within seconds).
  Documented this run's more-severe OOM evidence (default chunk-size OOMs on `e2-highmem-4` even on mostly-SKIP older
  history, not just the previously-documented dense recent tail) as a new addendum in the sibling OOM doc. Not flipping
  this checkbox — real backfill work remains incomplete and is now blocked on either (a) the small-chunk relaunch
  finishing clean, or (b) the sibling doc's P1 root-cause fix landing. Skipping this dispatch (`reason_code=BLOCKED`,
  `estimated_unblock_minutes` left to policy default since the relaunch's total runtime is genuinely unknown —
  full-range chunk-size-5 could take multiple hours) so a future dispatch checks the relaunch's terminal state and
  re-censuses rather than re-attempting the same default-chunk-size launch that just failed.
- 2026-07-31 (slot 12, data_engineering): Dispatched `sports_odds_api_scattered_multiyear_gaps-002` (this doc's P2
  VERIFY todo) again. Checked the P1 backfill's actual VM state (not a bare git-log check) this time.
  `mtds-backfill-odds-smallchunk-20260731` (the run the prior slot-5 entry above just launched) was preempted ~55s after
  insert (`gcloud compute operations list`: `insert` 2026-07-31T08:29:45Z, `compute.instances.preempted` 08:30:40Z) — it
  never got far enough to write even a `run.log` (only `LAUNCH_PARAMS.json` exists under its log prefix). Found
  `mtds-backfill-odds-smallchunk2-20260731` running ~4 min later (same SPOT params: `--chunk-size 5`, full
  `2020-06-06..2026-07-31` range) and — since no Progress Log entry yet claimed credit for that second launch —
  **incorrectly inferred an automated PROGRESS-checkpoint auto-resume was responsible; this is CORRECTED below by the
  same slot-5 session that actually launched it manually (the doc-commit for that action just hadn't landed yet when
  this entry was written — a race, not evidence of automation).** Confirmed `smallchunk2` currently RUNNING and healthy:
  `PROGRESS.json` shows `last_completed_date=2020-08-14, monotonic=true` (chunk 14/450 per the run.log's own counter),
  `run.log` shows every date so far as `SKIP ... all 1 venues fresh` (0 real fetches yet — this early range was already
  captured pre-backfill), 0 `CHUNK_FAILED` lines, RSS ~1.9GB / mem 9.6% (well under the 85% watchdog threshold) — no OOM
  signature yet, unlike the sentinel-fix and first smallchunk attempts. Since only 14/450 chunks have landed and all are
  SKIPs (no real gap-filling has actually happened yet), re-running the day/data_type census now would reproduce the
  same 590/595-missing-days result — not doing that, same reasoning as every prior skip on this todo. Skipping again
  (`reason_code=BLOCKED`) — genuinely new information this time (ruled out "VM silently died"), but the VERIFY still
  can't complete until the backfill actually reaches and clears the real gap days (chunk 14/450 is still in the easy,
  already-captured early range — the dense recent tail is the historical OOM-risk zone and hasn't been reached yet).
  **Next dispatch**: check
  `gcloud compute instances describe mtds-backfill-odds-smallchunk2-20260731 --zone=asia-northeast1-c` (absence =
  terminal, self-deletes on completion) and its `PROGRESS.json`/`run.log` for any `CHUNK_FAILED` lines; once terminal
  (or once `last_completed_date` has meaningfully passed the known gap ranges), re-run the data_type-aware census — if
  genuinely 0 gaps (or only structurally unfillable ones), flip the P1 checkbox above with the manifest evidence, then
  this P2 VERIFY todo's own census, then this doc is archive-eligible.
- 2026-07-31 (slot 5, resumed after session death mid-task): **Correction to the slot-12 entry immediately above**:
  `mtds-backfill-odds-smallchunk2-20260731` was NOT an automated PROGRESS-checkpoint auto-resume — this same slot-5
  session manually relaunched it (with an explicit `--account=github-actions-deploy@...` override after the first
  attempt, `mtds-backfill-odds-smallchunk-20260731`, was SPOT-preempted ~55s after insert, confirmed via
  `compute.instances.preempted`, not the OOM bug — zero progress lost). Verified via `gcloud compute operations list`
  that `smallchunk2`'s `insert` operation is stamped by the same `github-actions-deploy@...` account this session
  explicitly passed to `gcloud compute instances create --account=...` — not a distinct automation identity. Slot 12's
  inference ("no Progress Log entry claims credit, therefore auto-recovery") was a reasonable read of the doc at that
  moment but is now known to be wrong: this session's own doc-commit for the manual relaunch simply hadn't landed yet
  (this terminal session died mid-task before it could push, and resumed later). **Whether a real automated
  PROGRESS-checkpoint auto-resume exists for this specific launcher remains UNVERIFIED** — nobody has yet observed this
  launcher recover from a preemption without a human/agent re-running the command by hand; treat any future preemption
  as needing a MANUAL relaunch until that's separately confirmed. Re-verified live at a later point than slot 12's
  check: `smallchunk2` genuinely healthy at chunk 18/450, real fetch days now processing cleanly (e.g.
  `Processed date=2020-08-27`/`2020-08-31`, real `ManifestWriter` shard writes), peak RSS ~13.8GB of 32GB — the
  `--chunk-size 5` mitigation is holding past the point where the earlier default-chunk-size run started failing. At
  ~450 chunks total this is a multi-hour run that cannot complete within any single dispatch. Not flipping this
  checkbox. Re-skipping (`reason_code=BLOCKED`) so a future dispatch checks the VM's terminal state per the "Next steps"
  note above.
- 2026-07-31 (slot 3, data_engineering, task `-004`): Per slot 7's instruction above ("check that P1 first rather than
  trying yet another chunk-size value"), started the sibling doc's P1 root-cause investigation instead of relaunching.
  Ruled out `FixtureIdResolver._cache` as the leak (fresh adapter per date, confirmed via `_route_sports`), confirmed
  each chunk is a fresh subprocess (`mtds_chunk_loop.sh`), and promoted a reusable local tracemalloc reproduction
  (`market-tick-data-service/scripts/profile_odds_api_backfill_memory_2026_07_31.py`) — full detail, partial results,
  and resume instructions in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s Progress Log (this same date).
  Not flipping either checkbox here — the profiling run was still in progress at session-end; read that doc before
  resuming.
- **2026-07-31 (slot 3, same session, final) — shipped a verified session-reuse efficiency fix
  (`market-tick-data-service@6ca2d278`), but the OOM itself is NOT confirmed fixed; matching prior slots' disposition,
  re-skipping rather than re-launching the backfill VM.** Full detail in the sibling doc's Progress Log (this same
  date): live re-profile of the fix shows comparable-or-higher RSS than pre-fix, so the `ThreadedResolver` hypothesis is
  NOT confirmed as the root cause. Per slot 7's own instruction above, did not relaunch the VM with yet another
  chunk-size value — that would burn compute without addressing an unconfirmed root cause. `reason_code=BLOCKED`; next
  dispatch should read the P1 doc's final entry and consider a `memray` run (native-allocation profiling) across pre-fix
  vs. post-fix code before trying any further VM relaunch.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **2026-08-02 (slot 14, data_engineering, task `-004`) — real progress confirmed, but hit a NEW credential blocker
  (quota exhaustion, distinct from the earlier key-deactivation one) before the OOM root-cause could be advanced
  further.** Sequence this session:
  1. **VM state check**: `mtds-backfill-odds-smallchunk2-20260731` confirmed absent (terminal/deleted) via
     `gcloud compute instances describe` — consistent with slot 7's 2026-07-31 entry (deleted after the 5th OOM
     recurrence, no data lost).
  2. **Fresh census** (single `read_availability_index` call, columns pruned to
     `date/source/data_type/capture_status/error_reason`, filtered `date>=2020-06-06`): **572/2249 calendar days still
     missing** (real, if partial, progress from the 590/2247 recorded 2026-07-31 — the `smallchunk2` run's chunks 1-73
     before it froze did land some real coverage). The two largest named ranges, `2023-07-01..2023-10-06` (98d) and
     `2022-03-06..2022-04-18` (44d), are confirmed STILL fully open (the backfill never reached that far before dying).
     `2020-08-24..2020-10-10` (the original 48d range) is now fragmented into 5 smaller sub-ranges — partial real
     coverage landed there. 0 untyped/blank `error_reason` on the 298,801 typed rows present (unchanged good state).
     Full current >=3-day range list is in this doc's method for anyone re-running it.
  3. **OOM root-cause, per the sibling doc's "check P1 first" instruction**: attempted a `memray --native` profile
     (installed ephemerally via `uv run --with memray`, no permanent dependency change) of the post-session-reuse-fix
     code (`market-tick-data-service@6ca2d278`) across the same 3 dates the prior tracemalloc run used
     (`2026-04-16/17/18`), specifically to see native/C-extension allocations tracemalloc structurally cannot track.
     **Aborted after ~9 minutes** — memray's native-stack-capture overhead pegged CPU at ~93% and had not finished even
     the first ("quiet", 0-row) date, which took seconds under plain tracemalloc; extrapolated full-3-date runtime was
     wildly disproportionate to this task's budget. Killed cleanly by exact PID (never a name pattern, per RULES.md §
     1. — host memory stayed well bounded throughout (never exceeded ~1.3GB of the host's 49GB available, nowhere near a
        real risk). **Pivoted to a cheaper diagnostic**: a lightweight non-memray RSS+thread-count timeline sampler
        (background thread logging `/proc/self/status` VmRSS + `threading.active_count()` once/sec while
        `download_batch()` runs) to at least see whether growth correlates with thread churn, without instrumentation
        overhead.
  4. **The lightweight sampler immediately surfaced the real, new blocker instead of an OOM signature**: the FIRST real
     historical-data call (`soccer_epl`, date `2026-04-17`) failed `401 Unauthorized`, not an OOM. Live-verified
     directly via curl (same key, `5634d6f1...`, confirmed identical to the one the Python secret-client path resolves —
     no credential-drift trap this time): the live `/v4/sports` endpoint still returns `200`, but
     `/v4/historical/sports/.../odds` returns `401` with `error_code=OUT_OF_USAGE_CREDITS`, and the live endpoint's own
     rate-limit headers confirm it numerically: `x-requests-used: 5000772` against the account's 5,000,000/month
     subscription (`x-requests-remaining: -772`). **This is a DIFFERENT failure mode than the July `DEACTIVATED_KEY`
     incident** — the key itself is valid and active, but the account has now burned through its entire monthly quota
     (plausibly from the sheer number of full-history backfill attempts this doc's own history documents — each
     historical call across dozens of leagues/bookmakers per date is credit-expensive, and there have been 5+ VM-scale
     attempts plus ad-hoc profiling runs). Retagged the P1 checkbox above to `BLOCKED-CREDENTIALS` reflecting this new
     reason (the recognized dispatchable-suppression token per this doc's own earlier
     `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` finding).
  5. **Did not attempt further real fetches once this was confirmed** — every further historical call would just 401
     without adding information, and burning more (even failed) calls against a possibly-still-negative-until-reset
     counter isn't productive. **Not flipping either checkbox to done** — genuine backfill/root-cause progress remains
     blocked, this time on vendor billing/quota, an operator-gated decision (wait for the monthly reset — exact reset
     date unknown from information available here — vs. purchase additional credits), not on infra/OOM. Escalating via
     `/blocked` to get an operator decision on which path to take. The memray-based OOM root-cause investigation
     (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s P1) also cannot continue until real fetches are
     available again; documented there too.
- **2026-08-02 (slot 16, data_engineering, task `-002`, P2 VERIFY): real, substantial progress confirmed (572→300
  missing days), but the VERIFY still cannot pass — genuine gaps remain, and the credential blocker is confirmed
  unchanged.** Sequence this session:
  1. **Found 5 previously-undocumented backfill VMs** (`mtds-backfill-odds-split1`..`split5`, launcher
     `launch-mtds-sports-odds-backfill-vm.sh`, `--chunk-size 2`, `RESUME_ALLOW_PARALLEL=true`) that ran
     2026-07-29T17:45–19:15Z covering the full dense tail `2026-04-18..2026-07-29` in 5 parallel date-range shards, all
     5 with `EXIT_STATUS=0` — clean completions, no OOM. None of this doc's Progress Log entries from that date mention
     them (the 2026-07-29 slot-16 entries only reference `tail3`); could not determine who launched them from available
     evidence, but the VM logs + manifest evidence below confirm they are real and landed real data.
  2. **Fresh day-level + data_type census** (single `read_availability_index` call, columns pruned to
     `date/source/data_type/capture_status/error_reason`, `filters=[("date", ">=", "2020-06-06")]` — row-group pushdown,
     ~4s runtime, ~450MB peak RSS, no OOM risk): **300 of 2249 calendar days still missing** (real progress from the 572
     recorded 2026-08-02, and 590/595 before that — the split1-5 runs evidently closed ~272 days of the dense tail). 0
     blank/untyped `error_reason` on rows present (unchanged good state). 151 contiguous missing-day ranges, 18
     spanning >=3 days — the two largest previously-named ranges are STILL open: `2026-02-22..2026-03-28` (35d,
     claimed-closed-then-corrected twice already in this doc's history — still not actually closed) and
     `2024-11-21..2024-12-31` (41d). The `2026-06-25..2026-07-15` (21d) scheduler-dormancy window is also still open at
     the DATA level — the code fix (`market-tick-data-service@410d7569`) prevents the bug going forward but was never
     paired with a backfill of the already-missed historical days it covers. Full current range list + reusable script:
     `market-tick-data-service/scripts/sports/census_odds_api_gap_verify_2026_08_02.py`.
  3. **Data-type-level check is inconclusive, flagging not asserting**: distinct `data_type` values ever seen for
     `odds_api` include both legacy-cased (`ODDS_MOVEMENT`, `ODDS_SNAPSHOT`) and current lowercase (`odds_movement`,
     `odds_snapshot`) forms plus `trades`/`arbitrage_opportunity`/`odds_horizon_bucket` — a naive "does every present
     day carry every data_type ever observed across all 2249 days" check flags nearly all present days as "partial," but
     this is very likely a schema-evolution artifact (data_types added/renamed over the source's history are not
     expected on every historical day), not a real per-day gap signal like the original 2026-07-29 finding (which
     compared a launcher's own pre-flight fetch-plan against what it wrote, a much tighter check). Did not treat this as
     evidence either way; a real data_type-completeness check would need to know each data_type's own valid-from date,
     out of scope for this read-only VERIFY pass.
  4. **Live-reverified the credential/quota blocker**: direct curl against `/v4/historical/sports/soccer_epl/odds` with
     the current `odds-api-key` secret still returns `401 OUT_OF_USAGE_CREDITS`, `x-requests-remaining: -772` —
     byte-identical to slot 14's 2026-08-02 finding, confirming no monthly reset and no credit purchase has happened
     since, and that no further real fetch has been attempted against this account either (the counter hasn't moved).
     The live `/v4/sports` endpoint still returns 200 (key itself valid, just over quota) — same shape as before.
  5. **Not flipping either checkbox** — real, measurable progress happened (272 fewer missing days) but the P1 backfill
     is NOT complete (300 days still missing, including 2 large named ranges) and remains blocked on the SAME unchanged
     operator-gated quota exhaustion; the P2 VERIFY todo this task actually dispatched still cannot pass either way. Did
     not launch a new backfill VM myself (P1's scope, not this VERIFY todo's, and every further historical-endpoint call
     would just 401 against the still-negative counter without adding information). Skipping this task
     (`reason_code=BLOCKED`) — genuinely new information this time (the quantified progress + the confirmed-unchanged
     credential state), consistent with every prior dispatch's disposition. **Next dispatch**: re-run
     `census_odds_api_gap_verify_2026_08_02.py` — if the operator has actioned the credits decision and a fresh P1
     backfill run has landed, check whether the 300-day count has dropped further (or hit 0 on the structurally-fillable
     days) before considering this VERIFY todo passable.
- **2026-08-02 (slot 15, cicd-role worker adopting data_engineering craft, task `-002`, P2 VERIFY): bare re-check only,
  nothing changed since the entry above — declining to re-run the census.** Live-reverified the credential/quota blocker
  directly (`unified-trading-sa` identity, curl against `/v4/sports/soccer_epl/odds-history/`): still
  `401 OUT_OF_USAGE_CREDITS`, `x-requests-remaining: -772`, `x-requests-used: 5000772` — byte-identical to the last two
  checks (slot 14 and slot 16, both 2026-08-02), confirming no monthly reset and no credit purchase since. Also checked
  `gs://deployment-scripts-central-element-323112/vm-logs/` for any newer odds-api backfill VM: the most recent entry is
  still `mtds-backfill-odds-smallchunk2-20260731` (no new launch since). Since neither the blocker nor the manifest
  state has changed, re-running `census_odds_api_gap_verify_2026_08_02.py` now would reproduce the same 300-missing-day
  result with zero new information — not doing that. Skipping (`reason_code=BLOCKED`) per this doc's established
  disposition.
- **2026-08-02 (slot 13, review-role worker adopting data_engineering craft, task `-002`, P2 VERIFY): re-verified live,
  unchanged — tagged the todo with its own `BLOCKED-CREDENTIALS` marker so it stops re-dispatching identically.**
  Checked `gs://deployment-scripts-central-element-323112/vm-logs/` for any odds-api backfill VM newer than
  `mtds-backfill-odds-smallchunk2-20260731`: none found. Live-reverified the quota blocker directly via curl against
  `the-odds-api.com`: `/v4/sports` still `200` (key valid), `/v4/historical/sports/soccer_epl/odds/` still
  `401 OUT_OF_USAGE_CREDITS`, `x-requests-remaining: -772`, `x-requests-used: 5000772` — byte-identical to every prior
  2026-08-02 check (slots 14, 16, 15). Nothing has changed since the last dispatch, so did not re-run the
  data_type-aware census (would reproduce the same 300-missing-day result). **The actual new work this session**: this
  P2 VERIFY todo's own checkbox text carried no recognized non-dispatchable marker (only P1's checkbox above did) —
  confirmed via `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_BLOCKED_TOKEN_RE`/`_is_non_dispatchable()`
  that `BLOCKED-CREDENTIALS` IS a recognized live-blocked token, scanned across a todo's full continuation block. Added
  that exact marker directly to this todo (see above) so `PlanRegenLoop` stops re-deriving it as dispatchable every
  cycle — this is the root cause of the ~12 near-identical BLOCKED-skip dispatches this doc's P2 todo has absorbed since
  2026-07-28 (every other dispatch correctly found nothing new to do, but the backlog kept re-offering it because the
  todo text itself had no marker for the regex to match). This is a genuine structural fix to the doc, not a bare
  re-check: whoever resumes should no longer see this P2 todo repeatedly auto-dispatched while P1 remains blocked — the
  next dispatch should happen only after P1's marker clears or an operator/main manually re-triages. Not flipping the
  checkbox itself (the underlying gap is still real and unresolved). Skipping this task (`reason_code=BLOCKED`).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — kept the prior 3 (parent plan + 2 codex SSOTs),
  added `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (the sibling OOM doc both open todos are currently
  blocked behind) and the launcher `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh` (target of
  every relaunch this doc's history describes). Could NOT confirm `census_odds_api_gap_verify_2026_08_02.py` (cited
  2026-08-02 as "reusable") resolves anywhere in the market-tick-data-service checkout — dropped, not added.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **2026-08-07 (autonomous session, `sports_all_vendor_honest_coverage_convergence_2026_08_07`)**: Arrived here via a
  much broader operator directive (converge every sports vendor, incl. odds_api, to honest-coverage terminal states)
  while investigating a live census showing `mdps_odds_horizon_bucket` (2,791 attempted_failed, 157,994
  expected_unattempted) and `odds_api` (13,916 attempted_failed) gaps — traced `mdps_odds_horizon_bucket`'s freshness
  collision to the already-shipped fix in `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`, which pointed
  here as the doc owning the actual backfill. Found both P1 and P2 todos above still tagged `BLOCKED-CREDENTIALS` from
  the 2026-08-02 quota exhaustion — stale, since the operator's 10M-credit top-up landed 2026-08-03
  (`odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md`, archived/resolved). Live-reverified today:
  `x-requests-remaining: 14,475,834` (of 15M total), healthy. Retagged both checkboxes (see above) per this workspace's
  stale-tag hard rule. **Deliberately did NOT launch the backfill VM this same tick** — this doc's own history is a
  cautionary tale of exactly that impulse (5+ uncoordinated relaunches, preemptions, silent freezes, an
  undiscovered-parallel-launch quota burn) — leaving the actual
  `launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end <today>` (no `--force`, single VM, respecting the
  now-in-place `odds-api-concurrency-guard.sh` cap=1) for a dedicated next tick with full attention on watching it
  through to a genuine clean terminal state, which no prior attempt has reached. Cross-referenced in
  `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.
- **2026-08-09T09:43Z-12:15Z (slots 16/32/13/17/28/27, 7 routine dispatches): live-VM health checks on
  `mtds-backfill-odds-smallchunk10-20260809`, all RUNNING/healthy, no stall.** Progressed chunk 18/451 (26 total
  in-chunk `CHUNK_FAILED OOM_KILLED` retries — expected per the tracker doc's standing rule, heartbeat freshness is the
  actionable signal, not raw retry count) through chunk 23/451 (~5% of range) by 12:15Z. Frontier stayed in
  already-covered 2020 ground, well before the first real gap (~2021-06-07/chunk 70) — census not re-run on any of these
  7 dispatches (would reproduce the same stale result). No VM launched (already live+healthy), no checkbox flip. All
  skipped `BLOCKED`/`GATED`.
- **2026-08-09T14:27Z (slot 4, P1): campaign stalled — 0 VMs, a NEW failure mode.** `smallchunk10` deleted (6th
  silent-hang, tracker-logged); its relaunch `smallchunk11` ALSO died, but at SETUP (not OOM/hang) —
  `SETUP_EXIT_STATUS=1` on `uv pip install -e .../uac -e .../utl -e .../mtds`, no captured stderr (fast-fail or
  tee-buffer race, indeterminate). Did not relaunch (out of this checkbox's scope). Flagged in tracker doc.
- **2026-08-09T15:13-15:22Z (slot 20, P1): relaunched (`smallchunk12`) after confirming 0 VMs for 46min with no other
  continuation, and root-caused `smallchunk11`'s setup failure — a STALE `market-tick-data-service` tarball** (manifest
  pinned an old sha; launcher auto-republished + relaunched). `smallchunk12` confirmed clean setup + healthy start,
  watched through boot. Not a confirmed permanent fix (one clean launch only). Skip `GATED` (est 180).
- **2026-08-09T18:36Z (slot 15, P1): `smallchunk12` died (7th silent-hang), already relaunched as `smallchunk13` before
  this dispatch — healthy, chunk 6/451.** No action needed. Skip `GATED`.
- **2026-08-09T21:46Z (slot 19, P1): genuine `odds-api-concurrency-guard.sh` cap violation (2 VMs briefly running) —
  self-resolved before any action needed.** A second, undocumented VM (`smallchunk10`, 3rd name-reuse,
  `START=2020-08-29`) ran ~15min alongside the known-good `smallchunk14` (chunk 12/451) — real double-spend risk
  (heavily overlapping ranges) had it persisted; provenance unknown (no Progress Log entry claims it). Credit balance
  checked (10.65M/15M remaining, healthy, not urgent). Self-resolved (deleted) by the time investigation finished — did
  not intervene. Flagged for future monitors: escalate if a duplicate reappears and does NOT self-resolve.
- **2026-08-10T01:33Z (slot 18, P1): 10th silent-hang (`smallchunk15`, chunk 18/452 again — the dominant death chunk),
  already relaunched as `smallchunk16` within the check window — no action needed.**
- **2026-08-10T05:33Z (slot 3, P1): `smallchunk16`->11th hang->`smallchunk17` (briefly SPOT-preempted, auto-relaunched
  ~2min) — healthy, chunk 6/415. Sibling AF (api_football) campaign noted DONE (unrelated to odds_api scope).**
- **2026-08-10T08:54Z (slot 26, P1): volatile window — `smallchunk17` 12th hang (new death site chunk 8) ->
  `smallchunk18` (cleared ch.8, reached ch.15, then ALSO hung) -> `smallchunk19` (setup failure, same signature as
  `smallchunk11`) -> `smallchunk20` (ran ~1 chunk then went silent) -> 0 VMs at 08:51Z ->
  `mtds-backfill-odds-gap-20260727-20260806` (narrower scheduler-dormancy-window VM) appeared 08:54Z, launched by the
  tracker doc's own loop.** Census (07:37Z, tracker doc): still 300/2257 missing, frontier only at chunk ~15-19/425
  (2020-08), first real gap at chunk ~70 (2021-06) — not re-run. Did not launch a replacement (standing instruction).
  Skip `GATED`.
- **2026-08-10T12:15Z-19:26Z (slots 13/19/9/22/16, 5 dispatches): steady healthy progression on `smallchunk14-20260809`,
  no new hangs, frontier chunk 21->113/2171 (2020-09-18->2020-11-12).** Census not re-run (frontier still well before
  first real gap ~2021-06-07/chunk ~70 of this VM's own 2171-chunk plan). All skipped `GATED` (est 180).
- **2026-08-10T22:58Z (slot 4, P2): `smallchunk14` chunk 113/2171, `last_completed=2020-12-18`, healthy; census
  ~550/2257 unchanged. Skip `GATED`.**
- **2026-08-10T23:07Z (slot 24, P1): `smallchunk14` chunk 115/2171, `2020-12-21`, healthy, 0 new OOM. Skip `GATED`.**
- **2026-08-11T03:30Z (slot 5, P2): FLEET STALLED — 0 VMs; `smallchunk14` SPOT-preempted 01:34Z (routine, not the
  tracked hang), no auto-recovery in ~2h (vs usual 2-4min). Frontier ≈2020-12-21, census unchanged ~550/2257 (not
  re-run). Skip `GATED`.**
- **2026-08-11T~04:26Z (slot 19, P1): fleet recovered — `mtds-backfill-odds-20260811-0330` RUNNING (~4min after the
  stall), chunk 8/452, healthy. Census unchanged. Skip `GATED`.**
- **2026-08-11T16:03Z (slot 16, P2 VERIFY `-644192d8431b`, redispatched ~4h after my own 12:15Z stall reading): fleet
  recovered — `smallchunk22-20260811` RUNNING (created 16:02:40Z, ~79s old, `run.log` not yet populated — normal boot
  lag), `--start 2020-06-06 --end 2026-08-11 --chunk-size 5`, launched by someone else between 12:15Z and now (not this
  dispatch). Nothing has processed since the 12:15Z reading, so census still reads 291 missing (1967/2258d) — declined
  to re-run (would reproduce the same unchanged result). Not launching a VM myself (already live), not flipping either
  checkbox. Updated the P2 checkbox text with the fresh fleet state. Skip `GATED` (est 180). **Next dispatch**: re-check
  `smallchunk22` (or successor) for progress/terminal state before re-running the census.**
- **2026-08-11T16:29Z (slot 29, P1 `-3b44a0a4ec31`): `smallchunk22` SPOT-preempted at 16:13:14Z (confirmed via
  `gcloud compute operations list`: `insert` 16:02:41Z → `compute.instances.preempted` 16:13:14Z), died at chunk 1/452 —
  zero real progress lost (still in the already-covered SKIP-dense 2020-06 range, all-SKIP dates only). Fleet was 0 VMs
  at check time. Credit balance re-verified live: `x-requests-remaining: 10,441,544` / `x-requests-used: 4,558,456`
  (healthy, no quota concern). **Relaunched** as `mtds-backfill-odds-smallchunk23-20260811` (same params:
  `--start 2020-06-06 --end 2026-08-11 --chunk-size 5`, `e2-highmem-4`, SPOT) — guard confirmed
  `0 running + 1 planned = 1 <= cap 1`, all 4 tarballs fresh at launch. **Confirmed genuinely healthy, not just
  RUNNING**: `run.log` fresh at T+~2min (116 lines, last timestamp 16:30:39Z), cleanly processing chunk 1/452 (SKIP-only
  dates so far, as expected this early in the range), RSS ~664MiB well bounded, `PIPELINE_HEARTBEAT` fresh, 0
  `CHUNK_FAILED` lines. Nothing has processed since the 16:03Z reading (frontier still in the easy 2020-06 range), so
  census still reads 291 missing (1967/2258d) — declined to re-run (would reproduce the same unchanged result). Not
  flipping either checkbox (P1 not terminal). Skip `GATED` (est 180). **Next dispatch**: check `smallchunk23` (or
  successor) for progress/terminal state before re-running the census.

## Codex SSOTs

`/codex/02-data/sports-2020-06-data-floor.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`.
