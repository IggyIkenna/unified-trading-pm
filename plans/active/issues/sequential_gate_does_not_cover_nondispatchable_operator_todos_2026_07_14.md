---
doc_type: issue
title:
  `sequential: true` cannot gate on a non-dispatchable `[OPERATOR]` BLOCKED-OPERATOR-DECISION todo — write-todos
  downstream of an unresolved operator gate keep dispatching anyway
summary: >
  On `mtds_available_at_cross_asset_backfill_2026_07_13.md`, a P0 `[OPERATOR] BLOCKED-OPERATOR-DECISION` todo requires
  explicit operator sign-off before ANY production write (pausing a consolidator cron, applying a manifest backfill,
  resuming the cron). Per `task_template.md` §3, `[OPERATOR]`/`BLOCKED-<TOKEN>` lines are "non-dispatchable (kept
  visible, never ingested)" — they never become a backlog task. Adding `sequential: true` to the plan (to fix an
  earlier out-of-order dispatch, see this plan's own Progress Log) only orders DISPATCHABLE todos by "task N waits for
  N-1 done" — it has no way to wait on a todo that never becomes a task in the first place. Result: across this single
  session, THREE separate production-write todos (apply prediction manifest --no-dry-run, pause tradfi consolidator
  cron, resume tradfi consolidator cron) were each dispatched to slot 5 with the operator gate still unchecked and no
  operator sign-off on record — each had to be individually declined via `/skip-current-task`. This is a systemic gap
  in the `sequential: true` + `[OPERATOR]` pattern, not specific to this plan; any AO plan using an `[OPERATOR]` gate
  ahead of write-todos will hit the same premature-dispatch risk unless the plan author separately wires a
  `prereqs.conditions` gate (yaml-only tuning, main-agent/operator territory per `RULES.md` §4 — out of a worker's
  role to self-apply).
status: open
nature: notes
asset_group: [meta]
stage: [data]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog-dispatch, sequential, operator-gate, plan-authoring, data-correctness]
related:
  [
    plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    plans/active/task_template.md,
    codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-14
parent_epic: manifest_master
priority: P1
source: mtds_available_at_cross_asset_backfill-004/-007/-009 dispatched to slot 5, 2026-07-14
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_by:
locked_since:
supersedes:
superseded_by:
---

# `sequential: true` doesn't cover non-dispatchable `[OPERATOR]` todos

## What I found

`mtds_available_at_cross_asset_backfill_2026_07_13.md` has this todo shape (P0 order, prediction lane):

```
- [ ] [DATA] P0. Confirm library commits pinned...
- [ ] [OPERATOR] P0. BLOCKED-OPERATOR-DECISION — coordinate a maintenance window... get explicit per-bucket go-ahead.
- [ ] [DATA] P1. Dry-run rebuild_prediction_manifest.py...
- [ ] [DATA] P1. Snapshot the prediction canonical manifest index... and pause its consolidator cron.
- [ ] [DATA] P1. Apply rebuild_prediction_manifest.py (real write)...
- [ ] [DATA] P1. Resume the prediction consolidator cron...
```

I added `sequential: true` to this plan's frontmatter earlier this session (commit `unified-trading-pm@38d967dde`) after
finding task `-005` ("resume the prediction cron") dispatched to slot 5 with zero upstream steps done. That fix was
necessary but insufficient: `sequential: true`'s "task N waits for N-1 `done`" only orders todos that actually become
backlog tasks. Per `task_template.md` §3, an `[OPERATOR]`/`BLOCKED-<TOKEN>` line is explicitly "non-dispatchable (kept
visible, never ingested)" — it never becomes a task with a `done` state the sequencer can wait on. So the `[DATA]` todos
immediately after the `[OPERATOR]` gate are treated as adjacent in the sequential chain to whatever `[DATA]` todo came
before the gate, completely bypassing it.

Concretely, in this one session, THREE further production-write todos were dispatched to slot 5 with the operator gate
still unchecked and no sign-off on record anywhere (plan text, Progress Log, or heartbeat messages):

- `-004`: Apply `rebuild_prediction_manifest.py` for real (no `--dry-run`) — a genuine production write.
- `-007`: Pause the tradfi consolidator cron — a genuine production mutation.
- `-009`: Resume the tradfi consolidator cron — presupposes a pause + apply that never happened.

Each was declined via `/skip-current-task` with the operator-gate reasoning in the skip reason (visible in slot 5's
activity log). No production writes were made in any of these three cases — this issue is about the DISPATCH behavior,
not a data-correctness incident on its own. But it is exactly the shape of gap the sports CF-8 precedent (this same
plan's own "HARD constraint" section) warns about: an automated write reaching production ahead of an explicit human
safety decision.

## Why it matters

This is not specific to this one plan — it's a structural gap in the `[OPERATOR]` + `sequential: true` combination that
any AO plan author could hit. `RULES.md` §4 documents the actual fix (`prereqs.conditions`, created via
`POST /api/prerequisites/<name>` and attached to the gated task's `backlog.yaml` entry), but that section is scoped to
"main agent + operator" — a worker (my role, `data_engineering`) has neither the access nor the mandate to self-apply
it. So the fix has to come from whoever authors/maintains plans with this shape, and `task_template.md` §4's guidance on
`sequential: true` doesn't currently warn that it silently no-ops across a non-dispatchable `[OPERATOR]` line.

## Recommended decision

Two independent fixes, either or both:

1. **Immediate**: main/operator attach a `prereqs.conditions` gate (e.g.
   `mtds-available-at-maintenance-window-approved`, seeded `false`) to every remaining prediction/tradfi write-todo in
   `mtds_available_at_cross_asset_backfill_2026_07_13.md` (snapshot-cron-pause for real, apply, resume — both lanes),
   flipped `true` only once the operator has actually given the maintenance-window go-ahead tracked in
   `BLK-272f061b`/`BLK-1e6326c7`.
2. **Structural**: update `plans/active/task_template.md` §4's `sequential: true` guidance to explicitly call out this
   gap — a `sequential: true` plan containing a `[OPERATOR]`/`BLOCKED-<TOKEN>` gate ahead of write-todos MUST also carry
   an explicit `prereqs.conditions` gate on those write-todos, since the non-dispatchable line is invisible to the
   sequencer. Optionally, a QG/plan-hygiene check could flag this pattern automatically (a `[DATA]` todo immediately
   following an `[OPERATOR]` `BLOCKED-OPERATOR-DECISION` line, in a `sequential: true` plan, with no matching
   `prereqs.conditions` on the downstream todo).

No code change needed for option 1 (yaml/API only); option 2 is a `task_template.md` doc edit + optional QG script,
scoped as its own follow-up (not something I should absorb into the source plan's data-engineering work).
