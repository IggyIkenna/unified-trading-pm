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
# reclassified NA -> planning 2026-08-19 (na-eligibility-audit, ao tranche) — conflict-check CLEAR
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog run, 2026-08-18 (this session) — GET /api/scheduled-dispatch/status
  surfaced 3 paused modes with no reason/timestamp stored; reasons given live by the operator in
  chat when asked whether to resume them.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/scheduled_dispatch_pause.py,
    agent-orchestrator/server/state_store/scheduled_jobs.py,
    agent-orchestrator/server/plan_health.py,
    cursor-configs/skills/ao-watchdog/SKILL.md,
    /plans/active/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18_finalize_2026_08_19.md,
  ]
---

# Recorded reasons for the three currently-paused scheduled-dispatch modes

## Current state — re-checked against the LIVE registry 2026-08-20

```
paused: ["ag_closeout", "cefi_mtds_smoke", "ci_reconcile", "na_eligibility", "reconcile", "report"]
```

**Live read 2026-08-20 (slot 6, task ao_scheduled_dispatch_pause_reasons-7434f3d0c871)**: this section was
originally written 2026-08-18 from `GET /api/scheduled-dispatch/status` (3 modes), then updated same-day after
the `ci_reconcile` resume (2 modes). Re-checked today against the persisted registry the running server loads —
`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/scheduled_dispatch_paused_modes.dedup.json`
(mtime 2026-08-19 22:56) — the current paused set is **6 modes**: `ag_closeout`, `cefi_mtds_smoke`,
`ci_reconcile`, `na_eligibility`, `reconcile`, `report`. `ao_watchdog` is NOT paused (resumed 2026-08-19 per the
Todos section). `ci_reconcile` is paused again (it was resumed 2026-08-18, then re-paused — see the
`ci_reconcile` section + MEASURED UPDATE below). This live re-check is exactly the maintenance this todo
exists to force: a hand-maintained list went stale within 24h (3 → 7 → 6), which is the measured argument for
the open `paused_at`/`reason` schema-fix todo, not just the theoretical one.

`scheduled_dispatch_pause.py` stores this as a bare `set[str]` — no timestamp, no reason. The
reasons below come from the operator directly, not from any system field.

**Original same-day update (2026-08-18, historical)**: operator explicitly authorized resuming `ci_reconcile`
only (`ag_closeout` and `cefi_mtds_smoke` stayed paused — the smoke test in particular for VM-capacity reasons).
Resumed via `POST /api/scheduled-dispatch/ci_reconcile/resume` and verified end-to-end: a triggered dispatch
returned `status: "queued"` (the modern AutoSpawn-drain queue path, not the old "paused by operator" 503) — the
pause was genuinely lifted at that time. `ci_reconcile` has since been re-paused (see the MEASURED UPDATE
2026-08-19 section below).

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

- [x] [SCRIPT] P2. Add a `reason` + `paused_at` field to `scheduled_dispatch_pause.py`'s storage
      — agent-orchestrator@4bff9c1532 + evidence: quality-gates.sh (5286 passed; 469 dashboard tests passed; coverage 86.22%)
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
      quality-gates.sh green). Shipped a one-shot `POST /api/scheduled-jobs/purge-no-capacity`
      admin endpoint (status=no_capacity ONLY, never touches dispatched/queued/quarantined/timeout/
      error rows) to retroactively clear rows inserted before this fix; verified live 2026-08-18 —
      deploy confirmed via ao-self-pull (405 on the new route = live), then invoked once after the
      `ci_reconcile` resume below verified working: **purged 1301 historical no_capacity rows**.
      **Extended same day**: operator caught that `status=queued` has the identical repeat-spam
      pattern (na_eligibility_auditor/plan_reconciler's daily hourly-retry-until-queued cadence —
      dozens of duplicate `queued` rows per job observed live). Generalized `COALESCIBLE_STATUSES =
      {no_capacity, queued}` in the same collapse-on-write path, and replaced the narrower
      purge-no-capacity endpoint with `POST /api/scheduled-jobs/collapse-streaks` — a general
      retroactive pass that keeps the LATEST row of each consecutive same-status run instead of
      deleting every match outright, so a job currently sitting in a coalescible state stays visible
      rather than disappearing. Shipped agent-orchestrator@83731d3b83 (7 more new tests, quality
      gates green); verified live the same way (405/404 route-existence check), then invoked:
      **collapsed 250 historical duplicate `queued` rows**.
- [x] [REVIEW] P3. Once `ci_reconcile`'s manual-daily-task period produces enough signal on
      escalation-routing reliability, resume the timer and archive this doc's `ci_reconcile`
      section (or the whole doc, if all three have resolved by then). (repo: NA — operator
      judgment call on timing) — operator judged it satisfied 2026-08-18 and authorized the resume
      (see updated `ci_reconcile` section above); `ag_closeout`/`cefi_mtds_smoke` remain paused,
      untouched. Not archiving the doc/section since `ag_closeout`/`cefi_mtds_smoke` and follow-up 1
      are still open.
