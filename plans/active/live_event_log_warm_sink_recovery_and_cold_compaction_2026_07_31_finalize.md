---
doc_type: plan
title: Live event-log warm-sink recovery + cold-compaction — finalize (reconcile parent checkboxes + archive)
summary: >-
  Gated closeout for live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md, added per the
  finalize-plan-coverage gate (task_template.md §4 — every `assigned_vm: planning` plan needs a companion gated finalize
  plan so its checkboxes get reconciled and it goes through the archival ritual instead of sitting
  done-but-never-archived forever). Machine-held via `depends_on` + `gate_on_depends: true` until every todo on the
  parent is genuinely `[x]` or explicitly re-confirmed still-blocked.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [infra, pubsub, warm-sink, ao-dispatch, finalize, archival]
related: [/plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md]
created: "2026-07-31"
last_updated: "2026-08-06"
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: false
drift_direction: advance-code
depends_on: [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]
gate_on_depends: true
locked_by:
locked_since:
supersedes: live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize_2026_07_31
superseded_by:
source: >-
  check_finalize_plan_coverage.py regression (1 > baseline 0) surfaced while shipping unrelated doc updates for
  sports_odds_api_scattered_multiyear_gaps-004 (2026-07-31) — the parent plan is `assigned_vm: planning` with 10 total
  todos and no companion gated finalize plan.
context_scope:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/epics/batch_live_symmetry_master.md,
  ]
---

# Live event-log warm-sink recovery + cold-compaction — finalize

> **Machine-gated on `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue the todo below until every todo on that plan is done or
> explicitly re-confirmed still-blocked.

## Todos

- [ ] [REVIEW] P2. **Ported from the now-superseded
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize_2026_07_31.md` (operator ruling
      2026-08-06, de-racing two duplicate finalize plans).** Once every todo in
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` is `[x]`, re-verify each carries real
      evidence (the cited `terraform plan`/`apply` output, `gcloud pubsub subscriptions list` count,
      `gcloud run jobs describe`/`executions list` output, epsilon=0 determinism report path) rather than a
      false-progress claim — this plan is self-contained (not a batch extraction from other source docs), so there is no
      separate source-doc checkbox set to reconcile. Also re-check the plan's two deliberately-deferred/time-gated todos
      at close-out time even if they were left open when the rest landed: the "P2. Cross-check whether any of the 52
      combos still show ZERO messages a week later" todo and the "P3. 48h re-check the never-expire policy holds" todo —
      both have a real, checkable gate (elapsed time / a fresh `gcloud` count) that may have cleared since the rest of
      the plan shipped.
- [ ] [DOC] P2. **Reconcile + archive `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`.** Once
      every todo on the parent reads `[x]`: (1) verify no checkbox silently regressed (grep the doc for any remaining
      `- [ ]`); (2) for any todo still open, confirm whether it's genuinely blocked (credentials/operator
      decision/elapsed-time wait like the 48h re-check) vs. actually actionable — spin an explicit follow-up todo rather
      than leaving it silently stale; (3) only once every todo is genuinely `[x]` or explicitly re-confirmed
      still-blocked, run the standard 6-step archival ritual on the parent (migrate any DEFERRED → banner →
      codex-alignment check → update any referrer paths corpus-wide → clear lock). **Done when**: the parent doc's
      checkbox state matches reality and it is either archived (if fully resolved) or left `active` with an explicit
      dated note that the remaining items are still genuinely blocked.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries) -- genuinely code-free finalize gate;
  added the archival-discipline codex SSOT the todo's "standard 6-step archival ritual" phrase implies.
- **plan_reconciler agt-4fdce1 2026-08-06** (operator ruling, BLK-5eeacb63): this doc and
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize_2026_07_31.md` both gated on the same
  parent with `depends_on`+`gate_on_depends: true`, `status: active` — a real race once the parent's last 2 todos clear
  (each would run the identical archival on the same target). Operator ruled: keep THIS doc (cleaner filename), port the
  other's `[REVIEW]` evidence-verification todo here FIRST (done, above), then supersede the other.
  `check_finalize_plan_coverage.py`'s "no companion gated finalize plan exists" precondition — the actual root cause
  that generated a second finalize plan for a parent that already had one — filed separately, not blocking this de-race.
