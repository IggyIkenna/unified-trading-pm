---
doc_type: plan
title: Worker lifecycle by dispatch-context — persistent plan-backlog drain vs event-spawned one-shots
summary:
  Plan-backlog workers are wrongly reaped after every task because the reap-on-done gate keys on the STATIC role field
  (role_one_shot) and four plan-worker roles are declared one_shot. Roles are just boot prompts, so the field can't
  decide reaping. Rekey reaping on DISPATCH CONTEXT (who fired the worker) — event-spawned crafts carry a one_shot
  AgentRow and reap on /done; plan-backlog workers have none and persist, draining the next ready task in one session
  and going idle (the reclaimer retires them) when none is ready. Conversational context-resume is an explicit non-goal
  (durable state is in the plan/Progress Log) — A1 (reap-by-dispatch-context) is the whole fix.
status: complete # (was: active) ARCHIVED 2026-07-23 — all 4 P0 todos shipped + deployed + live-verified; the one [DEFERRED] P3 residual migrated to ao_open_issues_consolidated_close_out_2026_07_17.md Phase 8.
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, liveness, dispatch, lifecycle, reaper, resume, backlog-drain]
related:
  [
    /plans/archive/2026_07/ao_uniform_agent_liveness_contract_2026_07_20.md,
    /plans/archive/2026_07/ao_worker_lifecycle_reap_2026_07_20.md,
    ao_task_lifecycle_2026_07_09.md,
  ]
created: 2026-07-21
last_updated: 2026-07-23
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-supervised, NOT AO-dispatched (core live-fleet dispatch/lifecycle code)
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo dispatch/lifecycle change; design decided below, execution is mechanical
thinking_tier: high # a live-fleet lifecycle change — the reap/resume interactions are the risky part
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# Worker lifecycle by dispatch-context

> **✅ COMPLETE + ARCHIVED 2026-07-23 (operator instruction).** All 4 P0 todos shipped, deployed and live-verified
> (`agent-orchestrator@c17bd4e` A1 + `@c255895` the resume-pass fix; clean restart MainPID 240795, 13:33 UTC 2026-07-21;
> `role_one_shot` confirmed gone from the deployed `slots_worker.py`, `/health` 200, loops up). The single remaining
> `[DEFERRED]` P3 item (role lifecycle-field reclassification) had **no successor owner** — it is migrated by this
> archival to
> [`ao_open_issues_consolidated_close_out_2026_07_17.md`](ao_open_issues_consolidated_close_out_2026_07_17.md) **Phase 8
> — residuals inherited from ARCHIVED child plans**, which is that section's exact purpose. Nothing is descoped and
> nothing is stranded. Codex SSOTs were updated in-plan (see the DOCS todo) and re-verified present at archival.
>
> **The 🟡 backend-STOPPED banner below is DISCHARGED** — the service was restarted at the deploy todo and verified
> healthy; it is kept only as the historical record of how the change was landed. Do not read it as current state.

> **Operator design decisions (2026-07-21, slot-16).** Reaping is a property of **who fired the worker**, not the static
> role field. Plan-backlog workers **persist** (drain ready tasks in one session; go idle → the reclaimer retires them);
> event-spawned crafts are **one-shot** (reap on `/done`). Conversational context-resume is an explicit **non-goal**
> (durable state is in the plan/Progress Log) — the elaborate resume machinery discussed was **built then reverted**;
> **A1 (reap-by-dispatch-context) is the whole fix.** The 3-case model is the codex SSOT — this plan implements it.
>
> **Codex SSOTs (READ before touching code; plan↔codex drift is review-blocking):**
>
> - `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Dispatch-context-driven lifecycle" (THIS work's
>   SSOT)
> - `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "One-off / scheduled completion contract" (the
>   `/done` → archive → reap contract that crafts already follow; unchanged)
> - `plans/active/task_template.md` §4 (intra-plan concurrency: tasks are the unit, parallel by default,
>   `sequential: true` serialises; prereqs from `sequential`/`depends_on`+`gate_on_depends`, enforced by
>   `dispatch.py::_prereqs_met`)

