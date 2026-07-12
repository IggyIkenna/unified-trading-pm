---
doc_type: codex-ssot
title: agent-orchestrator — single-VM architecture (role-based dispatch)
summary:
  SSOT for the current agent-orchestrator deployment + dispatch model — ONE central orchestrator VM (id `planning`, EIP
  13.113.200.22) + N slot workers, role-based dispatch via `assigned_role` skill matching (no per-epic VMs, retired
  2026-06-27), `assigned_vm` restricted to `{planning, NA}`, plan-driven backlog, self-healing runtime, and the
  `ao-self-pull.sh` 15-min deploy-currency cron. Supersedes the retired 10-epic-VM topology.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, infrastructure, single-vm, role-registry, assigned-vm, deploy-currency, self-healing]
related:
  [
    ../04-architecture/agent-orchestrator-overview.md,
    ../04-architecture/role-registry.md,
    orchestrator-multi-vm-topology.md,
    ../11-project-management/doc-frontmatter-schema.md,
    ../../plans/epics/agent_operating_framework_master.md,
    ../../plans/PLAN_FORMAT.md,
  ]
created: 2026-07-12
authoritative_for: [agent-orchestrator-architecture, assigned-vm-semantics, ao-deploy-currency]
referenced_by: [cursor-configs/CLAUDE.md]
owner:
last_reviewed: 2026-07-12
code_refs:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/role_registry.py,
    agent-orchestrator/scripts/ao-self-pull.sh,
  ]
source: "operator ruling 2026-07-12 (plan-reconciliation Q&A): create missing SSOT"
---

# agent-orchestrator — single-VM architecture (role-based dispatch)

> **THE SSOT** for the current agent-orchestrator deployment + dispatch model. Created 2026-07-12 (operator ruling,
> plan-reconciliation Q&A, finding `codex-gap`) — `cursor-configs/CLAUDE.md` cited this path before the doc existed.
> Supersedes the retired 10-epic-VM topology in [`orchestrator-multi-vm-topology.md`](orchestrator-multi-vm-topology.md)
> (banner + `status: stale` added 2026-07-12) — read that doc ONLY for the historical multi-VM model.

## Topology (single-VM, since 2026-06-27)

One **central orchestrator VM** (id `planning`, AWS EC2, EIP `13.113.200.22`) runs the FastAPI/uvicorn backend
(`:8765`) + **N slot workers** (tmux sessions spawned/managed in-process — no separate epic VMs). The prior 10-epic-VM
fleet (`vm-defi` / `vm-cefi` / … one VM per epic, per `orchestrator-multi-vm-topology.md`) was retired 2026-06-27; **do
not stand up a new epic VM** or treat the old fleet as current. The separate `human-planning` VM (id
`i-0dd9812a96cdda5dc`, interactive-only, Ikenna+Harsh chats) is unaffected — it never executed backlog tasks.

## Dispatch: role-based, not VM-based

Work routes by **skill** via a plan's `assigned_role` frontmatter field, matched against the role registry
(`agent-orchestrator/agents/<role>.md`; schema SSOT [`role-registry.md`](../04-architecture/role-registry.md)), not by
"which epic VM owns this plan":

- `server/autospawn.py::_top_queued_task_params` reads the top queued task's `model`/`effort`/`thinking`/
  `assigned_role` and spawns the worker at those settings BEFORE dispatch picks its task.
- `server/prompts.py::render_worker` resolves `assigned_role` to the matching craft boot-prompt (fail-soft:
  unknown/absent role → generic worker stub, never a hard failure).
- `server/dispatch.py` / `server/orm.py` prefer a queued task whose `assigned_role` matches the slot's configured role
  (or is unset/generic), closing the gap where a role-specific worker idled on a mismatched task.

## `assigned_vm` — closed 2-value domain

Per epic `agent_operating_framework_master` D2 (locked 2026-06-24): **epic→VM delegation is DROPPED for dispatch
matching** — `parent_epic` survives only for orphan-check + priority rollup, never routing. A plan's `assigned_vm` is
the ONLY dispatch key, valid domain **`{planning, NA}`**:

