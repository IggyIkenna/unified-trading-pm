---
doc_type: issue
title: >-
  deployment-api's D.3 health-alert gate (_alert_on_health_transition) only ever runs as a side effect of
  _load_inventory — there is no dedicated Cloud Scheduler cron polling it, so a newly-alertable state's real page-firing
  cadence is bounded by whoever has the deployment-ui dashboard open (or the once-daily digest), not by any independent
  schedule
summary: >-
  Surfaced during this session's false-positive-risk investigation for
  /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md todo 1 (adding "hung" to
  `_ALERT_HEALTH_STATES`). `_alert_on_health_transition()` fires only inside `_compute_inventory()`
  (`deployment_api/routes/deployments_inventory.py`), which itself only runs as a side effect of a caller reaching
  `_load_inventory()` — a stale-while-revalidate cache with `_INVENTORY_TTL_SEC=45.0`. Confirmed by direct read: no
  `deployment-service/terraform/gcp/*.tf` Cloud Scheduler job targets deployment-api's inventory/health endpoint (unlike
  `heartbeat_stall_watcher.py`, `vm_zombie_watchdog.py`, and the exit-code monitor, which all have dedicated `*/5` or
  `*/15` crons — see `data_pipeline_fleet_monitor_scheduler.tf`). The only two real callers found: (1) the deployment-ui
  Cockpit "Health" tab / Deployments list view, which fires only while a human has that view open, and (2)
  `deployment_digest_worker.py`'s Cloud Scheduler cron (`deployment_digest_scheduler.tf`), which does call
  `_load_inventory()` but fires only once per day (`30 7 * * *` UTC) — far too coarse for meaningful paging. Net: today
  (before this session's fix) `_ALERT_HEALTH_STATES` only ever pages on oom-risk, and only when someone happens to have
  the dashboard open (or the next day's digest run happens to catch a still-alertable state) — not on any bounded,
  independent cadence. This session's fix additionally makes "hung" alertable
  (`migration_vm_hung_detection_monitoring_gap_2026_07_27.md` todo 1), which inherits the exact same scheduling gap: the
  new alert is provably correct in a unit test but is not, by itself, the automatic fleet-wide safety net the parent
  issue's investigation intended — it still depends on a human having the dashboard open or the digest cron's once-
  daily cadence. This is a distinct, adjacent gap from todo 1's own literal scope (which is specifically about the
  `_ALERT_HEALTH_STATES` frozenset membership + the transition-dedup logic, not about scheduling), so it is filed
  separately rather than silently folded into that fix.
status: open
nature: issue
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [infrastructure]; deployment-api's own
  # inventory/health-alert code path (repos: deployment-api primary, deployment-service for the missing cron)
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer]
tags:
  [
    vm-monitoring,
    hung-vm,
    fleet-auto-kill,
    stall-detection,
    heartbeat,
    deployment-observability,
    cloud-scheduler,
    alerting,
    inventory-cache,
  ]
