---
doc_type: issue
title:
  v1 _ENUMERATORS/main() dispatch in enumerate_expected_universe.py cannot be safely deleted — v2 depends on v1 for two
  documented slices
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
last_updated: 2026-07-07
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

Task `cefi_layer1_denominator_gaps-010` (P2, "Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it")
called for confirmation that the v1 dispatch surface in `instruments-service/scripts/enumerate_expected_universe.py` was
legacy and safe to delete. Investigation disqualified the "delete" step:

1. **v2 sports explicitly delegates pre-source-coverage to v1.** `_enumerate_v2_sports` docstring (line 1552-1555):

   > `date < the data_type's source coverage start → SKIP — those dates are owned by the v1 _enumerate_sports pre-coverage rows (EXPECTED_PRE_SOURCE_COVERAGE_START, league_id="" grain). v2 must NOT re-emit them or the (data_type, date) cell is double-counted at two grains.`

   Deleting `_enumerate_sports` from v1 removes the ONLY seeder for `EXPECTED_PRE_SOURCE_COVERAGE_START` rows.

2. **tradfi non-trading days are v1-only.** `tests/integration/test_enumerate_v2_superset_property.py` documents (lines
   26-27):

   > `tradfi v1 (non-trading days) is NOT a v2 grain match — v2 doesn't enumerate weekend/holiday cells (those are venue-grain by design, not instrument-grain).`

   Deleting `_enumerate_tradfi` removes the tradfi calendar seeder used to mark weekend/holiday cells with
   `EXPECTED_NON_TRADING_DAY`.

3. **Pre-launch venue-grain sentinel is a v1 feature.** v1 cefi/defi/prediction enumerators emit ONE row per
   `(venue, data_type, day)` with blank `instrument_type=""` `instrument_id=""` for pre-launch dates. v2 equivalents
   (`_enumerate_v2_cefi` etc.) DO emit `EXPECTED_PRE_VENUE_LAUNCH` (line 1054-1055 for cefi), but at
   PER-CATALOG-INSTRUMENT grain: no cataloged instrument alive in pre-launch → no row emitted. For a fresh asset_group
   whose historical catalog is empty during the pre-launch window, v2 would emit ZERO `EXPECTED_PRE_VENUE_LAUNCH` rows
   where v1 emits a full sentinel matrix. The superset property (documented in `test_enumerate_v2_superset_property.py`)
   holds only when the catalog contains ≥1 instrument overlapping the venue's pre-existence window — a condition that
   historical/reference-only asset groups do NOT satisfy.

4. **Cross-repo infra ties.** Deleting v1 leaves dangling references in `deployment-service` that are outside the
   `data_engineering` role scope:
   - `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` — invokes the enumerator without
     `--enumerator-version`, defaulting to v1
   - `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183` — registers
     `"expected-universe-enum-"` prefix → v1 launcher
   - `deployment-service/scripts/vm/vm_zombie_watchdog.py:627` — same prefix in the watchdog registry

## Why it matters

Deleting v1 without first extending v2 would silently drop three row classes from the enumeration output going forward:

- `EXPECTED_PRE_SOURCE_COVERAGE_START` (sports, per-source pre-coverage dates)
- `EXPECTED_NON_TRADING_DAY` (tradfi weekends + holidays)
- Venue-grain `EXPECTED_PRE_VENUE_LAUNCH` sentinels for empty-catalog windows

Consumers of these rows include the honest-coverage classifier (rows carry `capture_status=empty_confirmed`, so they
PROPERLY reflect coverage in the Layer-1 denominator). A silent regression here compounds the exact class of "silent
placeholder" the honest-coverage model exists to eliminate. Detection would be indirect (a Layer-1 re-measure moving in
the wrong direction weeks later, hard to attribute).

The original hygiene motivation (eliminate the second producer surface flagged by C2) remains valid, but the
prerequisite work is real: v2 must SUBSUME v1's residual roles before v1 can be retired.

## Recommended decision

Defer the v1 deletion until the four follow-on todos below are done. When done in order, they close the last v1
dependency and clear the way for a safe delete + cross-repo cleanup.

## Actionable todos

