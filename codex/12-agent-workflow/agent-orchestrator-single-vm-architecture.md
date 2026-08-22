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
    fleet-cooldown,
    auto-park,
  ]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
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
    fleet-dispatch-cooldown,
    durable-auto-park,
  ]
referenced_by: [cursor-configs/CLAUDE.md, cursor-configs/skills/check-agent-orchestrator/SKILL.md]
owner:
last_reviewed: 2026-07-31
code_refs:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/role_registry.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/state_store/cooldown.py,
    agent-orchestrator/server/auto_park.py,
    agent-orchestrator/server/auto_park_reconcile.py,
    agent-orchestrator/scripts/ao-self-pull.sh,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
  ]
source:
  "operator ruling 2026-07-12 (create missing SSOT) + 2026-07-18 (make this THE operating-model SSOT: two worker classes
  + behaviour-domain sections)"
---

# agent-orchestrator — architecture & operating model

> **THE governing SSOT** for what agent-orchestrator is, why it exists, and how it behaves. Read this first; the
> [service-implementation reference](/codex/04-architecture/agent-orchestrator-overview.md) (tech stack, auth,
> endpoints, deploy) and the per-domain docs it links sit under it. This doc is written **intention-first**: each
> behaviour states what the system is _meant_ to do so a reader can compare it against the cited code and see drift
> immediately.

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
[overview.md § "Difference vs trading services"](/codex/04-architecture/agent-orchestrator-overview.md).)

## Topology — one VM, N in-process slots (since 2026-06-27)

One **central orchestrator VM** (id `planning`, AWS EC2 ap-northeast-1, EIP `13.113.200.22`, instance
`i-0c9b283b31d6b5ca7`) runs the uvicorn backend (`:8765`) **and** all N slot workers as in-process tmux sessions
(`orch-slot-N`). There are **no epic VMs** — the prior 10-epic-VM fleet (`vm-defi` / `vm-cefi` / … one VM per epic) was
retired 2026-06-27; do not stand up a new epic VM or treat that fleet as current. The separate interactive-only
`human-planning` VM (id `i-0dd9812a96cdda5dc`) was **terminated 2026-08-03** (confirmed idle, no live traffic depended
on it) — do not reference it as a live host; any future operator-interactive box would be a fresh instance, not this
one.

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
- **Lifecycle**: `/boot` → claim a task → work → `/done` (clean-tree + checkbox-flip gated) → **drains the next ready
  task in the same session** (persistent; when no task is ready it goes idle → the reclaimer retires it — NOT reaped per
  task, see § Worker-lifecycle Reap). A dead worker mid-task RESUMES (`--resume`) or requeues.
- **Identity**: the task carries `dispatched_to`, `done_sha`, `brief_hash`; the slot carries `current_task`.

### Class B — Standing & event-driven agents (NOT plan-driven)

These never come from `backlog.yaml`. They are triggered by the keeper, by external events (GHA webhooks), or by timers,
and most are one-shot or scheduled.

> **✅ Completion-contract LANDED 2026-07-21 (`agent-orchestrator@0d510e9`; operator decision →
> [`ao_uniform_agent_liveness_contract`](../../plans/archive/2026_07/ao_uniform_agent_liveness_contract_2026_07_20.md)).**
> The prior model — _one-offs never `/done`; cleanup is the pruner/reaper's job on session death_ — was proven broken
> 2026-07-21: **a finished one-off does not die.** Saying "EXIT" in a role doc only ends the Claude _turn_; the tmux
> session lingers at an idle `❯` prompt, `WorkerLivenessKicker` re-nudges it, `has_session()` stays True, and every
> session-death-gated reaper is blind → the AgentRow stays `active` forever and pins its slot (15 such zombies pinned
> 15/16 slots → the reconciler `503 no free slot`). **The contract (NOW LIVE):** a `one_shot`/`scheduled` agent, on
> completing, POSTs an explicit **role-aware `/done`** (task-less for a task-less one-off, `one_shot_complete=true`) →
> the backend archives it `lifecycle-complete`, frees the slot → the agent then stops → the reap cleans the session.
> **Landed `agent-orchestrator@0d510e9`:** A1 (`/done` task-less path) + A2 (5 role docs) + A3 (boot-prompt STEP 3) + B1
> (`/boot` holds a one-off `working`) + C1 (the `f641968`/`1e7fec0` idle-scanner carve-outs deleted). The Class-B rows
> above and the § Worker-lifecycle Reap below reflect the live `/done`-then-reap behavior.