- **na-eligibility-audit 2026-08-19 (ao tranche)**: RECLASSIFY (whole-doc) -> `assigned_vm: planning`. 2 of 3 follow-up items already shipped same-day with evidence; sole remaining todo (add reason + paused_at field, surface on API + dashboard) is a scoped, deterministic schema/code change. Conflict-check clear: grepped plans/active/*.md for `scheduled_dispatch_pause` — zero hits outside this doc. Companion gated finalize: `ao_scheduled_dispatch_pause_reasons_2026_08_18_finalize_2026_08_19.md`.
- **context-scout 2026-08-19**: populated context_scope (5 entries).
- **2026-08-20 (slot 6, task ao_scheduled_dispatch_pause_reasons-7434f3d0c871)**: re-checked the "Current state"
  section against the live registry per this doc's own [REVIEW] P2 todo. Live read from the running server's
  persisted registry (`agent-orchestrator/data/state/scheduled_dispatch_paused_modes.dedup.json`, mtime
  2026-08-19 22:56): **6 modes paused** — `ag_closeout`, `cefi_mtds_smoke`, `ci_reconcile`, `na_eligibility`,
  `reconcile`, `report` — i.e. the 3-mode listing written 2026-08-18 had gone stale again (3 → 7 → 6 across
  2026-08-18/19/20), reinforcing the schema-fix todo. `ao_watchdog` confirmed NOT paused (resumed 2026-08-19).
  Updated the section + flipped the todo checkbox. No schema change made here (that's the separate open
  `[SCRIPT] P2` todo).

## MEASURED UPDATE 2026-08-19 — the paused set has grown from 3 to 7, and `ci_reconcile` is paused again

Read directly off the persisted registry on the orchestrator VM (read-only SSM;
`data/state/scheduled_dispatch_paused_modes.dedup.json`, the file
`scheduled_dispatch_pause.py` loads) rather than the API, since `/api/scheduled-dispatch/status`
needs auth:

```
["ag_closeout", "ao_watchdog", "cefi_mtds_smoke", "ci_reconcile", "na_eligibility", "reconcile", "report"]
```

**This doc's "Current state" section above is now wrong in two ways** and misled a 2026-08-19
investigation into the fleet's BOOTING slots: (1) it records 3 paused modes when 7 are, and
(2) it records `ci_reconcile` as RESUMED on 2026-08-18 — it is paused again, with today's
`scheduled_job_runs` rows confirming the effect live (`sjr-1a3d8ef3`, 19:24:05Z, 4 attempts,
`"mode 'ci_reconcile' is paused by operator"`). Four modes have no recorded reason at all:
`ao_watchdog`, `na_eligibility`, `reconcile`, `report`. Today's run rows show `plan_reconciler`
(all 10 tranches) and `na_eligibility_auditor` (all 10 tranches) each bouncing off their pause on
every tick.

This is exactly the structural gap the open `[FEATURE] P2` follow-up above exists to close: the
registry stores a bare `set[str]` with no `paused_at`/`reason`, so a pause added after a doc like
this one is written is invisible until someone reads the file by hand. Recording the measurement
here does not fix it — only the schema change does.

Separately, the modes that are NOT paused are starving on capacity rather than dispatching:
`scheduled_job_queue` rows for `escalation_queue_reconciler` (queued since 00:40Z, 6 attempts),
`data_pipeline_alerts_reconciler` (00:36Z, 11 attempts) and `context_scout_auditor` (00:53Z) carry
`last_error` of `"no free configured slot to dispatch plan_health check onto"`, and the
`na_eligibility_auditor` tranche rows carry `"no headroom account (Claude or DeepSeek) available to
dispatch"` — consistent with the account snapshots seen the same hour
(`overage_status: rejected`, `overage_disabled_reason: org_level_disabled` / `out_of_credits`).

## Todos (added 2026-08-19)

- [x] P1. Record the reason + rough date for the three still-unrecorded pauses
      (`na_eligibility`, `reconcile`, `report`) and for the re-pause of `ci_reconcile` in the
      sections above — or resume the ones that turn out to be forgotten.
      **`ao_watchdog` RESOLVED 2026-08-19**: operator authorized resuming it and only it;
      `POST /api/scheduled-dispatch/ao_watchdog/resume` returned `{"mode":"ao_watchdog",
      "status":"active"}` and the persisted registry re-read confirms it is gone from the paused
      set (6 remain: ag_closeout, cefi_mtds_smoke, ci_reconcile, na_eligibility, reconcile,
      report). It was the urgent one — it is the fleet's own daily health check
      (`/plans/active/issues/ao_watchdog_scheduled_timer_wiring_2026_08_17.md` wired its timer),
      so while it was paused nothing was running the check that would have surfaced the other six.
      **RESOLVED 2026-08-20 (operator ruling on todo
      ao_scheduled_dispatch_pause_reasons-53b859c93847 — source:
      /plans/active/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md)**: the three
      still-unrecorded pauses (`na_eligibility`, `reconcile`, `report`) were intentional — those
      skills were being run by operators on their own hosts because the fleet's claude accounts
      were exhausted at the time (roughly 2026-08-19), not forgotten. Nothing to resume, nothing
      further to record.
      (repo: NA — operator knowledge, not derivable from any system field)
- [x] ✅ [REVIEW] P2. Re-check the "Current state" section against the live registry file whenever
      this doc is touched, until the `paused_at`/`reason` schema change lands — a hand-maintained
      list of paused modes went stale within 24h of being written, which is the measured argument
      for the schema fix, not just the theoretical one. — re-checked 2026-08-20 (slot 6): "Current state"
      section updated to the live 6-mode set read from the running server's persisted registry
      (`agent-orchestrator/data/state/scheduled_dispatch_paused_modes.dedup.json`, mtime 2026-08-19 22:56) —
      `["ag_closeout","cefi_mtds_smoke","ci_reconcile","na_eligibility","reconcile","report"]`; prior 3-mode
      listing was stale. (repo: unified-trading-pm)
- [ ] [INFRA] P2. Decide whether scheduled-job capacity starvation deserves its own alert: the
      three `plan_health`-family jobs above sat queued ~20h on 2026-08-19 with `no free configured
      slot` / `no headroom account`, and nothing paged. Distinct from the pause question — these
      modes are enabled and still not running. (repo: agent-orchestrator)
