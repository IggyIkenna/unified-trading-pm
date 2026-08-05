---
doc_type: issue
title: >-
  Watchdog→deployment-api kill-event E2E verified, but two deployment gaps remain: RW_DEPLOYMENT_API_URL not wired into
  the watchdog systemd unit (prod dual-write inactive) + AO host not reachable in deployment-ui kill panel (not in
  resource_samples VM list)
summary: >-
  During the [REVIEW] P3 E2E verify for watchdog_kill_events_deployment_observability_2026_08_05.md (slot 16,
  2026-08-05): deployed deployment-api@4615dfe8 (revision 00440-b2s, 100% traffic) making GET /api/watchdog/kill-events
  + POST /api/fleet/watchdog/kill-events live, then triggered a dry-run-simulated watchdog kill that produced rows in
  BigQuery.deployment_operational_data.watchdog_kill_events (verified via bq query + the GET route — the exact data
  source the deployment-ui kill-events panel renders). Two gaps surfaced that block the production feature from being
  actually live: (1) the shipped opt-in `_rw_notify_deployment_api()` (unified-trading-pm@08f6a9571) is gated on
  RW_DEPLOYMENT_API_URL, which is absent from BOTH the live systemd unit and the repo unit file — so the LIVE watchdog
  still silently skips the deployment-api POST and real kills only reach AO; (2) the deployment-ui kill-events panel is
  a per-VM expandable row gated on /api/vm-resources/rolling, and the AO host (ip-172-31-5-118) has zero
  resource_samples rows, so its kill panel is not reachable through the UI.
status: open
nature: issue
asset_group: [cross-cutting, meta]
stage: [data]
repos: [unified-trading-pm, deployment-ui, deployment-api]
scope: [engineer, admin]
tags: [watchdog, deployment-api, deployment-ui, resource-monitoring, observability, systemd, dual-write, e2e-verify]
related:
  - /plans/active/watchdog_kill_events_deployment_observability_2026_08_05.md
  - /plans/active/resource_watchdog_host_guardian_2026_08_05.md
  - /codex/05-infrastructure/deployment-observability.md
  - /plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md
created: "2026-08-05"
author: ikennaigboaka [slot-16·planning]
source: [watchdog_kill_events_deployment_observability-008 review E2E, slot-16]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
parent_epic: observability_master
drift_direction: advance-code
resolved_by:
depends_on: []
locked_by:
locked_since:
---

# Watchdog→deployment-api kill-event E2E verified; deployment gaps remain

## What I found

E2E verify of `watchdog_kill_events_deployment_observability_2026_08_05.md` todo `[REVIEW] P3`
(watchdog_kill_events_deployment_observability-008). The data pipeline works end-to-end; two deployment gaps block the
production feature from being live.

**E2E result (verified live 2026-08-05 ~21:45–21:50 UTC):**

1. **Deployed the deployment-api watchdog routes** via `deployment-service/scripts/cloud-run/deploy-shared.sh` (Cloud
   Build `99107210-2188-48fb-a8bc-484cf560c4ac`, SUCCESS; image `4615dfe8`, revision `00440-b2s`, 100% traffic). Before
   this deploy the routes were NOT live: the last deployed image predated the route commits (`7d79433` POST, `37d6f14`
   GET, both 2026-08-05 20:05–21:04), so the prior `[BACKEND]`/`[INFRA]` todos had shipped code that was not yet
   deployed. Verified live: `GET /api/watchdog/kill-events` returns JSON (honest empty),
   `POST /api/fleet/watchdog/kill-events` returns `{"status":"ok","rows_written":1}` (DISABLE_AUTH=true in the deployed
   env so the no-auth watchdog POST is accepted).
2. **Triggered a dry-run-simulated watchdog kill**: ran `resource-watchdog.sh --dry-run --oneshot` with
   `RW_RSS_LIMIT_NORMAL_GB=3` + `RW_DEPLOYMENT_API_URL=<deployment-api>` against a controlled 4 GB test process spawned
   in slot 16. The watchdog flagged the process (reason `rss:…kB > 3145728kB`, slot_id=16, killed=false) and POSTed to
   deployment-api. Row verified in `deployment_operational_data.watchdog_kill_events` (bq query) and returned by
   `GET /api/watchdog/kill-events?vm_name=ip-172-31-5-118&hours=1` within <1 min — this GET response is the exact data
   source the deployment-ui kill-events panel renders (`getWatchdogKillEvents` → `/api/watchdog/kill-events` in
   `deployment-ui/src/api/deploymentApi.ts:1315`).
3. **No regression to the AO-internal kill-relay**: `POST /api/resource-watchdog/kill` on the orchestrator is live
   (returns `{"ok":true,"queued":false,"reason":"unknown_slot"}` for an unknown-slot payload — no Slack/queue side
   effect); `GET /api/resource-watchdog/status` reports `kill_count: 3` real relays intact; `_rw_notify_orchestrator` is
   an unchanged sibling call to the added `_rw_notify_deployment_api` (additive dual-write, resource-watchdog.sh
   enforcement path lines 449–457).

