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

| Type                                    | Registers AgentRow?      | Notes                                              |
| --------------------------------------- | ------------------------ | -------------------------------------------------- |
| `main`                                  | ✅ (main_agent_keeper)   | full                                               |
| `worker` / `review`                     | ✅ (`/api/agents/spawn`) | full                                               |
| `escalate` / `conflict-resolver`        | ❌                       | bespoke escalation_queue + EscalationWatchdog only |
| `plan-health`                           | ❌                       | DUPLICATE with plan-reconciler — one to be removed |
| `plan-reconciler`                       | ⚠️ unverified            | the newer daily deep reconciler                    |
| `monitor` / `backup` / `recovery-audit` | ⚠️ unverified            | purpose unclear — audit + fix boot prompts         |
| `usage_reporter`                        | ⚠️ unverified            | usage-poll reporter                                |

## Phased execution

### Phase 1 — Audit every agent type (the coverage matrix)

- [x] ✅ [ORCHESTRATOR] P1. For each template in `agents/`, document: PURPOSE, is it LIVE/used (which code path spawns it,
      or is it dead), the spawn entrypoint, whether it calls `register_agent` (→ AgentRow), whether `health.py`
      staleness + `reap_orphan_agents` + a watchdog cover it, and whether it shows in the dashboard. Produce a coverage
      matrix in this plan's Progress Log. Repo: agent-orchestrator (audit; no code).
- [x] ✅ [ORCHESTRATOR] P1. Classify each type: KEEP (register + cover), CLARIFY (live but boot-prompt/role unclear →
      rewrite the boot prompt), or DELETE (dead/duplicate). Record the decision per type. Repo: agent-orchestrator.

### Phase 2 — Rationalize the set (per Phase-1 decisions)

- [x] ✅ [ORCHESTRATOR] P2. `plan-health` + `plan-reconciler`: KEEP BOTH (Q1), document them in the `agents/*.md` headers +
      codex as the two modes of `run_plan_health` (report vs reconcile). See the dedicated "plan-health +
      plan-reconciler — duties + finding routing" section below for the decided design (Option B + routing). Repo:
      agent-orchestrator (`agents/`, codex).

#### plan-health + plan-reconciler — duties + finding routing (operator-decided 2026-06-17)

**Motivation (real evidence):** plan-health IS running and produces GOOD findings, but they go to a black hole.
`plan_health.record_result` writes them as one generic `activity_log` row (`event_type=plan_health_result`) and
**nothing consumes it** (no dashboard panel, no report, no Slack). Proof it's broken: the SAME doc-drift finding
("`SUB_AGENT_MANDATORY_RULES.md` still teaches the RETIRED tab-branch model") recurs across **3 consecutive runs**
(agt-9805fa / agt-68a4ca / agt-aed422, 2026-06-16) because nothing fixes it. Sample contradictions = epic-status ↔
active-plan drift (e.g. `defi_master` lists Phases 1-4 open while the child plan has them done).

