---
doc_type: issue
title:
  canned options B ("already done") and C ("not needed") on an [OPERATOR]-gated blocked card were still silent no-ops
  after operator_gated_blocked_answer_is_a_no_op_2026_07_30's fix — only option A and the reclassify/free-text path were
  actually wired
summary: >-
  Found while auditing why the operator kept seeing confusing/non-working operator-gated answer options (~20-25 open
  BLK-op-* cards, 2026-08-03). operator_gated_blocked_answer_is_a_no_op_2026_07_30 (archived, resolved) fixed option A's
  self-contradiction (D2) and built a real dispatch mechanism for the "Reclassify to role…" dropdown and free-text
  "Other" box (D3: submits `ruling_action="instruct"`/`"reclassify"`, which regen materializes into a real dispatchable
  `--ruling` task whose done_definition requires the plan edit). That archived doc's own D1-D5 decisions never touched
  canned options B/C, though — clicking either still submitted the plain canned text with no `ruling_action`, which
  `answer_blocked()` stores as an ordinary final answer and nothing materializes. Net effect, unchanged from the
  ORIGINAL pre-2026-07-30 bug for these two buttons specifically: clicking B or C hides the card from the pending queue
  while leaving the task permanently `status='blocked'`, undispatchable, and the plan checkbox untouched — B's own text
  ("flip the checkbox... prunes on the next regen") and C's own text ("remove this todo from the backlog") were false
  promises, byte-for-byte the same class of bug the archived doc's "Options B and C promise behaviour that does not
  exist" section already described, just never actually fixed for the canned-button path.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-queue, operator-gated, dashboard, dispatch, automation-gap]
related:
  [
    /plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md,
    /plans/active/issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
  ]
created: 2026-08-03
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Operator asked (interactive session, 2026-08-03) why so many operator-blocking questions stay open and what
    answering them actually does, after being shown a live sample of ~25 open BLK-op-* cards. Investigation traced the
    live answer-endpoint code and the archived operator_gated_blocked_answer_is_a_no_op_2026_07_30 doc, found B/C were
    excluded from that doc's D1-D5 fix, then fixed it in the same session per the operator's explicit follow-up
    instruction to fix known issues so answer options aren't confusing/non-working.",
  ]
resolved_by:
  'agent-orchestrator@5bfde668. Dashboard: BlockedCard''s canned-option submit button now calls a new
  `rulingForCannedOption(option, gated)` helper (dashboard/src/layout.tsx) that, for a gated row, submits B/C as
  `ruling_action="instruct"` with a canned instruction (verify-then-flip for B, flip-with-rationale for C) — byte-
  identical in shape to what typing free text already does, reusing the fully-tested D3 mechanism with zero backend
  risk. Option A is untouched (its own D2 auto-upgrade already works). Backend: reworded `OPTION_C_NOT_NEEDED`
  (server/operator_gated_options.py) — was "remove this todo from the backlog", which nothing ever did or will do (a
  dispatched worker edits the PLAN, never calls the backlog delete endpoint); now matches what actually happens,
  mirroring B''s already-accurate text.'
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
    agent-orchestrator/server/operator_gated_options.py,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/dashboard/src/layout.tsx,
  ]
---

# AO: operator-gated canned options B/C were still no-ops after the archived D1-D5 fix

## Why this was missed the first time

`operator_gated_blocked_answer_is_a_no_op_2026_07_30`'s own investigation section documented B and C as no-ops
identically to what this doc re-finds — but its "Decisions — RULED" section (D1-D5) only committed to fixing option A's
self-contradiction (D2) and building the reclassify/instruct dispatch mechanism for the dropdown + free-text box (D3).
Nothing in D1-D5 says "and also route B/C through D3" — an implicit assumption (never stated) that operators would stop
using the canned buttons in favor of free text, which the live evidence (an operator still clicking B/C on ~20-25 cards
a week later) shows didn't happen. The archived doc's own "Verified live" section only exercised the reclassify dropdown
and a free-text instruction, never the canned buttons — so the gap shipped invisibly.

## Fix

Reuse D3 verbatim rather than invent new server-side handling — see `resolved_by` above. No backend logic changed beyond
the button-copy correction; the endpoint (`POST /api/blocked/{blocked_id}/answer`) and regen materialization
(`_materialize_operator_ruling_tasks`) are exactly what free text and the reclassify dropdown already exercised and
D1-D5 already tested end-to-end live.

## Todos

- [x] ✅ [UI] P2. Route canned options B and C on an `[OPERATOR]`-gated blocked card through the same
      `ruling_action="instruct"` dispatch mechanism the free-text box already uses, instead of submitting a plain final
      answer nothing materializes (repo: agent-orchestrator). — agent-orchestrator@5bfde668. `rulingForCannedOption()`
      added to `dashboard/src/layout.tsx`; wired into the canned-option submit button. Tests:
      `dashboard/tests/e2e/reclassify-blocked.spec.ts` (new case + a third seeded fixture row in `seed_e2e_state.py`),
      `pw:L2 ✓` (`npx playwright test reclassify-blocked.spec.ts --project=chromium`, 4/4 passed, verified against the
      live e2e backend this session — log confirms `blocked_id=BLK-op-E2E-DISPATCHED-     canned-bc` routed through the
      same `slot-blocked-answered` path as the reclassify/instruct fixtures). Also reworded `OPTION_C_NOT_NEEDED`'s
      button text (was inaccurate even after this fix — see resolved_by). **Not verified against the live orchestrator
      VM** — this session had no write path to it (SSM reaches `localhost:8765` read-only by convention per
      `agent-orchestrator/scripts/orchestrator/check-ao-backlog-     status.sh`'s own header; a write via that channel
      would be a new, more invasive use of shared production access than anything currently sanctioned, so it was
      deliberately not attempted without the operator's own go-ahead). Confirm live once this reaches the deployed VM:
      click B or C on a real `BLK-op-*` card and verify a `--ruling` task appears in `/api/backlog` and the plan doc
      gets edited on completion, same bar `operator_gated_blocked_answer_is_a_no_op_2026_07_30`'s own `[REVIEW]` todo
      used.

## Progress Log

- **2026-08-03**: filed and resolved in the same session — see `source`/`resolved_by` above.
