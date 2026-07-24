---
doc_type: issue
title:
  Fixtures manifest atom migration (FIXTURES → FIXTURES_SCHEDULE/FIXTURES_OUTCOMES) — code shipped, but 337,464 legacy
  manifest rows still stamped the old atom; backfill needs a design decision, not a mechanical relabel
summary: >-
  sports_closeout_batch1_ao_ready_2026_07_24.md todo 1's writer/reader code migration shipped
  (instruments-service@e19c5a7a) — every NEW manifest write now uses FIXTURES_SCHEDULE/FIXTURES_OUTCOMES instead of the
  hardcoded "FIXTURES" literal, and the companion UAC SCHEDULE_DEFINING_DATA_TYPES change already shipped separately
  (unified-api-contracts@6d9c7b59). But the todo's own "Done when" clause (a corpus-wide manifest census returning zero
  data_type="FIXTURES" rows) is NOT met — a read-only prod census shows 337,464 legacy FIXTURES rows still in the sports
  manifest vs. 114,497 combined FIXTURES_SCHEDULE/FIXTURES_OUTCOMES rows. Closing this requires a genuine backfill with
  open design questions (not a mechanical find/replace) — see below.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, fixtures, manifest, data_type-atom, backfill, honest-coverage]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  found while shipping sports_closeout_batch1_ao_ready_2026_07_24.md todo 1 (fixtures manifest atom migration),
  2026-07-24
---

## What I found

**Code migration (shipped, `instruments-service@e19c5a7a`)**: every writer/reader call site named in
`sports_closeout_batch1_ao_ready_2026_07_24.md` todo 1 now emits/reads `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` instead
of the hardcoded `"FIXTURES"` literal — `sports_reference_fixtures.py`, `process_write.py`, `writers.py`,
`catalogue.py`, `process_completeness.py`, `process_preflight.py`, `process_zero_records.py`,
`sports_fixtures_daily_repoll.py`. QG green, sentinel-verified, shipped via quickmerge. The companion UAC change
(`SCHEDULE_DEFINING_DATA_TYPES` in `_honest_coverage_logic.py`) was already shipped separately
(`unified-api-contracts@6d9c7b59`) and is confirmed to read `frozenset({FIXTURES_SCHEDULE})`.

**Corpus census (read-only, 2026-07-24)**: invoked the sanctioned `deployment-api` axis-value-census logic directly
(`build_bucket_name("instruments-service", "sports")` + `read_availability_index(bucket, columns=[...])` — the same
bounded, column-pruned single read the `/data-status/axis-value-census` endpoint performs, single-walk-exempt per
`/codex/02-data/reconciliation-census-and-compute-tiers.md` §1.1) against the real prod bucket
`instruments-store-sports-prd-central-element-323112` (`row_count=5,526,420`). `data_type` axis result (relevant rows):

- `FIXTURES`: **337,464** (legacy atom — should be zero per the todo's Done-when clause)
- `FIXTURES_SCHEDULE`: 57,458
- `FIXTURES_OUTCOMES`: 57,039

**Why this isn't a mechanical relabel** (traced via
`unified-trading-library/unified_trading_library/manifest_writer/_rows.py` schema v9 +
`instruments-service/scripts/migrate_fixtures_split.py`):

1. **No per-row disambiguation signal exists in the manifest.** `ManifestRow`/`AvailabilityRecord` carries no
   `entity`/`gcs_path` column — `entity=` only ever existed as a GCS object-path segment, never captured into the
   manifest schema. A legacy `data_type="FIXTURES"` row cannot tell you on its own whether it should become
   `FIXTURES_SCHEDULE`, `FIXTURES_OUTCOMES`, or both.
2. **It's a 1-to-2 fan-out, not a 1:1 relabel.** `instruments-service/scripts/migrate_fixtures_split.py::_split_table`
   (already shipped for the GCS-object side, plan `sports_fixtures_schema_split_completion_2026_06_20.md`, `is@3f8b6a9`)
   splits each legacy `entity=fixtures` parquet into two parquets by column — schedule columns (`available_at`
   re-stamped to `announced_at`) and outcome columns (`available_at` re-stamped to `match_end_time`, or a stub for
   pre-Q6 data). A correct manifest backfill must therefore emit **two** new rows per legacy row, not overwrite
   `data_type` in place.
3. **That GCS-split script has zero `ManifestWriter`/`record_captured()` calls.** It only touches GCS objects. That is
   almost certainly why the 337,464 legacy manifest rows still exist even where the split may already have run at the
   object level — the manifest was never told.
