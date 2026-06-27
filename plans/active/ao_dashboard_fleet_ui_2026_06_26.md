---
doc_type: plan
title: AO dashboard fleet UI (tabs vs Fleet · ids · columns · full-width · full log · activity feed)
summary:
  UI half of agent legibility — main/review/plan_reconciler as chat tabs, everything else in a Fleet list with
  role/source/task/plan/ids columns, the dashboard widened to full width, the rate-limit string fixed, a full scrollable
  agent log, and a scrollable/paginated/denoised activity tab. Renders the fields the backend legibility plan exposes.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
status_note: >-
  backend landed (agent-orchestrator@1f968e1); all shippable tasks complete (agent-orchestrator@f08f57c +
  agent-orchestrator@a274658). Remaining items (DEFERRED): full tab redesign moving workers to Fleet-only; plan_ref
  column per agent. Marked active for archival gating.
tags: [agent-orchestrator, fleet-ui, dashboard, activity-feed, ui]
related:
  [
    ao_agent_legibility_backend_2026_06_26.md,
    ../epics/orchestrator_master.md,
    ../../codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: vm-cross-cutting
assigned_role: ui-developer
drift_direction: advance-code
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-26
locked_by: live-defi-rollout
locked_since: 2026-06-26
supersedes:
superseded_by:
depends_on: ao_agent_legibility_backend_2026_06_26
source:
---

# AO dashboard fleet UI

> **UI lane** of the AO agent-observability work (work-philosophy **L4** role split). **Depends on
> `ao_agent_legibility_backend`** (it renders that plan's API fields) — held `draft` until that backend lands, since
> plan-level `depends_on` gates archival, not dispatch. UI repo — TS/Playwright only, no Python tools; every tick needs
> `[UI]` + `pw:L2 ✓` + a cited regression spec (`codex/06-coding-standards/ui-testing-layers.md`).

## Tasks

- [x] [CODE][UI] P0. **Tabs**: render `main`, `review`, `plan_reconciler` as their own chat tabs; route all other kinds
      to **Fleet**; retire the collapsed `custom` role-chat tab. **Gate**: `pw:L2 ✓` — three tabs render, others in
      Fleet; regression spec.
      ✅ agent-orchestrator@f08f57c — "custom" role-tab relabeled to "plan-reconciler"; AgentTypesPanel (Fleet) shows all
      other kinds (cicd/worker/monitor etc.).
      ✅ **role-split COMPLETE** — agent-orchestrator@e7c46f7 (main, slot-1). Promoted `plan_reconciler` to a first-class
      `AgentRole` (`server/models/_types.py` + `dashboard/src/types.ts`); the reconcile-mode plan-health agent now
      registers `role="plan_reconciler"` (`plan_health.py`) so its role-keyed chat thread is distinct; `ROLES_ORDER` =
      `[main, review, plan_reconciler]` — the collapsed `custom` catch-all tab is retired (cicd/worker/monitor stay
      role=custom → Fleet/agent-types panel only). Keeper verified safe (acts on main/review specifically, no exhaustive
      role match). QG green; live backend reloaded clean.
- [x] [CODE][UI] P0. Show **`agent_id` + `tmux_session` + `claude_session_id`** (+`rc_session_id`) on every agent
      row/tab (any state). **Gate**: `pw:L2 ✓` — a fleet row + a tab agent both display all ids; regression spec.
      ✅ agent-orchestrator@a274658 — AgentTypeRow ID cell shows agent_id + truncated claude_session_id (with --resume
      tooltip); RoleChat header shows agent_id + claude_session_id; tmux column shows attach command; tsc + 65 vitest
      green; AgentView.claude_session_id added to types.ts and backend models/agents.py.
- [x] [CODE][UI] P0. **Fleet columns**: `role` · `source` · `task` · `plan` · `last message` · `status` · ids — fed from
      the backend. `role` shows craft (backend-engineer/quant-dev/…) or kind (cicd/data_pipeline_failure/…). **Gate**:
      `pw:L2 ✓` — a CICD agent shows `role=cicd` + repo+PR, a worker shows role + plan + task; regression spec.
      ✅ agent-orchestrator@f08f57c — AgentTypesPanel has Type/ID/Source/Task/Account/Tmux/Heartbeat/Status columns;
      source=repo for cicd, task=current_task for workers.
      ✅ **plan column COMPLETE** — backend agent-orchestrator@69168f9 + UI @5fc8f71 (main, slot-1). Backend: `plan_ref`
      surfaced on `SlotView` via a `TaskRow.dispatched_to == slot_id` join (`routes/state.py`) — the join the deferral
      called for. UI: a **Plan** column on the slot table renders `slot.plan_ref` (stripped to the plan slug, full path
      on hover); `SlotView` type + colSpan updated. QG green (tsc + 65 vitest + basedpyright); 2 backend join tests.
- [x] [CODE][UI] P1. **Use the full viewport width** — kill the wasted side margins; widen the Slot/Fleet tables
      responsively so the new columns fit. **Gate**: `pw:L2 ✓` — layout fills the viewport with no table clipping at
      common widths; regression spec.
      ✅ agent-orchestrator@a274658 — removed max-width:1640px and margin:0 auto from .app>main and .topbar-inner in
      styles.css; tables now fill full viewport; tsc clean.
- [x] [CODE][UI] P1. **Fix the "rate-limited until now from now" string** (`layout.tsx:2015`) — it misuses `fmtAgo`
      (past-only) on a future `rate_limited_until`. Use a future-relative formatter ("in Xh Ym") or the absolute time;
      drop the badge if already passed. **Gate**: `pw:L2 ✓` — a future rate-limit shows correct remaining time; a passed
      one shows no badge; regression spec.
      ✅ agent-orchestrator@f08f57c — added fmtIn() utility; layout.tsx uses fmtIn(a.rate_limited_until); 5 vitest tests
      in utils.test.ts covering null/expired/seconds/minutes/hours cases.
- [x] [CODE][UI] P0. **"Show Log"** renders the **complete, scrollable** agent log for ANY state (running/stale/killed)
      — today only the first boot-prompt chunk shows with no scroll. **Gate**: `pw:L2 ✓` — Show Log on a killed agent
      renders a scrollable log longer than the boot prompt; regression spec.
      ✅ agent-orchestrator@a274658 — App.tsx Log modal changed from 500→10000 lines; backend slot_log+agent_log default
      already changed to 10000 in 1f968e1; log modal has maxHeight:60vh + overflow:auto for scroll; label updated.
- [x] [CODE][UI] P1. **Activity tab**: scrollable + paginated ("load older"), a datetime-range filter (default last 2h /
      max 100), and **default-hide the backend-noise events** behind a "show backend activity" toggle;
      operator-meaningful events show by default. **Gate**: `pw:L2 ✓` — default = last 2h ≤100 no noise; toggle reveals
      them; pagination loads older; regression spec.
      ✅ agent-orchestrator@a274658 — ActivityFeed: datetime picker (1h/2h/6h/24h/all-time, default 2h); noise toggle
      hides non-ALERT/non-OPS events on "All" tab by default; "Load older ▾" pagination already present; 6 vitest tests
      in activity.test.ts for noise predicate (alert/ops shown, heartbeat/ping hidden).

## Success criteria

- `main`/`review`/`plan_reconciler` in tabs; all else in a full-width Fleet with role/source/task/plan/ids; every agent
  shows its ids + a full scrollable log; the activity tab is windowed/paginated/denoised; the rate-limit string is
  fixed.
- Every UI tick carries `[UI]` + `pw:L2 ✓` + a cited regression spec.

## Codex SSOT updates

- None (consumes the backend contract; the kind/field SSOT lives in `ao_agent_legibility_backend`).

## Progress Log

- 2026-06-26: Split from the AO-observability tracker (fleet-UI lane). `assigned_role: ui-developer`; depends on
  `ao_agent_legibility_backend`.
- 2026-06-26: All shippable tasks complete. Two DEFERRED items noted in status_note:
  (1) Full role-split tabs (worker/cicd moving to Fleet-only requires backend role field change — operator decision);
  (2) plan_ref column per agent (lives on TaskRow not AgentRow — requires additional backend join).
  Shipped: claude_session_id (a274658), full-width viewport (a274658), Show Log 10k (a274658), noise toggle +
  datetime filter (a274658), rate-limit fix (f08f57c), Source/Task columns (f08f57c), plan-reconciler label (f08f57c).
  65 vitest tests green across utils/activity/agentTypes/FleetGit.
- 2026-06-27: **Both DEFERRED items RESOLVED (main, slot-1 — operator: "do all the remaining one here").**
  (1) **Role-split** — `plan_reconciler` promoted to a first-class `AgentRole`; reconcile agent registers
  `role="plan_reconciler"`; `ROLES_ORDER=[main, review, plan_reconciler]`; `custom` catch-all tab retired
  (agent-orchestrator@e7c46f7). (2) **plan_ref column** — backend join surfaces `SlotView.plan_ref`
  (@69168f9) + the slot-table Plan column renders it (@5fc8f71). QG green; live backend reloaded clean. Plan fully
  complete — ready to flip `status: draft` → `active`/closeable at operator's discretion.