**Operator-confirmed design (Harsh ↔ Ikenna, 2026-06-17):** KEEP the reconciler — it is a trust-building step ("if
agents can't flip a verified checkbox, we can't trust them for overnight trading fixes on real capital"). Middle ground:
**auto-fix the verifiable EASY ones (flips with sha/PR evidence + mechanical hygiene), ALERT the HARD ones** for an
operator decision. **Single operator surface = the agent-orchestrator alerts feed (Slack)** — conflicts/questions
surface there and the operator decides in the dashboard chat; the PR + findings doc are the detailed record, but the
ALERT is the trigger ("alerts stay the only thing you need to look at"; nothing else would prompt the operator to read
PM-repo conflict notes).

**Reconciler lifecycle — async-ask → e2e → loop-and-wait → apply (operator 2026-06-17):**

- [x] ✅ [ORCHESTRATOR] P1. Change `agents/plan-reconciler.md` from strict one-shot to **persistent-until-resolved**: run
      the full e2e reconciliation pass first (auto-fix verifiable easy ones; on any issue/question **post an async
      alert + a filed todo/ping and CONTINUE — never block/wait**). After the pass, **re-check whether its questions
      were answered**: answered → apply; any still-open → **enter the heartbeat wait-loop like the persistent agents**,
      re-checking + applying each answer as it arrives, until resolved, THEN exit. Answers arrive via the dashboard-chat
      → message/poll path. Repo: agent-orchestrator (`agents/plan-reconciler.md`).
- [x] ✅ [ORCHESTRATOR] P1. While waiting, the reconciler sets **`status=blocked`** (the watchdog never reaps a `blocked`
      slot) and its `AgentRow` shows "blocked — waiting for operator answer" (honest, not fake-"working") — composing
      with the Phase-3 AgentRow registration so a waiting reconciler is visible in the dashboard. Each open question is
      ALSO filed (alert + todo/ping) so the loop is the fast path and the filed item the durable one. Repo:
      agent-orchestrator.

**Decided division — Option B (health = cheap frequent radar; reconciler = daily fixer that consumes it):**

- [ ] [ORCHESTRATOR] P1. **Route `doc_drift` → operator** (governance-doc edits are human-owned — the reconciler
      deliberately only flags them). In `plan_health.record_result`, when `doc_drift` is non-empty, (a) **Slack-page**
      it, DEDUPED by `(doc, contradicted_by, claim)` so the recurring tab-branch drift pages once, not every run, and
      (b) upsert a **single standing surface** (one issue doc, e.g. `plans/active/issues/governance_doc_drift.md`, or a
      standing todo) that persists until resolved — so re-detection updates the same entry instead of re-alerting. Repo:
      agent-orchestrator (`server/plan_health.py` + `notifications/slack.py`).
- [ ] [ORCHESTRATOR] P1. **Route `contradictions` → the reconciler** (it already verifies + flips/banners these). The
      daily plan-reconciler INGESTS the latest plan-health `contradictions` as its STEP-3b candidate list (read the most
      recent `plan_health_result` for the contradiction half) — verify against code, then flip/banner/file — rather than
      re-deriving from scratch. Repo: agent-orchestrator (`server/plan_health.py` reconcile path +
      `agents/plan-reconciler.md`).
- [x] ✅ [ORCHESTRATOR] P2. **Boot-prompt updates reflecting the routing:** `agents/plan-health.md` — note its findings now
      have real consumers (doc_drift→operator, contradictions→reconciler), so the output matters; keep it cheap +
      report-only (skeleton-only, no repo FF, fast model). `agents/plan-reconciler.md` — add the STEP that consumes the
      latest plan-health contradictions as its candidate set. Repo: agent-orchestrator (`agents/`).
- [ ] [ORCHESTRATOR] P3. Optional `plan-health` enrichment: surface a one-line hygiene/orphan pulse (it already builds
      the digest) in its report so the operator gets a daily snapshot. Repo: agent-orchestrator
      (`agents/plan-health.md`, `plan_health.py`).
- [x] ✅ [ORCHESTRATOR] P1. `recovery-audit`: KEEP but mark WIP / NOT-FINALISED (Q2). Banner `agents/recovery-audit.md` as
      WIP (boot prompt + duties owed) and add a HARD never-launch guard — the spawn/role surface must refuse to actually
      launch `recovery-audit` until finalised (e.g. exclude from the spawnable role set + an explicit `RuntimeError`/log
      if anything tries). Keep the supporting infra in place. Repo: agent-orchestrator (`agents/recovery-audit.md`,
      spawn/role wiring).
  - **DEFERRED-ASPIRATIONAL (operator 2026-06-19):** the never-launch holding pattern (guard shipped) is the durable
    state for now — **do NOT wire or delete it.** It "comes into picture later"; the wire-vs-delete finalization + what
    Layer-1 signoff/actuation it performs is **pending Ikenna's design intent** (unknown to Harsh). Not an open decision
    to action now — leave guarded + aspirational until Ikenna defines it.
- [x] ✅ [ORCHESTRATOR] P1. `usage_reporter`: DELETE (Q3). Remove `agents/usage_reporter.md` + its role from
      `spawn_agent_preview` / `/api/agents/spawn` role set + any other reference; usage stays on the httpx
      `UsagePoller`. Repo: agent-orchestrator (`agents/`, `routes/agents.py`, models).
- [x] ✅ [ORCHESTRATOR] P2. `monitor`: KEEP (Q4). Confirm/clarify the `agents/monitor.md` header documents it as the manual
      external-watch (custom-role) pattern, manual-spawn only. Repo: agent-orchestrator (`agents/`).

### Phase 3 — Register every LIVE agent type + capture its identity/attach handles

> Per the cross-cutting requirement above: every live agent persists `claude_session_id` (--resume handle) +
> `tmux_session` (attach/capture handle) at spawn, so the backend can resume, attach to, and health-check ALL types
> uniformly.
>
> **Already DONE by the failover plan** (`agent-orchestrator@380fe6c`+`dd6b545`, drained to staging — verified
> 2026-06-17): the **`claude_session_id` column exists on BOTH `SlotRow` (`orm.py:115`) and `AgentRow` (`orm.py:273`)**
>
> - a `bootstrap.py` migration; the deterministic id is minted via `tmux_spawn.new_session_id()` → `--session-id`
>   (`tmux_spawn._build_claude_flags`); and it is minted+persisted on the **autospawn** (`autospawn.py:391-397` +
>   snapshot persist-back `:731-738`), **manual /spawn** (`routes/slots_ops.py:359-366`), and **main-agent**
>   (`main_agent_keeper`) paths, with resume-on-cap in `worker_liveness_watchdog.py:847-966` + `main_agent_keeper`. So
>   the COLUMN + MINTING infra is in place — Phase 3 only has to extend PERSISTENCE + REGISTRATION to the slot-based
>   escalation/plan paths that the failover did not cover, and widen the role enum + UI.

- [x] ✅ [ORCHESTRATOR] P1. **Persist the minted identity on the escalation + plan-health paths** (the failover gap):
      `escalation.escalate` (`escalation.py:259-322`) and `plan_health.run_plan_health` (`plan_health.py:154`) call
      `autospawn.do_spawn(slot=slot_spec, …)` with a DETACHED snapshot — `_do_spawn` mints `spawn_session_id` onto the
      snapshot but the callers only persist their OWN row (`EscalationQueueRow`), never writing
      `claude_session_id`/`tmux_session` back to the live `SlotRow`. Write both back after `do_spawn` (the snapshot
      already carries the minted id — `snapshot.claude_session_id`). Repo: agent-orchestrator (`server/escalation.py`,
      `server/plan_health.py`).
- [x] ✅ [ORCHESTRATOR] P1. `escalate` / `conflict-resolver`: `register_agent` at dispatch (`escalation.py`) with
      role/label/`tmux_session`/`claude_session_id` + escalation_id linkage, so the agent appears as an `AgentRow` and
      is health/reaper-covered — WITHOUT breaking the escalation_queue/EscalationWatchdog tracking (reconcile the two:
      AgentRow = liveness/attach/oversight, escalation_queue = the wall's work-state). Use `review` (the slot-resident
      AgentRow + `/poll` heartbeat pattern, Phase-1 §⚠️2) as the reference. Repo: agent-orchestrator
      (`server/escalation.py`).
- [x] ✅ [ORCHESTRATOR] P1. `plan-health` + `plan-reconciler`: `register_agent` at spawn (`plan_health.py`) with
      role/label/`tmux_session`/`claude_session_id`. Repo: agent-orchestrator (`server/plan_health.py`).
- [x] ✅ [ORCHESTRATOR] P1. Widen `AgentRole` (`models/_types.py:14` = `Literal["main","review","backup","custom"]`) — add
      escalate/conflict-resolver/plan-health/plan-reconciler (or a parallel role field) so their registration is
      well-typed (reconcile with the `spawn_agent_preview` role set after the usage_reporter delete). Repo:
      agent-orchestrator (`server/models/_types.py`, `orm.py`).
- [x] ✅ [ORCHESTRATOR] P2. Backend can ATTACH/inspect any agent from its stored handles: a uniform "capture this agent's
      pane" path keyed off `tmux_session` works for every registered type (the reaper's dead-session check + the
      liveness probes already key off `tmux_session`; confirm they now cover the newly-registered types). Repo:
      agent-orchestrator.

