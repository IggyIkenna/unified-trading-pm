---
doc_type: issue
title: >-
  CI-escalation reserve slots (31/32/33) were claimable by ordinary Class-A backlog dispatch —
  same gap class as sched_reserve_dispatch_exclusion_gap_2026_08_16, for the sibling reserve —
  fixed 2026-08-21
summary: >-
  Live `/ao-watchdog`-style check (2026-08-21) found all 3 live CI-escalation reserve slots
  (31/32/33, `reserved_for: "ci_escalation"` in the dashboard's own computed slot view) running
  ORDINARY plan-dispatched worker tasks (an OMS-persistence impl, a citadel batch, an
  execution-service security audit) — none `target_slot`-pinned, all picked by AutoSpawn's normal
  Class-A fill loop. Root-caused to `server/dispatch.py`'s `_FILTERS` table (the SSOT both
  `pick_next_task` and AutoSpawn's spawn-target selection derive from): it already excludes
  `config.scheduled_task_reserved_slot_ids()` (fixed 2026-08-16, `sched_reserve_dispatch_
  exclusion_gap_2026_08_16`, `test_dispatch_scheduled_reserve_gate.py`) but had ZERO reference to
  `config.ci_escalation_reserved_slot_ids()` — the sibling reserve never got the symmetric fix.
  `escalation.py::_pick_free_slot` and `plan_health.py`'s own scheduled-dispatch pick both already
  exclude the CI reserve from THEIR OWN picks, but nothing stopped ordinary backlog dispatch from
  claiming INTO it. Not an active incident at discovery time (24/48 slots idle fleet-wide, the one
  live escalation dispatched fine to a non-reserve slot within ~10 minutes) but a live reproduction
  of the exact failure shape `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` hit once already
  from a different proximate cause (that incident: the reserve slots were `paused` and single-
  account-concentrated; this one: the reserve slots were simply never protected from ordinary
  dispatch reaching them at all). Fixed same day by mirroring the 2026-08-16 fix exactly for the
  CI-escalation reserve — see Fix section.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, escalation, ci-escalation-reserve, dispatch, slot-reclaim, capacity]
related:
  [
    /plans/active/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/tests/test_dispatch_scheduled_reserve_gate.py,
    /plans/active/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
  ]
source: >-
  Interactive /ao-watchdog-style investigation, 2026-08-21 (slot 17) — operator asked whether
  scheduled/escalation workers are firing correctly and whether more reserved slots are needed;
  live state pull found the 3-slot CI-escalation reserve fully occupied by ordinary backlog work.
---

# CI-escalation reserve slots were claimable by ordinary Class-A backlog dispatch

## What was found (live, 2026-08-21 ~06:40 UTC)

`GET /api/state` showed slots 31/32/33 (`reserved_for: "ci_escalation"`, the live 3-slot
`ci_escalation_slot_reserve()` default) running:

- Slot 31: `w_execution_orchestrator_oms_persistence_impl` (status `blocked`, stuck on an
  unresolved runtime/import-path bug — a real Class-A worker task, not an escalation).
- Slot 32: `citadel_satellite_ao_dispatch_batch2` (status `blocked`, waiting on an operator
  question).
- Slot 33: `w15_execution_service_venue_adaptor_security_audit` (status `working`).

`GET /api/backlog` confirmed all three tasks had `target_slot: null, affinity: "none"` — picked
by AutoSpawn's ordinary fill loop, not pinned. Not an active incident at discovery (24/48 slots
idle fleet-wide; the one genuinely active escalation, `agt-11b175`, dispatched to slot 21 within
~10 minutes) — but a latent single point of failure: if general fleet headroom tightens while the
reserve is occupied like this, a new CI-failure escalation reproduces
`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`'s exact "no free configured slot" stall from
a different proximate cause.

## Root cause

`server/dispatch.py`'s `EligibilityCtx`/`_FILTERS` table is the SSOT both `pick_next_task` (used
by worker slots asking for work) and `slots_with_claimable_task`/AutoSpawn's spawn-target
selection derive from. It already carries a `scheduled_reserve` filter
(`_blocks_scheduled_reserve`, `sched_reserved_slot_ids`) excluding
`config.scheduled_task_reserved_slot_ids()` — shipped 2026-08-16 after the identical failure mode
was caught live on slot 29 (`sched_reserve_dispatch_exclusion_gap_2026_08_16`,
`test_dispatch_scheduled_reserve_gate.py`).

