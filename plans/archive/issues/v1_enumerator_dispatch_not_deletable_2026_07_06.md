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
status: resolved # was: "open" — corrected 2026-07-12, doc-reconciliation finding 62, §A2 B-queue ruling: all 5 actionable todos [x], instruments-service@b0859183 (verified) ships the final one; body's own Progress Log already declared "this issue doc's actionable-todo list is fully closed"
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [enumerator-hygiene, honest-coverage, v2-completion, deferred, cross-repo-cleanup]
related:
  [
    /plans/active/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-09
parent_epic: infrastructure_master
priority: P2
source: cefi_layer1_denominator_gaps-010 (slot-10 planning, BLK-0ac84889 operator answer 2026-07-06)
assigned_vm: planning
resolved_by:
  "instruments-service@b0859183 (all 5 todos [x] verified) — status synced 2026-07-12, finding 62, §A2 B-queue ruling"
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
sequential: true
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
      (venue, `data_type`, day) matching v1's grain; add regression test using an empty catalog (repo:
      instruments-service). — 2026-07-07 slot-6: instruments-service@980f329. Added
      `_yield_v2_{cefi,defi,prediction}_pre_venue_launch_rows(date_axis, data_types)` helpers wired via `yield from` at
      the top of the respective v2 enumerators. cefi/prediction mirror v1 `_enumerate_{cefi,prediction}` (walk
      `VENUES_BY_ASSET_GROUP[<ag>]` × `{CEFI,PREDICTION}_VENUE_LAUNCH_DATES` × date × `data_types`, emit
      `EXPECTED_PRE_VENUE_LAUNCH` at `instrument_type`="" / `instrument_id`=""). defi mirrors v1 `_enumerate_defi` +
      `_enumerate_defi_gas_fees` (chain-level `gas_fees` pre-genesis at venue=ALCHEMY + per-(chain, protocol) pre-launch
      with `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_INSTRUMENT_NOT_LISTED`; chain-level `data_types` excluded from the
      per-protocol pass to avoid the ~142k `venue=<PROTOCOL>` phantom class).

      Renamed `_drop_v2_tradfi_venue_grain(rows)` → generic `_drop_v2_venue_grain(rows)` in the unit test file and
                                                                  applied it to ~30 per-instrument cefi/defi tests so their per-instrument row-count assertions stay focused
                                                                  (venue-grain rows have blank `instrument_type`/id — filter matches the existing tradfi convention). Regression
                                                                  tests added in
                                                                  `tests/integration/test_enumerate_v2_superset_property.py::test_{cefi,defi,prediction}_v2_covers_v1_pre_venue_launch_cells_with_empty_catalog`
                                                                  — assert v2 covers every v1 venue-grain pre-launch cell with `catalog=[]`. Fixed pre-existing filter bug in
                                                                  `test_defi_v2_covers_v1_pre_genesis_chain_cells` (v1 emits `venue=<PROTOCOL>` bare per the 2026-05 canonical
                                                                  naming SSOT, NOT `<PROTOCOL>-<CHAIN>` — filter now matches). Full `bash scripts/quality-gates.sh` green (110s);
                                                                  126 v2 unit tests + 92 catalogue/wiring tests + 8 superset property tests pass.

