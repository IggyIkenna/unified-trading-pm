---
doc_type: issue
title: >-
  defi manifest consolidator Cloud Scheduler cron left PAUSED for 13.5h — every mvp_backfill_defi_onchain_v10-002
  verification session on 2026-07-15 read frozen coverage numbers without realizing it
summary: >-
  While re-running this plan's G2 final-verification todo, found `uts-prod-manifest-consolidator-market-data-defi-cron`
  (the Cloud Scheduler job that triggers the defi manifest consolidator Cloud Run Job, normally `*/1 * * * *`) had been
  in state PAUSED since 2026-07-14T22:25:11Z (Admin Activity audit log — CloudScheduler.PauseJob by
  ikenna@odum-research.com, almost certainly an agent session testing the CONSOLIDATOR_LOCK_TTL_SECONDS fix in
  defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md that never re-enabled the cron afterward). Zero
  executions of the Cloud Run job ran between 2026-07-14T23:11:47Z and the resume below (~12h40m gap) despite
  mtds-pyth-archive-*/mtds-lending-indices-*/mtds-solana-drift-backfill VMs actively writing per-VM shards the whole
  time — so the consolidated _index/availability_index.parquet (and therefore every measure_honest_coverage.py reading)
  was frozen at 2026-07-14T22:47:57Z. At least 5 independent data_engineering slot sessions today (11:02Z, 11:14Z,
  11:22Z, 11:34Z, 11:50Z) each re-ran the coverage measurement and got byte-identical numbers, correctly concluding "no
  independent movement" on 5/6 data_types — but none of them checked WHY the manifest wasn't moving; the answer was "the
  tool that builds it was turned off", not "no real backfill progress is happening". The consolidator's own liveness
  watchdog (uts-prod-consolidator-liveness-watchdog, every 2 min) correctly detected this and has been logging "ERROR
  consolidator-liveness: ... market-data-tick-defi-prd-central-element-323112 -> down" + "exit(1)" every cycle since
  staleness crossed its 300s threshold — so DETECTION worked, but nothing paged a human/agent on a Cloud Run Job exit(1)
  (see Recommended decision #2), and nothing auto-resumes a scheduler that is PAUSED (as opposed to merely
  failing/erroring — a paused job is a deliberate-looking state that this watchdog design doesn't distinguish from "will
  recover on its own").
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [consolidator, cloud-scheduler, defi, manifest, staleness, alerting-gap]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-15
parent_epic: defi_master
source:
  [data_engineering slot-13, 2026-07-15, discovered while re-running mvp_backfill_defi_onchain_v10-002's G2 gate check]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-15
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

Re-running `mvp_backfill_defi_onchain_v10-002`'s own checklist (`measure_honest_coverage.py --asset-group defi`) at
11:50-11:51Z produced numbers **byte-identical** to slot-12's 11:22-11:40Z run and slot-7's 11:34-11:44Z run (same
`dex_pool_state`/`dex_pool_swaps`/`lending_indices`/`lst_rates`/`oracle_prices`/`perp_funding` captured /
attempted_failed / expected_unattempted for all 6 MVP data_types). Both runs' logs cited the identical pinned-primary
manifest blob `blob.updated=2026-07-14T22:47:57.690000+00:00` — i.e. the underlying manifest simply had not changed,
regardless of how much real capture work the active backfill VMs were doing.

Checked `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-defi`: last completed
execution was `2026-07-14T23:11:47Z`. Checked the triggering Cloud Scheduler job:

```
gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-defi-cron --location=asia-northeast1
  state: PAUSED
  lastAttemptTime: 2026-07-14T22:25:01Z
```

Admin Activity audit log confirms the pause action:

```
2026-07-14T22:25:11Z  google.cloud.scheduler.v1.CloudScheduler.PauseJob  ikenna@odum-research.com
```

No matching `ResumeJob` after that. The most likely origin: the same 2026-07-14/15 session that root-caused and fixed
the consolidator SIGKILL livelock (`defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`, Terraform
`CONSOLIDATOR_LOCK_TTL_SECONDS=4200` override) paused the cron to isolate a clean manual test run of the fix, then never
re-enabled it — an exact repeat of the pause/resume pattern already visible in the audit trail on 2026-07-10 (`PauseJob`
17:56Z → `ResumeJob` 21:34Z → `PauseJob` 21:38Z → `ResumeJob` 21:44Z), except this time the final resume was skipped.
That 07-10 issue doc even states explicitly: _"The scheduler was left **enabled** (not re-paused) — a
failing-but-harmless cycle is safer than a paused consolidator that would silently miss a REAL [outage]"_ — the exact
failure mode that then happened 4 days later.

**Verified the watchdog saw it the whole time** — `uts-prod-consolidator-liveness-watchdog` (Cloud Run Job, triggered
`*/2 * * * *`) logs, at every single cycle since staleness crossed 300s:

```
ERROR consolidator-liveness: 2 bucket(s) DOWN: instruments-store-sports-central-element-323112,
  market-data-tick-defi-prd-central-element-323112
Container called exit(1).
```

So `ConsolidatorLivenessMonitor.check()` (`unified_trading_library/monitors/consolidator_liveness.py`) worked exactly as
designed — stale heartbeat + per-VM shards present → `STATUS_DOWN` → logged ERROR + non-zero exit. The gap is
downstream: nothing converted 12+ hours of Cloud-Run-job exit(1) into a page, and nothing distinguishes "scheduler
explicitly PAUSED" (a state that will NEVER self-recover) from "scheduler enabled but the job is erroring" (which might
self-recover).

**Fix applied**:
`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron --location=asia-northeast1` at
11:56Z. Confirmed a new execution was created within the next cron tick
(`uts-prod-manifest-consolidator-market-data-defi-xsctw`, started 11:56:04Z) and is running (not immediately SIGKILLed,
consistent with the 07-10/07-14 lock-TTL fix holding). Left it running — a 12h40m backlog of per-VM shards may take a
single long cycle to fully absorb (the fixed lock TTL is 4200s = 70min, so this is expected to survive a
longer-than-usual merge). No `/done` claim of a completed catch-up in this doc; the next session re-running the coverage
tool will see whatever the caught-up manifest actually shows.

## Why it matters

This is a **data-correctness / verification-integrity** issue, not just a wasted-compute one: for 13.5 hours, EVERY
consumer of the defi honest-coverage numbers (this plan's G2 gate check, any dashboard reading the manifest, any other
plan cross-referencing defi coverage) was reading numbers that could not reflect reality no matter what the backfill
fleet did. At least 5 independent agent sessions today spent real time re-confirming "no movement" on 5/6 data_types
when the true state was "unmeasurable, not unmoving" — a subtly different and more time-wasting failure mode than a
simple stale cache, because each session's own diligence (re-running the tool fresh instead of trusting old numbers)
still produced the same wrong non-conclusion, since the tool's OWN input was frozen.

## Recommended decision

1. **[DONE this session]** Resumed the paused cron; a real merge cycle is in flight. Next session: re-run
   `measure_honest_coverage.py --asset-group defi` and expect the numbers to have moved for the first time in 13.5h
   (real signal on `oracle_prices`/`lending_indices`/`perp_funding` given the active VMs, per this plan's own recent
   Progress Log entries).
2. **[NOT done — P1 follow-up, repo: deployment-service or agent-orchestrator, whichever owns infra alerting]**
   Investigate why 12+ hours of `uts-prod-consolidator-liveness-watchdog` exit(1) failures did not escalate to a
   human/Slack page. Either the Cloud Run Job failure isn't wired to an alert policy at all, or it's wired but the
   channel/routing silently dropped it. Per this workspace's own alerting SSOT
   (`codex/04-architecture/agent-orchestrator-alerting.md` / `…/ci-alerting.md`), a standing-condition failure like this
   should dedup-and-page on the state transition, not require a human to stumble onto it via an unrelated verification
   task.
3. **[NOT done — P2 follow-up, repo: unified-trading-library]** `ConsolidatorLivenessMonitor.check()` treats "heartbeat
   stale" as one bucket of causes. Consider having the watchdog (or a sibling check) explicitly query each bucket's
   triggering Cloud Scheduler job state via the Scheduler API and flag `state=PAUSED` as its own, higher-confidence
   signal (a paused job is deterministically dead, not a maybe-transient error) — this would have surfaced "the cron is
   PAUSED" directly instead of requiring a human to manually check the scheduler describe output, as this session did.
4. **[Process note, no code]** Anyone pausing a production consolidator cron mid-debug (as both the 07-10 and 07-14/15
   sessions did) should treat the pause as a tracked TODO with an explicit resume step in the SAME session, not an
   implicit "I'll remember" — this is the second time in 5 days this exact class of leftover-paused-cron has happened on
   the identical job.

## Todos

- [x] [INFRA] P1. Resume `uts-prod-manifest-consolidator-market-data-defi-cron` (Cloud Scheduler) — done this session,
      2026-07-15T11:56Z, verified a new execution started. (repo: deployment-service)
- [x] [INFRA] P1. ✅ Determine why `uts-prod-consolidator-liveness-watchdog` Cloud Run Job exit(1) failures (12+
      consecutive cycles over 13.5h) did not escalate to a Slack/human page; wire the missing alert or fix the broken
      routing. — deployment-service@546216f. Findings: the app-level path (`log_event(CONSOLIDATOR_DOWN)` →
      `lifecycle-events` Pub/Sub → alerting-service's `handle_consolidator_down_payload` → PagerDuty/Telegram,
      `alerting-service/alerting_service/rules/consolidator_rules.py:103-136`) is fully coded and, per the incident's
      own quoted logs (no swallowed exception in `check_and_emit`), DID fire during the incident — the
      `unified_trading_library@bf6fb9c3` (2026-07-12) fix that wired `setup_events()` into
      `consolidator_liveness._main()` was already live. The confirmed, closeable gap was different: **zero
      Cloud-Monitoring-level coverage existed for this Cloud Run Job's own exit code** — grepping every
      `google_monitoring_alert_policy` in `deployment-service/terraform/gcp/*.tf` found none keyed off
      `resource.type="cloud_run_job"` for `uts-prod-consolidator-liveness-watchdog` (or any Cloud Run Job generically);
      the watchdog itself — the one thing watching the consolidator — had no independent watcher, violating the "each
      layer independent of the one it watches" design in `codex/05-infrastructure/deployment-observability.md` §
      "Out-of-band liveness". **Fix shipped**: added
      `google_monitoring_alert_policy.consolidator_liveness_watchdog_failed` to `consolidator_liveness_scheduler.tf`, a
      log-matched-condition alert on `resource.type="cloud_run_job" AND job_name=<this job> AND severity="ERROR"`, wired
      to the already-provisioned `google_monitoring_notification_channel.monitoring_deadman_email` (the same real,
      non-toothless channel `deployment_api_memory_alert.tf`/`critical_service_uptime.tf` use — deliberately NOT the
      empty-default-var pattern in `cf_manifest_audit_scheduler.tf`, which ships an alert nobody receives until a
      separate wiring step). Rate-limited to 1 page/hour while the condition persists (cron is `*/2 min`), auto-close
      7d. `terraform validate` clean. **Residual, NOT closed by this fix** (flagged as a fresh follow-up below since
      it's outside what could be verified from a repo-only sandbox): whether the app-level Pub/Sub→alerting-service page
      for THIS specific incident was actually delivered end-to-end or silently dropped downstream —
      `alerting-service/subscribers/alert_subscriber.py`'s `_route_one` wraps `dispatch_event()` in a broad
      `except Exception` that only `logger.warning`s ("skipping") on failure, so a PagerDuty/Telegram misconfiguration
      would silently eat a page with no escalation of that failure either. This repo-only investigation could not verify
      live Cloud Logging / PagerDuty delivery, so this is tracked as new todo #4 below rather than closed here.
- [ ] [SCRIPT] P2. Extend `ConsolidatorLivenessMonitor` (or add a sibling check) to query the triggering Cloud Scheduler
      job's `state` directly and flag `PAUSED` as a distinct, higher-confidence DOWN reason (not just consolidated-blob
      heartbeat age). (repo: unified-trading-library)
- [ ] [BACKEND] P2. `alerting-service/subscribers/alert_subscriber.py`'s `_route_one` (~lines 400-431) wraps
      `dispatch_event()` in a broad `except Exception` that only `logger.warning`s ("skipping ...") on failure — a
      downstream fault (missing PagerDuty/Telegram secret, a misconfigured rule, an unhandled payload shape) silently
      drops a page with no escalation of that failure itself, the same "who watches the watcher" gap this issue's P1
      todo just closed at the Cloud-Monitoring layer. Add a paging/summary-log path for `_route_one` dispatch failures
      (mirrors `notify_daily_summary_failed`'s "a dead digest must not be silent" pattern in
      `codex/04-architecture/agent-orchestrator-alerting.md`) so a broken alert route is itself loud. Found while
      investigating why the 2026-07-15 consolidator-liveness-watchdog exit(1) failures never paged — could not verify
      live whether THIS specific incident's page was actually delivered or silently eaten by this exact code path (no
      live Cloud Logging/PagerDuty access from a repo-only investigation). (repo: alerting-service)
