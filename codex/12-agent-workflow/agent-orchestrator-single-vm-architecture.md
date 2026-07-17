---
doc_type: codex-ssot
title: agent-orchestrator — architecture & operating model (single VM, role-based dispatch)
summary:
  THE governing SSOT for what agent-orchestrator is and how it behaves — operator tooling that runs the Claude Code
  fleet on ONE central VM (id `planning`, EIP 13.113.200.22) with N in-process slot workers. Covers the role/scope
  boundary (NOT a trading service), the TWO worker classes (plan-driven backlog workers vs standing/event-driven
  agents), and the four behaviour domains each in its own section — worker lifecycle, task lifecycle, dispatch, and
  regen — written intention-first so drift between doc and code is easy to spot. `assigned_vm ∈ {planning, NA}` only; no
  epic VMs (retired 2026-06-27).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    orchestrator,
    architecture,
    operating-model,
    single-vm,
    worker-classes,
    dispatch,
    regen,
    worker-lifecycle,
    task-lifecycle,
  ]
related:
  [
    ../04-architecture/agent-orchestrator-overview.md,
    ../04-architecture/agent-orchestrator-autospawn.md,
    ../04-architecture/agent-orchestrator-worker-liveness.md,
    ../04-architecture/agent-orchestrator-backlog-state-alignment.md,
    orchestrator-safety-mechanisms.md,
    ../11-project-management/doc-frontmatter-schema.md,
    ../../plans/PLAN_FORMAT.md,
  ]
created: 2026-07-12
authoritative_for:
  [
    agent-orchestrator-architecture,
    agent-orchestrator-operating-model,
    agent-orchestrator-worker-classes,
    assigned-vm-semantics,
    ao-deploy-currency,
    ao-read-only-status-check,
  ]
referenced_by: [cursor-configs/CLAUDE.md, cursor-configs/skills/check-agent-orchestrator/SKILL.md]
owner:
last_reviewed: 2026-07-18
code_refs:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/role_registry.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/scripts/ao-self-pull.sh,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
  ]
source:
  "operator ruling 2026-07-12 (create missing SSOT) + 2026-07-18 (make this THE operating-model SSOT: two worker classes
  + behaviour-domain sections)"
---

# agent-orchestrator — architecture & operating model

> **THE governing SSOT** for what agent-orchestrator is, why it exists, and how it behaves. Read this first; the
> [service-implementation reference](../04-architecture/agent-orchestrator-overview.md) (tech stack, auth, endpoints,
> deploy) and the per-domain docs it links sit under it. This doc is written **intention-first**: each behaviour states
> what the system is _meant_ to do so a reader can compare it against the cited code and see drift immediately.

## Role — what AO is, and what it is not

**agent-orchestrator is operator tooling that runs the Claude Code worker fleet.** It is a FastAPI + SQLite backend with
a React dashboard that turns idle worker slots into a self-driving workforce: workers report via HTTP endpoints
(`/boot`, `/progress`, `/done`, `/blocked`, `/heartbeat`) instead of the retired file-based dance (LEDGER.md + ping
files + a human hand-dispatching). State lives in SQLite (`data/state/state.db`); config in YAML/JSON under
`data/config/`.

**The need**: N worker slots should autonomously execute the plan backlog and keep themselves alive without a human in
the loop. AO makes that loop **plan-driven** (work derives from plan checkboxes), **self-healing** (the fleet wakes,
kills, resumes, and rotates itself), and **observable** (one dashboard + one activity log).

**AO is NOT a trading service.** No `asset_group`, no batch/live modes, no kill-switch surface, no event-bus emission to
UTL, not a node in the trading DAG (instruments → MTDS → features → strategy → execution). It coordinates _agents_, not
markets. Do not add `--asset-group` flags, backtest modes, or STARTED/STOPPED lifecycle events to it. (Full
service-vs-trading contrast:
[overview.md § "Difference vs trading services"](../04-architecture/agent-orchestrator-overview.md).)

## Topology — one VM, N in-process slots (since 2026-06-27)

One **central orchestrator VM** (id `planning`, AWS EC2 ap-northeast-1, EIP `13.113.200.22`, instance
`i-0c9b283b31d6b5ca7`) runs the uvicorn backend (`:8765`) **and** all N slot workers as in-process tmux sessions
(`orch-slot-N`). There are **no epic VMs** — the prior 10-epic-VM fleet (`vm-defi` / `vm-cefi` / … one VM per epic) was
retired 2026-06-27; do not stand up a new epic VM or treat that fleet as current. The separate `human-planning` VM (id
`i-0dd9812a96cdda5dc`, interactive-only) is unaffected — it never executes backlog tasks.