| Agent                     | Kind / lifecycle                    | Trigger                                                                                                                     | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **main**                  | persistent, one per fleet           | keeper (`main_agent_keeper`) respawns it                                                                                    | The coordinator/keeper agent; owns auto-answers to `authority=main_agent` blocked-questions, context-recycle, and fleet reconcile. Never dispatched from a plan.                                                                                                                                                                                                                                                                                                                                                                                |
| **review**                | persistent singleton                | standing                                                                                                                    | Reviews shipped work; a member of `_SINGLETON_AGENT_KINDS`, so a sessionless straggler is fast-reaped. Also usable as a `[REVIEW]` craft tag, but the standing reviewer is not backlog-driven.                                                                                                                                                                                                                                                                                                                                                  |
| **cicd**                  | one-shot escalator                  | GHA `escalate-to-orchestrator` webhook on a CI wall                                                                         | `escalation.escalate()` grabs a free slot, fixes the wall, pings the authoring slot, then POSTs a task-less `/done` (`one_shot_complete=true`) → reaped `lifecycle-complete`. Multi-instance (absent from `_SINGLETON_AGENT_KINDS`).                                                                                                                                                                                                                                                                                                            |
| **conflict_resolver**     | one-shot escalator                  | merge-conflict event                                                                                                        | Same escalator pattern as cicd.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **data_pipeline_failure** | one-shot escalator                  | data-pipeline-failure event                                                                                                 | Same escalator pattern.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **plan_health**           | scheduled report + escalation fixer | daily cron + LDR→main back-merge ping + PR gate                                                                             | Cross-plan contradiction + governance-doc-drift check; POSTs findings, exits. Dispatched via `POST /api/plan-health/dispatch` (`server/plan_health.py`), NOT the backlog.                                                                                                                                                                                                                                                                                                                                                                       |
| **plan_reconciler**       | scheduled                           | systemd timer, every-2h even-hour fire, sharded-by-tranche Sun-Fri (retry-until-capacity), one unsharded `all` run Saturday | Deep plan reconciliation (sonnet, server-forced — corrected 2026-08-09, was stale "daily 01:00 UTC, opus/max"; see `daily_trading_analyst_llm_job_design_2026_07_29.md`'s 07-28/29 rulings). Retry cadence widened hourly→2h 2026-07-30 (corrected 2026-08-09, was stale "hourly-retry"). Graduated to STEADY STATE (direct push, no review PR) 2026-08-09 — see `agents/plan_reconciler.md`. `install-plan-reconciler-timer.sh` → `plan-reconciler-dispatch.sh` → `POST /api/plan-health/dispatch {"mode":"reconcile"[, "tranche":"<name>"]}`. |
| **monitor**               | standing                            | standing                                                                                                                    | Fleet/observability monitor.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

**Free-slot semantics are shared but no longer symmetric** (`escalation._pick_free_slot` /
`plan_health._pick_free_slot`): a slot is "free" when it is configured (worktree+branch+operator), not
`paused`/`killed`, and has no live tmux session. Class-A backlog, CI-escalation (`escalation.py`), and scheduled
dispatch (`plan_health.py`) all compete for the same physical slots, so capacity, not just dispatch, is a first-class
concern. **Structural capacity split (2026-07-29)**: `config.ci_escalation_slot_reserve()` (default 3) +
`config.scheduled_task_slot_reserve()` (default 2) are held back from Class-A's effective `fleet_worker_cap()`
(default 10) via `_apply_fleet_cap`'s combined clamp — on top of that, `config.ci_escalation_reserved_slot_ids()` (the
top-N non-review slot ids) is EXCLUDED from `plan_health._pick_free_slot`'s own search, so a scheduled-task burst (e.g.
a 9-tranche ag-closeout-audit firing 9 concurrent dispatches) can never claim the CI-only reserve. CI escalation itself
is NOT symmetrically restricted and may overflow into the scheduled-task reserve, since its never-block guarantee
outranks a scheduled task's capacity floor. See `server/config.py`'s reserve/partition function docstrings for the exact
mechanics; SSOT for the historical single-combined-reserve incident this replaces:
`plans/archive/issues/ao_escalation_and_scheduled_dispatch_slot_starvation_2026_07_27.md`.

**`pm_repo_path` always resolves to the DISPATCHED SLOT's own clone, never the caller's default (RULED 2026-08-19,
`plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18`)**: `plan_health.dispatch()` rewrites
`pm_repo_path` to `str(Path(slot.worktree or f".tabs/{slot_id}/") / "unified-trading-pm")` immediately after
`_pick_free_slot()` resolves the actual slot — the caller-supplied value (e.g. `install-plan-reconciler-timer.sh`'s
`PM_REPO` default, the shared READ-ONLY root clone) is unconditionally overwritten before it ever reaches
`autospawn.do_spawn`'s `extra_vars`. One shared rewrite site covers every `mode` in `_MODE_PROMPT_TEMPLATE`
(`report`/`reconcile`/`docs_reconcile`/`ag_closeout`/`na_eligibility`/`context_scout`/etc.), not a plan_reconciler-only
patch — confirmed 3x broken live before this fix (2026-08-16 slot 10, 2026-08-18 slot 31, 2026-08-19 slot 30) and
verified fixed via an executed test against 2 distinct modes. **Boot-message "session variables" (`$PM_REPO_PATH`,
`$SERVER_URL`, `$SLOT_ID`, `$DISPATCH_ID`, `$TRANCHE`, `${WORKSPACE_ROOT}`, …) are literal text, never real exported
shell env vars** — `server/prompts.py::_compose` renders a plain `- KEY=VALUE` block and never `export`s into the
tmux pane's shell; even if it did, a worker's Bash tool calls each start a FRESH shell with no state persisted from a
prior call (confirmed live: `env | grep` returns nothing across 3 independent dispatches), so a copy-pasted `$VAR` in
a command would silently expand to empty rather than error. Full explanation + the worker-facing HARD RULE text lives
in `unified-trading-pm/agents/RULES.md` § "Your worktree — read from root, operate only in your slot" (read FIRST by
every role per `expected_read_files()`, so this reaches every plan_health-family role uniformly).

