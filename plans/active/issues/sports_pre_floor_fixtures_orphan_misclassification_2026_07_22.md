---
doc_type: issue
title:
  Sports orphan-sweep audit misclassified ~83,541 pre-2020-06-06 FIXTURES_SCHEDULE/FIXTURES_OUTCOMES objects as real
  orphans instead of floor violations (registry gap, now fixed)
summary:
  While preparing the sports ORPHAN_REAL backfill (estate_orphan_assessment_2026_07_21.md todo 1), found that
  `SPORTS_DATA_TYPE_TO_SOURCE` (UAC) never registered the two post-2026-07-14 fixture-split data_types
  (`FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`), so `is_pre_launch_date()` silently returned `False` for every row of those
  types regardless of date. This let the sports orphan-sweep's C3 pre-launch-window guard miss real GCS objects dated
  before the ratified 2020-06-06 sports data floor. 83,541 of the reference bucket's 186,971 `E_orphan_real` rows (day
  range 2014-01-01..2020-06-05) are pre-floor and, per `sports-2020-06-data-floor.md`, are fabrication-by- construction
  — they must be WIPED (human-only GCS delete), NOT backfilled into the manifest as real coverage. The registry gap
  itself is fixed (`unified-api-contracts@46d865df`); the WIPE disposition for the 83,541 objects is operator-gated and
  NOT executed here.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [sports, orphan, pre-launch-floor, data-floor, registry-gap, fixtures-schedule, fixtures-outcomes, honest-coverage]