## The two worker classes

Every agent the orchestrator runs falls into one of two classes. The distinction matters because they are _triggered_
differently, _tracked_ differently, and _reaped_ differently — conflating them is a recurring source of bugs (e.g. an
escalator being judged by backlog rules, or a scheduled job counted as a stuck worker).

### Class A — Backlog workers (plan-driven)

Craft workers dispatched from the **plan-derived backlog** by skill match. This is the class the dispatch + regen +
autospawn machinery below governs.

- **Roles** (`[TAG]` → role, `_TAG_TO_ROLE` in `regen_backlog_from_plan.py`): `[BACKEND]`→`backend_engineer`,
  `[DATA]`→`data_engineering`, `[INFRA]`→`infra`, `[UI]`→`ui_developer`, `[REVIEW]`→`review`. Generic
  `[CODE]`/`[SCRIPT]` fall back to the plan's `assigned_role`. Charters live in `unified-trading-pm/agents/<role>.md`.
- **Trigger**: a `queued`, prereq-met, role-matched task exists and AutoSpawn wakes a free slot for it.
- **Lifecycle**: `/boot` → claim a task → work → `/done` (clean-tree + checkbox-flip gated) → idle → next task. A dead
  worker mid-task RESUMES (`--resume`) or requeues (§ Worker lifecycle).
- **Identity**: the task carries `dispatched_to`, `done_sha`, `brief_hash`; the slot carries `current_task`.

### Class B — Standing & event-driven agents (NOT plan-driven)

