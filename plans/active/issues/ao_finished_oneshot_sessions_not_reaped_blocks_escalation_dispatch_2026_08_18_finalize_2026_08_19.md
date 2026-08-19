---
doc_type: issue
title: Finalize — finished one-shot sessions never reaped (reconcile + archive once live-verified)
summary: >-
  Gated finalize for ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md. That doc's sole
  remaining open todo is a live re-verification (post agent-orchestrator@89ca5609e0 deploy, confirm via SSM that
  idle+live slots past the reclaim-tick threshold are actually torn down, and that a queued escalation claims a
  freshly-reaped slot). Machine-gated via depends_on + gate_on_depends: true — will not dispatch until that todo is
  done.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
author: na_eligibility_auditor
source: >-
  Authored alongside ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md's RECLASSIFY per the mandatory finalize-twin rule (task_template.md
  Section 4) -- na-eligibility-audit 2026-08-19, ao tranche.
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: none
sequential: true
depends_on: [ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18]
gate_on_depends: true
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
  ]
---

# Finalize — ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch

Machine-gated: `depends_on: [ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18]` +
`gate_on_depends: true` — the dispatcher will not queue either todo below until that source plan's sole open todo
(the live re-verification) is done.

## Todos

- [ ] [REVIEW] P1. Reconcile: confirm the source doc's re-verification todo carries real evidence (a cited SSM check
      showing idle+live slots past 2 reclaim ticks are torn down, and a queued escalation claiming a freshly-reaped
      slot) before treating it as closed. If the honest-caveat's "not fully explained" residual (the 14:18:51
      single-uninterrupted-lifetime reclaim delay) recurred after this fix deployed, spin a fresh tracked follow-up
      todo/issue for the DEBUG-logging diagnostic step rather than letting it drop silently.
- [ ] [DOC] P1. Once reconciled, run the standard 6-step archival ritual on
      `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md` (git mv to
      `plans/archive/issues/`, SUPERSEDED-not-needed banner not required for a clean close, fix every corpus referrer
      including this finalize doc's own `related:`/`depends_on:` citations and
      `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`'s `related:` link).

## Progress Log
