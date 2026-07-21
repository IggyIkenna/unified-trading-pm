---
doc_type: issue
title: >-
  `gate_on_depends: true` is a structural no-op when its `depends_on` upstream is `assigned_vm: NA` (never ingested)
summary: >-
  `server/regen_backlog_from_plan.py::_wire_gate_on_depends_prereqs` (~line 1522) wires a gated task's prereqs from
  `file_to_ids` — built ONLY from `backlog.tasks` — then does `if not upstream_ids: continue`. An upstream `depends_on`
  plan with `assigned_vm: NA` / `execution_scope: local-only` is NEVER ingested into the backlog, so it has ZERO task
  rows, `upstream_ids` is empty, and the gate wires NOTHING — the gated task dispatches freely despite `gate_on_depends:
  true`. Confirmed 2 live instances on `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` (both todos gated on
  `cefi_chain_tail_v6_canonicalisation_2026_07_21.md`, an in-progress operator-driven migration, `assigned_vm: NA`):
  slot-7 hit this, added `gate_on_depends: true` believing it would fix the mis-dispatch, then slot-2 (this doc's
  author) was dispatched the SAME still-blocked todo again — proving the frontmatter fix alone is insufficient because
  the machinery cannot gate on a non-ingested upstream.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, gate_on_depends, backlog, plan-authoring, mis-dispatch]
related:
  [
    plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md,
    plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [manifest_v6_batch3_residual_orphaned_work-003]
resolved_by:
locked_by:
depends_on: []
---

# What I found

`gate_on_depends: true` on a plan/issue doc is documented as machine-holding dispatch of that doc's todos until every
task derived from its `depends_on` plan(s) is complete. In practice it silently does nothing when the `depends_on`
target itself is `assigned_vm: NA` / `execution_scope: local-only` (a human-driven, never-auto-dispatched plan) —
exactly the class of upstream an operator-driven migration like `cefi_chain_tail_v6_canonicalisation_2026_07_21.md`
falls into.

**Root cause (verified in code, main/review agent's diagnosis)**:
`server/regen_backlog_from_plan.py::_wire_gate_on_depends_prereqs` (~line 1522) builds `file_to_ids` ONLY from
`backlog.tasks` — the set of tasks already ingested into the live backlog — then resolves the gated task's upstream IDs
by looking up its `depends_on` file path(s) in that map. When the upstream plan has `assigned_vm: NA`, it was NEVER
ingested into the backlog in the first place (by design — `NA` means "not auto-dispatched"), so it contributes ZERO rows
to `file_to_ids`. The lookup returns an empty `upstream_ids` set, and the function does `if not upstream_ids: continue`
— silently skipping the gate wiring entirely instead of treating "upstream not ingested" as "upstream not yet
satisfied." The gated task's `prereqs.completed_tasks` is left unset, so the dispatcher has nothing to check and offers
the task freely.

**2 confirmed live instances**, both on `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`, both
`depends_on: [plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md]` (an in-progress, `assigned_vm: NA`
operator-driven v5→v6 migration with todos 5-8 still open):

1. **-002** (the deployment-api data-status API todo): dispatched to a worker despite the block; the worker confirmed
   the migration's todos 5-8 were still open and declined + escalated (`BLK-3f4c6134`). Believing the fix was a missing
   `gate_on_depends: true` field, slot-7 added it to this doc's frontmatter.
2. **-003** (the deployment-ui heatmap todo, this doc's `source`): dispatched to slot-2 (me) DESPITE
   `gate_on_depends: true` now being present — re-verified fresh that `cefi_chain_tail_v6_canonicalisation`'s todos 5-8
   were still open, declined, and escalated via `/blocked` (`BLK-65c84850`). The frontmatter fix from instance 1 did not
   resolve the underlying mechanism, because the mechanism cannot gate on a non-ingested upstream regardless of the
   flag.

# Why it matters

This is a **silent** dispatch-logic gap, not a loud failure — a gated task simply dispatches as if ungated, with no
error, no log line pointing at the cause, and no signal to the plan author that their `gate_on_depends: true` did
nothing. It specifically defeats gating for the exact case where gating matters most: a task whose correctness depends
on an in-progress, human-paced, operator-driven migration (`assigned_vm: NA` is precisely the marker for that class of
work). Left unfixed, every future `depends_on` + `gate_on_depends: true` pairing against an `NA`-class upstream will
silently no-op, and each occurrence costs a dispatched worker a full investigation cycle to independently re-discover
"yes, still blocked" before declining — as happened twice here.

# Recommended decision

Two candidate fixes, for careful review before implementation — **dispatch logic is high-blast-radius, do not implement
blind**:

1. **Synthetic never-satisfied prereq**: when an upstream `depends_on` plan resolves to zero backlog task rows (not
   ingested), wire a synthetic, permanently-unsatisfied prereq condition instead of silently continuing — e.g. an
   auto-`false` `upstream_na__<upstream-slug>` condition that only an operator can flip `true` (on migration completion,
   or explicitly to un-gate). This preserves the "gate holds until explicitly cleared" contract even when the upstream
   is never machine-tracked.
2. **Loud park instead of silent no-op**: have `regen_backlog_from_plan.py` detect an `NA`/`local-only` upstream at
   gate-wiring time and either refuse to wire the gate with a loud warning (surfaced in backlog-regen logs / dashboard),
   or auto-park the gated task in a distinct "blocked-on-uningested-upstream" state that a human must explicitly clear —
   rather than leaving it silently dispatchable.

Whichever direction, the fix should be validated against BOTH confirmed instances above (re-run backlog regen against
`manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` and confirm its 2 gated todos no longer dispatch while
`cefi_chain_tail_v6_canonicalisation_2026_07_21.md` has open todos).

## Todos

- [ ] [INFRA] P2. Fix `regen_backlog_from_plan.py::_wire_gate_on_depends_prereqs` so `gate_on_depends: true` holds
      correctly when the `depends_on` upstream is `assigned_vm: NA` / never ingested into the backlog — implement one of
      the two candidate fixes above (or a better one), reviewed carefully given dispatch-logic blast radius. Validate
      against the 2 confirmed instances on `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`. (repo:
      agent-orchestrator)

## Codex SSOTs

`codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.