**Gap 1 — `RW_DEPLOYMENT_API_URL` not wired into the watchdog systemd unit (prod dual-write INACTIVE).**

`unified-trading-pm@08f6a9571` added `_rw_notify_deployment_api()` gated on `RW_DEPLOYMENT_API_URL` (empty = silent
skip). The env var is set NOWHERE in deployment:

- Live unit `/etc/systemd/system/resource-watchdog.service` (checked via
  `systemctl show resource-watchdog -p Environment`) has no `RW_DEPLOYMENT_API_URL`.
- Repo unit file `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.service` likewise lacks it.
- `config.yaml` has `deployment_api_url: ""` (opt-in key, default empty).

Consequence: the LIVE watchdog's `_rw_notify_deployment_api()` returns at the empty-URL guard, so future REAL kills only
reach AO (`/api/resource-watchdog/kill`), NOT deployment-api/BQ/deployment-ui. My E2E used a standalone `--dry-run`
instance with the env var passed on the command line — that proves the code path, but the production watchdog will not
dual-write until the unit is updated.

**Gap 2 — AO host not reachable in the deployment-ui kill-events panel.**

The kill-events panel (`VmResourceComparison.tsx`, `data-testid="kill-events-panel"`) is a per-VM expandable row. Its
`vm_name` filter comes from `getWatchdogKillEvents(expandedVm, hours)`, and `expandedVm` comes from the VM list in
`/api/vm-resources/rolling` (resource_samples table). The AO host (`ip-172-31-5-118`) has zero resource_samples rows (it
isn't a deployment-service-launched target — the exact reason this plan exists), so it never appears in the VM list →
its kill-events panel is not reachable through the UI. The data pipeline works (GET route returns the row); the panel is
simply not reachable for the AO host specifically.

## Why it matters

- The plan's whole point is that watchdog kill/violation events surface through deployment-api/deployment-ui for the AO
  host. Gap 1 means that in production (real kills, real watchdog service) the deployment-api side never fires — the
  feature is only exercised by my test invocation. The E2E would be misread as "done" without Gap 1 fixed.
- Gap 2 means even with Gap 1 fixed, an operator opening deployment-ui cannot actually SEE the AO host's kill events —
  the panel exists but has no row to expand.

## Recommended decision

Fix Gap 1 first (it makes the feature actually live), then Gap 2 (UI discoverability). Tracked as todos below. The live
unit update + restart needs root — this slot runs with sudo blocked ("no new privileges" container), so the
`systemctl daemon-reload && systemctl restart resource-watchdog` step is operator-gated (or a worker on a root-capable
session).

## Todos

- [x] ✅ [INFRA] P2. Add `Environment=RW_DEPLOYMENT_API_URL=https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`
      and `Environment=RW_VM_NAME=ip-172-31-5-118` to
      `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.service` (repo unit file) so future
      installs/deploys enable the dual-write. (repo: unified-trading-pm) — unified-trading-pm@7f324271b
- [ ] [OPERATOR] P2. Update the LIVE unit `/etc/systemd/system/resource-watchdog.service` with the same two
      `Environment=` lines, then `systemctl daemon-reload && systemctl restart resource-watchdog`. Requires root (slot
      16 has no sudo). After restart, a real kill must produce a `killed=true` row in `watchdog_kill_events` (verify via
      `GET /api/watchdog/kill-events?vm_name=ip-172-31-5-118`). (repo: none — operator action on planning VM)
- [ ] [UI] P3. Make the AO host's kill events reachable in deployment-ui: either (a) extend the resource-history
      collector to also sample the orchestrator/AO host so it appears in `/api/vm-resources/rolling`, or (b) add an
      AO-host kill-events surface in `VmResourceComparison.tsx` (or the fleet view) that is not gated on
      resource_samples rows. (repo: deployment-ui)

## Evidence

- GET route live: `GET https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/watchdog/kill-events?hours=24` →
  `{"hours":24,"vm_name":null,"rows":[…]}` (JSON, not SPA fallback) after deploy.
- POST ingest live: `POST …/api/fleet/watchdog/kill-events` synthetic → `{"status":"ok","rows_written":1}`.
- Dry-run kill row (bq):
  `SELECT ts,vm_name,pid,slot_id,reason,killed FROM watchdog_kill_events WHERE ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)`
  → row `vm_name=ip-172-31-5-118, slot_id=16, killed=false, reason=rss:…kB > 3145728kB`.
- AO relay live: `POST localhost:8765/api/resource-watchdog/kill` (slot_id=unknown) →
  `{"ok":true,"queued":false,"reason":"unknown_slot"}`; `GET /api/resource-watchdog/status` →
  `service_active:true, kill_count:3`.
- Note: two test-artifact rows also exist in the table (a synthetic `vm_name=probe-check` probe and one row from a buggy
  first dry-run attempt with a decimal `RW_RSS_LIMIT_NORMAL_GB=3.6` which left `RSS_LIMIT_NORMAL_KB` unset) — both are
  `killed=false` violation records from the E2E; they are in the BQ streaming buffer so DML delete is not yet possible;
  they can be cleared later if desired.