- `planning` — the orchestrator VM ingests + dispatches the plan's tasks (role-based matching above).
- `NA` — intentionally unassigned; dispatched to nobody. Default for new plans (`plans/PLAN_FORMAT.md` HARD RULE — ask
  the operator before authoring a plan with `assigned_vm: planning`).
- Any other value (`vm-defi`, `vm-cefi`, …) is a STALE multi-VM-era artifact — flip to `planning`/`NA` on next touch.
- `human-planning` was the pre-2026-06-27 alias for the interactive VM; still accepted, treated as `planning`.

## Backlog is plan-driven, never hand-edited

`data/config/backlog.yaml` is DERIVED from `plans/active/*.md` `- [ ]` checkboxes by
`agent-orchestrator/server/regen_backlog_from_plan.py` — **never hand-edit the yaml**. `PlanRegenLoop` fires 60s after
boot, then every `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` (default 1800s); `pm-pull.timer` FF-pulls
`unified-trading-pm` every 5 min, so push→pickup latency is ≤35 min (or `POST /api/backlog/regen` for immediate).
Idempotent by content (dedup on `BacklogTask.brief == raw todo line`).

## Runtime self-heals — never manually kill tmux

Daemons keep the single VM's slots alive without operator intervention (full contracts:
[`agent-orchestrator-worker-liveness.md`](../04-architecture/agent-orchestrator-worker-liveness.md),
[`agent-orchestrator-autospawn.md`](../04-architecture/agent-orchestrator-autospawn.md)):

- **AutoSpawn** (`server/autospawn.py`) — wakes idle slots with queued work (60s tick).
- **WorkerLivenessWatchdog** (`server/worker_liveness_watchdog.py`) — kills stuck/silent/context-full tmux sessions;
  AutoSpawn respawns within ~60-180s.
- **Account failover** — usage-cap / auth-failure eviction rotates a slot off a dead/exhausted account onto a headroom
  account (resume-preserving where a session id exists).

Operators/agents must never manually `tmux kill-session` a slot — the watchdog + AutoSpawn own that lifecycle.

## Deploy currency — `ao-self-pull.sh`

The orchestrator backend runs `uvicorn server.server:app` from the VM's `WorkingDirectory` git checkout — nothing else
kept that checkout current (`pm-pull` covers `unified-trading-pm`; slot-cron covers `.tabs/*` worktrees).
**`scripts/ao-self-pull.sh`** closes the gap: a **15-min root cron** that FF-pulls `origin/live-defi-rollout` (git as
the slot user, ff-only, never forces; dirty/diverged → logs + skips) and `systemctl restart`s the orchestrator only when
HEAD moved. Shipped `agent-orchestrator@589b711` (2026-06-01, closed a 14-commit gap on vm-2). Hardened twice:

- `@d16d737` (2026-06-16) — also restarts when the RUNNING process predates the checkout HEAD (a FF applied off the
  restart path previously left a stale process running with no self-correction).
- `@5462959` (2026-06-23) — `_alert_wedge`: deduped Slack alert when self-pull is wedged (dirty/diverged) AND the clone
  is `>=AO_DRIFT_ALERT_COMMITS` (10) behind LDR — closes a prior silent-128-commits-behind incident.

**2026-07-12 caveat (open hardening gap)**: the wedge alert only fires on **checkout-behind** (dirty/diverged +
commits-behind ≥10) — NOT when the checkout is current but the RUNNING process is stale for N ticks (a live incident
found + operator-ruled 2026-07-12: a `regen-ldr-plans-*` generator writing into the repo tree jammed the dirty-gate ~37h
before a manual restart). Open P2 todo tracked in
`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (§ Progress Log, 2026-07-12) — do not treat
this gap as closed until that todo ships.

## Related

[`agent-orchestrator-overview.md`](../04-architecture/agent-orchestrator-overview.md) (full service architecture) ·
[`role-registry.md`](../04-architecture/role-registry.md) (role charter schema) ·
[`orchestrator-multi-vm-topology.md`](orchestrator-multi-vm-topology.md) (RETIRED — historical only) ·
`plans/PLAN_FORMAT.md` + [`doc-frontmatter-schema.md`](../11-project-management/doc-frontmatter-schema.md)
(`assigned_vm` enum authority).
