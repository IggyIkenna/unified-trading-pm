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
status: open
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
assigned_vm: NA
execution_scope: local-only
assigned_role: frontend
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["deferred from ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md Track C todo 1, same session"]
drift_direction: advance-code
context_scope: [agent-orchestrator/dashboard/src/layout.tsx]
---

## Todos

- [ ] 1. [UI] P3. Add the same `DoneBadge` (✓/✗ pill, hover reason) to `SlotCards` that `SlotTable` already carries,
      reusing the existing `latestDoneOutcomeBySlot` helper — no new correlation logic needed, purely a second render
      site for data already computed. Done-when: a vitest/Playwright case analogous to the existing `SlotTable` badge
      test passes for the card layout too.

## Sequencing note

Low priority, cosmetic parity gap — `SlotTable` is the default `slotLayout` and already covers the operator's daily
view. Pick up opportunistically, not urgent.
