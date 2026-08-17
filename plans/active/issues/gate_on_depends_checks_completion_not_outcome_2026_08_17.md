---
doc_type: issue
title: gate_on_depends dispatches on the dependency's checkbox being flipped, not on its recorded outcome
summary: >-
  A gated "finalize"-style plan (depends_on + gate_on_depends: true) becomes dispatchable the moment the
  dependency's own todo is checked [x] — regardless of whether that todo's recorded RESULT was the success
  condition the finalize plan assumes. A verify-then-act todo that legitimately completes with a
  correctly-withheld/non-GREEN result still satisfies the gate, producing a premature "confirm it landed"
  dispatch for an action that never ran. Observed live 2026-08-17 (slot-21):
  tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize.md was dispatched to confirm a GCS delete had
  landed, but the dependency's own P0 todo — though checked done — recorded "NOT GREEN (CF-8 RED), delete
  correctly WITHHELD".
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, dispatch, gate_on_depends, task_template, plan-authoring]
related:
  - /plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize.md
  - /plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md
  - /plans/active/task_template.md
  - /plans/active/ao_consolidated_closeout_2026_08_12.md
created: "2026-08-17"
author: slot-21 (data_engineering)
source:
  - venue_readiness_ao_dispatch_batch1_2026_08_16.md session (side-finding, not part of that plan's own scope)
assigned_vm: NA
parent_epic: orchestrator_master
resolved_by:
locked_by:
priority: P3
execution_scope: local-only
assigned_role:
drift_direction: none
depends_on: []
context_scope:
  [
    /plans/active/task_template.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize.md,
    /plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md,
  ]
---

# gate_on_depends checks completion, not outcome

## What I found

`task_template.md`'s own documented contract for `depends_on: [plan-slugs]` + `gate_on_depends: true` is: `_wire_gate_on_depends_prereqs`
"makes every task of THIS plan wait on every task of the named upstream plan(s)" — gated on `prereqs.completed_tasks`
all being `done`. That is purely a TASK-COMPLETION check (the todo's checkbox is `[x]`), not a check of what that
todo's own recorded RESULT was.

This is fine for most gated-finalize pairs (a verify step either passes or the plan stays open). It breaks down
specifically for a **verify-then-act** todo whose own done-when explicitly allows a legitimate non-success
outcome: "run the verify; if GREEN, execute the action; if not, correctly withhold it — either way the todo is
done once the verify step itself completed." That todo is correctly checked `[x]` even when the action never ran
— and `gate_on_depends` cannot see the difference, so it dispatches the downstream "confirm it landed" finalize
task exactly as if the action HAD run.

**Live instance (2026-08-17, slot-21)**: `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize.md`
(`depends_on: [tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16]`, `gate_on_depends: true`) dispatched to me with
the brief "Confirm the delete landed with evidence". The dependency's own P0 todo WAS `[x]` — but its own text
reads "**E7 Verify — DONE 2026-08-16 (slot-5)... Result: NOT GREEN (CF-8 RED) — delete correctly WITHHELD, gate
not met.**" I could not honestly flip the finalize todo (recorded in that plan's Progress Log,
`unified-trading-pm@47f88f723c`); released it `GATED` instead of a false `/done`.

## Why it matters

A worker (or reviewer) landing on the finalize task cold has no signal from the dispatch mechanism itself that the
dependency's outcome doesn't satisfy the finalize's premise — they have to open the dependency plan and read its
Progress Log narrative to discover this. At AO scale that's wasted dispatch cycles (a worker re-diagnoses the same
"not actually landed" state every time the finalize task gets redispatched after a `GATED` skip's cooldown expires)
and a real risk that a less careful pass flips the finalize checkbox on the mere presence of the dependency's `[x]`,
without reading the substance — exactly the false-done class CLAUDE.md's "runtime verification" HARD RULE exists to
prevent.

## Recommended decision

This is a genuine design question, not a bounded fix — options include (a) leave it as-is and rely on worker
discipline (status quo — costs a re-diagnose cycle per premature dispatch, as measured here), (b) a plan-authoring
convention: a verify-then-act todo whose done-when allows a non-success terminal state should say so explicitly in
a way `gate_on_depends`'s prereq wiring could someday key off (e.g. a distinguishable checkbox marker), or (c)
`task_template.md` gains an explicit callout warning authors: don't `gate_on_depends` a finalize plan on a
verify-then-act todo without also stating the finalize plan's own todo should independently re-verify the
substantive outcome before acting (which is what happened here, informally, because the worker read the
dependency's text rather than trusting the gate). Needs an operator/plan-authoring-convention call, not a worker
decision.

## Todos

- [ ] [DOC] P3. Decide + document (in `task_template.md`, near the existing `gate_on_depends` section) whether/how
      a gated finalize plan should be protected from this class of premature dispatch, per one of the three
      options above (or another). Repo: unified-trading-pm.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
