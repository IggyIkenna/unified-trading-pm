---
title: "Agent-Orchestrator Dashboard Monitoring — agent-type visibility · activity feed · escalations"
created: 2026-06-19
status: active
parent_epic: orchestrator_master
assigned_vm: planning
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/monitoring_surfaces_audit_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source:
  - 2026-06-18 operator design session — orchestrator UI = agents/orchestrator lens
  - 2026-06-19 operator decision — split monitoring_surfaces_overhaul into two single-surface plans (agent-orchestrator
    dashboard here; deployment-ui pane → deployment_ui_monitoring_pane_2026_06_19.md)
  - plans/audit/results/monitoring_surfaces_audit_2026_06_18.md (Opus audit, 4 background agents)
priority: P2
---

# Agent-Orchestrator Dashboard Monitoring

> **Split 2026-06-19** from `monitoring_surfaces_overhaul_2026_06_18.md` (operator: two single-surface plans so the
> agent-orchestrator side and the deployment-ui side can be worked by separate agents without collision). The
> deployment-ui monitoring pane moved to `deployment_ui_monitoring_pane_2026_06_19.md`. This plan owns the
> **agent-orchestrator** dashboard surface only.

## Why

Operator (2026-06-18): the orchestrator dashboard owns everything about AGENTS + the orchestrator; an alert clicks
through to the right surface. The `agent_kind`/`lifecycle` data is already served — it's rendering + retention that's
missing. Full evidence + per-ask current-state/gap/change-list:
`plans/audit/results/monitoring_surfaces_audit_2026_06_18.md`.

## Agent-orchestrator dashboard (repo: agent-orchestrator; ALL `[UI]` → playwright/vitest gate, PLAN_FORMAT §9)

- [x] ✅ [ORCHESTRATOR] P0. **Retain finished one-shot/scheduled agents** (load-bearing): stop hard-deleting on
      completion (`DELETE /api/agents/{id}` `routes/agents.py:703`); transition to a terminal status (`finished` +
      `finished_at`/`exit_reason` on AgentRow) + a retention prune (last N per kind / 7d). Without this "show past
      escalate/plan-health runs" is impossible. Repo: agent-orchestrator (server).
- [x] ✅ [ORCHESTRATOR] P1. Filterable `GET /api/agents` — honor the dead-contract `status` param + add
      `kind`/`lifecycle`/ `include_finished`/`limit`, pushed into `state_store.list_agents` (WHERE/ORDER BY). Repo:
      agent-orchestrator.
- [x] ✅ [ORCHESTRATOR][UI] P1. New `AgentTypesPanel` (one new tab, keyed on `agent_kind`, running+past) —
      `KINDS_ORDER` + reuse `RoleHolders`/`AGENT_KIND_LABEL`; per-kind online count + show-finished toggle; mount
      desktop + mobile. Keep role chat (`main/review/backup`) clean. Evidence:
      `— repo@sha | pw:L2 ✓ | regression: <spec>`. Repo: agent-orchestrator (dashboard).
- [x] ✅ [ORCHESTRATOR] P1. Activity feed backend — push `slot`/`type`/category filters into SQL BEFORE the limit
      (`activity.py:86` / `routes/state.py:91-111`), add cursor pagination (`before_id`/offset + envelope), add a
      **denoise rollup** (`GROUP BY event_type[,slot] within window` → "×N in last 1h"; generalize
      `count_recent_activity`). The denoise is the "90% repeats" fix. Repo: agent-orchestrator.
- [x] ✅ [ORCHESTRATOR][UI] P1. Activity feed frontend — "Load older"/cursor append (decouple from the live poll),
      server-driven filter tabs, collapse duplicate rows with ×N badge + expand, smaller live poll (~25). Repo:
      agent-orchestrator (dashboard).