**Report-mode dispatch throttle** (`plan_health._report_dispatch_gate`, AF-2
`plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md`, `agent-orchestrator@d098970`) — a SEPARATE,
plan_health-local mechanism from the fleet-wide dispatch-cooldown store above, no shared state: `mode="report"`
dispatches (the only mode this gate covers — `reconcile`/`docs_reconcile`/`ag_closeout`/`na_eligibility`/
`context_scout` register a disjoint `agent_kind` and are exempt by construction) coalesce onto the most recent
`agent_kind="plan_health"` `AgentRow` when it is still live (no result posted yet, inside
`tuning.plan_health_dispatch_timeout_seconds`, default 1800s) or the min-interval hasn't elapsed
(`tuning.plan_health_min_interval_seconds`, default 7200s/2h) — logged as `plan_health_dispatch_coalesced`. `force=true`
skips the interval half only; it never bypasses the live-dispatch check. Live-traffic re-measurement (2026-07-31, direct
read-only query against `data/state/state.db`): zero `superseded-plan_health` reaps in the table's entire history, and
`plan_health_dispatch_coalesced` has fired zero times since deploy — report-mode traffic (tied to
`main-backmerge-to-ldr.yml`'s promotion ping) has simply never come in fast enough to exercise the throttle's blocking
branch; no violation has occurred either.

## Behaviour domains

The operating model has four domains, each with a dedicated section below and a detailed code-mapped SSOT. Keep the
section here as the _intention_; the linked doc carries the mechanism. When code changes, update both.

### 1. Worker lifecycle — spawn → run → death → reap

**Intent**: a slot is never idle when there is claimable work, never running a wedged/stuck worker, and never leaves a
dead worker's task or process stranded.

- **Spawn** (`AutoSpawnLoop`, `server/autospawn.py`, 60s tick): wakes a free slot when a claimable task exists and an
  account has headroom. Full gate contract: [autospawn.md](/codex/04-architecture/agent-orchestrator-autospawn.md).
- **Liveness** (`WorkerLivenessWatchdog` + `WorkerLivenessKicker`): kicks a nudge-able worker; kills a genuinely
  stuck/silent/context-full one; AutoSpawn respawns. Full trigger contract + anti-thrash:
  [worker-liveness.md](/codex/04-architecture/agent-orchestrator-worker-liveness.md). **Sustained host saturation (QG
  churn + claude fleet + swap) is a distinct false-positive class, not "wedged agent"**: a busy host delays tmux pane
  reads past `verify_window_s`, so a genuinely-progressing worker's pane sample reads frozen and gets kicked — each kick
  interrupts real in-flight work, which can stall fleet-wide `slot_done` completions for over an hour even while
  dispatch keeps flowing. Fixed (`agent-orchestrator@64b5310`) via a progress-marker grace shield —
  `_progress_marker_shields_kick` suppresses `worker_kicked` whenever `slot.last_ping` advanced within
  `kick_progress_grace_seconds` (default 90s), even when the pane read classifies frozen. Full detail:
  [worker-liveness.md § "WorkerLivenessKicker — host-load-aware grace shield + hard-kill escalation"](/codex/04-architecture/agent-orchestrator-worker-liveness.md).
- **Death**: a dead worker with in-flight dirty WIP RESUMES (`--resume`, bounded by `ORCHESTRATOR_RESUME_MAX_ATTEMPTS`);
  dead + clean requeues. A `paused` slot's task is NEVER released (operator intent). Governed by
  `server/resume_lifecycle.py` + `server/tmux_pruner.py`.
- **Reap**: **Live behavior (as of `agent-orchestrator@0d510e9`, 2026-07-21):** a Class-B one-shot/scheduled agent POSTs
  a task-less role-aware `/done` (`one_shot_complete=true`) on completion → the backend archives it
  `lifecycle-complete` + frees the slot; the reaper then cleans the now-idle slot's lingering session. It is `working`
  throughout its run (claim sets it; B1 stops `/boot` resetting it), so the idle-scanning reapers skip it by
  construction (the `f641968`/`1e7fec0` carve-outs are DELETED — C1). The TmuxPruner (on session death) and
  `reap_orphan_agents` still archive `lifecycle-complete` as a backstop; sessionless terminal-lifecycle agents reap on a
  short grace (`one_shot_stale_grace_minutes`, default 15), not the 6h persistent grace. **The prior model** — never
  `/done`, cleanup relies on session death — assumed the agent becomes _sessionless_ on completion, which it does not: a
  finished one-off lingers session-alive, so the session-death-gated pruner/reaper never fire and it was never reaped —
  the exact leak (15 zombies pinned 15/16 slots) the live contract above fixes.
- **Class-A backlog workers are PERSISTENT — NOT reaped on `/done`** (dispatch-context lifecycle, 2026-07-21). Reaping
  is a property of WHO fired the worker, **not** the role's static `lifecycle` field — roles are just boot prompts (the
  same prompt can back a plan worker or a scheduled one). A plan-backlog worker (no `one_shot`/`scheduled` `AgentRow`)
  drains the next ready task in the **same live session**; when it has **no ready task** (backlog drained, or the only
  remaining tasks are prereq-blocked) it goes **idle → the idle-reclaimer retires it** (~2 ticks), and a **fresh**
  worker picks up later work (a cleared blocked task re-reads the plan — durable state lives in the plan/Progress Log,
  so conversational context-resume is an explicit NON-GOAL). Only Class-B event-spawned crafts (which carry a
  one_shot/scheduled `AgentRow`) reap on `/done`. Full model:
  [worker-liveness.md § "Dispatch-context-driven lifecycle"](/codex/04-architecture/agent-orchestrator-worker-liveness.md) +
  [`ao_worker_lifecycle_dispatch_context`](/plans/archive/2026_07/ao_worker_lifecycle_dispatch_context_2026_07_21.md).
  This corrects a live defect where four plan-worker roles declared `lifecycle: one_shot` were reaped per task via a
  static-role gate (`role_one_shot`); the gate now keys on dispatch context. Role-field reclassification (those four
  roles + `data_engineering` now declare `lifecycle: persistent`, matching `worker`) landed 2026-08-10 — cosmetic, since
  reaping never depended on the field.
