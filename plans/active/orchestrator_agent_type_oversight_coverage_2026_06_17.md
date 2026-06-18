---
title: "Orchestrator agent-type oversight coverage — every agent type registered, health-tracked, UI-visible"
created: 2026-06-17
status: active
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: local-only
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source:
  - 2026-06-17 account-pool exhaustion follow-up (operator design session) — fragmented agent-type oversight
priority: P2
---

# Orchestrator agent-type oversight coverage

## Why

The backend tracks agents through `AgentRow`s created by `register_agent`; that is what `health.py` (staleness marking),
`reap_orphan_agents` (the reaper), the watchdogs, and the dashboard all key off. But not every agent TYPE the
orchestrator spawns registers an `AgentRow` — so several types are **invisible to the unified oversight**: the backend
can't uniformly detect their staleness, a dead tmux session, or a stuck-at-prompt state, and the operator can't see them
working in the UI.

Confirmed unregistered (2026-06-17): **`escalate` / `conflict-resolver`** (`escalation.py` — `register_agent` count 0,
tracked only by the bespoke `escalation_queue` + `EscalationWatchdog`) and **`plan-health`** (`plan_health.py` — count
0). Several other types (`monitor`, `backup`, `recovery-audit`, `plan-reconciler`, `usage_reporter`) have unverified
coverage. There is also a known DUPLICATE: `plan-health` and `plan-reconciler` overlap — one supersedes the other and
the dead one must be removed.

Goal: **every LIVE agent type registers an `AgentRow` at spawn → uniform health / staleness / reaper / watchdog
coverage + visible in the UI while working**; dead/duplicate types are deleted; unclear types are clarified and their
boot prompts updated.

## Agent types in scope (`agent-orchestrator/agents/*.md` templates)

`main` · `worker` · `review` · `escalate` · `conflict-resolver` · `plan-health` · `plan-reconciler` · `monitor` ·
`backup` · `recovery-audit` · `usage_reporter`. (`RULES.md` is shared rules, not a type.)

Known coverage so far:

| Type | Registers AgentRow? | Notes |
| --- | --- | --- |
| `main` | ✅ (main_agent_keeper) | full |
| `worker` / `review` | ✅ (`/api/agents/spawn`) | full |
| `escalate` / `conflict-resolver` | ❌ | bespoke escalation_queue + EscalationWatchdog only |
| `plan-health` | ❌ | DUPLICATE with plan-reconciler — one to be removed |
| `plan-reconciler` | ⚠️ unverified | the newer daily deep reconciler |
| `monitor` / `backup` / `recovery-audit` | ⚠️ unverified | purpose unclear — audit + fix boot prompts |
| `usage_reporter` | ⚠️ unverified | usage-poll reporter |

## Phased execution

### Phase 1 — Audit every agent type (the coverage matrix)

- [ ] [ORCHESTRATOR] P1. For each template in `agents/`, document: PURPOSE, is it LIVE/used (which code path spawns it,
      or is it dead), the spawn entrypoint, whether it calls `register_agent` (→ AgentRow), whether `health.py`
      staleness + `reap_orphan_agents` + a watchdog cover it, and whether it shows in the dashboard. Produce a coverage
      matrix in this plan's Progress Log. Repo: agent-orchestrator (audit; no code).
- [ ] [ORCHESTRATOR] P1. Classify each type: KEEP (register + cover), CLARIFY (live but boot-prompt/role unclear →
      rewrite the boot prompt), or DELETE (dead/duplicate). Record the decision per type. Repo: agent-orchestrator.

### Phase 2 — Rationalize the set (per Phase-1 decisions)

- [ ] [ORCHESTRATOR] P2. `plan-health` + `plan-reconciler`: KEEP BOTH (Q1). No deletion — instead document them in the
      `agents/*.md` headers + codex as the two modes of `run_plan_health` (report vs reconcile) so the duplication
      reads as intentional. Repo: agent-orchestrator (`agents/`, codex).
- [ ] [ORCHESTRATOR] P1. `recovery-audit`: KEEP but mark WIP / NOT-FINALISED (Q2). Banner `agents/recovery-audit.md`
      as WIP (boot prompt + duties owed) and add a HARD never-launch guard — the spawn/role surface must refuse to
      actually launch `recovery-audit` until finalised (e.g. exclude from the spawnable role set + an explicit
      `RuntimeError`/log if anything tries). Keep the supporting infra in place. Repo: agent-orchestrator
      (`agents/recovery-audit.md`, spawn/role wiring).