- [x] ✅ [ORCHESTRATOR][UI] P1. Render the per-event FAILURE REASON in the activity feed + escalations surface (moved
      from `orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 7). Today a `escalation_dispatch_failed` row
      shows only the bare event name; the reason IS already persisted (`escalation_queue.last_error` +
      `activity_log.details_json.error`) — it just isn't rendered, so the operator can't see WHY a dispatch failed
      without DB access (incident 2026-06-18: a slot-1 branch-quarantine starved dispatch for hours, invisible in the
      UI). Surface `details_json.error` inline (expandable) on failure-class activity rows, and `last_error` on the
      escalations view. Repo: agent-orchestrator (`server/` read path already has it + `dashboard/`).
- [x] ✅ [ORCHESTRATOR][UI] P2. Conditions tab collapsible (frontend-only): `COLLAPSED_COUNT=5`, sort
      OFF+`gates_queued>0` first, "Show N more ▾"/"Collapse ▴", keep the count chip. Repo: agent-orchestrator
      (dashboard).
- [x] ✅ [ORCHESTRATOR][UI] P2. Message-delivery VISIBILITY chip (operator decision 2026-06-19: **NO messaging-layer
      rewrite** — no adaptive-cadence / long-poll / SSE; the poll model stays). The only real gap is not knowing whether
      a sent message landed → surface the already-computed `count_pending_to_agent`/`pending_count` as a per-agent
      "queued → delivered" chip in the chat UI (data already served; frontend-only). Repo: agent-orchestrator
      (dashboard). NOTE: the **wake-on-message tmux nudge IS in scope** — but it lives in the unified-AgentKeeper work
      (`orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 6), because the default loops are now long
      (review 15 min, main up to 60 min) and the nudge is what makes a long idle loop responsive to a UI message. Live
      UI loop-interval control is the P3 nice-to-have there too.

### Follow-ups surfaced during live validation (2026-06-19)

- [x] ✅ [ORCHESTRATOR] P3. `scripts/deploy-dashboard.sh` hardcodes `TARGET=/var/www/orch.epiphanytechnologies.com` (+
      `chown hk:hk`) — a stale local-deploy target that fails on the central VM (which is **API-only**: nginx serves
      only `api.agent-orchestrator.odum-research.com → :8765`; the dashboard is a **separate origin**
      `agent-orchestrator.odum-research.com`, not served here). Parameterize the target via env/arg + document the real
      dashboard host/deploy path. Repo: agent-orchestrator. — agent-orchestrator@48089f7
- [x] ✅ [ORCHESTRATOR] P3. `server/orm.py` `AgentRow` docstring still reads "main, review, backup, etc." + "promote backup
      → main" — stale after the backup-role deprecation; update to main/review/custom. Repo: agent-orchestrator. — agent-orchestrator@1376070
- [x] ✅ [ORCHESTRATOR] P2. Review agent's `AgentRow.last_ping` isn't refreshed while its slot churns — a LIVE working
      review agent (owns a live `orch-slot-N` tmux, actively churning) shows `last_ping` hours stale and gets mislabeled
      `stale`/`offline` in the dashboard. **DONE** — three composing fixes, agent-orchestrator: (1)
      `touch_review_agent_heartbeat` refreshes the review heartbeat when its pane is `working` (gated so a frozen/hung
      review still falls through to stuck-detection); (2) **cadence-aware silence thresholds**
      (`health._agent_silence_thresholds`) scale offline/stale to the agent's `/loop` cadence (review polls every 15 min
      → offline 20 min / stale 25 min) so a healthy long-loop review is never false-dimmed; (3) reaper now **dedups
      superseded non-main records on a live session** (a watchdog respawn no longer strands the old review record).
      Verified live: one active review, `online=True` at 8-min silence. agent-orchestrator@c405e3c8 (+ earlier
      working-pane refresh) + 6 unit tests.

### Per-agent chat + Fleet / main-tab agent surfaces (operator design session 2026-06-19 — IMPLEMENT LATER)

> **DEFERRED (operator 2026-06-19: "append as todo, implement later").** Tagged `[OPERATOR]` so the backlog regen
> inserts them BLOCKED (never auto-dispatched) until the operator greenlights.
>
> **Problem:** messaging is ROLE-keyed (`AgentMessageRow.target_role` — _"addressed to a ROLE, not a specific agent"_),
> so every task-agent registers as role=`custom` and COLLAPSES into ONE `custom` chat + one currentHolder — you can't
> address one escalate agent out of ten (live 2026-06-19: 6 task-agents crammed in one `custom · 6` tab). **Model
> (operator-confirmed 2026-06-19):** per-agent chats + per-agent liveness, split by cardinality — **Fleet** (swarm, many
> concurrent): `escalate`, `conflict_resolver`, `recovery_audit`; **main-tab** (singleton, recurring):
> `plan_reconciler`, `plan_health`, `monitor` (+ `main`/`review`).

