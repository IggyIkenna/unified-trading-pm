---
doc_type: plan
title: >-
  anthropic_per_task_actual_spend_and_account_calibration_2026_08_10 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md — machine-held via depends_on
  + gate_on_depends: true until that plan's pricing, attribution, calibration, per-account-breakdown and repricing todos
  are all shipped. Reconciles the operator's originating symptom (blank $ column on the task-usage dashboard) against
  live evidence, confirms the measured subscription multiplier was recorded rather than assumed, then archives the
  source plan via the standard 6-step ritual. Authored 2026-08-10 per task_template.md's finalize-plan-coverage rule
  (every assigned_vm:planning doc needs a companion gated finalize plan).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, billing, cost-attribution, pricing, anthropic]
related:
  [
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [anthropic_per_task_actual_spend_and_account_calibration_2026_08_10]
gate_on_depends: true
source: >-
  Operator request 2026-08-10 (interactive session) — authored alongside the source plan to satisfy the
  finalize-plan-coverage gate that check_finalize_plan_coverage.py enforces on any newly-staged assigned_vm:planning
  plan.
assigned_role: review
effort: high
drift_direction: none
context_scope:
  [
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    agent-orchestrator/server/state_store/slots.py,
  ]
---

# anthropic_per_task_actual_spend_and_account_calibration_2026_08_10 — finalize

Gated closeout. Nothing here starts until the source plan's own todos are done — `gate_on_depends: true` holds it.

## Todos

- [ ] [REVIEW] P3. **Reconcile the originating symptom against live evidence before any archival.** The operator's
      report was a blank `$` column on the task-usage panel; confirm via the live endpoint that a non-null `spend_usd`
      now renders for every window under `provider=deepseek&role_group=planning` AND under an Anthropic-scoped filter,
      and that per-account totals sum to the provider total. **Done when**: both endpoint responses are pasted into this
      plan citing non-null spend in 1h/5h/24h/7d/lifetime, and the source plan's corresponding checkboxes are flipped
      `[x]` with that evidence. Repo: unified-trading-pm (checkboxes) + agent-orchestrator (the verification).
- [ ] [REVIEW] P3. **Confirm the subscription multiplier was MEASURED and recorded per account, not hardcoded.** The
      source plan exists because a first pass returned a 3x-107x spread that must not be averaged into one number.
      Verify the shipped code reads a stored per-account measurement carrying the window that produced it, and that an
      account with no measurement is flagged rather than silently priced at list. **Done when**: the per-account
      measured multipliers are recorded in the source plan's Progress Log with their windows, and a named test proves
      the unmeasured-account path is flagged. Repo: agent-orchestrator.
- [ ] [DOC] P3. **Archive** `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` via the standard
      6-step ritual (per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm todos 1-2 are
      recorded, add the archived-banner cross-reference, run the post-phase codex audit (the cost-attribution SSOT the
      source plan's last todo creates must exist and be authoritative rather than duplicated in the plan), update every
      corpus referrer, `git mv` to `plans/archive/2026_08/`. **Done when**: the source doc is at its archived path with
      every referrer updated and this finalize plan's own todos all `[x]`. Repo: unified-trading-pm.

## Progress Log

- 2026-08-10: drafted alongside the source plan, to satisfy the finalize-plan-coverage gate.
