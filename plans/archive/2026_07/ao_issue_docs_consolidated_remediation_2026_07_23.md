---
doc_type: plan
title: AO issue-docs remediation — held + blocked residual (the parts NOT dispatched to AO)
summary:
  The 2026-07-23 /plan-reconcile AO-scope sweep produced 22 dispatchable todos, which were offloaded 2026-07-23 into two
  child plans — ao_remediation_a_independent_fixes (8, parallel) and ao_remediation_b_code_chain (14, sequential, gated
  behind A). What remains here is only the work that is NOT ready for the fleet — 2 safety-sensitive backend todos held
  for operator review (operator ruling Q2) and 4 operator-decision / upstream-blocked items. assigned_vm is NA so none
  of it dispatches; each becomes an AO todo only once the operator rules or the blocker clears.
status: archived
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, held, blocked, plan-reconcile]
related:
  [
    /plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/2026_08/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md,
  ]
created: 2026-07-23
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: "/plan-reconcile AO-scope run 2026-07-23"
---

# AO issue-docs remediation — held + blocked residual

> **🟡 ARCHIVED 2026-07-27 — 2 items DEFERRED (unresolved), per operator instruction.** The 2 safety-sensitive Q2-held
> todos already shipped via `ao_held_safety_fixes_dispatch_2026_07_24` (see below). Of the 4 non-dispatchable items, 2
> were resolved in place (epic-VM code artifacts ruled + deleted; dirty-fleet spot-check clean) and 2 remain genuinely
> blocked with no gate that cleared — the `/api/escalate` route-collision decision and the backlog-relations-view design
> handoff. Operator instruction 2026-07-27: stop tracking those 2 here and archive the plan rather than let it sit open
> indefinitely; both are marked **DEFERRED** below with their full context preserved inline. Neither has a separate
> issue doc, so this archived plan is their only record — re-open as a fresh todo (in a new or existing plan) once its
> blocker clears.

> The 22 dispatchable todos from the 2026-07-23 `/plan-reconcile` sweep were offloaded into two child plans:
> [`ao_remediation_a_independent_fixes_2026_07_23`](/plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md)
> (8 parallel) and
> [`ao_remediation_b_code_chain_2026_07_23`](/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md) (14
> sequential, gated behind A). **This doc holds only the work that is NOT dispatchable yet** — `assigned_vm: NA`, so
> regen never ingests it. Each item below moves to a child plan (or a new one) once the operator rules or its blocker
> clears.

## Held for operator review (operator ruling Q2, 2026-07-23) — MOVED 2026-07-24

> **Both dispatched 2026-07-24** to
> [`ao_held_safety_fixes_dispatch_2026_07_24`](/plans/archive/2026_07/ao_held_safety_fixes_dispatch_2026_07_24.md) —
> operator ruling: confirmed neither touches a file `ao_remediation_b_code_chain_2026_07_23` touches, so both run now
> rather than waiting for Plan B to finish. The regression-test gate stated in each todo, plus green `quality-gates.sh`,
> IS the review mechanism the Q2 hold was waiting on.

## Non-dispatchable — operator decision / upstream-blocked

> `[OPERATOR]` and `BLOCKED-` items. Kept here as the record; none is AO-eligible until resolved.

- [x] ✅ [OPERATOR] P2. Rule on the epic-VM code artifacts — `deployment-service/scripts/vm/launch-epic-vm.sh`,
      `launch-epic-vm-aws.sh`, and the ten `agent-orch-vm-*` prefixes registered `LONG_LIVED_LIVE` in
      `vm_prefix_registry.py`. Per-epic VMs were deprecated 2026-06-27 and CLAUDE.md says delete deprecated code with no
      shims, but the failover module received an explicit KEEP ruling on the multi-VM-may-return argument, so this is a
      judgment call rather than a cleanup. Operator direction 2026-07-23 was to file it and decide later. **Gate**: a
      recorded keep-or-delete ruling; if KEEP, the named single-VM scenario that still needs it. — **RULED 2026-07-24
      (REVISED, same day): DELETE.** First pass recorded KEEP with a named workload-isolation scenario; operator then
      overruled it — don't want the code debt right now, recreate from git history if the per-epic model ever returns.
      **Shipped `deployment-service@7438ec5`**: deleted `launch-epic-vm.sh` + `launch-epic-vm-aws.sh`, removed all 10
      `agent-orch-vm-*` entries from `vm_prefix_registry.py` and the mirrored relaunch table in
      `data_pipeline_monitors/launcher_registry.py`, fixed the 2 dependent tests (`test_vm_launcher_scripts.py`'s stale
      EXEMPT entry, `test_vm_serial_capture_cron.py`'s spot-check) and the packer README (repointed at the surviving
      `launch-central-brain-aws.sh`), full QG green. **What KEEPS the failover story whole**: the operator's actual ask
      is single-VM DISASTER RECOVERY, not per-epic isolation — `launch-central-brain-aws.sh` already does a from-scratch
      relaunch of the CENTRAL/PLANNING box with EIP reassociation (near-instant, DNS stays valid) — confirmed it never
      depended on the epic-VM scripts. The one gap found: that relaunch does NOT re-provision the self-hosted GitHub
      Actions "glue" runner pool (`scripts/self-hosted-runners/`, ~39 workflows in this repo route through it) that also
      lives on this VM — tracked as a new finding, not resolved here.
