---
doc_type: issue
title: >-
  Recorded reasons for the three currently-paused scheduled-dispatch modes (ag_closeout,
  cefi_mtds_smoke, ci_reconcile) — operator-confirmed 2026-08-18, so a future watchdog run
  doesn't re-flag them as a forgotten pause
summary: >-
  ao-watchdog's first live run (2026-08-18) found `GET /api/scheduled-dispatch/status` reporting
  three modes paused (ag_closeout, cefi_mtds_smoke, ci_reconcile), responsible for 316 of the
  fleet's `no_capacity` dispatch attempts over the trailing 72h. `scheduled_dispatch_pause.py`
  stores only a bare set of mode names (no `paused_at`/`reason` field exists in the mechanism
  itself) — exactly the structural gap that let 6 modes sit forgotten-paused from an unrelated
  2026-08-11 investigation for days, per `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`.
  Operator confirmed live (2026-08-18) that all three are currently intentional, not forgotten,
  and gave the reason for each — recorded below with today's date since the mechanism itself
  can't say when the pause actually started.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-watchdog, scheduled-dispatch, operator-decision]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /cursor-configs/skills/ao-watchdog/SKILL.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog run, 2026-08-18 (this session) — GET /api/scheduled-dispatch/status
  surfaced 3 paused modes with no reason/timestamp stored; reasons given live by the operator in
  chat when asked whether to resume them.
resolved_by:
locked_by:
depends_on: []
---

# Recorded reasons for the three currently-paused scheduled-dispatch modes

## Current state (confirmed live 2026-08-18 via `GET /api/scheduled-dispatch/status`)

```
paused: ["ag_closeout", "cefi_mtds_smoke", "ci_reconcile"]
```

`scheduled_dispatch_pause.py` stores this as a bare `set[str]` — no timestamp, no reason. The
three reasons below come from the operator directly (2026-08-18 chat), not from any system field.

**Update, same day**: operator explicitly authorized resuming `ci_reconcile` only (`ag_closeout`
and `cefi_mtds_smoke` stay paused — the smoke test in particular for VM-capacity reasons). Resumed
via `POST /api/scheduled-dispatch/ci_reconcile/resume` and verified end-to-end: a triggered dispatch
returned `status: "queued"` (the modern AutoSpawn-drain queue path, not the old "paused by operator"
503) — the pause is genuinely lifted, not just API-flipped. Current paused set as of this update:
`["ag_closeout", "cefi_mtds_smoke"]`. See the `ci_reconcile` section below for the resume rationale.

## `cefi_mtds_smoke` — paused: cost/orphan-resource risk, pending deployment-service registration

The smoke test spins up real cloud resources and currently consumes too much of them. Before
re-enabling, the resources it launches need to be properly registered as deployment-service-
managed services so they're actually monitored and killed if the spawning agent dies mid-run —
today, an agent death after spawn risks an orphaned, unmonitored, unbilled-for resource running
indefinitely. This is the same failure class `/vm-preemption-billing-waste-audit` and the
resource-watchdog subsystem exist to catch generally; this specific test's resources aren't yet
wired into that net.

**Unblocks when**: the smoke test's spawned resources are registered as deployment-service-managed
(so kill-on-orphan applies to them too).

## `ag_closeout` — paused: heavy concurrent manual reconciliation work in flight

A lot of time-reconciliation work (`ag-closeout-audit` scope) is happening manually/actively right
now across asset groups. Running the automated `ag_closeout_auditor` concurrently would step on
that in-flight work rather than complement it.

**Unblocks when**: the current manual reconciliation wave settles — operator judgment call, not a
fixed date.

## `ci_reconcile` — RESUMED same day (was: intentionally manual, pending confidence in escalation routing)

Originally paused so CI reconciliation ran manually as a daily task rather than via the automated
timer, until there was more confidence in how `/ci-reconcile` findings route into escalation tasks.
Later the same day (2026-08-18), the operator judged that gate satisfied and explicitly authorized
resuming the timer — a considered decision, not a temporary test-then-repause. Resumed via
`POST /api/scheduled-dispatch/ci_reconcile/resume`; a triggered dispatch immediately after came back
`status: "queued"` (queue_key `ci_reconciler:-:2026-08-18`), confirming the timer now hits the
normal capacity/queue path instead of the "is paused by operator" 503.