### Phase 4 — UI visibility (operator can SEE every working agent)

- [ ] [ORCHESTRATOR][UI] P1. Verify the agents feed (`/api/agents`) surfaces ALL live agent types (escalate /
      conflict-resolver / plan-reconciler / monitor / …) while working, and the dashboard renders each role (icon/label
      per type, not just worker/main). Add any missing role rendering. Repo: agent-orchestrator dashboard (+
      deployment-ui if it mirrors the agents panel).
- [ ] [ORCHESTRATOR][UI] P2. Regression guard: a smoke/spec asserting a non-worker agent type (e.g. an escalation agent)
      appears in the agents list when registered. (If this touches `deployment-ui`, the playwright gate applies —
      `pw:L2 ✓` + cited regression spec.) Repo: deployment-ui / agent-orchestrator dashboard.

### Phase 5 — Uniform staleness/liveness verification + tests

- [x] ✅ [ORCHESTRATOR] P1. Confirm `health.py` staleness + `reap_orphan_agents` (incl. the Gap-1 stale-sessionless reap
      from the lifecycle issue doc) + the worker-liveness watchdog (or an equivalent) now apply to every registered
      type; close any type-specific gap. Repo: agent-orchestrator.
- [x] ✅ [ORCHESTRATOR] P1. Unit tests: each newly-registered type creates an AgentRow with the right role/session; the
      reaper/health path treats it like any agent; no double-count vs the escalation watchdog. Repo: agent-orchestrator
      (`tests/`).
- [ ] [ORCHESTRATOR] P2. Live smoke on the central VM: trigger an escalation + the plan-reconciler, confirm both appear
      as agents in the dashboard while working and are reaped when their session dies. Repo: agent-orchestrator.

### Phase 6 — Unified AgentKeeper + agent-lifecycle architecture (operator-decided 2026-06-19) — FOLLOW-UP, build AFTER Phases 1–5 ship+test