- [ ] [OPERATOR] P2. **Per-agent messaging (FOUNDATION — do first)** — add `target_agent_id` (nullable) to
      `AgentMessageRow` (+ `bootstrap.py` ALTER migration) alongside `target_role`; `/api/agents/{id}/poll` drains
      `target_agent_id == id` OR (`target_agent_id IS NULL` AND `target_role == role`) so role-broadcast still works;
      add per-agent `/api/agents/{id}/history` + `/api/agents/{id}/message` + agent-keyed `count_pending_to_agent`.
      Prereq for both surfaces below. Repo: agent-orchestrator (`server/orm.py`, `bootstrap.py`,
      `state_store/agents.py`, `routes/agents.py`).
- [ ] [OPERATOR] P2. **Per-kind `surface: fleet|tab` attribute** — registry/config per `AgentKind` (NOT
      lifecycle-derived: `escalate` + `recovery_audit` are both `one_shot` but route differently). Fleet = {escalate,
      conflict_resolver, recovery_audit}; tab = {plan_reconciler, plan_health, monitor}; main/review implicitly tab.
      Repo: agent-orchestrator (`server/` + dashboard `types.ts`).
- [ ] [OPERATOR] P2. **[UI] Main-tab chats for singleton kinds** — each `surface=tab` kind with a live agent gets its
      OWN agent-keyed chat tab beside main/review (no longer collapsed into `custom`), with the per-agent live dot
      (cadence-aware `online` — already shipped). pw/vitest gate (PLAN_FORMAT §9). Repo: agent-orchestrator (dashboard
      `App.tsx` tab bar + `RoleChat` → agent-keyed).
- [ ] [OPERATOR] P2. **[UI] Fleet swarm list** — render live swarm-kind agents as rows in the EXISTING Fleet view
      (operator 2026-06-19: "just another agent, no separate pane"): one row per agent (kind · task/PR · account · live
      dot · `tmux attach -t …`), click → that agent's per-agent chat drawer. A tab-per-agent can't scale to 10+
      concurrent escalates. pw/vitest gate. Repo: agent-orchestrator (dashboard Fleet view + per-agent chat component).
- [ ] [OPERATOR] P3. **[UI] Retire the collapsed `custom` role-chat tab** once per-agent chats + Fleet land (it is
      currently the only home for all task-agents; superseded by the per-kind surfaces). Repo: agent-orchestrator.

## Success criteria

- Every agent type (escalate/conflict-resolver/plan-health/plan-reconciler/monitor) is visible in the AO dashboard while
  running AND as past runs; activity feed is filterable + paginated + denoised; conditions collapse.

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — AgentTypesPanel + agent-retention + messaging path.

## Progress Log

### Plan B server (Wave 5, 2026-06-19, slot-2) — agent-orchestrator

The 3 SERVER items shipped (each QG-green + quickmerged to LDR); the 5 `[UI]` items follow (dashboard):

- **Retain finished agents** (P0) — agent-orchestrator@47c67fa: AgentRow `finished_at`/`exit_reason` + status `finished`
  (bootstrap migration); `DELETE /api/agents/{id}` now SOFT-deletes (`finish_agent` → status=finished + reason, row
  retained, tmux killed) instead of hard-delete; the reaper stamps finished_at/exit_reason on archival;
  `prune_finished_agents` (keep last N/kind, 7d) runs each AgentKeeper tick. Tests in test_reap_orphan_agents.py.
- **Filterable `GET /api/agents`** (P1) — agent-orchestrator@47c67fa:
  `list_agents(status/kind/lifecycle/include_finished/ limit)` (SQL WHERE/ORDER BY/LIMIT); default excludes terminal
  (live roster stays clean), include_finished/status shows past runs; AgentView gained finished_at/exit_reason.
- **Activity feed backend** (P1) — agent-orchestrator@b86c727:
  `list_activity(slot/event_type/event_types/before_id/limit)` filters in SQL BEFORE the limit (+ before_id cursor) +
  `activity_rollup` denoise (GROUP BY event_type[,slot] → counts); `/api/activity` gained types(CSV)/before_id + per-row
  `id`; new `/api/activity/rollup`. Tests in test_activity_feed.py.

