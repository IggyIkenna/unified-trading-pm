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
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, auto-park, dispatch, cooldown, follow-up]
related:
  - plans/active/ao_dispatch_cooldown_and_park_2026_07_20.md
  - plans/active/defi_consolidated_closeout_2026_07_18.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
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
resolved_by: "decision (c) explicitly-decline, 2026-07-29 batch closeout pass — no code shipped, see todo for reasoning"
---

# Auto-park's "no park without a flipper" rule needs a mechanism, not just a promise

## Todos

- [x] [BACKEND] P3. **Decide + build (or explicitly decline) mechanism-level enforcement.** Options to weigh: (a) at
      auto-park time, require the caller (the skip endpoint) to pass an owning-plan reference, stored on the
      `CooldownRow`, surfaced on the dashboard `auto_parked` count so an ownerless park is visibly flagged; (b) a
      periodic sweep (piggyback on `AutoParkReconciler`'s existing tick) that pages when a parked condition's age
      exceeds some threshold with no plan referencing it; (c) explicitly rule this is not worth building — auto-park is
      rare enough (N-skip threshold default 3) that a human always looks at it soon, and the mvp-defi incident was
      specifically a MANUAL park with no reconciler watching it at all, which this plan's auto-park mechanism does not
      reproduce. **Gate**: a recorded decision (built + tested, or explicitly declined with the reasoning above captured
      here). **Decided 2026-07-29 (batch closeout pass): (c) — explicitly decline to build.** Re-verified the todo's own
      premise still holds: `server/auto_park.py`'s auto-park path only fires after `N=3` consecutive skips (rare in
      practice — a human/watcher notices well before a park goes stale), and the ONE incident this rule exists to
      prevent (mvp-defi) was a hand-edited MANUAL park via RULES.md §4 — a code path this store never observes at all,
      so building mechanism-level enforcement here would not even have caught the incident that motivated it. Building
      (a) or (b) adds real surface (a new `CooldownRow` column + dashboard wiring, or a new periodic-sweep alarm) to
      guard against a failure mode that has not recurred via the auto-park path specifically. No code shipped;
      decision + reasoning recorded per the todo's own gate.

## Progress Log

- **2026-07-29 (batch closeout pass)** — Decided + closed the sole open todo as (c), explicit decline (see checkbox
  above for full reasoning). Every todo in this doc is now `[x]` — candidate for archival.
- **2026-07-20 — filed** during `ao_dispatch_cooldown_and_park_2026_07_20`'s session-end audit, converting a Progress
  Log deferral into a tracked todo per the workspace's "every deferral must already be a todo" rule.
