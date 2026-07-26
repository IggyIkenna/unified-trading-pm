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
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/archive/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md,
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
`[DATA] P0` todo** in `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md` (SPLIT out of that plan's
code todo, which is flipped ✅ for the shipped code scope). This issue doc stays the full analysis; the two todos below
are SUPERSEDED by that plan todo.

## Pre-flight findings (worker, 2026-07-24) — CORRECTS resolution point (3)

Ran the pre-flight scope-confirm grep-then-read main's resolution assigned to the backfill todo. Found the scope-confirm
was NOT clean (main's resolution assumed "expect zero post-`e19c5a7a`") — two real bugs, both fixed + shipped
(`instruments-service@47c1ffb3`, QG green):

1. **Live leak (now closed)**: `instruments-service/instruments_service/triggers/sports_fixture_status_refresh.py` (the
   stale-NS status-refresh cron trigger) still called `manifest.record_failed()`/`record_captured()` with the raw
   `"FIXTURES"` string literal — a 9th call site the original migration missed (it isn't in the todo's named-file list).
   This trigger runs regularly, so it was CONTINUOUSLY re-creating new legacy rows even after `e19c5a7a` shipped — any
   backfill run before this fix would have been chasing a moving target. Fixed to `FIXTURES_SCHEDULE` (imported from
   `unified_api_contracts.sports`), mirroring the sibling `sports_fixtures_daily_repoll.py` trigger's already-correct
   convention exactly (same import, same single-atom `record_captured`/`record_failed` shape — see its own module
   docstring). Two test assertions updated to match
   (`tests/unit/triggers/test_sports_fixture_status_refresh.py:218,536`).
2. **Silent mis-attribution (now closed)**: `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE`
   (`instruments_service/engine/orchestrator/__init__.py`) had no `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` keys — only
   the legacy `"FIXTURES"` key survived the migration. Any caller resolving pipeline_mode for the new atoms
   (`writers.py:270`, `_pipeline_mode_for_sports_data_type`) hit a `KeyError` caught by a bare
   `except KeyError: _venue_pm = PipelineMode.BATCH_INSTRUMENTS_SERVICE` fallback — not a crash, but a SILENT
   wrong-pipeline_mode stamp on every row that hit this path. Added both keys mapped to
   `PipelineMode.BATCH_API_FOOTBALL` (matching the retired `"FIXTURES"` entry, same source).

**Correction to resolution point (3) — the mechanism is simpler than assumed, not harder.** Exhaustive grep across every
repo for `FIXTURES_OUTCOMES` as a manifest `data_type=` write (not just the GCS `entity=` path label) found **zero live
call sites** — not in `instruments-service`, not in `migrate_fixtures_split.py`, nowhere. Both already-migrated sibling
call sites (`process_write.py`, `sports_fixtures_daily_repoll.py`) emit `record_captured()`/
`record_failed()`/`record_empty()` using `FIXTURES_SCHEDULE` ONLY — `FIXTURES_OUTCOMES` is a GCS-object-only label
(`entity=fixtures_outcomes/` partition), never a tracked manifest `data_type`. The established, PROVEN codebase
convention is: **one manifest atom per fixture-capture event (`FIXTURES_SCHEDULE`), not two.** So the backfill does
**not** need a 1-to-2 fan-out — it's a **1:1 in-place restamp** (`data_type: "FIXTURES"` → `"FIXTURES_SCHEDULE"`) on the
existing 337,464 rows, exactly mirroring the sibling `sports_closeout_batch1_ao_ready_2026_07_24.md` todo's
already-completed precedent: `market-tick-data-service/scripts/restamp_sports_odds_horizon_bucket_2026_07_22.py` (same
repo, same "re-stamp not delete" pattern — row-delete is verified-unsafe for this manifest, `_legacy_seed.parquet`
resurrection re-supplies deleted rows on the next consolidator merge). This removes point (3)'s "extend
`migrate_fixtures_split.py`" branch entirely — no GCS reads/re-derivation needed, no per-(date,league) enumeration, no
row-filtering convention question (point (2) is now moot: there is no outcomes row to conditionally emit at the manifest
level). Point (1) is resolved: the only found live-emitter was the trigger above, now fixed.

**Promoted verification tool** (was a scratchpad one-off; the backfill's own Done-when requires re-running this exact
census twice more — once right after the restamp, once after ≥2 consolidator cycles):
`deployment-api/scripts/census_manifest_data_type_2026_07_24.py` — read-only, sanctioned axis-value-census logic,
`--service`/`--asset-group`/--filter-prefix` args.

## Todos

- [x] [DATA] P1. ✅ SUPERSEDED (main 2026-07-24) — scope-confirm + convention are resolved above; folded into the
      dispatchable backfill todo's pre-flight in `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md`.
- [x] [DATA] P1. ✅ SUPERSEDED (main 2026-07-24) — the manifest backfill is scoped + dispatchable as the `[DATA] P0`
      todo in `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md` (main-resolved design; SPOT-VM;
      census-zero Done-when). Run + verify there.
- [x] ✅ [DATA] P0. **ACTION SHIPPED 2026-07-24, DONE-WHEN STILL BLOCKED (reconciled 2026-07-26, slot-5/review — see
      "Update (2026-07-26)" below for the full current picture).** The SIMPLIFIED 1:1 manifest restamp described here
      WAS already written and run in production — confirmed via `git log`: `instruments-service@e19c5a7a` (writer/reader
      migration), `instruments-service@e92efc78` (vectorized restamp script, verified 282,231 safe / 55,233 escalate / 0
      internal collisions on the real prod corpus), plus the restamp script itself
      (`instruments-service/scripts/restamp_fixtures_manifest_legacy_atom_2026_07_24.py`) and its actual `--apply` run
      documented in the sibling `fixtures_manifest_duplicate_collision_residual_2026_07_24.md`. **Do NOT write or re-run
      a new restamp script** — the action already shipped. The stated Done-when (census-zero `FIXTURES` rows) is NOT met
      and, per the 2026-07-26 update below, the reason is NOT simply the static 55,233 collision residual as originally
      scoped — see below for why. (repo: market-tick-data-service or instruments-service — whichever owns write access
      to the sports availability index; confirm via `_maintenance.py`'s existing
      `purge_venue_before_date()`/`rebuild_manifest()` precedent for which repo's script conventionally does this.) —
      **Related consumer-side gotcha found + separately patched 2026-07-25/26**: `--sports-entity FIXTURES`'s
      freshness-check routing in `instruments_service/engine/orchestrator/process_preflight.py` also keyed off the
      literal `"FIXTURES"` CLI string (not the `FIXTURES_SCHEDULE` constant), which meant an entity-scoped FIXTURES VM
      fell through to the coarse `check_shard_freshness` any-league-match path instead of a real per-league check — any
      single legacy `FIXTURES` row for a date (of which there are still ~337k per this doc) kept the WHOLE date "fresh"
      even when curated leagues added later were never captured. Patched narrowly via a
      `_FIXTURES_ENTITY_ALIASES = {"FIXTURES", FIXTURES_SCHEDULE}` routing fix (not a data restamp) — see
      `/plans/archive/issues/sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md`. This P0
      restamp is still the right long-term fix (retires the need for the alias set entirely); the routing patch is a
      stopgap that works correctly either way.

## Update (2026-07-26, slot-5/review — sports_satellite_ao_dispatch_batch4-002)

**Re-ran the sanctioned census**
(`deployment-api/scripts/census_manifest_data_type_2026_07_24.py --service instruments-service --asset-group sports --filter-prefix FIXTURES`,
live against `instruments-store-sports-prd-central-element-323112`):

```
FIXTURES_SCHEDULE: 461,881
FIXTURES_OUTCOMES: 102,086
FIXTURES:          100,801   (was 337,464 pre-restamp; expected to stabilize at ~55,233 per the collision-residual doc)
```

**Found the census did NOT stabilize at 55,233 — it's GROWING, not the static known residual.** Sampled the current
100,801 `FIXTURES` rows' `written_at` timestamps: 44,889 of them (44.5%) were written **TODAY (2026-07-26)**, in a
single burst at hour=01 UTC, all `service_name=instruments-service`, all `capture_status=expected_unattempted`, tagged
`enumerator_run_id='enum-universe-sports-20260726-013031'`. This is NOT the previously-fixed
`sports_fixture_status_refresh.py` trigger leak (`instruments-service@47c1ffb3`, a `record_captured`/`record_failed`
path) — it's a **10th, previously-unidentified call site**: the sports expected-universe enumerator
(`instruments-service/scripts/enumerate_expected_universe.py`) seeds `expected_unattempted` placeholder rows via
`_sports_manifest_data_type()`, whose `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` map had an entry for `ODDS_HORIZON_BUCKET`
but NONE for `FIXTURES` — so every enumerator run re-seeded tens of thousands of legacy `"FIXTURES"` rows via identity
fallback (`.get(dt, dt)`), growing the residual by ~45K in 2 days on top of the stable 55,233 collision-blocked
population. **Fixed** (`instruments-service@ca8bd7b3ab`): added `"FIXTURES": "FIXTURES_SCHEDULE"` to the override map,
mirroring the existing `ODDS_HORIZON_BUCKET` pattern exactly; updated
`tests/unit/scripts/test_enumerate_expected_universe_v2.py`'s
`test_sports_manifest_data_type_helper_identity_except_odds_horizon_bucket` (which had asserted the OLD, buggy identity
behavior for `FIXTURES` — removed it from the identity list) and added a new
`test_sports_manifest_data_type_helper_maps_fixtures_to_fixtures_schedule` regression test; 184/184 tests pass.

**Revised Done-when path**: once this fix's next enumerator run lands + the manifest consolidator catches up, the
`FIXTURES` census should decay toward the TRUE stable residual (55,233, tracked in
`fixtures_manifest_duplicate_collision_residual_2026_07_24.md`) rather than continuing to grow. Re-verify with the same
census command after the next `enum-universe-sports-*` run + ≥2 consolidator cycles. `status: open` left unchanged — the
underlying 55,233 collision-residual decision (delete vs. leave) is still unresolved in the sibling doc.
