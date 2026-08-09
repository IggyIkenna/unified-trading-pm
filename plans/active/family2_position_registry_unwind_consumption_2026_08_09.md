---
doc_type: plan
title: Family2PositionRegistry — consume the Family-2 close/unwind event once it exists
summary: >-
  Add unwind/close consumption to Family2PositionRegistry.enumerate_open_positions() once strategy-service ships a real
  Family-2 close/unwind emission path. Gated on strategy_service_family2_close_unwind_emission_2026_08_09.md — split out
  per BLK-0fb75f8f (main ruling, 2026-08-09) rather than building against a speculative event schema.
status: active
nature: process
asset_group: [defi]
stage: [strategy]
repos: [execution-service]
scope: [engineer]
tags: [defi, carry, recursive-loop, family2, close-unwind]
related:
  [
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /plans/active/strategy_service_family2_close_unwind_emission_2026_08_09.md,
    /plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
context_scope:
  [
    /plans/active/strategy_service_family2_close_unwind_emission_2026_08_09.md,
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    execution-service/execution_service/defi_execution/monitors/family2_position_registry.py,
  ]
supersedes:
superseded_by:
depends_on: [strategy_service_family2_close_unwind_emission_2026_08_09]
gate_on_depends: true
source: >-
  Split out of recursive_loop_orchestrator_wiring_finalize_2026_08_09.md's "Add unwind/close consumption to
  Family2PositionRegistry" todo per BLK-0fb75f8f (main ruling, 2026-08-09, option A) — that todo was gated on a
  strategy-service emission path that did not exist and had no tracked prerequisite anywhere in the corpus.
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
---

# Family2PositionRegistry — unwind/close consumption

## Todos

- [ ] [BACKEND] P3. Add unwind/close consumption to `Family2PositionRegistry`
      (`execution-service/execution_service/defi_execution/monitors/family2_position_registry.py`) once
      `strategy_service_family2_close_unwind_emission_2026_08_09.md` ships strategy-service's real Family-2 close/unwind
      emission path (this plan is `gate_on_depends`-blocked until then — do not attempt this before the prerequisite's
      own commit lands, its real event schema is what this todo consumes). Today every observed Family-2 open event is,
      correctly for now, treated as currently-open since no close/unwind ever arrives; that assumption goes stale the
      moment the prerequisite ships unless this follow-up ships alongside it. Repo: execution-service. Done-when: the
      registry also consumes the prerequisite's close/unwind event (correlating on `correlation_id`/`instruction_id`,
      matching the prerequisite's own emitted correlation shape — read the prerequisite's shipped code, not this todo's
      guess, before implementing) and retires the matching open position from `enumerate_open_positions()`'s output;
      unit test covers the retire path; `quality-gates.sh` green on execution-service. Archival (single-todo plan — fold
      the 6-step ritual into this same todo per task_template.md §4's "genuinely single-todo plan" carve-out): once
      shipped + green, `git mv` this file to `plans/archive/2026_08/`, flip `status: complete`, fix any corpus referrers
      (`grep -rl 'family2_position_registry_unwind_consumption_2026_08_09'`), and confirm `run_hygiene_sweep.sh` stays
      green — as a commit SEPARATE from the checkbox-flip commit.

## Progress Log

- **2026-08-09 (slot 33, backend_engineer)**: Authored per BLK-0fb75f8f (main ruling, option A) — split out of
  `recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`'s unwind-consumption todo. Gated via `depends_on` +
  `gate_on_depends: true` on `strategy_service_family2_close_unwind_emission_2026_08_09` so the dispatcher holds it
  until the real emission path ships, rather than a worker guessing a schema.