4. **Row-filtering convention conflict.** The live writer (`sports_fixtures.py`, `home_score_regulation.notna()` gate)
   only writes an outcomes shard for _completed_ fixtures. The existing migration script writes an outcomes stub for
   _every_ row regardless of completion. A backfill script has to pick one convention — this is a genuine design call,
   not something a worker can resolve unilaterally.
5. **No delete/supersede step exists anywhere in the current tooling** — even after a correct backfill, old and new GCS
   objects/manifest rows would coexist unless a follow-up cleanup step is scoped too (consistent with the
   `gcs-and-manifest-delete-safety-protocol.md` human-gated-delete pattern).
6. Live per-row sampling of the 337,464 rows (e.g. are they ALL pre-2026-06-24, i.e. genuinely pre-cutover?) was not
   done in this pass — the plan-doc evidence (`sports_fixtures_schema_split_completion_2026_06_20.md` 2026-06-24 VERIFY
   note) is consistent with that, but should be confirmed before scoping the backfill.

## Why it matters

The plan's todo 1 "Done when" clause is not satisfied by the code-only migration — leaving it checked off would be a
false-progress plan-flip (the census result is real, reproducible, read-only-verified prod data). Downstream honest-
coverage consumers keyed on `SCHEDULE_DEFINING_DATA_TYPES` (now `{FIXTURES_SCHEDULE}`) will silently undercount schedule
coverage for any date/league whose only manifest record is still the legacy `FIXTURES` row, since that atom is no longer
in the schedule-defining set. This is a real (if likely bounded to historical/pre-cutover dates) honest- coverage gap,
not just a bookkeeping nit.

## Recommended decision

Operator/main-agent decision needed on:

1. **Confirm scope**: are all 337,464 legacy rows pre-2026-06-24 (pre schema-split cutover), or does the live writer
   still emit legacy `FIXTURES` under some code path today? (worth a quick grep-then-read before scoping the backfill —
   I did not find one, but didn't exhaustively rule it out.)
2. **Pick the outcomes-row convention** for the backfill: mirror the live writer (outcomes row only for completed
   fixtures) or the existing migration script (stub row for every legacy row regardless of completion)? Recommend
   mirroring the live writer — a stub outcomes row for an unplayed fixture is itself a small honest-absence violation.
3. **Decide the backfill mechanism**: extend `migrate_fixtures_split.py` to also call `ManifestWriter.record_captured()`
   for both split shards it writes (reusing its existing `(date, league)` GCS enumeration + `_split_table` logic), or
   write a separate manifest-only backfill that reads the now-existing `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` GCS
   objects (if the object-level split already ran) and just re-derives manifest rows from what's actually on disk.
4. Once (1)-(3) are decided, this becomes a properly-scoped, AO-dispatchable backfill todo (idempotent, SPOT-VM-eligible
   per the backfill HARD RULE) — file it as a new plan/todo at that point.

## Resolution (main, 2026-07-24, re BLK-61c182dc)

Main resolved the design autonomously (rapid-dev — these are codex-grounded data-architecture calls, not operator-owned;
operator wakes only for plan-unlock): (1) scope-confirm is a worker grep-then-read folded into the backfill pre-flight;
(2) outcomes-row convention = **mirror the live writer** (outcomes row only for completed fixtures,
`home_score_regulation.notna()`) — a stub row for an unplayed fixture is an honest-absence HARD-RULE violation, so the
choice is codex-dictated, not open; (3) mechanism = **re-derive both rows from the on-disk
`FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` GCS objects**, extending `migrate_fixtures_split.py` with
`ManifestWriter.record_captured()` only where the object-split hasn't run. The backfill is now a **dispatchable
`[DATA] P0` todo** in `/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md` (SPLIT out of that plan's code todo,
which is flipped ✅ for the shipped code scope). This issue doc stays the full analysis; the two todos below are
SUPERSEDED by that plan todo.

## Todos

- [x] [DATA] P1. ✅ SUPERSEDED (main 2026-07-24) — scope-confirm + convention are resolved above; folded into the
      dispatchable backfill todo's pre-flight in `/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md`.
- [x] [DATA] P1. ✅ SUPERSEDED (main 2026-07-24) — the manifest backfill is scoped + dispatchable as the `[DATA] P0`
      todo in `/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md` (main-resolved design; SPOT-VM; census-zero
      Done-when). Run + verify there.
