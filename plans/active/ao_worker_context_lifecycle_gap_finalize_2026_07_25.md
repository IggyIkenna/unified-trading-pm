---
doc_type: plan
title: AO plain-worker context lifecycle gap — finalize
summary: >-
  Gated closeout for ao_worker_context_lifecycle_gap_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 12 of that plan's dispatchable todos are done. Re-verifies each done-claim's evidence, re-checks todo 8's
  BLOCKED-OPERATOR-DECISION (context_burn_kill default flip) to see whether the operator has since ruled on it and spins
  it into a new tracked todo if so, and runs the standard archival ritual.
status: draft
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [orchestrator, context-management, close-out]
related: [/plans/active/ao_worker_context_lifecycle_gap_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_worker_context_lifecycle_gap_2026_07_25]
gate_on_depends: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4): every AO-dispatched plan needs a gated finalize plan.
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO plain-worker context lifecycle gap — finalize

> **Machine-gated on `ao_worker_context_lifecycle_gap_2026_07_25.md`** — will not dispatch until all 12 dispatchable
> todos in that plan are `done` (todo 8 there is `[OPERATOR]`/`BLOCKED-OPERATOR-DECISION` and never ingested, so it does
> not block this gate — handled explicitly by todo 2 below instead).
>
> **Status starts `draft`** (not `active`) — this finalize plan should stay undispatched until the parent plan is
> actually close to done; flip to `active` once the parent's todos are substantially underway, per the draft-gated
> phase-chain pattern in task_template.md §4.

## Todos

- [ ] [REVIEW] P0. **Re-verify all 12 parent-plan done-claims.** For each dispatchable todo in
      `ao_worker_context_lifecycle_gap_2026_07_25.md`, confirm the cited evidence (commit SHA + a resolving
      `quality-gates.sh` run, or the specific test file/name for todos that only claim "a unit test asserts...")
      actually exists and passes — re-run `git show <sha>` for every cited commit; re-run the cited tests directly
      rather than trusting the checkbox. **Done when**: all 12 todos' evidence independently re-verified, any
      discrepancy logged in this doc's Progress Log and re-opened as a new todo if evidence doesn't hold up.
- [ ] [INFRA] P0. **Re-check todo 8's `BLOCKED-OPERATOR-DECISION`** (context_burn_kill default flip). Ask whether the
      operator has ruled on it since the parent plan shipped; if yes, spin the decision into a new tracked todo (either
      "flip context_burn_kill default to True in server/config.py, with tests" or "explicitly keep False, document why
      in the config comment") in a fresh small plan or as a follow-up here. If no ruling yet, leave it open and note
      that explicitly — do not silently drop it. **Done when**: this doc's Progress Log states either the new todo's
      location or that the decision remains genuinely open.
- [ ] [REVIEW] P0. **Cross-check against `ao_fleet_throughput_incident_finalize_2026_07_25.md`'s dormant-slot finding**
      (todo 2 of that finalize plan) — if AutoSpawn has a concurrency cap that limits which slots ever run long enough
      to need this plan's gate/directive logic, note whether that changes this plan's expected impact. **Done when**: a
      one-paragraph cross-check note is added to this doc's Progress Log.
- [ ] [INFRA] P0. **Run the standard 6-step archival ritual** on `ao_worker_context_lifecycle_gap_2026_07_25.md`:
      migrate any DEFERRED items into new tracked todos, add a `> **🟢 ARCHIVED**` banner, run the codex-alignment check
      (does `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` need a new section documenting the
      `/done`/`/progress` `directive` field contract this plan introduced?), update CLAUDE.md/codex on the new contract
      (the worker-scoped compact-gate mechanism belongs alongside the existing `context_lifecycle.py` description), fix
      every referrer's path corpus-wide (`grep -rl ao_worker_context_lifecycle_gap_2026_07_25 plans/ codex/` and update
      each hit), then move the plan file to `plans/archive/2026_07/`. **Done when**: the plan is archived with a banner,
      zero corpus-wide stale referrers remain (verified by the grep above returning only the archived copy's own path),
      and the new `directive`-field contract is documented in codex.
