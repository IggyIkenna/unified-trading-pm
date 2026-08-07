---
doc_type: issue
title: "SlotCards (non-default fleet layout) missing the Done ✓/✗ badge that SlotTable already shipped"
summary: >-
  `ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md`'s Track C shipped a per-slot Done ✓/✗ badge
  (`DoneBadge` + `latestDoneOutcomeBySlot`, `agent-orchestrator@e761cb1`) into `dashboard/src/layout.tsx`'s `SlotTable`
  — the default `slotLayout` view, matching what the operator's own screenshots showed at scoping time. `SlotCards` (the
  secondary, non-default card-grid layout) was explicitly left out of that scope rather than silently dropped — this
  issue exists so that deferral is a real trackable todo instead of a prose aside that would have evaporated when the
  parent plan archived (fully done, archived same day per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, done-badge, ui-parity, low-priority]
related: [/plans/archive/2026_08/ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md]
created: "2026-08-06"
author: unknown
priority: P3
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: ui_developer
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: agent-orchestrator@777bd3e
source: ["deferred from ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md Track C todo 1, same session"]
drift_direction: advance-code
context_scope: [agent-orchestrator/dashboard/src/layout.tsx, agent-orchestrator/dashboard/src/activity.test.ts]
---

## Todos

- [x] 1. ✅ [UI] P3. Add the same `DoneBadge` (✓/✗ pill, hover reason) to `SlotCards` that `SlotTable` already carries,
      reusing the existing `latestDoneOutcomeBySlot` helper — no new correlation logic needed, purely a second render
      site for data already computed. Done-when: a vitest/Playwright case analogous to the existing `SlotTable` badge
      test passes for the card layout too. — agent-orchestrator@777bd3e | `SlotCards` now takes
      `doneBySlot?: Map<number,     SlotDoneOutcome>` and renders `<DoneBadge outcome={doneBySlot?.get(s.slot_id)} />`
      in the card's bottom row; both call sites (`DesktopLayout` + `MobileTriage` in App.tsx) now compute/pass
      `doneBySlot` via the existing `latestDoneOutcomeBySlot` helper. Vitest: `layout.test.ts` — new "SlotCards
      DoneBadge — latestDoneOutcomeBySlot lookup for card layout" describe block (4 cases:
      pass/fail/no-event/independent-per-slot), all green (234/234 dashboard tests pass).
      `bash scripts/quality-gates.sh` PASSED (tsc clean, vitest 234/234, pytest 2600 passed/2 skipped, basedpyright 0
      errors).

## Sequencing note

Low priority, cosmetic parity gap — `SlotTable` is the default `slotLayout` and already covers the operator's daily
view. Pick up opportunistically, not urgent.

## Progress Log

- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): RECLASSIFY → `planning`. Bounded, deterministic-outcome
  UI parity task — reuses an existing helper (`latestDoneOutcomeBySlot`), a named second render site, and a stated
  done-when (a vitest/Playwright case analogous to the existing `SlotTable` badge test). Conflict-check clear: only
  other `SlotCards`/`DoneBadge` hit in the active corpus is the unrelated, already-shipped `ProviderBadge` feature
  (`deepseek_claude_blended_provider_routing_2026_07_28.md`, agent-orchestrator@12ae7c2) — no active claim on this exact
  fix. Also corrected `assigned_role` from `frontend` (not a real role — no `agents/frontend.md`) to `ui_developer` (the
  live registry's TS/React dashboard role) and `execution_scope` to `orchestrator-agent` to match the `planning` flip.
- **context-scout 2026-08-07**: populated context_scope (2 entries) — `layout.tsx` (where `DoneBadge`, `SlotCards`, and
  `latestDoneOutcomeBySlot` all live) plus `activity.test.ts` (the file carrying `latestDoneOutcomeBySlot`'s existing
  test coverage, the closest analog to the "existing SlotTable badge test" this doc's todo references).
- **ao_slotcards_done_badge_parity-001 2026-08-07 (slot 13)**: shipped. `SlotCards` gained a
  `doneBySlot?: Map<number, SlotDoneOutcome>` prop and now renders `<DoneBadge outcome={doneBySlot?.get(s.slot_id)} />`;
  both `App.tsx` call sites wired to pass it via the existing `latestDoneOutcomeBySlot` helper (`DesktopLayout` already
  computed it for `SlotTable` — just added it to the `SlotCards` call; `MobileTriage` didn't compute it at all — added
  the `useMemo`). New `layout.test.ts` describe block covers pass/fail/absent/multi-slot lookup.
  `agent-orchestrator@777bd3e` via quickmerge, QG green (tsc/vitest/pytest/basedpyright all clean). Only todo done,
  unlocked → archiving this doc in a follow-up commit per the completion-and-archival discipline.