The 5 `[UI]` items (AgentTypesPanel, activity frontend, failure-reason render, conditions collapse, message-delivery
chip) build on this API. **AO dashboard gate is Vitest + tsc --noEmit + build smoke, NOT playwright** (the dashboard has
no pw harness — evidence is a `.test.tsx` regression spec, per PLAN_FORMAT §9's vitest path).

### Plan B UI (Wave 6, 2026-06-19) — agent-orchestrator@85f737d

All 5 `[UI]` items + the oversight Phase-4 "agents feed renders every kind" verify — DONE in one cohesive commit (they
share types.ts/api.ts/App.tsx and only compile together). Gate: `tsc --noEmit` clean · `vitest run` **51/51** (17
pre-existing + 34 new) · `vite build` OK · prettier clean.

- **AgentTypesPanel** — `KINDS_ORDER` + `groupAgentsByKind` + `AgentTypesPanel` (reuses `AGENT_KIND_LABEL`); per-kind
  online count + show-finished toggle (`/api/agents?include_finished=true`, renders finished_at/exit_reason); mounted
  desktop + a new mobile "Agents" tab. Regression: `dashboard/src/agentTypes.test.ts`.
- **Activity feed** — server-driven filter tabs (category sets single-sourced as ALERT_TYPES/OPS_TYPES → `types=` CSV),
  "Load older" `before_id` cursor decoupled from the live poll, `collapseActivity` xN collapse+expand, live poll 50→25.
  Regression: `dashboard/src/activity.test.ts`.
- **Failure-reason render** — `isFailureEvent` + `extractFailureError` (details.error →
  last_error/reason/detail/message); inline expandable "why?" on failure rows. Regression:
  `dashboard/src/activity.test.ts`.
- **Conditions collapsible** — `sortConditionsForDisplay` (blocking-gates-first, OFF-first), COLLAPSED_COUNT=5, Show
  N/Collapse, count chip kept. Regression: `dashboard/src/agentTypes.test.ts`.
- **Message-delivery chip** — `deliveryChip(pending, hasHolder)` → "queued N" → "delivered" in RoleChat. Regression:
  `dashboard/src/agentTypes.test.ts`.

NOTE (provenance): 85f737d was direct-pushed from the sub-agent's git WORKTREE (the `scripts/quickmerge.sh` symlink
dangles in `.claude/worktrees/`, so quickmerge couldn't run — the dispatch's sanctioned fallback
`git push origin HEAD:live-defi-rollout` was used; the pre-push strict-quickmerge hook WARN-only allowed it). It carries
NO `Quickmerge:` trailer → the LDR→staging promote bot won't auto-arm that range, so a **one-time manual LDR→staging
promote** is needed (handled with the Wave 7 alerts commit, which has the same provenance). Code is green on LDR;
staging-PR v2 is the gate.

### Live validation + deploy (2026-06-19)

Deployed the server to the central VM (in-place from LDR + `systemctl restart`, mode=live) and ran a local live
dev-stack (`scripts/dev.sh`, port 8765/5173) for the operator UI review. The live test caught **two real bugs** + one
finding:

- **Bug #1 — main agent unclassified**: the keeper registered `main` without `agent_kind`, so `groupAgentsByKind` folded
  the orchestrator into "custom". Fixed: keeper sets `agent_kind=orchestrator`/`lifecycle=persistent`
  (agent-orchestrator@15180e79) + test; deployed; live main rows backfilled to `orchestrator`.
- **Bug #2 — reaper skipped stale records**: `reap_orphan_agents` queried only `status=='active'`, so a dead-but-stale
  agent (an old `main`) lingered in the dashboard forever. Fixed: reconcile **active+stale** + accurate
  `dead-main-session` reason (agent-orchestrator@7b5e838) + 2 regression tests; deployed. **Verified on the VM
  journal**: `AgentKeeper reaped 2 orphan agent record(s): superseded-main`.
- **Finding #3 — review heartbeat mislabel** (P2 follow-up above): a LIVE working review agent shows `stale` because its
  `AgentRow.last_ping` isn't refreshed while the slot churns; the reaper correctly KEEPS it (live session) — the badge
  is wrong, not the reaper. Not fixed here (never kill a working agent over a stale badge).

Also confirmed `ORCHESTRATOR_MODE=live` is the default in code + env files (`.env.example`@254f1ecc + local `.env.local`
pin); only the demo/e2e paths use mock.