- **Persistence is now GATED on self-reported context, not unconditional**
  (`ao_worker_context_lifecycle_gap_2026_07_25`, archived). The "same live session drains the next task" behavior above
  holds ONLY while `context_used_pct < tuning.context_worker_compact_gate_pct` (default 70). All four dispatch-adjacent
  routes — `/done`, `/progress`, `/boot`, `/heartbeat` — check this before calling `pick_next_task`; at/above threshold
  the candidate task is left `queued` (untouched) and the response carries `directive="compact_before_next"`
  (`/done`/`/boot`/`/heartbeat`) or `directive="compact_now"` (`/progress`) — a machine-checkable field (not prose) the
  worker's boot-loop MUST act on (`unified-trading-pm/agents/worker.md`'s HARD RULE: run `/pre-compact` then `/compact`
  before the next `/boot` call). This closed a live gap where a persistent session climbed to 100% context with zero
  compaction across many back-to-back tasks — `worker_liveness_watchdog.py`'s `context_burn` anomaly trigger (Trigger 4)
  independently backstops a session that ignores the directive (kills it once genuinely stuck, WIP-preserved first;
  AutoSpawn respawns fresh — see worker-liveness.md).
- **A SECOND, independent persistence gate — plan continuity, not just context**
  (`ao_worker_session_continuity_and_resume_threshold_2026_07_27`, archived, feature-flagged
  `tuning.plan_continuity_reset_enabled`, **default True** — shipped gated `False`, operator-approved-flipped True
  same-day, 2026-07-27). The context-pct gate above asks "is this session still fit to continue?"; this one asks "does
  the NEXT task actually continue what this session was just doing?" When enabled, `done_slot` additionally withholds
  the picked next task (same "stays `queued`, untouched" contract) whenever it differs from the just-completed task in
  `plan_ref`, OR `assigned_role`, OR its `repos` set — logs `worker_plan_switch_reset`, kills this slot's own tmux
  session off-thread (the same established daemon-thread pattern the one_shot-reap branch already uses), and returns
  `directive="reset_before_next"` (worker takes no action — the server has already scheduled the teardown). This closes
  the gap between the blanket "same live session drains the next task" behavior above and the operator's actual intent:
  a persistent session should only be kept alive for genuine same-plan continuation; an unrelated/parallel task should
  get a fresh session, per
  [worker-liveness.md § "Conversational context-resume is an explicit NON-GOAL"](/codex/04-architecture/agent-orchestrator-worker-liveness.md)
  — durable state was never supposed to depend on the conversation anyway. Shipped gated OFF, mirroring the
  `context_burn_kill` precedent (a new fleet-wide dispatch-behavior change gets an explicit operator flip once verified,
  not an unreviewed default-on) — the flip itself was that same explicit operator approval, verbatim "Flip to True now".
