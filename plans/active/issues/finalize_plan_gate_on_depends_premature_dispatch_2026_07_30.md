---
doc_type: issue
title: gate_on_depends did not block dispatch of a finalize plan whose depends_on plans still had ~20 open todos
summary: >-
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md declares depends_on:
  [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26] +
  gate_on_depends: true, with an explicit banner stating the dispatcher will not queue any of its todos until all 31
  todos across both parts are done. Slot 14 was dispatched its todo 1 (finalize-001) on 2026-07-30 while the live
  backlog showed 20 queued (not done) tasks still belonging to those two depends_on plans (9 in batch1, 11 in batch1b) —
  the gate did not hold.
status: open
nature: issue
resolved_by:
asset_group: [cross-cutting, meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [gate_on_depends, dispatcher, backlog, ao-dispatch, finalize-plan, process-bug]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Discovered by slot 14 while working cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize-001 (2026-07-30).
  Assigned_role: review (adopted from infra per the per-task craft-role rule).
assigned_role: infra
drift_direction: advance-code
---

# gate_on_depends premature-dispatch finding

## What I found

`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md` declares:

```yaml
depends_on:
  [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26]
gate_on_depends: true
```

with an explicit body banner: "the dispatcher will not queue any todo below until all 31 tasks across both parts are
`done`."

Slot 14 was dispatched `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize-001` (todo 1: "Reconcile all
distinct source docs' checkboxes... For each of the 31 now-done todos...") on 2026-07-30. At dispatch time, a live
`GET /api/backlog` query showed:

- `cross_cutting_satellite_ao_dispatch_batch1-*`: 12 backlog rows, 9 still `queued` (batch1-001, -002, -003, -006, -011,
  -013, -014, -016, -017)
- `cross_cutting_satellite_ao_dispatch_batch1b-*`: 13 backlog rows, 11 still `queued` (batch1b-001, -002, -003, -005,
  -006, -007, -010, -011, -013, -014, -023)

That's 20 still-`queued` (not `done`) tasks across the two `depends_on` plans — the `gate_on_depends: true` mechanism
did not block dispatch of the finalize plan's own todo despite this. Direct read of both source `.md` files confirms the
same: `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` has 10 unchecked `- [ ]` todos (of 19 current, grown
from the original "16" via mid-flight splits like `-017`), and
`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` has 12 unchecked `- [ ]` todos (of 18 current, grown from
the original "15"). The finalize plan's own "31 todos across both parts" premise is now stale — the real current total
is 37 (19+18), of which only ~15 are done.

## Why it matters

`gate_on_depends: true` + `depends_on` is the documented mechanism (RULES.md, `PLAN_FORMAT.md`) for expressing "don't
dispatch until these other plans are fully done" — it's exactly the primitive a finalize/closeout plan needs to avoid
archiving/reconciling prematurely. If it silently doesn't hold, every gated finalize plan in the corpus is at risk of
the same premature dispatch, and a worker following the todo's own instructions literally (treating "31 now-done" as
true without checking) could have produced false-completion writes (flipping source-doc checkboxes for work that hasn't
shipped, or worse, flipping the finalize plan's `status` toward archival before the real prerequisite work lands).

## Recommended decision

1. Root-cause why `gate_on_depends` didn't hold for this dispatch — check
   `agent-orchestrator/server/regen_backlog_from_plan.py` / the dispatcher's `depends_on` resolution: does it check
   whether the referenced plan **files** are archived/complete (a doc-level check) rather than counting each referenced
   plan's own derived backlog-task completion? If so, that's the root cause — a plan can stay `status: active`
   indefinitely while still having many `[x]`-flippable-but-actually-`[ ]` todos, and a doc-level "is it archived" check
   would never see that.
2. Once root-caused, fix the dispatcher so `gate_on_depends: true` genuinely blocks until every backlog task derived
   from each `depends_on` plan is `done` (not merely queued-with-lower-priority).
3. Audit the rest of the active corpus for other `gate_on_depends: true` finalize plans that may have been prematurely
   dispatched the same way (`rg -l 'gate_on_depends: true' plans/active/`).
4. `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize-001` itself: I did NOT do the full "31 now-done"
   reconciliation since the premise was false — I verified + reconciled only the ~15 todos that are genuinely done right
   now (2 source docs needed real edits, the rest were already correctly reconciled inline by their own workers). See
   the finalize plan's Progress Log for the up-to-date accounting. This todo should be re-dispatched once batch1 +
   batch1b actually reach 0 open todos, to catch the remaining ~22.

## Todos

- [ ] [INFRA] P1. Root-cause `gate_on_depends`'s actual dependency-resolution logic in agent-orchestrator (likely
      `regen_backlog_from_plan.py` or the dispatcher's task-eligibility check) and confirm whether it checks per-task
      backlog completion vs. a coarser doc-level signal. Repo: agent-orchestrator.
- [ ] [INFRA] P1. Fix the resolution logic so `gate_on_depends: true` blocks dispatch until every backlog task derived
      from each `depends_on` plan is genuinely `done`. Add a regression test exercising a plan with a partially
      -complete dependency. Repo: agent-orchestrator.
- [ ] [DOC] P2. Sweep `plans/active/` for other `gate_on_depends: true` finalize plans and spot-check whether any were
      dispatched while their dependencies still had open todos. File follow-ups per-doc if found.
