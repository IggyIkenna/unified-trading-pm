---
doc_type: issue
title: monitoring-deadman cron crashes in run_lifecycle log_event (DP_ZOMBIE_WATCHDOG_DOWN root)
summary:
  "The `uts-prod-monitoring-deadman` Cloud Run job (cron `*/…`) is FAILING every run (recent executions X/X, 0/1
  complete). Traceback:"
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer, admin]
tags: [monitoring, observability, self-healing, data-pipeline, runbook, slack]
related:
  [
    /plans/archive/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md,
    /plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md,
  ]
created: 2026-06-23
parent_epic: mtds_mdps_master
priority: P2
source: [alerts.log Slack triage 2026-06-23 (DP_ZOMBIE_WATCHDOG_DOWN + DP_CRON_DID_NOT_FIRE deadman)]
assigned_vm:
resolved_by:
  dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md open-work item 1 (deployment-api rebuild, cloudbuild 0c9af143
  SUCCESS), verified 2026-06-23 ~22:00Z
locked_by: live-defi-rollout
locked_since: 2026-05-21
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
---

> **✅ CODE FIX SHIPPED 2026-06-23 — deployment-service@`9b32ea5`.** Root cause confirmed via Cloud Logging: the deadman
> entered `run_lifecycle("monitoring-deadman")` → UTL `run_lifecycle` calls `log_event` WITHOUT `setup_events()` →
> `RuntimeError("Event logging not initialized")`. The deadman is the OUT-OF-BAND watcher (its docstring forbids
> `log_event`/PubSub; GCP-native execution-absence alerting is its bedrock), and its sibling out-of-band monitors use no
> `run_lifecycle` — so the fix REMOVES `run_lifecycle` + honors the documented "never raises, exits 0 always" contract.
> **✅ Live verification DONE + VERIFIED 2026-06-23 ~22:00Z** (was: "BLOCKED on `deployment-api:latest` rebuilding" —
> corrected 2026-07-12, finding id 181, §A2 B-queue ruling): `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md`
> "Open work" item 1 (line ~104) records the rebuild landing (Cloud Build `0c9af143` SUCCESS, image CLONES
> deployment-service@live-defi-rollout so the "170 commits ahead of main" concern never mattered) and the deadman
> re-pinned + executed: **deadman 1/1 GREEN (exit 0, was exit 1 every run)**. Full triage in
> `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` (the full #data-pipeline-alerts flood triage — real-vs-false
> per class + the remaining monitor + data fixes).

## What I found

The `uts-prod-monitoring-deadman` Cloud Run job (cron `*/…`) is FAILING every run (recent executions X/X, 0/1 complete).
Traceback:

```
deployment_service/data_pipeline_monitors/deadman_poster.py:343  with run_lifecycle(service_name="monitoring-deadman"):
unified_trading_library/events/run_lifecycle.py:141              log_event(f"{prefix}_RUN_STARTED", severity="INFO", details=initial_details)
```

`prefix = _derive_event_prefix("monitoring-deadman")` → the derived event (`MONITORING_DEADMAN_RUN_STARTED`) is almost
certainly **not a registered lifecycle event** (or `_derive_event_prefix` rejects the service name), so `log_event`
raises at the very start of `run_lifecycle` and the deadman never posts its heartbeat.

## Why it matters

The deadman is the META-monitor (it verifies the other DP monitors/crons fired). Its crash is the ROOT of these Slack
alerts (all firing because the deadman's durable heartbeat is stale, NOT because the watched things are actually down):

- `DP_ZOMBIE_WATCHDOG_DOWN` (vm-zombie-watchdog census stale)
- `DP_CRON_DID_NOT_FIRE` for `dp-exit-code-monitor` / `manifest-consolidator-cefi` (FALSE — both verified ENABLED +
  running with recent ✔; the deadman just couldn't confirm them)

It also matches the QG flaky failure `test_data_pipeline_deadman.py::test_check_monitor_crons_missing_sentinel`. The
PRIMARY monitors (exit-code-monitor, heartbeat-watcher) are healthy (✔), so backfill VM monitoring is degraded (no
meta-check) but not lost.

## Recommended decision

Fix `run_lifecycle`/`_derive_event_prefix` (UTL) OR `deadman_poster.py` so `service_name="monitoring-deadman"` derives a
VALID registered lifecycle event (register `MONITORING_DEADMAN_*` lifecycle events, or pass a recognized service_name /
bypass run_lifecycle for the deadman). Cross-cutting UTL+deployment-service; redeploy the deadman job after. NOT
cefi-asset-group — flag to the monitoring/infra owner. (Gated by the current deployment-service QG flaky-test block —
see the fleet-health follow-up.)

## cefi alert triage (this pass — RESOLVED/transient)

- `DP_CATALOG_NOT_RUNNING` (cefi) — catalogue present + fresh (`prod/catalog.parquet` 3.2MB, mtime 18:19 UTC, <24h).
  Fired during a catalogue-rollup delete-rewrite window. RESOLVED.
- `DP_CRON_DID_NOT_FIRE` (manifest-consolidator-cefi) — cron ENABLED `*/1` + recent ✔. Transient/heartbeat
  false-positive (the deadman crash above). RESOLVED.
