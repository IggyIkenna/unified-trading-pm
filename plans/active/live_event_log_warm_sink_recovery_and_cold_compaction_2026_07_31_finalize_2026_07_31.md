---
doc_type: plan
title: >-
  live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md -- machine-held via depends_on
  + gate_on_depends: true until all of that plan's todos are done. Verifies each of its own checkboxes carries real
  evidence (cited terraform/gcloud/build output, not a false-progress claim), re-checks its two
  deliberately-deferred/time-gated todos (the 1-week zero-message cross-check, the 48h subscription-persistence
  re-verify) to see whether they've since cleared, and archives the parent via the standard 6-step ritual once fully
  closed. Authored 2026-07-31 to close the finalize-plan-coverage gate the parent plan's own creation triggered
  (task_template.md §4 — every assigned_vm:planning plan needs a companion gated finalize plan).
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, live-trading, pubsub, warm-sink]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Filed to close the finalize-plan-coverage QG regression (scripts/quality_gates/check_finalize_plan_coverage.py)
  flagged against live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md, which shipped assigned_vm:
  planning without a companion gated finalize plan (task_template.md §4, operator ruling 2026-07-24).
---

# live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31 — finalize

## Todos

- [ ] [REVIEW] P2. Once every todo in `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` is `[x]`,
      re-verify each carries real evidence (the cited `terraform plan`/`apply` output,
      `gcloud pubsub subscriptions     list` count, `gcloud run jobs describe`/`executions list` output, epsilon=0
      determinism report path) rather than a false-progress claim — this plan is self-contained (not a batch extraction
      from other source docs), so there is no separate source-doc checkbox set to reconcile. Also re-check the plan's
      two deliberately-deferred/ time-gated todos at close-out time even if they were left open when the rest landed:
      the "P2. Cross-check whether any of the 52 combos still show ZERO messages a week later" todo and the "P3. 48h
      re-check the never-expire policy holds" todo — both have a real, checkable gate (elapsed time / a fresh `gcloud`
      count) that may have cleared since the rest of the plan shipped.
- [ ] [DOC] P3. Run the standard 6-step archival ritual on
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` once fully closed (including the above
      todo), plus the corpus-wide referrer-path fixup, then archive this finalize plan itself in the same pass (per
      task_template.md §4's "skip only for a plan that IS ITSELF already a finalize plan" — this doc has served its gate
      once its dependency archives).

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this plan's second
  todo runs.