- [x] ✅ [CODE] P2. **Extend `_enumerate_v2_tradfi` to emit `EXPECTED_NON_TRADING_DAY` at venue-grain**
      (`instrument_type=""` `instrument_id=""`) — mirror v1 `_enumerate_tradfi`'s weekend/holiday walk via
      `is_non_trading_day` / `non_trading_day_reason`; add regression test asserting v2 output covers the same calendar
      cells v1 emits (repo: instruments-service). — 2026-07-06 slot-12: instruments-service@24f7716 (feature: 705deec
      code + 24f7716 tests). `_yield_v2_tradfi_non_trading_day_rows(date_axis, data_types)` helper mirrors v1
      `_enumerate_tradfi`'s (venue × non-trading-day × data_type) walk, emitted as `instrument_type=""` /
      `instrument_id=""` / `capture_status="empty_confirmed"` with reason `EXPECTED_WEEKEND` or `EXPECTED_HOLIDAY` from
      `non_trading_day_reason()`. `_enumerate_v2_tradfi` `yield from`s it before the per-instrument lifecycle pass.
      Regression test:
      `tests/integration/test_enumerate_v2_superset_property.py::test_tradfi_v2_covers_v1_non_trading_day_cells`
      (2024-07-01 → 2024-07-07 window spans Independence Day + Sat/Sun; verified v1=240 cells, v2=240 cells, missing=0).
      14 pre-existing per-instrument tests updated to filter the new venue-grain rows via a
      `_drop_v2_tradfi_venue_grain(rows)` helper — the per-instrument assertions stay focused; the v1↔v2 parity is
      asserted by the new superset test. Full `bash scripts/quality-gates.sh` green (117s).
- [x] ✅ [CODE] P2. **Extend `_enumerate_v2_sports` to emit `EXPECTED_PRE_SOURCE_COVERAGE_START` at (source, data_type,
      date) grain** with `league_id=""` for dates before each source's `SOURCE_COVERAGE_START`; drop the "date <
      coverage start → SKIP" branch that currently defers to v1; update the docstring to reflect the new responsibility;
      add regression test asserting parity with v1 output on pre-coverage dates (repo: instruments-service). —
      2026-07-06 slot-11: instruments-service@3d26351.
      `_yield_v2_sports_pre_source_coverage_rows(date_axis, data_types)` helper iterates the passed-in data_types,
      resolves `source = SPORTS_DATA_TYPE_TO_SOURCE.get(dt)` + `coverage_start = get_source_coverage_start(source, dt)`
      (honours the per-(source, dt) `DATA_TYPE_COVERAGE_START` override before falling back to source-wide
      `SOURCE_COVERAGE_START`), then emits ONE row per `(source, dt, day)` with `venue=source_key`, `league_id=""`,
      `instrument_type=""`, `instrument_id=""`, `reason="EXPECTED_PRE_SOURCE_COVERAGE_START"`. `_enumerate_v2_sports`
      `yield from`s it before the per-league loop. The per-league skip on pre-coverage dates is RETAINED (comment
      updated to point at the helper) to prevent (a) double- counting the (data_type, date) cell at two grains AND (b)
      fabricating expected_unattempted for alive leagues on dates the source could never have covered. Regression test:
      `tests/integration/test_enumerate_v2_superset_property.py::test_sports_v2_covers_v1_pre_source_coverage_cells`
      (picks the day before the earliest `SOURCE_COVERAGE_START`, asserts v2 covers every v1 per-source pre-coverage
      cell on the mapped (source, dt) intersection — v1's Cartesian iteration also emits spurious un-mapped cells that
      v2 correctly omits). Existing v2 sports precov unit test in
      `tests/unit/scripts/test_build_instrument_catalogue.py` updated: pre-coverage date now yields exactly ONE
      per-source sentinel row instead of zero. Full `bash scripts/quality-gates.sh` green (95s), 238 enumerator unit
      tests pass.