These never come from `backlog.yaml`. They are triggered by the keeper, by external events (GHA webhooks), or by timers,
and most are one-shot (they never call `/done` — cleanup is the pruner/reaper's job, § Worker lifecycle).

| Agent                     | Kind / lifecycle                    | Trigger                                             | Notes                                                                                                                                                                                           |
| ------------------------- | ----------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **main**                  | persistent, one per fleet           | keeper (`main_agent_keeper`) respawns it            | The coordinator/keeper agent; owns auto-answers to `authority=main_agent` blocked-questions, context-recycle, and fleet reconcile. Never dispatched from a plan.                                |
| **review**                | persistent singleton                | standing                                            | Reviews shipped work; a member of `_SINGLETON_AGENT_KINDS`, so a sessionless straggler is fast-reaped. Also usable as a `[REVIEW]` craft tag, but the standing reviewer is not backlog-driven.  |
| **cicd**                  | one-shot escalator                  | GHA `escalate-to-orchestrator` webhook on a CI wall | `escalation.escalate()` grabs a free slot, fixes the wall, pings the authoring slot, EXITS without `/done`. Multi-instance (absent from `_SINGLETON_AGENT_KINDS`). Reaped `lifecycle-complete`. |
| **conflict_resolver**     | one-shot escalator                  | merge-conflict event                                | Same escalator pattern as cicd.                                                                                                                                                                 |
| **data_pipeline_failure** | one-shot escalator                  | data-pipeline-failure event                         | Same escalator pattern.                                                                                                                                                                         |
| **plan_health**           | scheduled report + escalation fixer | daily cron + LDR→main back-merge ping + PR gate     | Cross-plan contradiction + governance-doc-drift check; POSTs findings, exits. Dispatched via `POST /api/plan-health/dispatch` (`server/plan_health.py`), NOT the backlog.                       |
| **plan_reconciler**       | scheduled                           | systemd timer, daily 01:00 UTC                      | Deep plan reconciliation (opus/max, server-forced). `install-plan-reconciler-timer.sh` → `plan-reconciler-dispatch.sh` → `POST /api/plan-health/dispatch {"mode":"reconcile"}`.                 |
| **monitor**               | standing                            | standing                                            | Fleet/observability monitor.                                                                                                                                                                    |

**Free-slot semantics are shared** (`escalation._pick_free_slot` == `plan_health._pick_free_slot`): a slot is "free"
when it is configured (worktree+branch+operator), not `paused`/`killed`, and has no live tmux session. So Class-B agents
and Class-A workers compete for the same physical slots — a busy backlog can starve escalators of a slot and vice-versa,
which is why capacity, not just dispatch, is a first-class concern.

## Behaviour domains

The operating model has four domains, each with a dedicated section below and a detailed code-mapped SSOT. Keep the
section here as the _intention_; the linked doc carries the mechanism. When code changes, update both.

### 1. Worker lifecycle — spawn → run → death → reap

**Intent**: a slot is never idle when there is claimable work, never running a wedged/stuck worker, and never leaves a
dead worker's task or process stranded.

- **Spawn** (`AutoSpawnLoop`, `server/autospawn.py`, 60s tick): wakes a free slot when a claimable task exists and an
  account has headroom. Full gate contract: [autospawn.md](../04-architecture/agent-orchestrator-autospawn.md).
- **Liveness** (`WorkerLivenessWatchdog` + `WorkerLivenessKicker`): kicks a nudge-able worker; kills a genuinely
  stuck/silent/context-full one; AutoSpawn respawns. Full trigger contract + anti-thrash:
  [worker-liveness.md](../04-architecture/agent-orchestrator-worker-liveness.md).
- **Death**: a dead worker with in-flight dirty WIP RESUMES (`--resume`, bounded by `ORCHESTRATOR_RESUME_MAX_ATTEMPTS`);
  dead + clean requeues. A `paused` slot's task is NEVER released (operator intent). Governed by
  `server/resume_lifecycle.py` + `server/tmux_pruner.py`.
- **Reap**: Class-B one-shot/scheduled agents never `/done`; the TmuxPruner (on session death) and the reaper
  (`reap_orphan_agents`) archive them `lifecycle-complete`. Sessionless terminal-lifecycle agents reap on a short grace
  (`one_shot_stale_grace_minutes`, default 15), not the 6h persistent grace.
- **Account failover**: usage-cap / auth-failure evicts a slot off a dead/exhausted account onto a headroom account
  (resume-preserving where a `claude_session_id` exists). Health is a poller verdict, never a heartbeat inference. Full
  contract:
  [worker-liveness.md § "Account auth-failure eviction"](../04-architecture/agent-orchestrator-worker-liveness.md).

> **Never manually `tmux kill-session` a slot.** The watchdog + AutoSpawn own that lifecycle; a manual kill races them.

### 2. Task lifecycle — the backlog task state machine

**Intent**: a task's status always reflects reality — `done` means the work shipped AND the plan checkbox flipped, and a
task no live worker can complete does not churn the fleet.

- **States**: `queued` → `dispatched` (to a slot) → `done` | `cancelled`. Blocked-on-a-question is a separate axis
  (`BlockedRow` + `authority`), not a task status.
- **Done-gate** (`/done`, `slots_worker.py`): rejects (409) while any repo in the slot dir carries uncommitted WIP
  (`ORCHESTRATOR_DONE_REQUIRE_CLEAN`), AND — since `check_plan_flip` was upgraded to diff the checkbox, not just the
  file touch (`server/verify.py::_diff_flips_checkbox`) — rejects a `done_sha` that touched the plan file without
  flipping the task's `- [ ]`→`- [x]`. This is what keeps `status=done` honest against `/skip-current-task` "declining"
  commits.
- **Skip / park**: a worker that reads the plan and finds the task blocked calls `/skip-current-task` with a reason; the
  skip is recorded per-slot (`slot_skips`, 24h TTL). A durably-blocked task is _parked_ (false prerequisite /
  `priority_override`) so it leaves the dispatchable set until its blocker clears.
- **Prerequisite vs blocked-question** (do NOT conflate): a task gated by EARLIER tasks WAITS on a `prerequisite`; a
  task needing a human/main answer raises a `BlockedRow` with `authority ∈ {main_agent, operator}`. Full contract + the
  `condition`→`prerequisite` rename:
  [overview.md § "Blocked-questions, authority…"](../04-architecture/agent-orchestrator-overview.md).

### 3. Dispatch — role-based, not VM-based

**Intent**: the right task reaches the right slot, and the fleet never spawns or churns onto work no live slot can take.

- **Routing key**: a plan's `assigned_role` (and per-task `[TAG]`), matched against the role registry — NOT "which VM
  owns this plan". `parent_epic` survives only for orphan-check + priority rollup, never routing.
- **`assigned_vm` — closed 2-value domain `{planning, NA}`**: `planning` = the orchestrator ingests + dispatches the
  plan's tasks; `NA` = dispatched to nobody (default for new plans — ask the operator before authoring a
  `assigned_vm: planning` plan). Any `vm-defi`/`vm-cefi`/… value is a stale multi-VM artifact — flip to `planning`/`NA`
  on next touch. `human-planning` is a pre-2026-06-27 alias treated as `planning`.
- **Ordering**: dispatch sorts `(tier, priority, plan_order, plan_ref)`; a live worker `--resume`s to each task's
  model/effort/thinking tier (`server/model_tier.py`, chain `haiku<sonnet<opus<fable`).
