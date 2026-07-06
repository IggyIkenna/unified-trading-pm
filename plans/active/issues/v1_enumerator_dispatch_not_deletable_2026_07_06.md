---
doc_type: issue
title: v1 _ENUMERATORS/main() dispatch in enumerate_expected_universe.py cannot be safely deleted — v2 depends on v1 for two documented slices
summary: |
  Filed 2026-07-06 as follow-up to cefi_layer1_denominator_gaps-010 (P2 hygiene "Confirm v1 is legacy → DELETE").
  Investigation confirmed v1 is NOT fully legacy: (1) v2 _enumerate_v2_sports EXPLICITLY delegates
  pre-source-coverage-start rows to v1 (per docstring at line 1552-1555, "date < the data_type source coverage
  start → SKIP — those dates are owned by the v1 _enumerate_sports pre-coverage rows"), (2)
  tests/integration/test_enumerate_v2_superset_property.py documents "tradfi v1 (non-trading days) is NOT a v2 grain
  match — v2 doesn't enumerate weekend/holiday cells" as an INTENTIONAL asymmetry, (3) v2 cefi/defi/prediction
  pre-launch coverage is per-instrument grain vs v1 venue-grain sentinel — backfills over new/empty catalogs would
  lose venue-grain PRE_VENUE_LAUNCH sentinel seeding, and (4) cross-repo cleanup required in deployment-service
  (launch-expected-universe-enumerator-vm.sh + launcher_registry.py "expected-universe-enum-" + vm_zombie_watchdog.py)
  which is INFRA role, outside data_engineering scope. Operator ruling (main-agent 2026-07-06, on BLK-0ac84889):
  BLOCK the full v1 deletion — v1 NOT safe to fully delete. Re-scope the parent hygiene task to defer deletion.
  Follow-up work needed: extend v2 to cover tradfi non-trading days + sports pre-source-coverage before v1 can be
  retired, and drive cross-repo infra cleanup.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [enumerator-hygiene, honest-coverage, v2-completion, deferred, cross-repo-cleanup]
related:
  [
    cefi_layer1_denominator_gaps_2026_07_03.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: infrastructure_master
priority: P2
source: cefi_layer1_denominator_gaps-010 (slot-10 planning, BLK-0ac84889 operator answer 2026-07-06)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
depends_on:
supersedes:
superseded_by:
---

## What I found

Task `cefi_layer1_denominator_gaps-010` (P2, "Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE
it") called for confirmation that the v1 dispatch surface in
`instruments-service/scripts/enumerate_expected_universe.py` was legacy and safe to delete. Investigation
disqualified the "delete" step:

1. **v2 sports explicitly delegates pre-source-coverage to v1.** `_enumerate_v2_sports` docstring (line 1552-1555):

   > `date < the data_type's source coverage start → SKIP — those dates are owned by the v1 _enumerate_sports
   > pre-coverage rows (EXPECTED_PRE_SOURCE_COVERAGE_START, league_id="" grain). v2 must NOT re-emit them or the
   > (data_type, date) cell is double-counted at two grains.`

   Deleting `_enumerate_sports` from v1 removes the ONLY seeder for `EXPECTED_PRE_SOURCE_COVERAGE_START` rows.

2. **tradfi non-trading days are v1-only.** `tests/integration/test_enumerate_v2_superset_property.py` documents
   (lines 26-27):

   > `tradfi v1 (non-trading days) is NOT a v2 grain match — v2 doesn't enumerate weekend/holiday cells (those are
   > venue-grain by design, not instrument-grain).`

   Deleting `_enumerate_tradfi` removes the tradfi calendar seeder used to mark weekend/holiday cells with
   `EXPECTED_NON_TRADING_DAY`.

3. **Pre-launch venue-grain sentinel is a v1 feature.** v1 cefi/defi/prediction enumerators emit ONE row per
   `(venue, data_type, day)` with blank `instrument_type=""` `instrument_id=""` for pre-launch dates. v2
   equivalents (`_enumerate_v2_cefi` etc.) DO emit `EXPECTED_PRE_VENUE_LAUNCH` (line 1054-1055 for cefi), but at
   PER-CATALOG-INSTRUMENT grain: no cataloged instrument alive in pre-launch → no row emitted. For a fresh
   asset_group whose historical catalog is empty during the pre-launch window, v2 would emit ZERO
   `EXPECTED_PRE_VENUE_LAUNCH` rows where v1 emits a full sentinel matrix. The superset property (documented in
   `test_enumerate_v2_superset_property.py`) holds only when the catalog contains ≥1 instrument overlapping the
   venue's pre-existence window — a condition that historical/reference-only asset groups do NOT satisfy.

4. **Cross-repo infra ties.** Deleting v1 leaves dangling references in `deployment-service` that are outside the
   `data_engineering` role scope:
   - `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` — invokes the enumerator without
     `--enumerator-version`, defaulting to v1
   - `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183` — registers
     `"expected-universe-enum-"` prefix → v1 launcher
   - `deployment-service/scripts/vm/vm_zombie_watchdog.py:627` — same prefix in the watchdog registry

## Why it matters

Deleting v1 without first extending v2 would silently drop three row classes from the enumeration output going
forward:

- `EXPECTED_PRE_SOURCE_COVERAGE_START` (sports, per-source pre-coverage dates)
- `EXPECTED_NON_TRADING_DAY` (tradfi weekends + holidays)
- Venue-grain `EXPECTED_PRE_VENUE_LAUNCH` sentinels for empty-catalog windows

Consumers of these rows include the honest-coverage classifier (rows carry `capture_status=empty_confirmed`, so
they PROPERLY reflect coverage in the Layer-1 denominator). A silent regression here compounds the exact class
of "silent placeholder" the honest-coverage model exists to eliminate. Detection would be indirect (a Layer-1
re-measure moving in the wrong direction weeks later, hard to attribute).

The original hygiene motivation (eliminate the second producer surface flagged by C2) remains valid, but the
prerequisite work is real: v2 must SUBSUME v1's residual roles before v1 can be retired.

## Recommended decision

Defer the v1 deletion until the four follow-on todos below are done. When done in order, they close the last v1
dependency and clear the way for a safe delete + cross-repo cleanup.

## Actionable todos

- [x] ✅ [CODE] P2. **Extend `_enumerate_v2_tradfi` to emit `EXPECTED_NON_TRADING_DAY` at venue-grain**
      (`instrument_type=""` `instrument_id=""`) — mirror v1 `_enumerate_tradfi`'s weekend/holiday walk via
      `is_non_trading_day` / `non_trading_day_reason`; add regression test asserting v2 output covers the same
      calendar cells v1 emits (repo: instruments-service).
      — 2026-07-06 slot-12: instruments-service@24f7716 (feature: 705deec code + 24f7716 tests).
        `_yield_v2_tradfi_non_trading_day_rows(date_axis, data_types)` helper mirrors v1
        `_enumerate_tradfi`'s (venue × non-trading-day × data_type) walk, emitted as `instrument_type=""` /
        `instrument_id=""` / `capture_status="empty_confirmed"` with reason `EXPECTED_WEEKEND` or
        `EXPECTED_HOLIDAY` from `non_trading_day_reason()`. `_enumerate_v2_tradfi` `yield from`s it before the
        per-instrument lifecycle pass. Regression test:
        `tests/integration/test_enumerate_v2_superset_property.py::test_tradfi_v2_covers_v1_non_trading_day_cells`
        (2024-07-01 → 2024-07-07 window spans Independence Day + Sat/Sun; verified v1=240 cells, v2=240 cells,
        missing=0). 14 pre-existing per-instrument tests updated to filter the new venue-grain rows via a
        `_drop_v2_tradfi_venue_grain(rows)` helper — the per-instrument assertions stay focused; the
        v1↔v2 parity is asserted by the new superset test. Full `bash scripts/quality-gates.sh` green (117s).
- [x] ✅ [CODE] P2. **Extend `_enumerate_v2_sports` to emit `EXPECTED_PRE_SOURCE_COVERAGE_START` at (source, data_type,
      date) grain** with `league_id=""` for dates before each source's `SOURCE_COVERAGE_START`; drop the "date <
      coverage start → SKIP" branch that currently defers to v1; update the docstring to reflect the new
      responsibility; add regression test asserting parity with v1 output on pre-coverage dates (repo:
      instruments-service).
      — 2026-07-06 slot-11: instruments-service@3d26351.
        `_yield_v2_sports_pre_source_coverage_rows(date_axis, data_types)` helper iterates the passed-in
        data_types, resolves `source = SPORTS_DATA_TYPE_TO_SOURCE.get(dt)` +
        `coverage_start = get_source_coverage_start(source, dt)` (honours the per-(source, dt)
        `DATA_TYPE_COVERAGE_START` override before falling back to source-wide `SOURCE_COVERAGE_START`),
        then emits ONE row per `(source, dt, day)` with `venue=source_key`, `league_id=""`,
        `instrument_type=""`, `instrument_id=""`, `reason="EXPECTED_PRE_SOURCE_COVERAGE_START"`.
        `_enumerate_v2_sports` `yield from`s it before the per-league loop. The per-league skip on
        pre-coverage dates is RETAINED (comment updated to point at the helper) to prevent (a) double-
        counting the (data_type, date) cell at two grains AND (b) fabricating expected_unattempted for
        alive leagues on dates the source could never have covered. Regression test:
        `tests/integration/test_enumerate_v2_superset_property.py::test_sports_v2_covers_v1_pre_source_coverage_cells`
        (picks the day before the earliest `SOURCE_COVERAGE_START`, asserts v2 covers every v1
        per-source pre-coverage cell on the mapped (source, dt) intersection — v1's Cartesian iteration
        also emits spurious un-mapped cells that v2 correctly omits). Existing v2 sports precov unit test
        in `tests/unit/scripts/test_build_instrument_catalogue.py` updated: pre-coverage date now yields
        exactly ONE per-source sentinel row instead of zero. Full `bash scripts/quality-gates.sh` green
        (95s), 238 enumerator unit tests pass.
- [ ] [CODE] P2. **Extend cefi/defi/prediction v2 enumerators to emit venue-grain
      `EXPECTED_PRE_VENUE_LAUNCH` sentinel rows** when the catalog is empty for a `(venue, day)` in the
      pre-launch window; single sentinel row per (venue, data_type, day) matching v1's grain; add regression
      test using an empty catalog (repo: instruments-service).
- [ ] [CODE] P2. **Retire deployment-service v1 launcher path** — remove
      `launch-expected-universe-enumerator-vm.sh`, delete the `"expected-universe-enum-"` entry from
      `launcher_registry.py` + `vm_zombie_watchdog.py`; verify no live scheduler still references the prefix
      (repo: deployment-service; role: **infra** — cross-craft handoff).
- [ ] [CODE] P2. **DELETE v1 dispatch surface from enumerate_expected_universe.py** — after the four todos
      above land: remove `_ENUMERATORS` dict, seven v1 functions (`_enumerate_tradfi` / `_enumerate_tradfi_indices`
      / `_enumerate_defi` / `_enumerate_defi_gas_fees` / `_enumerate_sports` / `_enumerate_cefi` /
      `_enumerate_prediction`), `main()` v1 branch, and `--enumerator-version=v1` choice (default flip to v2);
      refactor `tests/unit/scripts/test_enumerate_expected_universe.py` +
      `tests/integration/test_enumerate_v2_superset_property.py` to drop v1 references (repo:
      instruments-service).

## Progress Log

- **2026-07-06** — Issue filed by slot-10 planning after gap-010 investigation. Operator ruling
  (main-agent, BLK-0ac84889): "BLOCK the full v1 deletion — v1 is NOT safe to fully delete. Re-scope this task
  to defer the delete; file an issue doc noting the v1-cannot-be-deleted finding for operator review." Gap-010
  checkbox flipped to DEFERRED with pointer to this doc.