- [x] ✅ [INFRA] P2. **Retire deployment-service v1 launcher path** — remove
      `launch-expected-universe-enumerator-vm.sh`, delete the `"expected-universe-enum-"` entry from
      `launcher_registry.py` + `vm_zombie_watchdog.py`; verify no live scheduler still references the prefix (repo:
      deployment-service; role: **infra** — cross-craft handoff). — 2026-07-09 slot-6 (infra):
      deployment-service@f45f89a (delete launcher script) + @466f4c6 (registry entries + dead dispatch branch) +
      @dc67a61 (restore TID251/RUF100 noqa dropped by prek autofix collateral, unrelated fix). Prereq #3 (v2 venue-grain
      sentinel) confirmed landed before starting (instruments-service@980f329, see todo #3 above). Verified no live
      Cloud Scheduler/Terraform job references the v1 prefix — only
      `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf` exists, no v1 equivalent. Removed: GCP
      launcher script + `launcher_registry.py` `"expected-universe-enum-"` entry + `vm_zombie_watchdog.py`
      `"expected-universe-enum-"` entry + `vm_zombie_watchdog_aws.py` `"eu-enum-"` entry + `launch-ec2-vm.sh`
      `_register "expected-universe-enumerator" … "eu-enum-" …` AWS mirror + the now-unreachable
      `expected-universe-enum` branch in `setup-data-pipeline-vm.sh` (v2 uses a different VM_TASK, unaffected). Also
      updated the `continuous_verifier` field in the 19 codex audit YAMLs
      (`cron:expected-universe-enumerator- + manifest spot-check` → `cron:expected-universe-v2- + manifest spot-check`,
      this same commit — see PM commit below). Full `bash scripts/quality-gates.sh` green (65s), sentinel verified,
      shipped via `quickmerge --agent --files`.
- [x] ✅ [CODE] P2. **DELETE v1 dispatch surface from enumerate_expected_universe.py** — after the four todos above
      land: remove `_ENUMERATORS` dict, seven v1 functions (`_enumerate_tradfi` / `_enumerate_tradfi_indices` /
      `_enumerate_defi` / `_enumerate_defi_gas_fees` / `_enumerate_sports` / `_enumerate_cefi` /
      `_enumerate_prediction`), `main()` v1 branch, and `--enumerator-version=v1` choice (default flip to v2); refactor
      `tests/unit/scripts/test_enumerate_expected_universe.py` +
      `tests/integration/test_enumerate_v2_superset_property.py` to drop v1 references (repo: instruments-service). —
      **2026-07-09 slot-7 (data_engineering)**: instruments-service@b0859183. Both prereqs (#3 v2 venue-grain sentinels,
      #4 deployment-service launcher retirement) were independently re-verified landed on a fresh pull before starting
      (26th dispatch of this park, first time both were actually true — see Progress Log for prior 25 bounces). Deleted
      `_ENUMERATORS` + all 7 v1 functions, kept the 3 helpers v2 also depends on (`_DEFI_CHAIN_LEVEL_DATA_TYPES` /
      `_GAS_FEE_VENUE` / `_gas_fee_chain_names`), flattened `main()`'s `if enumerator_version == "v2":` wrapper (dead
      branch removed, so the `-> int` return type stays satisfied without a v1 else), flipped `--enumerator-version` to
      `choices=["v2"], default="v2"`, and dropped the now-dead `manifest_df` param + column-alignment branch on
      `_write_absent_rows` (only the v1 caller ever passed it). Refactored both named test files: removed the 13 v1-only
      enumerator tests + the 2 `_ENUMERATORS`-keyed cross-asset-group invariant tests from
      `test_enumerate_expected_universe.py` (already covered by `test_enumerate_expected_universe_v2.py`'s v2
      equivalents — verified `test_v2_all_reasons_in_closed_set` + the `_V2_ENUMERATORS` dispatch-completeness test
      exist there first); deleted `test_enumerate_v2_superset_property.py` entirely since every test in it except one
      called a deleted v1 function — its whole purpose (prove v2 ⊇ v1) is moot once v1 doesn't exist. Also found + fixed
      a live breakage `git grep` surfaced outside the two named files:
      `tests/unit/scripts/test_enumerate_total_universe_wiring.py::test_v1_dispatch_equals_uac_total_universe_axes`
      asserted on `enumerator_module._ENUMERATORS` directly — removed. Scrubbed dangling docstring pointers to the
      deleted superset-property file (4 in the script, 4 in `test_enumerate_expected_universe_v2.py`) and updated the
      module docstring's per-asset-group implementation-status table + CLI examples (default is now v2, which requires
      `--catalog-path`). 156/156 tests pass in the 3 touched+kept test files; full test collection (4511 tests) clean;
      `bash scripts/quality-gates.sh` green (108s, sentinel-verified); shipped via `quickmerge --agent --files`. Prereq
      #1 (extend-v2-tradfi), #2 (extend-v2-sports), #3, #4, and this todo #5 are now ALL done — this issue doc's
      actionable-todo list is fully closed. **2026-07-07 slot-11 (data_engineering)** — dispatcher routed -008 with todo
      #3 still `- [ ]` and todo #4 PARKED. Deleting v1 now silently drops the venue-grain PRE_VENUE_LAUNCH row class for
      empty-catalog windows (main-agent confirmed this is a data-correctness hard-stop, not a style preference). Slot-11
      raised BLK-530cea75; main answered "implement todo #3 first, then #5". Slot-11 STARTED todo #3 (added
      `_yield_v2_cefi/defi/prediction_pre_venue_launch_rows` helpers + venue-grain wiring in
      `_enumerate_v2_cefi/defi/prediction` at `instruments-service/scripts/enumerate_expected_universe.py`), then
      reverted because todo #3 requires substantial existing-test refactoring (~10+ tests that assert row counts on
      pre-launch date_axis fail when the helper walks all venues in `VENUES_BY_ASSET_GROUP` / `PROTOCOL_LAUNCH_DATES` —
      any test using a date pre a venue/protocol launch gets extra venue-grain rows). Todo #3 needs its own dedicated
      dispatch cycle. Todo #4 (deployment-service launcher retirement) needs an infra-role worker. -008 stays PARKED
      until BOTH #3 and #4 land on LDR.

