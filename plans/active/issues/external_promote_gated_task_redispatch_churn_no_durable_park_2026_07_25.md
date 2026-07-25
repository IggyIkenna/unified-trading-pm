---
doc_type: issue
title:
  A verification task gated on an EXTERNAL promote (deployment-api LDR->main) reads "ready (no blockers)" and
  release-requeues, so it re-dispatches to a fresh worker on every tick (observed 3x — slots 8, 2, 5 — on
  deployment_registry_reaper-002 while deployment-api@3fea307 stayed off main); it should PARK durably via an
  auto_unpark prereq (as batch2-011 does), not churn through workers
summary: >-
  On 2026-07-25 main (agt-52bb99) observed deployment_registry_reaper_not_draining_stale_entries-002 re-dispatch to
  THREE workers in sequence (slot 8 ~13:14Z -> slot 2 ~12:5xZ -> slot 5 ~13:19Z). The task's remaining work is a
  verification — re-confirm the gunicorn fix deployment-api@3fea307 is live + observe reap-tick convergence — that
  cannot complete until deployment-api promotes LDR->main. That promote is stuck on a KNOWN issue
  (sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md, P2/DEVOPS, ~156min precedent). Main measured
  `git merge-base --is-ancestor 3fea307 origin/main` = FALSE on every re-dispatch (fix genuinely not on main yet). The
  gap: this EXTERNAL gate (a promote landing on main) cannot be expressed as a backend `depends_on`/blocker, so
  `/api/backlog/<id>/blockers` returns "ready (no blockers)" and the dispatcher hands it to the next free worker each
  tick. Each worker boots, does a fast check-and-release (cheap, <1s git check — not a full wasted cycle), and the task
  requeues, repeating indefinitely until the promote lands. Contrast batch2-011, which parks DURABLY via a named
  `auto_unpark__sports_satellite_ao_dispatch_batch2-011` prereq that survives re-derivation and correctly holds the task
  (and its 52 downstream) until the unpark condition fires. A worker-applied `priority_override` park (priority 999)
  does NOT survive a backlog re-derivation tick (it gets wiped and re-dispatched) — so the reaper task has no durable
  park and churns. Low blast radius (cheap check-and-release, self-terminates when the promote lands), but it is real
  dispatch noise, it repeatedly re-raises the same operator/main blocked question, and it defeats the "pick up other
  work" answer because the backend keeps handing the SAME gated task back.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, external-gate, promote-gate, auto-unpark, re-dispatch, churn, throughput, watchdog]
related:
  [
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/active/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    /plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P3
parent_epic: orchestrator_master
source:
  "main orchestrator (agt-52bb99) read-only per-task diagnosis + git ancestry checks during poll loop, 2026-07-25
  ~13:10-13:20Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# External-promote-gated verification task re-dispatches every tick instead of parking durably

## Evidence (read-only, on-host :8765 + git, 2026-07-25, main agt-52bb99)

- Task: `deployment_registry_reaper_not_draining_stale_entries-002`. Remaining work = verify `deployment-api@3fea307`
  gunicorn fix is live on the deployed container + observe reap-tick convergence — impossible until deployment-api
  promotes LDR->main.
- `/api/backlog/<id>/blockers` → **"ready (no blockers)"** on every check (the external promote gate is invisible to the
  backend).
- Re-dispatch trail (all `status=dispatched` to a different `dispatched_to` across ticks): **slot 8** (raised
  `BLK-394af695`, main answered A: park + monitor + pick up other work) -> **slot 2** (main messaged the gate context +
  park recommendation) -> **slot 5** (3rd worker, same wall).
- `git merge-base --is-ancestor 3fea307 origin/main` = **FALSE** measured at each re-dispatch — the fix is genuinely not
  on main; workers are correctly detecting a real gate, not a phantom.
- The gate's root (the stuck promote) is already tracked: `sit_validated_tree_treadmill_blocks_breaking_promotes` (P2,
  DEVOPS-owned).

## Root cause / the gap

An external condition (a commit reaching `main` via the LDR->main promote) is not representable as a backend
`depends_on`/blocker, so the task reads dispatchable and is handed to the next free worker every tick. The worker can
only discover the gate at runtime (a git ancestry check), then release — and because a worker-applied
`priority_override` park (priority 999) does NOT survive a backlog re-derivation tick, nothing makes the park stick. The
mechanism that WOULD make it stick already exists and is proven in the same fleet: the named `auto_unpark__<task-id>`
prereq (as `sports_satellite_ao_dispatch_batch2-011` uses) durably parks a task + its downstream until the unpark
condition fires.

## Todos

- [ ] [BACKEND] P3. Give a worker that hits an EXTERNAL gate (a commit/promote not yet on a target branch) a way to park
      the task DURABLY — either (a) let it set a named `auto_unpark__<task-id>` prereq keyed on the gate condition
      (mirroring batch2-011), which the dispatcher already honors and which survives re-derivation, or (b) support an
      explicit "gated on external ref reaching branch X" marker the dispatcher treats as a real blocker. **Done when**:
      a promote-gated verification task parks after the FIRST worker detects the gate and does NOT re-dispatch to a
      fresh worker every tick, resuming only when the gate clears — with a test simulating "ref not yet on main".
- [ ] [BACKEND] P3. Confirm why a `priority_override` (priority 999) park does not survive backlog re-derivation while a
      named `auto_unpark__` prereq does — document the difference so workers pick the durable mechanism for external
      gates (cross-ref RULES.md sec4 and the batch2-011 park). If `priority_override` parks are meant to be durable,
      that is a separate bug; if not, workers should stop using them for anything that must outlast a re-derivation
      tick.

## Triage / charter note

Main (agt-52bb99) diagnosed read-only (per-task `/api/backlog` + `/blockers` + `git merge-base` ancestry) and is
charter-barred from editing dispatch/task state, hand-parking tasks, or hand-editing backlog.yaml. Severity **P3**: low
blast radius (cheap check-and-release per re-dispatch, self-terminates the moment the promote lands — which the
DEVOPS-owned treadmill fix will do), but a real, repeatable dispatch-noise + throughput gap that also defeats the "pick
up other work" guidance by handing the SAME gated task back to each freed worker. Filed per the big-finding triage rule
(cross-cutting dispatch gap, recurred 3x in one window). The durable-park mechanism already exists (auto_unpark) — this
is about routing external-gate tasks through it instead of through the churn path.
