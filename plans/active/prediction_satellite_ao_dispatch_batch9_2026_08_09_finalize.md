---
doc_type: plan
title: Prediction satellite AO batch 9 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch9_2026_08_09.md — machine-held via depends_on +
  gate_on_depends: true until both of that plan's todos are done. Reconciles
  prediction_cross_venue_arb_and_coverage_2026_07_24.md's own checkboxes for the 2 items batch9 closes, re-checks the 3
  not-extracted items for whether any blocking condition has since cleared, then archives batch9 via the standard 6-step
  ritual.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
  ]
depends_on: [prediction_satellite_ao_dispatch_batch9_2026_08_09]
gate_on_depends: true
source: >-
  Targeted satellite-batch extraction (2026-08-09), per task_template.md §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 9 — finalize

**status: active — gated on batch9's 2 todos via `depends_on` + `gate_on_depends: true`.**

## Todos

- [ ] [REVIEW] P1. **Source-doc reconciliation**: confirm `prediction_cross_venue_arb_and_coverage_2026_07_24.md` shows
      both extracted items closed — the series-scoped Kalshi historical-backfill todo and the cqg batch
      re-classification `--apply` todo — either flipped `[x]` with the batch9 commit citation, or annotated with a
      pointer to it. Repo: unified-trading-pm. Done when: both items are closed-by-citation with no orphaned "still
      looks open" gap; also re-verify the doc's own line count is still under `check_line_caps.sh`'s hard cap after the
      edit (the source doc was measured at 999-1000 lines as of 2026-08-08 per a sibling batch's own line-cap extraction
      todo).
- [ ] [DOC] P2. **Re-check the 3 not-extracted items** (tarball-overwrite race, fixture-pairing team-name canonicaliser,
      and `prediction_consolidated_closeout_2026_07_18.md`'s own 0-todo status) for whether anything has changed — in
      particular whether `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s team-name-alias work has landed,
      which would let the fixture-pairing residual's citation be closed at the source. Repo: unified-trading-pm. Done
      when: an explicit still-held / cleared verdict is recorded for each.
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm todo 2's verdict is recorded, add
      the archived-banner cross-reference, run the post-phase codex audit, confirm no new CLAUDE.md contract is owed,
      update every corpus referrer, `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch9 is
      at its archived path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside batch9,
  `status: active`, gated via `depends_on` + `gate_on_depends: true`. No work started — waiting on batch9's dispatch
  - completion.