## Progress Log

- **2026-07-09** — **TODO #4 SHIPPED — infra worker finally routed correctly, 25 bounces later** (slot-6 infra,
  `v1_enumerator_dispatch_not_deletable-010`, the 24th-bounce `[INFRA]`-tag-position fix landed and this dispatch was
  the first to actually route to an `infra` slot instead of bouncing back to `data_engineering`). Fresh-pulled all
  slot-6 repos; confirmed prereq #3 (v2 venue-grain sentinel) landed (`instruments-service@980f329`,
  `_yield_v2_cefi/defi/prediction_pre_venue_launch_rows` present + wired). Confirmed no live Cloud Scheduler/Terraform
  job references the v1 prefix (`deployment-service/terraform/gcp/` has `expected_universe_v2_scheduler.tf` only, no v1
  equivalent — safe to retire). Removed the v1 GCP launcher script + the `"expected-universe-enum-"`/`"eu-enum-"`
  registry entries from `launcher_registry.py`, `vm_zombie_watchdog.py`, `vm_zombie_watchdog_aws.py`, `launch-ec2-vm.sh`
  (AWS mirror), and the now-dead `expected-universe-enum` dispatch branch in `setup-data-pipeline-vm.sh` — shipped as
  `deployment-service@f45f89a` + `@466f4c6`. Also updated the `continuous_verifier` field in all 19 codex audit YAMLs
  (`cron:expected-universe-enumerator-` → `cron:expected-universe-v2-`, this PM commit). **Self-inflicted detour, fixed
  same session**: the `466f4c6` commit's prek ruff-autofix pass silently stripped two pre-existing `# noqa: TID251`
  markers on `google.cloud`/`boto3` imports in `vm_zombie_watchdog.py`/`vm_zombie_watchdog_aws.py` as an unrelated side
  effect (RUF100 "unused noqa" — the repo's default `pyproject.toml` ruff select doesn't enable TID251, but the isolated
  STEP 5.95 ratchet checker (`check_ruff_rule_ratchet.py`) DOES select it explicitly, so the suppression is load-bearing
  there). First re-run of `quality-gates.sh` caught this (STEP 5.95 failed: tid251 14 > baseline 13). Restored using the
  established `# noqa: TID251,RUF100 — reason` double-code pattern already in use at
  `deployment_service/backends/aws_census.py:39` (RUF100 suppresses ruff's own "unused" complaint under the local
  default config) — shipped as `deployment-service@dc67a61`. Verified
  `check_ruff_rule_ratchet.py --scope deployment-service` reports `tid251: 13 (== baseline)`, `dtz: 7 (== baseline)`
  before re-running full QG (green, 65s, sentinel matched HEAD). **Lesson for future infra workers touching import lines
  near an existing `# noqa: TID251` comment in this repo**: the local `ruff check`/prek hook alone is NOT sufficient to
  validate a TID251 noqa — it will happily "fix" (strip) it as unused, since TID251 isn't in this repo's own pyproject
  select. Always also run `check_ruff_rule_ratchet.py --scope <repo>` (or the full `quality-gates.sh` STEP 5.95) before
  trusting a green `ruff check`.