**`dispatch.py` had zero reference to `config.ci_escalation_reserved_slot_ids()` at all.** The
docstring on `ci_escalation_reserved_slot_ids()` (`config.py:543`) claims the reserve is
"Protected from Class-A backlog spawn (via `_apply_fleet_cap`'s combined-reserve clamp)" — but
`_apply_fleet_cap` (`autospawn.py`) only reduces the fleet-wide ACTIVE-WORKER COUNT budget by the
reserve size; it does not exclude the specific reserved slot IDs from being chosen. The intended
protection was emergent (assumes ordinary dispatch always fills lowest slot_id first and stops at
the count-clamped budget) rather than an explicit ID exclusion — and the emergent assumption did
not hold under today's fleet churn (605 boots / 326 dispatches over the trailing 24h), so ordinary
dispatch reached all the way into slots 31-33.

`escalation.py::_pick_free_slot` and `plan_health.py`'s scheduled-dispatch pick both already
exclude `ci_escalation_reserved_slot_ids()` from THEIR OWN picks (protecting the reserve from
scheduled-task overflow) — but nothing protected the reserve from ordinary Class-A backlog
dispatch, the exact same asymmetric gap shape the 2026-08-16 fix closed for the sibling reserve.

## Fix (shipped 2026-08-21)

Mirrored the 2026-08-16 `scheduled_reserve` fix exactly, for the CI-escalation reserve:

- `server/dispatch.py`: added `EligibilityCtx.ci_reserved_slot_ids: frozenset[int]`, a
  `_blocks_ci_escalation_reserve` filter function, a new `ci_escalation_reserve` `_Filter` entry
  (`FilterScope.SLOT`) in `_FILTERS`, and wired `ci_reserved_slot_ids=frozenset(config.
  ci_escalation_reserved_slot_ids(non_review_ids_for_reserve))` into `_build_ctx`.
- `tests/conftest.py`: added `_default_ci_escalation_reserve_off` (autouse), mirroring
  `_default_scheduled_reserve_off` — neutralizes the production CI-reserve default (3) for the
  general suite so existing small-fixture dispatch tests aren't silently affected by the reserve
  becoming enforced for the first time.
- `tests/test_dispatch_ci_escalation_reserve_gate.py` (new): mirrors
  `test_dispatch_scheduled_reserve_gate.py`'s full test set (single-slot reserve, spawn-budget
  exclusion, reserve-is-only-slot, opt-out honoured, human-fleet-slot never swept into the
  reserve pool, multi-slot reserve) plus one new regression test
  (`test_ci_and_scheduled_reserves_stack_without_overlap`) confirming the two reserves compose
  correctly now that both filters exist in the same table.
- Evidence: `Evidence: <fill in commit sha + quality-gates.sh result once shipped>`.

## Todos

- [x] [BACKEND] P1. Add the `ci_escalation_reserve` filter to `dispatch.py`'s `_FILTERS`,
      mirroring `scheduled_reserve` exactly. Repo: agent-orchestrator.
- [x] [BACKEND] P1. Add `_default_ci_escalation_reserve_off` to `tests/conftest.py` so the
      production reserve default doesn't silently affect the wider test suite. Repo:
      agent-orchestrator.
- [x] [BACKEND] P1. Write `test_dispatch_ci_escalation_reserve_gate.py` mirroring the sched-reserve
      test file, plus a stacking regression test. Repo: agent-orchestrator.
- [ ] [SCRIPT] P2. Once shipped, live re-verify: confirm slots 31/32/33 are no longer claimable by
      ordinary Class-A backlog dispatch (e.g. watch the next AutoSpawn tick after the fix deploys,
      or directly call `GET /api/backlog` + `GET /api/state` a few ticks later and confirm no new
      non-escalation task lands there). Repo: agent-orchestrator.
- [ ] [OPERATOR] P2. Separately, the reserve is still 100% single-account-concentrated
      (`codex-luna` as of 2026-08-21, was `sub-b-iggy2london` on 2026-08-18) — this doc's fix
      protects the SLOTS from ordinary dispatch, but does not address the account-concentration
      risk already tracked as an open todo in
      [[ao_stuck_escalation_mtds_no_free_slot_2026_08_18]] ("spread 31/32/33 across more than one
      account"). Not duplicating that todo here — cross-referenced only.

## Progress Log

- **2026-08-21 (slot 17, interactive)**: found live during a scheduled/escalation-worker health
  check requested by the operator; root-caused via direct code read (`dispatch.py`, `config.py`,
  `escalation.py`) and confirmed via the live `target_slot: null` backlog data for the 3 tasks
  occupying the reserve. Fix implemented same session, mirroring the 2026-08-16 precedent for the
  sibling reserve. Pending: quality-gates.sh verification + quickmerge ship (see Fix section for
  evidence once complete).