- [x] ✅ [CODE] P2. **Extend cefi/defi/prediction v2 enumerators to emit venue-grain `EXPECTED_PRE_VENUE_LAUNCH`
      sentinel rows** when the catalog is empty for a `(venue, day)` in the pre-launch window; single sentinel row per
      (venue, data_type, day) matching v1's grain; add regression test using an empty catalog (repo:
      instruments-service). — 2026-07-07 slot-6: instruments-service@980f329. Added
      `_yield_v2_{cefi,defi,prediction}_pre_venue_launch_rows(date_axis, data_types)` helpers wired via `yield from` at
      the top of the respective v2 enumerators. cefi/prediction mirror v1 `_enumerate_{cefi,prediction}` (walk
      `VENUES_BY_ASSET_GROUP[<ag>]` × `{CEFI,PREDICTION}_VENUE_LAUNCH_DATES` × date × data_types, emit
      `EXPECTED_PRE_VENUE_LAUNCH` at instrument_type="" / instrument_id=""). defi mirrors v1 `_enumerate_defi` +
      `_enumerate_defi_gas_fees` (chain-level `gas_fees` pre-genesis at venue=ALCHEMY + per-(chain, protocol) pre-launch
      with `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_INSTRUMENT_NOT_LISTED`; chain-level data_types excluded from the
      per-protocol pass to avoid the ~142k `venue=<PROTOCOL>` phantom class). Renamed
      `_drop_v2_tradfi_venue_grain(rows)` → generic `_drop_v2_venue_grain(rows)` in the unit test file and applied it to
      ~30 per-instrument cefi/defi tests so their per-instrument row-count assertions stay focused (venue-grain rows
      have blank instrument_type/id — filter matches the existing tradfi convention). Regression tests added in
      `tests/integration/test_enumerate_v2_superset_property.py::test_{cefi,defi,prediction}_v2_covers_v1_pre_venue_launch_cells_with_empty_catalog`
      — assert v2 covers every v1 venue-grain pre-launch cell with `catalog=[]`. Fixed pre-existing filter bug in
      `test_defi_v2_covers_v1_pre_genesis_chain_cells` (v1 emits `venue=<PROTOCOL>` bare per the 2026-05 canonical
      naming SSOT, NOT `<PROTOCOL>-<CHAIN>` — filter now matches). Full `bash scripts/quality-gates.sh` green (110s);
      126 v2 unit tests + 92 catalogue/wiring tests + 8 superset property tests pass.
- [ ] **[PARKED — needs infra worker; do NOT dispatch to data_engineering]** [CODE] P2. **Retire deployment-service v1
      launcher path** — remove `launch-expected-universe-enumerator-vm.sh`, delete the `"expected-universe-enum-"` entry
      from `launcher_registry.py` + `vm_zombie_watchdog.py`; verify no live scheduler still references the prefix (repo:
      deployment-service; role: **infra** — cross-craft handoff). — 2026-07-06 slot-7 (data_engineering) PARKED with
      reason
      `craft-mismatch: infra task (deployment-service       VM launcher + Cloud Scheduler/Run coordination) dispatched to data_engineering slot`.
      Escalated via BLK-8b97bdfe, main-agent confirmed (2026-07-06): "self-park -004 ... Do NOT touch
      launch-expected-universe-enumerator-vm.sh, launcher_registry.py, vm_zombie_watchdog.py, or Cloud Scheduler/Run
      teardown." — **IMPORTANT for the infra worker who picks this up**: retiring the `expected-universe-enumerator-` /
      `cron:expected-universe-enumerator-` prefix ALSO requires updating the `continuous_verifier` field in **19 codex
      audit YAMLs** under `unified-trading-pm/codex/10-audit/repos/*.yaml` (each currently reads
      `continuous_verifier: "cron:expected-universe-enumerator- + manifest spot-check"`). Enumerate with
      `rg -l 'cron:expected-universe-enumerator-' unified-trading-pm/codex/10-audit/repos/`. Also review
      `deployment-service/scripts/vm/launch-ec2-vm.sh` line 148
      (`_register "expected-universe-enumerator" …       "eu-enum-" …`) — the AWS EC2 registration mirrors the GCP
      prefix and needs the same treatment. — **Blocked-by note**: todo #3 above (v2 venue-grain
      `EXPECTED_PRE_VENUE_LAUNCH` sentinel) is still `- [ ]`. If v1 is currently the sole producer of the venue-grain
      sentinel row class in prod, retiring the v1 launcher path BEFORE #3 lands silently drops that row class from the
      enumeration output — the exact "silent placeholder" class the honest-coverage model exists to eliminate. Infra
      worker should confirm with data_engineering that #3 is landed OR that no live scheduler still invokes the v1
      launcher, before completing the retirement.