- [ ] [ORCHESTRATOR] P1. `usage_reporter`: DELETE (Q3). Remove `agents/usage_reporter.md` + its role from
      `spawn_agent_preview` / `/api/agents/spawn` role set + any other reference; usage stays on the httpx `UsagePoller`.
      Repo: agent-orchestrator (`agents/`, `routes/agents.py`, models).
- [ ] [ORCHESTRATOR] P2. `monitor`: KEEP (Q4). Confirm/clarify the `agents/monitor.md` header documents it as the manual
      external-watch (custom-role) pattern, manual-spawn only. Repo: agent-orchestrator (`agents/`).

### Phase 3 — Register every LIVE agent type + capture its identity/attach handles

> Per the cross-cutting requirement above: every live agent persists `claude_session_id` (--resume handle) +
> `tmux_session` (attach/capture handle) at spawn, so the backend can resume, attach to, and health-check ALL types
> uniformly. The `AgentRole` enum (`main/review/backup/custom`) must also be widened (or a parallel role field added)
> to admit the slot-based types we now register (escalate/conflict-resolver/plan-health/plan-reconciler).

- [ ] [ORCHESTRATOR] P1. Add `claude_session_id` + ensure `tmux_session` on every owning row (`SlotRow` for slot-based,
      `AgentRow` for standalone); set BOTH at spawn for every type. `claude_session_id` = the deterministic Claude UUID
      (shared with the failover plan's `--session-id` capture — reuse it, do not fork). Repo: agent-orchestrator
      (`server/orm.py`, all spawn paths).
- [ ] [ORCHESTRATOR] P1. `escalate` / `conflict-resolver`: `register_agent` at dispatch (`escalation.py`) with
      role/label/`tmux_session`/`claude_session_id` + escalation_id linkage, so the agent appears as an `AgentRow` and is
      health/reaper-covered — WITHOUT breaking the escalation_queue/EscalationWatchdog tracking (reconcile the two:
      AgentRow = liveness/attach/oversight, escalation_queue = the wall's work-state). Repo: agent-orchestrator
      (`server/escalation.py`).
- [ ] [ORCHESTRATOR] P1. `plan-health` + `plan-reconciler`: `register_agent` at spawn (`plan_health.py`) with
      role/label/`tmux_session`/`claude_session_id`. Repo: agent-orchestrator (`server/plan_health.py`).
- [ ] [ORCHESTRATOR] P1. Widen `AgentRole` (or add a role field) to admit escalate/conflict-resolver/plan-health/
      plan-reconciler so their registration is well-typed (reconcile with the `spawn_agent_preview` role set after the
      usage_reporter delete). Repo: agent-orchestrator (`server/models/_types.py`, `orm.py`).
- [ ] [ORCHESTRATOR] P2. Backend can ATTACH/inspect any agent from its stored handles: a uniform "capture this agent's
      pane" path keyed off `tmux_session` works for every registered type (the reaper's dead-session check + the
      liveness probes already key off `tmux_session`; confirm they now cover the newly-registered types). Repo:
      agent-orchestrator.

### Phase 4 — UI visibility (operator can SEE every working agent)

- [ ] [ORCHESTRATOR][UI] P1. Verify the agents feed (`/api/agents`) surfaces ALL live agent types (escalate /
      conflict-resolver / plan-reconciler / monitor / …) while working, and the dashboard renders each role (icon/label
      per type, not just worker/main). Add any missing role rendering. Repo: agent-orchestrator dashboard (+ deployment-ui
      if it mirrors the agents panel).
- [ ] [ORCHESTRATOR][UI] P2. Regression guard: a smoke/spec asserting a non-worker agent type (e.g. an escalation agent)
      appears in the agents list when registered. (If this touches `deployment-ui`, the playwright gate applies — `pw:L2 ✓`
      + cited regression spec.) Repo: deployment-ui / agent-orchestrator dashboard.

### Phase 5 — Uniform staleness/liveness verification + tests

- [ ] [ORCHESTRATOR] P1. Confirm `health.py` staleness + `reap_orphan_agents` (incl. the Gap-1 stale-sessionless reap
      from the lifecycle issue doc) + the worker-liveness watchdog (or an equivalent) now apply to every registered
      type; close any type-specific gap. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P1. Unit tests: each newly-registered type creates an AgentRow with the right role/session; the
      reaper/health path treats it like any agent; no double-count vs the escalation watchdog. Repo: agent-orchestrator
      (`tests/`).
- [ ] [ORCHESTRATOR] P2. Live smoke on the central VM: trigger an escalation + the plan-reconciler, confirm both appear
      as agents in the dashboard while working and are reaped when their session dies. Repo: agent-orchestrator.

## Success criteria

- A coverage matrix exists for all agent types (✅ Phase 1) with a recorded decision per type.
- `plan-health` + `plan-reconciler` both retained, documented as the two modes of `run_plan_health`.
- `recovery-audit` retained but bannered WIP/NOT-FINALISED with a HARD never-launch guard (cannot be spawned until
  finalised); `monitor` retained + documented as the manual external-watch pattern.
- `usage_reporter` deleted (template + role surface); usage stays on the httpx `UsagePoller`.
- Every LIVE agent (every type) persists `claude_session_id` (--resume handle) + `tmux_session` (attach handle) at
  spawn; the backend can resume, attach to, and health-check every type uniformly.
- Every LIVE agent type registers an `AgentRow` (role widened to fit) and is covered by the SAME staleness / reaper /
  liveness oversight as workers and the main agent — no agent type invisible to the backend.
- Every working agent (any type) is visible in the UI while running.

## Risks / open items

- Registering escalation agents as AgentRows must NOT double-count or conflict with the existing `escalation_queue` +
  `EscalationWatchdog` lifecycle — reconcile the two tracking models (AgentRow = liveness/oversight; escalation_queue =
  the wall's work-state), don't fork them.
- Deleting the superseded plan-* type must remove its scheduler/event trigger too (a dangling cron/dispatch that spawns
  a deleted template would error).
- UI work touching `deployment-ui` is gated by the playwright HARD RULE (`pw:L2 ✓` + regression spec).

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — document the full agent-type roster + that EVERY live type
  registers an AgentRow and is health/reaper/UI-covered (single oversight model, no bespoke-only types).
- `codex/05-infrastructure/agent-orchestrator-worker-topology.md` — agent-type coverage matrix.

## Cross-links

- Lifecycle issue doc (Gap 1 = reaper never reaps a stale sessionless AgentRow — same oversight theme; this plan extends
  coverage to the types that don't even create an AgentRow): `plans/active/issues/orchestrator_agent_lifecycle_gaps_2026_06_16.md`.
- Sibling orchestrator-reliability plan: `plans/active/orchestrator_account_failover_resume_respawn_2026_06_17.md`.

## Progress Log

### Phase 1 coverage audit — 2026-06-17 (slot-2)

**Two distinct oversight systems exist (the root of the fragmentation):**

- **Slot-based** — agents spawned into an `orch-slot-N` tmux session via a `SlotRow` (`_pick_free_slot` → `do_spawn`).
  Overseen by `WorkerLivenessWatchdog` (scans slots: stuck-at-prompt / heartbeat-silent / usage-cap). No `AgentRow`.
- **AgentRow-based** — standalone sessions registered via `register_agent` into the `agents` table
  (`AgentRole = Literal["main","review","backup","custom"]`). Overseen by `health.py` staleness + `reap_orphan_agents`
  (+ `main_agent_keeper` for main). This is the path that feeds the dashboard agents list / `/api/agents`.

A type is well-covered only if it lands cleanly in ONE of these. The gap class is the types that run in a slot but
whose `SlotRow`/dashboard state may not reflect them, and the types registered as agents but not health-covered.

**Coverage matrix** (✅ confirmed · ⚠️ needs deeper walk · ❌ confirmed-absent):

| Type | Purpose | Live? | Spawn path | Oversight model | UI-visible while working | Class |
| --- | --- | --- | --- | --- | --- | --- |
| `main` | the orchestrator agent | ✅ | `main_agent_keeper._spawn` (`orch-agent-main`) | AgentRow + health + reaper + keeper | ✅ (agents list) | KEEP |
| `worker` | does plan-backlog work in a slot | ✅ | `autospawn._do_spawn` (default template) | Slot + WorkerLivenessWatchdog | ✅ (slots panel) | KEEP |
| `review` | reviews work | ✅ | `autospawn` review slots (`_REVIEW_PROMPT_TEMPLATE`) AND an `AgentRole` | ⚠️ dual (slot AND AgentRow) — clarify | ⚠️ | KEEP+CLARIFY |
| `backup` | idle, promote→main/review via dashboard | ✅ | `/api/agents/spawn` (role) | AgentRow + health + reaper | ✅ | KEEP |
| `escalate` | resolves a CI wall on LDR | ✅ | `escalation.escalate` → free slot | Slot watchdog + escalation_queue + EscalationWatchdog; **no AgentRow** | ⚠️ slot panel only | KEEP+REGISTER |
| `conflict-resolver` | resolves a PR merge conflict | ✅ | `escalation.escalate` (PR walls) → free slot | same as escalate | ⚠️ | KEEP+REGISTER |
| `plan-health` | REPORT-mode cross-plan drift check | ⚠️ report-mode of `run_plan_health` | `plan_health.run_plan_health(mode="report")` → free slot | Slot watchdog; **no AgentRow** | ⚠️ | DECISION (see Q1) |
| `plan-reconciler` | RECONCILE-mode daily deep fixer (opus/max) | ⚠️ bringup (systemd timer pending per lifecycle doc) | `run_plan_health(mode="reconcile")` → free slot | Slot watchdog; **no AgentRow** | ⚠️ | DECISION (see Q1) |
| `monitor` | manual "custom-role" pattern: watch an external long-running thing + ping | ⚠️ template/pattern only — no auto-spawner | manual (custom role) | none specific | ❌ | CLARIFY (Q4) |
| `recovery-audit` | aspirational Layer-1 defence-in-depth signoff/actuator | ❌ no spawner found in code | — | none | ❌ | CLARIFY/DELETE (Q2) |
| `usage_reporter` | refresh account usage — **header self-declares DEFERRED**; real path is `UsagePoller` (httpx) | ⚠️ manually spawnable via agent-spawn dropdown only | `/api/agents/spawn` (role) | not in `AgentRole` enum → ⚠️ may not register cleanly | ⚠️ | DECISION (Q3) |

**Confirmed findings:**

1. `plan-health` and `plan-reconciler` are **two MODES of one entrypoint** (`run_plan_health`: `report`→plan-health,
   `reconcile`→plan-reconciler forced opus/effort-max), NOT rival spawners. So "delete one" is a product call, not a
   dedup.
2. `escalate` / `conflict-resolver` / `plan-health` / `plan-reconciler` all run in **slots** (covered by the slot
   watchdog) but create **no `AgentRow`** — so they're absent from the `agents` list / `/api/agents` health view. The
   slot watchdog sees the tmux session, but the unified agents-oversight + dashboard agents panel do not.
3. `monitor` / `recovery-audit` / `usage_reporter` have **no automated spawner** in `server/`. `usage_reporter` +
   `monitor` are reachable only via the manual `/api/agents/spawn` dropdown (`spawn_agent_preview` lists role set
   `main/review/backup/usage_reporter`); `recovery-audit` has no caller at all.
4. Role-set mismatch: `spawn_agent_preview` offers `usage_reporter` but `AgentRole` is `main/review/backup/custom` —
   `usage_reporter`/`monitor` don't map to a registered role.

**Open questions for the operator (Phase-1 exit — needed before Phase 2 deletes/changes):**

- **Q1 — plan-health vs plan-reconciler:** they're report-mode vs reconcile-mode of one dispatcher. Keep BOTH modes
  (lightweight report + heavy daily reconcile), or does reconcile-mode supersede report-mode → delete `plan-health`
  (report) + its template? (You said one should be removed — the code keeps both as modes, so this is your call.)
- **Q2 — recovery-audit:** aspirational Layer-1 from the autonomous-recovery-matrix, no spawner. Wire it (it's part of
  the DR design) or delete the template until DR Layer-1 is actually built?
- **Q3 — usage_reporter:** its own header says the agent path is DEFERRED and `UsagePoller` already does the real work.
  Delete the agent template (keep the deferred note in codex) or keep it manually-spawnable?
- **Q4 — monitor:** keep as the documented manual "custom-role" pattern template for ad-hoc external-watch agents, or
  delete?

⚠️-cells still to walk in a Phase-1 follow-up: whether slot-spawned escalation/plan agents set `SlotRow.status`+
`tmux_session` so the slots panel shows them as working; exact `review` dual-tracking; whether the `plan-reconciler`
systemd timer is live yet (lifecycle doc says bringup pending).

### Phase 1 decisions (operator 2026-06-17)

- **Q1 → KEEP BOTH** `plan-health` (report) and `plan-reconciler` (reconcile). They are complementary modes of
  `run_plan_health`; neither is deleted.
- **Q2 → KEEP recovery-audit, mark WIP / NOT-FINALISED, NEVER LAUNCH.** Do not delete it — we still owe its boot prompt
  + duties. Keep the infra ready to support it, banner the template as WIP, and add a HARD guard so it can never
  actually be spawned/launched until finalised.
- **Q3 → DELETE usage_reporter.** Account usage comes from the httpx `UsagePoller`; the agent path is vestigial. Remove
  the template + its role from the spawn-preview/spawn surface.
- **Q4 → KEEP monitor** as the documented manual external-watch (custom-role) pattern.

### New cross-cutting requirement (operator 2026-06-17) — per-agent identity + attach handles

EVERY live agent (every type) must persist, at spawn time, the handles the backend needs to (a) resume it and (b)
attach to / health-check it:

- **`claude_session_id`** — the deterministic Claude session UUID (the `--resume` handle; shared with the failover
  plan's Phase 1). Already being added to the main-agent row; must extend to ALL types.
- **`tmux_session`** (+ the exact pane/attach target) — the handle to attach to the running tmux session and capture
  its pane, so the backend (and the operator) can inspect/health-check any agent uniformly.

These become mandatory columns on whatever row owns the agent (`SlotRow` for slot-based, `AgentRow` for standalone), set
at spawn, so no agent is un-attachable or un-resumable and the backend can check every one the same way.

### ⚠️ follow-up walk — RESOLVED 2026-06-17

- **Escalation slot identity (⚠️1):** `escalation.py` sets the **`EscalationQueueRow`** status (`"dispatched"`), NOT
  the `SlotRow` — it never stamps `SlotRow.status`/`tmux_session`/`claude_session_id` when it occupies a slot. The
  escalate/conflict-resolver worker DOES run in a slot and `WorkerLivenessWatchdog` covers it, but with KNOWN
  status-accuracy quirks (the watchdog carries special handling for one-shot escalate/conflict-resolver/review workers:
  "idle slot but live session" + "stale working/killed", incidents 2026-06-10). → confirms the gap: dispatcher-set slot
  identity is incomplete; Phase 3's AgentRow registration + handle-capture is the fix.
- **`review` dual-tracking (⚠️2):** review is dual **by design and correctly** — a PERSISTENT slot-resident agent
  (`ORCHESTRATOR_REVIEW_SLOTS` / `config.review_slot_ids()`, template `review`) that registers an `AgentRow` and
  heartbeats via `/poll` (`AgentRow.last_ping`; `_review_agent_heartbeat_silent` checks it by `tmux_session`). It is the
  **reference pattern** for Phase 3 — exactly what escalate/plan-health/plan-reconciler should become (slot-resident +
  AgentRow-registered + heartbeat + identity handles). No change needed to review itself.
- **`plan-reconciler` timer (⚠️3):** **NOT live** — `systemctl list-timers` on the central VM shows no
  plan-reconciler/orch timer at all. The installer (`scripts/install-plan-reconciler-timer.sh`) exists (infra-ready) but
  has not been run on the VM; bringup still pending per the lifecycle doc. So today only `plan-health` (report mode, via
  `run_plan_health`/`plan_health` escalation walls) is live; `plan-reconciler` (reconcile mode) is dormant until the
  timer is installed.

**Phase 1 is COMPLETE** — full matrix + decisions + the three ⚠️ cells resolved. Phase 2 (rationalize per decisions) +
Phase 3 (register + identity capture, using `review` as the reference pattern) are unblocked.