- **One-task-per-session hard rule SUPERSEDES both persistence gates above by default** (operator ruling 2026-08-04, the
  AO cost-halving fix — `tuning.one_task_per_session_enabled`, **default True**, shipped as the new standard not a gated
  experiment). The plan-continuity gate above only resets on an actual plan/role/repo SWITCH — a long same-plan
  sequential chain sails straight through it, since consecutive same-plan tasks never trigger
  `_plan_switch_needs_reset`. This was the dominant real-world cost driver: sessions observed climbing to 40-65%+
  context across many same-plan tasks with only the 70%-threshold in-session compact (never a real reset) between them.
  With this rule on, `done_slot` withholds the next task and kills the session **unconditionally, on every task
  boundary** — no plan/role/repo comparison needed — same `directive="reset_before_next"` contract, same kill-thread
  mechanism (`_one_task_per_session_reset_response`, `server/routes/slots_worker.py::_maybe_plan_switch_reset`). Net
  effect: "same live session drains the next task" (first bullet above) is no longer the default path — one task, one
  bounded session, AutoSpawn respawns fresh each time (defaulting to sonnet-4.6 per
  [model-tier-selection.md](/codex/06-coding-standards/model-tier-selection.md)'s sonnet-variant ruling, since a
  single-task session is small enough to trust the lighter snapshot). `sequential: true` plans keep their ordering +
  same-slot-affinity preference (`state_store/slots.py::_claim_plan_for_slot`) — that's about dispatch ORDER and
  worktree-reuse efficiency, not context continuity, and is unaffected by this rule. Set
  `one_task_per_session_enabled=False` to fall back to the pre-2026-08-04 behavior (debugging/comparison only).