- [ ] **[PARKED — prereqs #3 and #4 not landed]** [CODE] P2. **DELETE v1 dispatch surface from
      enumerate_expected_universe.py** — after the four todos above land: remove `_ENUMERATORS` dict, seven v1 functions
      (`_enumerate_tradfi` / `_enumerate_tradfi_indices` / `_enumerate_defi` / `_enumerate_defi_gas_fees` /
      `_enumerate_sports` / `_enumerate_cefi` / `_enumerate_prediction`), `main()` v1 branch, and
      `--enumerator-version=v1` choice (default flip to v2); refactor
      `tests/unit/scripts/test_enumerate_expected_universe.py` +
      `tests/integration/test_enumerate_v2_superset_property.py` to drop v1 references (repo: instruments-service).
      **2026-07-07 slot-11 (data_engineering)** — dispatcher routed -008 with todo #3 still `- [ ]` and todo #4 PARKED.
      Deleting v1 now silently drops the venue-grain PRE_VENUE_LAUNCH row class for empty-catalog windows (main-agent
      confirmed this is a data-correctness hard-stop, not a style preference). Slot-11 raised BLK-530cea75; main
      answered "implement todo #3 first, then #5". Slot-11 STARTED todo #3 (added
      `_yield_v2_cefi/defi/prediction_pre_venue_launch_rows` helpers + venue-grain wiring in
      `_enumerate_v2_cefi/defi/prediction` at `instruments-service/scripts/enumerate_expected_universe.py`), then
      reverted because todo #3 requires substantial existing-test refactoring (~10+ tests that assert row counts on
      pre-launch date_axis fail when the helper walks all venues in `VENUES_BY_ASSET_GROUP` / `PROTOCOL_LAUNCH_DATES` —
      any test using a date pre a venue/protocol launch gets extra venue-grain rows). Todo #3 needs its own dedicated
      dispatch cycle. Todo #4 (deployment-service launcher retirement) needs an infra-role worker. -008 stays PARKED
      until BOTH #3 and #4 land on LDR.

## Progress Log

