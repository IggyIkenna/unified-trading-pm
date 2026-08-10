---
doc_type: issue
title:
  Sports golden-window (2025-09-01..2025-11-30) ODDS+PREDICTIONS blank-reason `empty_confirmed` residual — RE-MEASURED,
  0 blank cells remain (already resolved by prior shipped typing work)
summary: >-
  Re-measured `sports_satellite_ao_dispatch_batch9-003` / `data_completion_sports_2026_07_24.md`'s golden-window
  ODDS+PREDICTIONS blank-reason `empty_confirmed` residual (originally ~3,062 ODDS + 3,078 PREDICTIONS as of the
  2026-06-24 measurement, later ~3,255 combined) against the LIVE `instruments-store-sports-prd` manifest via a bounded,
  column-pruned + filtered read (no whole-corpus walk). Current state: **0 blank-reason cells remain** — every
  `empty_confirmed` cell in the window now carries a typed `EmptyConfirmedReason`. The relabeling was already closed out
  by prior shipped work (`reconcile_sports_blank_empty_reason_2026_06_24.py`,
  `type_footystats_odds_non_covered_leagues_2026_06_29.py`,
  `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`,
  `reclassify_oos_sports_expected_unattempted_2026_06_24.py`) between the original 2026-06-24 measurement and now.
  Read-only diagnosis — no code or manifest change made by this task.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, golden-window, empty-confirmed, blank-reason, honest-coverage, diagnosis, resolved]
related:
  [
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-09
author: slot-20 (data_engineering)
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P3
estimate_class: research
source: >-
  sports_satellite_ao_dispatch_batch9_2026_08_04.md todo (id sports_satellite_ao_dispatch_batch9-003), sourced from
  data_completion_sports_2026_07_24.md's golden-window P0 lock-in todo's "remaining unaddressed gaps" follow-on.
resolved_by: >-
  already resolved by prior shipped instruments-service typing work (reconcile_sports_blank_empty_reason_2026_06_24.py +
  type_footystats_odds_non_covered_leagues_2026_06_29.py +
  type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py +
  reclassify_oos_sports_expected_unattempted_2026_06_24.py); confirmed via this doc's 2026-08-09 live-manifest
  re-measurement (0 blank-reason cells found)
locked_by:
context_scope: [/codex/02-data/honest-coverage-model.md, /codex/02-data/availability-manifest-and-data-status.md]
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` at creation (measured residual is already 0, no fix needed), filed
> directly to `plans/archive/issues/` per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule (never lived at an active path). Resolution evidence carried in `resolved_by:`.

# Sports golden-window ODDS+PREDICTIONS blank-reason `empty_confirmed` residual — re-measured, resolved

## What I found

**Measurement method**: bounded read of the single live `_index/availability_index.parquet` manifest blob at
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (bucket resolved via
`resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`), projected to 5 columns
(`capture_status`, `venue`, `data_type`, `date`, `error_reason`) with row filters `data_type in (ODDS, PREDICTIONS)` and
`date` in `[2025-09-01, 2025-11-30]` applied at read time (`pd.read_parquet(..., filters=...)`) — a single-blob,
column-pruned, row-filtered read, not a new whole-corpus GCS walk. Run under `run-bounded-analysis.sh` (RSS-poll
fallback, 4G cap; peak usage well under cap).

**Result (measured 2026-08-09)**:

| data_type   | captured | empty_confirmed | attempted_failed | expected_unattempted |
| ----------- | -------- | --------------- | ---------------- | -------------------- |
| ODDS        | 1,067    | 3,663           | 0                | 0                    |
| PREDICTIONS | 1,065    | 7,671           | 0                | 0                    |
| **total**   | 2,132    | 11,334          | 0                | 0                    |

Full 91-date golden-window coverage confirmed (`date.nunique()==91`, min `2025-09-01`, max `2025-11-30` — no missing
dates). Single `venue=''` (footystats fixture/league-level granularity — no per-bookmaker venue axis for these two
data_types, expected structurally and unrelated to this residual).

**`empty_confirmed` by `error_reason`** (this is the residual metric the source todo asked about):

| error_reason                    | count |
| ------------------------------- | ----- |
| `EXPECTED_NO_FIXTURE`           | 7,330 |
| `EXPECTED_NO_PROVIDER_COVERAGE` | 3,277 |
| `EXPECTED_POST_SEASON`          | 378   |
| `EXPECTED_PRE_SEASON`           | 349   |
| **blank / untyped**             | **0** |

**Zero blank-reason cells remain.** The originally-reported ~3,062 (ODDS) + 3,078 (PREDICTIONS) ≈ 6,140 blank-reason
cells (later ~3,255 combined per the 2026-06-24 DONE-entry re-check) from the 2026-06-24 measurement have all since been
typed. This is not a new fix — it was already closed by shipped work landed between 2026-06-24 and now:

- `instruments-service/scripts/reconcile_sports_blank_empty_reason_2026_06_24.py` — types legacy blank `empty_confirmed`
  cells fixture-pinned (footystats ODDS/PREDICTIONS/MATCHES): no fixture on the (league, day) → `EXPECTED_NO_FIXTURE`;
  fixture exists but source returned zero → `SOURCE_RETURNED_ZERO`.
- `instruments-service/scripts/type_footystats_odds_non_covered_leagues_2026_06_29.py` and
  `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py` — type footystats ODDS/PREDICTIONS/MATCHES
  cells for leagues footystats does not cover as `EXPECTED_NO_PROVIDER_COVERAGE`.
- `instruments-service/scripts/reclassify_oos_sports_expected_unattempted_2026_06_24.py` — types out-of-season cells
  `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`.

The measured reason distribution (`EXPECTED_NO_FIXTURE` dominant, plus `EXPECTED_NO_PROVIDER_COVERAGE` +
pre/post-season) is consistent with exactly this set of scripts having run against the golden window's legacy blanks.
This task did not re-run or verify any of those scripts directly (out of scope — read-only diagnosis); it only confirms
their combined effect against the live manifest today.

## Why it matters

The source plan (`data_completion_sports_2026_07_24.md`) carried this as an open P2 follow-on gap since 2026-06-24. It
is not a live gap — the fleet's normal typing/reclassification work already closed it out. Leaving the todo open
indefinitely would have kept inviting re-diagnosis (as this very re-measurement task shows) of an already-resolved
issue. Confirming and recording the resolved state here lets both the source todo and this task's own todo close cleanly
with evidence, instead of leaving a stale "P2 residual" line item live in the plan corpus.

## Recommended decision

No fix needed — the residual is already fully resolved.

- `data_completion_sports_2026_07_24.md`'s originating P2 todo (line ~487, "Re-measure the golden-window ... residual")
  should likewise be flipped/struck citing this doc's measurement, by whoever next touches that plan — not done here
  since this task's scope is the batch9 todo, not a second plan's checkbox (avoid an unrequested cross-plan edit).
