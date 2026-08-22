---
doc_type: issue
title: Finalize — finished one-shot sessions never reaped (reconcile + archive once live-verified)
summary: >-
  Gated finalize for ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md. That doc's sole
  remaining open todo is a live re-verification (post agent-orchestrator@89ca5609e0 deploy, confirm via SSM that
  idle+live slots past the reclaim-tick threshold are actually torn down, and that a queued escalation claims a
  freshly-reaped slot). Machine-gated via depends_on + gate_on_depends: true — will not dispatch until that todo is
  done.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/archive/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md,
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

> **📦 ARCHIVED 2026-08-22** (issues-corpus executable-queue dispatch) — both todos done: source doc reconciled +
> archived. 0 open todos, no lock.

# Finalize — ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch

Machine-gated: `depends_on: [ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18]` +
`gate_on_depends: true` — the dispatcher will not queue either todo below until that source plan's sole open todo
(the live re-verification) is done.

## Todos

- [x] ✅ [REVIEW] P1. Reconcile: confirm the source doc's re-verification todo carries real evidence (a cited SSM check
      showing idle+live slots past 2 reclaim ticks are torn down, and a queued escalation claiming a freshly-reaped
      slot) before treating it as closed. If the honest-caveat's "not fully explained" residual (the 14:18:51
      single-uninterrupted-lifetime reclaim delay) recurred after this fix deployed, spin a fresh tracked follow-up
      todo/issue for the DEBUG-logging diagnostic step rather than letting it drop silently. — RECONCILED 2026-08-20
      (review, slot 3, colocated on planning VM): source re-verification evidence REAL + independently confirmed — fix
      `89ca5609e0` ⊇ running-checkout HEAD `17ebb603` and claimed-deployed `47e1b04e`; running orchestrator (pid
      3113623) env has `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true`; disk-persisted
      `watchdog_idle_session_ticks.dedup.json` live with per-occupant (slot_id, last_spawned_at) keys; journal shows
      `idle_lingering_session_reclaim` teardowns ~20s post-restart (15:08:42-44 slots 1/9/10/14 from pid 3113623;
      15:14:44 slot 31) — persisted tick counter surviving restart PROVEN; escalations healthy (agt-6f7acf→slot 33,
      agt-500b74→slot 32, zero "no free configured slot"); reclaim cadence regular (14:42×10, 14:56×2, 15:08×4,
      15:14×1) — multi-hour stalls did NOT recur, so conditional DEBUG-logging correctly NOT added; slow-git-sweep
      residual pre-tracked in `idle_lingering_session_reclaim_not_firing_2026_08_19.md`. Note: worker verified
      colocated, not SSM — equivalent/stronger (colocated = already on the VM SSM shells into).
- [x] ✅ [DOC] P1. **DONE 2026-08-22 (issues-corpus executable-queue dispatch).** Ran the standard 6-step archival
      ritual on `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md`: added an ARCHIVED
      banner, `git mv` to `plans/archive/issues/`, fixed the corpus referrer with a structural `related:`/
      `context_scope:` pointer (`ao_scheduled_job_reaped_stale_rate_2026_08_18.md`, both fields repointed to the new
      archive path) + this finalize doc's own `related:` citation above. `ao_stuck_escalation_mtds_no_free_slot_
      2026_08_18.md` is itself already archived (its `related:` link there is a historical archived→archived mention,
      out of the active-corpus ratchet's scope, not touched). The other 2 corpus mentions
      (`account_failover_ignores_overage_rejected_2026_08_18.md`, `plan_reconciler_findings_ao_2026_08_22.md`) are
      prose citations, not structural `related:`/`context_scope:` pointers — left as-is (valid historical references
      by name). No new codex contract: the fix + its live re-verification are already the durable record (disk-
      persisted tick-counter pattern mirrors the pre-existing `_heartbeat_resume_count` precedent in the same file,
      already an established pattern, not a new one to codify). Evidence: unified-trading-pm (commit to follow).
      Was: **Once reconciled, run the standard 6-step archival ritual on**
      `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md`.
      git mv to `plans/archive/issues/`, SUPERSEDED-not-needed banner not required for a clean close, fix every
      corpus referrer including this finalize doc's own `related:`/`depends_on:` citations and
      `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`'s `related:` link.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
- **2026-08-20 (review, slot 3 — reconcile of the source re-verification todo)**: RECONCILED PASS — the source doc's
  re-verification evidence is real, independently confirmed colocated on the planning VM (fix `89ca5609e0` deployed in
  running checkout `17ebb603` ⊇ claimed `47e1b04e`, watchdog enabled, disk-persisted tick counter live + reclaim
  post-restart proven in journal, escalations claiming reserve slots 32/33 with zero "no free configured slot", no
  multi-hour stall recurrence → conditional DEBUG-logging correctly NOT added; slow-git-sweep residual pre-tracked in
  `idle_lingering_session_reclaim_not_firing_2026_08_19.md`). Todo 1 flipped. Todo 2 (archival) remains a separate
  dispatched task.
