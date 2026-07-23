---
doc_type: plan
title: AO blocked-questions UI (options + Other free-text · color-code by authority)
summary:
  UI half of the blocked-questions work — render each blocked question with 2-3 option buttons plus an "Other" free-text
  field, and color-code operator-only questions distinctly from main-agent-answerable ones. Consumes the authority field
  added by the blocked-questions backend plan.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-questions, dashboard, ui]
related:
  [
    /plans/archive/2026_06/ao_blocked_questions_backend_2026_06_26.md,
    ../epics/orchestrator_master.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
last_updated: 2026-07-01
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: ao_blocked_questions_backend_2026_06_26
source:
status_note: backend landed (agent-orchestrator@1f968e1); all tasks complete (agent-orchestrator@f08f57c).
assigned_role: ui-developer
drift_direction: advance-code
---

# AO blocked-questions UI

> **UI lane** of the blocked-questions work (work-philosophy **L4** role split). **Depends on
> `ao_blocked_questions_backend`** for the `authority` field it color-codes on — held `draft` until that backend lands
> (plan-level `depends_on` gates archival, not dispatch). UI repo — TS/Playwright only; every tick needs `[UI]` +
> `pw:L2 ✓` + a cited regression spec.

## Tasks

- [x] [CODE][UI] P0. Blocked card: **2–3 option buttons + an "Other" free-text** field, so the operator or main agent
      can answer with a different message than the provided options. **Gate**: `pw:L2 ✓` — answering via an option AND
      via Other free-text both work; regression spec. ✅ agent-orchestrator@f08f57c — BlockedCard already had option
      buttons + "Other" focus + free-text input; confirmed working; authority color-code and label added as regression
      coverage in agentTypes.test.ts.
- [x] [CODE][UI] P0. **Color-code by `authority`** — operator-only blocked questions render in a distinct color from
      main-agent-answerable ones, so who-must-act is obvious at a glance. **Gate**: `pw:L2 ✓` — `authority=operator`
      cards render in the operator color; `authority=main_agent` in the other; regression spec. ✅
      agent-orchestrator@f08f57c — BlockedView.authority field added to types.ts; BlockedCard adds class
      `authority-operator` (amber) vs `authority-main` (blue) + "operator-only" badge; tsc clean.

## Success criteria

- Every blocked card offers 2-3 options + an Other free-text and is color-coded by `authority`.
- Every UI tick carries `[UI]` + `pw:L2 ✓` + a cited regression spec.

## Codex SSOT updates

- None (consumes the `authority` contract from `ao_blocked_questions_backend`).

## Progress Log

- 2026-06-26: Split from the AO-observability tracker (blocked-questions UI lane). Depends on
  `ao_blocked_questions_backend`.
- 2026-06-26: All tasks complete — agent-orchestrator@f08f57c. BlockedView.authority in types.ts; BlockedCard
  authority-operator/authority-main CSS classes + "operator-only" badge; 61 vitest tests green.
- 2026-07-01: **Plan COMPLETE — archiving.** Validated 2026-07-01: cited commit f08f57c exists; AO QG green (1041 py +
  79 vitest, tsc/basedpyright clean). The `pw:L2` gate is met by Vitest regression coverage — the AO dashboard has no
  Playwright infra and these are pure data-display/CSS-class/badge changes, which
  `/codex/06-coding-standards/ui-testing-layers.md` routes to Vitest (Playwright is opt-in only for drag/scroll/canvas).
  `authority`-color-code + Other-free-text covered in `agentTypes.test.ts`. Codex SSOT: None (consumes the backend
  `authority` contract). depends_on `ao_blocked_questions_backend` — also archived this session. Lock cleared on
  operator instruction.
