---
doc_type: plan
title: Family-2 (CARRY_BASIS_PERP_INV) close/unwind instruction emission — strategy-service
summary: >-
  Ship a real close/unwind AtomicInstruction emission path in recursive_staked.py's Family-2 tick handler. Today it only
  ever opens a position once and never emits a close. Prerequisite for
  family2_position_registry_unwind_consumption_2026_08_09.md, split out per BLK-0fb75f8f (main ruling, 2026-08-09).
status: active
nature: design
asset_group: [defi]
stage: [strategy]
repos: [strategy-service]
scope: [engineer]
tags: [defi, carry, recursive-loop, family2, close-unwind]
related:
  [
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /plans/active/family2_position_registry_unwind_consumption_2026_08_09.md,
    /plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
context_scope:
  [
    /plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Split out from recursive_loop_orchestrator_wiring_finalize_2026_08_09.md's "Add unwind/close consumption to
  Family2PositionRegistry" todo per BLK-0fb75f8f (main ruling, 2026-08-09, option A — SPLIT the prerequisite into its
  own gated plan pair rather than guess a speculative event schema or fold cross-repo scope into one todo).
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
---

# Family-2 close/unwind instruction emission — strategy-service

## Todos

- [ ] [DESIGN][BACKEND] P2. Ship a real Family-2 (`CARRY_BASIS_PERP_INV`) close/unwind instruction emission path in
      strategy-service's `recursive_staked.py`. Today `_on_tick_family2_basis_perp_inv()` only ever opens the position
      once (`if self.current_position_units != 0: return []` guards every subsequent tick — confirmed via direct
      2026-08-09 read; no close/unwind emission exists anywhere in the file) and every observed Family-2 open is,
      correctly for now, treated as permanently open downstream in `Family2PositionRegistry.enumerate_open_positions()`.
      This is the load-bearing prerequisite for `family2_position_registry_unwind_consumption_2026_08_09.md`'s
      registry-consumption todo, which cannot be correctly implemented without a real event schema to consume. Repo:
      strategy-service. Design scope (resolve as part of this todo, not pre-decided here): the actual close/unwind
      TRIGGER condition (an operator/ strategy-owner exit signal, an on-chain liquidation-risk threshold read via the
      same Aave data `PerpHedgeSizer` already reads, a fixed unwind schedule, or something else) — read
      `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md` before deciding; if the archetype doc
      already specifies an intended exit condition, use it, don't invent a new one. Done-when: (1) a real close/unwind
      condition + emission path exists in `_on_tick_family2_basis_perp_inv()` (or a sibling method it calls); (2) the
      emitted close/unwind `AtomicInstruction` correlates back to the original open via
      `correlation_id`/`instruction_id` (matching how `Family2PositionRegistry` already correlates opens — read
      `execution_service/defi_execution/monitors/family2_position_registry.py` for the existing correlation shape before
      designing the close side); (3) unit tests cover both the close-trigger-fires and no-close-when-not-triggered
      paths, following the existing Family-2 `on_tick()` test file's pattern; (4) `quality-gates.sh` green on
      strategy-service. Codex SSOTs: `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md`,
      `/codex/04-architecture/tier-and-import-architecture.md`. Archival (single-todo plan — fold the 6-step ritual into
      this same todo per task_template.md §4's "genuinely single-todo plan" carve-out): once shipped + green, `git mv`
      this file to `plans/archive/2026_08/`, flip `status: complete`, fix any corpus referrers
      (`grep -rl 'strategy_service_family2_close_unwind_emission_2026_08_09'`), and confirm `run_hygiene_sweep.sh` stays
      green — as a commit SEPARATE from the checkbox-flip commit, per the never-combine-flip-with-git-mv rule.

## Progress Log

- **2026-08-09 (slot 33, backend_engineer)**: Authored per BLK-0fb75f8f (main ruling, option A) — split out of
  `recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`'s unwind-consumption todo, which was gated on this
  not-yet-existing emission path. No `depends_on` — this is the prerequisite plan itself, ungated.
