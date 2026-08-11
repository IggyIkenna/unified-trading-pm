---
doc_type: plan
title:
  Render the blocked-question card's structured context collapsed by default, and stop leaking the no-worker slot
  sentinel as "#-1"
summary: >-
  The `[UI]` half of the blocked-question payload fix — gated behind its backend dependency rather than dispatched
  alongside it. Renders the new `BlockedRow.context` field as a `<details>` block collapsed by default so the headline
  question stays one line while the full structured context (both sides' verbatim quotes, file anchors, the worker's
  description, detection timestamps) is one click away, and replaces the raw `#{q.slot_id}` render with a named source
  chip so `NO_WORKER_SLOT_SENTINEL` never reaches the screen as "#-1". Both todos edit `dashboard/src/layout.tsx`, and
  the first cannot start until the `context` column exists — hence a separate plan with `gate_on_depends` rather than
  two more todos on the backend plan.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, blocked-questions, dashboard, ux, playwright]
related:
  [
    /plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /plans/archive/2026_08/issues/ao_model_main_agent_as_first_class_slot_2026_08_10.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: escalation_and_disaster_recovery_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: ui_developer
effort: max
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Split out of /plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md on 2026-08-10 when
  the operator flipped that plan to AO dispatch — partial parallelism is not expressible in one plan, and the UI work
  has a real backend dependency that must be machine-gated, not merely ordered.
depends_on: [blocked_question_payload_quality_and_condition_retirement_2026_08_10]
gate_on_depends: true
# Cross-repo (mode-2) two-commit bridge (2026-08-11, slot-16): flip-only commit
# must land BEFORE the git mv, and check_archive_candidates --only flags a flip-only
# commit on a 0-open-todo unlocked doc — this flag is the sanctioned exemption; it
# is dropped as part of the immediately-following archival commit.
archive_exempt: true
context_scope:
  [
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/styles.css,
    agent-orchestrator/dashboard/src/types.ts,
    agent-orchestrator/server/orm.py,
    /plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
---

# Blocked-question card — collapsed structured context + source chip

## Why this is a separate, gated plan

Both todos below edit the same file (`dashboard/src/layout.tsx`, the `BlockedCard` component), so they cannot run
concurrently — hence `sequential: true`. And the first one renders a `BlockedRow.context` field that does not exist yet:
it is created by the `[BACKEND] P1` todo on
[`/plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md`](/plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md).
`depends_on` + `gate_on_depends: true` makes that a machine-held gate rather than a hope.

The precedent for insisting on the gate is in this exact subject area. The sibling issue doc
[`/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`](/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
carries an ungated UI-todo-on-backend-todo pair, and its Progress Log records two `ui_developer` workers (slot-11 and
slot-27, both 2026-08-08) each being dispatched onto the UI todo while the backend todo was still `queued`, and each
burning a dispatch declining it as GATED. That doc's own todo text even flagged the risk ("sequence via
`sequential: true` if these are ever pulled into their own dispatched plan") — nobody set the field, and it happened
twice.

## Repo note — this is `agent-orchestrator`, not `deployment-ui`

The blocked-question queue is rendered ONLY by `agent-orchestrator/dashboard/src/layout.tsx` (`BlockedCard`).
`deployment-ui` contains no blocked-question code at all — verified 2026-08-10, its only `blocked` matches are
`promotion_blocked` PR counters in `Cockpit.tsx`. The sibling doc names `deployment-ui` for this same component and is
wrong; correcting it is tracked as todo D on the backend plan. Do not go looking for `BlockedCard` in `deployment-ui`.

## The design constraint being satisfied

Operator framing, 2026-08-10: more information on the card, "without making it impossible for a human to see the full
question on the page". The resolution is structure, not length — a one-line headline that always fits, with the volume
behind a disclosure widget that costs nothing to scan past in a queue of ~30 cards.

## Codex SSOTs

- `/codex/06-coding-standards/ui-testing-layers.md` — the `pw:L2` gate; no `[UI]` tick without a cited regression spec.

## Todos

- [x] ✅ [UI] P2. **Render `BlockedRow.context` as a `<details>` block collapsed by default** under `.question` in
      `BlockedCard` (`agent-orchestrator/dashboard/src/layout.tsx`) — headline question stays one line, expanding
      reveals both sides' verbatim quotes, their `file:line` anchors, the worker's `description`, and the first-detected
      / last-reconfirmed timestamps. **Done when**: collapsed-by-default and expand-to-full are both covered by a cited
      `pw:L2` Playwright spec, a row with `context: null` renders with no empty disclosure widget, the `<details>` block
      does not force horizontal page scroll at narrow widths, and `tsc` / `vitest` / `quality-gates.sh` are clean. Repo:
      agent-orchestrator.
- [x] ✅ [UI] P3. **Replace the raw `#{q.slot_id}` render with a named source chip** so `NO_WORKER_SLOT_SENTINEL`
      (`orm.py`, value `-1`) never reaches the screen as `#-1` — show `#N` for a real worker slot, and a named chip
      (`plan_health`, `operator-gated`) for synthetic rows, with a tooltip explaining there is no originating worker
      session because the one-shot that raised it freed its slot before the row outlived it. **Done when**: no code path
      can render `#-1`, a cited `pw:L2` spec covers a real-slot row and both synthetic variants, and `tsc` / `vitest` /
      `quality-gates.sh` are clean. Repo: agent-orchestrator.

## Progress Log

- **2026-08-10 (filed, slot-3 interactive)**: split out of the backend plan when the operator flipped that plan from
  `assigned_vm: NA` to `planning`. Kept as its own doc rather than two more todos on a `sequential: true` plan
  specifically so the backend dependency is a machine-held `gate_on_depends` gate — the sibling UX doc's Progress Log
  shows what an ungated pair costs here (two `ui_developer` dispatches burned on 2026-08-08). Verified while filing that
  `BlockedCard` lives in `agent-orchestrator/dashboard/`, not `deployment-ui`, contrary to what the sibling doc says. No
  `[OPERATOR]` todos — both items are bounded UI changes with machine-checkable done-whens, per the operator's "no
  operator-blocked parts" instruction the same day.
- **2026-08-11 (shipped, slot-16)**: P2 + P3 both shipped as `agent-orchestrator@4d2c9580ec`.
  - P2 — `BlockedCard` renders `BlockedRow.context` (now typed on `BlockedView` in `types.ts`) as a
    `<details class="context-details">` block collapsed by default under `.question`; expanding shows both sides'
    verbatim quotes, file:line anchors, the worker's description, and timestamps as a pretty-printed `<pre>`.
    `context: null` renders no disclosure widget. `word-break: break-word` + `overflow-x` containment prevent horizontal
    scroll at narrow widths.
  - P3 — `#{q.slot_id}` is replaced by a source-chip: real worker slots keep `#N` (`.slot-ref`), and synthetic rows
    (`slot_id === NO_WORKER_SLOT_SENTINEL`/`-1`) render a named chip — `plan_health` for `doc_drift:`-prefixed
    `blocked_id`s, `operator-gated` otherwise — each with a tooltip explaining there is no originating worker session.
    No code path can render `#-1`.
  - Regression: `dashboard/tests/e2e/blocked-context-rendering.spec.ts` — pw:L2 covers collapsed-by-default +
    expand-to-full, null-context renders no widget, no horizontal scroll at 420px viewport, real-slot `#N`, both
    synthetic source-chip variants, and an exhaustive no-`#-1` sweep across every card. Seed fixture `seed_e2e_state.py`
    gains a doc_drift row with structured context.
  - Gates: `tsc` clean, vitest 290/290, `quality-gates.sh` PASSED.
  - **2026-08-11 (archival bridge, slot-16)**: both todos done + unlocked → archival-eligible. `archive_exempt: true`
    set here as the mode-2 bridge so the flip-only commit can land at the still-active path (per
    `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "archive_exempt is the sanctioned bridge");
    the flag is dropped when the follow-up `git mv` to `plans/archive/2026_08/` lands.