- **2026-07-08** — **-009 RE-DISPATCHED (9TH SLOT BOUNCE) — SAME PARK** (slot-4 data_engineering). Re-verified
  independently against the current `.tabs/4` clones (fresh-pulled `instruments-service` to `be95c76` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` before checking): prereq #3 (v2 venue-grain sentinel) IS
  landed in `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line
  1007), `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope (per RULES.md craft-lines + the 2026-07-06
  main-agent ruling on BLK-0b46d0f3 / BLK-8b97bdfe). The underlying decision was already made (main-agent, BLK-530cea75
  / BLK-0ac84889: data-correctness hard-stop, do not delete v1 until BOTH prereqs land) — this is not a fresh ambiguity,
  so self-parking via `/skip-current-task` per the established precedent from bounces 3-8 rather than re-raising
  `/blocked`. **Systemic ask (9th bounce across 3 days — still unaddressed after 8 requests)**: operator/main-agent to
  either (a) set `priority: 999` + a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry
  keyed on prereq #4 landing, since `assigned_role: data_engineering` alone isn't stopping the bounce, or (b) dispatch
  an infra-role worker to close prereq #4 directly (removes the parked task's blocker entirely — the single
  highest-leverage fix available, unchanged advice from every prior bounce).
- **2026-07-08** — **-009 RE-DISPATCHED (8TH SLOT BOUNCE) — SAME PARK** (slot-2 data_engineering). Re-verified against
  the current `.tabs/2` clones (no new fetch needed — worktree already current): prereq #3 (v2 venue-grain sentinel) IS
  landed in `instruments-service/scripts/enumerate_expected_universe.py` (`_yield_v2_cefi_pre_venue_launch_rows` /
  `_yield_v2_defi_pre_launch_rows` / `_yield_v2_prediction_pre_venue_launch_rows` all present, wired via `yield from`).
  Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope (per RULES.md craft-lines + the prior 2026-07-06
  main-agent ruling on BLK-0b46d0f3). The underlying decision was already made (main-agent, BLK-530cea75 / BLK-0ac84889:
  data-correctness hard-stop, do not delete v1 until BOTH prereqs land) — this is not a fresh ambiguity, so self-parking
  via `/skip-current-task` per the established precedent from bounces 3-7 rather than re-raising `/blocked`. **Systemic
  ask (8th bounce across 3 days — still unaddressed after 7 requests)**: operator/main-agent to either (a) set
  `priority: 999` + a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on prereq
  #4 landing, since `assigned_role: data_engineering` alone isn't stopping the bounce, or (b) dispatch an infra-role
  worker to close prereq #4 directly (removes the parked task's blocker entirely — the single highest- leverage fix
  available, unchanged advice from every prior bounce).
- **2026-07-08** — **-009 RE-DISPATCHED (7TH SLOT BOUNCE) — SAME PARK** (slot-3 planning, resumed session). Verified
  against `origin/live-defi-rollout` tip `c8a5925a2`: prereq #3 (v2 venue-grain sentinel) IS landed
  (`instruments-service@980f329` — confirmed `_yield_v2_cefi_pre_venue_launch_rows` / `_yield_v2_defi_pre_launch_rows` /
  `_yield_v2_prediction_pre_venue_launch_rows` present in `scripts/enumerate_expected_universe.py`). Prereq #4 (infra
  launcher retirement) is STILL NOT landed — verified
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/launch-ec2-vm.sh:148`, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` all still reference the
  v1 `expected-universe-enum-`/`eu-enum-` prefix — this is an infra-role task, outside data_engineering scope, and no
  infra worker has picked it up across 2+ days. Checked the live `backlog.yaml`
  (`agent-orchestrator/data/config/backlog.yaml`, task `v1_enumerator_dispatch_not_deletable-009`): still `priority: 50`
  with an EMPTY `prereqs.completed_tasks`/`prerequisites` block — the systemic gate requested on the 4th/5th/6th bounces
  (a `priority: 999` + `conditions:` gate keyed on prereq #4 landing) has NOT been applied. Since the decision itself
  was already made by main-agent (data-correctness hard-stop, do not delete v1 until prereqs land — see BLK-530cea75 /
  BLK-0ac84889), this is not a fresh ambiguity to re-escalate via `/blocked`; self-parked via `/skip-current-task` per
  the established precedent from bounces 4-6. **Not fixing the systemic gate here** — editing `backlog.yaml` by hand is
  banned (it's a derived runtime artifact); the fix requires either an operator edit to the YAML
  `conditions:`/`priority` fields, or dispatching an infra-role worker to close prereq #4, which removes the parked
  task's blocker entirely. Recommend the latter: dispatching prereq #4 to any available infra slot resolves both the
  immediate parked task AND the recurring bounce (7 bounces and counting) in one move.
- **2026-07-07** — slot-6 (data_engineering) received -006 (venue-grain PRE_VENUE_LAUNCH sentinel) dispatch and shipped
  todo #3. Implementation followed slot-11's WIP notes (helpers per-asset-group; `yield from` at v2 enumerator top;
  `_drop_v2_venue_grain` filter refactor across ~30 per-instrument tests). Ship: instruments-service@980f329 (feature +
  filter refactor + 3 empty-catalog superset regression tests + 1 pre-existing defi filter-bug fix in the same test
  file). Full QG green (110s). Todos #4 (infra) and #5 (v1 DELETE) still gated per parent plan.
- **2026-07-07** — **-009 RE-DISPATCHED (6TH SLOT BOUNCE) — SAME PARK** (`BLK-fb4a4cb0`, slot-3 planning). Same root
  cause as the 5 prior bounces (slots 11 + 9 + 12 today, slots 7 + 8 on 2026-07-06): dispatcher re-issued -009 to slot-3
  even though the task's own text starts with `[PARKED — prereqs #3 and #4 not landed]` and this Progress Log documents
  the pattern across 6 bounces. Verified against `origin/live-defi-rollout` PM tip `4963e6b29`: prereq #3 (v2
  venue-grain sentinel, line 147) is still `- [ ]`; prereq #4 (infra launcher retirement, line 150) is still `- [ ]` and
  PARKED for infra worker. Slot-11's WIP helpers for #3 are NOT on LDR (reverted per session log; latest
  `instruments-service` LDR commits touching `scripts/enumerate_expected_universe.py` are `4a8cff7` and `3d26351`,
  neither adds `_yield_v2_cefi_pre_venue_launch_rows` / `_yield_v2_defi_pre_launch_rows` /
  `_yield_v2_prediction_pre_venue_launch_rows`). Executing the delete would silently drop the venue-grain
  `EXPECTED_PRE_VENUE_LAUNCH` row class for empty-catalog windows — main-agent already confirmed on `BLK-530cea75`
  (2026-07-07, slot-11) that this is a **data-correctness hard-stop**, not a style preference. Awaiting
  `/skip-current-task` on `BLK-fb4a4cb0`. **Systemic ask (6th bounce across 2 days — still unaddressed after 5
  requests)**: operator to set `priority: 999` + a `conditions:` gate on the -009 backlog entry keyed on the LDR-landing
  of BOTH #3 and #4 in `backlog.yaml`, so this stops burning slot-boot windows on a task whose own text says PARK.
  Follow-up (still needed): dispatch todo #3 (v2 venue-grain `EXPECTED_PRE_VENUE_LAUNCH` sentinel) as its own
  `-006`-style backlog task to a data_engineering slot — slot-11's session revert `instruments-service@2727dd7` is the
  WIP starting point.