## Repeated `no_capacity` dashboard rows while paused (separate gap, found 2026-08-18)

Distinct from the missing `reason`/`paused_at` field above: while a mode is paused, its timer keeps
firing on its normal cadence (`ci_reconciler` every 15min, `ag_closeout_auditor` every 2h), each
tick 503s on `is_paused()` (`plan_health.py:662-666`, checked before any slot/capacity logic runs),
and `record_scheduled_job_run()` (`state_store/scheduled_jobs.py:38-70`) **unconditionally inserts a
brand-new row** for every one of those attempts — no dedup key, no upsert. Result: one dashboard row
per tick, accumulating indefinitely for as long as the mode stays paused (observed: `ci_reconciler`
logged ~10+ rows over 2h while paused). The rows are individually correct (each really was a
paused-mode 503) but the aggregate reads as fleet-capacity spam rather than a static, known state.

The fix pattern already exists in the same file and just isn't applied to this path:
`queue_scheduled_job()` (`state_store/scheduled_jobs.py:107-145`) upserts by key
`(job, tranche, day)` instead of inserting duplicates. Route the paused-mode outcome through an
equivalent upsert (keyed by `(job, tranche)`, no `day` component needed since a pause can span many
days) instead of `record_scheduled_job_run`'s always-insert path, so the dashboard shows one row
per paused job that updates its "last checked" timestamp in place.

No catch-up/queue-drain logic is needed on resume — confirmed both `ci_reconciler` and
`ag_closeout_auditor` are periodic rechecks (not one-shot daily crons); a paused tick never marks
itself "done," so the next natural tick after unpause dispatches normally with nothing to drain.

## Follow-up

- [ ] [SCRIPT] P2. Add a `reason` + `paused_at` field to `scheduled_dispatch_pause.py`'s storage
      (currently a bare `set[str]` via `dedup_state.load_seen_keys`/`save_seen_keys` — needs a
      small schema change to a `dict[str, {reason, paused_at}]` or equivalent), and surface both
      on `GET /api/scheduled-dispatch/status` and the dashboard's pause UI. This is the structural
      fix for the gap this doc exists to paper over by hand — without it, every future watchdog
      run (or operator) has to re-ask "why is this paused" from scratch, exactly as happened here
      and in the 2026-08-11 incident. (repo: agent-orchestrator)
- [x] [SCRIPT] P2. Stop `record_scheduled_job_run()` from inserting a fresh row on every tick for a
      known-paused mode's 503 — route it through an upsert keyed by `(job, tranche)` (mirroring
      `queue_scheduled_job`'s dedup-by-key pattern in the same file) so the Scheduled Jobs dashboard
      shows one persistent, in-place-updating row per paused job instead of one new row per ~15-30min
      tick. No catch-up/drain logic needed on resume (see section above — both affected jobs are
      periodic rechecks, not one-shot crons). — agent-orchestrator@6bfd8eef9f (7 new tests, full
      quality-gates.sh green). Also shipped a one-shot `POST /api/scheduled-jobs/purge-no-capacity`
      admin endpoint (status=no_capacity ONLY, never touches dispatched/queued/quarantined/timeout/
      error rows) to retroactively clear rows inserted before this fix; verified live 2026-08-18 —
      deploy confirmed via ao-self-pull (405 on the new route = live), then invoked once after the
      `ci_reconcile` resume below verified working: **purged 1301 historical no_capacity rows**.
- [x] [REVIEW] P3. Once `ci_reconcile`'s manual-daily-task period produces enough signal on
      escalation-routing reliability, resume the timer and archive this doc's `ci_reconcile`
      section (or the whole doc, if all three have resolved by then). (repo: NA — operator
      judgment call on timing) — operator judged it satisfied 2026-08-18 and authorized the resume
      (see updated `ci_reconcile` section above); `ag_closeout`/`cefi_mtds_smoke` remain paused,
      untouched. Not archiving the doc/section since `ag_closeout`/`cefi_mtds_smoke` and follow-up 1
      are still open.
