---
doc_type: plan
title: Worker lifecycle by dispatch-context — persistent plan-backlog drain vs event-spawned one-shots
summary:
  Plan-backlog workers are wrongly reaped after every task because the reap-on-done gate keys on the STATIC role field
  (role_one_shot) and four plan-worker roles are declared one_shot. Roles are just boot prompts, so the field can't
  decide reaping. Rekey reaping on DISPATCH CONTEXT (who fired the worker) — event-spawned crafts carry a one_shot
  AgentRow and reap on /done; plan-backlog workers have none and persist by draining the next ready task, retiring when
  the work is done, or going idle+preserve-session and --resume (same-slot only) when a blocked task clears.
status: active # operator-directed 2026-07-21 (slot-16). LOCAL execution — this session works it, backend STOPPED while it lands.
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, liveness, dispatch, lifecycle, reaper, resume, backlog-drain]
related:
  [
    ao_uniform_agent_liveness_contract_2026_07_20.md,
    ao_worker_lifecycle_reap_2026_07_20.md,
    ao_task_lifecycle_2026_07_09.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
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

> **Operator design decisions (2026-07-21, slot-16 discussion, all locked before any code).** Reaping is a property of
> **who fired the worker**, not the static role field. Plan-backlog workers **persist** (drain the backlog);
> event-spawned crafts are **one-shot** (reap on `/done`). The full model, the four lifecycle cases, and the resume
> rules are the codex SSOT — this plan implements them.
>
> **Codex SSOTs (READ before touching code; plan↔codex drift is review-blocking):**
>
> - `codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Dispatch-context-driven lifecycle" (THIS work's
>   SSOT)
> - `codex/04-architecture/agent-orchestrator-worker-liveness.md` § "One-off / scheduled completion contract" (the
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

## Design (decided 2026-07-21) — the four lifecycle cases

Reaping keys on dispatch context. A plan-backlog worker persistently drains the backlog; at `/done`:

| #   | Situation                                           | Action                                                                                                          |
| --- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | next task ready                                     | same live session drains it — no reap                                                                           |
| 2   | blocked, work remains                               | go idle → idle-reclaimer reaps (correct); preserve `claude_session_id`; `--resume` when the blocked task clears |
| 3   | no work left                                        | retire + reap now (don't idle-loop a finished plan)                                                             |
| 4   | event-spawned craft (one_shot/scheduled `AgentRow`) | reap on `/done`, always                                                                                         |

**Resume rules (case 2).** One session **per plan-context**, reaped+preserved on plan-switch (each plan's transcript
stays independently resumable). `--resume` is **same-slot only** — transcripts are bound to `orch-slot-N` + the slot's
`.tabs/N` worktree cwd, so cross-slot resume is unsafe and **not done**. When a blocked task clears: if the origin slot
frees soon (**`≤ 1` task remaining**, config knob) → wait, `--resume` on the origin slot; else → dispatch the cleared
task to another free slot as a **fresh spawn** (safe — a task routable to any slot is an independent, different-file
task by the intra-plan-concurrency rule). New plans prefer free slots **not** holding a resume obligation.

**Transcripts are the resume substrate and survive reaps** (verified: no code deletes the config dir / `projects/` /
`.jsonl`; reaped sessions persist at `~/.claude-configs/orch-slot-N/…`). The existing dead-worker resume infra
(`SlotRow.claude_session_id` / `resume_pending_session_id` / `resume_fresh_context_pct`, `ao_task_lifecycle` Phase B) is
the substrate to extend — not build from scratch.

## Todos

### Phase A — reap by dispatch context (the core fix)

- [ ] [BACKEND] P0. **A1 — Reap-on-done keys on dispatch context, not the static role field.** In
      `server/routes/slots_worker.py` (`_done_task` completion path, ~L1099-1158) DROP the `role_one_shot` term; reap on
      `/done` only when `agent_one_shot` (a bound `one_shot`/`scheduled` `AgentRow` owns the session) — case 4 — OR the
      retire-when-no-work condition (A2). A plan-backlog worker (no such AgentRow) is NEVER reaped by role. **Gate**: a
      `backend_engineer` plan-worker that `/done`s a task with a next task ready keeps its session and drains it
      (regression test); an escalation `cicd` worker still reaps on `/done` (unchanged); QG green.
- [ ] [BACKEND] P0. **A2 — Retire-when-no-work (case 3).** When a plan-backlog worker `/done`s and `pick_next_task`
      returns None AND there is no non-terminal task this worker will ever get (backlog drained for its routing),
      retire + reap now (archive/free the slot; kill the session) — do NOT idle-loop. Distinguish from case 2 (blocked,
      work remains) which must NOT reap-at-done. **Gate**: a worker finishing the last dispatchable task of the backlog
      is reaped promptly; a worker whose only remaining tasks are prereq-blocked goes idle (not retired). Cite the
      completeness signal used.

### Phase B — persistence + resume

- [ ] [BACKEND] P0. **B1 — Blocked→idle→preserve session (case 2).** At `/done` with no ready task but non-terminal work
      remaining, leave the worker idle WITHOUT reaping-at-done; the idle-reclaimer reaps the tmux session on its normal
      tick, and `claude_session_id` is preserved as resume-eligible (do not null it). **Gate**: a worker blocked on a
      prereq goes idle, its session is later reaped, and its `claude_session_id` is retained for resume.
- [ ] [BACKEND] P0. **B2 — Resume a cleared blocked task, same-slot with the `≤1` wait rule.** When a prereq clears and
      the cleared task's plan-context has a preserved session on its origin slot: if that slot has `≤ 1` task remaining
      → hold the cleared task for it and re-spawn via `--resume <claude_session_id>` on the origin slot; else → dispatch
      it to another free slot as a fresh spawn. Reuse the `resume_pending_session_id` machinery. Config knob
      `ORCHESTRATOR_RESUME_WAIT_MAX_REMAINING_TASKS` (default 1). **Gate**: origin-slot ≤1-remaining → resumed with
      prior context on the same slot; origin-slot busy → fresh spawn elsewhere, no cross-slot resume attempted.
- [ ] [BACKEND] P1. **B3 — One session per plan-context, preserved on plan-switch.** When a persistent worker's current
      plan blocks (case 2) and the next dispatched task is a DIFFERENT plan, reap+preserve the current session and start
      a FRESH session for the new plan (so each plan's context is independently resumable). **Gate**: a worker that
      drains plan A (blocks), then picks up plan B, has A's session preserved on disk and a distinct session for B;
      resuming A later loads A's context, not A+B.

### Phase C — slot selection + tests + deploy

- [ ] [BACKEND] P1. **C1 — New-plan slot preference.** When assigning a NEW plan/task, prefer a free slot NOT holding a
      blocked-prereq resume obligation (`resume_pending_session_id` set); fall back to any free slot only if none
      available. Wire into the slot-selection path (`dispatch.py` / `_task_is_routable_to` / the free-slot picker).
      **Gate**: with one resume-pending free slot and one clean free slot, a new plan goes to the clean slot.
- [ ] [BACKEND] P0. **C2 — Tests.** Cover: reap-by-dispatch-context (plan-worker persists, craft reaps); retire-on-
      no-work; blocked→idle→preserve; same-slot resume vs fresh-spawn-elsewhere at the `≤1` boundary;
      session-per-plan-context on switch; new-plan slot preference. Extend `tests/test_slots_worker*.py` /
      `tests/test_dispatch*.py` / the lifecycle tests. **Gate**: new cases fail on `main`, pass on the branch.
- [ ] [BACKEND] P0. **C3 — AO quality gate green** (`bash scripts/quality-gates.sh`: ruff + ruff-format + basedpyright +
      pytest + dashboard tsc/vitest). Commit per shippable unit (backend STOPPED, so commit freely; ship via quickmerge
      at the deploy step).
- [ ] [OPS] P0. **C4 — Deploy + live-verify.** Quickmerge to LDR; sync the deployed checkout; restart
      `orchestrator.service`; re-allocate a small multi-task plan and verify LIVE: (a) ONE worker drains multiple tasks
      in one session (case 1), (b) a finished plan retires the worker promptly (case 3), (c) a prereq-blocked task goes
      idle then resumes same-slot with context (case 2/B2), (d) no per-task spawn/reap churn. Cite activity-log
      evidence.

### Deferred (tracked, not this plan's scope)

- [ ] [DEFERRED] P3. **Role lifecycle-field reclassification** — align the declared `lifecycle` on plan-worker roles
      (`backend_engineer`/`ui_developer`/`quant_dev`/`infra` `one_shot → persistent`; resolve `data_engineering`
      scheduled-vs-persistent) with reality. NOT required for correctness (reaping keys on dispatch context, not the
      field). Operator-owned timing: "after updating docs, fixing this, and everything discussed" (2026-07-21).

## Progress Log

- **2026-07-21 (design + docs-first):** Operator-directed. Full design discussed + locked over slot-16 (dispatch-context
  reaping; four cases; one-session-per-plan-context; same-slot-resume-only; `≤1`-task resume-wait; new-plan slot
  preference; role-field reclassification deferred). Verified: jsonl transcripts survive reaps (no deletion path;
  1547/1650 transcripts persist for slots 2/3 incl. today's reaped sessions); the `--resume` infra already exists
  (`ao_task_lifecycle` Phase B). Codex SSOT written FIRST (`agent-orchestrator-worker-liveness.md` § "Dispatch-context-
  driven lifecycle"). Backend STOPPED throughout. Implementation (Phases A-C) pending.