- **Mid-task UNCONDITIONAL force-compact, no idle check** (operator ruling 2026-08-05, "the guidance isn't useful if it
  doesn't force" — `tuning.context_worker_force_compact_pct`, default 60). All three gates above only ever withhold the
  NEXT task; none of them touches a worker mid-task even while it climbs past 90%+ context on one long-running task.
  `ContextLifecyclePolicy` (`server/context_lifecycle.py`, originally main/review-only) now ticks EVERY
  `status == "working"` slot too — the moment a worker's self-reported `context_used_pct` crosses this threshold, the
  keeper injects `/pre-compact` then `/compact` directly into its pane, unconditionally: no idle-pane classification, no
  deadline wait, unlike the idle-gated forced fallback main/review still use (guidance at 60%, force after 2 min unacked
  IF genuinely idle — tightened from 50%/~45min the same ruling). Rationale for the asymmetry: a worker runs ONE bounded
  task, not a multi-day loop, so there's no safe multi-tick window to wait for a natural checkpoint the way the
  idle-gated path assumes; the operator explicitly accepted the risk of interrupting a worker mid-action. Re-armable
  within a single long task: an observed compaction (context% drops sharply) resets the force gate, so a task that
  climbs, compacts, and climbs again gets forced again rather than staying spent for the rest of the episode. A worker
  whose task just finished is never a target: it drops out of the `status == "working"` query that same tick, and the
  one-task-per-session rule above already hands its next task a brand-new session. Supersedes the old large-plan-only
  carve-out keyed on `model_tier.LARGE_PLAN_TODO_THRESHOLD` — see
  [model-tier-selection.md](/codex/06-coding-standards/model-tier-selection.md). Operator-facing note:
  `unified-trading-pm/agents/worker.md`.
- **Account failover**: usage-cap / auth-failure evicts a slot off a dead/exhausted account onto a headroom account
  (resume-preserving where a `claude_session_id` exists). Health is a poller verdict, never a heartbeat inference. Full
  contract:
  [worker-liveness.md § "Account auth-failure eviction"](/codex/04-architecture/agent-orchestrator-worker-liveness.md).

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
  commits. **Checkbox state = truth** (`ao_backlog_regen_integrity_2026_07_20` todo 4): the diff-based check proves a
  SPECIFIC commit did the flip, but a `done_sha` can be the wrong commit for honest reasons (predates the M3-hard gate,
  reassigned by a squash/rebase) without the completion itself being untrue. `check_plan_flip` falls back to reading the
  CURRENT plan text — if the brief is genuinely `- [x]` today, it accepts
  (`reason="checkbox_currently_checked_sha_mismatch"`) rather than 409ing an honestly-done task on a provenance gap.
  `audit_false_done.py` (the periodic false-`done` sweep) already worked this way — it was `check_plan_flip` that needed
  to catch up.
- **Skip / cooldown / park** (`ao_dispatch_cooldown_and_park_2026_07_20`): a worker that reads the plan and finds the
  task blocked calls `/skip-current-task` with a reason. Two INDEPENDENT exclusions are recorded, not one:
  - `slot_skips` (per-SLOT, 24h TTL, `slot_skip_ttl_hours`) — this slot specifically never re-claims the task; other
    slots are unaffected. Unchanged since 2026-07-07 (RC-3).
  - **The fleet-scoped dispatch cooldown store** (`server/state_store/cooldown.py`, `CooldownRow`/`dispatch_cooldowns`
    table) — ONLY armed when the skip's `reason_code ∈ {BLOCKED, PARKED, GATED}` (a plain scope/craft-mismatch skip,
    `reason_code=OTHER`, stays slot-scoped-only, unchanged). Holds the task un-dispatchable to **every** slot — closing
    the cross-slot thrash `slot_skips` alone could not (measured: 117 `slot_task_skipped`/24h, the same verdict
    re-derived 3x in ~35min, each a full worker boot). Base window `tuning.dispatch_cooldown_base_minutes` (default
    12min, operator range 10-15min); a repeat decline with NO detected relevant change steps out to
    `tuning.dispatch_cooldown_extended_minutes` (default 60min); a worker-supplied `estimated_unblock_minutes` overrides
    either when plausible. **Change-triggered re-eligibility**: a prerequisite flip, or a priority/brief edit on the
    task, grants immediate re-eligibility regardless of the window (`dispatch._cooldown_snapshot` fingerprints the
    watched state; compared at check time by the FLEET-scope `fleet_cooldown` dispatch filter — a pure read, all arming
    happens at write time in `register_cooldown`).
  - **Public contract, generic over an opaque `key` string** (not just `task_id`) — the store is meant to be REUSED,
    never re-implemented: `register_cooldown(session, key, *, reason_code, snapshot, eta_minutes=None)` arms/re-arms and
    returns the row (read `.skip_count` for an N-skip escalation); `get_cooldown`/`clear_cooldown` read/release;
    `mark_parked`/`mark_unparked`/`parked_rows`/`count_parked` back the durable-park escalation below. A second consumer
    namespaces its OWN key prefix (e.g. `f"escalation:{escalation_id}"` for a future escalator backoff) rather than
    building a second cooldown/backoff engine — that divergence is exactly the failure mode this store exists to
    prevent.
  - **Durable auto-park** (`server/auto_park.py`) is the N-skip escalation of the SAME store:
    `>= tuning.dispatch_cooldown_auto_park_skip_threshold` (default 3) distinct BLOCKED/PARKED/GATED declines within the
    counting window (`tuning.dispatch_cooldown_park_window_hours`, default 24h — mirrors `slot_skip_ttl_hours`)
    auto-parks the task via the SAME manual recipe an operator would apply by hand (below): `priority: 999` +
    `priority_override: true` + a synthetic `prereqs.prerequisites` condition named `auto_unpark__<task_id>`, created
    `false`. **Unpark is condition-driven, not blocker-driven** — the module deliberately does not try to detect that
    the ORIGINAL blocker resolved (the store's snapshot is generic, not semantic); instead, whoever/whatever sets the
    synthetic condition `true` (an operator, or another system, via the existing `POST /api/prerequisites/{name}`) is
    the trigger, and `AutoParkReconciler` (`server/auto_park_reconcile.py`,
    `tuning.auto_park_reconcile_interval_seconds` default 300s) notices on its next tick and reverts `priority_override`
    (letting the next `PlanRegenLoop` tick restore the plan-derived `priority` — the reconciler never guesses the
    pre-park value). Operator-visible surface: `task_auto_parked`/`task_auto_unparked` activity events + the
    `/api/state` `backlog_summary.auto_parked` dashboard count (same class as `AgentView.needs_operator_count`) + a
    manual override, `POST /api/backlog/{task_id}/unpark`.
  - A hand-set park (an operator applying the recipe directly, not via auto-park) is unaffected — it still leaves the
    dispatchable set purely via the `prereqs` FLEET filter (false named prerequisite), independent of the cooldown
    store.
- **Prerequisite vs blocked-question** (do NOT conflate): a task gated by EARLIER tasks WAITS on a `prerequisite`; a
  task needing a human/main answer raises a `BlockedRow` with `authority ∈ {main_agent, operator}`. Full contract + the
  `condition`→`prerequisite` rename:
  [overview.md § "Blocked-questions, authority…"](/codex/04-architecture/agent-orchestrator-overview.md).

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
  [backlog-state-alignment.md](/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md).

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
- **Known sharp edge, narrowed** (`ao_backlog_regen_integrity_2026_07_20` todo 1): task ids are POSITIONAL
  (`slug + next index`), so a completed todo re-read as `- [ ]` under a shifted index can still collide with a sibling's
  id — `TaskRow.brief_hash` detects the mismatch, but `sync_backlog_to_db` now REFUSES to reset a row that is `done`
  with a `done_sha` (a done row is audit history, never silently recycled) instead of blindly resetting it. Accepted
  trade-off: this also blocks the legitimate "id genuinely reused for a brand-new todo" case — that todo silently reads
  as `done` and never dispatches. **Detection + remediation shipped**
  (`ao_backlog_collision_alert_and_remediation_ui_2026_07_26`): the guard's refusal is now a queryable
  `backlog_sibling_reset_guard_refused` activity row, pages Slack once (deduped by `task_id`+incoming-brief-hash — see
  `/codex/04-architecture/agent-orchestrator-alerting.md`), surfaces in the dashboard's "Backlog Integrity" panel, and a
  one-click `POST /api/backlog/{task_id}/remint-collision` mints the stuck content a genuinely fresh id (checked against
  both `backlog.yaml` AND the full historical `tasks` table) while leaving the original done row's audit fields
  byte-for-byte untouched — no longer "until someone notices." The real fix (content-derived ids) was originally scoped
  out deliberately, pending proof the remediation flow was insufficient. Tracked in
  `plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` — corrected 2026-08-18
  (`/plan-reconcile ao`): that doc is `status: resolved`, 0 open todos; the content-derived-id follow-up itself
  shipped via `content_derived_backlog_task_ids_2026_08_08.md` — migration applied and holding (2037/2037 planned
  rows migrated, 0 unexplained); independent verification pending via the finalize plan's
  (`content_derived_backlog_task_ids_2026_08_08_finalize.md`) 0/6 gate (corrected 2026-08-19, `/plan-reconcile ao`,
  operator-ruled — the migration mechanism itself is done, but "done" here should not be read as "verified").

### 5. Dispatch-scope eligibility — bounded outcome only, judgment calls resolved BEFORE dispatch

Operator ruling 2026-07-23. A todo is eligible for `assigned_vm: planning` only if its outcome is DETERMINABLE by the
dispatched worker alone — a checkable fact, a scoped code change, an audit with a stated done-when. It is NOT eligible
if completing it requires a judgment call, a design decision, or open-ended exploration whose answer isn't already
decided — e.g. "figure out how the data pipeline should look for features" has no defined target and no way for an
isolated worker to know when it's done; the real decision is a human call masquerading as a todo. **Audits ARE eligible
when precisely scoped**: "does X match Y" / "count instances of Z" is a determinable, checkable fact, unlike "figure out
what X should be" — the scope, not the word "audit," is what makes it dispatchable. The judgment-call work that decides
"what X should be" happens FIRST, as a LOCAL/human plan (`task_template.md` §1) or an interactive session; its OUTCOME
(the decision) becomes the input to a later, properly-scoped AO todo — never the todo itself. Authoring-time check:
`task_template.md` §4. Review-time check: `/plan-reconcile`'s AO-dispatch-readiness hunters (line 3 of the plan-quality
four-line-defense, `/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md`).

