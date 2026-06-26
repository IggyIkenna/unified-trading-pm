---
doc_type: plan
title: AO dashboard fleet UI (tabs vs Fleet · ids · columns · full-width · full log · activity feed)
summary:
  UI half of agent legibility — main/review/plan_reconciler as chat tabs, everything else in a Fleet list with
  role/source/task/plan/ids columns, the dashboard widened to full width, the rate-limit string fixed, a full scrollable
  agent log, and a scrollable/paginated/denoised activity tab. Renders the fields the backend legibility plan exposes.
status: draft
nature: design
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
status_note:
  draft = dispatch-gated on ao_agent_legibility_backend (plan-level depends_on only gates archival, not dispatch) — flip
  to active when the backend lands
tags: [agent-orchestrator, fleet-ui, dashboard, activity-feed, ui]
related:
  [
    ao_agent_legibility_backend_2026_06_26.md,
    ../epics/orchestrator_master.md,
    ../../codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: harsh_pc
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

- [ ] [CODE][UI] P0. **Tabs**: render `main`, `review`, `plan_reconciler` as their own chat tabs; route all other kinds
      to **Fleet**; retire the collapsed `custom` role-chat tab. **Gate**: `pw:L2 ✓` — three tabs render, others in
      Fleet; regression spec.
- [ ] [CODE][UI] P0. Show **`agent_id` + `tmux_session` + `claude_session_id`** (+`rc_session_id`) on every agent
      row/tab (any state). **Gate**: `pw:L2 ✓` — a fleet row + a tab agent both display all ids; regression spec.
- [ ] [CODE][UI] P0. **Fleet columns**: `role` · `source` · `task` · `plan` · `last message` · `status` · ids — fed from
      the backend. `role` shows craft (backend-engineer/quant-dev/…) or kind (cicd/data_pipeline_failure/…). **Gate**:
      `pw:L2 ✓` — a CICD agent shows `role=cicd` + repo+PR, a worker shows role + plan + task; regression spec.
- [ ] [CODE][UI] P1. **Use the full viewport width** — kill the wasted side margins; widen the Slot/Fleet tables
      responsively so the new columns fit. **Gate**: `pw:L2 ✓` — layout fills the viewport with no table clipping at
      common widths; regression spec.
- [ ] [CODE][UI] P1. **Fix the "rate-limited until now from now" string** (`layout.tsx:2015`) — it misuses `fmtAgo`
      (past-only) on a future `rate_limited_until`. Use a future-relative formatter ("in Xh Ym") or the absolute time;
      drop the badge if already passed. **Gate**: `pw:L2 ✓` — a future rate-limit shows correct remaining time; a passed
      one shows no badge; regression spec.
- [ ] [CODE][UI] P0. **"Show Log"** renders the **complete, scrollable** agent log for ANY state (running/stale/killed)
      — today only the first boot-prompt chunk shows with no scroll. **Gate**: `pw:L2 ✓` — Show Log on a killed agent
      renders a scrollable log longer than the boot prompt; regression spec.
- [ ] [CODE][UI] P1. **Activity tab**: scrollable + paginated ("load older"), a datetime-range filter (default last 2h /
      max 100), and **default-hide the backend-noise events** behind a "show backend activity" toggle;
      operator-meaningful events show by default. **Gate**: `pw:L2 ✓` — default = last 2h ≤100 no noise; toggle reveals
      them; pagination loads older; regression spec.

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
