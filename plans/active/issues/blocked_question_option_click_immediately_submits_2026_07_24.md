---
doc_type: issue
title: "Blocked-questions dashboard: clicking an option button submits it immediately, with no select-then-confirm step"
summary:
  "Operator-reported live bug (2026-07-24). BlockedCard's pre-defined option buttons
  (dashboard/src/layout.tsx::BlockedCard) call submit(opt) directly in onClick -- a single click both selects AND
  answers the blocked question, with no chance to review or change the choice first. The free-text path (type a custom
  answer, then press Enter or click Send) already has the correct two-step shape; the lettered option buttons do not.
  Fix: clicking an option should only SELECT it (visually highlighted, no network call); a separate Submit action
  commits the selected option via onAnswer."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, blocked-questions, ux, frontend]
related:
  [
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /plans/epics/orchestrator_master.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P0
parent_epic: orchestrator_master
source: "Operator-reported, live-experienced 2026-07-24 while answering blocked questions from the dashboard"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Blocked-question option buttons submit on click instead of select-then-submit

## What was found

`agent-orchestrator/dashboard/src/layout.tsx::BlockedCard` (lines ~1234-1315) renders each of a blocked question's
`options[]` as a button whose `onClick` calls `submit(opt)` directly:

```tsx
<button key={i} className={`opt ${rec ? "recommended" : ""}`} onClick={() => submit(opt)}>
```

`submit()` calls `onAnswer(q, answer, fromRole)` immediately, which POSTs the answer and removes the question from the
queue. There is no intermediate "selected but not yet sent" state for the lettered options — one click both picks AND
commits the answer, so a misclick or a change of mind after reading the options more carefully has no recovery short of
the operator noticing before the click lands.

By contrast, the free-text path directly below (the `<input>` + "Send" button) already does this correctly: typing does
not submit anything, and only pressing Enter or clicking the dedicated Send button calls `submit(text)`. The lettered
option buttons are the only path in this component that skips the confirm step.

## Desired behavior

- Clicking an option button **selects** it (visually highlighted — e.g. an active/selected CSS state) and does **not**
  call `onAnswer`.
- A separate, explicit **Submit** action (a button, enabled once an option is selected) is what actually calls
  `onAnswer` with the selected option.
- Re-clicking a different option before submitting changes the selection (no accumulation, no need to "unselect" first).
- The existing free-text input + Send button behavior is unchanged (it already has the correct two-step shape) —
  selecting a lettered option and typing custom text should be mutually exclusive in what gets submitted (whichever the
  operator actually confirms).

## Why this wasn't just fixed inline

Filed as a tracked issue (rather than a same-turn fix) so it carries proper before/after regression coverage — there is
currently zero test coverage of `BlockedCard`'s option-click behavior (`dashboard/src/layout.test.ts` has no
`Blocked`-prefixed case at all) — and so the fix's test can be gated on actually catching this exact bug (assert a
single option click does NOT call `onAnswer`, only the Submit action does).

## Open todos

**ACKED-INTO-PLAN 2026-07-24**: the live, actionable todo for this finding is Phase 7 of
[`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md#phase-7--operator-reported-dashboard-bug-2026-07-24)
(per direct operator instruction to track this in an active plan, not a standalone issue doc). This doc stays open as
the finding write-up; do not duplicate a second open todo here — track completion against the plan.

## Progress Log

- **2026-07-24**: Filed verbatim from a live operator report — clicking a blocked-question option in the dashboard
  answers it immediately instead of just selecting it. Related to, but distinct in scope from,
  [`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24`](blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
  (that doc covers the bigger, deliberately-deferred context-loss/dedup redesign; this is a small, immediately
  actionable interaction bug in the same component).
