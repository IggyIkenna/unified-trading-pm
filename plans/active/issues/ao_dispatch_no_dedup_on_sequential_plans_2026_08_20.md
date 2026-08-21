---
doc_type: issue
title: AO Dispatch Has No Dedup Check for an Already-Claimed sequential:true Plan
summary:
  Observed twice in one session (2026-08-20, `fund_administration_redemption_cadence_engine_2026_08_20.md`'s own
  Progress Log) — the agent-orchestrator fleet dispatched MULTIPLE workers (at least slot-5, slot-14, plus an
  interactive session's own manually-spawned sub-agent) against the SAME `sequential:true` plan concurrently,
  causing real merge conflicts that had to be hand-resolved (documented in that plan's Progress Log, now archived at
  `plans/archive/2026_08/fund_administration_redemption_cadence_engine_2026_08_20.md`). `sequential:true` already
  encodes that a plan's todos form one serial chain — nothing in the dispatcher currently uses that as a signal to
  avoid handing a SECOND worker a todo from a plan another worker already has in flight.
status: open
resolved_by:
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dispatch, dedup, sequential, worker-collision]
related:
  [
    /plans/archive/2026_08/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: flagged in fund_administration_redemption_cadence_engine_2026_08_20.md's own Progress Log during the
  operator's 2026-08-20 /autonomous session; filed as a proper tracked issue during pre-compact so the finding
  survives beyond an archived plan's prose
context_scope:
  [
    /plans/archive/2026_08/fund_administration_redemption_cadence_engine_2026_08_20.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
  ]
---

# AO Dispatch Has No Dedup Check for an Already-Claimed `sequential:true` Plan

**Why this doc exists**: this is a judgment/design question (should the dispatcher hold back a plan's remaining
todos while one is already claimed, and how — a slot-affinity lock? a plan-level in-flight flag?), not a fully
bounded mechanical fix, so it stays `assigned_vm: NA` pending a design decision, per the same reasoning already
observed live: single-agent stickiness is deliberately NOT enforced today (`regen_backlog_from_plan.py` sets no slot
affinity, `_task_is_routable_to` returns `True` for any free slot) — this is a real feature for INDEPENDENT
same-priority todos (fan-out concurrency), but the same permissiveness lets two workers grab different todos from
the SAME `sequential:true` chain at once, which is never intended (the whole point of `sequential:true` is that
todo N waits on N-1).

**Measured cost this session**: on `fund_administration_redemption_cadence_engine_2026_08_20.md` alone, at least 2
real merge-conflict resolutions were required (documented in that plan's own now-archived Progress Log) from
concurrent workers independently implementing the same already-in-flight todo, plus a manually-spawned interactive
sub-agent burning ~79 minutes / ~517K tokens partly re-treading ground a live AO worker had already covered. This is
wasted compute + merge friction that compounds with plan size, not a one-off.

## Todos

- [ ] [REVIEW] P2. Investigate the dispatcher's current claim/lock model (`agent-orchestrator/server/dispatch.py`,
  `regen_backlog_from_plan.py`) and propose a concrete mechanism to prevent a SECOND worker from claiming a todo out
  of a `sequential:true` plan that already has an in-flight (dispatched, not yet done) todo — e.g. a plan-level
  in-flight flag checked at dispatch time, or slot affinity scoped specifically to `sequential:true` plans (not a
  blanket affinity change, which would undo the deliberate fan-out-concurrency feature for independent-todo plans).
  Done-when: a stated recommendation with the specific check/lock point named, or a finding that the fan-out benefit
  outweighs the collision cost and this should stay as-is (a real answer either way, not left open).
- [ ] [BACKEND] P2. BLOCKED-ON: the above investigation's recommendation — implement the chosen dedup mechanism once
  a design is picked, with a test proving two concurrent dispatch requests against the same `sequential:true`
  plan's next todo only ever route one to a live worker.

## Progress Log

- **2026-08-20**: Filed during `/pre-compact` — the finding existed only as prose in an archived plan's Progress Log
  (mentioned to the operator in a chat summary but never converted into a real tracked todo, a HARD RULE violation
  this filing corrects) after being observed twice live in the same session.