- **2026-07-07** — **-009 RE-DISPATCHED (5TH SLOT BOUNCE) — SAME PARK** (`BLK-7237ea97`, slot-12 planning). Same root
  cause as the 4 prior bounces (slot-11 + slot-9 today, slots 7 + 8 on 2026-07-06): dispatcher re-issued -009 to slot-12
  even though the task's own text starts with `[PARKED — prereqs #3 and #4 not landed]` and this Progress Log documents
  the pattern across 5 bounces. Verified against `origin/live-defi-rollout` tip at commit `405ef9c4e`: prereq #3 (v2
  venue-grain sentinel, line 147) is still `- [ ]`; prereq #4 (infra launcher retirement, line 150) is still `- [ ]` and
  PARKED for infra worker. Executing the delete would silently drop the venue-grain `EXPECTED_PRE_VENUE_LAUNCH` row
  class for empty-catalog windows — main-agent already confirmed on `BLK-530cea75` (2026-07-07, slot-11) that this is a
  **data-correctness hard-stop**, not a style preference. Awaiting `/skip-current-task` on `BLK-7237ea97`. **Systemic
  ask (5th bounce across 2 days — still unaddressed after 4 requests)**: operator to set `priority: 999` + a
  `conditions:` gate on the -009 backlog entry keyed on the LDR-landing of BOTH #3 and #4 in `backlog.yaml`, so this
  stops burning slot-boot windows on a task whose own text says PARK. Follow-up (still needed): dispatch todo #3 (v2
  venue-grain `EXPECTED_PRE_VENUE_LAUNCH` sentinel) as its own `-006`-style backlog task to a data_engineering slot —
  slot-11 has a WIP starting point at `instruments-service@2727dd7` (session revert), and it is the actionable in-craft
  blocker for -009.
- **2026-07-07** — **-009 RE-DISPATCHED (4TH SLOT BOUNCE) — SAME PARK** (`BLK-035ed29a`, slot-9 planning). Same root
  cause as the 3 prior bounces (slot-11 today, slots 7 + 8 on 2026-07-06): dispatcher re-issued -009 to slot-9 even
  though the task's own text starts with `[PARKED — prereqs #3 and #4 not landed]` and the Progress Log below documents
  the pattern. Verified: prereq #3 (v2 venue-grain sentinel) is still `- [ ]` at PM tip; prereq #4 (infra launcher
  retirement) is PARKED. `/skip-current-task`. **Systemic ask (4th bounce across 2 days)**: operator to set
  `priority: 999` + a `conditions:` gate keyed on the LDR-landing of BOTH #3 and #4 in `backlog.yaml`, so this stops
  burning slot-boot windows on a task whose own text says PARK.