> **🟡 Live-fleet change — backend is STOPPED while this lands (operator, 2026-07-21).** `orchestrator.service` is
> `inactive` (stopped to halt the wrong per-task reaping). It is restarted only at the DEPLOY todo, after the gate is
> green. Do not restart it mid-implementation.

## Why (the defect, measured 2026-07-21)

Two deployment-ui plans were allocated to AO. Each task was dispatched to a fresh `backend_engineer` worker that did ONE
task, `/done`'d, and was **reaped** — then a fresh worker spawned for the next task. One plan's tasks sprayed across
slots (cost_per_day tasks ran on slot 3 **and** slot 4); slots churned spawn→task→reap→respawn every few minutes. Every
task completed + verified on origin (no work lost), but the churn is waste and defeats intra-plan context.

Root cause: the reap-on-done gate (`server/routes/slots_worker.py:1129-1158`) fires on
**`role_one_shot OR agent_one_shot`**, and `role_one_shot` reads the **static role field** — `backend_engineer` (and
`ui_developer`, `quant_dev`, `infra`) are declared `lifecycle: one_shot`. Roles are just boot prompts (the same prompt
can back a plan worker or a scheduled worker), so the field cannot decide reaping. The authoritative signal is the
**dispatch context**: an event-spawned craft carries a `one_shot`/`scheduled` `AgentRow` (`escalation.py` register
pattern); a plan-backlog worker has **none** (verified: the `agents` table was empty for the deployment-ui dispatches).

## Design (decided 2026-07-21, simplified per operator ruling) — reap by dispatch context

Reaping keys on **dispatch context** (who fired the worker), not the static role field. A plan-backlog worker
persistently drains the backlog; at `/done`:

