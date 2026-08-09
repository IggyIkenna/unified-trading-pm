---
doc_type: issue
title:
  reprobe_new_empty_confirmed.py's _DATE_COLUMNS priority picks blank `available_at` over populated `written_at`,
  silently returning zero new empties for defi
summary: >-
  Discovered while row-filter-testing the dp-reprobe-empty OOM fix
  (dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md) against the real defi manifest: `_DATE_COLUMNS
  = ("available_at", "date", "day", "written_at")` picks `available_at` first because it's the first name present in
  defi's schema — but its value is an EMPTY STRING for every empty_confirmed row in the real manifest (confirmed live,
  5/5 sampled SOURCE_RETURNED_ZERO rows). `_select_new_empties()`'s `pd.to_datetime(sub[date_col], errors="coerce",
  utc=True)` on an all-blank column coerces to NaT for every row, so the `sub_dates == day` mask is False for every row
  regardless of whether the cell genuinely became empty today — reprobe silently selects ZERO new empties for defi,
  every day, even after the OOM is fixed. `written_at` (last in the priority tuple, correctly populated with a real
  timestamp — e.g. `2026-07-28T00:24:48...+00:00`) is the column that actually reflects "when this row was written", but
  never gets picked because `available_at` is present (just empty) and short-circuits the `next(...)` lookup.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing]
scope: [engineer]
tags: [e2e-testing, data-pipeline, reprobe, self-healing, date-resolution, silent-failure]
related:
  [
    /plans/active/issues/dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
    e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py,
  ]
created: "2026-08-09"
author: data_engineering (slot 15)
parent_epic: observability_master
resolved_by: e2e-testing@9c75040
locked_by:
locked_since:
source: >-
  Found while implementing + verifying the row_filter OOM fix for
  dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md's CODE P1 todo — measuring the real defi
  manifest's SOURCE_RETURNED_ZERO rows surfaced `available_at` being blank for every one of them.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
archive_exempt: true
---

# reprobe's date-column resolution prefers a blank `available_at` over a populated `written_at`

> **🟢 ARCHIVED 2026-08-09 — RESOLVED** (status: resolved, 0 open todos, unlocked). Fixed (e2e-testing@9c75040):
> `_select_new_empties()` now resolves the date column via a new `_resolve_date_column()` helper that picks the first
> `_DATE_COLUMNS` entry present AND carrying ≥1 non-blank value among the candidate rows, instead of the first present
> NAME — so a wholesale-blank `available_at` no longer short-circuits past a populated `written_at`. Verified via a
> regression test (`test_reprobe_prefers_populated_written_at_over_blank_available_at`, `tests/unit/test_dp_audit.py`)
> reproducing this doc's exact fixture shape, plus a full green QG (178 tests, forced full re-run bypassing the content
> sentinel).

## What I found

`reprobe_new_empty_confirmed.py`'s `_select_new_empties()` resolves which column carries the "when" signal via
`next((c for c in _DATE_COLUMNS if c in cols), None)` — the FIRST name in
`_DATE_COLUMNS = ("available_at", "date", "day", "written_at")` present in the AG's schema, not the first one with a
genuinely useful (non-blank) value. Measured live against the real `market-data-tick-defi-prd-central-element-323112`
manifest (81.6M rows), sampling `SOURCE_RETURNED_ZERO` empty_confirmed rows directly via DuckDB:

```
available_at   written_at                       date
''             2026-07-28T00:24:48.451076+00:00 2021-10-01
''             2026-07-26T07:03:03.390399+00:00 2021-09-25
''             2026-07-26T07:03:34.833289+00:00 2021-09-26
```

`available_at` is present in defi's schema (so the `next(...)` lookup stops there) but is an empty string for every
sampled row. `_select_new_empties()` then does `pd.to_datetime(sub[date_col], errors="coerce", utc=True).dt.date` — an
empty string coerces to `NaT`, so `sub_dates == day` is `False` for every row, and the function returns an empty
candidate list regardless of whether a cell genuinely became `empty_confirmed`+`SOURCE_RETURNED_ZERO` TODAY.
`written_at` (last in the tuple, but the column that actually holds a real, populated timestamp reflecting when the row
was written) never gets picked because the `next(...)` short-circuits on the first present NAME, not the first present
VALUE.

`date` also has a real value, but it's the instrument's OWN date dimension (e.g. `2021-10-01`), not "when was this row
classified empty" — using it would silently select historical rows as if they were "new today", the opposite failure
mode.

## Why it matters

DP-FETCH-006's self-healing reclassify (`empty_confirmed` → `attempted_failed` on a proven misclassification) depends on
reprobe actually selecting TODAY's new empties. Even once the OOM regression (this doc's sibling) is fixed, defi's
reprobe pass will silently select ZERO candidates every day — not because there are none, but because the date-column
resolution picks the wrong (blank) column. This is a distinct silent-failure mode from the OOM: the job would exit 0,
log "0 new SOURCE_RETURNED_ZERO empties", and never surface as a problem unless someone specifically checks whether that
0 is genuine.

## Recommended decision

`_select_new_empties()`'s date-column resolution should prefer the first PRESENT AND NON-EMPTY column, not just the
first present name — e.g. check `cols` in order but also require the column not be all-blank for the AG (or simply try
each candidate in `_DATE_COLUMNS` order and skip past ones that are empty for the ACTUAL date the row is being tested
against). Alternatively, reorder `_DATE_COLUMNS` so `written_at` (the "when was this row written" signal every AG's
manifest schema reliably populates) is checked before `available_at`, if `available_at`'s blank-for-empty_confirmed
shape is a crosscutting pattern (not defi-specific) — verify against at least one other AG's real manifest before
reordering, since a per-AG override could otherwise regress an AG where `available_at` IS populated.

- [x] ✅ [CODE] P2. Fix `_select_new_empties()`'s date-column resolution in `reprobe_new_empty_confirmed.py` so it does
      not silently pick a present-but-blank `_DATE_COLUMNS` entry over a populated one — verify against the real defi
      manifest (today's date filter must actually match `SOURCE_RETURNED_ZERO` rows written today, not return zero
      candidates). Add a regression test using a fixture where `available_at` is present-but-blank and `written_at` is
      populated. (repo: e2e-testing) — e2e-testing@9c75040. Added `_resolve_date_column()` helper: picks the first
      `_DATE_COLUMNS` entry that is present AND has ≥1 non-blank value among the candidate rows, instead of the first
      present NAME — the `next(...)` short-circuit no longer stops on a wholesale-blank `available_at` before reaching a
      populated `written_at`. Regression test `test_reprobe_prefers_populated_written_at_over_blank_available_at` added
      to `tests/unit/test_dp_audit.py` (blank `available_at` + populated `written_at` fixture, asserts only the row
      whose `written_at` matches `day` is selected). Full QG (178 tests, forced full re-run bypassing the content
      sentinel) green on 9c75040.
