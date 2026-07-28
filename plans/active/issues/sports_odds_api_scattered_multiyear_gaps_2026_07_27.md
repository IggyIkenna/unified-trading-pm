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

## Root-cause investigation (2026-07-28)

**Method**: checked all three evidence surfaces the todo named, for all 6 ranges, before concluding.

**(1) Cloud Logging retention** — `gcloud logging buckets list --project=central-element-323112` shows exactly 2
buckets, retention **2 days** and **400 days** (no longer-retention bucket exists). 400 days before today
(2026-07-28) is ≈2025-06-23. Of the 6 ranges, only **2026-02-22..03-28** falls inside that window — the other 5
(2020-08, 2022-03, 2023-07, 2024-11, 2025-03-11..04-11) are entirely outside Cloud Logging retention; no query can
recover them.

**(2) Git history depth** — checked the oldest commit in every repo this pipeline touches:
`market-tick-data-service` 2025-10-22, `instruments-service` 2025-11-08, `unified-trading-library` 2025-11-06,
`unified-api-contracts` 2026-02-26, `deployment-service` 2026-03-04, `unified-trading-pm` 2026-02-25. **No repo in
the current workspace has history older than 2025-10-22** — every one of 2020/2022/2023/2024/2025-03 predates every
repo's earliest commit. Git archaeology is categorically unavailable for those 5 ranges (only 2026-02-22..03-28
postdates all repos' history starts).

**(3) `vm-logs/` archives** — listed `gs://deployment-scripts-central-element-323112/vm-logs/` in full (3,177
entries) and filtered for every odds/sports/mtds-backfill-prefixed VM name. The only real (non-`pipelinecheck`-smoke-
test) sports-odds backfill VM runs found are recent, narrowly-targeted supplemental runs: `mtds-backfill-odds-ucl-gap`,
`mtds-backfill-odds-ucl-gap2`, `mtds-backfill-sports-odds-3leagues-1` — none cover any of the 6 gap date ranges, and
there is no trace anywhere of the launcher's documented "Full 5.8yr run" (`--start 2020-06-01 --end 2026-03-28`
default) ever having executed as one continuous, discoverable VM run. (`log-archive/final/` — the no-TTL durable
copy — has the same gap; nothing pre-dates 2026-07.)

**(4) Decisive finding for the one in-range window (2026-02-22..03-28)** — a direct Cloud Logging query
(`resource.labels.job_name=~"sports"`, full 35-day window) returned **zero log entries of any kind** — no Cloud Run
Job with "sports" in its name executed at all during this window. Cross-checked against git:
- `deployment-service@1a6fb02` (`feat(sports-scheduler): add --one-shot CLI flag + Cloud Run Job + cron activation`,
  **2026-04-21**) is the commit that first activates the sports Cloud Scheduler cron + Cloud Run Job in the current
  infra — i.e. **no automated sports capture scheduler existed at all until 3.5 weeks after this gap ends.**
- `market-tick-data-service`'s current `odds_api_adapter.py` has no history before **2026-04-11**.
- The one commit that DOES fall inside the gap window, `market-tick-data-service@22a2cded` (2026-03-10, "sports
  migration b5 — odds API validation contract"), only adds a schema *validator* — its own commit message states it
  "remove[s] eager `SportsOddsTickAdapter` import (**was already broken** — UMI `BaseSportsAdapter` not in top-level
  `__init__`)". The capture adapter was non-functional/unwired at that point, by the shipping developer's own words.

**Conclusion**: all 6 ranges — including the one nominally inside Cloud Logging's retention window — **predate the
sports odds capture pipeline's own existence as a scheduled, automated system** (scheduler activated 2026-04-21;
adapter wiring broken as late as 2026-03-10). None of the 3 candidate classes the dispatching todo offered fits:
not **scheduler-dormancy** (no scheduler existed yet to go dormant — a structurally different situation from the
already-fixed 2026-06/07 dormancy bug, which affected an *already-running* scheduler), not a **live-pipeline capture
bug** (no live pipeline was running), and **vendor-side outage** is unfalsifiable either way (the-odds-api.com key is
currently deactivated, so it can't be tested, and no capture attempt — successful or failed — was ever logged for
these windows to know if the vendor was even asked). The correct classification is a 4th, more precise one:
**pre-automation historical-backfill non-coverage** — the 1,608 present days' odds_api data was migrated into the
canonical manifest via `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` from an "orphaned" MTDS location,
implying some earlier, now-untraceable backfill or ad-hoc process populated most-but-not-all of 2020-06-06..present
before the live scheduler ever existed; the 635 missing days are simply the days that process never reached (vendor
historical-data unavailability vs an unretrieved backfill-run failure cannot be distinguished with any surviving
evidence — both are equally consistent with what's left). **No code defect exists to fix for these 6 ranges** — this
is evidentiarily distinct from the two already-fixed bugs cross-checked in this doc's original census (the
2026-06-27..07-15 scheduler-dormancy window and the future-date-guard bug, both of which affected the *live*,
already-running pipeline and are correctly excluded from these 6). The path forward is unchanged from todo #2 below:
plain re-backfill of the missing ranges once the vendor key is restored, via the standard idempotent launcher — no
separate fix commit is needed or possible.

## Recommended decision / next steps

- [x] [DATA] P1. Root-cause the 6 undocumented multi-week odds_api gaps above (2020-08-24..10-10, 2022-03-06..04-18,
      2023-07-01..10-06, 2024-11-19..12-31, 2025-03-11..04-11, 2026-02-22..03-28) — check whichever of GCP Cloud Logging
      retention / `vm-logs/` archives / Cloud Scheduler job history still covers each window; classify each as
      scheduler-dormancy (same class as the already-fixed 2026-06/07 bug), vendor-side outage, or a genuine capture bug.
      Recent ranges (2025, 2026) are far more likely to have retrievable logs than 2020-2022. ✅ — see "Root-cause
      investigation (2026-07-28)" above. Verdict: all 6 ranges predate the sports capture pipeline's own existence
      (scheduler activated 2026-04-21; adapter wiring broken as late as 2026-03-10) — classified as pre-automation
      historical-backfill non-coverage, not scheduler-dormancy/vendor-outage/live-capture-bug (no code fix applies;
      resolution is the plain re-backfill already tracked in todo #2 below). (unified-trading-pm, this doc)
- [ ] [DATA] P1. BLOCKED-PREREQUISITES on `sports_odds_api_key_deactivated_2026_07_26.md` landing first (key restoration
      is [OPERATOR]-gated there). Once the key is restored, backfill all 635 missing days via
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --start <range-start> --end <range-end>` per
      contiguous range (idempotent/manifest-skip by default, no `--force` needed — will not re-fetch the 1,608
      already-present days). (repo: deployment-service)
- [ ] [VERIFY] P2. Once the backfill above lands, re-run this same census (single manifest read, filter
      `source == "odds_api"`, `date >= 2020-06-06"`, diff against the full calendar range) to confirm 0 missing days,
      then close this doc.

## Codex SSOTs

`/codex/02-data/sports-2020-06-data-floor.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`.