| #   | Situation                                                    | Action                                                                                                                                  |
| --- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | next task ready                                              | **same live session drains it** — no reap (consecutive ready tasks, incl. a `sequential` plan's chain, run in ONE session)              |
| 2   | no ready task (backlog drained, OR only prereq-blocked left) | go **idle → the idle-reclaimer retires it** (~`watchdog_idle_session_ticks`, default 2×60s); a cleared blocked task gets a FRESH worker |
| 3   | event-spawned craft (`one_shot`/`scheduled` `AgentRow`)      | reap on `/done`, always                                                                                                                 |

**Conversational context-resume is an explicit NON-GOAL (operator ruling 2026-07-21).** No `--resume`-with-context, no
session-per-plan binding, no `target_slot` pinning of a plan to a slot. **Durable state lives in the plan items +
Progress Log** (+ shipped commits); a fresh worker on a cleared blocked task re-reads those and continues — losing
conversational memory re-reads a plan, it does not lose work. (The dead-worker `--resume` for a MID-task crash —
`resume_lifecycle.py`, `ao_task_lifecycle` Phase B — is a separate mechanism and stays.) SSOT:
`/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Dispatch-context-driven lifecycle".

## Todos

- [x] [BACKEND] P0. **A1 — Reap-on-done keys on dispatch context, not the static role field.** ✅ DONE — `done_slot`
      (`server/routes/slots_worker.py`) DROPPED the `role_one_shot` term + the now-unused `role_registry` import; reap
      on `/done` only when `agent_one_shot` (a bound `one_shot` `AgentRow` owns the session). A plan-backlog worker (no
      such AgentRow) is never reaped by role → it drains the next ready task in the same session (case 1) and goes idle
      when none is ready (case 2). Regression tests `test_plan_backlog_worker_not_reaped_on_done` +
      `test_event_spawned_craft_reaps_on_done` (`tests/test_task_lifecycle_done_gate_resume.py`). AO gate green (1557
      py + 113 vitest).
- [x] [BACKEND] P0. **A2 — Retire-when-no-work — satisfied by the existing idle-reclaimer (no new code).** A plan-worker
      with no ready task goes idle, and `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` reaps the
      idle-lingering session after `watchdog_idle_session_ticks` (default 2×60s ≈ 2 min) → the slot retires; AutoSpawn
      respawns a fresh worker only when claimable work exists. No idle-loop (the finished-immortal bug) and no per-task
      churn (the reap-per-task defect). Prompt-reap-at-`/done` was considered + dropped as unnecessary (the ~2-min
      reclaim is fine).
- [x] [DOCS] P0. **Simplify the SSOTs to the shipped model.** ✅
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Dispatch-context-driven lifecycle" +
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` reduced to the 3-case model + the
      context-resume NON-GOAL; the resume / session-per-plan / `≤1`-wait content removed.
- [x] [OPS] P0. **Deploy + live-verify.** ✅ Quickmerged A1 (`agent-orchestrator@c17bd4e`), synced the deployed
      checkout, clean `systemctl restart` (MainPID 240795, 13:33 UTC). Verified live: `role_one_shot` gone from the
      deployed `slots_worker.py`, `/health` 200, all loops up incl. `CIReconcileLoop interval=900s`. **Also cleared a
      pre-existing `QueuePool` exhaustion** (someone had restarted the service at 13:00 onto a leaking pool; the clean
      restart reset it — 0 pool errors since). The live multi-task drain manifests on the next plan dispatch; the code
      behaviour is unit-proven by `test_plan_backlog_worker_not_reaped_on_done` +
      `test_event_spawned_craft_reaps_on_done`.

### Dropped (operator ruling 2026-07-21 — over-engineering)

- **B1/B2/B3 (resume-with-context, session-per-plan, sequential-slot-binding), C1 (slot preference), the
  `resume_eligible_plan_ref` field + `≤1`-wait knob** — all removed. Context-preservation is a nice-to-have, not a
  necessity: durable state lives in the plan/Progress Log, so a fresh worker on a cleared task loses nothing that
  matters. (Built + reverted this session; **A1 is the whole fix.**)

### Deferred (tracked, not this plan's scope) — MIGRATED OUT 2026-07-23

🔁 **MOVED →
[`ao_open_issues_consolidated_close_out_2026_07_17.md`](ao_open_issues_consolidated_close_out_2026_07_17.md) § "Phase 8
— residuals inherited from ARCHIVED child plans".** Checkbox removed here so the archived plan cannot double-count it.

**Role lifecycle-field reclassification** — align the declared `lifecycle` on plan-worker roles
(`backend_engineer`/`ui_developer`/`quant_dev`/`infra` `one_shot → persistent`; resolve `data_engineering`
scheduled-vs-persistent) with reality. NOT required for correctness (reaping keys on dispatch context, not the field).
Operator-owned timing: "after updating docs, fixing this, and everything discussed" (2026-07-21).

## Progress Log

- **2026-07-21 (design + docs-first + A1):** Operator-directed. Design discussed + locked over slot-16, then
  **simplified by operator ruling**: conversational context-preservation is a nice-to-have, not a necessity (durable
  state is in the plan/Progress Log), so the elaborate resume machinery (B1/B2/B3/C1 — `resume_eligible_plan_ref` field,
  migration, same-slot `--resume`, session-per-plan, `≤1`-wait, sequential-slot-binding) was **built then reverted**;
  **A1 is the whole fix.** A1 landed + tested (reap-by-dispatch-context, drop `role_one_shot`); retire-when-no-work is
  handled by the existing idle-reclaimer (no new code). Codex SSOTs (worker-liveness + single-vm-architecture) reduced
  to the 3-case model + the context-resume NON-GOAL. Backend STOPPED throughout; deploy is the one remaining todo. Also
  verified (kept for the record): jsonl transcripts survive reaps (no deletion path; 1547/1650 persist for slots 2/3).
- **2026-07-21 (deploy + 2 pre-existing live bugs found & fixed):** A1 quickmerged (`agent-orchestrator@c17bd4e`),
  deployed, clean restart, verified (reap gate live, `/health` 200, loops up incl. CIReconcile). During deploy the
  backend (restarted by someone else at 13:00) showed two pre-existing issues, both **unrelated to A1**, both cleared:
  (1) an ongoing **`QueuePool` connection exhaustion** — fixed by the clean restart (0 errors since); (2) the AutoSpawn
  **resume pass crashing every tick** on `AttributeError: 'SimpleNamespace' has no attribute 'context_used_pct'` —
  `snapshot_slot` omitted the field `_do_spawn` reads on the resume path (latent since the ~07-14 context-aware resume
  gate; only fires when a slot is `resume_pending`). Fixed 1-line + regression test
  (`test_snapshot_slot_carries_context_used_pct`), quickmerged `agent-orchestrator@c255895`; verified live — resume-pass
  errors → 0 and **slot 4's stuck dead-worker resume completed** (`resume_pending` cleared → `status=working`). **Plan
  complete.**

## Lessons (2026-07-21)

- **Lifecycle is a property of the DISPATCH, not the role.** Roles are boot prompts; the same prompt backs a plan worker
  or a scheduled one, so the static `role.lifecycle` field cannot decide reaping. The authoritative signal is "who fired
  it" — an event-spawned craft carries a `one_shot`/`scheduled` `AgentRow`; a plan-backlog worker has none. Keying
  reaping on the field (`role_one_shot`) was the exact bug.
- **Don't over-engineer context-preservation.** The design ballooned (session-per-plan, same-slot `--resume`,
  sequential-slot-binding, `≤1`-wait) before the operator ruled it a **non-goal**: durable state lives in the plan
  items + Progress Log, so a fresh worker on a cleared task loses nothing that matters. Built ~5 pieces, then reverted
  to a 2-line fix. Lesson: name the end-game (correctness vs efficiency) before building the mechanism.