- **The spawn budget must match the dispatch gate**: AutoSpawn's "is there work worth spawning for?" count and
  dispatch's "can this slot take it?" filter share one SSOT (`dispatch.claimable_queued_task_ids`) so a fleet-skipped,
  role-blocked, or collision-blocked task cannot inflate the spawn budget and churn the fleet. Full code map + the
  dispatch-correctness contract:
  [backlog-state-alignment.md](../04-architecture/agent-orchestrator-backlog-state-alignment.md).

### 4. Regen — plans are the source of work

**Intent**: `backlog.yaml` is a pure projection of the active plans; editing a plan checkbox is the only way to change
the fleet's work, and a task's identity is stable across regens.

- **Derivation** (`server/regen_backlog_from_plan.py`): `- [ ]` checkboxes in `plans/active/*.md` → backlog tasks, for
  plans with `assigned_vm: planning` and NOT `execution_scope: local-only` and NOT `status: draft`. **Never hand-edit
  `backlog.yaml`** — the backend owns it.
- **Cadence**: `PlanRegenLoop` fires 60s after boot then every `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` (default
  1800s); `pm-pull.timer` FF-pulls `unified-trading-pm` every 5 min, so push→pickup latency is ≤35 min
  (`POST /api/backlog/regen` for immediate).
- **Reconcile, not append**: regen updates a matched task's `model`/`effort`/`thinking`/`assigned_role`/`priority`/
  `plan_order` in place (dedup key = `BacklogTask.brief` == raw todo line); a removed-while-dispatched task becomes
  terminal `cancelled`; hand-tuned park fields survive via `priority_override` / `brief_hash`.
- **Known sharp edge**: task ids are POSITIONAL (`slug + next index`), so a completed todo re-read as `- [ ]` under a
  shifted index can collide with a sibling's id — guarded by `brief_hash` but not eliminated. Tracked in
  `plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`.

## Deploy currency — `ao-self-pull.sh`

The backend runs `uvicorn server.server:app` from the VM's git checkout; nothing else keeps that checkout current.
**`scripts/ao-self-pull.sh`** (15-min root cron) FF-pulls `origin/live-defi-rollout` (ff-only, never forces; dirty →
logs + skips) and `systemctl restart`s the orchestrator only when HEAD moved, or when the running process predates the
checkout HEAD. A deduped Slack alert (`_alert_wedge`) fires when the pull is wedged AND the clone is `≥10` commits
behind. Full SSOT + the open "current-checkout-but-stale-process" hardening gap:
[overview.md § "Deployment scripts"](../04-architecture/agent-orchestrator-overview.md).

## Checking live status from a dev checkout (read-only)

The API needs a JWT most dev checkouts lack, and the VM's public `:8765` has no inbound rule. The supported read-only
path is **AWS SSM Session Manager** `send-command` running `curl localhost:8765/api/backlog` ON the VM (no firewall
change, no JWT, CloudTrail-audited):

- **Script**: `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh [substring-filter]` — needs AWS CLI
  authed against account `427895769566` with `ssm:SendCommand` + `ssm:GetCommandInvocation`.
- **Skill**: `/check-agent-orchestrator` wraps it for interactive use — trigger it rather than re-deriving the path.
- **Instance**: `i-0c9b283b31d6b5ca7`, `ap-northeast-1`, EIP `13.113.200.22`. If the VM is replaced, re-derive with
  `aws ec2 describe-addresses --public-ips 13.113.200.22 --region ap-northeast-1`.
- **READ-ONLY only** — never fold a write (`POST /api/backlog/regen`, `/reopen`, …) into a routine status check.

## Related

[`agent-orchestrator-overview.md`](../04-architecture/agent-orchestrator-overview.md) (service-implementation reference:
stack / auth / state / deploy / endpoints) ·
[`agent-orchestrator-autospawn.md`](../04-architecture/agent-orchestrator-autospawn.md) ·
[`agent-orchestrator-worker-liveness.md`](../04-architecture/agent-orchestrator-worker-liveness.md) ·
[`agent-orchestrator-backlog-state-alignment.md`](../04-architecture/agent-orchestrator-backlog-state-alignment.md) ·
[`orchestrator-safety-mechanisms.md`](orchestrator-safety-mechanisms.md) · `unified-trading-pm/agents/<role>.md` (role
charters) · `plans/PLAN_FORMAT.md` + [`doc-frontmatter-schema.md`](../11-project-management/doc-frontmatter-schema.md)
(`assigned_vm` enum authority).
