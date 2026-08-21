---
doc_type: issue
title: "pipeline_e2e_check.py's `_declared_violations()` sports full-exemption is stale (coarser check only, not a false-failure risk)"
summary: >-
  Migrated from `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md` (archived
  2026-08-18, all 3 todos done) per the plan-completion-and-archival-discipline "todos-not-prose" rule — that doc's
  2026-08-10 fix commit (`market-data-processing-service@f89112b`) left `_declared_violations()`'s sports
  full-exemption (`return []`) UNCHANGED and explicitly flagged it as a "KNOWN GAP" code comment + "candidate
  follow-up rather than shipping unverified," never converted to a tracked todo.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, pipeline-e2e-check, checker-template, declared-violations, tech-debt]
related:
  [
    /plans/archive/issues/mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-18"
author: plan_reconciler
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: "Migrated during archival of mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md, plan_reconciler dispatch agt-57336e, slot 31, 2026-08-18."
context_scope: [market-data-processing-service/scripts/pipeline_e2e_check.py]
---

# `_declared_violations()`'s sports full-exemption is stale — coarser check only, no false-failure risk

`scripts/pipeline_e2e_check.py`'s `_declared_violations()` still `return []`s unconditionally for the whole sports
asset_group (the §3B "canonical/declared" leg). The 2026-08-10 fix
(`market-data-processing-service@f89112b`, see the now-archived origin doc) scoped `_measured_root()` and
`_valid_timeframes()` correctly to what sports candle data_types actually produce, but left this SEPARATE
declared-shape check exempted — the origin doc's own note: "it is now technically stale (sports DOES claim the
standard declared template) but not a false-failure risk (just a coarser check)."

## Todos

- [ ] [CODE] P3. Tighten `_declared_violations()` so sports is checked against the standard declared template like
      every other asset_group (matching `_measured_root()`'s 2026-08-10 fix), instead of the blanket `return []`
      exemption. Done when: a from-scratch `pipeline_e2e_check.py --day <D> --asset-group SPORTS` run's §3B leg
      produces a real (not vacuously-empty) declared-violations verdict, and no new false failures appear across a
      spot-checked sample of days.
- **context-scout 2026-08-20**: populated/refreshed context_scope (1 entry)
- **na-eligibility-audit 2026-08-21**: RECLASSIFY (whole-doc) → `assigned_vm: planning` — sole open todo is a
  mechanical scope-tightening of `_declared_violations()` mirroring the already-shipped 2026-08-10
  `_measured_root()`/`_valid_timeframes()` fix, with an explicit machine-checkable done-when (a real, non-vacuous §3B
  verdict + no new false failures on a spot-checked sample). No design/judgment call. Conflict-check clear: grepped
  `plans/active/` for `_declared_violations()` and this file was the only hit — no existing `assigned_vm: planning`
  doc already claims this ground. `doc_type: issue`, so no companion finalize plan required per task_template.md's
  exemption.