- **A detached scalar snapshot must carry EVERY field its consumer READS, not just the obvious ones.** `snapshot_slot`
  omitted `context_used_pct`; `_do_spawn` reads it only on the resume path (`… if resume_session_id else 0`), so the
  crash was latent for weeks and fired only when a slot was `resume_pending`. When you add a `slot.<attr>` READ to
  `_do_spawn`, add it to `snapshot_slot` in the same change (writes to a SimpleNamespace are harmless; reads of a
  missing attr crash).
- **`--reload` deploys cause TRANSIENT DB-contention bursts** (`database is locked` / brief `QueuePool` timeouts) while
  the worker restarts — they self-recover; do NOT panic-restart into them (that overlaps two processes → the same lock).
  But an **ONGOING** `QueuePool` exhaustion (seen here after another operator's 13:00 restart) needs a **clean
  `systemctl restart`** to reset the pool — `--reload` alone won't. Distinguish transient (settles in <30s) from ongoing
  (keeps firing) before acting.
- **The backend can be restarted by someone else mid-session.** It was stopped for this work, yet a peer
  `systemctl restart`'d it at 13:00 onto the pre-fix code — verify the live `ExecMainStartTimestamp` / running SHA
  before assuming the state you left it in.

## Deferred work — migrated to:

**RESOLVED 2026-07-23 (at archival):**
[`ao_open_issues_consolidated_close_out_2026_07_17.md`](ao_open_issues_consolidated_close_out_2026_07_17.md) **§ "Phase
8 — residuals inherited from ARCHIVED child plans"** now owns the "Role lifecycle-field reclassification" `[DEFERRED]`
P3 item. That section exists precisely for calendar-time- or operator-gated residuals left by archived AO child plans,
and the item carries its source citation back to this plan so the evidence trail survives.

_(was: **Not yet identified** — grepping `plans/active/` and `plans/epics/` for "role lifecycle" / "one_shot" /
"persistent" reclassification found no owner, so this plan remained the record of the deferral until a successor was
authored. The archival supplied that successor rather than creating a new plan for one P3 item.)_