### 6. Holding a todo — DECLARE the marker, or it reads as an accident

A `BLOCKED-<TOKEN>` / `DEFERRED-BY-DESIGN` / `STRETCH` marker anywhere in a todo stops that todo dispatching. Whether
that was **intended** is a separate question, and it is the one the dispatch-visibility gate answers: a marker
**declares** the hold only when it opens the checkbox line — inside the leading `[TAG]` cluster or at the head of the
description. Buried mid-sentence it still blocks dispatch but counts as an **accidental exclusion**, i.e. a todo nobody
will ever work and nobody meant to park.

```
- [ ] [BLOCKED-CREDENTIALS][INFRA] P1. **Thing** — waiting on the vendor.   ← declared
- [ ] BLOCKED-CREDENTIALS [INFRA] P1. **Thing** — waiting on the vendor.    ← declared
- [ ] [INFRA] P1. **Thing** — we can't start until the vendor replies, so BLOCKED-CREDENTIALS.  ← accidental
```

Continuation lines deliberately do not count: prose wrapping is a formatting artifact, so any rule keyed on "starts a
line" can be satisfied by accident. The checkbox line's head is the one position prose cannot wander into, and complying
is a ten-character edit.

**When the corpus-wide gate fails, it is usually not your changeset.** `check_ao_dispatch_visibility_gate.py` scans
every `assigned_vm: planning` doc in `plans/active`, so a failure names the corpus, not your commit. Before treating it
as a blocker: run it with `--json` to get the offending docs, check whether any are yours, and **re-run it** — the
corpus moves ~50 commits/hour and a failure can clear itself as peers close the todos involved (observed 2026-08-10: 6
accidental exclusions → 0 within ~20 minutes, no action taken). Read the result as a corpus health signal, not as
"someone broke origin". Never hand-edit `ao_dispatch_visibility_baseline.yaml`; `--update-baseline` needs a stated,
reviewed reason.

**Your own instance is caught at commit time.** `scripts/plan-hygiene/check_accidental_exclusions_only.sh` runs in
`run_hygiene_sweep.sh --precommit` (so it fires on a plain `safe-doc-push.sh`, which takes prek only) and flags a NEW
undeclared exclusion in a staged plan, HEAD-vs-current, before it can reach origin. The verdict comes from AO's own
`dispatch_visibility_report --check-files`, reusing `_eligible_todos` and `_is_declared` rather than re-deriving the
marker rule — that predicate has four recorded widen-the-regex regressions, and a check that disagrees with the
dispatcher is worse than no check. A marker-token grep gates the ~8s module import, so plans carrying no marker (roughly
three in four) pay nothing.

## Deploy currency — `ao-self-pull.sh`