> **Supersedes** the 2026-06-18 "demand-driven adaptive-cadence" review design (workload-signal fast/idle polling is
> dropped — replaced by **flat default loops + a wake-on-message nudge**, which is simpler and the operator's decision)
> AND resolves the deferred "should review get its own keeper?" question: **YES — one unified keeper for ALL mandatory
> agents.** Its own unit of work — do NOT fold into the 1–5 branch. Principle retained: the backend supplies the record;
> the AGENT owns what/how-much to review — never gate its capacity.
>
> **Architecture (operator 2026-06-19):**
>
> - **ONE unified `AgentKeeper` runs on EVERY VM** (local / planning / each worker VM) — merges today's `MainAgentKeeper`
>   + AutoSpawn's `_ensure_review_agents` into a single keeper that guarantees the MANDATORY set is present + respawns it
>   if it dies. Fixes the dev-box gap (review didn't come up because it rode AutoSpawn).
> - **Mandatory on ALL VMs: `main` AND `review`** (both, every VM — not central-only).
>   - `main`: default **60s** loop; **env-configurable interval** (e.g. raise to 5 min when not needed; up to 60 min on
>     slow-moving VMs).
>   - `review`: default **15-min** loop; env-configurable. Keeps the `/compact`-discipline + the advisory reviewed-ledger
>     (below). The long idle loop is made responsive by the wake-nudge, NOT by fast workload-signal polling.
> - **Wake-on-message nudge (IN SCOPE — the enabler for long loops):** when a UI message arrives for an agent, the
>   backend wakes it from its (possibly 15–60 min) loop via `tmux_spawn.send_command(session, …)` (the send-keys
>   primitive already exists, `tmux_spawn.py:829`). So a long idle loop saves tokens WITHOUT adding message latency. This
>   is NOT the dropped messaging-layer rewrite (no adaptive-cadence / long-poll / SSE) — just a one-shot tmux wake.
> - **On-demand agents via AutoSpawn (unchanged split):** escalate / conflict-resolver / plan-health / plan-reconciler /
>   fleet / workers — spawned as needed per VM-type policy.
> - **Fleet-worker cap (on-demand pool, SEPARATE from the 2 mandatory): 10 default on all VMs; 6 on the planning VM**
>   (planning also runs main+review+orchestration, so a lower fleet ceiling).
> - Loop intervals are env-vars per agent type/VM; **live UI loop-control is a P3 nice-to-have (not mandatory).**

- [ ] [ORCHESTRATOR] P1. Unified `AgentKeeper` (every VM): merge `MainAgentKeeper` + `_ensure_review_agents` → one keeper
      that guarantees mandatory {main, review} present + respawns on death; remove the AutoSpawn `_ensure_review_agents`
      path. Repo: agent-orchestrator (`server/`).
- [ ] [ORCHESTRATOR] P1. Env-configurable loop intervals: `main` default 60s, `review` default 900s (15 min), each
      overridable per VM (e.g. `ORCHESTRATOR_MAIN_LOOP_SECONDS` / `ORCHESTRATOR_REVIEW_LOOP_SECONDS`); thread the value
      into the boot-prompt `/loop <N>s` render. Repo: agent-orchestrator (`server/` + `agents/main.md`,`agents/review.md`).
- [ ] [ORCHESTRATOR] P1. Wake-on-message nudge: `POST /api/agents/{id}/nudge` (and auto-fire on a UI message to an agent)
      → `tmux_spawn.send_command(tmux_session, …)` to wake the agent from a long loop for an immediate poll/drain. Repo:
      agent-orchestrator (`server/`).
- [ ] [ORCHESTRATOR] P1. AutoSpawn VM-type policy: on-demand fleet-worker cap = **10** default (all VMs), **6** on the
      planning VM; mandatory main+review are not counted against it. Config-driven per VM. Repo:
      agent-orchestrator (`server/autospawn.py` + config).
- [ ] [ORCHESTRATOR] P1. **DEPRECATE the `backup` agent** (operator 2026-06-19 — supersedes the 2026-06-17 "KEEP backup"
      below): the AgentKeeper makes main+review mandatory + auto-respawns them, so the manual promote-from-backup failover
      is redundant; if the keeper ever fails, the operator spawns a fresh main/review from the UI. Remove `backup` from
      `AgentRole` + `AgentKind` (`models/_types.py`), `ROLES_ORDER`/`KINDS_ORDER` (`dashboard/`), `_default_kind_lifecycle`
      (`state_store/agents.py`), and **delete `agents/backup.md`**. Keep the generic `promote` (role-swap) mechanism. NOTE
      `ROLES_ORDER` is also touched by `agent_orchestrator_dashboard_monitoring_2026_06_19.md` (AgentTypesPanel) — same
      agent should own both to avoid a collision. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P2. Reviewed-ledger (advisory, NOT a gate): persist reviewed (sha/task/event_id + verdict + ts) per
      `review` role + a mark-reviewed endpoint; review reads it to skip redundant **isolated** re-review but stays free to
      review across multiple commits/plans at its own discretion. Repo: agent-orchestrator (`server/`).
- [ ] [ORCHESTRATOR] P2. `agents/review.md`: 15-min default loop + `/compact` discipline + mark-reviewed call + ledger is
      an aid not a limit + responds to the wake-nudge. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P3. (nice-to-have) Live loop-interval control from the dashboard UI (re-issue an agent's `/loop`
      cadence via the nudge/tmux path). Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P2. Tests: keeper brings up {main, review} on a VM with AutoSpawn OFF; env loop-interval override
      lands in the rendered loop; nudge wakes an agent mid-long-loop; fleet cap enforced (10 / planning 6) excluding
      mandatory. Repo: agent-orchestrator (`tests/`).

### Phase 7 — Escalation dispatch reliability (incident found on the central VM 2026-06-18)

> **Live incident (central VM `i-0c9b283b...`, diagnosed 2026-06-18):** escalation dispatch was failing in a tight
> `dispatch_initiated → dispatch_failed` loop (one wall, `agt-c9d2ff`, hit **316 attempts**); 19 walls abandoned at TTL.
> **Root cause (full chain):** slot-1's `unified-api-contracts` worktree had **1 uncommitted source file**
> (`canonical/domain/sports/league_data.py`, real orphan WIP) → the `*/5` FF-cron `[skip:dirty]`'d it → uac drifted **88
> commits behind** → the pre-spawn branch-state gate ran `git merge --ff-only`, which **fails on a dirty tree** → status
> `diverged` → **slot-1 quarantined** → every escalation dispatch onto slot-1 (the lowest sessionless slot) failed and
> was re-picked next tick. NOT capacity, NOT stale code, NOT the gate logic. The reasons were fully captured in
> `escalation_queue.last_error` + `activity_log.details_json` but were **invisible in the dashboard UI** (only the bare
> `escalation_dispatch_failed` event showed). The three robustness gaps this exposed:

- [x] ✅ [ORCHESTRATOR] P0. Immediate unblock (DONE 2026-06-18): preserved slot-1's uac orphan WIP to
      `origin/wip-preserve/slot1-uac-sports-league-data-2026-06-18` (uac@9169c40) + reset clean + ff'd the 88-behind →
      `check_slot_branch_state(1)` now `should_stop=False` → verified `escalation_dispatched` at 16:41:49 (the 316-retry
      loop broke). Repo: agent-orchestrator (central VM op).
- **MOVED → `monitoring_surfaces_overhaul_2026_06_18.md` Track A** (no dual-tracking): "Render the per-event FAILURE
  REASON in the activity feed + escalations surface" — surfacing `last_error` / `details_json.error` in the UI is a
  monitoring-surface concern, tracked there with the activity-feed overhaul.
- [x] ✅ [ORCHESTRATOR] P1. Fix the slot-starvation bug (DONE — agent-orchestrator@51bf0b6, QG-green):
      `escalation._pick_free_slot` now skips a recently-branch-quarantined slot (`_recently_quarantined` + 10-min TTL)
      so a sessionless quarantined slot is no longer re-picked every tick (the 316-retry loop) — dispatch falls through
      to a healthy slot; the TTL lets it recover once the worktree clears. Tests:
      `test_pick_free_slot_skips_quarantined_slot` + `test_dispatch_failure_on_quarantine_marks_the_slot` +
      `test_quarantine_skip_marks_then_recovers_after_ttl`. Repo: agent-orchestrator (`server/escalation.py`).
- [ ] [ORCHESTRATOR] P2. Self-heal a dead-session dirty dep: `_do_spawn` only auto-resolves dirty state AFTER the
      branch-state gate passes, but the gate STOPs first on the ff-fail. A dead-session dirty dep (no live editor)
      should be auto-preserved to `wip-preserve/` + FF'd rather than quarantining the slot indefinitely. Repo:
      agent-orchestrator (`server/autospawn.py` + `worktree_clean_check`).
- **MOVED → `alert_quality_overhaul_2026_06_18.md` Phase 3** (no dual-tracking): "ADD a missing alert: slot stuck in
  branch-state quarantine" — a slot quarantined > N min while walls queue pages with the specific repo + cause. It's an
  alert-quality concern, tracked there with the error-pointer standard.

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
- Deleting the superseded plan-\* type must remove its scheduler/event trigger too (a dangling cron/dispatch that spawns
  a deleted template would error).
- UI work touching `deployment-ui` is gated by the playwright HARD RULE (`pw:L2 ✓` + regression spec).

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — document the full agent-type roster + that EVERY live type
  registers an AgentRow and is health/reaper/UI-covered (single oversight model, no bespoke-only types).
- `codex/05-infrastructure/agent-orchestrator-worker-topology.md` — agent-type coverage matrix.

## Cross-links

- Lifecycle issue doc (Gap 1 = reaper never reaps a stale sessionless AgentRow — same oversight theme; this plan extends
  coverage to the types that don't even create an AgentRow):
  `plans/active/issues/orchestrator_agent_lifecycle_gaps_2026_06_16.md`.
- Sibling orchestrator-reliability plan: `plans/active/orchestrator_account_failover_resume_respawn_2026_06_17.md`.

## Progress Log

### Phase 1 coverage audit — 2026-06-17 (slot-2)

**Two distinct oversight systems exist (the root of the fragmentation):**

- **Slot-based** — agents spawned into an `orch-slot-N` tmux session via a `SlotRow` (`_pick_free_slot` → `do_spawn`).
  Overseen by `WorkerLivenessWatchdog` (scans slots: stuck-at-prompt / heartbeat-silent / usage-cap). No `AgentRow`.
- **AgentRow-based** — standalone sessions registered via `register_agent` into the `agents` table
  (`AgentRole = Literal["main","review","backup","custom"]`). Overseen by `health.py` staleness + `reap_orphan_agents`
  (+ `main_agent_keeper` for main). This is the path that feeds the dashboard agents list / `/api/agents`.

A type is well-covered only if it lands cleanly in ONE of these. The gap class is the types that run in a slot but whose
`SlotRow`/dashboard state may not reflect them, and the types registered as agents but not health-covered.

**Coverage matrix** (✅ confirmed · ⚠️ needs deeper walk · ❌ confirmed-absent):

| Type                | Purpose                                                                                       | Live?                                                | Spawn path                                                              | Oversight model                                                        | UI-visible while working | Class               |
| ------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------ | ------------------- |
| `main`              | the orchestrator agent                                                                        | ✅                                                   | `main_agent_keeper._spawn` (`orch-agent-main`)                          | AgentRow + health + reaper + keeper                                    | ✅ (agents list)         | KEEP                |
| `worker`            | does plan-backlog work in a slot                                                              | ✅                                                   | `autospawn._do_spawn` (default template)                                | Slot + WorkerLivenessWatchdog                                          | ✅ (slots panel)         | KEEP                |
| `review`            | reviews work                                                                                  | ✅                                                   | `autospawn` review slots (`_REVIEW_PROMPT_TEMPLATE`) AND an `AgentRole` | ⚠️ dual (slot AND AgentRow) — clarify                                  | ⚠️                       | KEEP+CLARIFY        |
| `backup`            | idle, promote→main/review via dashboard                                                       | ✅                                                   | `/api/agents/spawn` (role)                                              | AgentRow + health + reaper                                             | ✅                       | ~~KEEP~~ → **DEPRECATE** (2026-06-19; AgentKeeper supersedes — see Phase 6) |
| `escalate`          | resolves a CI wall on LDR                                                                     | ✅                                                   | `escalation.escalate` → free slot                                       | Slot watchdog + escalation_queue + EscalationWatchdog; **no AgentRow** | ⚠️ slot panel only       | KEEP+REGISTER       |
| `conflict-resolver` | resolves a PR merge conflict                                                                  | ✅                                                   | `escalation.escalate` (PR walls) → free slot                            | same as escalate                                                       | ⚠️                       | KEEP+REGISTER       |
| `plan-health`       | REPORT-mode cross-plan drift check                                                            | ⚠️ report-mode of `run_plan_health`                  | `plan_health.run_plan_health(mode="report")` → free slot                | Slot watchdog; **no AgentRow**                                         | ⚠️                       | DECISION (see Q1)   |
| `plan-reconciler`   | RECONCILE-mode daily deep fixer (opus/max)                                                    | ⚠️ bringup (systemd timer pending per lifecycle doc) | `run_plan_health(mode="reconcile")` → free slot                         | Slot watchdog; **no AgentRow**                                         | ⚠️                       | DECISION (see Q1)   |
| `monitor`           | manual "custom-role" pattern: watch an external long-running thing + ping                     | ⚠️ template/pattern only — no auto-spawner           | manual (custom role)                                                    | none specific                                                          | ❌                       | CLARIFY (Q4)        |
| `recovery-audit`    | aspirational Layer-1 defence-in-depth signoff/actuator                                        | ❌ no spawner found in code                          | —                                                                       | none                                                                   | ❌                       | CLARIFY/DELETE (Q2) |
| `usage_reporter`    | refresh account usage — **header self-declares DEFERRED**; real path is `UsagePoller` (httpx) | ⚠️ manually spawnable via agent-spawn dropdown only  | `/api/agents/spawn` (role)                                              | not in `AgentRole` enum → ⚠️ may not register cleanly                  | ⚠️                       | DECISION (Q3)       |

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
  - duties. Keep the infra ready to support it, banner the template as WIP, and add a HARD guard so it can never
    actually be spawned/launched until finalised.
- **Q3 → DELETE usage_reporter.** Account usage comes from the httpx `UsagePoller`; the agent path is vestigial. Remove
  the template + its role from the spawn-preview/spawn surface.
- **Q4 → KEEP monitor** as the documented manual external-watch (custom-role) pattern.

### New cross-cutting requirement (operator 2026-06-17) — per-agent identity + attach handles

EVERY live agent (every type) must persist, at spawn time, the handles the backend needs to (a) resume it and (b) attach
to / health-check it:

- **`claude_session_id`** — the deterministic Claude session UUID (the `--resume` handle; shared with the failover
  plan's Phase 1). **Column + minting DONE by the failover** on SlotRow + AgentRow (worker/manual/main paths); remaining
  = extend persistence to the escalation/plan paths (see Phase 3).
- **`tmux_session`** (+ the exact pane/attach target) — the handle to attach to the running tmux session and capture its
  pane, so the backend (and the operator) can inspect/health-check any agent uniformly.

These become mandatory columns on whatever row owns the agent (`SlotRow` for slot-based, `AgentRow` for standalone), set
at spawn, so no agent is un-attachable or un-resumable and the backend can check every one the same way.

### ⚠️ follow-up walk — RESOLVED 2026-06-17

- **Escalation slot identity (⚠️1):** `escalation.py` sets the **`EscalationQueueRow`** status (`"dispatched"`), NOT the
  `SlotRow` — it never stamps `SlotRow.status`/`tmux_session`/`claude_session_id` when it occupies a slot. The
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

### Boot-prompt enhancement progress — 2026-06-17 (local commits, not yet pushed)

Reworking each agent's `agents/*.md` boot prompt per the decided duties. Done so far (LOCAL commits in
`agent-orchestrator`; operator pushes later):

- **`plan-health` + `plan-reconciler`** (`agent-orchestrator@183910f`): plan-health = cheap frequent radar, header
  documents the decided routing (doc_drift→operator, contradictions→reconciler). plan-reconciler = persistent-until-
  resolved: middle-ground (auto-fix verifiable easy / ALERT hard to the single dashboard surface), ASK-but-never-block
  via `/blocked`, STEP-4 two-channel routing (alert + filed todo), new STEP-6 loop-and-wait apply.
- **`escalate` + `conflict-resolver`** (`agent-orchestrator@e000cde`): human-decision walls now ASK via `/blocked` with
  a **BOUNDED 2-min wait** (operator-decided 2026-06-17) — they run on the central VM beside the MAIN agent (first
  responder, answers in seconds) → apply; main says exit/stop OR 2-min timeout → free the slot (shared CI capacity; the
  question persists → operator answer re-dispatches). Authoring-slot ping kept as the completion FYI. **Also fixed the
  recurring plan-health doc-drift**: escalate's `ldr_qg_failure`/`plan_health` cases shipped via the RETIRED
  "tab-branch→mirror path" → now `quickmerge --agent --files` (Path-B) / the sanctioned `docs(plans)` carve-out.
  - **Lifecycle distinction:** plan-reconciler (dedicated daily run) = unbounded loop-and-wait; escalate/conflict-
    resolver (shared CI-firefighter capacity) = bounded 2-min wait then free the slot. Both never silently abandon.

**Remaining set DONE — 2026-06-18 (`agent-orchestrator@b3ec360`, LOCAL commit, not yet pushed):**

- **`worker`**: the FRESH-PULL / git-discipline section was the worker-facing tab-branch surface flagged in
  `worktree_ldr_unification_2026_06_08.md` line 179 — rewritten tab-branch → Path-B (each slot is its own clone ON
  `live-defi-rollout`, no tab branch; ship via `quickmerge --agent --files`; on LDR push-reject rebase keeping both
  sides; fixed the "`.git` is a FILE worktree" comment + the non-FF remedy → quickmerge).
- **`recovery-audit`** (Q2): **WIP / NOT-FINALISED "DO NOT LAUNCH" banner** at the top — no spawner, MUST be excluded
  from the spawnable role set + a `RuntimeError` guard until DR Layer-1 is built; keep the infra, don't wire any spawn
  path. (The code-side never-launch guard is the Phase-2 wiring item above; this is the boot-prompt half.)
- **`monitor`** (Q4): **MANUAL-SPAWN-ONLY** clarification — no auto-spawner/scheduler; operator spawns ad-hoc; registers
  an `AgentRow` (`role: custom`) so `health.py` + `reap_orphan_agents` cover it. KEEP as the documented pattern.
- **`main`**: blocked-queue sweep (STEP 2.5) note — it is first-responder for the NEW types too. escalate/conflict-
  resolver = bounded 2-min wait (answer within a tick or they free the slot); plan-reconciler = unbounded loop-and-wait.
  All POST the same blocked queue, so the one sweep covers every agent type — prioritise the bounded ones.
- **`backup`** — assessed, **no change**: already AgentRow-registered (`role: backup`) + `/poll` heartbeat + promote→
  main/review; full health/reaper coverage; does no git (follows main/review only once promoted) → no Path-B needed.
- **`review`** — assessed, **no change**: the reference pattern (slot-resident AgentRow + `/poll` heartbeat + identity
  handles, per ⚠️2); already modern, zero tab-branch drift.

`usage_reporter` is **NOT** in this boot-prompt pass — Q3 deletes it, but that is a COUPLED Phase-2 code change (remove
the template AND its role from `spawn_agent_preview` / `/api/agents/spawn` / models together); deleting the `.md` alone
would leave a dangling role reference, so it stays for the Phase-2 delete item above.

### Failover-implementation review — 2026-06-17

Reviewed the now-shipped account-failover (`agent-orchestrator@380fe6c`+`dd6b545`+`4985ef7`, drained to staging). It
materially advances Phase 3:

- **DONE:** `claude_session_id` column on `SlotRow`(`orm.py:115`)+`AgentRow`(`orm.py:273`) + `bootstrap.py` migration;
  deterministic `--session-id` minting (`tmux_spawn.new_session_id`); minted+persisted on autospawn
  (`autospawn.py:391-397`,`:731-738`), manual /spawn (`slots_ops.py:359-366`), main agent (`main_agent_keeper`);
  resume-on-cap (`worker_liveness_watchdog.py:847-966` + keeper, Decision-B headroom-gated).
- **Gap that is now Phase-3's job (NOT a failover defect — out of its scope):** `escalation.escalate`
  (`escalation.py:281-322`) + `plan_health.run_plan_health` spawn via a DETACHED `slot_spec` snapshot and persist only
  the `EscalationQueueRow` — they never write the minted `claude_session_id`/`tmux_session` back to the live `SlotRow`,
  and never register an `AgentRow`. So escalate/conflict-resolver/plan-health/plan-reconciler currently can't be
  `--resume`d on a cap and stay invisible to the agents view. Phase 3 (persist-back + register) closes it; the column +
  minting infra it needs already exists.

### Wave 1 — verification + Phase 1–5 backfill flips (2026-06-19, slot-2)

`/autonomous` dispatch resumed: complete EVERYTHING agent-orchestrator-side across this plan +
`agent_orchestrator_dashboard_monitoring_2026_06_19.md` + `alert_quality_overhaul_2026_06_18.md` (deployment-ui is owned
by another agent — explicitly out of scope here). Verified the post-compaction state directly against the code (the
summary was stale): **Phases 1–5 were implemented + pushed in prior commits but the checkboxes were never flipped.**
Backfilling now per the Commit+Push+Flip backfill rule. Evidence (all on `origin/live-defi-rollout`):

| Item                                              | Evidence                                                                                                       |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| P1 coverage matrix + classify                     | this Progress Log (matrix + Phase-1 decisions)                                                                 |
| P2 plan-health+reconciler KEEP BOTH (doc)         | agent-orchestrator@183910f boot prompts + headers                                                              |
| P1 plan-reconciler.md persistent-until-resolved   | agent-orchestrator@183910f                                                                                     |
| P1 reconciler status=blocked while waiting        | boot prompt @183910f + watchdog skips `blocked` (`worker_liveness_watchdog.py:565`)                            |
| P2 boot-prompt updates reflecting routing         | agent-orchestrator@183910f (plan-health.md + plan-reconciler.md)                                               |
| P1 recovery-audit KEEP/WIP + never-launch guard   | banner @b3ec360 + guard `prompts.py:71` `NEVER_LAUNCH` frozenset + `RuntimeError` + excluded from spawnable    |
| P1 usage_reporter DELETE                          | agent-orchestrator@51bf0b6 (`agents/usage_reporter.md` gone; `spawn_agent_preview` = main/review/backup/worker) |
| P2 monitor KEEP/clarify                           | agent-orchestrator@b3ec360 (manual-spawn-only, role=custom AgentRow)                                           |
| P1 persist identity on escalation+plan-health     | `escalation.py:356-361` + `plan_health.py:198-204` write claude_session_id/tmux_session back to live SlotRow   |
| P1 escalate/conflict-resolver register_agent      | `escalation.py:369` (kind=escalate/conflict_resolver, lifecycle=one_shot); `test_escalate_registers_one_shot_agent` |
| P1 plan-health/reconciler register_agent          | `plan_health.py:207` (kind=plan_health/plan_reconciler, lifecycle=scheduled); `test_dispatch_registers_scheduled_agent` |
| P1 widen role → two-axis kind+lifecycle           | `_types.py:23-37` AgentKind(11)+AgentLifecycle; `models/agents.py:28-29,56-57`                                 |
| P2 backend attach/inspect from tmux_session       | tmux_session persisted for all types; reaper/liveness probes key off it                                        |
| P1 health.py staleness+reaper cover every type    | `health.py:248-255` reaper is lifecycle-aware (one_shot/scheduled ending = EXPECTED, not a stale incident)     |
| P1 unit tests per newly-registered type           | test_escalation.py + test_plan_health.py registration tests assert kind+lifecycle                              |

**Still OPEN (this plan), driving next in order:** Phase 2 `doc_drift`→operator routing + `contradictions`→reconciler
ingestion (code in `plan_health.record_result` — today writes only the generic activity_log row, the "black hole");
Phase 2 P3 plan-health hygiene-pulse (optional); Phase 4 full per-role render + regression spec (Wave 6, **AO dashboard
gate is Vitest + tsc + build smoke — NO playwright, the dashboard has no pw harness**); Phase 5 live smoke (Wave 9);
Phase 6 unified AgentKeeper (whole phase); Phase 7 dead-session dirty-dep self-heal.