- **2026-07-07** — slot-11 (data_engineering) received -008 (DELETE v1) dispatch. Prereq #3 (v2 venue-grain sentinel) is
  `- [ ]` and prereq #4 (infra launcher retirement) is PARKED. Deleting v1 now would silently drop the venue-grain
  PRE_VENUE_LAUNCH row class for empty-catalog windows (`_enumerate_cefi` line 617 emits it, v2's per-instrument path
  requires ≥1 catalog instrument to emit anything). Slot-11 raised BLK-530cea75 to main. Main answered: "DO NOT delete
  v1 yet — data-correctness hard-stop. Implement todo #3 (in-craft) first; ship via quickmerge; then delete." Slot-11
  built the todo #3 helpers in-tree (`_yield_v2_cefi_pre_venue_launch_rows` / `_yield_v2_defi_pre_launch_rows` /
  `_yield_v2_prediction_pre_venue_launch_rows` walking `VENUES_BY_ASSET_GROUP` / `PROTOCOL_LAUNCH_DATES` and
  yielding-from at the top of each v2 enumerator; mirrors the tradfi/sports pattern from todo #1/#2) but REVERTED before
  ship: the helpers emit venue-grain sentinels for ALL pre-launch venues, breaking ~10+ existing per-instrument tests
  that assert on row counts using pre-launch date_axes (e.g. `test_cefi_v2_pre_venue_launch_beats_instrument_lifecycle`,
  `test_defi_v2_pre_chain_genesis_yields_pre_genesis`, `test_defi_v2_empty_catalog`, others). Full test refactor + the
  `_drop_v2_venue_grain(rows)` filter pattern is a dedicated dispatch cycle, not within -008's scope. Recommendation:
  dispatch **-006** (todo #3) to a data_engineering slot as its own unit; the helpers above are a WIP starting point
  (see slot-11 session revert on `instruments-service@2727dd7`). -008 PARKED with prereq marker; slot-11 idle after this
  note.
- **2026-07-06** — Issue filed by slot-10 planning after gap-010 investigation. Operator ruling (main-agent,
  BLK-0ac84889): "BLOCK the full v1 deletion — v1 is NOT safe to fully delete. Re-scope this task to defer the delete;
  file an issue doc noting the v1-cannot-be-deleted finding for operator review." Gap-010 checkbox flipped to DEFERRED
  with pointer to this doc.
- **2026-07-06** — slot-7 (data_engineering) received todo #4 dispatch, escalated via BLK-8b97bdfe with craft-mismatch
  reason (infra task in deployment-service dispatched to data_engineering). Main-agent confirmed self-park; annotated
  todo #4 with `[PARKED — needs infra worker]` marker plus a coordination note for the infra worker documenting (a) 19
  codex audit YAMLs still reference `cron:expected-universe-enumerator-` as `continuous_verifier`, (b)
  `deployment-service/scripts/vm/launch-ec2-vm.sh:148` also registers the AWS EC2 mirror `"eu-enum-"`, and (c) todo #3
  is a blocked-by if the v1 launcher is still actively scheduled in prod.
- **2026-07-06** — slot-8 (data_engineering) received the SAME todo #4 dispatch AGAIN (backlog task
  `v1_enumerator_dispatch_not_deletable-007`, tier=1 priority=50), despite the
  `[PARKED — needs infra worker; do NOT dispatch to data_engineering]` title marker added after slot-7's escalation.
  This is now the 2nd craft-mismatch dispatch to a data_engineering slot for this todo. Escalated via BLK-0b46d0f3;
  main-agent confirmed self-park with status `BLOCKED-CRAFT-SCOPE`. **Operator hardening ask (main-agent 2026-07-06)**:
  the title marker is not sufficient — the dispatcher ignores it. Operator must (1) set `assigned_role: infra` on the
  -007 backlog entry so data_engineering slots never receive it, AND (2) add a `depends_on` gate or prereq condition
  (e.g. a `v1-enumerator-007-role-gated` condition seeded `false` until an infra worker is available) so the row is
  blocked from dispatch until picked up by the correct craft. Until this is done, -007 will keep bouncing to
  data_engineering slots on every /boot. No deployment-service files touched from slot-8; the todo remains `- [ ]` for a
  real infra worker.