The backend runs `uvicorn server.server:app` from the VM's git checkout; nothing else keeps that checkout current.
**`scripts/ao-self-pull.sh`** (15-min root cron) FF-pulls `origin/live-defi-rollout` (ff-only, never forces; dirty →
logs + skips) and `systemctl restart`s the orchestrator only when HEAD moved, or when the running process predates the
checkout HEAD. A deduped Slack alert (`_alert_wedge`) fires when the pull is wedged AND the clone is `≥10` commits
behind. Full SSOT + the open "current-checkout-but-stale-process" hardening gap:
[overview.md § "Deployment scripts"](/codex/04-architecture/agent-orchestrator-overview.md).

**Deploy currency covers the systemd unit file too, not just app code** (closed 2026-07-31,
`orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md`, `agent-orchestrator@90a2b2f`): a
9-day-stale `/etc/systemd/system/orchestrator.service` (still running a removed `--reload` flag) survived two
cron-triggered `systemctl restart`s on the same day, because `systemctl restart` reuses whatever unit is already
installed — the code-currency loop above has no equivalent for the unit file itself. `ao-self-pull.sh` now also runs
`install-orchestrator-service.sh --operator ubuntu --restart` unconditionally every tick, after the code-pull logic;
that script was already idempotent (diffs the rendered SSOT `scripts/orchestrator.service` against the installed copy,
no-ops when identical, restarts only when it actually applies a change), so no new diff-detection logic was needed —
just wiring the existing self-heal-capable command into the cron loop — the same "extract the idempotent check, run it
every tick regardless of what triggered this tick" pattern `rescale-memory-cap.sh` already established for the cgroup
memory cap (`orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`).

## Checking live status from a dev checkout (read-only)

**Corrected 2026-08-15** (`ao_human_fleet_integration_2026_08_15.md` Phase 2 investigation) — the "no inbound rule"
claim below was STALE (verified wrong, not re-derived from doc): security group `sg-066c852065f8cdcac` on
`i-0c9b283b31d6b5ca7` allows `0.0.0.0/0` on `tcp/8765` (also `22` and `443`), and the API is directly, publicly
reachable — `curl https://13.113.200.22:8765/api/agents` (or plain `http://`) returns a real `401 missing bearer token`
from a machine outside AWS, confirming both the port is open AND the app-level auth gate is live. Whether this was
always the case or changed since this doc was written is unknown from here — flagging as a fact, not a ruling on whether
it's the intended posture.

A real anomaly, unresolved: the same IP over the **proper domain name** (`api.agent-orchestrator.odum-research.com` —
DNS resolves correctly to `13.113.200.22`, a valid Let's Encrypt cert for that exact CN is served on `:443`) times out
at the TLS handshake, reproducibly, even when the IP is pinned via `curl --resolve` — while a bare-IP HTTPS connection
to the identical port succeeds immediately. Points at SNI-based filtering somewhere in the path (client-side network, or
a WAF/proxy on the server side); root cause not established from this investigation alone — worth checking whether it
reproduces from a different network before assuming either side.

**Practical effect**: a caller with a real bearer token (`issue_token(role="worker", ...)`, see `server/auth.py`) can
reach the API directly over HTTPS today — no SSM tunnel required for that case. The SSM path below remains the right
choice for **credential-free, read-only** checks (no JWT provisioning needed) and stays documented as-is for that use:

The API needs a JWT most dev checkouts lack. The supported credential-free read-only path is **AWS SSM Session Manager**
`send-command` running `curl localhost:8765/api/backlog` ON the VM (no firewall change, no JWT, CloudTrail-audited):

- **Script**: `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh [substring-filter]` — needs AWS CLI
  authed against account `427895769566` with `ssm:SendCommand` + `ssm:GetCommandInvocation`.
- **Skill**: `/check-agent-orchestrator` wraps it for interactive use — trigger it rather than re-deriving the path.
- **Instance**: `i-0c9b283b31d6b5ca7`, `ap-northeast-1`, EIP `13.113.200.22`. If the VM is replaced, re-derive with
  `aws ec2 describe-addresses --public-ips 13.113.200.22 --region ap-northeast-1`.
- **READ-ONLY only** — never fold a write (`POST /api/backlog/regen`, `/reopen`, …) into a routine status check.

## Related

[`agent-orchestrator-overview.md`](/codex/04-architecture/agent-orchestrator-overview.md) (service-implementation
reference: stack / auth / state / deploy / endpoints) ·
[`agent-orchestrator-autospawn.md`](/codex/04-architecture/agent-orchestrator-autospawn.md) ·
[`agent-orchestrator-worker-liveness.md`](/codex/04-architecture/agent-orchestrator-worker-liveness.md) ·
[`agent-orchestrator-backlog-state-alignment.md`](/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md)
· [`orchestrator-safety-mechanisms.md`](orchestrator-safety-mechanisms.md) · `unified-trading-pm/agents/<role>.md` (role
charters) · `plans/PLAN_FORMAT.md` +
[`doc-frontmatter-schema.md`](/codex/11-project-management/doc-frontmatter-schema.md) (`assigned_vm` enum authority).
