---
doc_type: issue
title: 'Durable auto-park''s "no park without a named LIVE flipper" rule is asserted in prose, not enforced in code'
summary: >-
  ao_dispatch_cooldown_and_park_2026_07_20 todo 4 (the mvp-defi unpark re-point) closed its gate's closing clause — "no
  park exists without a named LIVE flipper" — by writing a flip instruction into
  defi_consolidated_closeout_2026_07_18.md Track 5 as prose, not by making the auto-park mechanism itself enforce it.
  `server/auto_park.py::maybe_auto_park` will happily park a task whose synthetic condition (`auto_unpark__<task_id>`)
  has no plan anywhere naming who/when flips it — the mvp-defi case just happened to get a human-written flipper this
  time. A future auto-park (or a manual RULES.md §4 park, which does not touch this store at all) can still silently
  outlive its reason exactly the way the original mvp-defi park did before this plan. Not fixed here: the
  escalation-triggered park path fires from a live skip event with no natural place to demand "and name the flipper now"
  without blocking the worker; the manual park path is a hand-edit that this store doesn't observe at all. Deliberately
  deferred, not urgent — flagged in ao_dispatch_cooldown_and_park_2026_07_20's Progress Log rather than silently
  dropped.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, auto-park, dispatch, cooldown, follow-up]
related:
  - plans/active/ao_dispatch_cooldown_and_park_2026_07_20.md
  - plans/active/defi_consolidated_closeout_2026_07_18.md
  - codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: [ao_dispatch_cooldown_and_park_2026_07_20.md todo 4 Progress Log, 2026-07-20]
resolved_by:
---

# Auto-park's "no park without a flipper" rule needs a mechanism, not just a promise

## Todos

- [ ] [BACKEND] P3. **Decide + build (or explicitly decline) mechanism-level enforcement.** Options to weigh: (a) at
      auto-park time, require the caller (the skip endpoint) to pass an owning-plan reference, stored on the
      `CooldownRow`, surfaced on the dashboard `auto_parked` count so an ownerless park is visibly flagged; (b) a
      periodic sweep (piggyback on `AutoParkReconciler`'s existing tick) that pages when a parked condition's age
      exceeds some threshold with no plan referencing it; (c) explicitly rule this is not worth building — auto-park is
      rare enough (N-skip threshold default 3) that a human always looks at it soon, and the mvp-defi incident was
      specifically a MANUAL park with no reconciler watching it at all, which this plan's auto-park mechanism does not
      reproduce. **Gate**: a recorded decision (built + tested, or explicitly declined with the reasoning above captured
      here).

## Progress Log

- **2026-07-20 — filed** during `ao_dispatch_cooldown_and_park_2026_07_20`'s session-end audit, converting a Progress
  Log deferral into a tracked todo per the workspace's "every deferral must already be a todo" rule.