- [x] ✅ [OPERATOR] P3. Spot-check the live fleet for a slot dirty over 24h with no live session, to rank the periodic
      dirty-resolution sweep. If none exists this is a structural gap with no active incident — a reason to sequence it
      behind P1 work, NOT a reason to close it. **Gate**: the one-line finding recorded in the issue doc. — **CHECKED
      2026-07-24** (live query, all 17 slots' `git_status_json`, all repos): **zero repos dirty fleet-wide right now** —
      no slot matches dirty>24h+no-live-session. No active incident; Plan B todo #7 (the periodic dirty-resolution
      sweep) stays exactly as prioritized — this result doesn't argue for deprioritizing it, since the gap is structural
      (no watchdog owns this today) regardless of today's snapshot.
- [ ] [BACKEND] P0. BLOCKED-OPERATOR-DECISION — resolve the `/api/escalate` versus proposed `/api/escalation/{id}` route
      collision before ANY escalation code is written. `/api/escalate` already exists as the GHA-to-orchestrator CI-wall
      judgment dispatch; the proposed route is operator escalation. Whoever implements the second without noticing the
      first will either collide or wire operator escalations into the CI judgment path. Blocked on the
      `escalation_and_disaster_recovery_master` epic being un-paused. **Gate**: one of the two is renamed, or a recorded
      decision explains why the near-collision is acceptable. — **DEFERRED 2026-07-27** (operator instruction): the
      `escalation_and_disaster_recovery_master` epic is still paused, so the blocker has not cleared. Archiving this
      plan rather than continuing to hold it open; re-file as a fresh todo once the epic un-pauses.
- [ ] [UI] P0. BLOCKED-UPSTREAM-DESIGN — build the backlog-relations view once a design lands. The brief plus real data
      and a 100-task synthetic fixture were handed to the design agent on 2026-07-17; re-checked 2026-07-23 with no
      movement, no `GET /api/backlog/graph` endpoint and no relations UI commit. The model is a cross-cutting GRAPH, not
      a hierarchy, which is why three table/tree attempts were rejected. **Gate**: design received, implemented, and the
      relation a table cannot express — one prereq gating tasks in multiple plans — is visible in one view. —
      **CORRECTED 2026-07-24 (operator)**: the design is NOT stalled/lost — operator confirms it already exists (held
      outside this tracker, not yet committed anywhere this audit could see, which is why the artifact-level check read
      as "no movement"). Deliberately sequenced LAST in this remediation pass per operator direction; not AO-eligible
      until the operator brings the design in and this todo is re-scoped as a concrete build task. — **DEFERRED
      2026-07-27** (operator instruction): the design still has not been brought in. Archiving this plan rather than
      continuing to hold it open; re-file as a concrete build task once the design lands.

## Parked decisions — not in any plan (judgment calls, per task_template section 4)

Two swept todos are open design questions with no chosen target, so they are not AO-eligible and were never brought into
this plan. They stay in their own issue docs until resolved interactively:

- **`auto_park_no_flipper_rule_not_mechanism_enforced`** — "decide and build, or decline, mechanism-level enforcement".
- **`regen_positional_task_ids_not_content_stable`** — content-derived task ids, deferred until a new incident forces
  it. **RULED 2026-07-28** (operator gated-decision closeout pass): the 2026-07-25 incident meets this trigger — see
  `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`'s updated `[BACKEND] P2` todo for
  the ruling + fully-scoped mandate. Archive convention (this doc's own 2026-07-27 Progress Log entry) means this
  historical record is not otherwise retroactively edited — this one line is the exception, added only to prevent a
  reader following this doc alone from citing a since-superseded deferral.

## Progress Log

- **2026-07-23**: Authored from the `/plan-reconcile` AO-scope sweep as one draft plan of 28 todos, then split per
  operator rulings: Q1 (split for parallelism) moved the 22 dispatchable todos into child plans A + B; Q2 (hold the 2
  safety-sensitive backend todos) kept them here. This doc was flipped `draft` -> `active` + `assigned_vm: planning` ->
  `NA` so it now tracks only the held/blocked residual without dispatching it.
- **2026-07-27**: Operator instruction: the 2 remaining open items (route-collision `[BACKEND]` P0, backlog-relations
  `[UI]` P0) are still genuinely blocked — neither gate cleared — but archive the plan rather than keep it open
  indefinitely waiting on them. Both marked **DEFERRED** inline with their full context preserved; neither has a
  separate issue doc, so this archived doc is their only record until re-filed. `status` flipped `active` -> `archived`,
  moved to `plans/archive/2026_07/`. Referrer paths fixed corpus-wide: `plans/epics/orchestrator_master.md` (removed —
  matches how sibling plans A/B and the Q2 dispatch plan were delisted on archival),
  `plans/active/ao_consolidated_closeout_2026_07_25.md` (Track 5 Sources link repointed + noted archived),
  `plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md` (2 prose references repointed), and
  `/plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (regenerated via
  `regenerate_active_plan_inventory.py`, not hand-edited — it's auto-generated). The 3 sibling docs already in
  `plans/archive/` that also reference this plan (`ao_remediation_a_independent_fixes_2026_07_23`,
  `ao_remediation_b_code_chain_2026_07_23`, `ao_held_safety_fixes_dispatch_2026_07_24`) and
  `master_to_live_defi_2026_05_23` were left as-is — archives are closed historical records
  (`check_frontmatter_schema.py` explicitly excludes `plans/archive/**`, operator decision 2026-07-04), not
  retroactively maintained.
