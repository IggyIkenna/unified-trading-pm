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

- [ ] [ORCHESTRATOR] P0. **Retain finished one-shot/scheduled agents** (load-bearing): stop hard-deleting on completion
      (`DELETE /api/agents/{id}` `routes/agents.py:703`); transition to a terminal status (`finished` +
      `finished_at`/`exit_reason` on AgentRow) + a retention prune (last N per kind / 7d). Without this "show past
      escalate/plan-health runs" is impossible. Repo: agent-orchestrator (server).
- [ ] [ORCHESTRATOR] P1. Filterable `GET /api/agents` — honor the dead-contract `status` param + add `kind`/`lifecycle`/
      `include_finished`/`limit`, pushed into `state_store.list_agents` (WHERE/ORDER BY). Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR][UI] P1. New `AgentTypesPanel` (one new tab, keyed on `agent_kind`, running+past) — `KINDS_ORDER` +
      reuse `RoleHolders`/`AGENT_KIND_LABEL`; per-kind online count + show-finished toggle; mount desktop + mobile. Keep
      role chat (`main/review/backup`) clean. Evidence: `— repo@sha | pw:L2 ✓ | regression: <spec>`. Repo:
      agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR] P1. Activity feed backend — push `slot`/`type`/category filters into SQL BEFORE the limit
      (`activity.py:86` / `routes/state.py:91-111`), add cursor pagination (`before_id`/offset + envelope), add a
      **denoise rollup** (`GROUP BY event_type[,slot] within window` → "×N in last 1h"; generalize
      `count_recent_activity`). The denoise is the "90% repeats" fix. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR][UI] P1. Activity feed frontend — "Load older"/cursor append (decouple from the live poll),
      server-driven filter tabs, collapse duplicate rows with ×N badge + expand, smaller live poll (~25). Repo:
      agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR][UI] P1. Render the per-event FAILURE REASON in the activity feed + escalations surface (moved from
      `orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 7). Today a `escalation_dispatch_failed` row
      shows only the bare event name; the reason IS already persisted (`escalation_queue.last_error` +
      `activity_log.details_json.error`) — it just isn't rendered, so the operator can't see WHY a dispatch failed
      without DB access (incident 2026-06-18: a slot-1 branch-quarantine starved dispatch for hours, invisible in the
      UI). Surface `details_json.error` inline (expandable) on failure-class activity rows, and `last_error` on the
      escalations view. Repo: agent-orchestrator (`server/` read path already has it + `dashboard/`).
- [ ] [ORCHESTRATOR][UI] P2. Conditions tab collapsible (frontend-only): `COLLAPSED_COUNT=5`, sort OFF+`gates_queued>0`
      first, "Show N more ▾"/"Collapse ▴", keep the count chip. Repo: agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR][UI] P2. Message-delivery VISIBILITY chip (operator decision 2026-06-19: **NO messaging-layer
      rewrite** — no adaptive-cadence / long-poll / SSE; the poll model stays). The only real gap is not knowing whether
      a sent message landed → surface the already-computed `count_pending_to_agent`/`pending_count` as a per-agent
      "queued → delivered" chip in the chat UI (data already served; frontend-only). Repo: agent-orchestrator
      (dashboard). NOTE: the **wake-on-message tmux nudge IS in scope** — but it lives in the unified-AgentKeeper work
      (`orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 6), because the default loops are now long
      (review 15 min, main up to 60 min) and the nudge is what makes a long idle loop responsive to a UI message. Live
      UI loop-interval control is the P3 nice-to-have there too.

## Success criteria

- Every agent type (escalate/conflict-resolver/plan-health/plan-reconciler/monitor) is visible in the AO dashboard while
  running AND as past runs; activity feed is filterable + paginated + denoised; conditions collapse.

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — AgentTypesPanel + agent-retention + messaging path.
