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
    /plans/active/issues/sports_odds_api_key_deactivated_2026_07_26.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
    /plans/archive/2026_07/mdt_legacy_canonical_row_gap_2026_07_16.md,
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
- [ ] [DATA] P1. BLOCKED-PREREQUISITES on `sports_odds_api_key_deactivated_2026_07_26.md` landing first (key restoration
      is [OPERATOR]-gated there). Once the key is restored, backfill all 635 missing days via
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --start <range-start> --end <range-end>` per
      contiguous range (idempotent/manifest-skip by default, no `--force` needed — will not re-fetch the 1,608
      already-present days). (repo: deployment-service)
- [ ] [VERIFY] P2. Once the backfill above lands, re-run this same census (single manifest read, filter
      `source == "odds_api"`, `date >= 2020-06-06"`, diff against the full calendar range) to confirm 0 missing days,
      then close this doc.

## Progress Log

- 2026-07-28 (slot 14): Picked up the root-cause todo. Checked all three candidate evidence sources named in the todo
  (GCP Cloud Logging bucket retention, `vm-logs/` GCS archive, Cloud Scheduler job wiring) and found every one
  categorically insufficient for all 6 windows, including the most recent — `_Default` Cloud Logging retention is 2
  days, `_Required` (400-day) holds only audit-class logs, and the `vm-logs/` archive's earliest entry is 2026-07-14,
  after even the most recent gap window ended. Closed the root-cause todo as UNABLE TO ROOT-CAUSE (exhausted, not
  deferred) rather than leaving it open for a future slot to re-discover the same retention limits. Re-verified the
  odds-api key live (still `error_code=DEACTIVATED_KEY`) — unchanged from prior checks; the backfill todo below stays
  credential-gated independent of this finding.

## Codex SSOTs

`/codex/02-data/sports-2020-06-data-floor.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`.