related:
  [
    /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-27
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P2
estimate_class: infra
assigned_role: infrastructure
source: >-
  Found during this session's false-positive-risk investigation for
  /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md todo 1 (adding "hung" to
  `_ALERT_HEALTH_STATES`), 2026-07-27 — an interactive `/autonomous` session shipping that todo's fix. All code-path
  claims in this doc were verified this session by direct file read: `_load_inventory`/`_compute_inventory`/
  `_INVENTORY_TTL_SEC` in `deployment_api/routes/deployments_inventory.py`; a corpus grep of
  `deployment-service/terraform/gcp/*.tf` for any scheduler targeting an inventory/health endpoint (none found);
  `deployment_digest_scheduler.tf` (`30 7 * * *`, confirmed calls `_load_inventory()` via
  `deployment_api/routes/deployment_digest.py`); and the deployment-ui Cockpit/Deployments call sites
  (`getDeploymentInventory`, fetched once per mount).
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
context_scope:
  [
    /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /codex/05-infrastructure/deployment-observability.md,
    deployment-api/deployment_api/routes/deployments_inventory/_aggregation.py,
    deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf,
    deployment-api/deployment_api/routes/deployments_inventory/,
  ]
locked_since:
resolved_by:
---

# deployment-api's D.3 health-alert gate has no independent polling schedule — it rides the on-demand inventory cache

> Investigation-only record (this doc). No terraform/scheduler resource was added, no endpoint was wired, while
> authoring this doc. `assigned_vm: NA`, `execution_scope: local-only` — a human decides when to pick up the fix todo
> below.

## What I found

`deployment_api/routes/deployments_inventory.py`'s `_alert_on_health_transition()` — the function that fires
`_persist_alert(...)` for any state in `_ALERT_HEALTH_STATES` (`oom-risk`/`stalled`, and as of this session's
migration_vm_hung_detection_monitoring_gap_2026_07_27.md todo 1 fix, `hung`) — is called once per `DeploymentItem`
inside `_compute_inventory()` (confirmed call site). `_compute_inventory()` itself is NOT a standing job: it only runs
as a side effect of a caller reaching `_load_inventory()`, which is a stale-while-revalidate cache
(`_INVENTORY_TTL_SEC=45.0`): a request within the TTL serves the cached snapshot with zero recompute; a stale snapshot
triggers exactly one background refresh via `_inventory_refresh_pool` (`max_workers=1`), but ONLY when some caller
invokes `_load_inventory` in the first place.

Grepping `deployment-service/terraform/gcp/*.tf` for any Cloud Scheduler job targeting deployment-api's inventory/health
endpoint returns nothing. This is a real asymmetry against the sibling watchers documented in the parent issue doc:

- `heartbeat_stall_watcher.py` — dedicated `dp_heartbeat_watcher_cron`, `*/5 * * * *`
  (`data_pipeline_fleet_monitor_scheduler.tf`).
- `vm_zombie_watchdog.py` — standing daemon VM, default sweep `INTERVAL=300s` (`launch-vm-zombie-watchdog.sh`).
- The fleet exit-code monitor — its own dedicated cron (not re-derived here, see
  `data_pipeline_fleet_monitor_scheduler.tf`).
- deployment-api's own D.3 alert gate — **no dedicated cron at all.**

The two real callers that DO reach `_load_inventory()` today:

1. **deployment-ui's Cockpit "Health" tab + Deployments list view** — `getDeploymentInventory` fetches once per mount.
   Fires only while a human happens to have that browser tab open.
2. **`deployment_digest_worker.py`** — a genuine Cloud Scheduler cron (`deployment_digest_scheduler.tf`, `30 7 * * *`
   UTC, once per day), whose `run_deployment_digest()` (`deployment_api/routes/deployment_digest.py`) does call
   `_load_inventory()` and would therefore exercise `_alert_on_health_transition()` as a side effect — but once/day is
   far too coarse a cadence for meaningful paging on a state meant to catch a VM hung for as little as 15 minutes.

## Net effect

Before this session's fix, `_ALERT_HEALTH_STATES = {"oom-risk", "stalled"}` already had this same scheduling gap — it
was simply masked by the fact that `"stalled"` almost never fires (BATCH-only, per the parent issue doc's Gap-1 side
note) and `"oom-risk"` alerts are rare enough that the gap wasn't obviously costing anything. Adding `"hung"` (this
session, todo 1) changes that: `"hung"` is expected to fire far more often (a VM simply going 15+ minutes without a
heartbeat write is a common, not rare, failure mode — it's exactly the failure this whole parent issue doc is about).
Without an independent poll, a VM that goes hung while nobody has the dashboard open will not page until either (a) a
human opens the Cockpit/Deployments view, or (b) the next day's 07:30 UTC digest run happens to still observe the `hung`
state (a fresh transition only fires once — if the VM went hung-and-recovered, or hung-and-was-manually-killed, between
polls, the digest's once-daily sample can miss the transition event entirely, per `_alert_on_health_transition`'s
dedup-by-transition design). This reproduces, in a more silent form, the exact manual-staleness-sweep workaround the
parent issue doc's Script-1 incident describes — the fix "works" (proven by the todo 1 unit test) but is not the
automatic fleet-wide safety net that investigation's stated intent was.

## What this is NOT

- **Not a bug in the `"hung"` classifier itself, nor in `_alert_on_health_transition`'s dedup logic.** Both are correct
  and unit-tested (see `migration_vm_hung_detection_monitoring_gap_2026_07_27.md` todo 1's shipped test:
  `test_alert_on_health_transition_fires_on_hung_transition`). This doc is about the surrounding SCHEDULE, not the
  gate's own logic.
- **Not a claim that deployment-api's inventory is never computed on a schedule.** It IS computed once/day via the
  digest cron (a side effect, not the digest's own purpose) — this doc's point is that once/day is not a meaningful
  alerting cadence for a 15-minute-threshold state.
- **Not itself a fix.** No code was changed while authoring this doc — see the banner above.

## What's NOT done / follow-up needed

- [ ] [HUMAN] P2. **Add an independent, dedicated polling cadence for deployment-api's D.3 health-alert gate** — e.g. a
      Cloud Scheduler job analogous to `dp_heartbeat_watcher_cron`'s `*/5 * * * *` hitting a lightweight
      `/api/deployments/inventory` (or equivalent) endpoint on a schedule independent of any dashboard being open or the
      once-daily digest. Weigh whether to reuse the existing inventory endpoint (accepting its ~45s TTL / `_census_pool`
      cost) vs. building a narrower "alert-check-only" path that skips the full Cloud Run job/service/AWS census fan-out
      (cheaper, lower blast-radius on the `max_workers=1` refresh-serialization invariant documented at
      `deployments_inventory.py` line ~296-307 — see that comment for why raising pool concurrency without also bounding
      total fan-out risks the OOM regression it fixed). Done when: a Cloud Scheduler job (or equivalent standing
      trigger) reaches `_load_inventory()` on a bounded interval (target: `*/5`-`*/15` minutes, matching the sibling
      watchers' cadence) independent of UI traffic and the daily digest, verified via `gcloud scheduler jobs describe`
      showing recent successful invocations and a corresponding `_persist_alert` ledger entry appearing within that
      interval of a deliberately-induced `hung` test VM (not just the unit test — an end-to-end schedule-fires-in-prod
      check).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Single todo embeds a real
  unresolved architecture trade-off (reuse existing endpoint vs. build a narrower alert-check-only path) citing a
  specific OOM-regression-risk code comment — genuine judgment call.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-2cd17a)**: KEEP-NA, valid — re-confirmed; the 2026-07-30
  verdict (filed under the pre-retag `infra` tranche label) still holds unchanged: the single open todo is a genuine
  unresolved architecture trade-off (reuse the existing 45s-TTL inventory endpoint vs. build a narrower alert-check-only
  path) citing a specific OOM-regression-risk code comment. No content change since; doc has no `last_updated` field so
  this refresh anchors the next incremental diff.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