related:
  [
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/orphan-object-detection.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-22
last_updated: 2026-07-22
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: found while preparing the sports orphan back-fill (estate_orphan_assessment_2026_07_21.md todo 1), 2026-07-22
depends_on: []
---

# Sports pre-floor FIXTURES_SCHEDULE/FIXTURES_OUTCOMES misclassification (2026-07-22)

## What happened

The 2026-07-14 fixture-schedule-split writer cutover (`fixture_lifecycle.py`) added two new live data_types,
`FIXTURES_SCHEDULE` and `FIXTURES_OUTCOMES`, replacing the legacy `FIXTURES` for all new writes. The cutover updated
`gcs_paths.SPORTS_DATA_TYPE_TO_FOLDER` (so paths/reads work) but **never updated the separate
`SPORTS_DATA_TYPE_TO_SOURCE` registry** in `league_data.py` — two parallel registries, one updated, one not.

`is_pre_launch_date(data_type, iso_date)` resolves `source = SPORTS_DATA_TYPE_TO_SOURCE.get(data_type)` and returns
`False` (defensively, "can't prove it's pre-launch") whenever `source` is `None`. With the two new data_types absent
from the map, every `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` row — including ones dated years before the sports data
floor — passed the pre-launch check and was classified `E_orphan_real` (a real, legitimate manifest-completeness gap) by
`migration_orphan_sweep_sports.py`, instead of `C3_pre_launch_window` (a floor violation, exempt from backfill and
scoped for deletion).

## Measured impact

Of the reference bucket's (`instruments-store-sports-prd-central-element-323112`) 186,971 `E_orphan_real` rows in the
2026-07-21 audit (`gs://instruments-store-sports-prd-central-element-323112/_index/audit/orphan_sweep_sports.parquet`,
durable, do not re-walk):

- **83,541 rows (~45%)** have `data_type ∈ {FIXTURES_SCHEDULE, FIXTURES_OUTCOMES}` and `day` in
  `[2014-01-01, 2020-06-05]` — strictly before the ratified floor (`SOURCE_COVERAGE_START` clamped to `date(2020, 6, 6)`
  for every sports source, operator ruling 2026-07-21, `sports-2020-06-data-floor.md`).
- The remaining **103,430** reference-bucket `E_orphan_real` rows, and all **27,348** odds-bucket `E_orphan_real` rows,
  are unaffected by this gap (different data_types, or dated on/after the floor) — those are genuine backfill targets.

This is a **data-correctness finding**: per the data-pipeline-correctness HARD RULE, a registry gap that lets sub-floor
data escape the floor-exemption guard is exactly the class of issue that must not be worked around ("pre-existing is not
a triage criterion") — it is fixed at the root (see Resolution) and the resulting misclassified objects are flagged here
for the operator-gated disposition rather than silently backfilled.

## Root cause — fixed

**Shipped `unified-api-contracts@46d865df`**: added `"FIXTURES_SCHEDULE"` / `"FIXTURES_OUTCOMES"` to
`SPORTS_DATA_TYPE_TO_SOURCE` (source=`api_football`, matching legacy `FIXTURES`), the corresponding `SOURCE_PRIORITY`
entries (`["api_football", "footystats"]`), and `AVAILABILITY_AT_SEMANTICS` entries (`announced_at` for SCHEDULE —
matches legacy FIXTURES; `match_end_time` for OUTCOMES — matches the split's own documented lookahead-bias rationale).
Added a regression test (`test_fixtures_schedule_and_outcomes_are_registered`,
`tests/test_sports_source_coverage_propagation.py`) asserting `is_pre_launch_date()` now correctly returns `True` for a
pre-floor date and `False` for a post-floor date on both data_types. Full `quality-gates.sh` green (sentinel
`328a5ce...`→`46d865df`).

This fixes the guard for ALL FUTURE sweeps (any asset_group/data_type combination reaching this code path going forward
will classify correctly) — it does not retroactively reclassify the 2026-07-21 audit parquet, which remains
durable/as-written per the single-walk discipline.

## Todos

- [x] 1. [DATA] P1. Root-cause + fix the `SPORTS_DATA_TYPE_TO_SOURCE` registry gap so `is_pre_launch_date()` correctly
      classifies `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` against the floor. — **DONE**, `unified-api-contracts@46d865df`
      (see Resolution above).
- [ ] 2. [OPERATOR] P1. **Disposition ruling needed**: confirm the 83,541 pre-floor `FIXTURES_SCHEDULE`/
      `FIXTURES_OUTCOMES` objects should be WIPED per the standing sports-floor ruling (same disposition as every other
      pre-2020-06-06 sports artifact), not backfilled. Per-object detail is in the durable audit parquet (filter
      `obj_class == "E_orphan_real"` AND `data_type in ("FIXTURES_SCHEDULE","FIXTURES_OUTCOMES")` AND
      `day <     "2020-06-06"`). The GCS delete itself is human-only (delete-safety protocol).
- [ ] 3. [DATA] P2. Once ruled, run the delete-safety protocol's 5-part proof + execute the wipe (or, if the operator
      rules otherwise, document why these 83,541 are an exception to the standing floor policy — would need its own
      `AE-`-style taxonomy entry).
- [ ] 4. [REVIEW] P2. Re-run `migration_orphan_sweep_sports.py --bucket reference --dry-run` after the wipe to confirm
      these 83,541 no longer appear as `E_orphan_real` (either wiped from GCS, or now correctly classified `C3` if any
      remain pending the wipe) — closes the loop on the registry fix's real-world effect.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE** — the registry-gap fix (todo 1) is confirmed shipped and durable; the operator-gated
disposition (todos 2-4, the actual wipe) has NOT executed, so this is not yet resolvable to `resolved`.

Evidence (current code + git log, re-read 2026-07-23):

- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:240-241` —
  `"FIXTURES_SCHEDULE": "api_football"` and `"FIXTURES_OUTCOMES": "api_football"` are present in
  `SPORTS_DATA_TYPE_TO_SOURCE`, confirming `unified-api-contracts@46d865df` is on the branch and durable —
  `is_pre_launch_date()` now resolves a source for both data_types instead of silently returning `False`.
- Searched `market-tick-data-service`, `instruments-service`, and `unified-api-contracts` git history since 2026-07-22
  12:00 for any wipe/delete execution touching the 83,541 pre-floor `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows — found
  none. The only sports-manifest deletes in that window are `mtds@e9d9dec0` (the unrelated `source=api_football`
  wrong-source wipe, 1,266,874 rows, tracked by a different doc) and `mtds@f9f012cb` (a `soccer_*` phantom league_id
  prune, also a different doc/population).
- Todo 4 (re-run `migration_orphan_sweep_sports.py --dry-run` to confirm the 83,541 clear) has therefore also not run.

No conflict with another doc. This remains exactly where the doc's own todos 2-4 leave it: root cause fixed, human
disposition ruling + execution still outstanding.

## Lesson (do not re-learn)

A writer cutover that introduces new data_type constants must update **every** registry keyed on data_type, not just the
one the writer/reader path exercises directly. `gcs_paths.SPORTS_DATA_TYPE_TO_FOLDER` and
`league_data.SPORTS_DATA_TYPE_TO_SOURCE` are two independent tables serving different consumers (path resolution vs.
floor/source guards) — a split that updates one silently leaves the other's dependent logic (`is_pre_launch_date`,
`SOURCE_PRIORITY`, `AVAILABILITY_AT_SEMANTICS`) defensively permissive rather than loudly broken, which is precisely why
this went undetected for over a week (cutover 2026-07-14, found 2026-07-22).

## Duplicate-tracking note (2026-07-24)

This doc's 83,541-row population and disposition (todos 2-4: operator ruling, wipe, re-verify) are the SAME work as
`sports_consolidated_closeout_2026_07_19.md`'s Track V "decision 14" bullet (the pre-floor wipe todo). That bullet is
canonical — execute there, then flip todos 2-4 here as done citing the same evidence, rather than executing twice.
