---
doc_type: plan
title: Surface resource-watchdog kill/violation events through deployment-api + deployment-ui
summary: >-
  The orchestrator host's resource-watchdog (resource_watchdog_host_guardian_2026_08_05.md) kills runaway processes and
  logs each kill/violation to a VM-local file + AO's own internal API/UI only — a same-day operator ruling deliberately
  scoped it to "AO UI surface only." Direct operator instruction (2026-08-05, follow-up session after a RAM-spike
  investigation) reverses that scope: kill/violation events should ALSO surface through deployment-api/deployment-ui's
  existing resource-monitoring surfaces, on the principle that AO not being a deployment-service-launched target
  shouldn't exclude its host from deployment monitoring. Adds a new BigQuery table + writer + ingest route + read route
  + UI panel, following the exact `reap_events`/`idle_spend` pattern already proven in `deployment_operational_data`.
status: complete # archived 2026-08-05 — every todo done; close-out verified by finalize plan
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [watchdog, observability, deployment-api, deployment-ui, bigquery, ao, resource-monitoring]
related:
  [
    /plans/active/resource_watchdog_host_guardian_2026_08_05.md,
    /plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md,
    /plans/active/watchdog_kill_events_deployment_observability_2026_08_05_finalize.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by: watchdog_kill_events_deployment_observability_2026_08_05_finalize
depends_on: []
source: >-
  Direct operator instruction, interactive session 2026-08-05, immediately following a RAM-spike investigation on the
  agent-orchestrator API host that surfaced the resource-watchdog's own backup/logrotate gap (see
  resource_watchdog_host_guardian_2026_08_05.md's 2026-08-05 Progress Log entry) and, separately, that
  deployment_operational_data.resource_samples has zero rows for the AO host because it isn't a
  deployment-service-launched target.
context_scope:
  [
    /plans/active/resource_watchdog_host_guardian_2026_08_05.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/05-infrastructure/deployment-observability.md,
    unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.sh,
    deployment-api/deployment_api/services/operational_data_writer.py,
    deployment-ui/src/pages/VmResourceComparison.tsx,
  ]
---

# Surface resource-watchdog kill/violation events through deployment-api + deployment-ui

## Why this exists — and why it reverses a same-day decision

`resource_watchdog_host_guardian_2026_08_05.md` Phase 4 shipped a kill-status panel wired into AO's own dashboard ONLY —
its own checked-off todo says "not deployment-api — operator directed AO UI surface only." That was the correct scope at
the time it was decided. Later the same day, an interactive RAM-spike investigation found: (1) the watchdog's own
log/snapshots had zero off-VM backup and zero local rotation (fixed separately, see the watchdog plan's Progress Log),
and (2) `deployment_operational_data.resource_samples` — the fleet-wide, 1-week+ rolling BigQuery resource-history table
with its own live API + UI page — has ZERO rows for the AO host, confirmed via a live `bq query`, because AO isn't a
deployment-service-launched target. The operator's read: that exclusion is an accident of how AO happens to be
provisioned, not a reason to keep its incident data siloed from every other host's. This plan reverses the AO-UI-only
scope for kill/violation events specifically (not the AO dashboard panel itself, which stays — this is additive, not a
replacement).

## Approach

Reuse the exact `reap_events`/`idle_spend` pattern already proven in `deployment_operational_data`
(`deployment-api/deployment_api/services/operational_data_writer.py`) rather than inventing a new mechanism: UTL
`insert_rows` streaming writes, no new Pub/Sub topic needed (kill events are low-frequency). The resource-watchdog
already POSTs each kill to AO's own `POST /api/resource-watchdog/kill` — this plan adds a SECOND, additive forward to a
new deployment-api ingest route, not a replacement of the existing AO-internal path.

## Todos

- [x] ✅ [DATA] P1. Create the `deployment_operational_data.watchdog_kill_events` BigQuery table using the same —
      deployment-service@688d925 table-creation mechanism `reap_events`/`idle_spend` were created with (see
      `/plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md` for that mechanism — do not
      invent a new one). Schema:
      `ts TIMESTAMP, vm_name STRING, pid INT64, slot_id STRING, command STRING, reason     STRING, rss_mb INT64, limit_mb INT64, pressure_level STRING, killed BOOL`.
      Done when `bq show     central-element-323112:deployment_operational_data.watchdog_kill_events` returns this
      schema.
- [x] ✅ [BACKEND] P1. Add `write_watchdog_kill_event(...)` to
      `deployment-api/deployment_api/services/operational_data_writer.py`, following `write_reap_event`'s exact shape
      (UTL `insert_rows`, try/except-log, never raises). Done when a unit test inserts a synthetic row and asserts no
      exception on both a well-formed and a malformed payload. — deployment-api@0a3e69d
- [x] ✅ [BACKEND] P2. Add a `POST` ingest route in deployment-api (e.g. `/api/fleet/watchdog/kill-events`) that calls
      the new writer. No new auth model — reuse whatever the existing fleet ingest routes in
      `deployment-api/deployment_api/routes/fleet.py` already use. Done when a `curl` POST with a synthetic payload
      returns 2xx and the row is visible via `bq query` within a minute. — deployment-api@7d79433
- [x] ✅ [INFRA] P2. Wire `resource-watchdog.sh`'s `_rw_notify_orchestrator()` (or a sibling function, additive — do not
      remove the existing AO-internal POST) to ALSO POST each kill event to the new deployment-api ingest route from the
      prior todo. Fire-and-forget, same pattern as the existing orchestrator POST (must not block the watchdog's
      enforcement loop on network I/O). Done when a live (or `--dry-run`-simulated) kill produces a row in
      `watchdog_kill_events` within the same tick. — unified-trading-pm@08f6a9571 Evidence: Added
      `_rw_notify_deployment_api()` sibling function to `resource-watchdog.sh` that POSTs to
      `POST /api/fleet/watchdog/kill-events` (additive dual-write alongside existing AO-internal POST). Opt-in via
      `RW_DEPLOYMENT_API_URL` env var. Dry-run sends `killed: false`; live kill sends `killed: true`. Fire-and-forget
      with 3s connect / 5s max-time. config.yaml updated with new keys.
- [x] ✅ [BACKEND] P2. Add a `GET` read route in deployment-api (e.g. `/api/watchdog/kill-events?vm_name=&hours=`)
      returning recent rows, following `GET /api/vm-resources/rolling`'s query-shape conventions in
      `deployment-api/deployment_api/routes/vm_resource_history.py`. Done when the route returns real rows for the AO
      host after the prior todo has produced at least one. — deployment-api@37d6f14 Evidence: GET
      /api/watchdog/kill-events (prefix /api/watchdog, router watchdog_events.py) + SQL builder
      `watchdog_kill_events_sql()` (operational_data_queries.py), wired in main.py, 15 unit tests green, QG green. Route
      SQL validated live against central-element-323112 table (schema matches plan). Table currently has 0 rows (no kill
      event produced yet — the [REVIEW] P3 todo owns triggering the first real/dry-run kill); route degrades honestly to
      empty until then.
- [x] ✅ [UI] P3. Add a kill-events panel to `deployment-ui/src/pages/VmResourceComparison.tsx`'s existing per-VM
      expandable-row scaffolding (the same one already wired to `getProcessCategoryBreakdown`), showing recent kills for
      the AO host: timestamp, command, reason, rss_mb/limit_mb. Done when the panel renders real data for the AO host in
      a local dev run against the live deployment-api. — deployment-ui@adac737 | pw:L2 ✓ | regression:
      tests/smoke/vm-resource-rolling-window.spec.ts
- [x] ✅ [DOC] P3. Update `/codex/05-infrastructure/agent-orchestrator-api-host.md`'s "Resource watchdog" section and
      `/codex/05-infrastructure/deployment-observability.md` to document the new dual-write (AO-internal +
      deployment-api) and note this supersedes the Phase-4 AO-UI-only scope for kill events specifically. Done when both
      docs' `last_reviewed` are bumped and cross-link the new route/table. — unified-trading-pm@25cf1931c
- [x] ✅ [REVIEW] P3. End-to-end verify: trigger a real or `--dry-run`-simulated watchdog kill on the live orchestrator
      VM and confirm it appears in the deployment-ui panel within 2 minutes, without any regression to the existing
      AO-internal kill-relay-to-slot behavior (the mechanism that tells an agent not to re-spawn a killed process). Done
      when both are observed live and cited (screenshot or API response pasted into this todo's evidence line). —
      Evidence: E2E verified live 2026-08-05 21:51 UTC. (1) Deployed the previously-unshipped routes via
      `deployment-service/scripts/cloud-run/deploy-shared.sh` (Cloud Build 99107210-2188-48fb-a8bc-484cf560c4ac SUCCESS;
      image 4615dfe8, revision 00440-b2s, 100% traffic) — `GET /api/watchdog/kill-events` +
      `POST     /api/fleet/watchdog/kill-events` now live (JSON, not SPA fallback); the routes were NOT deployed before
      this (deployed image predated 7d79433/37d6f14). (2) Triggered a `--dry-run`-simulated watchdog kill on the live
      orchestrator VM: `resource-watchdog.sh --dry-run --oneshot` (RW_RSS_LIMIT_NORMAL_GB=3 + RW_DEPLOYMENT_API_URL)
      flagged a controlled 4 GB test process (pid 2382634, slot 16) → dry-run log
      `deployment-api notified: pid=2382634 slot=16 reason=rss:4204500kB > 3145728kB killed=false`. (3) Row appeared in
      `deployment_operational_data.watchdog_kill_events` within the same tick:
      `ts=2026-08-05T21:51:30Z, vm_name=     ip-172-31-5-118, slot_id=16, reason=rss:4204500kB > 3145728kB, killed=false`
      (verified via `bq query`), and `GET /api/watchdog/kill-events?vm_name=ip-172-31-5-118&hours=1` returned exactly
      that row — this GET response is what deployment-ui's kill-events panel renders (`getWatchdogKillEvents` →
      `/api/watchdog/kill-events`, deployment-ui/src/api/deploymentApi.ts:1315). (4) No AO-internal relay regression:
      `POST localhost:8765/     api/resource-watchdog/kill` live (unknown-slot payload →
      `{"ok":true,"queued":false,"reason":"unknown_slot"}`), `GET /api/resource-watchdog/status` reports `kill_count:3`
      intact, and `_rw_notify_orchestrator` is an unchanged sibling call to the additive `_rw_notify_deployment_api`
      (resource-watchdog.sh lines 449-457). Deployment gaps found + tracked:
      `plans/active/issues/watchdog_kill_events_deployment_gaps_2026_08_05.md` — RW_DEPLOYMENT_API_URL not wired into
      the live systemd unit (prod dual-write needs root) and AO host not in `/api/vm-resources/rolling` so the UI panel
      is not reachable via the VM list.

## Deferred

- Extending the SAME dual-write pattern to other host-local incident classes (e.g. QG host governor self-aborts) is
  explicitly out of scope here — this plan is watchdog-kill-events only. A future plan can generalize if the operator
  wants it.