- **2026-07-09** — **-010 RE-DISPATCHED (24TH SLOT BOUNCE) — ROOT CAUSE OF THE 23RD-BOUNCE FIX FAILURE FOUND + FIXED**
  (slot-3 data_engineering). Booted and received `v1_enumerator_dispatch_not_deletable-010` — the regen'd successor to
  `-009` after the 23rd-bounce systemic fix (commit `8e4ea0058`, 2026-07-09T15:42:56Z) retagged todo #4 `[CODE]` →
  `[INFRA]` in this doc. `-010`'s own title/brief correctly SHOW the `[INFRA]` tag text
  (`queued_at 2026-07-09T15:46:54Z`, i.e. regen'd AFTER the fix landed) — yet the backlog row still carried
  `dispatched_to: 3` and the `/boot` response still reported `"assigned_role":"data_engineering"`, meaning the retag did
  NOT actually change routing. Root-caused by reading `agent-orchestrator/server/regen_backlog_from_plan.py`:
  `_TAG_RE = re.compile(r"^\s*\[([A-Z]+)\]")` (line 691) only matches when `[TAG]` is the FIRST thing in the todo's
  description string — and `_parse_open_todos` sets `description = m.group(1).strip()` from the raw
  `- [ ] <description>` text with no stripping of leading bold/marker text. The 23rd-bounce edit placed `[INFRA]` AFTER
  the `**[PARKED — needs infra worker; do NOT dispatch to data_engineering]**` prefix
  (`- [ ] **[PARKED …]** [INFRA] P2. …`), so `_TAG_RE.match(description)` saw `**[PARKED` first, never matched `[A-Z]+`,
  and `_task_role_from_tag` silently fell through to `plan_role` (this doc's frontmatter
  `assigned_role: data_engineering`) — reproducing the exact bounce the fix was meant to close. **Fix applied THIS
  bounce** (doc-only, no orchestrator code touched — same category of change as the 23rd-bounce fix): reordered todo
  #4's line to `- [ ] [INFRA] **[PARKED — …]** P2. **Retire deployment-service v1 …` so `[INFRA]` is the first token
  after the checkbox, matching `_TAG_RE` at position 0. `_PRIORITY_RE.search()` (P-tag extraction) is unaffected — it
  uses `.search`, not `.match`, so it's position-independent and still finds `P2.` after the reordering. No other open
  todo in this doc needs the same fix: todo #5 (`-009`, DELETE v1) carries `[CODE]` which is UNMAPPED in `_TAG_TO_ROLE`
  (only `INFRA` / `DATA` / `BACKEND` / `UI` / `REVIEW` are mapped) and correctly falls through to the plan's
  `data_engineering` role regardless of position, so it was never affected by this bug. Self-parked -010 via
  `/skip-current-task` (craft-mismatch, established precedent) — the fix should take effect on the next `PlanRegenLoop`
  tick / next dispatch of the regenerated todo-#4 task, watch for it landing on an `infra` slot next time instead of
  bouncing back here. If it bounces again with `[INFRA]` still not routing, the bug is deeper than tag position (e.g.
  `_TAG_TO_ROLE` map not being consulted at dispatch time at all, only at task-creation time when the role field is
  first written and never re-read) — that would need an agent-orchestrator code fix, outside data_engineering craft
  scope, and should route to an infra/backend worker via `/blocked` rather than another doc-only park.
- **2026-07-09** — **-009 RE-DISPATCHED (23RD SLOT BOUNCE) — SYSTEMIC FIX APPLIED, SAME PARK** (slot-5
  data_engineering). Re-verified independently against a fresh `.tabs/5` pull (`instruments-service@f136eec0`,
  `deployment-service@a1bf966` on `live-defi-rollout`): prereq #3 (v2 venue-grain sentinel) confirmed landed
  (`_yield_v2_cefi_pre_venue_launch_rows` line 1061, `_yield_v2_defi_pre_launch_rows` line 1269 present, wired via
  `yield from`). Prereq #4 (infra launcher retirement) still NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, `scripts/vm/launch-ec2-vm.sh:148` still reference the v1 prefix;
  `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists. Rather than bounce a 23rd identical note, applied
  the systemic fix every prior bounce (3 through 22) recommended, using mechanisms already supported by
  `regen_backlog_from_plan.py` (no `backlog.yaml` hand-edit — this is a plan-doc frontmatter/tag change, which the
  backend derives from): (1) retagged todo #4's checkbox from `[CODE]` → `[INFRA]` — `_TAG_TO_ROLE` maps `INFRA` →
  `infra`, so the per-task role resolution now assigns todo #4 to the `infra` craft and the dispatcher will stop
  offering it to `data_engineering` slots (root cause of the parallel todo-#4 bounces documented in the 2026-07-06
  slot-7/slot-8 entries below); (2) added `sequential: true` to this doc's frontmatter — `regen`'s
  `_wire_sequential_prereqs` chains each remaining unchecked todo's backlog task to its immediate predecessor by
  `plan_order` within the plan, so todo #5 (-00X, DELETE v1) will get `prereqs.completed_tasks` wired to todo #4's task
  id on the next regen tick and stop being dispatched until an infra worker actually completes todo #4 — turning the
  22-bounce prose-only PARK into a structural gate. Self-parked via `/skip-current-task` (decision already made, not a
  fresh ambiguity). No code touched; only this issue doc edited. Next regen tick should confirm the gate landed (watch
  for todo #4 dispatching to an `infra` slot instead of `data_engineering`, and todo #5/-0XX no longer bouncing here).
- **2026-07-09** — **-009 RE-DISPATCHED (22ND SLOT BOUNCE) — SAME PARK** (slot-2 data_engineering). Re-verified
  independently against a fresh `.tabs/2` pull (`instruments-service` to `f136eec0`, `deployment-service` to `a1bf966`
  on `live-defi-rollout`): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1061),
  `_yield_v2_defi_pre_launch_rows` (line 1269), `_yield_v2_prediction_pre_venue_launch_rows` (line 2084) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-21.
  **Systemic ask (22nd bounce across 3 days — still unaddressed after 21 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-09** — **-009 RE-DISPATCHED (21ST SLOT BOUNCE) — SAME PARK** (slot-3 data_engineering). Re-verified
  independently against a fresh `.tabs/3` pull (`instruments-service` to `bac235a3`, `deployment-service` to `a1bf966`
  on `live-defi-rollout`, both later than the 20th bounce's tips): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1061),
  `_yield_v2_defi_pre_launch_rows` (line 1269), `_yield_v2_prediction_pre_venue_launch_rows` (line 2084) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183` and
  `scripts/vm/vm_zombie_watchdog.py:627` still reference the v1 `expected-universe-enum-` prefix, and
  `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists. This is an infra-role task, outside
  `data_engineering` craft scope. The underlying decision was already made — this is not a fresh ambiguity, so
  self-parking via `/skip-current-task` per the established precedent from bounces 3-20. **Systemic ask (21st bounce
  across 3 days — still unaddressed after 20 requests)**: unchanged from every prior bounce — set `priority: 999` / a
  `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on prereq #4 landing, or
  dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker entirely).
