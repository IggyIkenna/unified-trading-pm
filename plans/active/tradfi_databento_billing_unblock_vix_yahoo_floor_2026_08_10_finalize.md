---
doc_type: plan
title: TradFi Databento billing unblock + VIX scope + Yahoo floor fix — finalize
summary: >-
  Gated closeout for `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` — machine-held via `depends_on` +
  `gate_on_depends` until all 7 of that plan's todos are done. Re-verifies each done-claim against reality (not just the
  checkbox), then archives the parent plan once confirmed.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, databento, billing, vix, yahoo, discovery-floor, mvp-scope, finalize]
related:
  [
    /plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: review
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  Operator ruling (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored the same turn
  as its parent, 2026-08-10.
---

# TradFi Databento billing unblock + VIX scope + Yahoo floor fix — finalize

> **Machine-gated on `/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until all 7 of that plan's todos are `done`.

## Todos

- [ ] [REVIEW] P0. **Re-verify all 7 of the parent plan's done-claims against reality, not against their checkboxes** —
      for each doc-edit todo, `grep` the target file on `origin/live-defi-rollout` for the marker string the parent
      plan's todo specifies and confirm it's actually there (not just locally, not just staged); for the VIX-launch
      todo, confirm via a live manifest query that real `captured` rows landed. **Done when**: each of the 7 claims is
      independently confirmed against `origin/live-defi-rollout`/live infra, and any discrepancy is re-opened as a new
      tracked todo here with the discrepancy stated.
- [ ] [REVIEW] P1. **Check whether `tradfi_databento_account_billing_suspended_2026_08_09.md` is now fully closed** (its
      own follow-up todo — retagging the 4 downstream docs — done) — if so, run the standard 6-step archival ritual on
      it. Do not force an archival if the follow-up todo is still open. **Done when**: the doc's open-todo count is
      confirmed, and it's archived with evidence cited here if fully closed.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the parent plan itself, then regenerate the inventory** — banner
      `/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`, move to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/ `depends_on:`, then re-run the
      active-plan inventory generator. **Done when**: the parent plan is archived with a banner, the inventory
      regenerates cleanly, and `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`.
