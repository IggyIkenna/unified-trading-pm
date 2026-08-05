---
doc_type: plan
title: >-
  resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md -- machine-held via depends_on +
  gate_on_depends: true until that plan's 4 phases (dual-write, MDPS migration, consumer audit/migration, alias removal)
  are done. Reconciles the source doc's own checkboxes/prose once its remaining todos ship (citing each landing commit),
  then archives it via the standard 6-step ritual once fully closed. Authored 2026-08-05 to close the
  finalize-plan-coverage gate the source plan's own creation triggered (task_template.md §4 — every assigned_vm:planning
  plan needs a companion gated finalize plan).
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, mtds, mdps, tradfi, data-correctness, ts_event]
related:
  [
    /plans/active/resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md,
    /plans/active/issues/mdps_tradfi_nasdaq_timestamp_overflow_candle_crash_2026_07_27.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05]
gate_on_depends: true
source: >-
  Authored 2026-08-05 to close the finalize-plan-coverage regression
  (scripts/quality_gates/check_finalize_plan_coverage.py) that
  resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md's own creation triggered — that plan carries 4 open
  Phase 1/3/4 todos (well past the single-todo carve-out) with no gated finalize companion.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05 — finalize

## Todos

- [ ] [REVIEW] P3. **Reconcile `resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md`'s checkboxes** against
      whatever shipped — flip each remaining `- [ ]` (Phase 1 dual-write, Phase 3 calculator migration + grep audit,
      Phase 4 alias removal) to `- [x]` citing the landing commit(s), confirm no residual consumer was missed by the
      Phase 3 blast-radius survey, then run the standard 6-step archival ritual (migrate DEFERRED items, banner,
      codex-alignment check, update any CLAUDE.md/codex pointer on a new contract, update every referrer's path
      corpus-wide, clear lock) once fully closed. Phase 4 (alias removal) is explicitly gated ≥2 weeks after Phase 1
      lands per the source plan — do not force-archive before Phase 4's own gate condition is met. If real work remains
      after the AO-dispatched todos land, leave the source plan active and note what's still open here instead.