- **2026-07-09** — **-009 RE-DISPATCHED (20TH SLOT BOUNCE) — SAME PARK** (slot-6 data_engineering). Re-verified
  independently against a fresh `.tabs/6` pull (`instruments-service` to `8128189e`, `deployment-service` to `a1bf966`
  on `live-defi-rollout`, both later than the 19th bounce's tips): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1061),
  `_yield_v2_defi_pre_launch_rows` (line 1269), `_yield_v2_prediction_pre_venue_launch_rows` (line 2084) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-19.
  **Systemic ask (20th bounce across 3 days — still unaddressed after 19 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-09** — **-009 RE-DISPATCHED (19TH SLOT BOUNCE) — SAME PARK** (slot-4 data_engineering). Re-verified
  independently against a fresh `.tabs/4` pull (`instruments-service` to `8128189e`, `deployment-service` to `a1bf966`
  on `live-defi-rollout`): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1061),
  `_yield_v2_defi_pre_launch_rows` (line 1269), `_yield_v2_prediction_pre_venue_launch_rows` (line 2084) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-18.
  **Systemic ask (19th bounce across 3 days — still unaddressed after 18 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (18TH SLOT BOUNCE) — SAME PARK** (slot-14 data_engineering). Re-verified
  independently against the current `.tabs/14` clones (fresh-pulled `instruments-service` to `42eeefb` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — both SAME tips as the 17th bounce, no new commits landed in
  the interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-17.
  **Systemic ask (18th bounce across 3 days — still unaddressed after 17 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (17TH SLOT BOUNCE) — SAME PARK** (slot-13 data_engineering). Re-verified
  independently against the current `.tabs/13` clones (fresh-pulled `instruments-service` to `42eeefb` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — deployment-service unchanged from the 16th bounce;
  instruments-service advanced but the check is unaffected): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-16.
  **Systemic ask (17th bounce across 3 days — still unaddressed after 16 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (16TH SLOT BOUNCE) — SAME PARK** (slot-11 data_engineering). Re-verified
  independently against the current `.tabs/11` clones (fresh-pulled `instruments-service` to `666bca5` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — SAME tips as the 15th bounce, no new commits landed in the
  interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-15.
  **Systemic ask (16th bounce across 3 days — still unaddressed after 15 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (15TH SLOT BOUNCE) — SAME PARK** (slot-12 data_engineering). Re-verified
  independently against the current `.tabs/12` clones (fresh-pulled `instruments-service` to `666bca5` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — SAME tips as the 14th bounce, no new commits landed in the
  interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-14.
  **Systemic ask (15th bounce across 3 days — still unaddressed after 14 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (14TH SLOT BOUNCE) — SAME PARK** (slot-10 data_engineering). Re-verified
  independently against the current `.tabs/10` clones (fresh-pulled `instruments-service` to `666bca5` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — deployment-service unchanged from the 13th bounce;
  instruments-service advanced but the check is unaffected): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all confirmed
  present and wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-13.
  **Systemic ask (14th bounce across 3 days — still unaddressed after 13 requests)**: unchanged from every prior bounce
  — set `priority: 999` / a `conditions:` gate on the `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on
  prereq #4 landing, or dispatch an infra-role worker to close prereq #4 directly (removes the parked task's blocker
  entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (13TH SLOT BOUNCE) — SAME PARK** (slot-8 data_engineering). Re-verified
  independently against the current `.tabs/8` clones (fresh-pulled `instruments-service` to `be95c76` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — SAME tips as the 12th bounce, no new commits landed in the
  interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215) confirmed present and wired. Prereq #4 (infra launcher retirement) is
  STILL NOT landed — `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope. The underlying decision was already made — this is
  not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from bounces 3-12 rather
  than re-raising `/blocked`. **Systemic ask (13th bounce across 3 days — still unaddressed after 12 requests)**:
  unchanged from every prior bounce — set `priority: 999` / a `conditions:` gate on the
  `v1_enumerator_dispatch_not_deletable-0XX` backlog entry keyed on prereq #4 landing, or dispatch an infra-role worker
  to close prereq #4 directly (removes the parked task's blocker entirely).
- **2026-07-08** — **-009 RE-DISPATCHED (12TH SLOT BOUNCE) — SAME PARK** (slot-9 data_engineering). Re-verified
  independently against the current `.tabs/9` clones (fresh-fetched `instruments-service` to `be95c76` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — SAME tips as the 10th and 11th bounce, no new commits
  landed in the interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all present and
  wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope (per RULES.md craft-lines + the 2026-07-06
  main-agent ruling on BLK-0b46d0f3 / BLK-8b97bdfe / BLK-530cea75 / BLK-0ac84889). The underlying decision was already
  made — this is not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from
  bounces 3-11 rather than re-raising `/blocked`. **Systemic ask (12th bounce across 3 days — still unaddressed after 11
  requests)**: the backlog entry for `v1_enumerator_dispatch_not_deletable-0XX` (currently `-009`) STILL has no
  `priority: 999` / `conditions:` gate keyed on prereq #4 landing, and `assigned_role: data_engineering` alone is not
  stopping the bounce. Recommend dispatching an infra-role worker to close prereq #4 directly (removes the parked task's
  blocker entirely — unchanged advice from every prior bounce, now at a dozen repeats and still growing).
- **2026-07-08** — **-009 RE-DISPATCHED (11TH SLOT BOUNCE) — SAME PARK** (slot-6 data_engineering). Re-verified
  independently against the current `.tabs/6` clones (fresh-fetched `instruments-service` to `be95c76` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` — same tips as the 10th bounce, no new commits landed in the
  interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all present and
  wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope (per RULES.md craft-lines + the 2026-07-06
  main-agent ruling on BLK-0b46d0f3 / BLK-8b97bdfe / BLK-530cea75 / BLK-0ac84889). The underlying decision was already
  made — this is not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from
  bounces 3-10 rather than re-raising `/blocked`. **Systemic ask (11th bounce across 3 days — still unaddressed after 10
  requests)**: the backlog entry for `v1_enumerator_dispatch_not_deletable-0XX` (currently `-009`) STILL has no
  `priority: 999` / `conditions:` gate keyed on prereq #4 landing, and `assigned_role: data_engineering` alone is not
  stopping the bounce. Recommend dispatching an infra-role worker to close prereq #4 directly (removes the parked task's
  blocker entirely — unchanged advice from every prior bounce, now at double-digit repeats and still growing).
- **2026-07-08** — **-009 RE-DISPATCHED (10TH SLOT BOUNCE) — SAME PARK** (slot-5 data_engineering). Re-verified
  independently against the current `.tabs/5` clones (fresh-fetched `instruments-service` to `be95c76` and
  `deployment-service` to `87df9d1` on `live-defi-rollout` before checking — same tips as the 9th bounce, no new commits
  landed in the interim): prereq #3 (v2 venue-grain sentinel) IS landed in
  `instruments-service/scripts/enumerate_expected_universe.py` — `_yield_v2_cefi_pre_venue_launch_rows` (line 1007),
  `_yield_v2_defi_pre_launch_rows` (line 1215), `_yield_v2_prediction_pre_venue_launch_rows` (line 2023) all present and
  wired via `yield from`. Prereq #4 (infra launcher retirement) is STILL NOT landed —
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py:183`,
  `scripts/vm/vm_zombie_watchdog.py:627`, and `scripts/vm/launch-ec2-vm.sh:148` all still reference the v1
  `expected-universe-enum-`/`eu-enum-` prefix, and `scripts/vm/launch-expected-universe-enumerator-vm.sh` still exists.
  This is an infra-role task, outside `data_engineering` craft scope (per RULES.md craft-lines + the 2026-07-06
  main-agent ruling on BLK-0b46d0f3 / BLK-8b97bdfe / BLK-530cea75 / BLK-0ac84889). The underlying decision was already
  made — this is not a fresh ambiguity, so self-parking via `/skip-current-task` per the established precedent from
  bounces 3-9 rather than re-raising `/blocked`. **Systemic ask (10th bounce across 3 days — still unaddressed after 9
  requests)**: the backlog entry for `v1_enumerator_dispatch_not_deletable-0XX` (currently `-009`) STILL has no
  `priority: 999` / `conditions:` gate keyed on prereq #4 landing, and `assigned_role: data_engineering` alone is not
  stopping the bounce. Recommend dispatching an infra-role worker to close prereq #4 directly (removes the parked task's
  blocker entirely — unchanged advice from every prior bounce, now at double-digit repeats).
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
